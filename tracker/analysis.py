"""Turn raw daily closes into EGP-denominated series and KPIs. Pure functions, no network."""
import bisect
import calendar
import datetime as dt
import statistics

OUNCE_G = 31.1034768  # grams per troy ounce


def add_months(day, n):
    month_index = day.year * 12 + (day.month - 1) + n
    year, month = divmod(month_index, 12)
    month += 1
    return dt.date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def _d(s):
    return dt.date.fromisoformat(s[:10])  # also accepts the live point's key, e.g. "2026-10-01T16:33"


class Lookup:
    """Last known value on or before a date (forward fill)."""

    def __init__(self, series):
        self.dates = sorted(series)
        self.series = series

    def at(self, day):
        day = day if isinstance(day, str) else day.isoformat()
        i = bisect.bisect_right(self.dates, day)
        return self.series[self.dates[i - 1]] if i else None


def _pct(new, old):
    return (new / old - 1.0) * 100.0 if old else None


def _month_label(ym):
    return dt.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%b %Y")


def compute_kpis(points, today, base=None):
    """points: ascending list of (date_str, value) in the current year.
    base: (date_str, value) of the previous year's last close - the YTD starting point - or None.
    Returns None when there is nothing at all to measure."""
    allp = ([base] if base else []) + list(points)
    if not allp:
        return None
    dates = [p[0] for p in allp]
    vals = [p[1] for p in allp]
    first, last = vals[0], vals[-1]
    body = points or allp  # high / low / average describe this year's trading days when there are any
    bvals = [p[1] for p in body]
    i_hi = max(range(len(bvals)), key=bvals.__getitem__)
    i_lo = min(range(len(bvals)), key=bvals.__getitem__)

    # Daily statistics (average, daily swing) use one price per day: a live point (its key has a time,
    # e.g. "2026-10-01T16:33") is not an extra day.
    dvals = [v for d, v in allp if len(d) == 10]
    rets = [dvals[i] / dvals[i - 1] - 1.0 for i in range(1, len(dvals))]
    vol = statistics.stdev(rets) * 100.0 if len(rets) > 2 else None
    avg_vals = [v for d, v in body if len(d) == 10] or bvals

    peak, max_dd = vals[0], 0.0
    for v in vals:
        peak = max(peak, v)
        max_dd = min(max_dd, v / peak - 1.0)

    last_day = _d(dates[-1])

    def change_over(days):
        target = (last_day - dt.timedelta(days=days)).isoformat()
        i = bisect.bisect_right(dates, target)
        return _pct(last, vals[i - 1]) if i else None  # None if history is shorter than the lookback

    # Month-over-month: each calendar month's last close vs the previous month's last close.
    # January is measured from the YTD starting point (31 Dec close, or the first close of the year).
    months, order = {}, []
    for d, v in points:
        ym = d[:7]
        if ym not in months:
            order.append(ym)
        months[ym] = (d, v)
    monthly = []
    base_date, base_val = dates[0], first
    for ym in order:
        end_date, end = months[ym]
        year, mon = int(ym[:4]), int(ym[5:7])
        partial = (year, mon) == (today.year, today.month) and today.day < calendar.monthrange(year, mon)[1]
        monthly.append(
            {
                "month": ym,
                "label": _month_label(ym),
                "base_date": base_date,
                "base": base_val,
                "end_date": end_date,
                "end": end,
                "change_pct": _pct(end, base_val),
                "partial": partial,
            }
        )
        base_date, base_val = end_date, end

    complete = [m for m in monthly if not m["partial"] and m["change_pct"] is not None]
    best = max(complete, key=lambda m: m["change_pct"]) if complete else None
    worst = min(complete, key=lambda m: m["change_pct"]) if complete else None

    return {
        "start_date": dates[0],
        "start": first,
        "start_is_prev_close": base is not None,
        "end_date": dates[-1],
        "end": last,
        "change_abs": last - first,
        "change_pct": _pct(last, first),
        "change_1d_pct": _pct(vals[-1], vals[-2]) if len(vals) > 1 else None,
        "prev_date": dates[-2] if len(dates) > 1 else None,  # what change_1d_pct compares with
        "change_7d_pct": change_over(7),
        "change_30d_pct": change_over(30),
        "high": bvals[i_hi],
        "high_date": body[i_hi][0],
        "low": bvals[i_lo],
        "low_date": body[i_lo][0],
        "average": statistics.fmean(avg_vals),
        "daily_volatility_pct": vol,
        "max_drawdown_pct": max_dd * 100.0,
        "monthly": monthly,
        "best_month": {"month": best["month"], "change_pct": best["change_pct"]} if best else None,
        "worst_month": {"month": worst["month"], "change_pct": worst["change_pct"]} if worst else None,
        "n_days": len(points),
    }


def _drivers(first_date, last_date, base_lookup, fx, base_label):
    """Split an EGP price change into 'global/base move' x 'USD/EGP move' (they multiply exactly)."""
    b0, b1 = base_lookup.at(first_date), base_lookup.at(last_date)
    x0, x1 = fx.at(first_date), fx.at(last_date)
    if None in (b0, b1, x0, x1):
        return None
    return {"base_label": base_label, "base_pct": _pct(b1, b0), "fx_pct": _pct(x1, x0)}


