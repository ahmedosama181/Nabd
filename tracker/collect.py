"""Keep a small on-disk store of this year's prices, top it up incrementally, build the UI payload.

Store rules
  * Only the current calendar year is kept, plus the previous year's last close (the YTD starting point).
  * When a new year starts the store is wiped and rebuilt from 20 Dec of the previous year.
  * Each update only downloads from the last saved day (minus a few days of overlap, so a price that was
    still moving when it was saved gets corrected) up to today.
"""
import csv
import datetime as dt
import io
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from . import analysis, sources
from .fetch import FetchError
from .live import Throttle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE_PATH = os.path.join(ROOT, "data", "store.json")
LEGACY_CACHE = os.path.join(ROOT, "data", "cache.json")
MAX_AGE_SECONDS = 30 * 60  # don't hit the network again within 30 minutes unless asked
MIN_FORCED_SECONDS = 60    # Refresh re-downloads the daily rates at most once a minute, however often it is clicked
RETRY_SECONDS = 5 * 60     # after a failed update (offline), try again on its own at most every 5 minutes
OVERLAP_DAYS = 4
SYMBOLS = list(sources.YAHOO_SYMBOLS)

_lock = threading.Lock()
_last_failed = 0.0  # when the last update reached no source at all (kept in memory only)


def _empty_store(year):
    return {"version": 2, "year": year, "series": {s: {} for s in SYMBOLS}, "sources": {}, "status": {},
            "local": None, "fetched_at": None}


def load_store(today):
    try:
        with open(STORE_PATH, encoding="utf-8") as fh:
            store = json.load(fh)
        if store.get("version") != 2 or store.get("year") != today.year:
            return _empty_store(today.year)  # a new year (or old format): history is not kept
        for s in SYMBOLS:
            store["series"].setdefault(s, {})
        return store
    except (OSError, ValueError):
        return _empty_store(today.year)


def save_store(store):
    try:
        os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
        tmp = STORE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(store, fh, separators=(",", ":"))
        os.replace(tmp, STORE_PATH)
        if os.path.exists(LEGACY_CACHE):
            os.remove(LEGACY_CACHE)  # file from the first version of the app
    except OSError:
        pass


def _year_start_fetch(today):
    return dt.date(today.year - 1, 12, 20)  # far enough back to always catch the last close of December


def fetch_start(series, today):
    """First day to download for one symbol: from the last saved day minus a small overlap."""
    if not series:
        return _year_start_fetch(today)
    last = dt.date.fromisoformat(max(series))
    return max(_year_start_fetch(today), last - dt.timedelta(days=OVERLAP_DAYS))


def prune(series, today):
    """Keep this year's days plus only the single last close of the previous year."""
    start = dt.date(today.year, 1, 1).isoformat()
    before = [d for d in series if d < start]
    keep_base = max(before) if before else None
    return {d: v for d, v in series.items() if d >= start or d == keep_base}


SRC_DAILY, SRC_YAHOO, SRC_ECB = "daily", "yahoo", "frankfurter"


def source_id(label):
    """Source id for a stored source name (older versions saved longer labels)."""
    if not label:
        return None
    low = label.lower()
    if low == SRC_DAILY or "currency-api" in low:
        return SRC_DAILY
    if "yahoo" in low:
        return SRC_YAHOO
    if "frankfurter" in low:
        return SRC_ECB
    return low


