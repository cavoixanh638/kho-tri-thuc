"""P12 isolated fixtures: PostgreSQL TestCase, no production account or AI."""
from django.contrib.auth import get_user_model
from django.core import signing
from django.test import RequestFactory, TestCase
from django.utils import timezone

from processing.models import DerivedContent

from .models import Assignment, Item, ItemProject, ItemTag, ItemTopic, Project, Tag, Topic
from .organization_review import (
    GROUPS, SALT, REJECT_SESSION_KEY, ReviewError, decide, queue, review, undo,
)


class OrgReviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="p12-owner")
        cls.other = get_user_model().objects.create_user(username="p12-other")
        cls.topic = Topic.objects.create(owner=cls.owner, name="Quản lý dự án")
        cls.tag = Tag.objects.create(owner=cls.owner, name="Hạ tầng số")
        cls.project = Project.objects.create(owner=cls.owner, name="Kế hoạch 2026")

    def item(self, note="Chủ đề: Quản lý dự án\nNhãn: Hạ tầng số\nDự án: Kế hoạch 2026", **kwargs):
        return Item.objects.create(owner=self.owner, kind=Item.Kind.TEXT, note=note, **kwargs)

    def proposal(self, item, kind="topic", session=None):
        return next(p for p in review(self.owner.pk, item.pk, session)["proposals"] if p["kind"] == kind)

    def test_fifty_vietnamese_labeled_items_precision_coverage(self):
        audited = correct = eligible = accepted = wrong = 0
        for number in range(50):
            item = self.item(title=f"Văn bản số {number}")
            result = review(self.owner.pk, item.pk)
            for kind, expected_id in (
                ("topic", self.topic.pk), ("tag", self.tag.pk), ("project", self.project.pk)
            ):
                eligible += 1
                proposal = next(p for p in result["proposals"] if p["kind"] == kind)
                audited += 1
                if proposal["group_id"] == expected_id:
                    correct += 1
                else:
                    wrong += 1
                self.assertEqual(decide(self.owner.pk, item.pk, proposal["receipt"], "accept")["state"], "accepted")
                accepted += 1
        self.assertEqual((audited, correct, wrong, accepted, eligible), (150, 150, 0, 150, 150))
        self.assertEqual(correct / audited, 1.0)
        self.assertEqual(accepted / eligible, 1.0)
        self.assertEqual(wrong / audited, 0.0)

    def test_evidence_no_text_and_versioned_derived_source(self):
        item = self.item(note="", title="", description="")
        view = review(self.owner.pk, item.pk)
        self.assertEqual(view["evidence_status"], "missing_text")
        self.assertEqual(view["proposals"], [])
        derived = DerivedContent.objects.create(
            item=item, kind="document", text="Hạ tầng số phục vụ dữ liệu",
            processor="fixture", processor_version="2", input_hash="a" * 64,
        )
        first = self.proposal(item, "tag")
        self.assertEqual(first["processor"], "fixture")
        self.assertEqual(first["processor_version"], "2")
        self.assertEqual(first["field"], "nội dung trích xuất")
        derived.status = DerivedContent.Status.STALE
        derived.save(update_fields=["status"])
        with self.assertRaisesMessage(ReviewError, "review_source_changed"):
            decide(self.owner.pk, item.pk, first["receipt"], "accept")
        self.assertFalse(ItemTag.objects.filter(item=item).exists())

    def test_owner_deleted_and_archived_groups_rejected(self):
        item = self.item()
        proposal = self.proposal(item)
        with self.assertRaises(ReviewError):
            review(self.other.pk, item.pk)
        with self.assertRaises(ReviewError):
            decide(self.other.pk, item.pk, proposal["receipt"], "accept")
        self.topic.archived = True
        self.topic.save(update_fields=["archived"])
        with self.assertRaisesMessage(ReviewError, "review_evidence_changed"):
            decide(self.owner.pk, item.pk, proposal["receipt"], "accept")
        item.deleted_at = timezone.now()
        item.save(update_fields=["deleted_at"])
        with self.assertRaisesMessage(ReviewError, "review_item_unavailable"):
            review(self.owner.pk, item.pk)

    def test_accept_retry_undo_and_conflict(self):
        item = self.item()
        proposal = self.proposal(item)
        receipt = proposal["receipt"]
        first = decide(self.owner.pk, item.pk, receipt, "accept")
        self.assertEqual(first["writes"], 1)
        row = ItemTopic.objects.get(item=item, topic=self.topic)
        self.assertEqual(row.origin, Assignment.Origin.USER)
        self.assertFalse(row.user_pinned)
        self.assertEqual(decide(self.owner.pk, item.pk, receipt, "accept")["writes"], 0)
        self.assertEqual(undo(self.owner.pk, item.pk, first["undo_receipt"])["writes"], 1)
        self.assertEqual(undo(self.owner.pk, item.pk, first["undo_receipt"])["writes"], 0)
        self.assertFalse(ItemTopic.objects.filter(item=item).exists())
        again = decide(self.owner.pk, item.pk, receipt, "accept")
        row = ItemTopic.objects.get(item=item, topic=self.topic)
        row.user_pinned = True
        row.save(update_fields=["user_pinned"])
        with self.assertRaisesMessage(ReviewError, "review_undo_conflict"):
            undo(self.owner.pk, item.pk, again["undo_receipt"])

    def test_curated_pinned_never_overwritten_and_pin_undo(self):
        item = self.item()
        user_row = ItemTopic.objects.create(item=item, topic=self.topic, user_pinned=True)
        self.assertEqual(len([p for p in review(self.owner.pk, item.pk)["proposals"] if p["kind"] == "topic"]), 0)
        current = next(x for x in review(self.owner.pk, item.pk)["current"] if x["kind"] == "topic")
        self.assertEqual(current["receipt"], "")
        tag = self.proposal(item, "tag")
        pin = decide(self.owner.pk, item.pk, tag["receipt"], "pin")
        self.assertTrue(ItemTag.objects.get(item=item, tag=self.tag).user_pinned)
        self.assertEqual(undo(self.owner.pk, item.pk, pin["undo_receipt"])["writes"], 1)
        self.assertTrue(ItemTopic.objects.filter(pk=user_row.pk, user_pinned=True).exists())
        self.assertFalse(ItemTag.objects.filter(item=item, tag=self.tag).exists())

    def test_reject_session_scope_and_undo(self):
        item = self.item()
        session = {}
        proposal = self.proposal(item, session=session)
        rejected = decide(self.owner.pk, item.pk, proposal["receipt"], "reject", session)
        self.assertEqual((rejected["writes"], rejected["state"]), (0, "rejected"))
        self.assertTrue(session[REJECT_SESSION_KEY])
        self.assertFalse(any(p["kind"] == "topic" for p in review(self.owner.pk, item.pk, session)["proposals"]))
        self.assertEqual(undo(self.owner.pk, item.pk, rejected["undo_receipt"], session)["state"], "undone")
        self.assertEqual(len(review(self.owner.pk, item.pk, session)["proposals"]), 3)
        self.assertEqual(decide(self.owner.pk, item.pk, proposal["receipt"], "reject", session)["writes"], 0)

    def test_tampered_receipt_cross_item_and_version_conflict(self):
        item = self.item()
        other_item = self.item()
        receipt = self.proposal(item)["receipt"]
        with self.assertRaises(ReviewError):
            decide(self.owner.pk, other_item.pk, receipt, "accept")
        with self.assertRaises(ReviewError):
            decide(self.owner.pk, item.pk, receipt + "tampered", "accept")
        item.note = "Đã chuyển nhóm"
        item.user_edit_version += 1
        item.save(update_fields=["note", "user_edit_version"])
        with self.assertRaisesMessage(ReviewError, "review_source_changed"):
            decide(self.owner.pk, item.pk, receipt, "accept")

    def test_project_requires_explicit_user_declaration(self):
        item = self.item(note="Đang triển khai Kế hoạch 2026")
        view = review(self.owner.pk, item.pk)
        self.assertFalse(any(p["kind"] == "project" for p in view["proposals"]))

    def test_duplicate_normalized_topic_names_no_guess(self):
        item = self.item(note="Chủ đề: Quản lý dự án")
        parent = Topic.objects.create(owner=self.owner, name="Kho khác")
        Topic.objects.create(owner=self.owner, parent=parent, name="Quan ly du an")
        self.assertFalse(any(p["kind"] == "topic" for p in review(self.owner.pk, item.pk)["proposals"]))

    def test_queue_ten_thousand_paging_without_loading_all(self):
        Item.objects.bulk_create(
            [Item(owner=self.owner, kind=Item.Kind.TEXT, title=f"Bài {i}") for i in range(10000)]
        )
        page = queue(self.owner.pk, limit=37, offset=9900)
        self.assertEqual(len(page["results"]), 37)
        self.assertEqual(page["next_offset"], 9937)
        with self.assertRaises(ReviewError):
            queue(self.owner.pk, limit=101)
        with self.assertRaises(ReviewError):
            queue(self.owner.pk, offset=-1)

    def test_manual_pin_current_auto_preserves_undo(self):
        item = self.item(note="")
        row = ItemTag.objects.create(
            item=item, tag=self.tag, origin=Assignment.Origin.AUTO,
            confidence=0.8, method_version="old", source_version="old",
        )
        current = next(x for x in review(self.owner.pk, item.pk)["current"] if x["kind"] == "tag")
        changed = decide(self.owner.pk, item.pk, current["receipt"], "pin")
        row.refresh_from_db()
        self.assertTrue(row.user_pinned)
        self.assertEqual(row.origin, Assignment.Origin.USER)
        undo(self.owner.pk, item.pk, changed["undo_receipt"])
        row.refresh_from_db()
        self.assertEqual((row.origin, row.user_pinned, row.confidence),
                         (Assignment.Origin.AUTO, False, 0.8))
