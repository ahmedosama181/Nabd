"""Data sources.

Daily history (all five series):
  * currency-api daily rate files (github.com/fawazahmed0/exchange-api), served by jsDelivr, mirrored on
    Cloudflare Pages - one file per day with USD/EGP, EUR, GBP, gold (XAU) and silver (XAG). Primary source:
    one consistent series for everything, no rate limits.
  * Yahoo Finance chart API - backup (Yahoo often answers scripts with HTTP 429 "Too Many Requests")
  * Frankfurter (ECB reference rates) - backup for EUR/USD and GBP/USD only (ECB has no EGP)

Live prices (today, while the page is open):
  * gold-api.com - real-time gold and silver in USD per ounce (free, no key)

Local Egyptian market snapshot (today only, scraped from public pages):
  * egypt.gold-price-today.com
  * edahabapp.com
"""
import datetime as dt
import json
import re
from html.parser import HTMLParser
from urllib.parse import quote

from .fetch import FetchError, get

YAHOO_HOSTS = ("query1.finance.yahoo.com", "query2.finance.yahoo.com")

# symbol -> what it is
YAHOO_SYMBOLS = {
    "GC=F": "Gold, USD per ounce",
    "SI=F": "Silver, USD per ounce",
    "EGP=X": "USD/EGP",
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
}


def _to_ts(day):
    return int(dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp())


def yahoo_history(symbol, start, end):
    """Return {'YYYY-MM-DD': close} for [start, end]. Raises FetchError if every host fails."""
    errors = []
    for host in YAHOO_HOSTS:
        url = "https://%s/v8/finance/chart/%s?period1=%d&period2=%d&interval=1d" % (
            host,
            quote(symbol, safe=""),
            _to_ts(start),
            _to_ts(end + dt.timedelta(days=1)),
        )
        try:
            payload = json.loads(get(url, retries=1, accept="application/json").decode("utf-8"))
            return parse_yahoo(payload)
        except (FetchError, ValueError, KeyError) as exc:
            errors.append("%s: %s" % (host, exc))
            if "429" in str(exc):  # rate limited: the other host shares the same limit
                break
    raise FetchError("Yahoo Finance failed for %s -> %s" % (symbol, "; ".join(errors)))


def parse_yahoo(payload):
    chart = payload["chart"]
    if not chart.get("result"):
        raise ValueError((chart.get("error") or {}).get("description", "no data"))
    result = chart["result"][0]
    offset = result["meta"].get("gmtoffset", 0) or 0
    closes = result["indicators"]["quote"][0]["close"]
    out = {}
    for ts, close in zip(result.get("timestamp", []), closes):
        if close is None:  # Yahoo emits nulls for non-trading days
            continue
        day = dt.datetime.fromtimestamp(ts + offset, tz=dt.timezone.utc).strftime("%Y-%m-%d")
        out[day] = float(close)
    if not out:
        raise ValueError("empty series")
    return out


def frankfurter_usd_cross(currency, start, end):
    """EUR/USD or GBP/USD from ECB rates (USD->currency inverted)."""
    url = "https://api.frankfurter.dev/v1/%s..%s?base=USD&symbols=%s" % (start, end, currency)
    payload = json.loads(get(url, accept="application/json").decode("utf-8"))
    return {day: 1.0 / vals[currency] for day, vals in payload["rates"].items() if vals.get(currency)}


DAILY_MIRRORS = (
    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{day}/v1/currencies/usd.json",
    "https://{day}.currency-api.pages.dev/v1/currencies/usd.json",
)
DAILY_CODES = (("EGP=X", "egp", False), ("EURUSD=X", "eur", True), ("GBPUSD=X", "gbp", True),
               ("GC=F", "xau", True), ("SI=F", "xag", True))


def _daily_file(day):
    """The rates file for one day (USD base), from the first mirror that answers, or None."""
    for template in DAILY_MIRRORS:
        try:
            return json.loads(get(template.format(day=day), retries=1, accept="application/json").decode("utf-8"))["usd"]
        except (FetchError, ValueError, KeyError):
            continue
    return None


