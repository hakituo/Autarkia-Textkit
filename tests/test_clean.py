"""Cleaning and display grouping tests."""

from autarkia_textkit import (
    clean_chat_text,
    is_ellipsis_only,
    split_for_display,
    strip_ai_timestamp,
    strip_trailing_punctuation,
)


class TestTimestamps:
    def test_leading_timestamp(self):
        assert strip_ai_timestamp("[05-22 01:45] 早啊") == "早啊"

    def test_relative_timestamp(self):
        assert strip_ai_timestamp("[今天 20:00] 在吗") == "在吗"
        assert strip_ai_timestamp("[3天前 08:00] 早") == "早"

    def test_mid_text_timestamp(self):
        assert strip_ai_timestamp("刚回来[昨天 22:10] 你睡了吗") == "刚回来你睡了吗"

    def test_plain_time_not_stripped(self):
        assert strip_ai_timestamp("现在 20:00 了") == "现在 20:00 了"


class TestTrailingPunctuation:
    def test_period_removed(self):
        assert strip_trailing_punctuation("好呀好呀。") == "好呀好呀"

    def test_comma_removed(self):
        assert strip_trailing_punctuation("噢噢，好呀好呀，") == "噢噢，好呀好呀"

    def test_mid_sentence_punctuation_kept(self):
        assert strip_trailing_punctuation("好呀，走吧") == "好呀，走吧"

    def test_period_before_parenthesis_removed(self):
        assert strip_trailing_punctuation("笑。（真的）") == "笑（真的）"

    def test_period_inside_parenthesis_removed(self):
        assert strip_trailing_punctuation("（笑。）") == "（笑）"

    def test_ellipsis_preserved(self):
        assert strip_trailing_punctuation("就是……") == "就是……"

    def test_ellipsis_only_preserved(self):
        assert strip_trailing_punctuation("……") == "……"
        assert strip_trailing_punctuation("...") == "..."
        assert strip_trailing_punctuation(". . .") == ". . ."

    def test_single_dot_is_not_ellipsis_only(self):
        assert is_ellipsis_only(".") is False
        assert is_ellipsis_only("……") is True
        assert is_ellipsis_only("……好") is False

    def test_clean_combines_both(self):
        assert clean_chat_text("[今天 20:00] 好呀好呀。") == "好呀好呀"


class TestDisplayGrouping:
    def test_empty(self):
        assert split_for_display("") == []

    def test_plain_text_splits(self):
        chunks = split_for_display(
            "我觉得你今天真的特别辛苦，早点休息吧。明天还要早起呢。",
            min_split_len=10,
        )
        assert len(chunks) == 2
        assert chunks[0].endswith("吧")
        assert chunks[1] == "明天还要早起呢"

    def test_code_block_stays_whole(self):
        text = "看这个：\n```python\nprint(1)\nprint(2)\n```\n就这样。"
        chunks = split_for_display(text)
        code = [chunk for chunk in chunks if "```" in chunk]
        assert len(code) == 1
        assert "print(1)" in code[0] and "print(2)" in code[0]

    def test_table_stays_whole(self):
        text = "| a | b |\n| - | - |\n| 1 | 2 |"
        assert split_for_display(text) == ["| a | b |\n| - | - |\n| 1 | 2 |"]

    def test_heading_is_atomic(self):
        chunks = split_for_display("# 标题\n正文内容。")
        assert chunks[0] == "# 标题"
        assert chunks[1] == "正文内容"

    def test_latex_line_is_atomic(self):
        text = "$$E = mc^2$$\n结论是这个。"
        chunks = split_for_display(text)
        assert chunks[0] == "$$E = mc^2$$"

    def test_timestamp_and_trailing_cleanup(self):
        assert split_for_display("[今天 20:00] 好呀好呀。") == ["好呀好呀"]

    def test_fence_unclosed_streams_to_end(self):
        text = "开头。\n```\ncode"
        chunks = split_for_display(text)
        assert any("```" in chunk and "code" in chunk for chunk in chunks)
