# Third-party notices

## Bundled code

| Component | Version | License | Where |
|---|---|---|---|
| [Chart.js](https://www.chartjs.org) | 4.4.7 | MIT, © 2024 Chart.js Contributors | `web/vendor/chart.umd.js` (the license header is kept at the top of the file) |

## Downloaded at run time (not included in this repository)

| Component | Used for | License / terms |
|---|---|---|
| Python ([python.org](https://www.python.org) embeddable package for Windows, [python-build-standalone](https://github.com/astral-sh/python-build-standalone) for macOS) | Only when the computer has no Python 3.8+ | Python Software Foundation License |

## Data services

Nabd reads public data; it does not redistribute it. Each service keeps its own terms:

- [currency-api / exchange-api](https://github.com/fawazahmed0/exchange-api) (daily exchange, gold and silver rates)
- [gold-api.com](https://gold-api.com/docs) (live gold and silver prices)
- [Coinbase](https://docs.cdp.coinbase.com/coinbase-app/track-apis/exchange-rates) (live dollar, euro and pound rates, public exchange-rates endpoint)
- [Wise](https://wise.com) (backup for live currency rates)
- [Yahoo Finance](https://finance.yahoo.com) and [Frankfurter](https://frankfurter.dev) (backup history)
- www.gold-price-today.com and edahabapp.com (Egyptian gold shop prices)
