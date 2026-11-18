from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from catalog.models import Item

from .models import CaptureEvent


class CaptureEventSchemaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create(username="owner")
        cls.item = Item.objects.create(owner=cls.owner, kind=Item.Kind.TEXT)

    def make_capture(self, **overrides):
        fields = {
            "owner": self.owner,
            "item": self.item,
            "raw_kind": CaptureEvent.Kind.TEXT,
            "raw_text": " Tri thức\n Tiếng Việt ",
        }
        return CaptureEvent.objects.create(**(fields | overrides))

    def test_history_is_immutable_even_on_bulk_update(self):
        event = self.make_capture(idempotency_key="request-1")
        events = CaptureEvent.objects.filter(pk=event.pk)
        for change in [
            {"server_received_at": event.server_received_at + timedelta(seconds=1)},
            {"raw_text": "replaced"},
            {"original_url": "https://example.com/replaced"},
            {"idempotency_key": "request-2"},
            {"client_sent_at": timezone.now()},
        ]:
            with self.subTest(change=change), self.assertRaises(IntegrityError):
                with transaction.atomic():
                    events.update(**change)

        events.update(status="processed")
        event.refresh_from_db()
        self.assertEqual(event.status, "processed")
        self.assertEqual(event.raw_text, " Tri thức\n Tiếng Việt ")

    def test_request_key_is_unique_per_owner_and_channel_when_present(self):
        self.make_capture(idempotency_key="request-1")
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_capture(idempotency_key="request-1")

        self.make_capture(idempotency_key="request-1", source_channel="android")
        another_owner = get_user_model().objects.create(username="another")
        another_item = Item.objects.create(owner=another_owner, kind=Item.Kind.TEXT)
        self.make_capture(
            owner=another_owner, item=another_item, idempotency_key="request-1"
        )
        self.make_capture()
        self.make_capture()

    def test_raw_kind_requires_the_matching_input(self):
        for change in [{"raw_text": ""}, {"raw_kind": CaptureEvent.Kind.LINK}]:
            with self.subTest(change=change), self.assertRaises(IntegrityError):
                with transaction.atomic():
                    self.make_capture(**change)
