from jobs.handlers import JobFailure

from .organization import OrganizationService


def organize_item(job):
    if job.item_id is None:
        raise JobFailure("invalid_organization_job", retryable=False)
    OrganizationService().organize(job.item_id)
