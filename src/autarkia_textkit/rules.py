"""Rule constants shared by the segmenter (single source of truth)."""

from __future__ import annotations

import re

# Timestamps the model copies from history prefixes, e.g. ``[05-22 01:45]``,
# ``[今天 20:00]`` or ``[3天前 08:00]``. Stripped everywhere, not just at line
# starts, because the model can emit one mid-reply.
AI_TIMESTAMP_PATTERN_SOURCE = (
    r"\[(?:(?:\d{2,4}(?:-\d{2}){1,2}|今天|昨天|\d+天前)\s+)?"
    r"\d{2}:\d{2}(?::\d{2})?(?:\s*\([^)]+\))?\]\s*"
)
AI_TIMESTAMP_PATTERN = re.compile(AI_TIMESTAMP_PATTERN_SOURCE)

# Trailing punctuation removed at the end of a bubble. The ellipsis ``…`` is
# deliberately absent: it is part of the emotion, not noise.
TRAILING_PUNCT_CHARS = "。.，,．、；;"

# Markdown block starts: fences, headings, list items, quotes.
_MARKDOWN_BLOCK_START_RE = re.compile(r"(?m)^\s{0,3}(?:```|~~~|#{1,6}\s|[-*+]\s|>)")
# GFM table rows (whole line wrapped in pipes) must stay grouped.
_MARKDOWN_TABLE_LINE_RE = re.compile(r"^\s*\|.*\|\s*$")
# Unescaped ``$$`` marks a LaTeX block; keep the whole line.
_LATEX_MARKER_RE = re.compile(r"(?<!\\)\$\$")

CONTINUATION_ADVERBS = frozenset({"再", "又", "还", "更"})
CONTINUATION_ENDINGS = ("：", ":", "——", "—")
HARD_BUBBLE_BOUNDARY_ENDINGS = ("。", ".", "！", "!", "？", "?", "…")
EXPLICIT_SPACE_BOUNDARY_ENDINGS = HARD_BUBBLE_BOUNDARY_ENDINGS + (
    "，",
    ",",
    "；",
    ";",
)
PUNCTUATION_FOR_SPACE_GUARD = frozenset(
    "。.!！?？,，;；:：、…~～()（）[]【】{}<>《》\"'“”‘’"
)

# Short prefixes before an ellipsis merge with the following sentence instead
# of becoming their own bubble (``就是……戳废了`` stays one bubble).
ELLIPSIS_MERGE_PREFIX_LIMIT = 6

# Numbered list item: ``1. xxx`` / ``2、xxx`` / ``3) xxx``. A number followed
# by a separator only counts when actual content follows, so decimals,
# versions and dates are not mistaken for list items.
_NUMBERED_ITEM_RE = re.compile(r"(?P<num>\d{1,2})(?P<sep>[.．、)）])")
_NUMBERED_ITEM_ALLOWED_PREV = frozenset(
    "。.!！?？,，;；:：、…~～()（）[]【】{}<>《》\"'“”‘’——-—*·/|"
)
_NUMBERED_LIST_LEAD_MERGE_LIMIT = 24
_NUMBERED_LIST_LEAD_MERGE_ENDINGS = ("：", ":", "——", "—", "-", "～", "~")


__all__ = [
    "AI_TIMESTAMP_PATTERN",
    "AI_TIMESTAMP_PATTERN_SOURCE",
    "TRAILING_PUNCT_CHARS",
    "CONTINUATION_ADVERBS",
    "CONTINUATION_ENDINGS",
    "HARD_BUBBLE_BOUNDARY_ENDINGS",
    "EXPLICIT_SPACE_BOUNDARY_ENDINGS",
    "PUNCTUATION_FOR_SPACE_GUARD",
    "ELLIPSIS_MERGE_PREFIX_LIMIT",
]
