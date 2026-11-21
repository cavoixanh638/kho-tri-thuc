from datetime import datetime, timedelta, timezone
from io import BytesIO
from unittest.mock import patch

from django.test import SimpleTestCase

from .gemini_model_catalog import list_models, snapshot
from .gemini_model_policy import (
    ModelCandidate, RouterPolicy, SelectionMode, parse_model_catalog, select_model,
)


def candidate(name="gemini-new-flash", score=0.95, input_cost=0.2, output_cost=1.0,
              accessible=True, stable=True, cooldown=None):
    return ModelCandidate(
        model_id=name, supports_image_input=True, supports_text_output=True,
        supported_actions=frozenset({"generateContent"}), stable=stable,
        quality_score=score, input_cost_per_million=input_cost,
        output_cost_per_million=output_cost, accessible=accessible,
        validated_at=datetime.now(timezone.utc), cooldown_until=cooldown,
    )


class ModelGovernorTests(SimpleTestCase):
    def test_catalog_pagination_and_key_is_not_in_url(self):
        calls = []
        class Response:
            def __init__(self, data):
                self.data = data
            def __enter__(self): return self
            def __exit__(self, *args): return None
            def read(self, limit): return self.data
        pages = [
            b'{"models":[{"name":"models/gemini-one","supportedGenerationMethods":["generateContent"]}],"nextPageToken":"second"}',
            b'{"models":[{"name":"models/gemini-two","supportedGenerationMethods":["embedContent"]}]}',
        ]
        def transport(request, timeout):
            calls.append(request)
            return Response(pages[len(calls)-1])
        models = list_models("synthetic-secret", transport=transport)
        self.assertEqual([item["model_id"] for item in models], ["gemini-one", "gemini-two"])
        self.assertEqual(len(calls), 2)
        self.assertIn("pageToken=second", calls[1].full_url)
        for request in calls:
            self.assertNotIn("synthetic-secret", request.full_url)
            self.assertEqual(request.get_header("X-goog-api-key"), "synthetic-secret")

    def test_invalid_catalog_does_not_masquerade_as_available(self):
        with self.assertRaisesRegex(ValueError, "invalid_models_list"):
            parse_model_catalog({"models": "not an array"})
        with self.assertRaisesRegex(ValueError, "missing_or_invalid"):
            list_models("")

    def test_delta_reports_new_removed_and_changed_models(self):
        previous = {"models": [
            {"model_id": "old", "x": 1}, {"model_id": "changed", "x": 1}
        ]}
        output = snapshot([{"model_id": "changed", "x": 2}, {"model_id": "new"}], previous)
        self.assertEqual(output["new_models"], ["new"])
        self.assertEqual(output["removed_models"], ["old"])
        self.assertEqual(output["changed_models"], ["changed"])
        self.assertEqual(output["quota_information"], "NOT_AVAILABLE_IN_MODELS_LIST")

    def test_auto_modes_and_manual_pin(self):
        efficient = candidate("flash-lite", 0.93, .1, .4)
        stronger = candidate("flash", .98, .7, 2.5)
        models = [stronger, efficient]
        self.assertEqual(select_model(models, RouterPolicy(mode=SelectionMode.ECONOMY)), "flash-lite")
        self.assertEqual(select_model(models, RouterPolicy(mode=SelectionMode.QUALITY)), "flash")
        self.assertEqual(select_model(models, RouterPolicy(mode=SelectionMode.MANUAL,
                         manual_model_id="flash-lite")), "flash-lite")

    def test_denies_unvalidated_preview_limited_and_cooling_models(self):
        now = datetime.now(timezone.utc)
        ok = candidate("allowed")
        disallowed = [
            candidate("preview", stable=False),
            candidate("unavailable", accessible=False),
            candidate("cooldown", cooldown=now + timedelta(minutes=4)),
            candidate("weak", score=.5),
            candidate("too-expensive", input_cost=10.0),
        ]
        self.assertEqual(select_model([*disallowed, ok], RouterPolicy(), now), "allowed")
        self.assertIsNone(select_model(disallowed, RouterPolicy(), now))
        self.assertIsNone(select_model([ok], RouterPolicy(mode=SelectionMode.MANUAL,
                             manual_model_id="missing"), now))
