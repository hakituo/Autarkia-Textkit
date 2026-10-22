"""Merge helpers, forced splitting, numbered lists, emoji and similarity."""

from autarkia_textkit import (
    char_ngrams,
    cjk_bigrams,
    cjk_chars,
    containment,
    find_numbered_list_starts,
    force_split_long_sentence,
    glue_cjk_ascii_spaces,
    has_unclosed_inline_span,
    intersection_over_max,
    is_continuation_start,
    is_emoji_char,
    is_numbered_item_start,
    jaccard,
    looks_like_manual_space_split,
    merge_chunks_to_limit,
    merge_continuation_chunks,
    merge_space_chunks_to_limit,
    normalize_numbered_list,
    repair_broken_inline_spans,
    token_ngrams,
)


class TestGlueSpaces:
    def test_cjk_number(self):
        assert glue_cjk_ascii_spaces("睡 4 小时") == "睡4小时"

    def test_cjk_latin(self):
        assert glue_cjk_ascii_spaces("就是 DMT 了") == "就是DMT了"

    def test_greek(self):
        assert glue_cjk_ascii_spaces("回归的 β 和") == "回归的β和"

    def test_cjk_cjk_space_kept(self):
        assert glue_cjk_ascii_spaces("今天 天气") == "今天 天气"


class TestManualSpaceSplit:
    def test_phrases_detected(self):
        assert looks_like_manual_space_split("今天 天气 真好 呀") is True

    def test_typographic_spaces_not_detected(self):
        assert looks_like_manual_space_split("还有你昨天睡 4 小时 51 分") is False

    def test_punctuation_disables(self):
        assert looks_like_manual_space_split("今天，天气 真好 呀") is False

    def test_too_few_parts(self):
        assert looks_like_manual_space_split("今天 天气") is False

    def test_long_part_disables(self):
        assert looks_like_manual_space_split("今天 天气 真的特别好特别舒服特别开心 呀") is False


class TestChunkMerging:
    def test_merge_to_limit(self):
        chunks = [f"第{i}句" for i in range(9)]
        merged = merge_chunks_to_limit(chunks, max_chunks=6)
        assert len(merged) == 6
        assert "".join(merged) == "".join(chunks)

    def test_no_merge_needed(self):
        assert merge_chunks_to_limit(["a", "b"], max_chunks=6) == ["a", "b"]

    def test_continuation_word_merges_short_prefix(self, monkeypatch):
        monkeypatch.setattr("autarkia_textkit.merge.is_continuation_start", lambda text: text.startswith("然后"))
        assert merge_continuation_chunks(["我去做饭", "然后吃饭"], min_split_len=40) == ["我去做饭然后吃饭"]

    def test_continuation_word_not_merged_after_sentence_end(self, monkeypatch):
        monkeypatch.setattr("autarkia_textkit.merge.is_continuation_start", lambda text: text.startswith("然后"))
        chunks = merge_continuation_chunks(["我去做饭。", "然后吃饭"], min_split_len=40)
        assert len(chunks) == 2

    def test_open_ending_merges(self, monkeypatch):
        monkeypatch.setattr("autarkia_textkit.merge.is_continuation_start", lambda text: False)
        assert merge_continuation_chunks(["我跟你说：", "明天要早起"], min_split_len=40) == ["我跟你说：明天要早起"]

    def test_max_merge_len_blocks(self, monkeypatch):
        monkeypatch.setattr("autarkia_textkit.merge.is_continuation_start", lambda text: False)
        chunks = merge_continuation_chunks(["长" * 20 + "：", "后面"], max_merge_len=10)
        assert len(chunks) == 2

    def test_fallback_continuation_detection(self):
        # Works with or without the optional jieba extra.
        assert is_continuation_start("然后我们去吃饭") is True
        assert is_continuation_start("还有你昨天睡得怎么样") is True
        assert is_continuation_start("今天天气不错") is False

    def test_merge_space_chunks(self):
        chunks = [f"第{i}段" for i in range(9)]
        merged = merge_space_chunks_to_limit(chunks, max_chunks=6)
        assert len(merged) == 6
        assert " ".join(merged).replace(" ", "") == "".join(chunks)


