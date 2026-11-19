import re
from collections.abc import Callable

from .models import Job


# Handlers may be run again after lease expiry. Keep side effects idempotent and
# bound I/O and subprocess timeouts to finish within the claim's lease_until.
def upload_original(job: Job) -> None:
    from storage.upload_job import upload_asset

    upload_asset(job)


def retrieve_source(job: Job) -> None:
    from processing.source_jobs import fetch_source_job

    fetch_source_job(job)


def organize(job: Job) -> None:
    from catalog.organization_job import organize_item

    organize_item(job)


def retrieve_video(job: Job) -> None:
    from processing.video_jobs import download_video

    download_video(job)


def export_knowledge(job: Job) -> None:
    from processing.knowledge_sync import export_knowledge as synchronize

    synchronize(job)


HANDLERS: dict[str, Callable[[Job], None]] = {
    "upload_asset": upload_original,
    "fetch_source": retrieve_source,
    "organize": organize,
    "download_video": retrieve_video,
    "export_knowledge": export_knowledge,
}


class JobFailure(Exception):
    """A job outcome with a safe code suitable for persistence and logs."""

    def __init__(self, code: str, *, retryable: bool = True):
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", code):
            raise ValueError("Job failure codes must be short lowercase identifiers.")
        self.code = code
        self.retryable = retryable
        super().__init__(code)
