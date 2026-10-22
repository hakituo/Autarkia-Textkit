"""Continuation detection and chunk merging.

With ``jieba`` installed, the first non-punctuation token's POS tag decides
whether a chunk begins with a continuation (conjunction ``c`` or an adverb
stem like 再/又/还/更). Without ``jieba`` the library falls back to a compact
conjunction prefix list, so the package stays dependency-free by default.
"""

from __future__ import annotations

import logging
import re

from .rules import (
    CONTINUATION_ADVERBS,
    CONTINUATION_ENDINGS,
    EXPLICIT_SPACE_BOUNDARY_ENDINGS,
    PUNCTUATION_FOR_SPACE_GUARD,
)

try:  # optional dependency
    import jieba
    import jieba.posseg as pseg

    HAS_JIEBA = True
    jieba.setLogLevel(logging.INFO)
except ImportError:  # pragma: no cover - exercised only without the extra
    pseg = None
    HAS_JIEBA = False

# Fallback prefixes used when jieba is unavailable. Kept intentionally small:
# they cover the conjunctions/continuations that actually appear at bubble
# starts, without pretending to be a full POS tagger.
_CONTINUATION_PREFIXES = (
    "然后",
    "而且",
    "并且",
    "但是",
    "不过",
    "所以",
    "因为",
    "虽然",
    "如果",
    "要是",
    "不然",
    "否则",
    "于是",
    "接着",
    "随后",
    "同时",
    "另外",
    "再说",
    "还有",
    "反正",
    "毕竟",
    "其实",
    "只是",
    "就是",
) + tuple(CONTINUATION_ADVERBS)


_PUNCTUATION_CHARS = "".join(PUNCTUATION_FOR_SPACE_GUARD)


def is_continuation_start(text: str) -> bool:
    """Whether the text starts with a continuation word.

    Leading punctuation is skipped. With jieba, the first token's POS decides;
    otherwise a prefix list is used.
    """
    if not text or not text.strip():
        return False
    stripped = text.strip()[:30]

    if HAS_JIEBA and pseg is not None:
        for word, flag in pseg.cut(stripped):
            if not word.strip():
                continue
            if flag in ("x", "w"):
                continue
            if flag == "c":
                return True
            return any(word.startswith(adverb) for adverb in CONTINUATION_ADVERBS)

    cleaned = stripped.lstrip(_PUNCTUATION_CHARS)
    return any(cleaned.startswith(prefix) for prefix in _CONTINUATION_PREFIXES)


def merge_chunks_to_limit(chunks: list[str], max_chunks: int = 7) -> list[str]:
    """Merge the shortest adjacent pairs until at most ``max_chunks`` remain."""
    if len(chunks) <= max_chunks:
        return chunks

    result = list(chunks)
    for _ in range(len(result) - max_chunks):
        min_len = float("inf")
        merge_index = -1
        for index in range(len(result) - 1):
            combined_len = len(result[index]) + len(result[index + 1])
            if combined_len < min_len:
                min_len = combined_len
                merge_index = index
        if merge_index < 0:
            break
        result[merge_index] = result[merge_index] + result[merge_index + 1]
        result.pop(merge_index + 1)
    return result


def merge_continuation_chunks(
    chunks: list[str], max_merge_len: int = 300, min_split_len: int = 40
) -> list[str]:
    """Merge unnatural breaks caused by continuation words or open endings."""
    if len(chunks) <= 1:
        return chunks

    result = [chunks[0]]
    for index in range(1, len(chunks)):
        prev = result[-1]
        curr = chunks[index]
        curr_stripped = curr.strip()
        prev_stripped = prev.strip()

        should_merge = False
        if is_continuation_start(curr_stripped):
            prev_ends_with_sentence_punct = bool(
                prev_stripped
                and any(
                    prev_stripped.endswith(ending)
                    for ending in EXPLICIT_SPACE_BOUNDARY_ENDINGS
                )
            )
            if not prev_ends_with_sentence_punct and len(prev_stripped) < min_split_len:
                should_merge = True

        if prev_stripped and any(
            prev_stripped.endswith(ending) for ending in CONTINUATION_ENDINGS
        ):
            should_merge = True

        if should_merge and len(prev) + len(curr) <= max_merge_len:
            result[-1] = prev + curr
        else:
            result.append(curr)
    return result


# A space between a CJK character and a Latin/digit/Greek/math character is
# typography, not a manual bubble separator.
_CJK_ASCII_SPACE_RE = re.compile(
    r"(?<=[\u4e00-\u9fff])[ \t]+"
    r"(?=[0-9A-Za-z\u00c0-\u024f\u0370-\u03ff\u0400-\u04ff"
    r"\u1e00-\u1eff\u2070-\u209f\u2150-\u218f\u2200-\u22ff])"
    r"|(?<=[0-9A-Za-z\u00c0-\u024f\u0370-\u03ff\u0400-\u04ff"
    r"\u1e00-\u1eff\u2070-\u209f\u2150-\u218f\u2200-\u22ff])[ \t]+"
    r"(?=[\u4e00-\u9fff])"
)


def glue_cjk_ascii_spaces(text: str) -> str:
    """Remove typographic spaces between CJK and Latin/number/math characters."""
    return _CJK_ASCII_SPACE_RE.sub("", str(text or ""))


def looks_like_manual_space_split(text: str) -> bool:
    """Whether punctuation-free text looks like manually space-separated bubbles."""
    normalized = str(text or "").strip()
    if not normalized or "\n" in normalized:
        return False
    if any(char in PUNCTUATION_FOR_SPACE_GUARD for char in normalized):
        return False

    glued = glue_cjk_ascii_spaces(normalized)
    parts = [part.strip() for part in re.split(r"\s+", glued) if part.strip()]
    if len(parts) < 3:
        return False

    cjk_chars = re.findall(r"[\u4e00-\u9fff]", glued)
    if len(cjk_chars) < max(6, len(glued.replace(" ", "")) // 3):
        return False
    if any(len(part) > 12 for part in parts):
        return False

    avg_len = sum(len(part) for part in parts) / max(1, len(parts))
    return avg_len <= 8


def merge_space_chunks_to_limit(chunks: list[str], max_chunks: int = 6) -> list[str]:
    """Re-merge space-separated chunks until the bubble count fits."""
    cleaned = [str(chunk or "").strip() for chunk in chunks if str(chunk or "").strip()]
    if len(cleaned) <= max_chunks:
        return cleaned

    result = list(cleaned)
    while len(result) > max_chunks:
        min_len = float("inf")
        merge_index = -1
        for index in range(len(result) - 1):
            combined_len = len(result[index]) + len(result[index + 1])
            if combined_len < min_len:
                min_len = combined_len
                merge_index = index
        if merge_index < 0:
            break
        result[merge_index] = f"{result[merge_index]} {result[merge_index + 1]}".strip()
        result.pop(merge_index + 1)
    return result


__all__ = [
    "HAS_JIEBA",
    "is_continuation_start",
    "merge_chunks_to_limit",
    "merge_continuation_chunks",
    "glue_cjk_ascii_spaces",
    "looks_like_manual_space_split",
    "merge_space_chunks_to_limit",
]
