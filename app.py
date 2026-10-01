#!/usr/bin/env python3
"""Nabd (نبض) - Egyptian pound market pulse. Local dashboard. Standard library only (Python 3.8+).

    python3 app.py                 # start the dashboard (year to date) and open it in your browser
    python3 app.py --no-browser    # just print the URL
"""
import argparse
import datetime as dt
import json
import mimetypes
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # the portable Windows Python doesn't add it
from tracker import collect  # noqa: E402

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")


class Handler(BaseHTTPRequestHandler):
    server_version = "Nabd"

    def log_message(self, fmt, *args):  # keep the terminal quiet
        pass

    def _send(self, code, body, ctype, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json; charset=utf-8")

    def _payload(self, force):
        try:
            return collect.get_payload(force=force), None
        except Exception as exc:  # shown to the user in the page
            return None, str(exc)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/api/data":
            force = parse_qs(url.query).get("refresh", ["0"])[0] == "1"
            payload, err = self._payload(force)
            return self._json(200, payload) if payload else self._json(502, {"error": err})
        if url.path == "/api/live":
            try:
                return self._json(200, collect.live_payload())
            except Exception as exc:  # live prices are optional: the page simply hides the live strip
                return self._json(502, {"error": str(exc)})
        if url.path == "/api/export.csv":
            payload, err = self._payload(False)
            if not payload:
                return self._json(502, {"error": err})
            lang = parse_qs(url.query).get("lang", ["en"])[0]
            name = "nabd-%s.csv" % dt.date.today().isoformat()
            return self._send(200, collect.to_csv(payload, lang), "text/csv; charset=utf-8",
                              {"Content-Disposition": 'attachment; filename="%s"' % name})
        if url.path == "/favicon.ico":
            return self._send(204, b"", "image/x-icon")
        rel = "index.html" if url.path in ("/", "") else url.path.lstrip("/")
        full = os.path.realpath(os.path.join(WEB, rel))
        if not full.startswith(os.path.realpath(WEB) + os.sep) or not os.path.isfile(full):
            return self._send(404, b"Not found", "text/plain")
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        with open(full, "rb") as fh:
            self._send(200, fh.read(), ctype)


def main():
    ap = argparse.ArgumentParser(description="Nabd - gold, silver and currencies in Egyptian pounds")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    server = None
    for port in range(args.port, args.port + 20):  # pick the next free port if busy
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    if server is None:
        sys.exit("Could not find a free port near %d." % args.port)
    url = "http://127.0.0.1:%d/" % server.server_address[1]
    print("Nabd is running at %s  (close this window or press Ctrl+C to stop)" % url)
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
