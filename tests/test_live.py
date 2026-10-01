"""Live prices: throttling and back-off (fake clock), live currency validation, the live 'now' point.
Offline: every source is replaced by a fake."""
import datetime as dt
import json
import os
import statistics
import tempfile
import threading
import time
import unittest
from unittest import mock

from tracker import analysis, collect
from tracker.fetch import FetchError
from tracker.live import Throttle


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


class ThrottleRules(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.th = Throttle(min_interval=300, force_floor=30, base_backoff=60, max_backoff=1800, clock=self.clock)
        self.n = 0

    def ok(self):
        self.n += 1
        return self.n

    def fail(self):
        raise FetchError("HTTP 429")

    def test_reuses_value_until_it_is_old(self):
        self.assertEqual(self.th.get(self.ok), 1)
        self.clock.advance(299)
        self.assertEqual(self.th.get(self.ok), 1)
        self.clock.advance(1)
        self.assertEqual(self.th.get(self.ok), 2)
        self.assertEqual(self.th.calls, 2)

    def test_force_is_limited_to_once_per_floor(self):
        self.th.get(self.ok)
        for _ in range(50):  # someone clicking Refresh fifty times in ten seconds
            self.clock.advance(0.2)
            self.th.get(self.ok, force=True)
        self.assertEqual(self.th.calls, 1)
        self.clock.advance(30)
        self.assertEqual(self.th.get(self.ok, force=True), 2)

    def test_back_off_doubles_and_is_capped(self):
        self.th.get(self.ok)
        self.clock.advance(300)
        waits = []
        for _ in range(8):
            self.th.get(self.fail, force=True)
            start = self.clock()
            while not self.th.due(force=True):  # how long until we may ask again?
                self.clock.advance(1)
            waits.append(self.clock() - start)
        self.assertEqual(waits, [60, 120, 240, 480, 960, 1800, 1800, 1800])
        self.assertEqual(self.th.value, 1)  # the last good value is kept meanwhile

    def test_failures_never_cause_rapid_retries(self):
        # an hour of polling every second against a source that always fails
        for _ in range(3600):
            self.th.get(self.fail, force=True)
            self.clock.advance(1)
        self.assertLessEqual(self.th.calls, 7)  # 60+120+240+480+960+1800 s fit in an hour

    def test_one_success_resets_the_back_off(self):
        self.th.get(self.fail)
        self.clock.advance(60)
        self.assertEqual(self.th.get(self.ok), 1)
        self.assertEqual(self.th.failures, 0)
        self.assertEqual(self.th.retry_after, 0.0)

    def test_empty_answer_counts_as_failure(self):
        self.assertIsNone(self.th.get(lambda: None))
        self.assertEqual(self.th.failures, 1)

    def test_simultaneous_callers_share_one_request(self):
        th = Throttle(min_interval=300)
        started = threading.Event()

        def slow():
            started.set()
            time.sleep(0.3)
            return "v"

        results = []
        threads = [threading.Thread(target=lambda: results.append(th.get(slow))) for _ in range(10)]
        for x in threads:
            x.start()
        for x in threads:
            x.join()
        self.assertEqual(th.calls, 1)
        self.assertEqual(results, ["v"] * 10)


REF = {"usd": 50.0, "eur": 56.0, "gbp": 65.0}


class LiveCurrencies(unittest.TestCase):
    def fx(self, usd, eur, gbp, source):
        return {"usd": usd, "eur": eur, "gbp": gbp, "source": source}

    def run_fx(self, coinbase, wise):
        def make(value):
            def f():
                if isinstance(value, Exception):
                    raise value
                return value
            return f
        cb, wi = make(coinbase), make(wise)
        cb.__name__, wi.__name__ = "coinbase_fx", "wise_fx"
        with mock.patch.object(collect.sources, "coinbase_fx", cb), mock.patch.object(collect.sources, "wise_fx", wi):
            return collect.fetch_live_fx(REF)

    def test_coinbase_first(self):
        out = self.run_fx(self.fx(50.3, 56.4, 65.2, "coinbase"), FetchError("unused"))
        self.assertEqual(out["source"], "coinbase")
        self.assertIn("at", out)

    def test_wise_when_coinbase_fails(self):
        out = self.run_fx(FetchError("HTTP 451"), self.fx(50.2, 56.1, 65.1, "wise"))
        self.assertEqual(out["source"], "wise")

    def test_implausible_reading_is_skipped(self):
        out = self.run_fx(self.fx(0.02, 56.0, 65.0, "coinbase"), self.fx(50.2, 56.1, 65.1, "wise"))
        self.assertEqual(out["source"], "wise")

    def test_far_reading_needs_both_sources_to_agree(self):
        jump = self.fx(70.0, 78.0, 91.0, "coinbase")  # +40%: e.g. a devaluation
        self.assertEqual(self.run_fx(jump, self.fx(70.3, 78.2, 91.4, "wise"))["usd"], 70.0)
        with self.assertRaises(FetchError):
            self.run_fx(jump, self.fx(90.0, 99.0, 117.0, "wise"))  # both far, but they disagree

    def test_far_reading_with_backup_close_to_daily_uses_backup(self):
        out = self.run_fx(self.fx(70.0, 78.0, 91.0, "coinbase"), self.fx(50.2, 56.1, 65.1, "wise"))
        self.assertEqual(out["source"], "wise")

    def test_everything_down(self):
        with self.assertRaises(FetchError):
            self.run_fx(FetchError("x"), FetchError("y"))


class LiveNowPoint(unittest.TestCase):
    def raw(self):
        days = ["2025-12-31", "2026-03-03", "2026-03-04"]
        return {
            "EGP=X": dict(zip(days, [50.0, 52.0, 52.0])),
            "EURUSD=X": dict(zip(days, [1.1, 1.1, 1.1])),
            "GBPUSD=X": dict(zip(days, [1.3, 1.3, 1.3])),
            "GC=F": dict(zip(days, [3110.34768] * 3)),
            "SI=F": dict(zip(days, [31.1034768] * 3)),
        }

    def test_live_point_is_last_and_today_compares_with_start_of_day(self):
        raw = self.raw()
        before = json.dumps(raw, sort_keys=True)
        live = {"EGP=X": 52.52, "EURUSD=X": 1.12, "GBPUSD=X": 1.3, "GC=F": 3110.34768 * 1.01}
        p = analysis.build(raw, None, dt.date(2026, 3, 4), live=live, live_key="2026-03-04T16:33")
        self.assertEqual(json.dumps(raw, sort_keys=True), before)  # the daily history is not changed
        self.assertEqual(p["live_key"], "2026-03-04T16:33")
        self.assertEqual(p["grid"]["dates"][-2:], ["2026-03-04", "2026-03-04T16:33"])
        a = {x["key"]: x for x in p["assets"]}
        self.assertAlmostEqual(a["usd"]["kpis"]["end"], 52.52)
        self.assertAlmostEqual(a["usd"]["kpis"]["change_1d_pct"], 1.0)  # vs today's daily (start of day) value
        self.assertAlmostEqual(a["eur"]["kpis"]["end"], 1.12 * 52.52)
        self.assertAlmostEqual(a["gold_24"]["kpis"]["end"], 100 * 1.01 * 52.52)
        self.assertAlmostEqual(a["silver"]["kpis"]["end"], 1 * 52.52)  # no live silver: global price from the daily data
        d = a["gold_24"]["drivers"]
        self.assertAlmostEqual((1 + d["base_pct"] / 100) * (1 + d["fx_pct"] / 100) - 1, a["gold_24"]["kpis"]["change_pct"] / 100, places=9)
        self.assertEqual(a["usd"]["kpis"]["monthly"][-1]["end_date"], "2026-03-04T16:33")

    def test_csv_writes_the_live_point_as_date_and_time(self):
        p = analysis.build(self.raw(), None, dt.date(2026, 3, 4), live={"EGP=X": 52.52}, live_key="2026-03-04T16:33")
        rows = collect.to_csv(p).decode("utf-8").splitlines()
        self.assertTrue(rows[-1].startswith("2026-03-04 16:33,52.52"))
        self.assertTrue(rows[-2].startswith("2026-03-04,52.0"))

    def test_without_live_nothing_changes(self):
        p = analysis.build(self.raw(), None, dt.date(2026, 3, 4))
        self.assertIsNone(p["live_key"])
        self.assertEqual(p["grid"]["dates"][-1], "2026-03-04")

    def test_overlay_and_freshness(self):
        today = dt.date.today()
        now = dt.datetime.now()
        fx = {"usd": 52.5, "eur": 59.0, "gbp": 70.0, "source": "coinbase", "at": now.isoformat(timespec="seconds")}
        metals = {"XAU": {"price": 4000.0}, "at": (now - dt.timedelta(minutes=1)).isoformat(timespec="seconds")}
        values, key = collect.live_overlay(fx, metals, today)
        self.assertAlmostEqual(values["EURUSD=X"], 59.0 / 52.5)
        self.assertEqual(values["GC=F"], 4000.0)
        self.assertNotIn("SI=F", values)
        self.assertEqual(key, today.isoformat() + "T" + now.strftime("%H:%M"))
        self.assertEqual(collect.live_overlay(None, None, today), (None, None))
        old = dict(fx, at=(now - dt.timedelta(hours=4)).isoformat(timespec="seconds"))
        self.assertIsNone(collect._fresh(old, today))
        self.assertIsNone(collect._fresh(fx, today - dt.timedelta(days=1)))
        self.assertIsNotNone(collect._fresh(fx, today))


class LiveEndToEnd(unittest.TestCase):
    """get_payload and live_payload with a saved store and fake live sources."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.old_path = collect.STORE_PATH
        collect.STORE_PATH = os.path.join(self.tmp, "store.json")
        collect._fx, collect._metals, collect._shops = Throttle(300), Throttle(60), Throttle(600)
        today = dt.date.today()
        days = [(today - dt.timedelta(days=n)).isoformat() for n in (3, 2, 1, 0)]
        st = collect._empty_store(today.year)
        base = {"EGP=X": 50.0, "EURUSD=X": 1.1, "GBPUSD=X": 1.3, "GC=F": 3110.34768, "SI=F": 31.1034768}
        for sym, v in base.items():
            st["series"][sym] = {d: v for d in days}
            st["sources"][sym] = "daily"
        st["fetched_at"] = dt.datetime.now().isoformat(timespec="seconds")
        with open(collect.STORE_PATH, "w") as fh:
            json.dump(st, fh)
        self.calls = {"coinbase": 0, "gold": 0}

    def tearDown(self):
        collect.STORE_PATH = self.old_path
        collect._fx, collect._metals, collect._shops = Throttle(300), Throttle(60), Throttle(600)

    def patched(self):
        def coinbase():
            self.calls["coinbase"] += 1
            return {"usd": 50.5, "eur": 55.55, "gbp": 65.65, "source": "coinbase"}

        def gold(code):
            self.calls["gold"] += 1
            return {"price": 3141.4511568 if code == "XAU" else 31.1034768, "updated_at": "t"}

        p = mock.patch.object
        down = FetchError("offline test")
        return [p(collect.sources, "coinbase_fx", coinbase), p(collect.sources, "live_price", gold),
                p(collect.sources, "local_gold_snapshot", return_value={"error": "offline"}),
                p(collect.sources, "daily_history", side_effect=down), p(collect.sources, "yahoo_history", side_effect=down),
                p(collect.sources, "frankfurter_usd_cross", side_effect=down), p(collect.time, "sleep")]

    def test_payload_shows_live_now_and_refresh_is_throttled(self):
        patches = self.patched()
        for x in patches:
            x.start()
        try:
            p = collect.get_payload()
            usd = next(a for a in p["assets"] if a["key"] == "usd")
            self.assertAlmostEqual(usd["kpis"]["end"], 50.5)
            self.assertAlmostEqual(usd["kpis"]["change_1d_pct"], 1.0)
            self.assertEqual(p["live"]["fx_source"], "coinbase")
            self.assertTrue(p["grid"]["dates"][-1].startswith(dt.date.today().isoformat() + "T"))
            gold = next(a for a in p["assets"] if a["key"] == "gold_24")
            self.assertAlmostEqual(gold["kpis"]["end"], 101.0 * 50.5, places=6)
            for _ in range(20):  # twenty quick Refresh clicks
                collect.get_payload(force=True)
            for _ in range(20):  # the live strip polling
                collect.live_payload()
            self.assertEqual(self.calls["coinbase"], 1)
            self.assertEqual(self.calls["gold"], 2)  # one request per metal
            live = collect.live_payload()
            self.assertAlmostEqual(live["fx"]["usd"], 50.5)
            self.assertAlmostEqual(live["metals"]["XAU"]["usd_oz"], 3141.4511568)
            self.assertEqual(live["fx_daily"], 50.0)
        finally:
            for x in patches:
                x.stop()

    def test_live_sources_down_fall_back_to_daily(self):
        p = mock.patch.object
        down = FetchError("offline test")
        with p(collect.sources, "daily_history", side_effect=down), p(collect.sources, "yahoo_history", side_effect=down), \
                p(collect.sources, "frankfurter_usd_cross", side_effect=down), p(collect.time, "sleep"), \
                p(collect.sources, "coinbase_fx", side_effect=FetchError("down")), \
                p(collect.sources, "wise_fx", side_effect=FetchError("down")), \
                p(collect.sources, "live_price", side_effect=FetchError("down")), \
                p(collect.sources, "local_gold_snapshot", return_value={"error": "offline"}):
            payload = collect.get_payload()
            live = collect.live_payload()
        self.assertIsNone(payload["live"])
        self.assertIsNone(payload["live_key"])
        self.assertEqual(next(a for a in payload["assets"] if a["key"] == "usd")["kpis"]["end"], 50.0)
        self.assertIsNone(live["fx"])
        self.assertEqual(live["metals"], {})
        self.assertGreater(collect._fx.retry_after, 0)  # backing off, not retrying on every call



class RefreshStorm(unittest.TestCase):
    """Clicking Refresh over and over must not re-download the daily rates more than once a minute."""

    def test_forced_updates_are_spaced(self):
        tmp = tempfile.mkdtemp()
        old = collect.STORE_PATH
        collect.STORE_PATH = os.path.join(tmp, "store.json")
        collect._fx, collect._metals, collect._shops = Throttle(300), Throttle(60), Throttle(600)
        calls = []
        today = dt.date.today()

        def daily(start, end):
            calls.append(start)
            d = today.isoformat()
            return {"EGP=X": {d: 50.0}, "EURUSD=X": {d: 1.1}, "GBPUSD=X": {d: 1.3}, "GC=F": {d: 3000.0}, "SI=F": {d: 30.0}}

        p = mock.patch.object
        try:
            with p(collect.sources, "daily_history", daily), p(collect.sources, "local_gold_snapshot", return_value={"error": "x"}), \
                    p(collect.sources, "coinbase_fx", side_effect=FetchError("x")), p(collect.sources, "wise_fx", side_effect=FetchError("x")), \
                    p(collect.sources, "live_price", side_effect=FetchError("x")):
                for _ in range(30):
                    collect.get_payload(force=True)
            self.assertEqual(len(calls), 1)
        finally:
            collect.STORE_PATH = old
            collect._fx, collect._metals, collect._shops = Throttle(300), Throttle(60), Throttle(600)


class DailyStatistics(unittest.TestCase):
    """The live point is the latest price, but not an extra day in daily statistics."""

    def test_average_and_daily_swing_ignore_the_live_point(self):
        days = ["2025-12-31", "2026-03-02", "2026-03-03", "2026-03-04"]
        usd = [50.0, 51.0, 50.5, 52.0]
        raw = {"EGP=X": dict(zip(days, usd))}
        p = analysis.build(raw, None, dt.date(2026, 3, 4), live={"EGP=X": 60.0}, live_key="2026-03-04T16:33")
        k = p["assets"][0]["kpis"]
        self.assertAlmostEqual(k["end"], 60.0)
        self.assertAlmostEqual(k["average"], (51.0 + 50.5 + 52.0) / 3)
        rets = [usd[i] / usd[i - 1] - 1 for i in range(1, len(usd))]
        self.assertAlmostEqual(k["daily_volatility_pct"], statistics.stdev(rets) * 100)
        self.assertEqual(k["prev_date"], "2026-03-04")
        self.assertAlmostEqual(k["change_1d_pct"], (60.0 / 52.0 - 1) * 100)
        self.assertEqual((k["high"], k["high_date"]), (60.0, "2026-03-04T16:33"))  # "highest this year" includes now


class FetchHelper(unittest.TestCase):
    def test_no_wait_after_the_last_attempt(self):
        import urllib.error
        from tracker import fetch

        with mock.patch.object(fetch.urllib.request, "urlopen", side_effect=urllib.error.URLError("down")), \
                mock.patch.object(fetch.time, "sleep") as sleep:
            with self.assertRaises(FetchError):
                fetch.get("https://example.invalid/x", retries=1)
            self.assertEqual(sleep.call_count, 0)
            with self.assertRaises(FetchError):
                fetch.get("https://example.invalid/x", retries=2)
            self.assertEqual(sleep.call_count, 1)  # only between the two attempts


class ParallelLive(unittest.TestCase):
    def tearDown(self):
        collect._fx, collect._metals = Throttle(300), Throttle(60)

    def test_currencies_and_metals_are_asked_at_the_same_time(self):
        collect._fx, collect._metals = Throttle(300), Throttle(60)
        both = threading.Barrier(2, timeout=5)  # passes only if the two requests are in flight together

        def coinbase():
            both.wait()
            return {"usd": 50.5, "eur": 55.55, "gbp": 65.65, "source": "coinbase"}

        def metal(code):
            if code == "XAU":
                both.wait()
            return {"price": 3000.0, "updated_at": "t"}

        today = dt.date.today().isoformat()
        store = {"series": {"EGP=X": {today: 50.0}, "EURUSD=X": {today: 1.1}, "GBPUSD=X": {today: 1.3}}}
        with mock.patch.object(collect.sources, "coinbase_fx", coinbase), mock.patch.object(collect.sources, "live_price", metal):
            fx, metals = collect.live_rates(store, dt.date.today(), force=True)
        self.assertIsNotNone(fx)
        self.assertEqual(metals["XAU"]["price"], 3000.0)



class ShopPoliteness(unittest.TestCase):
    """The gold shop pages are scraped at most every 10 minutes, however often the daily data is updated."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.old = collect.STORE_PATH
        collect.STORE_PATH = os.path.join(self.tmp, "store.json")
        collect._fx, collect._metals, collect._shops = Throttle(300), Throttle(60), Throttle(600)

    def tearDown(self):
        collect.STORE_PATH = self.old
        collect._fx, collect._metals, collect._shops = Throttle(300), Throttle(60), Throttle(600)

    def test_daily_updates_reuse_recent_shop_prices(self):
        today = dt.date.today()
        reads = []

        def shops():
            reads.append(1)
            return {"source": "shop", "fetched_at": dt.datetime.now().isoformat(timespec="seconds"),
                    "karats": {"21": {"sell": 4000, "buy": 3950}}}

        def daily(start, end):
            d = today.isoformat()
            return {"EGP=X": {d: 50.0}, "EURUSD=X": {d: 1.1}, "GBPUSD=X": {d: 1.3}, "GC=F": {d: 3000.0}, "SI=F": {d: 30.0}}

        p = mock.patch.object
        with p(collect.sources, "daily_history", daily), p(collect.sources, "local_gold_snapshot", shops), \
                p(collect.sources, "coinbase_fx", side_effect=FetchError("x")), p(collect.sources, "wise_fx", side_effect=FetchError("x")), \
                p(collect.sources, "live_price", side_effect=FetchError("x")), p(collect, "MIN_FORCED_SECONDS", 0):
            for _ in range(10):  # ten forced daily updates in a row
                payload = collect.get_payload(force=True)
        self.assertEqual(len(reads), 1)
        self.assertEqual(payload["local"]["rows"][0]["sell"], 4000)

    def test_failed_reading_marks_saved_prices_as_older(self):
        old = {"source": "shop", "fetched_at": "2026-01-01T10:00:00", "karats": {"21": {"sell": 4000, "buy": 3950}}}
        with mock.patch.object(collect.sources, "local_gold_snapshot", return_value={"error": "down"}):
            got = collect.shop_snapshot({"local": old})
        self.assertTrue(got["stale"])
        self.assertEqual(got["karats"], old["karats"])
        with mock.patch.object(collect.sources, "local_gold_snapshot", return_value={"error": "down"}):
            collect._shops = Throttle(600)
            self.assertIn("error", collect.shop_snapshot({"local": None}))



class OfflineRetries(unittest.TestCase):
    """Offline with saved prices: answer at once from the store, and only retry the sources now and then."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.old = collect.STORE_PATH
        collect.STORE_PATH = os.path.join(self.tmp, "store.json")
        collect._fx, collect._metals, collect._shops = Throttle(300), Throttle(60), Throttle(600)
        collect._last_failed = 0.0
        today = dt.date.today()
        st = collect._empty_store(today.year)
        for sym, v in {"EGP=X": 50.0, "EURUSD=X": 1.1, "GBPUSD=X": 1.3, "GC=F": 3000.0, "SI=F": 30.0}.items():
            st["series"][sym] = {today.isoformat(): v}
            st["sources"][sym] = "daily"
        st["fetched_at"] = (dt.datetime.now() - dt.timedelta(hours=1)).isoformat(timespec="seconds")
        with open(collect.STORE_PATH, "w") as fh:
            json.dump(st, fh)

    def tearDown(self):
        collect.STORE_PATH = self.old
        collect._fx, collect._metals, collect._shops = Throttle(300), Throttle(60), Throttle(600)
        collect._last_failed = 0.0

    def test_refresh_while_offline_is_instant_and_spaced(self):
        calls = []

        def daily(start, end):
            calls.append(1)
            raise FetchError("offline")

        p = mock.patch.object
        down = FetchError("offline")
        with p(collect.sources, "daily_history", daily), p(collect.sources, "yahoo_history", side_effect=down), \
                p(collect.sources, "frankfurter_usd_cross", side_effect=down), p(collect.time, "sleep"), \
                p(collect.sources, "local_gold_snapshot", return_value={"error": "offline"}), \
                p(collect.sources, "coinbase_fx", side_effect=down), p(collect.sources, "wise_fx", side_effect=down), \
                p(collect.sources, "live_price", side_effect=down):
            first = collect.get_payload()
            for _ in range(10):  # Refresh clicked again and again
                again = collect.get_payload(force=True)
            self.assertEqual(len(calls), 1)
            self.assertEqual((first["notice"], again["notice"]), ("offline", "offline"))
            self.assertEqual(again["assets"][0]["kpis"]["end"], 50.0)
            collect._last_failed -= 61  # a minute later, Refresh tries the sources again
            collect.get_payload(force=True)
            self.assertEqual(len(calls), 2)
            collect.get_payload()  # but a normal page load waits 5 minutes between tries
            self.assertEqual(len(calls), 2)
            collect._last_failed -= 5 * 60
            collect.get_payload()
            self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
