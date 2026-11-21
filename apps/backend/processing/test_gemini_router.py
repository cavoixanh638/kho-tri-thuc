from datetime import datetime, timedelta, timezone as UTC
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, SimpleTestCase, override_settings
from django.utils import timezone

from .gemini_catalog import (
    DiscoveryError, apply_discovery, list_models, refresh_if_due,
)
from .gemini_policy import choose_model
from .gemini_routing import (
    pacific_day_start, record_observed_outcome, select_for_user,
)
from .models import (
    GeminiCatalogState, GeminiModelCatalog, GeminiPreference, GeminiUsageEvent,
)


def entry(code, actions=None):
    return {
        "model_id": code,
        "label": code,
        "description": "QA model",
        "generation_methods": actions if actions is not None else ["generateContent"],
        "input_token_limit": 200000,
        "output_token_limit": 4096,
    }


def available(*names):
    return {
        name: {
            "active": True, "reviewed": True, "generation_methods": ["generateContent"]
        }
        for name in names
    }


class ModelSelectionTests(SimpleTestCase):
    def test_balanced_prefers_cheap_for_simple_and_flash_for_complex(self):
        rows = available("gemini-3.5-flash-lite", "gemini-3.6-flash")
        self.assertEqual(
            choose_model(mode="balanced", task="ocr_simple", catalog=rows).model,
            "gemini-3.5-flash-lite",
        )
        self.assertEqual(
            choose_model(mode="balanced", task="ocr_complex", catalog=rows).model,
            "gemini-3.6-flash",
        )

    def test_newest_unreviewed_or_image_generation_is_never_autoselected(self):
        rows = available("gemini-3.5-flash-lite", "gemini-4-argon",
                         "gemini-4-neon", "gemini-3.1-flash-image")
        self.assertEqual(
            choose_model(mode="quality", task="ocr_complex", catalog=rows).model,
            "gemini-3.5-flash-lite",
        )
        self.assertIsNone(
            choose_model(mode="manual", task="ocr_simple", catalog=rows,
                         manual_model="gemini-4-argon").model,
        )

    def test_tier_gate_manual_no_fallback_and_cooldown(self):
        rows = available("gemini-3.5-flash-lite", "gemini-3.6-flash",
                         "gemini-3.8-flash")
        self.assertEqual(
            choose_model(mode="quality", task="ocr_complex", catalog=rows,
                         allowed_tiers=("economy", "balanced")).model,
            "gemini-3.6-flash",
        )
        self.assertIsNone(
            choose_model(mode="manual", task="ocr_complex", catalog=rows,
                         manual_model="gemini-3.8-flash",
                         allowed_tiers=("economy", "balanced")).model,
        )
        self.assertEqual(
            choose_model(mode="balanced", task="ocr_complex", catalog=rows,
                         cooldown={"gemini-3.6-flash"}).model,
            "gemini-3.5-flash-lite",
        )
        self.assertIsNone(
            choose_model(mode="manual", task="ocr_complex", catalog=rows,
                         manual_model="gemini-3.6-flash",
                         cooldown={"gemini-3.6-flash"}).model,
        )

    def test_pacific_day_reset_includes_dst(self):
        summer = pacific_day_start(datetime(2026, 7, 1, 12, tzinfo=UTC))
        winter = pacific_day_start(datetime(2026, 11, 21, 12, tzinfo=UTC))
        self.assertEqual(summer.hour, 7)
        self.assertEqual(winter.hour, 8)


class StubOpener:
    def __init__(self, payloads):
        self.payloads = payloads
        self.urls = []
        self.headers = []

    def open(self, request, timeout):
        self.urls.append(request.full_url)
        self.headers.append(dict(request.header_items()))
        self.assert_no_secret_in_url(request.full_url)
        return BytesIO(self.payloads.pop(0))

    @staticmethod
    def assert_no_secret_in_url(url):
        assert "test-api-key" not in url


