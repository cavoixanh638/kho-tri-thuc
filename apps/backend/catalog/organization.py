"""Assign existing catalog groups and refresh evidence for related items."""

import hashlib
import json
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch, Q

from processing.models import DerivedContent

from .models import (
    Assignment,
    Item,
    ItemProject,
    ItemTag,
    ItemTopic,
    Project,
    RelatedItem,
    Tag,
    Topic,
)
from .organization_rules import (
    GroupEvidence,
    LexicalSimilarity,
    lexical_fields,
    normalize_phrase,
)

CandidateProvider = Callable[[Item, tuple[str, ...]], Iterable[UUID]]

GROUP_METHOD_VERSION = "catalog-label-rules-v1"
RELATED_METHOD_VERSION = "catalog-lexical-overlap-v1"


def _fingerprint(value) -> str:
    data = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


@dataclass
class _ItemEvidence:
    item: Item
    parts: tuple[tuple[str, str], ...]
    version: str
    tokens: tuple[tuple[str, frozenset[str]], ...] = field(init=False)

    def __post_init__(self):
        self.tokens = lexical_fields(self.parts)

    @classmethod
    def from_item(cls, item: Item):
        source_parts = (
            ("tiêu đề", item.title),
            ("mô tả", item.description),
            ("ghi chú", item.note),
        )
        derived = item.organization_content
        parts = source_parts + tuple(
            (f"DerivedContent ({row.kind})", row.text) for row in derived
        )
        version = _fingerprint(
            (
                item.kind,
                item.user_edit_version,
                source_parts,
                [
                    (
                        row.pk,
                        row.kind,
                        row.input_hash,
                        row.processor,
                        row.processor_version,
                        row.text,
                    )
                    for row in derived
                ],
            )
        )
        parts = tuple((label, text) for label, text in parts if text.strip())
        return cls(item, parts, version)

    @property
    def texts(self) -> tuple[str, ...]:
        return tuple(text for _, text in self.parts)


def _with_evidence(items):
    return items.prefetch_related(
        Prefetch(
            "derived_content",
            queryset=DerivedContent.objects.filter(status=DerivedContent.Status.ACTIVE)
            .exclude(text="")
            .order_by("pk"),
            to_attr="organization_content",
        )
    )


