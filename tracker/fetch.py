"""Tiny HTTP helper (stdlib only) with retries and a clear message for macOS certificate problems."""
import os
import ssl
import time
import urllib.error
import urllib.request

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


class FetchError(Exception):
    pass


_CTX = None


def _context():
    """TLS context: certifi if installed, else the system store. A portable Python on macOS may not
    know where the system certificates live, so fall back to macOS's own bundle at /etc/ssl/cert.pem."""
    global _CTX
    if _CTX is None:
        try:
            import certifi  # type: ignore

            _CTX = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            _CTX = ssl.create_default_context()
            if not _CTX.cert_store_stats().get("x509_ca") and os.path.exists("/etc/ssl/cert.pem"):
                _CTX.load_verify_locations("/etc/ssl/cert.pem")
    return _CTX


def get(url, timeout=20, retries=2, accept="*/*"):
    """GET a URL and return the body as bytes. Raises FetchError after the last retry."""
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
            with urllib.request.urlopen(req, timeout=timeout, context=_context()) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            last = "HTTP %s" % exc.code
            if exc.code in (400, 403, 404):  # retrying will not help
                break
            if exc.code == 429:  # rate limited: retrying right away only makes it worse
                break
        except urllib.error.URLError as exc:
            reason = exc.reason
            if isinstance(reason, ssl.SSLCertVerificationError):
                raise FetchError(
                    "TLS certificate check failed. On a Mac with python.org Python, run "
                    "'Install Certificates.command' (in /Applications/Python 3.x/) and try again."
                )
            last = str(reason)
        except Exception as exc:  # timeouts, resets, ...
            last = "%s: %s" % (type(exc).__name__, exc)
        time.sleep(1.5 * (attempt + 1))
    raise FetchError("%s (%s)" % (url.split("?")[0], last))