class CatalogueTests(TestCase):
    def test_paginated_list_and_auth_is_header_only(self):
        opener = StubOpener([
            b'{"models":[{"name":"models/gemini-3.5-flash-lite","displayName":"Lite","supportedGenerationMethods":["generateContent"],"inputTokenLimit":1000}],"nextPageToken":"page-2"}',
            b'{"models":[{"name":"models/gemini-4-argon","displayName":"New","supportedGenerationMethods":["generateContent"]}]}',
        ])
        data = list_models("test-api-key", opener=opener)
        self.assertEqual(len(data), 2)
        self.assertIn("pageToken=page-2", opener.urls[1])
        self.assertEqual(opener.headers[0]["X-goog-api-key"], "test-api-key")
        self.assertEqual(data[0]["input_token_limit"], 1000)

    def test_new_model_pending_and_known_model_not_sticky_after_removal(self):
        now = timezone.now()
        apply_discovery([entry("gemini-3.5-flash-lite"), entry("gemini-4-argon")], now=now)
        self.assertTrue(GeminiModelCatalog.objects.get(pk="gemini-3.5-flash-lite").reviewed)
        self.assertFalse(GeminiModelCatalog.objects.get(pk="gemini-4-argon").reviewed)
        apply_discovery([entry("gemini-4-argon")], now=now + timedelta(hours=12))
        self.assertTrue(GeminiModelCatalog.objects.get(pk="gemini-3.5-flash-lite").active)
        apply_discovery([entry("gemini-4-argon")], now=now + timedelta(hours=24))
        self.assertFalse(GeminiModelCatalog.objects.get(pk="gemini-3.5-flash-lite").active)

    def test_transient_catalog_failure_keeps_last_success(self):
        now = timezone.now()
        self.assertEqual(refresh_if_due(api_key="secret", now=now,
                          fetcher=lambda key: [entry("gemini-3.5-flash-lite")]),
                         "refreshed")
        state = GeminiCatalogState.objects.get(pk=1)
        self.assertEqual(state.discovered_count, 1)
        def failure(key):
            raise DiscoveryError("network_unavailable")
        later = now + timedelta(hours=13)
        self.assertEqual(refresh_if_due(api_key="secret", now=later, fetcher=failure),
                         "network_unavailable")
        state.refresh_from_db()
        self.assertEqual(state.last_success_at, now)
        self.assertEqual(state.last_error_code, "network_unavailable")
        self.assertTrue(GeminiModelCatalog.objects.get(pk="gemini-3.5-flash-lite").active)
        self.assertEqual(refresh_if_due(api_key="secret", now=later + timedelta(minutes=2),
                         force=True, fetcher=lambda k: []), "not_due")

    @override_settings(GEMINI_API_KEY="fake", GEMINI_OCR_ENABLED=True,
                       GEMINI_ALLOW_PREMIUM_MODELS=False,
                       GEMINI_MAX_LOCAL_REQUESTS_PER_DAY=2)
    def test_router_quota_is_project_scoped_and_not_an_exact_remaining_counter(self):
        apply_discovery([entry("gemini-3.5-flash-lite"), entry("gemini-3.6-flash")])
        owner = get_user_model().objects.create_user(username="gemini-a")
        other = get_user_model().objects.create_user(username="gemini-b")
        first = select_for_user(owner, task="ocr_simple")
        self.assertEqual(first["model"], "gemini-3.5-flash-lite")
        self.assertEqual(first["quota"], "unknown")
        record_observed_outcome(owner=owner, model=first["model"],
                                task="ocr_simple", status="model_rate_limit")
        self.assertEqual(select_for_user(other, task="ocr_simple")["model"],
                         "gemini-3.6-flash")
        record_observed_outcome(owner=owner, model="gemini-3.6-flash",
                                task="ocr_simple", status="project_quota")
        self.assertEqual(select_for_user(other)["reason"], "project_limit_or_billing")

    @override_settings(GEMINI_API_KEY="fake", GEMINI_OCR_ENABLED=True)
    def test_user_manual_model_is_strict(self):
        apply_discovery([entry("gemini-3.5-flash-lite"), entry("gemini-3.6-flash")])
        owner = get_user_model().objects.create_user(username="gemini-manual")
        GeminiPreference.objects.create(owner=owner, mode="manual",
                                        manual_model_id="gemini-3.6-flash")
        self.assertEqual(select_for_user(owner, task="ocr_simple")["model"],
                         "gemini-3.6-flash")
        record_observed_outcome(owner=owner, model="gemini-3.6-flash",
                                task="ocr_simple", status="model_rate_limit")
        self.assertIsNone(select_for_user(owner)["model"])


class ModelPreferencesApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="gemini-owner")
        self.client.force_login(self.user)

    @override_settings(GEMINI_API_KEY="", GEMINI_OCR_ENABLED=False,
                       GEMINI_ALLOW_PREMIUM_MODELS=False)
    def test_no_key_discloses_no_secrets_or_fake_remaining_quota(self):
        response = self.client.get("/api/v1/integrations/gemini/models")
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertFalse(data["configured"])
        self.assertFalse(data["ocr_enabled"])
        self.assertEqual(data["mode"], "balanced")
        self.assertIsNone(data["usage"]["provider_remaining_requests"])
        self.assertIsNone(data["usage"]["provider_remaining_tokens"])
        self.assertEqual(data["automatic_status"], "provider_not_configured")
        self.assertNotIn("GEMINI_API_KEY", str(data))

    @override_settings(GEMINI_API_KEY="fixture-only",
                       GEMINI_OCR_ENABLED=False,
                       GEMINI_ALLOW_PREMIUM_MODELS=False)
    def test_user_can_update_mode_but_cannot_choose_unknown_or_premium_model(self):
        apply_discovery([entry("gemini-3.5-flash-lite"),
                         entry("gemini-3.8-flash"),
                         entry("gemini-4-argon")])
        from json import dumps
        endpoint = "/api/v1/integrations/gemini/preferences"
        bad = self.client.post(endpoint,
            data=dumps({"mode": "manual", "manual_model_id": "gemini-4-argon"}),
            content_type="application/json")
        self.assertEqual(bad.status_code, 422, bad.content)
        expensive = self.client.post(endpoint,
            data=dumps({"mode": "manual", "manual_model_id": "gemini-3.8-flash"}),
            content_type="application/json")
        self.assertEqual(expensive.status_code, 422, expensive.content)
        good = self.client.post(endpoint,
            data=dumps({"mode": "manual", "manual_model_id": "gemini-3.5-flash-lite"}),
            content_type="application/json")
        self.assertEqual(good.status_code, 200, good.content)
        self.assertEqual(GeminiPreference.objects.get(owner=self.user).mode, "manual")

    def test_catalog_refresh_is_staff_only(self):
        denied = self.client.post("/api/v1/integrations/gemini/refresh",
                                   data="{}", content_type="application/json")
        self.assertEqual(denied.status_code, 403, denied.content)
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        with patch("processing.gemini_api.refresh_if_due", return_value="not_due") as call:
            accepted = self.client.post("/api/v1/integrations/gemini/refresh",
                                        data="{}", content_type="application/json")
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(accepted.json()["refresh_status"], "not_due")
        call.assert_called_once_with(force=True)

    def test_anonymous_cannot_access_catalog(self):
        self.client.logout()
        response = self.client.get("/api/v1/integrations/gemini/models")
        self.assertEqual(response.status_code, 401)