def update(store, today):
    """Download what is missing (in place). Returns the number of new days added.

    Every series comes from one source for the whole year: the daily rates first, then Yahoo Finance,
    then (EUR, GBP only) the ECB. If a series has to change source, the whole year is downloaded again
    from the new source instead of joining two sources (futures closes and spot snapshots differ a little,
    and a join would show up as a fake jump).
    """
    now = dt.datetime.now()
    year_start = _year_start_fetch(today)
    starts = {s: fetch_start(store["series"][s], today) for s in SYMBOLS}
    stored = {s: source_id(store["sources"].get(s)) for s in SYMBOLS}
    blocked = store.get("yahoo_blocked_until")
    yahoo_ok = not (blocked and dt.datetime.fromisoformat(blocked) > now)  # Yahoo refused us recently: skip it
    daily_cache, yahoo_calls = {}, [0]

    def daily(start):
        if start not in daily_cache:
            try:
                daily_cache[start] = sources.daily_history(start, today)
            except FetchError as exc:
                daily_cache[start] = exc
        if isinstance(daily_cache[start], Exception):
            raise daily_cache[start]
        return daily_cache[start]

    def fetch(sym, src, start):
        if src == SRC_DAILY:
            data = daily(start).get(sym)
            if not data:
                raise FetchError("no %s in the daily rates" % sym)
            return data
        if src == SRC_YAHOO:
            if yahoo_calls[0]:
                time.sleep(0.8)  # Yahoo rate-limits bursts
            yahoo_calls[0] += 1
            return sources.yahoo_history(sym, start, today)
        return sources.frankfurter_usd_cross(sym[:3], start.isoformat(), today.isoformat())

    got, errors = {}, {}
    with ThreadPoolExecutor(max_workers=1) as pool:
        local_future = pool.submit(shop_snapshot, store)  # throttled: at most every 10 minutes
        for sym in SYMBOLS:
            order = [SRC_DAILY, SRC_YAHOO] + ([SRC_ECB] if sym in ("EURUSD=X", "GBPUSD=X") else [])
            errors[sym] = []
            for src in order:
                if src == SRC_YAHOO and not yahoo_ok:
                    errors[sym].append("Yahoo Finance skipped (it refused recent requests)")
                    continue
                full = bool(store["series"][sym]) and stored[sym] not in (None, src)  # source change: redo the year
                try:
                    data = fetch(sym, src, year_start if full else starts[sym])
                except (FetchError, ValueError, KeyError) as exc:
                    errors[sym].append("%s: %s" % (src, exc))
                    if src == SRC_YAHOO:
                        yahoo_ok = False
                        store["yahoo_blocked_until"] = (now + dt.timedelta(hours=3)).isoformat(timespec="seconds")
                    continue
                got[sym] = (data, src, full)
                break
        local = local_future.result()

    added, status = 0, {}
    for sym in SYMBOLS:
        if sym in got:
            data, src, full = got[sym]
            before = len(store["series"][sym])
            if full:
                store["series"][sym] = dict(data)
            else:
                store["series"][sym].update(data)
            added += max(0, len(store["series"][sym]) - before)
            store["sources"][sym] = src
            status[sym] = {"ok": True, "source": src}
        else:
            status[sym] = {"ok": False, "error": " | ".join(errors[sym])}
        store["series"][sym] = prune(store["series"][sym], today)
    store["status"] = status
    if local and "error" not in local:
        store["local"] = local
    elif store.get("local"):
        store["local"] = dict(store["local"], stale=True)
    else:
        store["local"] = local
    store["fetched_at"] = dt.datetime.now().isoformat(timespec="seconds")
    return added


def get_payload(force=False, today=None):
    """Return the UI payload. Tops up the store when it is older than 30 minutes (or when forced)."""
    global _last_failed
    today = today or dt.date.today()
    with _lock:
        store = load_store(today)
        fresh = False
        if store["fetched_at"]:
            age = (dt.datetime.now() - dt.datetime.fromisoformat(store["fetched_at"])).total_seconds()
            fresh = age < (MIN_FORCED_SECONDS if force else MAX_AGE_SECONDS)
        notice, added = None, 0
        if not fresh and store["series"]["EGP=X"] and time.time() - _last_failed < (MIN_FORCED_SECONDS if force else RETRY_SECONDS):
            fresh, notice = True, "offline"  # nothing answered moments ago: show the saved prices, don't ask again yet
        if not fresh:
            had_data = bool(store["series"]["EGP=X"])
            before = json.dumps(store["series"], sort_keys=True)
            added = update(store, today)
            reached = any(s["ok"] for s in store["status"].values())
            if not reached and had_data:
                notice = "offline"  # nothing answered: keep the saved prices, try again next time
                _last_failed = time.time()
                store = load_store(today)
            elif store["series"]["EGP=X"]:
                save_store(store)
                if not all(s["ok"] for s in store["status"].values()):
                    notice = "partial"
            elif json.dumps(store["series"], sort_keys=True) == before and had_data:
                notice = "offline"
            else:
                errs = "; ".join(s.get("error", "") for s in store["status"].values() if not s["ok"])
                print("Could not download prices: " + errs)  # details for the terminal; the page shows a short message
                raise RuntimeError("no-connection")
        fx, metals = live_rates(store, today, force=force or not fresh)
        values, key = live_overlay(fx, metals, today)
        local = newest_local(store.get("local"), shop_prices(store))
        payload = analysis.build(store["series"], local, today, live=values, live_key=key)
        payload.update(
            live={"key": key, "fx_source": fx and fx.get("source"), "fx_at": fx and fx.get("at"),
                  "metals_at": metals and metals.get("at")} if key else None,
            fetched_at=store["fetched_at"],
            sources={s: source_id(store["sources"].get(s)) for s in SYMBOLS},
            labels=dict(sources.YAHOO_SYMBOLS),
            from_store=fresh,
            added_days=added,
            notice=notice,
        )
        return payload


