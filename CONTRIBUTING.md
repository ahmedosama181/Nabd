# Contributing to Nabd

Thanks for helping make Nabd better. Bug reports, ideas, translations and code are all welcome.

## Reporting a bug or asking for a feature

Open an [issue](https://github.com/ahmedosama181/nabd/issues/new/choose) and pick the right form. For bugs, please include your operating system, browser, language (EN/AR) and a screenshot if something looks wrong.

## Working on the code

Nabd deliberately has **no dependencies**: the server uses only the Python standard library (3.8+), and the page is plain HTML/CSS/JavaScript with Chart.js bundled in `web/vendor`. Please keep it that way, so it keeps starting with one double-click on any computer.

```bash
git clone https://github.com/ahmedosama181/nabd.git
cd nabd
python3 app.py                                  # opens http://127.0.0.1:8765/
python3 -m unittest discover -s tests -t .      # offline tests, must pass
```

Guidelines:

- **Both languages.** Every visible text lives in the `T.en` / `T.ar` dictionaries in `web/app.js`. Add both. Arabic uses right-to-left layout and Western digits (0-9).
- **No horizontal scrolling** at any width, from 360 px phones to wide monitors, in both languages.
- **Plain language.** The page is for people who are not finance experts; explain new numbers with a ⓘ hint.
- **Tests.** Add or update tests in `tests/` for changes to calculations, data sources or the saved store. Tests must not use the network.
- **Data sources.** Only free, public sources without API keys. Never mix two sources inside one saved price series (the live "now" point is added on top, labelled and never saved).
- **Be polite to sources.** Every live request goes through `tracker/live.py` (minimum interval, back-off, one request at a time), and the page only polls while someone is using it.
- **Small pull requests** with a clear description of what changed and how you checked it.

## Code of conduct

Be kind and respectful. Harassment or abusive behaviour is not tolerated in issues, pull requests or discussions.
