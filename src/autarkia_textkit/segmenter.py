"""The main bubble splitter.

Rules (long-tuned against real chat behavior):

1. Prefer sentence punctuation (。？！) once the current chunk is long enough.
2. Fall back to commas/semicolons, with a configurable probability.
3. Force-break over-long text near a punctuation mark.
4. Keep bracketed spans, quotes and numbered lists intact.
5. Merge unnatural breaks caused by continuation words or open endings.

``rng`` is injectable so the comma-split probability can be made deterministic
in tests. The default uses the module-level RNG, matching the runtime.
"""

from __future__ import annotations

import random
import re
from typing import Callable, Optional

from .emoji import is_emoji_char
from .force import force_split_long_sentence, repair_broken_inline_spans
from .merge import (
    glue_cjk_ascii_spaces,
    looks_like_manual_space_split,
    merge_chunks_to_limit,
    merge_continuation_chunks,
    merge_space_chunks_to_limit,
)
from .numbered import normalize_numbered_list
from .rules import (
    ELLIPSIS_MERGE_PREFIX_LIMIT,
    EXPLICIT_SPACE_BOUNDARY_ENDINGS,
    HARD_BUBBLE_BOUNDARY_ENDINGS,
)

Preprocess = Callable[[str], str]


def split_chat_message(
    text: str,
    max_len: int = 150,
    comma_split_prob: float = 0.2,
    min_split_len: int = 40,
    preprocess: Optional[Preprocess] = None,
    pass_through_markers: tuple[str, ...] = (),
    rng: Optional[random.Random] = None,
) -> list[str]:
    """Split one chat message into bubbles.

    Args:
        text: Input text.
        max_len: Maximum bubble length.
        comma_split_prob: Probability of splitting at a comma when over the
            soft limit.
        min_split_len: Minimum accumulated length before sentence punctuation
            is allowed to split.
        preprocess: Optional channel-specific preprocessing (e.g. Markdown
            stripping). Runs before splitting.
        pass_through_markers: If any marker is present, return the text whole.
        rng: Optional seeded RNG for the comma-split probability.
    """
    s = str(text or "")
    if not s:
        return []
    for marker in pass_through_markers:
        if marker and marker in s:
            return [s]

    if preprocess is not None:
        s = preprocess(s)
        s = str(s or "")
        if not s:
            return []

    # Normalize explicit newline escapes: /n, \n and double-escaped \\n.
    s = re.sub(r"(?:\\+|[／/])[nN]", "\n", s)

    if looks_like_manual_space_split(s):
        glued = glue_cjk_ascii_spaces(s)
        parts = [part.strip() for part in re.split(r"\s+", glued) if part.strip()]
        return merge_space_chunks_to_limit(parts, max_chunks=6)

    s = re.sub(r"。\.{3,}", "......", s)
    s = re.sub(r"。…+", "……", s)

    for _ in range(3):
        merged = re.sub(
            r"([（(][^）)\n]{1,120})\n([^）)\n]{0,120}[）)])",
            r"\1 \2",
            s,
        )
        if merged == s:
            break
        s = merged

    # Remove newlines inside western and Chinese corner quotes.
    s = re.sub(r"([\u201c\u2018\u300c\u300e])\s*\n", r"\1", s)
    s = re.sub(r"\n\s*([\u201d\u2019\u300d\u300f])", r"\1", s)

    if s.startswith("[") and "]" in s:
        first_close_index = s.find("]")
        if first_close_index == len(s) - 1:
            return [s]
        if len(s) - first_close_index <= 10:
            return [s]

    s = normalize_numbered_list(s)

    max_len = max(20, int(max_len or 150))
    comma_split_prob = max(0.0, min(1.0, float(comma_split_prob)))
    min_split_len = max(10, int(min_split_len or 40))
    if "\n" in s:
        lines = s.split("\n")
        merged_chunks: list[str] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            merged_chunks.extend(
                split_chat_message(
                    line,
                    max_len,
                    comma_split_prob,
                    min_split_len,
                    preprocess=preprocess,
                    pass_through_markers=pass_through_markers,
                    rng=rng,
                )
            )
        # Explicit newlines are user intent: no continuation merge, no cap.
        return merged_chunks

    result: list[str] = []
    current = ""
    i = 0
    stack: list[str] = []
    closing_to_opening = {
        "）": "（",
        ")": "(",
        "]": "[",
        "}": "{",
        "】": "【",
        "\u201d": "\u201c",
        "\u2019": "\u2018",
        '"': '"',
        "'": "'",
    }
    while i < len(s):
        char = s[i]
        prev_char = s[i - 1] if i > 0 else ""
        next_char = s[i + 1] if i + 1 < len(s) else ""
        look_ahead = i + 1
        saw_space_after_punct = False
        while look_ahead < len(s) and s[look_ahead].isspace():
            saw_space_after_punct = True
            look_ahead += 1
        next_visible_char = s[look_ahead] if look_ahead < len(s) else ""
        explicit_space_boundary = saw_space_after_punct and bool(next_visible_char)

        if char == '"':
            if stack and stack[-1] == char:
                stack.pop()
            else:
                stack.append(char)
        elif char == "'":
            is_contraction = (
                i > 0
                and i < len(s) - 1
                and s[i - 1].isalpha()
                and s[i + 1].isalpha()
            )
            if not is_contraction:
                if stack and stack[-1] == char:
                    stack.pop()
                else:
                    stack.append(char)
        elif char in ["（", "(", "[", "{", "【", "\u201c", "\u2018"]:
            stack.append(char)
        elif char in closing_to_opening:
            opening = closing_to_opening[char]
            if stack and stack[-1] == opening:
                stack.pop()

        current += char

        # After a closing parenthesis followed by an ellipsis and then an
        # ordinary sentence, split at the parenthesis.
        if char in ["）", ")"] and not stack:
            look_ahead = i + 1
            while look_ahead < len(s) and s[look_ahead].isspace() and s[look_ahead] != "\n":
                look_ahead += 1
            if look_ahead < len(s) and s[look_ahead] == "…":
                while look_ahead < len(s) and s[look_ahead] == "…":
                    look_ahead += 1
                after_ellipsis = look_ahead
                while (
                    after_ellipsis < len(s)
                    and s[after_ellipsis].isspace()
                    and s[after_ellipsis] != "\n"
                ):
                    after_ellipsis += 1
                next_char = s[after_ellipsis] if after_ellipsis < len(s) else ""
                exclamation_words = ("哈", "啊", "哇", "哎", "唉", "唔", "嗯", "哼", "咦", "嘿", "噢")
                if (
                    next_char
                    and next_char not in HARD_BUBBLE_BOUNDARY_ENDINGS
                    and next_char not in exclamation_words
                    and next_char != "\n"
                ):
                    if current.strip() and len(result) < 2:
                        result.append(current.strip())
                        current = ""

        if char == ".":
            dot_count = 1
            while i + dot_count < len(s) and s[i + dot_count] == ".":
                dot_count += 1
            current += "." * (dot_count - 1)
            if dot_count >= 3:
                look_ahead = i + dot_count
                while look_ahead < len(s) and s[look_ahead].isspace() and s[look_ahead] != "\n":
                    look_ahead += 1
                next_char = s[look_ahead] if look_ahead < len(s) else ""

                exclamation_words_en = (
                    "哈", "啊", "哇", "哎", "唉", "唔", "嗯", "哼", "咦", "嘿", "噢",
                    "ha", "Ha", "HA", "ah", "Ah", "AH", "oh", "Oh", "OH",
                    "wow", "Wow", "WOW",
                )
                is_exclamation_pattern = False
                if next_char and next_char in exclamation_words_en:
                    after_word = look_ahead + 1
                    while after_word < len(s) and s[after_word] not in HARD_BUBBLE_BOUNDARY_ENDINGS:
                        if s[after_word].isspace() and s[after_word] != "\n":
                            after_word += 1
                            continue
                        break
                    if after_word < len(s) and s[after_word] in HARD_BUBBLE_BOUNDARY_ENDINGS:
                        is_exclamation_pattern = True

                should_split = (
                    not stack
                    and len(result) < 2
                    and not is_exclamation_pattern
                    and (
                        next_char == ""
                        or next_char == "\n"
                        or (look_ahead > i + dot_count and s[look_ahead - 1] == " ")
                        or (
                            next_char not in HARD_BUBBLE_BOUNDARY_ENDINGS
                            and next_char not in exclamation_words_en
                        )
                    )
                )
                if should_split:
                    if current.strip():
                        result.append(current.strip())
                    current = ""
            i += dot_count
            continue

        if char == "…":
            ellipsis_count = 1
            while i + ellipsis_count < len(s) and s[i + ellipsis_count] == "…":
                ellipsis_count += 1
            current += "…" * (ellipsis_count - 1)
            look_ahead = i + ellipsis_count
            while look_ahead < len(s) and s[look_ahead].isspace() and s[look_ahead] != "\n":
                look_ahead += 1
            next_char = s[look_ahead] if look_ahead < len(s) else ""

            exclamation_words = ("哈", "啊", "哇", "哎", "唉", "唔", "嗯", "哼", "咦", "嘿", "噢")
            is_exclamation_pattern = False
            if next_char and next_char in exclamation_words:
                after_word = look_ahead + 1
                while after_word < len(s) and s[after_word] not in HARD_BUBBLE_BOUNDARY_ENDINGS:
                    if s[after_word].isspace() and s[after_word] != "\n":
                        after_word += 1
                        continue
                    break
                if after_word < len(s) and s[after_word] in HARD_BUBBLE_BOUNDARY_ENDINGS:
                    is_exclamation_pattern = True

            ellipsis_core = current.rstrip("…").strip()
            is_short_prefix = bool(ellipsis_core) and len(ellipsis_core) <= ELLIPSIS_MERGE_PREFIX_LIMIT
            is_normal_sentence_after = (
                next_char
                and next_char not in HARD_BUBBLE_BOUNDARY_ENDINGS
                and next_char not in exclamation_words
                and next_char != "\n"
            )
            has_explicit_space_after = look_ahead > i + ellipsis_count and s[look_ahead - 1] == " "

            should_split = (
                not stack
                and len(result) < 2
                and not is_exclamation_pattern
                and not (
                    is_short_prefix
                    and is_normal_sentence_after
                    and not has_explicit_space_after
                )
                and (
                    next_char == ""
                    or next_char == "\n"
                    or has_explicit_space_after
                    or (
                        next_char not in HARD_BUBBLE_BOUNDARY_ENDINGS
                        and next_char not in exclamation_words
                    )
                )
            )
            if should_split:
                if current.strip():
                    result.append(current.strip())
                current = ""
            i += ellipsis_count
            continue

        if (not stack) and char in ["。", "!", "！", "?", "？", ",", "，", ".", ";", "；"]:
            if char == "." and prev_char.isdigit() and next_char.isdigit():
                i += 1
                continue
            if char == ".":
                numbered_prefix = current.strip()
                look_ahead = i + 1
                while look_ahead < len(s) and s[look_ahead].isspace():
                    look_ahead += 1
                if re.fullmatch(r"\d{1,3}\.", numbered_prefix):
                    if look_ahead < len(s) and (
                        s[look_ahead].isalpha() or "\u4e00" <= s[look_ahead] <= "\u9fff"
                    ):
                        i += 1
                        continue
            if char in ["?", "？", "!", "！"]:
                repeat_count = 1
                while i + repeat_count < len(s) and s[i + repeat_count] == char:
                    repeat_count += 1
                if repeat_count > 1:
                    current += char * (repeat_count - 1)
                    i += repeat_count - 1

            # Glue an emoji directly after terminal punctuation to the current
            # sentence instead of letting it start the next bubble.
            if char in ["?", "？", "!", "！", "。", "."]:
                emoji_look = i + 1
                if emoji_look < len(s) and is_emoji_char(s[emoji_look]):
                    while emoji_look < len(s) and is_emoji_char(s[emoji_look]):
                        current += s[emoji_look]
                        emoji_look += 1
                    i = emoji_look - 1
                    if emoji_look < len(s) and s[emoji_look] == "\n":
                        if current.strip():
                            result.append(current.strip())
                        current = ""
                    elif emoji_look < len(s) and s[emoji_look].isspace():
                        if current.strip() and len(result) < 2:
                            result.append(current.strip())
                            current = ""
                    i += 1
                    continue

            if char in [",", "，", ";", "；"]:
                first_chunk_prefix = current[:-1].strip()
                if len(result) == 0 and first_chunk_prefix in {
                    "等等", "等下", "等一下", "稍等", "先等等", "先等下",
                }:
                    i += 1
                    continue
            current_len = len(current.strip())

            exclamation_words_punct = ("哈", "啊", "哇", "哎", "唉", "唔", "嗯", "哼", "咦", "嘿", "噢")
            is_ellipsis_exclamation = False
            stripped_current = current.strip()
            if stripped_current.startswith("……") or stripped_current.startswith("..."):
                after_ellipsis = stripped_current.lstrip("……").lstrip("...")
                if after_ellipsis and after_ellipsis[0] in exclamation_words_punct:
                    is_ellipsis_exclamation = True
            if is_ellipsis_exclamation and char in ["?", "？", "!", "！"]:
                look_ahead_punct = i + 1
                while look_ahead_punct < len(s) and s[look_ahead_punct].isspace():
                    look_ahead_punct += 1
                if (
                    look_ahead_punct < len(s)
                    and s[look_ahead_punct] in HARD_BUBBLE_BOUNDARY_ENDINGS
                ):
                    i += 1
                    continue
                if current_len < 10 and len(result) >= 2:
                    i += 1
                    continue

            if char in [",", "，", ";", "；"]:
                if not explicit_space_boundary:
                    if current_len < max_len:
                        i += 1
                        continue
                    if (rng or random).random() > comma_split_prob:
                        i += 1
                        continue
            else:
                very_short_threshold = 10
                is_very_short = current_len < very_short_threshold
                is_long_enough = current_len >= min_split_len
                if not explicit_space_boundary and not is_very_short and not is_long_enough:
                    i += 1
                    continue
                if len(result) >= 2:
                    i += 1
                    continue

            if current.strip():
                if explicit_space_boundary and any(
                    current.strip().endswith(ending)
                    for ending in EXPLICIT_SPACE_BOUNDARY_ENDINGS
                ):
                    result.append(current.strip())
                elif char in [",", "，", "。", ";", "；"]:
                    result.append(current[:-1].strip())
                else:
                    result.append(current.strip())
            current = ""
        i += 1

    if current.strip():
        result.append(current.strip())

    if len(result) > 1:
        result = merge_continuation_chunks(
            result, max_merge_len=max_len * 2, min_split_len=min_split_len
        )
        if len(result) > 6:
            result = merge_chunks_to_limit(result, max_chunks=6)
        return repair_broken_inline_spans(result)

    if len(s) > max_len * 2:
        forced = force_split_long_sentence(s, max_len=max_len, max_chunks=6)
        if len(forced) > 1:
            return repair_broken_inline_spans(forced)

    return [s]


__all__ = ["split_chat_message"]