# ---------------------------------------------------------------- live prices (while the page is open)
# How often each live source may be asked (see tracker/live.py for the full rules, including back-off).
FX_INTERVAL, METALS_INTERVAL, SHOPS_INTERVAL = 5 * 60, 60, 10 * 60  # seconds
LIVE_MAX_AGE = 3 * 3600  # a "live" value older than this is not shown as live
_fx = Throttle(FX_INTERVAL)
_metals = Throttle(METALS_INTERVAL)
_shops = Throttle(SHOPS_INTERVAL)
_shops_busy = threading.Event()


def _now_iso():
    return dt.datetime.now().isoformat(timespec="seconds")


def _latest(store, sym):
    series = store["series"].get(sym) or {}
    if not series:
        return None, None
    day = max(series)
    return day, series[day]


def daily_reference(store):
    """The latest daily USD, EUR and GBP in EGP, used to sanity-check live rates."""
    usd = _latest(store, "EGP=X")[1]
    if not usd:
        return None
    eur, gbp = _latest(store, "EURUSD=X")[1], _latest(store, "GBPUSD=X")[1]
    return {"usd": usd, "eur": eur * usd if eur else None, "gbp": gbp * usd if gbp else None}


def _sane(fx):
    try:
        return (1 < fx["usd"] < 10000 and 0.5 < fx["eur"] / fx["usd"] < 2.0 and 0.5 < fx["gbp"] / fx["usd"] < 3.0)
    except (KeyError, TypeError, ZeroDivisionError):
        return False


def _close(a, b, tol):
    return all(b.get(k) and abs(a[k] / b[k] - 1) <= tol for k in ("usd", "eur", "gbp") if b.get(k))


def fetch_live_fx(reference):
    """Live USD, EUR and GBP in EGP: Coinbase first, Wise as backup.

    A reading more than 10% away from the latest daily rate is accepted only when both live sources agree
    within 1% (a real jump, such as a devaluation, rather than a bad reading)."""
    far, errors = [], []
    for fetch in (sources.coinbase_fx, sources.wise_fx):
        try:
            fx = fetch()
        except (FetchError, ValueError, KeyError, TypeError) as exc:
            errors.append("%s: %s" % (fetch.__name__, exc))
            continue
        if not _sane(fx):
            errors.append("%s: implausible values" % fetch.__name__)
            continue
        if reference is None or _close(fx, reference, 0.10):
            return dict(fx, at=_now_iso())
        far.append(fx)
    if len(far) == 2 and _close(far[0], far[1], 0.01):
        return dict(far[0], at=_now_iso())
    raise FetchError("no plausible live exchange rate (%s)" % "; ".join(errors or ["far from the daily rate"]))