class OrganizationService:
    """Process a catalog item from a trusted job.

    The optional local candidate provider receives the item and its nonempty
    source texts, and returns candidate UUIDs. Pair evidence is checked in this
    service. Supply evaluated lexical thresholds when enabling relationships.
    """

    def __init__(
        self,
        *,
        candidate_provider: CandidateProvider | None = None,
        similarity: LexicalSimilarity | None = None,
    ):
        if (candidate_provider is None) != (similarity is None):
            raise ValueError(
                "Related items require both a candidate provider and thresholds"
            )
        self.candidate_provider = candidate_provider
        self.similarity = similarity

    @transaction.atomic
    def organize(self, item_id: UUID) -> None:
        owner_id = (
            Item.objects.filter(pk=item_id).values_list("owner_id", flat=True).first()
        )
        if owner_id is None:
            return
        # Runs from either endpoint can update the same pair. Serialize writes
        # within the owner while allowing FK inserts referencing that owner.
        get_user_model().objects.select_for_update(no_key=True).get(pk=owner_id)
        item = _with_evidence(
            Item.objects.select_for_update(no_key=True).filter(
                pk=item_id, owner_id=owner_id
            )
        ).first()
        if item is None:
            return
        if item.deleted_at is not None:
            _incident_links(item).filter(status=RelatedItem.Status.ACTIVE).update(
                status=RelatedItem.Status.STALE
            )
            return
        evidence = _ItemEvidence.from_item(item)
        self._assign_groups(evidence)
        if self.candidate_provider is not None and self.similarity is not None:
            self._refresh_links(evidence, self.candidate_provider, self.similarity)

    def _assign_groups(self, evidence: _ItemEvidence) -> None:
        item = evidence.item
        rules = GroupEvidence.from_texts(item.note, evidence.texts)
        owner_id = item.owner_id
        taxonomies = (
            (Topic.objects.filter(owner_id=owner_id, archived=False), ItemTopic, "topic"),
            (Project.objects.filter(owner_id=owner_id, archived=False), ItemProject, "project"),
            (Tag.objects.filter(owner_id=owner_id), ItemTag, "tag"),
        )
        assigned = False
        for groups, assignment_model, group_type in taxonomies:
            names = [
                (group_id, normalize_phrase(name))
                for group_id, name in groups.values_list("pk", "name")
            ]
            counts = Counter(name for _, name in names)
            matches = {
                group_id
                for group_id, name in names
                if counts[name] == 1 and rules.supports(group_type, name)
            }
            has_auto_assignment = _sync_assignments(
                item, assignment_model, group_type, matches, evidence.version
            )
            assigned |= has_auto_assignment
        status = "auto_assigned" if assigned else "unclassified"
        Item.objects.filter(pk=item.pk).exclude(classification_status=status).update(
            classification_status=status
        )

    def _refresh_links(
        self, evidence: _ItemEvidence, provider: CandidateProvider, similarity: LexicalSimilarity
    ) -> None:
        item = evidence.item
        existing = {
            (b_id if a_id == item.pk else a_id): link_id
            for link_id, a_id, b_id in _incident_links(item)
            .exclude(status=RelatedItem.Status.DISMISSED)
            .values_list("pk", "item_a_id", "item_b_id")
        }
        candidate_ids = set(existing)
        if evidence.tokens:
            candidate_ids.update(provider(item, evidence.texts))
        candidate_ids.discard(item.pk)
        candidates = _with_evidence(
            Item.objects.filter(
                owner_id=item.owner_id, deleted_at__isnull=True, pk__in=candidate_ids
            )
        )
        refreshed = set()
        for candidate in candidates:
            other = _ItemEvidence.from_item(candidate)
            left, right = sorted((evidence, other), key=lambda value: value.item.pk)
            match = similarity.match(left.tokens, right.tokens)
            if match is None:
                continue
            self._save_link(left, right, match)
            refreshed.add(candidate.pk)
        stale = [link_id for peer, link_id in existing.items() if peer not in refreshed]
        RelatedItem.objects.filter(pk__in=stale, status=RelatedItem.Status.ACTIVE).update(
            status=RelatedItem.Status.STALE
        )

    def _save_link(
        self, left: _ItemEvidence, right: _ItemEvidence, match: tuple[str, float]
    ) -> None:
        reason, confidence = match
        values = {
            "reason": reason,
            "confidence": confidence,
            "method_version": RELATED_METHOD_VERSION,
            "source_version": _fingerprint((left.version, right.version)),
            "status": RelatedItem.Status.ACTIVE,
        }
        link, created = RelatedItem.objects.get_or_create(
            item_a_id=left.item.pk, item_b_id=right.item.pk, defaults=values
        )
        if not created:
            (
                RelatedItem.objects.filter(pk=link.pk, relation_type="similar")
                .exclude(status=RelatedItem.Status.DISMISSED)
                .exclude(**values)
                .update(**values)
            )


def _sync_assignments(item, model, group_type, matches, source_version) -> bool:
    assignments = model.objects.filter(item=item)
    field_name = f"{group_type}_id"
    automatic = assignments.filter(origin=Assignment.Origin.AUTO, user_pinned=False)
    automatic.exclude(**{f"{field_name}__in": matches}).delete()
    values = {
        # Exact rule evidence; this score is not a calibrated probability.
        "confidence": 1.0,
        "method_version": GROUP_METHOD_VERSION,
        "source_version": source_version,
    }
    for group_id in sorted(matches):
        key = {field_name: group_id}
        assignment, created = model.objects.get_or_create(
            item=item, **key, defaults={"origin": Assignment.Origin.AUTO, **values}
        )
        if not created and assignment.origin == Assignment.Origin.AUTO:
            automatic.filter(pk=assignment.pk).exclude(**values).update(**values)
    return assignments.filter(origin=Assignment.Origin.AUTO).exists()


def _incident_links(item: Item):
    return RelatedItem.objects.filter(
        Q(item_a_id=item.pk) | Q(item_b_id=item.pk), relation_type="similar"
    )
