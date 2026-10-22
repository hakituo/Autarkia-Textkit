"""Main splitter behavior tests (deterministic RNG where needed)."""

import random

from autarkia_textkit import split_chat_message


class TestBasics:
    def test_empty(self):
        assert split_chat_message("") == []
        assert split_chat_message(None) == []

    def test_short_text_returns_one(self):
        assert split_chat_message("早") == ["早"]

    def test_sentence_split_after_min_length(self):
        text = "我觉得你今天真的特别辛苦，早点休息吧。明天还要早起呢。"
        assert split_chat_message(text, min_split_len=10) == [
            "我觉得你今天真的特别辛苦，早点休息吧",
            "明天还要早起呢",
        ]

    def test_terminal_punctuation_kept_for_questions(self):
        text = "你吃饭了吗？我也刚吃完。"
        chunks = split_chat_message(text, min_split_len=10)
        assert chunks[0].endswith("？")

    def test_no_more_than_six_chunks(self):
        text = "第一句话很长很长很长。第二句也很长很长。第三句还是很长。第四句继续。第五句。第六句。第七句。"
        chunks = split_chat_message(text, min_split_len=10)
        assert len(chunks) <= 6

    def test_explicit_newlines_preserved(self):
        assert split_chat_message("第一行\n第二行") == ["第一行", "第二行"]

    def test_escaped_newline_normalized(self):
        assert split_chat_message("第一行\\n第二行") == ["第一行", "第二行"]

    def test_pass_through_marker(self):
        text = "[CQ:image,file=abc]"
        assert split_chat_message(text, pass_through_markers=("[CQ:",)) == [text]

    def test_preprocess_applied(self):
        chunks = split_chat_message("**早** 今天怎么样", preprocess=lambda s: s.replace("**", ""))
        assert chunks == ["早 今天怎么样"]

    def test_bracketed_prefix_stays_whole(self):
        assert split_chat_message("[THINK_STORE: internal]") == ["[THINK_STORE: internal]"]


class TestParenthesesAndQuotes:
    def test_punctuation_inside_parentheses_does_not_split(self):
        text = "他昨天说（其实我早就知道了，只是没说。）然后走了。"
        chunks = split_chat_message(text, min_split_len=10)
        assert len(chunks) == 1
        assert "（其实我早就知道了，只是没说）" in chunks[0] or "（其实我早就知道了，只是没说。）" in chunks[0]

    def test_math_range_not_split(self):
        text = "取值范围是 [1, 3] 之间，别搞错了。"
        assert split_chat_message(text, min_split_len=10) == ["取值范围是 [1, 3] 之间，别搞错了。"]

    def test_quoted_newlines_removed(self):
        text = "“\n第一行第二行\n”"
        assert split_chat_message(text) == ["“第一行第二行”"]

    def test_contraction_apostrophe_not_a_quote(self):
        assert split_chat_message("it's fine") == ["it's fine"]


class TestEllipsis:
    def test_short_prefix_merges_with_following_sentence(self):
        text = "就是……戳废了两个半成品。"
        assert split_chat_message(text, min_split_len=10) == ["就是……戳废了两个半成品。"]

    def test_full_sentence_before_ellipsis_splits(self):
        text = "倒是你，声音听起来有点飘……是困了吧。"
        chunks = split_chat_message(text, min_split_len=10)
        assert len(chunks) >= 2
        assert chunks[0].endswith("……")

    def test_ellipsis_exclamation_stays_together(self):
        text = "……哈？！"
        assert split_chat_message(text) == ["……哈？！"]

    def test_ascii_ellipsis(self):
        chunks = split_chat_message("等等我...马上到", min_split_len=10)
        assert len(chunks) >= 1


class TestEmoji:
    def test_emoji_glued_after_punctuation(self):
        chunks = split_chat_message("真的吗？😊 那就好。", min_split_len=10)
        assert chunks[0].endswith("😊")
        assert len(chunks) == 2


class TestNumberedLists:
    def test_inline_list_split_into_items(self):
        text = "你可以这样做：1. 先洗手 2. 再吃饭 3. 最后刷牙"
        chunks = split_chat_message(text, min_split_len=10)
        assert len(chunks) == 3
        assert chunks[0].startswith("你可以这样做：1.") or chunks[0].startswith("1.")
        assert chunks[1].startswith("2.")
        assert chunks[2].startswith("3.")

    def test_decimal_not_a_list(self):
        assert split_chat_message("版本是 1.2.3，别升级。") == ["版本是 1.2.3，别升级。"]

    def test_version_number_not_split(self):
        text = "现在跑的是 v1.2.3 版本。"
        assert split_chat_message(text, min_split_len=10) == [text]


class TestManualSpaceSplit:
    def test_space_separated_phrases(self):
        chunks = split_chat_message("今天 天气 真好 呀")
        assert len(chunks) >= 1
        assert all(chunk.strip() for chunk in chunks)

    def test_typographic_space_not_manual(self):
        assert split_chat_message("还有你昨天睡 4 小时 51 分") == ["还有你昨天睡 4 小时 51 分"]

    def test_greek_letter_not_manual(self):
        assert split_chat_message("再往旁边是回归的 β 和 SE") == ["再往旁边是回归的 β 和 SE"]


class TestDeterminism:
    def test_same_seed_same_split(self):
        text = "这句话有点长，需要按逗号决定切不切，再来一个逗号，看看结果如何。"
        first = split_chat_message(text, max_len=20, comma_split_prob=0.9, rng=random.Random(7))
        second = split_chat_message(text, max_len=20, comma_split_prob=0.9, rng=random.Random(7))
        assert first == second

    def test_zero_probability_never_comma_splits(self):
        text = "今天真的很开心，吃了好吃的，还看了电影，晚上早点睡。"
        chunks = split_chat_message(text, max_len=10, comma_split_prob=0.0, rng=random.Random(1))
        assert len(chunks) == 1
