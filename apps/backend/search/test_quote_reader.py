import json
import unicodedata
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from catalog.models import Item, ItemTopic, Topic
from search import quote_reader


def model_response(hits, finish="stop"):
    return {
        "choices": [{"finish_reason": finish, "message": {"content": json.dumps({"hits": hits})}}],
        "usage": {"prompt_tokens": 76, "completion_tokens": 14},
    }


class QuoteReaderTests(SimpleTestCase):
    def test_question_or_record(self):
        for text, expected in (
            ("Liệu quầy có nhận đổi sách đã viết tên?", "polar"),
            ("Quầy không nhận sách đã viết tên, đúng không?", "polar"),
            ("Có ghi chú xác nhận quầy nhận sách viết tên không?", "record"),
            ("Ghi chú nào xác nhận quầy nhận sách viết tên?", "record"),
            ("Có ghi chú nói quầy nhận sách vào ngày nào không?", None),
            ("Sách viết tên phải gửi cho ai?", None),
            ("quy định trả sách ở nhà văn hóa", None),
        ):
            with self.subTest(text=text):
                self.assertEqual(quote_reader.intent(text), expected)

    def test_long_original_lines_remain_verbatim_and_in_source_order(self):
        phrase = unicodedata.normalize("NFD", "Quầy chỉ nhận bìa bọc tháo rời.")
        text = "Tiêu đề\n" + ("hộp " * 140) + "\nMột. Hai. Ba. Bốn. Năm.\n" + phrase
        selected = quote_reader.source_lines(text, phrase)
        self.assertEqual(selected[0], "Tiêu đề")
        self.assertIn(phrase, selected)
        self.assertLessEqual(len(selected), quote_reader.MAX_LINES)
        self.assertTrue(all(part in text and len(part) <= quote_reader.MAX_LINE_CHARS for part in selected))
        self.assertEqual([text.index(part) for part in selected], sorted(text.index(part) for part in selected))

    def test_source_indices_and_original_question_determine_display(self):
        text = "Đổi sách\nTên viết trên trang thì quầy từ chối.\nChỉ nhận bìa bọc tháo rời."
        question = "Quầy nhận sách viết tên ngay trên trang không?"
        decision = {"d": 0, "a": "no", "s": [2, 1]}
        with patch.object(quote_reader, "_request", return_value=model_response([decision])) as call:
            matches, check = quote_reader.verify(question, "polar", [text])
            self.assertEqual(call.call_args.args, (question, "polar", [text.splitlines()]))
            self.assertEqual(matches, {0: quote_reader.Verification("no", tuple(text.splitlines()[1:]))})
            self.assertEqual((check.status, check.prompt_tokens, check.completion_tokens), ("checked", 76, 14))
            self.assertGreaterEqual(check.elapsed_ms, 0)
            record_matches, _ = quote_reader.verify(question, "record", [text])
            self.assertEqual(record_matches, {})

    def test_missing_evidence_and_invalid_replies_have_different_status(self):
        cases = [
            (model_response([]), "checked"),
            (model_response([], finish="length"), "unavailable"),
            (model_response([{"d": 1, "a": "no", "s": [0]}]), "unavailable"),
            (model_response([{"d": 0, "a": "no", "s": [1]}]), "unavailable"),
            (model_response([{"d": 0, "a": "yes", "s": [True]}]), "unavailable"),
            (model_response([{"d": 0, "a": "yes", "s": ["câu do mô hình viết"]}]), "unavailable"),
            (model_response([{"d": 0, "a": "yes", "s": [0]}, {"d": 0, "a": "no", "s": [0]}]), "unavailable"),
            ({"choices": [{"finish_reason": "stop", "message": {"content": ""}}]}, "unavailable"),
        ]
        for reply, expected in cases:
            with self.subTest(reply=reply), patch.object(quote_reader, "_request", return_value=reply):
                matches, check = quote_reader.verify("Có mượn được máy không?", "polar", ["Sổ giao máy."])
                self.assertEqual(check.status, expected)
                self.assertEqual(matches, {} if expected == "checked" else None)

    def test_only_the_configured_loopback_chat_endpoint_receives_material(self):
        for url in ("https://example.invalid/v1/chat/completions", "http://localhost/other",
                    "http://user:pass@127.0.0.1/v1/chat/completions"):
            with self.subTest(url=url), self.settings(SEARCH_QUOTE_READER_URL=url), patch("http.client.HTTPConnection") as conn:
                matches, check = quote_reader.verify("Có mượn được máy không?", "polar", ["Sổ giao máy."])
                self.assertIsNone(matches)
                self.assertEqual(check.status, "unavailable")
                conn.assert_not_called()


