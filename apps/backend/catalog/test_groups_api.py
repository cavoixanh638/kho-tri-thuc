from django.contrib.auth import get_user_model
from django.test import TestCase

from jobs.models import Job

from .models import Assignment, Item, ItemTopic, RelatedItem, Topic
from .organization_job import organize_item


class OrganizationApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create(username="owner")
        cls.other = users.create(username="other")
        cls.item = Item.objects.create(
            owner=cls.owner,
            kind=Item.Kind.TEXT,
            title="Hạ tầng số",
            note="Chuyển đổi số cho trường học",
        )
        cls.other_item = Item.objects.create(
            owner=cls.other, kind=Item.Kind.TEXT, title="Hạ tầng số"
        )
        cls.topic = Topic.objects.create(owner=cls.owner, name="Chuyển đổi số")
        cls.private_topic = Topic.objects.create(
            owner=cls.other, name="Không công khai"
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def test_create_and_pin_group_without_removing_automatic_assignment(self):
        topic = self.client.post(
            "/api/v1/groups",
            {"kind": "topic", "name": "Kỹ thuật"},
            content_type="application/json",
        )
        self.assertEqual(topic.status_code, 201)
        duplicate = self.client.post(
            "/api/v1/groups",
            {"kind": "topic", "name": "KỸ THUẬT"},
            content_type="application/json",
        )
        self.assertEqual(duplicate.status_code, 200)
        auto = ItemTopic.objects.create(
            item=self.item, topic=self.topic, origin=Assignment.Origin.AUTO
        )
        url = f"/api/v1/items/{self.item.pk}/organization"
        group_id = topic.json()["id"]
        response = self.client.patch(
            url, {"topic_ids": [group_id]}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["topics"]), 2)
        self.assertTrue(
            ItemTopic.objects.get(item=self.item, topic_id=group_id).user_pinned
        )
        self.assertTrue(ItemTopic.objects.filter(pk=auto.pk).exists())
        rejected = self.client.patch(
            url, {"topic_ids": [self.private_topic.pk]}, content_type="application/json"
        )
        self.assertEqual(rejected.status_code, 422)
        self.assertEqual(ItemTopic.objects.filter(item=self.item).count(), 2)

    def test_organization_job_and_group_results_keep_owner_scope(self):
        job = Job.objects.create(
            kind="organize", idempotency_key="job:unit:1", item=self.item
        )
        organize_item(job)
        self.assertTrue(
            ItemTopic.objects.filter(item=self.item, topic=self.topic).exists()
        )
        self.assertEqual(
            self.client.get(
                f"/api/v1/items/{self.other_item.pk}/organization"
            ).status_code,
            404,
        )

    def test_related_rejects_stale_hidden_and_foreign_items(self):
        peer = Item.objects.create(
            owner=self.owner, kind=Item.Kind.TEXT, title="Mục ngang hàng"
        )
        faded = Item.objects.create(
            owner=self.owner, kind=Item.Kind.TEXT, title="Đã cũ"
        )
        for other, status in [
            (peer, RelatedItem.Status.ACTIVE),
            (faded, RelatedItem.Status.STALE),
            (self.other_item, RelatedItem.Status.ACTIVE),
        ]:
            first, second = sorted([self.item, other], key=lambda item: item.pk)
            RelatedItem.objects.create(
                item_a=first,
                item_b=second,
                reason="Có bằng chứng",
                method_version="test",
                source_version="test",
                status=status,
            )
        response = self.client.get(f"/api/v1/items/{self.item.pk}/related")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [r["item_id"] for r in response.json()["results"]], [str(peer.pk)]
        )
