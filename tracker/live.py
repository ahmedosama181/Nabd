"""Polite access to live prices: every source is asked rarely, never twice at once, and backs off after failures.

Rules (per source):
  * A cached value is reused until it is `min_interval` seconds old.
  * `force=True` (app start, the Refresh button) asks again right away, but never more often than once per
    `force_floor` seconds, however often Refresh is clicked.
  * After a failure the source is left alone for 1, 2, 4, ... minutes (at most `max_backoff`), even when
    forced, so a source that is down or rate-limiting us is never hammered. One success resets this.
  * Only one request per source is ever in flight: callers arriving meanwhile wait for it and share its result.
"""
import threading
import time


class Throttle:
    def __init__(self, min_interval, force_floor=30, base_backoff=60, max_backoff=30 * 60, clock=time.time):
        self.min_interval = min_interval
        self.force_floor = force_floor
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff
        self.clock = clock
        self.value = None          # last good value
        self.at = 0.0              # when the last good value was fetched
        self.last_try = 0.0        # when we last asked the source (success or not)
        self.failures = 0          # failures in a row
        self.retry_after = 0.0     # no request before this time (back-off)
        self.error = None
        self.calls = 0             # requests made (for tests and diagnostics)
        self._lock = threading.Lock()

    def due(self, force=False):
        now = self.clock()
        if now < self.retry_after:
            return False
        if self.value is None:
            return True  # nothing yet: ask (failures are already spaced out by the back-off above)
        if force:
            return now - self.last_try >= self.force_floor
        return now - self.at >= self.min_interval

    def get(self, fetch, force=False):
        """Return the freshest value allowed by the rules above (may be None if never fetched successfully)."""
        with self._lock:
            if self.due(force):
                now = self.clock()
                self.last_try = now
                self.calls += 1
                try:
                    value = fetch()
                    if value is None:
                        raise ValueError("no value")
                except Exception as exc:  # any failure: keep the old value, back off
                    self.failures += 1
                    self.error = "%s: %s" % (type(exc).__name__, exc)
                    self.retry_after = now + min(self.max_backoff, self.base_backoff * 2 ** (self.failures - 1))
                else:
                    self.value, self.at = value, now
                    self.failures, self.retry_after, self.error = 0, 0.0, None
            return self.value

    def age(self):
        return None if self.value is None else self.clock() - self.at
