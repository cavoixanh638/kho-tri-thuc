from unittest.mock import Mock
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from django.test import TestCase
from django.utils import timezone

from ingestion.models import CaptureEvent
from processing.models import DerivedContent

from .models import (
    Assignment,
    Item,
    ItemProject,
    ItemTag,
    ItemTopic,
    Project,
    RelatedItem,
    Source,
    Tag,
    Topic,
)
from .organization import (
    GROUP_METHOD_VERSION,
    RELATED_METHOD_VERSION,
    LexicalSimilarity,
    OrganizationService,
)


class OrganizationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.owner = users.objects.create(username="organization-owner")
        cls.other_owner = users.objects.create(username="organization-other")

    def item(self, note="", **overrides):
        return Item.objects.create(
            **{"owner": self.owner, "kind": Item.Kind.TEXT, "note": note, **overrides}
        )

    def related_service(self, provider):
        # Deliberately fixture-only thresholds. KT-107 must evaluate production policy.
        return OrganizationService(
            candidate_provider=provider,
            similarity=LexicalSimilarity(min_shared_tokens=3, min_similarity=0.45),
        )

    def derived(self, item, text, version, **overrides):
        return DerivedContent.objects.create(
            item=item,
            kind="document",
            text=text,
            processor="fixture-parser",
            processor_version=version,
            input_hash=version.zfill(64),
            **overrides,
        )

    def test_n09_assigns_existing_groups_with_provenance(self):
        item = self.item(
            "Kế hoạch sao lưu định kỳ cho thư viện.\nDự án: Chuyển kho 2026\nNhãn: PostgreSQL"
        )
        topic = Topic.objects.create(owner=self.owner, name="Sao lưu định kỳ")
        project = Project.objects.create(owner=self.owner, name="Chuyển Kho 2026")
        tag = Tag.objects.create(owner=self.owner, name="PostgreSQL")
        service = OrganizationService()

        service.organize(item.pk)
        for model, expected, field in (
            (ItemTopic, topic, "topic"),
            (ItemProject, project, "project"),
            (ItemTag, tag, "tag"),
        ):
            assignment = model.objects.get(item=item)
            self.assertEqual(getattr(assignment, field), expected)
            self.assertEqual(assignment.origin, Assignment.Origin.AUTO)
            self.assertEqual(assignment.confidence, 1.0)
            self.assertFalse(assignment.user_pinned)
            self.assertEqual(assignment.method_version, GROUP_METHOD_VERSION)
            self.assertRegex(assignment.source_version, r"^[a-f0-9]{64}$")
        item.refresh_from_db()
        self.assertEqual(item.classification_status, "auto_assigned")

    def test_n10_reprocess_preserves_manual_and_pinned_rows_even_on_match(self):
        item = self.item("Chủ đề: Sao lưu\nNhãn: Postgres\nDự án: Chuyển kho")
        topic = Topic.objects.create(owner=self.owner, name="Sao lưu")
        pinned_tag = Tag.objects.create(owner=self.owner, name="Postgres")
        project = Project.objects.create(owner=self.owner, name="Chuyển kho")
        manual = ItemTopic.objects.create(item=item, topic=topic, source_version="manual")
        pinned = ItemTag.objects.create(
            item=item,
            tag=pinned_tag,
            origin=Assignment.Origin.AUTO,
            user_pinned=True,
            confidence=0.75,
            method_version="old-rules",
            source_version="accepted",
        )
        manual_before, pinned_before = (
            model_to_dict(assignment) for assignment in (manual, pinned)
        )
        service = OrganizationService()

        service.organize(item.pk)
        self.assertTrue(ItemProject.objects.filter(item=item, project=project).exists())
        item.note = "Đã chuyển chủ đề của ghi chú."
        item.save(update_fields=["note"])
        service.organize(item.pk)
        service.organize(item.pk)

        self.assertFalse(ItemProject.objects.filter(item=item).exists())
        self.assertEqual(model_to_dict(ItemTopic.objects.get(pk=manual.pk)), manual_before)
        self.assertEqual(model_to_dict(ItemTag.objects.get(pk=pinned.pk)), pinned_before)

    def test_n11_does_not_guess_project_or_create_taxonomy(self):
        Project.objects.create(owner=self.owner, name="Chuyển kho 2026")
        Topic.objects.create(owner=self.owner, name="Lưu trữ lâu dài", archived=True)
        Topic.objects.create(owner=self.other_owner, name="Lưu trữ lâu dài")
        Tag.objects.create(owner=self.owner, name="kho")
        item = self.item(
            "Đọc về chuyển kho 2026 và lưu trữ lâu dài.\nDự án: Chưa có nhóm.",
            description="Dự án: Chuyển kho 2026",
        )

        OrganizationService().organize(item.pk)

        self.assertFalse(ItemTopic.objects.filter(item=item).exists())
        self.assertFalse(ItemProject.objects.filter(item=item).exists())
        self.assertFalse(ItemTag.objects.filter(item=item).exists())
        counts = (Topic.objects.count(), Project.objects.count(), Tag.objects.count())
        self.assertEqual(counts, (2, 1, 1))
        item.refresh_from_db()
        self.assertEqual(item.classification_status, "unclassified")

    def test_ambiguous_normalized_topic_name_needs_disambiguation(self):
        parent = Topic.objects.create(owner=self.owner, name="Kỹ thuật")
        Topic.objects.create(owner=self.owner, name="Lưu trữ")
        Topic.objects.create(owner=self.owner, parent=parent, name="Luu tru")
        item = self.item("Chủ đề: Lưu trữ")
        OrganizationService().organize(item.pk)
        self.assertFalse(ItemTopic.objects.filter(item=item).exists())

    def test_n06_keeps_similar_notes_separate_and_link_unique_from_both_sides(self):
        topic = Topic.objects.create(owner=self.owner, name="Sao lưu định kỳ")
        first = self.item("Hướng dẫn sao lưu định kỳ\nGiữ file gốc.")
        second = self.item("Cách sao lưu định kỳ\nGiữ file gốc!")
        provider = Mock(return_value=[second.pk, first.pk, second.pk, uuid4()])
        service = self.related_service(provider)

        service.organize(first.pk)
        created = RelatedItem.objects.get()
        provider.assert_called_once_with(first, (first.note,))
        service.organize(second.pk)
        link = RelatedItem.objects.get()

        self.assertEqual(link.pk, created.pk)
        self.assertEqual((link.item_a_id, link.item_b_id), tuple(sorted((first.pk, second.pk))))
        self.assertEqual(link.reason, created.reason)
        self.assertIn("ghi chú", link.reason)
        self.assertEqual(link.source_version, created.source_version)
        self.assertEqual(link.method_version, RELATED_METHOD_VERSION)
        self.assertGreater(link.confidence, 0.0)
        self.assertEqual(link.status, RelatedItem.Status.ACTIVE)
        self.assertEqual(Item.objects.get(pk=first.pk).note, first.note)
        self.assertEqual(Item.objects.get(pk=second.pk).note, second.note)
        self.assertEqual(ItemTopic.objects.filter(topic=topic).count(), 2)

    def test_n12_reprocessing_refreshes_then_stales_link_and_preserves_capture(self):
        topic = Topic.objects.create(owner=self.owner, name="Sao lưu định kỳ")
        item = self.item("Ghi chú ban đầu.")
        peer = self.item("Sao lưu định kỳ giữ dữ liệu an toàn.")
        capture = CaptureEvent.objects.create(
            owner=self.owner, item=item, raw_kind=CaptureEvent.Kind.TEXT, raw_text=item.note
        )
        text = peer.note
        first = self.derived(item, text, "1")
        provider = Mock(return_value=[peer.pk])
        service = self.related_service(provider)
        service.organize(item.pk)
        assignment_before = ItemTopic.objects.get(item=item, topic=topic)
        link_before = RelatedItem.objects.get()

        # An existing relationship is re-evaluated even if retrieval omits its peer.
        provider.return_value = []
        first.status = DerivedContent.Status.STALE
        first.save(update_fields=["status"])
        second = self.derived(item, text, "2")
        service.organize(item.pk)
        assignment_after = ItemTopic.objects.get(item=item, topic=topic)
        link_after = RelatedItem.objects.get()
        self.assertEqual(assignment_before.pk, assignment_after.pk)
        self.assertNotEqual(assignment_before.source_version, assignment_after.source_version)
        self.assertEqual(link_before.pk, link_after.pk)
        self.assertNotEqual(link_before.source_version, link_after.source_version)
        self.assertEqual(link_after.status, RelatedItem.Status.ACTIVE)

        second.status = DerivedContent.Status.STALE
        second.save(update_fields=["status"])
        self.derived(item, "Viết bản tin tuần sau.", "3")
        self.derived(item, text, "4", status=DerivedContent.Status.FAILED)
        service.organize(item.pk)
        self.assertFalse(ItemTopic.objects.filter(item=item, topic=topic).exists())
        link_after.refresh_from_db()
        self.assertEqual(link_after.status, RelatedItem.Status.STALE)
        self.assertEqual(link_after.reason, link_before.reason)
        item_after = Item.objects.get(pk=item.pk)
        capture_after = CaptureEvent.objects.get(pk=capture.pk)
        self.assertEqual(item_after.classification_status, "unclassified")
        self.assertEqual(item_after.note, item.note)
        self.assertEqual(item_after.saved_at, item.saved_at)
        self.assertEqual(capture_after.raw_text, capture.raw_text)
        self.assertEqual(capture_after.server_received_at, capture.server_received_at)

        self.derived(item, text, "5")
        service.organize(item.pk)
        link_after.refresh_from_db()
        self.assertEqual(link_after.status, RelatedItem.Status.ACTIVE)
        link_after.status = RelatedItem.Status.DISMISSED
        link_after.save(update_fields=["status"])
        provider.return_value = [peer.pk]
        service.organize(item.pk)
        link_after.refresh_from_db()
        self.assertEqual(link_after.status, RelatedItem.Status.DISMISSED)
        self.assertEqual(RelatedItem.objects.count(), 1)

    def test_n16_metadata_link_explains_title_evidence(self):
        title = "Hướng dẫn sao lưu PostgreSQL"
        video = self.item(kind=Item.Kind.LINK, title=title)
        other = self.item(kind=Item.Kind.LINK, title=title)
        Source.objects.create(
            item=video,
            original_url="https://video.example/watch/fixture",
            canonical_url="https://video.example/watch/fixture",
            identity_hash="f" * 64,
            platform="youtube",
        )
        self.related_service(lambda _item, _texts: [other.pk]).organize(video.pk)

        self.assertEqual(
            RelatedItem.objects.get().reason,
            "Trùng 5 từ sau chuẩn hóa (tiêu đề ↔ tiêu đề).",
        )
        self.assertFalse(DerivedContent.objects.filter(item=video).exists())

    def test_n17_disjoint_synonym_fixture_has_no_lexical_candidate_or_link(self):
        item = self.item("Mua ô tô cũ")
        peer = self.item("Sắm xe hơi qua sử dụng")
        # One labelled relevant peer and zero lexical hits in this small boundary fixture.
        # This exercises the no-common-terms limit in a controlled fixture.
        common = set(item.note.casefold().split()) & set(peer.note.casefold().split())
        candidates = [peer.pk] if common else []
        self.assertEqual(candidates, [])
        provider = Mock(return_value=candidates)
        service = self.related_service(provider)
        service.organize(item.pk)
        provider.return_value = [peer.pk]
        service.organize(item.pk)
        self.assertFalse(RelatedItem.objects.exists())

    def test_related_candidates_are_owner_scoped_and_recheck_deleted_items(self):
        text = "Hướng dẫn sao lưu định kỳ"
        item = self.item(text)
        peer = self.item(text)
        foreign = self.item(text, owner=self.other_owner)
        deleted = self.item(text, deleted_at=timezone.now())
        service = self.related_service(lambda _item, _texts: [peer.pk, foreign.pk, deleted.pk])
        service.organize(item.pk)
        link = RelatedItem.objects.get()
        self.assertEqual({link.item_a_id, link.item_b_id}, {item.pk, peer.pk})

        peer.deleted_at = timezone.now()
        peer.save(update_fields=["deleted_at"])
        service.organize(item.pk)
        link.refresh_from_db()
        self.assertEqual(link.status, RelatedItem.Status.STALE)

    def test_provider_failure_rolls_back_organization_for_retry(self):
        item = self.item("Sao lưu định kỳ")
        Topic.objects.create(owner=self.owner, name=item.note)
        provider = Mock(side_effect=RuntimeError("candidate retrieval failed"))
        service = self.related_service(provider)
        with self.assertRaisesMessage(RuntimeError, "candidate retrieval failed"):
            service.organize(item.pk)
        self.assertFalse(ItemTopic.objects.filter(item=item).exists())
        item.refresh_from_db()
        self.assertEqual(item.classification_status, "pending")
        provider.side_effect = None
        provider.return_value = []
        service.organize(item.pk)
        self.assertTrue(ItemTopic.objects.filter(item=item).exists())
