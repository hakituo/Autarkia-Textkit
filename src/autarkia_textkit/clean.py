"""Cleaning and display grouping: timestamps, trailing punctuation, blocks."""

from __future__ import annotations

import re

from .rules import (
    AI_TIMESTAMP_PATTERN,
    TRAILING_PUNCT_CHARS,
    _LATEX_MARKER_RE,
    _MARKDOWN_BLOCK_START_RE,
    _MARKDOWN_TABLE_LINE_RE,
)
from .segmenter import split_chat_message

_ELLIPSIS_ONLY_RE = re.compile(r"^[\s.…]+$")


def is_ellipsis_only(text: str) -> bool:
    """Whether the whole text consists only of ellipses and whitespace."""
    stripped = str(text or "").strip()
    if not stripped or not _ELLIPSIS_ONLY_RE.match(stripped):
        return False
    return "…" in stripped or stripped.count(".") >= 3


def strip_ai_timestamp(text: str) -> str:
    """Remove model-emitted history timestamps anywhere in the text."""
    return AI_TIMESTAMP_PATTERN.sub("", str(text or "")).strip()


def strip_trailing_punctuation(text: str) -> str:
    """Remove trailing punctuation without touching ellipses."""
    text = str(text or "")
    if is_ellipsis_only(text):
        return text.strip()
    text = re.sub(r"[。.]\s*(?=[（(])", "", text)
    text = re.sub(r"[。.]+\s*([）)])", r"\1", text)
    text = text.rstrip(TRAILING_PUNCT_CHARS).strip()
    text = re.sub(r"[。.]+$", "", text)
    return text.strip()


def clean_chat_text(text: str) -> str:
    """Timestamp removal + trailing punctuation removal."""
    return strip_trailing_punctuation(strip_ai_timestamp(text))


def _group_display_lines(text: str) -> list[tuple[str, bool]]:
    """Split into ``(text, atomic)`` groups by Markdown block structure.

    Fenced code, ``$$`` blocks and table runs stay whole; single-line block
    markers (heading/list/quote) stay on their line. Ordinary lines still go
    through :func:`split_chat_message`.
    """
    lines = text.split("\n")
    groups: list[tuple[str, bool]] = []
    index = 0
    total = len(lines)

    while index < total:
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue

        fence = None
        if stripped.startswith("```"):
            fence = "```"
        elif stripped.startswith("~~~"):
            fence = "~~~"
        if fence is not None:
            buffer: list[str] = []
            cursor = index
            while cursor < total:
                buffer.append(lines[cursor])
                cursor += 1
                if cursor > index + 1 and lines[cursor - 1].strip().startswith(fence):
                    break
            groups.append(("\n".join(buffer), True))
            index = cursor
            continue

        if stripped == "$$":
            buffer = []
            cursor = index
            while cursor < total:
                buffer.append(lines[cursor])
                cursor += 1
                if cursor > index + 1 and lines[cursor - 1].strip() == "$$":
                    break
            groups.append(("\n".join(buffer), True))
            index = cursor
            continue

        if _MARKDOWN_TABLE_LINE_RE.match(line):
            buffer = []
            cursor = index
            while cursor < total and _MARKDOWN_TABLE_LINE_RE.match(lines[cursor]):
                buffer.append(lines[cursor].strip())
                cursor += 1
            groups.append(("\n".join(buffer), True))
            index = cursor
            continue

        atomic = bool(
            _MARKDOWN_BLOCK_START_RE.search(stripped) or _LATEX_MARKER_RE.search(stripped)
        )
        groups.append((stripped, atomic))
        index += 1

    return groups


def split_for_display(
    text: str,
    max_len: int = 150,
    comma_split_prob: float = 0.2,
    min_split_len: int = 40,
    rng=None,
) -> list[str]:
    """Clean, group by structure, split each group, clean each bubble again."""
    cleaned = clean_chat_text(text)
    if not cleaned:
        return []
    result: list[str] = []
    for group_text, atomic in _group_display_lines(cleaned):
        if atomic:
            if group_text.strip():
                result.append(group_text)
            continue
        for chunk in split_chat_message(
            group_text,
            max_len,
            comma_split_prob,
            min_split_len,
            rng=rng,
        ):
            chunk = strip_trailing_punctuation(chunk)
            if chunk:
                result.append(chunk)
    return result


__all__ = [
    "is_ellipsis_only",
    "strip_ai_timestamp",
    "strip_trailing_punctuation",
    "clean_chat_text",
    "split_for_display",
]
