"""Autarkia-Textkit: Chinese chat text segmentation and set similarity."""

from .clean import (
    clean_chat_text,
    is_ellipsis_only,
    split_for_display,
    strip_ai_timestamp,
    strip_trailing_punctuation,
)
from .emoji import EMOJI_RANGES, is_emoji_char
from .force import (
    force_split_long_sentence,
    has_unclosed_inline_span,
    repair_broken_inline_spans,
)
from .merge import (
    HAS_JIEBA,
    glue_cjk_ascii_spaces,
    is_continuation_start,
    looks_like_manual_space_split,
    merge_chunks_to_limit,
    merge_continuation_chunks,
    merge_space_chunks_to_limit,
)
from .numbered import (
    find_numbered_list_starts,
    is_numbered_item_start,
    normalize_numbered_list,
)
from .rules import (
    AI_TIMESTAMP_PATTERN,
    AI_TIMESTAMP_PATTERN_SOURCE,
    CONTINUATION_ADVERBS,
    CONTINUATION_ENDINGS,
    ELLIPSIS_MERGE_PREFIX_LIMIT,
    EXPLICIT_SPACE_BOUNDARY_ENDINGS,
    HARD_BUBBLE_BOUNDARY_ENDINGS,
    PUNCTUATION_FOR_SPACE_GUARD,
    TRAILING_PUNCT_CHARS,
)
from .segmenter import split_chat_message
from .similarity import (
    char_ngrams,
    cjk_bigrams,
    cjk_chars,
    containment,
    intersection_over_max,
    jaccard,
    token_ngrams,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # rules
    "AI_TIMESTAMP_PATTERN",
    "AI_TIMESTAMP_PATTERN_SOURCE",
    "CONTINUATION_ADVERBS",
    "CONTINUATION_ENDINGS",
    "ELLIPSIS_MERGE_PREFIX_LIMIT",
    "EXPLICIT_SPACE_BOUNDARY_ENDINGS",
    "HARD_BUBBLE_BOUNDARY_ENDINGS",
    "PUNCTUATION_FOR_SPACE_GUARD",
    "TRAILING_PUNCT_CHARS",
    # emoji
    "EMOJI_RANGES",
    "is_emoji_char",
    # cleaning / display
    "clean_chat_text",
    "is_ellipsis_only",
    "split_for_display",
    "strip_ai_timestamp",
    "strip_trailing_punctuation",
    # splitting
    "split_chat_message",
    "force_split_long_sentence",
    "repair_broken_inline_spans",
    "has_unclosed_inline_span",
    # numbered lists
    "find_numbered_list_starts",
    "is_numbered_item_start",
    "normalize_numbered_list",
    # merging
    "HAS_JIEBA",
    "is_continuation_start",
    "glue_cjk_ascii_spaces",
    "looks_like_manual_space_split",
    "merge_chunks_to_limit",
    "merge_continuation_chunks",
    "merge_space_chunks_to_limit",
    # similarity
    "intersection_over_max",
    "containment",
    "jaccard",
    "char_ngrams",
    "token_ngrams",
    "cjk_chars",
    "cjk_bigrams",
]
