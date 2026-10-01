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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE_PATH = os.path.join(ROOT, "data", "store.json")
LEGACY_CACHE = os.path.join(ROOT, "data", "cache.json")
MAX_AGE_SECONDS = 30 * 60  # don't hit the network again within 30 minutes unless asked
OVERLAP_DAYS = 4
SYMBOLS = list(sources.YAHOO_SYMBOLS)

_lock = threading.Lock()


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
        local_future = pool.submit(sources.local_gold_snapshot)
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
    today = today or dt.date.today()
    with _lock:
        store = load_store(today)
        fresh = False
        if store["fetched_at"] and not force:
            age = (dt.datetime.now() - dt.datetime.fromisoformat(store["fetched_at"])).total_seconds()
            fresh = age < MAX_AGE_SECONDS
        notice, added = None, 0
        if not fresh:
            had_data = bool(store["series"]["EGP=X"])
            before = json.dumps(store["series"], sort_keys=True)
            added = update(store, today)
            reached = any(s["ok"] for s in store["status"].values())
            if not reached and had_data:
                notice = "offline"  # nothing answered: keep the saved prices, try again next time
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
        payload = analysis.build(store["series"], store.get("local"), today)
        payload.update(
            fetched_at=store["fetched_at"],
            sources={s: source_id(store["sources"].get(s)) for s in SYMBOLS},
            labels=dict(sources.YAHOO_SYMBOLS),
            from_store=fresh,
            added_days=added,
            notice=notice,
        )
        return payload


# ---------------------------------------------------------------- live prices (while the page is open)
LIVE_TTL, LOCAL_TTL = 30, 10 * 60  # seconds
_live = {"at": 0.0, "data": None}
_local = {"at": 0.0, "data": None, "busy": False}
_live_lock = threading.Lock()


def _refresh_local():
    try:
        snap = sources.local_gold_snapshot()
        if snap and "error" not in snap:
            _local["data"] = snap
        _local["at"] = time.time()
    finally:
        _local["busy"] = False


def live_payload(today=None):
    """Real-time gold and silver (USD/oz) plus the latest saved dollar rate and Egyptian shop prices.

    Cached for 30 s, so any number of open pages costs at most two small requests per 30 s. Shop prices are
    re-read in the background every 10 minutes and never slow this call down.
    """
    today = today or dt.date.today()
    with _live_lock:
        now = time.time()
        if _live["data"] and now - _live["at"] < LIVE_TTL:
            return _live["data"]
        store = load_store(today)

        def last(sym):
            series = store["series"].get(sym) or {}
            if not series:
                return None, None
            day = max(series)
            return day, series[day]

        if _local["data"] is None and store.get("local") and "error" not in store["local"]:
            _local["data"] = store["local"]
            try:
                _local["at"] = dt.datetime.fromisoformat(store["local"]["fetched_at"]).timestamp()
            except (KeyError, ValueError):
                _local["at"] = 0.0
        if now - _local["at"] > LOCAL_TTL and not _local["busy"]:
            _local["busy"] = True
            threading.Thread(target=_refresh_local, daemon=True).start()  # daemon: never delays quitting the app

        fx_day, fx = last("EGP=X")
        metals = {}
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {code: pool.submit(sources.live_price, code) for code in ("XAU", "XAG")}
            for code, sym in (("XAU", "GC=F"), ("XAG", "SI=F")):
                try:
                    p = futures[code].result()
                except (FetchError, ValueError, KeyError, TypeError):
                    continue
                ref_day, ref = last(sym)
                metals[code] = {"usd_oz": p["price"], "updated_at": p["updated_at"], "ref": ref, "ref_date": ref_day}
        out = {"metals": metals, "fx": fx, "fx_date": fx_day, "local": _local["data"],
               "fetched_at": dt.datetime.now().isoformat(timespec="seconds")}
        _live.update(at=now, data=out)
        return out


CSV_LABELS_AR = {
    "usd": "الدولار الأمريكي (جنيه)", "eur": "اليورو (جنيه)", "gbp": "الجنيه الإسترليني (جنيه)",
    "gold_24": "ذهب عيار 24 (جنيه/جرام)", "gold_21": "ذهب عيار 21 (جنيه/جرام)", "gold_18": "ذهب عيار 18 (جنيه/جرام)",
    "gold_oz_usd": "الذهب عالمياً (دولار/أوقية)", "silver": "فضة (جنيه/جرام)", "silver_oz_usd": "الفضة عالمياً (دولار/أوقية)",
}


def to_csv(payload, lang="en"):
    """Daily table (forward-filled), UTF-8 with BOM so Excel opens it correctly."""
    buf = io.StringIO()
    w = csv.writer(buf)
    if lang == "ar":
        labels = {a["key"]: CSV_LABELS_AR.get(a["key"], a["label"]) for a in payload["assets"]}
    else:
        labels = {a["key"]: "%s (%s)" % (a["label"], a["unit"]) for a in payload["assets"]}
    keys = list(payload["grid"]["series"])
    w.writerow(["التاريخ" if lang == "ar" else "Date"] + [labels[k] for k in keys])
    for i, d in enumerate(payload["grid"]["dates"]):
        w.writerow([d] + ["" if payload["grid"]["series"][k][i] is None else payload["grid"]["series"][k][i] for k in keys])
    return ("﻿" + buf.getvalue()).encode("utf-8")
