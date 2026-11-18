from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Job


class JobSchemaTests(TestCase):
    def test_idempotency_key_is_unique_per_job_kind(self):
        Job.objects.create(kind="fetch_source", idempotency_key="source:1")
        Job.objects.create(kind="organize", idempotency_key="source:1")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Job.objects.create(kind="fetch_source", idempotency_key="source:1")