class TestForceSplit:
    def test_short_text_untouched(self):
        assert force_split_long_sentence("短句", max_len=10) == ["短句"]

    def test_long_text_split(self):
        text = "一二三四五六七八九十一二三四五六七八九十，" * 5
        chunks = force_split_long_sentence(text, max_len=30, max_chunks=4)
        assert 1 < len(chunks) <= 4
        assert all(chunk.strip() for chunk in chunks)

    def test_unclosed_span_detection(self):
        assert has_unclosed_inline_span("**abc") is True
        assert has_unclosed_inline_span("**abc**") is False
        assert has_unclosed_inline_span("`code") is True
        assert has_unclosed_inline_span("\\*\\*escaped") is False

    def test_repair_merges_split_bold(self):
        assert repair_broken_inline_spans(["**古之人", "** 顺便说"]) == ["**古之人** 顺便说"]

    def test_repair_leaves_balanced(self):
        assert repair_broken_inline_spans(["a", "b"]) == ["a", "b"]


class TestNumberedLists:
    def test_find_inline_list(self):
        starts = find_numbered_list_starts("做法：1. 洗 2. 切 3. 炒")
        assert len(starts) == 3

    def test_single_item_is_not_a_list(self):
        assert find_numbered_list_starts("只有 1. 一项") == []

    def test_decimal_not_a_list(self):
        assert find_numbered_list_starts("版本 1.2 到 1.3") == []

    def test_numbered_start_allows_punctuation(self):
        assert is_numbered_item_start("：1. 项", 1) is True
        assert is_numbered_item_start("a1. 项", 1) is False
        assert is_numbered_item_start("11. 项", 1) is False

    def test_normalize_merges_short_lead(self):
        normalized = normalize_numbered_list("这样做：1. 先洗手 2. 再吃饭")
        assert normalized.split("\n")[0] == "这样做：1. 先洗手"

    def test_normalize_keeps_long_lead_separate(self):
        lead = "这是一段很长的前言内容需要单独成为一段而不是和列表挤在一起"
        normalized = normalize_numbered_list(f"{lead} 1. 先洗手 2. 再吃饭")
        lines = normalized.split("\n")
        assert lines[0] == lead
        assert lines[1].startswith("1.")


class TestEmoji:
    def test_emoji_detected(self):
        assert is_emoji_char("😊") is True
        assert is_emoji_char("🎉") is True
        assert is_emoji_char("。") is False
        assert is_emoji_char("") is False


class TestSimilarity:
    def test_intersection_over_max(self):
        assert intersection_over_max({1, 2, 3}, {2, 3, 4, 5}) == 2 / 4

    def test_containment_is_one_for_subset(self):
        assert containment({1, 2}, {1, 2, 3, 4}) == 1.0

    def test_jaccard(self):
        assert jaccard({1, 2, 3}, {2, 3, 4}) == 2 / 4

    def test_measures_differ(self):
        a, b = {1, 2}, {1, 2, 3, 4}
        assert containment(a, b) == 1.0
        assert intersection_over_max(a, b) == 0.5
        assert jaccard(a, b) == 0.5

    def test_empty_inputs(self):
        assert intersection_over_max(set(), {1}) == 0.0
        assert containment({1}, set()) == 0.0
        assert jaccard(set(), set()) == 0.0

    def test_char_ngrams(self):
        assert char_ngrams("abc", 2) == {"ab", "bc"}
        assert char_ngrams("a", 2) == {"a"}
        assert char_ngrams("", 2) == set()

    def test_token_ngrams(self):
        assert token_ngrams(["a", "b", "c"], 2) == {("a", "b"), ("b", "c")}
        assert token_ngrams([], 2) == set()

    def test_cjk_chars(self):
        assert cjk_chars("a你b好") == {"你", "好"}

    def test_cjk_bigrams(self):
        assert cjk_bigrams("a你好b") == {"你好"}
