"""Numbered list detection: split ``1. xxx 2. xxx`` into separate lines."""

from __future__ import annotations

from .rules import (
    _NUMBERED_ITEM_ALLOWED_PREV,
    _NUMBERED_ITEM_RE,
    _NUMBERED_LIST_LEAD_MERGE_ENDINGS,
    _NUMBERED_LIST_LEAD_MERGE_LIMIT,
)


def is_numbered_item_start(s: str, idx: int) -> bool:
    """Whether the number at ``idx`` can start a numbered list item."""
    if idx <= 0:
        return True
    prev = s[idx - 1]
    if prev.isspace():
        return True
    if prev.isdigit() or prev == ".":
        return False
    return prev in _NUMBERED_ITEM_ALLOWED_PREV


def find_numbered_list_starts(s: str) -> list[int]:
    """Offsets of items in the longest strictly increasing numbering run.

    At least two items are required, so decimals, versions and dates are not
    mistaken for lists.
    """
    candidates: list[tuple[int, int]] = []
    for match in _NUMBERED_ITEM_RE.finditer(s):
        start = match.start()
        if not is_numbered_item_start(s, start):
            continue
        look = match.end()
        while look < len(s) and s[look].isspace():
            look += 1
        next_char = s[look] if look < len(s) else ""
        if not (next_char.isalpha() or "\u4e00" <= next_char <= "\u9fff"):
            continue
        candidates.append((start, int(match.group("num"))))

    if len(candidates) < 2:
        return []

    best: list[tuple[int, int]] = []
    index = 0
    while index < len(candidates):
        sequence = [candidates[index]]
        cursor = index + 1
        while cursor < len(candidates) and candidates[cursor][1] > sequence[-1][1]:
            sequence.append(candidates[cursor])
            cursor += 1
        if len(sequence) > len(best):
            best = sequence
        index = cursor

    return [start for start, _ in best] if len(best) >= 2 else []


def normalize_numbered_list(s: str) -> str:
    """Turn an inline numbered list into newline-separated items.

    The downstream newline splitter then treats each item as its own bubble,
    so a bubble cannot end mid-item and resume at ``2.``.
    """
    starts = find_numbered_list_starts(s)
    if not starts:
        return s

    segments: list[str] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(s)
        segments.append(s[start:end])

    lead = s[: starts[0]]
    lead_stripped = lead.strip()
    lead_has_newline = lead.rstrip(" \t").endswith("\n")
    merge_lead = bool(lead_stripped) and not lead_has_newline and (
        len(lead_stripped) <= _NUMBERED_LIST_LEAD_MERGE_LIMIT
        or lead_stripped.endswith(_NUMBERED_LIST_LEAD_MERGE_ENDINGS)
    )

    if lead_stripped:
        if merge_lead:
            gap = " " if lead[-1:].isspace() else ""
            segments[0] = f"{lead_stripped}{gap}{segments[0]}"
        else:
            segments.insert(0, lead_stripped)

    return "\n".join(segment.strip() for segment in segments if segment.strip())


__all__ = ["is_numbered_item_start", "find_numbered_list_starts", "normalize_numbered_list"]