@override_settings(SEARCH_BGE_MODEL_DIR="", SEARCH_QUOTE_EVIDENCE_ENABLED=True)
class ClickEvidenceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create_user(username="owner-quote")
        other = users.create_user(username="other-quote")
        cls.topic = Topic.objects.create(owner=cls.owner, name="Dây thuyền")
        cls.items = []
        for index in range(13):
            item = Item.objects.create(
                owner=other if index == 10 else cls.owner, kind=Item.Kind.TEXT,
                title=f"Móc dây {index:02}", description="Sổ tay", note=f"Cất buồm trước bão, kệ {index:02}.",
                deleted_at=timezone.now() if index == 11 else None,
            )
            if index != 12:
                ItemTopic.objects.create(item=item, topic=cls.topic)
            cls.items.append(item)

    def setUp(self):
        self.client.force_login(self.owner)
        self.params = {"q": "dây buồm mạn thuyền", "topic_id": self.topic.pk,
                       "exclude_item_id": str(self.items[9].pk), "limit": 25}

    def page(self, **changes):
        response = self.client.get("/api/v1/search", {**self.params, **changes})
        self.assertEqual(response.status_code, 200)
        return response.json()

    @patch.object(quote_reader, "_request")
    def test_default_disabled_open_questions_and_group_browse(self, provider):
        with self.settings(SEARCH_QUOTE_EVIDENCE_ENABLED=False):
            default = self.page()
            old_click = self.page(expand="true")
            old_group = self.page(q="")
        self.assertTrue(default["can_expand"])
        self.assertEqual(self.page(), default)
        self.assertEqual(self.page(q=""), old_group)
        self.assertEqual(self.page(expand="true"), old_click)
        for query in ("Móc dây", "AX3917", ""):
            self.assertNotIn("quote_check", self.page(q=query, expand="true"))
        provider.assert_not_called()

    @patch.object(quote_reader, "intent", return_value="polar")
    def test_scoped_source_sentences_and_next_page_after_abstention(self, intent):
        with self.settings(SEARCH_QUOTE_EVIDENCE_ENABLED=False):
            control = self.page(expand="true")
        self.assertEqual(len(control["results"]), 9)
        with patch.object(quote_reader, "_request", return_value=model_response([])) as provider:
            first = self.page(expand="true")
            self.assertEqual(first["results"], [])
            self.assertEqual(first["quote_check"]["status"], "checked")
            self.assertEqual(first["next_cursor"]["item_id"], control["results"][4]["item_id"])
            cursor = first["next_cursor"]
            provider.return_value = model_response([{"d": 0, "a": "no", "s": [2]}])
            second = self.page(expand="true", cursor_score=cursor["score"], cursor_item_id=cursor["item_id"])
        self.assertIsNone(second["next_cursor"])
        self.assertEqual(second["results"][0]["item_id"], control["results"][5]["item_id"])
        title = control["results"][5]["title"]
        self.assertEqual(second["results"][0]["verification"], {
            "answer": "no", "quotes": [f"Cất buồm trước bão, kệ {title[-2:]}."]})
        sent = [doc[0] for call in provider.call_args_list for doc in call.args[2]]
        self.assertEqual(sent, [result["title"] for result in control["results"]])
        self.assertEqual(len(set(sent)), 9)

    @patch.object(quote_reader, "intent", return_value="polar")
    def test_reordered_candidate_keeps_its_own_source_and_lexical_cursor(self, intent):
        self.params["limit"] = 5
        with self.settings(SEARCH_QUOTE_EVIDENCE_ENABLED=False):
            lexical = self.page(expand="true")
        with self.settings(SEARCH_BGE_MODEL_DIR="fixture"), patch(
            "search.reranking.rerank_order", side_effect=lambda q, docs: tuple(reversed(range(len(docs))))
        ), patch.object(quote_reader, "_request", return_value=model_response([{"d": 0, "a": "yes", "s": [2]}])) as reader:
            result = self.page(expand="true")
        ranked_titles = [hit["title"] for hit in reversed(lexical["results"])]
        self.assertEqual([doc[0] for doc in reader.call_args.args[2]], ranked_titles)
        self.assertEqual(result["next_cursor"], lexical["next_cursor"])
        self.assertEqual(result["results"][0]["item_id"], lexical["results"][-1]["item_id"])
        self.assertEqual(result["results"][0]["verification"]["quotes"], [f"Cất buồm trước bão, kệ {ranked_titles[0][-2:]}."])

    @patch.object(quote_reader, "intent", return_value="polar")
    @patch.object(quote_reader, "_request", side_effect=TimeoutError)
    def test_reader_failure_restores_full_ui_page_even_with_bge(self, provider, intent):
        with self.settings(SEARCH_BGE_MODEL_DIR="fixture"), patch(
            "search.reranking.rerank_order", side_effect=lambda q, docs: tuple(reversed(range(len(docs))))
        ):
            with self.settings(SEARCH_QUOTE_EVIDENCE_ENABLED=False):
                original = self.page(expand="true")
            fallback = self.page(expand="true")
        self.assertEqual(fallback.pop("quote_check")["status"], "unavailable")
        self.assertEqual(fallback, original)
        self.assertEqual(len(fallback["results"]), 9)
        self.assertEqual(fallback["ranking"], "bge")
        provider.assert_called_once()
