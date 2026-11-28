from jobs.handlers import JobFailure
from search.services import SearchFilters, SearchService

from .organization import OrganizationService
from .organization_rules import LexicalSimilarity, normalize_phrase


def search_candidates(item, texts):
    candidates = set()
    for text in texts[:3]:
        tokens = list(dict.fromkeys(normalize_phrase(text).split()))[:12]
        if not tokens:
            continue
        page = SearchService().search(
            SearchFilters(owner_id=item.owner_id, exclude_item_id=item.pk),
            " ".join(tokens)[:300],
            limit=30,
            allow_partial=False,
        )
        candidates.update(hit.item_id for hit in page.hits)
    return tuple(candidates)


def organize_item(job):
    if job.item_id is None:
        raise JobFailure("invalid_organization_job", retryable=False)
    # The provisional evaluation covers conservative, identical token evidence.
    # KT-107 human validation is required before widening this threshold.
    OrganizationService(
        candidate_provider=search_candidates,
        similarity=LexicalSimilarity(min_shared_tokens=6, min_similarity=1.0),
    ).organize(job.item_id)
