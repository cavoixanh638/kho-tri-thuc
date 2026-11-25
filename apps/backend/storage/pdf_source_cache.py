"""Short-lived, process-private copies of SHA-verified PDF source bytes."""

from threading import Lock, Timer
from time import monotonic


MAX_PDF_BYTES = 24 * 1024 * 1024


class VerifiedPdfCache:
    """At most two PDFs (48 MiB) per process. Expire even when the app is idle."""

    def __init__(self):
        self._entries = {}
        self._lock = Lock()

    def get(self, key):
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None and monotonic() < entry[0]:
                return entry[1]
        return None

    def remember(self, key, source):
        if len(source) > MAX_PDF_BYTES:
            return
        with self._lock:
            # A concurrent request can finish validating the same bytes first.
            if key in self._entries:
                return
            if len(self._entries) >= 2:
                _, _, old_timer = self._entries.pop(next(iter(self._entries)))
                old_timer.cancel()
            deadline = monotonic() + 90
            timer = Timer(90, self._expire, args=(key, deadline))
            timer.daemon = True
            self._entries[key] = (deadline, source, timer)
            timer.start()

    def _expire(self, key, deadline):
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None and entry[0] == deadline:
                del self._entries[key]
