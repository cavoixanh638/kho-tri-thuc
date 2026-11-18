from unittest.mock import patch

from django.db import OperationalError, connection
from django.test import SimpleTestCase, TestCase


class DatabaseReadinessTests(TestCase):
    def test_health_uses_postgresql(self):
        self.assertEqual(connection.vendor, "postgresql")

        response = self.client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready"})


class DatabaseFailureTests(SimpleTestCase):
    @patch("config.api.check_database", side_effect=OperationalError("internal detail"))
    def test_health_reports_unavailability_without_exposing_database_error(self, mock_check):
        response = self.client.get("/api/v1/health")

        mock_check.assert_called_once_with()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
