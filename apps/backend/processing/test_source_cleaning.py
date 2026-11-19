from django.test import SimpleTestCase

from .source_cleaning import source_metadata, source_text


class SourceCleaningTests(SimpleTestCase):
    def test_engagement_prefixes_are_discarded_without_erasing_substantive_text(self):
        self.assertEqual(
            source_text(
                "1,3 triệu lượt xem · 9,6K cảm xúc | The tight lie lob shot 🔥 | Dan Grieve Golf"
            ),
            "The tight lie lob shot 🔥 | Dan Grieve Golf",
        )
        self.assertEqual(
            source_text("1.2M views | 12K likes | How to hit a lob shot"),
            "How to hit a lob shot",
        )
        self.assertEqual(source_text("12K likes"), "")
        self.assertEqual(
            source_text("Cảm xúc có vai trò trong ghi nhớ.\nBài học có 12 ví dụ."),
            "Cảm xúc có vai trò trong ghi nhớ.\nBài học có 12 ví dụ.",
        )

    def test_nested_counts_are_not_retained_in_source_metadata(self):
        data = {
            "title": "99 views | Topic",
            "video": {"view_count": 99, "like_count": 12, "duration": 6},
            "fetch": {"status": "done"},
        }
        self.assertEqual(
            source_metadata(data),
            {"title": "Topic", "video": {"duration": 6}, "fetch": {"status": "done"}},
        )
