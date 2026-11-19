import logging
from collections.abc import Callable, Mapping

from .handlers import JobFailure
from .models import Job
from .repository import JobRepository

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, handlers: Mapping[str, Callable[[Job], None]]):
        self.handlers = handlers

    def run_once(self) -> bool:
        job = JobRepository.claim(self.handlers.keys())
        if job is None:
            return False

        try:
            self.handlers[job.kind](job)
        except JobFailure as exc:
            settled = JobRepository.fail(job, code=exc.code, retryable=exc.retryable)
        except Exception:
            # Exceptions can contain remote responses, credentials, or user input.
            logger.warning("Unexpected handler error for job %s", job.pk)
            settled = JobRepository.fail(job, code="unexpected_error", retryable=True)
        else:
            settled = JobRepository.complete(job)
        if not settled:
            logger.warning("Lease no longer active for job %s", job.pk)
        elif job.item_id and job.kind != "export_knowledge":
            # Some processors use bulk updates, which do not emit model signals.
            from processing.knowledge_sync import request_sync

            try:
                request_sync(job.item_id)
            except Exception:
                logger.warning("Knowledge sync queue unavailable after job %s", job.pk)
        return True
