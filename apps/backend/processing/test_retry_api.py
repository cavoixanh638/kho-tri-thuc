from django.contrib.auth import get_user_model
from django.test import TestCase

from catalog.models import Item
from jobs.models import Job


class RetryApiTests(TestCase):
    def test_retry_preserves_capture_history_and_owner_scope(self):
        owner = get_user_model().objects.create(username="owner")
        other = get_user_model().objects.create(username="other")
        item = Item.objects.create(
            owner=owner, kind=Item.Kind.LINK, source_fetch="failed"
        )
        job = Job.objects.create(
            item=item,
            kind="fetch_source",
            idempotency_key="retry-test",
            state=Job.State.FAILED,
            attempt=5,
            error_code="source_unavailable",
        )
        url = f"/api/v1/items/{item.pk}/retry"
        self.client.force_login(other)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.client.force_login(owner)
        response = self.client.post(url)
        self.assertEqual(response.json(), {"queued": 1})
        job.refresh_from_db()
        self.assertEqual(job.attempt, 0)
        self.assertEqual(job.state, Job.State.RETRY)
        self.assertEqual(self.client.post(url).json(), {"queued": 0})