def build(raw, local, today, live=None, live_key=None):
    """raw: {symbol: {date: close}} covering the current year plus a few days of December
    (for the previous year's last close). Returns the JSON payload the UI renders.

    live: optional {symbol: value} read just now; it is added as one extra, last point under live_key
    (e.g. "2026-10-01T16:33"), after today's daily value, so "today" compares the live price with the latest
    daily price. With a live dollar rate, every other series also gets a "now" point (its latest global price
    at the live dollar rate). The daily history itself is never changed."""
    if live and live_key:
        raw = {sym: dict(series) for sym, series in raw.items()}
        for sym, value in live.items():
            if sym in raw and raw[sym] and value:
                raw[sym][live_key] = value
        if live.get("EGP=X"):  # with a live dollar rate, "now" for everything else uses it too
            for sym, series in raw.items():
                if series and live_key not in series:
                    series[live_key] = series[max(series)]
    start_s = dt.date(today.year, 1, 1).isoformat()
    base_label_date = dt.date(today.year - 1, 12, 31).isoformat()
    warnings = []

    fx_raw = raw.get("EGP=X")
    if not fx_raw:
        raise ValueError("USD/EGP history is unavailable, so nothing can be priced in EGP.")
    fx = Lookup(fx_raw)

    def convert(series, factor):
        out = {}
        for d, v in series.items():
            rate = fx.at(d)
            if rate is not None:
                out[d] = v * rate * factor
        return out

    specs = []  # (key, label, group, unit, decimals, native {date: value}, driver label, driver lookup)
    specs.append(("usd", "US Dollar", "currency", "EGP", 2, dict(fx_raw), None, None))
    for key, label, sym in (("eur", "Euro", "EURUSD=X"), ("gbp", "British Pound", "GBPUSD=X")):
        cross = raw.get(sym)
        if not cross:
            warnings.append("%s history unavailable - %s skipped." % (sym, label))
            continue
        specs.append((key, label, "currency", "EGP", 2, convert(cross, 1.0), "%s vs USD" % key.upper(), Lookup(cross)))

    gold, silver = raw.get("GC=F"), raw.get("SI=F")
    if gold:
        gl = Lookup(gold)
        for karat in (24, 21, 18):
            specs.append(("gold_%d" % karat, "Gold %dk" % karat, "gold", "EGP/g", 0,
                          convert(gold, karat / 24.0 / OUNCE_G), "Global gold price (USD/oz)", gl))
        specs.append(("gold_oz_usd", "Gold, global", "reference", "USD/oz", 2, dict(gold), None, None))
    else:
        warnings.append("Gold history unavailable - gold skipped.")
    if silver:
        specs.append(("silver", "Silver", "silver", "EGP/g", 2, convert(silver, 1.0 / OUNCE_G),  # pure (999) silver
                      "Global silver price (USD/oz)", Lookup(silver)))
        specs.append(("silver_oz_usd", "Silver, global", "reference", "USD/oz", 2, dict(silver), None, None))
    else:
        warnings.append("Silver history unavailable - silver skipped.")

    assets, native, bases = [], {}, {}
    for key, label, group, unit, dec, pts, drv_label, drv_lookup in specs:
        before = sorted((d, v) for d, v in pts.items() if d < start_s)
        points = sorted((d, v) for d, v in pts.items() if d >= start_s)
        base = before[-1] if before else None
        k = compute_kpis(points, today, base)
        if k is None:
            warnings.append("%s: no data yet this year - skipped." % label)
            continue
        asset = {"key": key, "label": label, "group": group, "unit": unit, "decimals": dec, "kpis": k}
        if drv_lookup is not None:
            asset["drivers"] = _drivers(k["start_date"], k["end_date"], drv_lookup, fx, drv_label)
        assets.append(asset)
        native[key] = dict(points)
        bases[key] = base[1] if base else None

    # Shared daily grid for charts / table / CSV: column 0 is the 31 Dec starting point,
    # then every trading day of this year, gaps forward-filled.
    all_dates = sorted({d for pts in native.values() for d in pts})
    grid_dates = [base_label_date] + all_dates
    series = {}
    for key, pts in native.items():
        cur = bases[key]
        out = [round(cur, 4) if cur is not None else None]
        for d in all_dates:
            cur = pts.get(d, cur)
            out.append(round(cur, 4) if cur is not None else None)
        series[key] = out

    return {
        "year": today.year,
        "live_key": live_key if live and live_key and live_key in all_dates else None,
        "period": {"start": start_s, "end": max(all_dates) if all_dates else start_s, "base_date": base_label_date},
        "assets": assets,
        "grid": {"dates": grid_dates, "series": series},
        "local": _local_vs_derived(local, native.get("gold_24")),
        "warnings": warnings,
    }


def _local_vs_derived(local, gold24_points):
    """Compare scraped local gold prices with what the global price x USD/EGP implies today."""
    if not local or "error" in local:
        return local
    derived24 = gold24_points[max(gold24_points)] if gold24_points else None  # latest value this year
    rows = []
    for karat, prices in sorted(local["karats"].items(), key=lambda kv: -int(kv[0])):
        derived = derived24 * int(karat) / 24.0 if derived24 else None
        gap = _pct(prices["sell"], derived) if derived else None
        rows.append(
            {
                "karat": int(karat),
                "sell": prices["sell"],
                "buy": prices["buy"],
                "derived": derived,
                "gap_pct": gap,
                "suspect": gap is not None and abs(gap) > 15,  # likely a mis-parse - flagged in the UI
            }
        )
    return dict({k: v for k, v in local.items() if k != "karats"}, rows=rows)
