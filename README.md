<div align="center">

<img src="docs/logo.svg" width="88" alt="Nabd logo">

# Nabd · نبض

**The Egyptian pound market pulse.** Gold, silver, US dollar, euro and pound sterling, priced in Egyptian pounds, year to date, explained in plain words.

[![Tests](https://github.com/ahmedosama181/nabd/actions/workflows/tests.yml/badge.svg)](https://github.com/ahmedosama181/nabd/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![macOS | Windows](https://img.shields.io/badge/runs%20on-macOS%20%7C%20Windows-lightgrey.svg)
![English | العربية](https://img.shields.io/badge/language-English%20%7C%20%D8%A7%D9%84%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9-orange.svg)

**[⬇ Download Nabd (ZIP, about 130 KB)](https://github.com/ahmedosama181/Nabd/releases/latest/download/Nabd.zip)** · [Releases](https://github.com/ahmedosama181/nabd/releases/latest) · [How to run it](#-quick-start) · [بالعربي](#-بالعربي)

<img src="docs/screenshots/dashboard-en-dark.png" alt="Nabd dashboard in English, dark theme" width="100%">

</div>

## ✨ What it does

Nabd is a small app that runs on your own computer and opens in your browser. It shows how the prices Egyptians care about have moved since the start of the year, in language anyone can follow.

- **Live prices**: the cards and charts end at the live price, and a live strip shows real-time gold and silver, gold per gram in EGP for your karat, the dollar, euro and pound in EGP, and what Egyptian gold shops sell and buy at. Live prices update only while you are using the page.
- **Plain-language summary and insights**: what rose most and fell most, whether the pound got stronger or weaker, the year's peak and how far below it gold is now, the most jumpy and most stable asset, streaks.
- **Five price cards**: the live price, % up or down this year, the 31 December price, a trend line and today's change.
- **One chart, three views**: *Price* (with the year's highest and lowest points marked), *Compare all* (everything starts at 100), *Month by month*. Every tooltip shows the % change. Save any chart as an image.
- **"How much is it worth?"**: grams of gold (24k / 21k / 18k), Egyptian gold pounds (8 g of 21k), silver or foreign cash, converted to EGP, with what a gold shop would pay and the change since 31 December. Or the reverse: what your budget buys.
- **"What if?"**: what an amount would be worth today if you had put it into each asset on 31 December, compared with keeping cash.
- **All the numbers** for those who want them: change over 1 / 7 / 30 days, highs and lows, averages, daily swing, biggest drop, best and worst month, what moved each price, daily data table, CSV export for Excel.
- **English and Arabic**, with a true right-to-left layout in Arabic (numbers stay 0-9), light / dark / automatic theme, phone-friendly.

<table>
<tr>
<td width="62%"><img src="docs/screenshots/dashboard-ar-light.png" alt="Nabd in Arabic, light theme"></td>
<td width="38%"><img src="docs/screenshots/mobile-en.png" alt="Nabd on a phone"></td>
</tr>
<tr><td colspan="2"><img src="docs/screenshots/tools-en.png" alt="Calculator and What if tools"></td></tr>
</table>

## 🚀 Quick start

1. **[Download Nabd.zip](https://github.com/ahmedosama181/Nabd/releases/latest/download/Nabd.zip)** and unzip it. It holds only the files needed to run Nabd; there is no installer.
2. Open the folder and start Nabd:

| | What to do | First time only |
|---|---|---|
| **macOS** | Double-click **`Start-Mac.command`** | macOS blocks downloaded scripts ("Apple could not verify…"). Open **System Settings → Privacy & Security**, scroll to *Security* and click **Open Anyway**. On macOS 15+ right-click → Open no longer works. |
| **Windows** | Double-click **`Start-Windows.bat`** | If SmartScreen says "Windows protected your PC", click **More info → Run anyway**. |

Your browser opens Nabd at `http://127.0.0.1:8765/`. To stop it, close the terminal window that opened with it.

**You don't need to install anything.** If the computer has no Python 3.8+, the launcher downloads a private, portable copy into the `runtime/` folder the first time (no admin password, nothing installed system-wide; delete the folder to remove it). Nabd itself only uses Python's standard library.

| | Portable Python | Integrity check |
|---|---|---|
| Windows | python.org "embeddable" Python 3.12.10 (~11 MB) | SHA-256 pinned in [`tools/bootstrap-windows.ps1`](tools/bootstrap-windows.ps1) |
| macOS | python-build-standalone 3.12.14 (Apple Silicon or Intel, ~20 MB) | SHA-256 checked against the release's `SHA256SUMS` |

Prefer the terminal? `python3 app.py` (macOS/Linux) or `py -3 app.py` (Windows). Options: `--port 9000`, `--no-browser`.

## 🔢 How the numbers are calculated

- **Gold and silver in EGP per gram** = global price in USD per ounce × USD/EGP ÷ 31.1035 (grams in a troy ounce). Gold 21k = 24k × 21/24, 18k = 24k × 18/24. Silver is pure (999). An Egyptian **gold pound** = 8 g of 21k.
- **Euro and pound sterling in EGP** = EUR/USD (or GBP/USD) × USD/EGP.
- **Year to date** = latest price vs the price on 31 December of last year.
- **Month by month** = each month's last price vs the previous month's last price (January starts from 31 December; the current month is marked "so far").
- Daily values are the rates published once a day (spot prices), not exchange closing prices. Weekends and holidays carry the last known price forward in the charts; the statistics use real trading days only.
- **Live price** = the last point of every chart and the price on every card: gold and silver from gold-api.com, the dollar, euro and pound from Coinbase (or Wise). These are market rates: a bank or exchange office buys a little lower and sells a little higher. **Today** = the live price vs the latest daily price (currency-api usually publishes it early in the morning, Cairo time). The live point is added on top of the daily history and is never saved; averages and the daily swing use daily prices only.

## 🌐 Data sources

| Data | Source | Notes |
|---|---|---|
| Daily history: USD/EGP, EUR, GBP, gold and silver | [currency-api](https://github.com/fawazahmed0/exchange-api) daily rate files (jsDelivr, mirrored on Cloudflare Pages) | Primary source; one consistent source for every series |
| Backup history | Yahoo Finance; Frankfurter (ECB) for EUR and GBP | Only if the daily rates can't be reached. Yahoo often answers scripts with HTTP 429 ([yfinance #2422](https://github.com/ranaroussi/yfinance/issues/2422)), so Nabd then skips it for 3 hours |
| Live gold and silver | [gold-api.com](https://gold-api.com/docs) | Free, no key |
| Live dollar, euro and pound | [Coinbase exchange rates](https://docs.cdp.coinbase.com/coinbase-app/track-apis/exchange-rates) | Public, no key ("This endpoint doesn't require authentication") |
| Backup for live currencies | Wise's public live rate (`wise.com/rates/live`) | No key; not officially documented. Used only when Coinbase doesn't answer or its rate looks wrong |
| Egyptian gold shop prices | www.gold-price-today.com/egypt, then edahabapp.com | Read from their public pages |

A saved price series never mixes sources: if one has to change, that series' whole year is downloaded again from the new source, so the charts never show a fake jump.

## ⚡ Live prices without getting blocked

Every live source goes through one polite gatekeeper ([`tracker/live.py`](tracker/live.py)):

| Source | While you use the page | The most it can ever be asked |
|---|---|---|
| gold-api.com | 2 requests a minute (gold, silver) | 4 a minute |
| Coinbase | 1 request every 5 minutes | 2 a minute |
| Gold shop page | 1 every 10 minutes | 1 every 10 minutes |
| Daily rates (jsDelivr) | a few small files every 30 minutes | a few small files a minute |

- Live prices are fetched when Nabd starts, when you press **Refresh** (honoured at most every 30 seconds, however often you click), and then once a minute **only while you are using the page**. Nothing is fetched while Nabd is on another tab, after 3 minutes without using it (1 minute if you are working in another window), or while the computer sleeps. The live strip then shows **PAUSED**, and fresh prices come the moment you are back.
- If a source fails or answers "too many requests", Nabd leaves it alone for 1 minute, then 2, 4, … up to 30 minutes, and keeps showing the last good price meanwhile. Only one request per source is ever in flight.
- A live currency rate more than 10% away from the latest daily rate is shown only if Coinbase and Wise agree within 1%. A live price from an earlier day, or older than 3 hours, is not shown as live.
- The sources' own limits: currency-api says "No Rate limits" ([README](https://github.com/fawazahmed0/exchange-api)); gold-api.com says "No Rate Limiting for real time prices" ([docs](https://gold-api.com/docs)); Coinbase publishes no limit for this public endpoint (its documented limit for API keys is 10,000 requests an hour, [rate limiting](https://docs.cdp.coinbase.com/coinbase-app/api-architecture/rate-limiting)).

## 🔒 Privacy

Nabd runs entirely on your computer. There are no accounts, no tracking and no analytics. It only downloads public prices from the sources above. Your settings stay in your browser, and the prices are saved in `data/store.json` (about 30 KB). Only the current year is kept, plus the 31 December price; on 1 January the saved prices are cleared and the new year starts fresh.

## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| macOS: "Apple could not verify…" | System Settings → Privacy & Security → **Open Anyway** (once). Or run `xattr -dr com.apple.quarantine ` followed by the Nabd folder in Terminal. |
| "TLS certificate check failed" (Mac with python.org Python) | Run `Install Certificates.command` from `/Applications/Python 3.x/` once. |
| Port 8765 is busy | Nabd picks the next free port and prints the address. |
| No internet | Nabd shows the last saved prices with a notice and tries again later. |
| A section is empty | That source didn't answer; everything else keeps working. Press **Refresh** later. |
| The live strip says **PAUSED** | Live prices pause while Nabd is on another tab or you are away. Move the mouse or tap the page and they update right away. |

## 🧑‍💻 For developers

The full source (tests, docs, screenshots) is in this repository: clone it or download [main.zip](https://github.com/ahmedosama181/Nabd/archive/refs/heads/main.zip).

```bash
python3 app.py --no-browser                     # run the server
python3 -m unittest discover -s tests -t .      # offline tests
python3 tools/build_release.py                  # build the small download: dist/Nabd.zip
```

Publishing a release on GitHub builds `Nabd.zip` and attaches it to the release automatically ([`.github/workflows/release.yml`](.github/workflows/release.yml)).

```
app.py              local web server (standard library only)
tracker/
  sources.py        data sources: daily rates, live prices, backups, gold-shop scraping
  collect.py        the yearly store, incremental updates, live prices, CSV export
  live.py           polite access to live sources: throttling, back-off, one request at a time
  analysis.py       EGP conversion and all KPIs (pure functions)
  fetch.py          small HTTP helper with retries
web/                the page: index.html, style.css, app.js (+ Chart.js in web/vendor)
tools/              portable-Python setup for Windows, release zip builder
Start-Mac.command   macOS launcher (also sets up Python if needed)
Start-Windows.bat   Windows launcher (also sets up Python if needed)
```

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). Version history is in [CHANGELOG.md](CHANGELOG.md).

## 🇪🇬 بالعربي

**نبض** أداة مجانية تعرض أسعار **الذهب والفضة والدولار واليورو والجنيه الإسترليني بالجنيه المصري منذ بداية العام**، مع شرح مبسّط ورسوم بيانية واضحة، وأسعار مباشرة، وحاسبة لقيمة الذهب (بالجرام أو الجنيه الذهب)، وتعمل باللغتين العربية والإنجليزية.

**طريقة التشغيل:**

1. [حمّل الملف المضغوط Nabd.zip](https://github.com/ahmedosama181/Nabd/releases/latest/download/Nabd.zip) وفك الضغط.
2. على **ماك**: اضغط مرتين على `Start-Mac.command`. في أول مرة: إعدادات النظام ← الخصوصية والأمان ← **فتح على أي حال**.
3. على **ويندوز**: اضغط مرتين على `Start-Windows.bat`. لو ظهرت رسالة الحماية: **More info ← Run anyway**.

لا تحتاج لتثبيت أي شيء: لو الجهاز ليس عليه بايثون، تقوم الأداة بتحميل نسخة خاصة بها تلقائياً في أول تشغيل. الأداة تعمل على جهازك فقط، بدون حسابات أو تتبع.

الأسعار المباشرة (الذهب والفضة والدولار واليورو والإسترليني) تتحدث فقط وأنت تستخدم الصفحة، وتتوقف تلقائياً عند الانتقال لتبويب آخر أو ترك الصفحة دون استخدام، ثم تتحدث فور رجوعك.

## 📄 License and contact

Released under the [MIT License](LICENSE) © 2026 **Ahmed Osama**. Third-party components and data services are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Questions, ideas or feedback: **[ahmedosama181@outlook.com](mailto:ahmedosama181@outlook.com)**, or open an [issue](https://github.com/ahmedosama181/nabd/issues).

> For information only, not financial advice. Prices come from free public sources and can differ from what a bank or shop quotes.