def fetch_live_metals():
    """Real-time gold and silver (USD per ounce). Keeps the previous value of a metal that failed this time."""
    out, previous = {}, _metals.value or {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {code: pool.submit(sources.live_price, code) for code in ("XAU", "XAG")}
        for code, future in futures.items():
            try:
                out[code] = future.result()
            except (FetchError, ValueError, KeyError, TypeError):
                if code in previous:
                    out[code] = previous[code]
    if not out:
        raise FetchError("gold-api.com did not answer")
    out["at"] = _now_iso()
    return out


def _fresh(value, today):
    """A live value is used only on the day it was read and while it is less than LIVE_MAX_AGE old."""
    if not value or "at" not in value:
        return None
    at = dt.datetime.fromisoformat(value["at"])
    if at.date() != today or (dt.datetime.now() - at).total_seconds() > LIVE_MAX_AGE:
        return None
    return value


def live_rates(store, today, force=False):
    """(fx, metals): the live values allowed right now; force=True at app start and on Refresh."""
    reference = daily_reference(store)
    with ThreadPoolExecutor(max_workers=2) as pool:  # both at once: a slow source never delays the other
        fx = pool.submit(_fx.get, lambda: fetch_live_fx(reference), force)
        metals = pool.submit(_metals.get, fetch_live_metals, force)
        return _fresh(fx.result(), today), _fresh(metals.result(), today)


def live_overlay(fx, metals, today):
    """The live 'now' point for analysis.build: {series: value} under one key like '2026-10-01T16:33'."""
    values = {}
    if fx:
        values.update({"EGP=X": fx["usd"], "EURUSD=X": fx["eur"] / fx["usd"], "GBPUSD=X": fx["gbp"] / fx["usd"]})
    if metals:
        for code, sym in (("XAU", "GC=F"), ("XAG", "SI=F")):
            if code in metals:
                values[sym] = metals[code]["price"]
    if not values:
        return None, None
    stamps = [dt.datetime.fromisoformat(v["at"]) for v in (fx, metals) if v]
    return values, today.isoformat() + "T" + max(stamps).strftime("%H:%M")


def _read_shops():
    snap = sources.local_gold_snapshot()
    if not snap or "error" in snap:
        raise FetchError((snap or {}).get("error", "no shop prices"))
    return snap


def _seed_shops(store):
    """Start from the shop prices saved in the store, so a restart doesn't read the shop pages again right away."""
    if _shops.value is None and store.get("local") and "error" not in store["local"]:
        _shops.value = store["local"]
        try:
            _shops.at = dt.datetime.fromisoformat(store["local"]["fetched_at"]).timestamp()
        except (KeyError, ValueError):
            _shops.at = 0.0


def shop_snapshot(store):
    """Shop prices for the daily update: the shop pages are read only when the last reading is 10+ minutes old.
    Returns the error (as {"error": ...}) when nothing could ever be read, like local_gold_snapshot()."""
    _seed_shops(store)
    value = _shops.get(_read_shops)
    if value is None:
        return {"error": _shops.error or "no shop prices"}
    return dict(value, stale=True) if _shops.error else value  # the last reading failed: these are older prices


def _refresh_shops():
    try:
        _shops.get(_read_shops)
    finally:
        _shops_busy.clear()


def shop_prices(store):
    """Egyptian gold shop prices: re-read in the background (never slows a request down), at most every 10 min."""
    _seed_shops(store)
    if _shops.due() and not _shops_busy.is_set():
        _shops_busy.set()
        threading.Thread(target=_refresh_shops, daemon=True).start()  # daemon: never delays quitting the app
    return _shops.value


def newest_local(*snapshots):
    """The most recent usable shop-price snapshot (or the first one, error included, if none is usable)."""
    good = [x for x in snapshots if x and "error" not in x]
    if good:
        return max(good, key=lambda x: x.get("fetched_at", ""))
    return next((x for x in snapshots if x), None)


def live_payload(today=None):
    """Live strip data: real-time gold and silver, live currency rates, Egyptian shop prices.

    Every source is throttled (tracker/live.py), so polling this every minute from any number of open pages
    costs at most: gold-api 2 requests/min, Coinbase 1 request/5 min, the shop page 1 request/10 min."""
    today = today or dt.date.today()
    store = load_store(today)
    fx, metals = live_rates(store, today)
    fx_day, fx_daily = _latest(store, "EGP=X")
    out_metals = {}
    for code, sym in (("XAU", "GC=F"), ("XAG", "SI=F")):
        if metals and code in metals:
            ref_day, ref = _latest(store, sym)
            out_metals[code] = {"usd_oz": metals[code]["price"], "updated_at": metals[code].get("updated_at"),
                                "ref": ref, "ref_date": ref_day}
    daily = daily_reference(store) or {}
    return {"metals": out_metals, "fx": fx, "fx_daily": fx_daily, "fx_date": fx_day, "fx_ref": daily,
            "local": shop_prices(store), "fetched_at": _now_iso()}


CSV_LABELS_AR = {
    "usd": "الدولار الأمريكي (جنيه)", "eur": "اليورو (جنيه)", "gbp": "الجنيه الإسترليني (جنيه)",
    "gold_24": "ذهب عيار 24 (جنيه/جرام)", "gold_21": "ذهب عيار 21 (جنيه/جرام)", "gold_18": "ذهب عيار 18 (جنيه/جرام)",
    "gold_oz_usd": "الذهب عالمياً (دولار/أوقية)", "silver": "فضة (جنيه/جرام)", "silver_oz_usd": "الفضة عالمياً (دولار/أوقية)",
}


def to_csv(payload, lang="en"):
    """Daily table (forward-filled, plus the live point when there is one), UTF-8 with BOM so Excel opens it correctly."""
    buf = io.StringIO()
    w = csv.writer(buf)
    if lang == "ar":
        labels = {a["key"]: CSV_LABELS_AR.get(a["key"], a["label"]) for a in payload["assets"]}
    else:
        labels = {a["key"]: "%s (%s)" % (a["label"], a["unit"]) for a in payload["assets"]}
    keys = list(payload["grid"]["series"])
    w.writerow(["التاريخ" if lang == "ar" else "Date"] + [labels[k] for k in keys])
    for i, d in enumerate(payload["grid"]["dates"]):
        # the live point's key "2026-10-01T16:33" is written as "2026-10-01 16:33", which Excel reads as a date and time
        w.writerow([d.replace("T", " ")] + ["" if payload["grid"]["series"][k][i] is None else payload["grid"]["series"][k][i] for k in keys])
    return ("﻿" + buf.getvalue()).encode("utf-8")