def daily_history(start, end, workers=12):
    """Daily rates for every weekday in [start, end]: one small file per day, fetched in parallel.

    Returns {series key: {date: value}} with the same keys the rest of the app uses
    (USD/EGP as-is; EUR/USD, GBP/USD, gold and silver in USD per ounce are inverted from 'units per USD').
    """
    from concurrent.futures import ThreadPoolExecutor

    days = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            days.append(d.isoformat())
        d += dt.timedelta(days=1)
    if not days:
        raise FetchError("no weekdays in range")
    # One quick probe first: if the source is unreachable, fail fast instead of trying every day.
    if _daily_file(days[0]) is None and (len(days) == 1 or _daily_file(days[-1]) is None):
        raise FetchError("currency-api unreachable")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = [(day, r) for day, r in zip(days, pool.map(_daily_file, days)) if r]
    if len(rows) < 0.6 * len(days):
        raise FetchError("currency-api returned only %d of %d days" % (len(rows), len(days)))
    out = {key: {} for key, _, _ in DAILY_CODES}
    for day, r in rows:
        for key, code, invert in DAILY_CODES:
            v = r.get(code)
            if v:
                out[key][day] = (1.0 / v) if invert else float(v)
    return out


def live_price(code):
    """Real-time price of gold ('XAU') or silver ('XAG') in USD per ounce from gold-api.com."""
    payload = json.loads(get("https://api.gold-api.com/price/%s" % code, timeout=10, retries=1,
                             accept="application/json").decode("utf-8"))
    return {"price": float(payload["price"]), "updated_at": payload.get("updatedAt")}


# ---------------------------------------------------------------- local Egyptian market


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def html_to_text(html):
    p = _Text()
    p.feed(html)
    text = " ".join(p.parts)
    # Arabic-Indic digits -> ASCII
    text = text.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789.,"))
    return re.sub(r"\s+", " ", text)


def _num(s):
    return float(s.replace(",", ""))


KARATS = ("24", "21", "18", "14")

# 'عيار 21 6,160 جنيه 6,110 جنيه'  (sell first, then buy: column order on the page is بيع then شراء)
_RE_GPT = re.compile(r"عيار\s*(24|21|18|14)\s+([\d,.]+)\s*جنيه\s+([\d,.]+)\s*جنيه")
# 'الذهب عيار 21: بيع: 6139 جنيه شراء: 6119 جنيه'
_RE_EDAHAB = re.compile(r"عيار\s*(24|21|18|14)\s*:\s*بيع\s*:\s*([\d,.]+)\s*جنيه\s*شراء\s*:\s*([\d,.]+)")


def parse_karats(text, pattern):
    out = {}
    for karat, sell, buy in pattern.findall(text):
        if karat not in out:  # first occurrence = the main price table
            out[karat] = {"sell": _num(sell), "buy": _num(buy)}
    return out


LOCAL_SOURCES = (
    ("gold-price-today.com", "https://egypt.gold-price-today.com/", _RE_GPT),
    ("edahabapp.com", "https://edahabapp.com/", _RE_EDAHAB),
)


def local_gold_snapshot():
    """Try each local source in turn; return the first one that yields a 21k and 24k price.

    Returns {'source', 'url', 'fetched_at', 'karats': {'24': {sell, buy}, ...}} or {'error': ...}.
    """
    errors = []
    for name, url, pattern in LOCAL_SOURCES:
        try:
            text = html_to_text(get(url).decode("utf-8", errors="replace"))
            karats = parse_karats(text, pattern)
            if "21" in karats and "24" in karats:
                return {
                    "source": name,
                    "url": url,
                    "fetched_at": dt.datetime.now().isoformat(timespec="seconds"),
                    "karats": karats,
                }
            errors.append("%s: page layout changed (karat prices not found)" % name)
        except FetchError as exc:
            errors.append("%s: %s" % (name, exc))
    return {"error": " | ".join(errors)}
