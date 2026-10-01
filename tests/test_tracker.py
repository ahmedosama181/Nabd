"""Offline tests: python3 -m unittest discover -s tests   (no network needed)."""
import datetime as dt
import os
import unittest

from tracker import analysis, collect, sources

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def read(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as fh:
        return fh.read()


class Parsing(unittest.TestCase):
    def test_gold_price_today(self):
        k = sources.parse_karats(read("gold_price_today.txt"), sources._RE_GPT)
        self.assertEqual(k["21"], {"sell": 6160.0, "buy": 6110.0})
        self.assertEqual(set(k), {"24", "21", "18", "14"})

    def test_edahab(self):
        k = sources.parse_karats(read("edahab.txt"), sources._RE_EDAHAB)
        self.assertEqual(k["24"], {"sell": 7017.0, "buy": 6994.0})

    def test_arabic_digits_and_html(self):
        text = sources.html_to_text("<script>x</script><p>عيار 21 ٦٬١٦٠ جنيه ٦٬١١٠ جنيه</p>")
        self.assertEqual(sources.parse_karats(text, sources._RE_GPT)["21"]["sell"], 6160.0)

    def test_yahoo_skips_nulls_and_uses_exchange_offset(self):
        payload = {"chart": {"result": [{"meta": {"gmtoffset": -14400},
                                         "timestamp": [1775016000, 1775102400, 1775188800],
                                         "indicators": {"quote": [{"close": [10.0, None, 12.0]}]}}]}}
        self.assertEqual(sources.parse_yahoo(payload), {"2026-04-01": 10.0, "2026-04-03": 12.0})


class Math(unittest.TestCase):
    def test_add_months_clamps_day(self):
        self.assertEqual(analysis.add_months(dt.date(2026, 8, 31), -6), dt.date(2026, 2, 28))

    def test_kpis_and_mom_from_prev_close(self):
        base = ("2025-12-31", 100.0)
        pts = [("2026-01-15", 99.0), ("2026-01-30", 110.0), ("2026-02-27", 121.0), ("2026-03-02", 60.5)]
        k = analysis.compute_kpis(pts, dt.date(2026, 3, 2), base)
        self.assertTrue(k["start_is_prev_close"])
        self.assertEqual(k["start_date"], "2025-12-31")
        self.assertAlmostEqual(k["change_pct"], -39.5)
        self.assertAlmostEqual(k["change_1d_pct"], -50.0)
        m = {x["month"]: x for x in k["monthly"]}
        self.assertEqual(list(m), ["2026-01", "2026-02", "2026-03"])   # December is only the baseline
        self.assertAlmostEqual(m["2026-01"]["change_pct"], 10.0)         # 31 Dec 100 -> 30 Jan 110
        self.assertAlmostEqual(m["2026-02"]["change_pct"], 10.0)
        self.assertTrue(m["2026-03"]["partial"])
        self.assertEqual(k["low"], 60.5)
        self.assertEqual(k["high"], 121.0)
        self.assertEqual(k["n_days"], 4)

    def test_kpis_on_new_years_day_with_only_baseline(self):
        k = analysis.compute_kpis([], dt.date(2027, 1, 1), ("2026-12-31", 50.0))
        self.assertEqual(k["end"], 50.0)
        self.assertAlmostEqual(k["change_pct"], 0.0)
        self.assertEqual(k["n_days"], 0)
        self.assertIsNone(analysis.compute_kpis([], dt.date(2027, 1, 1), None))

    def _raw(self):
        days = ["2025-12-30", "2025-12-31", "2026-01-02", "2026-02-02", "2026-03-02"]
        return {
            "EGP=X": dict(zip(days, [49.0, 50.0, 51.0, 52.0, 55.0])),
            "GC=F": dict(zip(days, [3110.34768] * 5)),
            "SI=F": dict(zip(days, [31.1034768] * 5)),
            "EURUSD=X": dict(zip(days, [1.1] * 5)),
            "GBPUSD=X": dict(zip(days, [1.3] * 5)),
        }

    def test_build_ytd_prices_and_decomposition(self):
        p = analysis.build(self._raw(), None, dt.date(2026, 3, 2))
        a = {x["key"]: x for x in p["assets"]}
        # 3110.34768 USD/oz = 100 USD/g -> 24k EGP/g = 100 x USD/EGP; base = 31 Dec close
        self.assertAlmostEqual(a["gold_24"]["kpis"]["start"], 100 * 50.0, places=4)
        self.assertAlmostEqual(a["gold_21"]["kpis"]["end"], 100 * 55.0 * 21 / 24, places=4)
        self.assertAlmostEqual(a["usd"]["kpis"]["change_pct"], 10.0)
        self.assertAlmostEqual(a["eur"]["kpis"]["end"], 1.1 * 55.0, places=4)
        d = a["gold_24"]["drivers"]
        self.assertAlmostEqual((1 + d["base_pct"] / 100) * (1 + d["fx_pct"] / 100) - 1, a["gold_24"]["kpis"]["change_pct"] / 100, places=9)
        self.assertEqual(p["grid"]["dates"], ["2025-12-31", "2026-01-02", "2026-02-02", "2026-03-02"])
        self.assertEqual(p["grid"]["series"]["usd"][0], 50.0)

    def test_missing_source_is_reported_not_fatal(self):
        raw = self._raw(); del raw["SI=F"]
        p = analysis.build(raw, None, dt.date(2026, 3, 2))
        self.assertTrue(any("Silver" in w for w in p["warnings"]))
        self.assertNotIn("silver", {a["key"] for a in p["assets"]})

    def test_local_gap(self):
        local = {"source": "x", "karats": {"21": {"sell": 5000.0, "buy": 4900.0}}}
        p = analysis.build(self._raw(), local, dt.date(2026, 3, 2))
        row = p["local"]["rows"][0]
        self.assertAlmostEqual(row["derived"], 100 * 55.0 * 21 / 24)
        self.assertFalse(row["suspect"])

    def test_csv_has_bom_and_header(self):
        p = analysis.build(self._raw(), None, dt.date(2026, 3, 2))
        out = collect.to_csv(p).decode("utf-8")
        self.assertTrue(out.startswith("\ufeffDate,US Dollar (EGP)"))
        self.assertEqual(len(out.strip().splitlines()), 5)
        self.assertTrue(collect.to_csv(p, "ar").decode("utf-8").startswith("\ufeffالتاريخ"))


class Store(unittest.TestCase):
    def test_fetch_start_incremental_with_overlap(self):
        today = dt.date(2026, 10, 1)
        self.assertEqual(collect.fetch_start({}, today), dt.date(2025, 12, 20))
        self.assertEqual(collect.fetch_start({"2026-09-30": 1.0, "2026-01-02": 1.0}, today), dt.date(2026, 9, 26))
        self.assertEqual(collect.fetch_start({"2025-12-31": 1.0}, today), dt.date(2025, 12, 27))

    def test_prune_keeps_year_and_single_baseline(self):
        s = {"2025-12-29": 1, "2025-12-30": 2, "2026-01-02": 3}
        self.assertEqual(collect.prune(s, dt.date(2026, 5, 1)), {"2025-12-30": 2, "2026-01-02": 3})

    def test_new_year_wipes_store(self):
        import json, tempfile
        tmp = tempfile.mkdtemp()
        old = collect.STORE_PATH
        collect.STORE_PATH = os.path.join(tmp, "store.json")
        try:
            st = collect._empty_store(2026); st["series"]["EGP=X"] = {"2026-05-01": 50.0}
            with open(collect.STORE_PATH, "w") as fh:
                json.dump(st, fh)
            self.assertEqual(collect.load_store(dt.date(2026, 6, 1))["series"]["EGP=X"], {"2026-05-01": 50.0})
            self.assertEqual(collect.load_store(dt.date(2027, 1, 1))["series"]["EGP=X"], {})
        finally:
            collect.STORE_PATH = old


class Sources(unittest.TestCase):
    """update() with fake sources: which source is used, and whole-year re-downloads on a source change."""

    def setUp(self):
        from unittest import mock
        self.mock = mock
        self.today = dt.date(2026, 3, 4)
        days = ["2025-12-30", "2025-12-31", "2026-01-02", "2026-03-03", "2026-03-04"]
        self.daily = {k: dict(zip(days, [1.0 + i for i in range(5)])) for k in collect.SYMBOLS}
        self.yahoo = {k: dict(zip(days, [10.0 + i for i in range(5)])) for k in collect.SYMBOLS}
        self.calls = []

    def run_update(self, store, daily_ok=True, yahoo_ok=True):
        from tracker.fetch import FetchError

        def fake_daily(start, end):
            self.calls.append(("daily", start))
            if not daily_ok:
                raise FetchError("down")
            return {k: {d: v for d, v in s.items() if d >= start.isoformat()} for k, s in self.daily.items()}

        def fake_yahoo(sym, start, end):
            self.calls.append(("yahoo", sym, start))
            if not yahoo_ok:
                raise FetchError("HTTP 429")
            return {d: v for d, v in self.yahoo[sym].items() if d >= start.isoformat()}

        p = self.mock.patch
        with p.object(collect.sources, "daily_history", fake_daily), p.object(collect.sources, "yahoo_history", fake_yahoo), \
                p.object(collect.sources, "frankfurter_usd_cross", side_effect=FetchError("down")), \
                p.object(collect.sources, "local_gold_snapshot", return_value={"error": "x"}), p.object(collect.time, "sleep"):
            return collect.update(store, self.today)

    def test_daily_rates_are_the_primary_source(self):
        store = collect._empty_store(2026)
        self.run_update(store)
        self.assertEqual(set(store["sources"].values()), {"daily"})
        self.assertFalse([c for c in self.calls if c[0] == "yahoo"])
        self.assertEqual(store["series"]["EGP=X"], {"2025-12-31": 2.0, "2026-01-02": 3.0, "2026-03-03": 4.0, "2026-03-04": 5.0})

    def test_backup_source_redownloads_the_whole_year_instead_of_mixing(self):
        store = collect._empty_store(2026)
        self.run_update(store)                      # year from the daily rates
        self.calls.clear()
        self.run_update(store, daily_ok=False)      # daily rates down -> Yahoo, whole year
        self.assertEqual(store["sources"]["GC=F"], "yahoo")
        self.assertEqual(store["series"]["GC=F"]["2026-01-02"], 12.0)  # old daily values replaced, not mixed
        self.assertIn(("yahoo", "GC=F", dt.date(2025, 12, 20)), self.calls)
        self.calls.clear()
        self.run_update(store)                      # daily rates back -> whole year again from them
        self.assertEqual(store["sources"]["GC=F"], "daily")
        self.assertEqual(store["series"]["GC=F"]["2026-01-02"], 3.0)
        self.assertIn(("daily", dt.date(2025, 12, 20)), self.calls)

    def test_all_sources_down_reports_errors(self):
        store = collect._empty_store(2026)
        self.run_update(store, daily_ok=False, yahoo_ok=False)
        self.assertFalse(any(s["ok"] for s in store["status"].values()))
        self.assertIn("yahoo_blocked_until", store)

    def test_old_source_labels_are_understood(self):
        self.assertEqual(collect.source_id("currency-api (fallback, spot price)"), "daily")
        self.assertEqual(collect.source_id("Yahoo Finance"), "yahoo")
        self.assertEqual(collect.source_id("Frankfurter (ECB) - fallback"), "frankfurter")
        self.assertIsNone(collect.source_id(None))


if __name__ == "__main__":
    unittest.main()
