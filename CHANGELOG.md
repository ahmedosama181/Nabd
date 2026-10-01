# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-10-01

First public release.

### Added
- Year-to-date prices in Egyptian pounds for gold (24k / 21k / 18k), silver, US dollar, euro and pound sterling, from the 31 December price to today.
- Live prices: the cards and the last point of every chart show the live price, with "Today" measured from the latest daily price. Live strip with real-time gold and silver, gold per gram in EGP, the dollar, euro and pound in EGP (Coinbase, with Wise as a backup), and Egyptian gold shop sell/buy prices.
- Live prices are fetched at start, on Refresh and once a minute only while the page is in use; they pause on another tab, when the page is left idle and while the computer sleeps.
- Polite access to every live source: at most one request in flight, a minimum interval per source, Refresh honoured at most every 30 seconds, and growing back-off (1 to 30 minutes) after failures or HTTP 429.
- Plain-language summary and automatic insights.
- Price cards with trend lines; one chart with Price / Compare all / Month by month views, % change in every tooltip, highest/lowest markers, save as PNG.
- "How much is it worth?" calculator (grams, gold pounds, silver, foreign cash, budget mode) and "What if?" comparison.
- Detailed KPIs with explanations, what moved each price, daily table, CSV export (English or Arabic headers).
- English and Arabic with full right-to-left layout; light, dark and automatic themes; responsive layout without horizontal scrolling.
- Local yearly store with incremental updates; automatic refresh; offline mode with saved prices.
- One-double-click launchers for macOS and Windows that set up a private portable Python when none is installed.
