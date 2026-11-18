import re
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from google.auth.exceptions import RefreshError

from .drive import DRIVE_SCOPE, DriveClient, DriveError
from .models import DriveAccount
from .oauth import SESSION_KEY, client_for_owner

SETTINGS = {
    "GOOGLE_DRIVE_CLIENT_ID": "unit-test",
    "GOOGLE_DRIVE_CLIENT_SECRET": "unit-test",
    "GOOGLE_DRIVE_REDIRECT_URI": "http://127.0.0.1:5173/api/v1/integrations/drive/callback",
    "GOOGLE_DRIVE_TOKEN_KEY": Fernet.generate_key().decode(),
}
BASE = "/api/v1/integrations/drive"


class OAuthAuthenticationTests(TestCase):
    def test_anonymous_cannot_read_or_connect(self):
        self.assertEqual(self.client.get(f"{BASE}/status").status_code, 401)
        self.assertEqual(self.client.post(f"{BASE}/connect").status_code, 401)

    def test_authenticated_connect_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(get_user_model().objects.create(username="owner"))
        self.assertEqual(client.post(f"{BASE}/connect").status_code, 403)


@override_settings(**SETTINGS)
class OAuthIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create(username="owner")

    def setUp(self):
        self.client.force_login(self.owner)

    def start(self):
        response = self.client.post(f"{BASE}/connect")
        self.assertEqual(response.status_code, 200)
        return parse_qs(urlparse(response.json()["authorization_url"]).query)

    def callback(self, state):
        return self.client.get(
            f"{BASE}/callback", {"state": state, "code": "unit-test-code"}
        )

    def test_oauth_requests_the_minimum_scope_and_uses_pkce(self):
        query = self.start()
        self.assertEqual(query["scope"], [DRIVE_SCOPE])
        self.assertEqual(query["access_type"], ["offline"])
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertTrue(
            re.fullmatch(
                r"[A-Za-z0-9._~-]{43,128}", self.client.session[SESSION_KEY]["verifier"]
            )
        )

    @patch("storage.oauth.DriveClient")
    def test_bad_state_is_consumed_without_contacting_google(self, drive_client):
        query = self.start()
        first = self.callback("invalid-state")
        second = self.callback(query["state"][0])
        for response in [first, second]:
            self.assertEqual(response["Location"], "/?drive=drive_callback_invalid")
            self.assertEqual(response["Referrer-Policy"], "no-referrer")
        drive_client.assert_not_called()

    @patch("storage.oauth.DriveClient")
    def test_connect_encrypts_token_and_reconnect_reuses_root(self, drive_client):
        client = drive_client.return_value
        client.account_user.return_value = {
            "permissionId": "same-user",
            "displayName": "Drive test",
        }
        client.reserve_file_id.return_value = "root-id"
        flow = Mock()
        flow.credentials = SimpleNamespace(
            refresh_token="refresh-fixture",
            granted_scopes=[DRIVE_SCOPE],
            scopes=[DRIVE_SCOPE],
        )
        for _ in range(2):
            query = self.start()
            verifier = self.client.session[SESSION_KEY]["verifier"]
            with patch("storage.oauth.oauth_flow", return_value=flow) as build_flow:
                response = self.callback(query["state"][0])
                build_flow.assert_called_once_with(
                    state=query["state"][0], verifier=verifier
                )
            self.assertEqual(response["Location"], "/?drive=connected")
        flow.fetch_token.assert_called_with(code="unit-test-code", timeout=15)
        account = DriveAccount.objects.get(owner=self.owner)
        self.assertEqual(account.state, DriveAccount.State.CONNECTED)
        self.assertEqual(account.root_folder_id, "root-id")
        self.assertNotIn("refresh-fixture", account.refresh_token_ciphertext)
        self.assertEqual(
            Fernet(SETTINGS["GOOGLE_DRIVE_TOKEN_KEY"].encode()).decrypt(
                account.refresh_token_ciphertext.encode()
            ),
            b"refresh-fixture",
        )
        client.reserve_file_id.assert_called_once()
        self.assertEqual(client.ensure_root.call_count, 2)
        status = self.client.get(f"{BASE}/status")
        self.assertEqual(
            status.json(), {"state": "connected", "display_name": "Drive test"}
        )
        self.assertNotIn("root-id", status.content.decode())

    @patch("storage.oauth.DriveClient")
    def test_invalid_grant_sets_reauthorize_state(self, factory):
        account = DriveAccount.objects.create(
            owner=self.owner,
            google_user_id="uid",
            root_folder_id="root",
            refresh_token_ciphertext=Fernet(SETTINGS["GOOGLE_DRIVE_TOKEN_KEY"].encode())
            .encrypt(b"test-refresh")
            .decode(),
            state=DriveAccount.State.CONNECTED,
        )
        client_for_owner(self.owner.pk)
        hook = factory.call_args.kwargs["on_reauthorize"]
        client = DriveClient.__new__(DriveClient)
        client.on_reauthorize = hook
        action = Mock(side_effect=RefreshError("invalid_grant: credential revoked"))
        with self.assertRaisesRegex(DriveError, "^drive_reauthorize$"):
            client.call(action)
        account.refresh_from_db()
        self.assertEqual(account.state, DriveAccount.State.REAUTHORIZE)
