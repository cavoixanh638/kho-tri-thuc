from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings

URL = "/api/v1/session"
CREDENTIALS = {"username": "owner", "password": "test-password-only"}


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class SessionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        get_user_model().objects.create_user(**CREDENTIALS)

    def test_login_logout_and_csrf_rotation(self):
        client = Client(enforce_csrf_checks=True)
        before = client.get(URL)
        self.assertFalse(before.json()["authenticated"])
        self.assertIn("no-store", before["Cache-Control"])
        self.assertEqual(
            client.post(URL, CREDENTIALS, content_type="application/json").status_code,
            403,
        )

        login_response = client.post(
            URL,
            CREDENTIALS,
            content_type="application/json",
            headers={"X-CSRFToken": before.json()["csrf_token"]},
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(login_response.json()["authenticated"])
        self.assertEqual(login_response.json()["username"], "owner")
        self.assertEqual(
            client.delete(
                URL, headers={"X-CSRFToken": before.json()["csrf_token"]}
            ).status_code,
            403,
        )
        signed_out = client.delete(
            URL, headers={"X-CSRFToken": login_response.json()["csrf_token"]}
        )
        self.assertFalse(signed_out.json()["authenticated"])
        self.assertIsNone(signed_out.json()["username"])

    def test_bad_credentials_do_not_start_a_session(self):
        self.assertEqual(
            self.client.post(
                URL,
                CREDENTIALS | {"password": "wrong"},
                content_type="application/json",
            ).status_code,
            401,
        )
        self.assertFalse(self.client.get(URL).json()["authenticated"])
