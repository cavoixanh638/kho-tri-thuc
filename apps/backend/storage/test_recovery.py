from unittest.mock import Mock, patch

from django.test import TestCase

from catalog.models import Item
from jobs.models import Job

from .drive import DriveClient, DriveError
from .test_oauth import OAuthIntegrationTests


class RootDiscoveryTests(TestCase):
    def test_existing_root_is_discovered_and_ambiguous_mapping_is_rejected(self):
        client = DriveClient.__new__(DriveClient)
        client.api = Mock()
        client.execute = Mock(return_value={"files": [{"id": "existing-root"}]})
        self.assertEqual(client.find_root(), "existing-root")
        client.execute.return_value = {"files": [{"id": "first"}, {"id": "second"}]}
        with self.assertRaisesRegex(DriveError, "^drive_root_ambiguous$"):
            client.find_root()


class ReconnectQueueTests(OAuthIntegrationTests):
    @patch("storage.oauth.DriveClient")
    def test_successful_reconnect_recovers_waiting_uploads(self, client_factory):
        super().test_connect_encrypts_token_and_reconnect_reuses_root.__wrapped__(
            self, client_factory
        )
        item = Item.objects.create(owner=self.owner, kind=Item.Kind.FILE)
        job = Job.objects.create(
            item=item,
            kind="upload_asset",
            idempotency_key="disconnected:test",
            state=Job.State.FAILED,
            error_code="drive_not_connected",
            attempt=1,
        )
        query = self.start()
        callback_flow = Mock()
        from types import SimpleNamespace

        from .drive import DRIVE_SCOPE

        callback_flow.credentials = SimpleNamespace(
            refresh_token="new-token",
            scopes=[DRIVE_SCOPE],
            granted_scopes=[DRIVE_SCOPE],
        )
        with patch("storage.oauth.oauth_flow", return_value=callback_flow):
            response = self.callback(query["state"][0])
        self.assertEqual(response["Location"], "/?drive=connected")
        job.refresh_from_db()
        self.assertEqual(job.state, Job.State.RETRY)
        self.assertEqual(job.attempt, 0)
