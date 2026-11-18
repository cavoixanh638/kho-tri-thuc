import re
from collections.abc import Callable

from .models import Job


# Handlers may be run again after lease expiry. Keep side effects idempotent and
# bound I/O and subprocess timeouts to finish within the claim's lease_until.
def upload_original(job: Job) -> None:
    from storage.upload_job import upload_asset

    upload_asset(job)


HANDLERS: dict[str, Callable[[Job], None]] = {"upload_asset": upload_original}


class JobFailure(Exception):
    """A job outcome with a safe code suitable for persistence and logs."""

    def __init__(self, code: str, *, retryable: bool = True):
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", code):
            raise ValueError("Job failure codes must be short lowercase identifiers.")
        self.code = code
        self.retryable = retryable
        super().__init__(code)
