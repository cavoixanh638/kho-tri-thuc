from catalog.models import Item, Source
from django.contrib.auth import get_user_model
from django.test import Client, TransactionTestCase
from jobs.models import Job

from .models import CaptureEvent
from .services import CaptureSubmission, InvalidCapture, submit_capture


class AttachedSourceTests(TransactionTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="attached-owner")
        self.other = get_user_model().objects.create_user(username="attached-other")
        self.article = Item.objects.create(
            owner=self.owner,
            kind="text",
            title="Bài tri thức",
            note="# Nội dung đã biên soạn\nGiữ nguyên.",
        )
        self.client.force_login(self.owner)

    def submission(
        self, *, url="https://example.com/source", key="attach-1", target=None, **kwargs
    ):
        return CaptureSubmission(
            kind="link",
            url=url,
            idempotency_key=key,
            target_item_id=target or self.article.pk,
            **kwargs,
        )

    def test_attach_retry_keeps_authored_text_and_single_source_event_job(self):
        self.article.source_fetch = "done"
        self.article.content_extract = "done"
        self.article.save(update_fields=["source_fetch", "content_extract"])
        original = (
            self.article.note,
            self.article.saved_at,
            self.article.user_edit_version,
        )
        first, created = submit_capture(self.owner, self.submission())
        again, replay_created = submit_capture(self.owner, self.submission())
        self.assertTrue(created)
        self.assertFalse(replay_created)
        self.assertEqual(first.pk, again.pk)
        self.assertEqual(first.server_received_at, again.server_received_at)
        self.assertEqual(first.item_id, self.article.pk)
        self.article.refresh_from_db()
        self.assertEqual(self.article.source_fetch, "pending")
        self.assertEqual(self.article.content_extract, "pending")
        self.assertEqual(
            (
                Item.objects.count(),
                Source.objects.count(),
                CaptureEvent.objects.count(),
            ),
            (1, 1, 1),
        )
        self.assertEqual(
            Job.objects.filter(item=self.article, kind="fetch_source").count(), 1
        )
        self.article.refresh_from_db()
        self.assertEqual(
            (self.article.note, self.article.saved_at, self.article.user_edit_version),
            original,
        )
        source = Source.objects.get(item=self.article)
        self.assertEqual(
            Job.objects.get(item=self.article).input_ref,
            {"source_id": source.pk, "capture_id": str(first.pk)},
        )

    def test_multiple_sources_share_article_and_normal_capture_reuses_that_article(
        self,
    ):
        submit_capture(self.owner, self.submission())
        submit_capture(
            self.owner,
            self.submission(url="https://example.com/second", key="attach-2"),
        )
        event, created = submit_capture(
            self.owner,
            CaptureSubmission(
                kind="link",
                url="https://example.com/source",
                idempotency_key="ordinary-1",
            ),
        )
        self.assertTrue(created)
        self.assertEqual(event.item_id, self.article.pk)
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(self.article.sources.count(), 2)
        self.assertEqual(CaptureEvent.objects.filter(item=self.article).count(), 3)
        self.assertEqual(
            Job.objects.filter(item=self.article, kind="fetch_source").count(), 2
        )

    def test_idempotency_target_mismatch_existing_other_source_and_foreign_target_reject(
        self,
    ):
        submit_capture(self.owner, self.submission())
        peer = Item.objects.create(owner=self.owner, kind="text", note="Bài thứ hai")
        with self.assertRaisesRegex(InvalidCapture, "idempotency_target_mismatch"):
            submit_capture(self.owner, self.submission(target=peer.pk))
        with self.assertRaisesRegex(InvalidCapture, "source_already_in_another_item"):
            submit_capture(
                self.owner, self.submission(target=peer.pk, key="other-target")
            )
        private = Item.objects.create(owner=self.other, kind="text", note="Riêng")
        with self.assertRaisesRegex(InvalidCapture, "unknown_target_item"):
            submit_capture(
                self.owner,
                self.submission(
                    target=private.pk, url="https://example.com/private", key="foreign"
                ),
            )
        self.assertEqual(Source.objects.count(), 1)
        self.assertEqual(CaptureEvent.objects.count(), 1)
        self.assertEqual(Job.objects.count(), 1)

    def test_attachment_api_keeps_same_item_requires_owner_csrf_and_link_input(self):
        url = f"/api/v1/items/{self.article.pk}/sources"
        body = {"url": "https://example.com/public"}
        first = self.client.post(
            url,
            body,
            content_type="application/json",
            headers={"Idempotency-Key": "api-attach"},
        )
        self.assertEqual(first.status_code, 201)
        repeated = self.client.post(
            url,
            body,
            content_type="application/json",
            headers={"Idempotency-Key": "api-attach"},
        )
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(first.json(), repeated.json())
        self.assertEqual(first.json()["item_id"], str(self.article.pk))
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.owner)
        self.assertEqual(
            csrf.post(url, body, content_type="application/json").status_code, 403
        )
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.post(url, body, content_type="application/json").status_code,
            404,
        )
        self.client.force_login(self.owner)
        self.assertEqual(
            self.client.post(
                url, {"url": "javascript:alert(1)"}, content_type="application/json"
            ).status_code,
            422,
        )
        with self.assertRaisesRegex(InvalidCapture, "source_requires_link"):
            submit_capture(
                self.owner,
                CaptureSubmission(
                    kind="text", text="Chỉ văn bản", target_item_id=self.article.pk
                ),
            )
