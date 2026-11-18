from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Item, ItemTopic, RelatedItem, Topic


class CatalogSchemaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create(username="owner")
        items = [
            Item.objects.create(owner=cls.owner, kind=Item.Kind.TEXT) for _ in range(2)
        ]
        cls.first, cls.second = sorted(items, key=lambda item: item.pk)

    def test_saved_at_remains_first_timestamp_when_item_is_edited(self):
        timestamp = self.first.saved_at
        self.first.note = "Đã cập nhật"
        self.first.save()
        self.first.refresh_from_db()
        self.assertEqual(self.first.saved_at, timestamp)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Item.objects.filter(pk=self.first.pk).update(
                saved_at=timestamp + timedelta(seconds=1)
            )

    def test_related_pair_is_canonical_unique_and_never_self_referential(self):
        def link(item_a, item_b):
            return RelatedItem.objects.create(
                item_a=item_a,
                item_b=item_b,
                reason="Cùng chủ đề",
                method_version="rules-1",
                source_version="content-1",
            )

        link(self.first, self.second)
        for item_a, item_b in [
            (self.first, self.second),
            (self.second, self.first),
            (self.first, self.first),
        ]:
            with self.subTest(item_a=item_a.pk, item_b=item_b.pk):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    link(item_a, item_b)

    def test_assignment_does_not_duplicate_a_topic(self):
        topic = Topic.objects.create(owner=self.owner, name="Lĩnh vực")
        ItemTopic.objects.create(item=self.first, topic=topic, user_pinned=True)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ItemTopic.objects.create(item=self.first, topic=topic)
