"""Set similarity measures with unambiguous names.

The runtime had four implementations of "how similar are these two sets"; two
were containment, one used ``max`` as the denominator while being called
"similarity", and one was Jaccard. All four are provided here under names that
state their actual denominator.
"""

from __future__ import annotations

import re
from typing import Iterable, Set

_CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")


def intersection_over_max(a: Iterable, b: Iterable) -> float:
    """``|A∩B| / max(|A|, |B|)``.

    This is **not** Jaccard (whose denominator is the union) and **not**
    containment (which is 1.0 when one set is contained in the other).
    """
    set_a, set_b = set(a), set(b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / float(max(len(set_a), len(set_b), 1))


def containment(a: Iterable, b: Iterable) -> float:
    """``|A∩B| / min(|A|, |B|)`` — how much the shorter set is covered."""
    set_a, set_b = set(a), set(b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / float(min(len(set_a), len(set_b)))


def jaccard(a: Iterable, b: Iterable) -> float:
    """``|A∩B| / |A∪B|``."""
    set_a, set_b = set(a), set(b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / float(len(set_a | set_b))


def char_ngrams(text: str, n: int = 2) -> Set[str]:
    """Character n-grams; text shorter than ``n`` yields the text itself."""
    s = str(text or "")
    if len(s) < n:
        return {s} if s else set()
    return {s[i : i + n] for i in range(len(s) - n + 1)}


def token_ngrams(tokens: Iterable[str], n: int = 2) -> Set[tuple[str, ...]]:
    """Token n-grams (useful for word-level overlap)."""
    seq = [str(token) for token in tokens]
    if len(seq) < n:
        return {tuple(seq)} if seq else set()
    return {tuple(seq[i : i + n]) for i in range(len(seq) - n + 1)}


def cjk_chars(text: str) -> Set[str]:
    """Set of CJK characters in the text."""
    return set(_CJK_PATTERN.findall(str(text or "")))


def cjk_bigrams(text: str) -> Set[str]:
    """CJK-only character bigrams."""
    return char_ngrams("".join(_CJK_PATTERN.findall(str(text or ""))), 2)


__all__ = [
    "intersection_over_max",
    "containment",
    "jaccard",
    "char_ngrams",
    "token_ngrams",
    "cjk_chars",
    "cjk_bigrams",
]
