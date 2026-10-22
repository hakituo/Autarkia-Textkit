"""Forced splitting of long sentences and inline Markdown span repair."""

from __future__ import annotations


def has_unclosed_inline_span(text: str) -> bool:
    """Whether ``**bold**`` / `` `code` `` pairs were split apart.

    Only unescaped ``**`` and backticks count; escaped characters are skipped.
    An odd count means an unclosed pair.
    """
    count = 0
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if text.startswith("**", index):
            count += 1
            index += 2
            continue
        if char == "`":
            count += 1
            index += 1
            continue
        index += 1
    return count % 2 == 1


def repair_broken_inline_spans(chunks: list[str]) -> list[str]:
    """Merge following chunks until every inline span is balanced.

    Joining without a separator is intentional: the splitter removed the
    sentence punctuation at the break, so direct concatenation restores a
    valid ``**...**`` pair.
    """
    if len(chunks) < 2:
        return chunks
    result: list[str] = []
    buffer: str | None = None
    for chunk in chunks:
        candidate = chunk if buffer is None else buffer + chunk
        if has_unclosed_inline_span(candidate):
            buffer = candidate
        else:
            result.append(candidate)
            buffer = None
    if buffer is not None:
        result.append(buffer)
    return result


def force_split_long_sentence(s: str, max_len: int = 100, max_chunks: int = 7) -> list[str]:
    """Split an over-long sentence near punctuation, bounded by ``max_chunks``."""
    if len(s) <= max_len:
        return [s]

    result: list[str] = []
    target_chunk_size = max_len
    position = 0
    while position < len(s):
        remaining_length = len(s) - position
        if remaining_length <= max_len:
            if remaining_length > 0:
                result.append(s[position:].strip())
            break

        target_end = min(position + target_chunk_size, len(s))
        split_char_found = False
        for index in range(target_end - 1, max(position + max_len // 2, position), -1):
            if s[index] in [",", "，", " ", "\u3000", ".", "。", ";", "；", "!", "！", "?", "？"]:
                chunk = s[position : index + 1].strip()
                if chunk:
                    result.append(chunk)
                    position = index + 1
                    split_char_found = True
                    break

        if not split_char_found:
            for index in range(target_end, min(target_end + 20, len(s))):
                if s[index] in [",", "，", " ", "\u3000", ".", "。", ";", "；", "!", "！", "?", "？"]:
                    chunk = s[position : index + 1].strip()
                    if chunk:
                        result.append(chunk)
                        position = index + 1
                        split_char_found = True
                        break

        if not split_char_found:
            chunk = s[position:target_end].strip()
            if chunk:
                result.append(chunk)
                position = target_end

    if len(result) > max_chunks:
        avg_chunk_size = len(s) // max_chunks
        new_result: list[str] = []
        current_chunk = ""
        for chunk in result:
            if len(current_chunk) + len(chunk) <= avg_chunk_size + 20:
                current_chunk += chunk
            else:
                if current_chunk:
                    new_result.append(current_chunk.strip())
                current_chunk = chunk
        if current_chunk:
            new_result.append(current_chunk.strip())

        if len(new_result) <= max_chunks:
            result = new_result
        else:
            result = []
            step = len(s) // max_chunks
            for index in range(0, len(s), step):
                chunk = s[index : index + step].strip()
                if chunk:
                    result.append(chunk)

    return result if result else [s]


__all__ = [
    "has_unclosed_inline_span",
    "repair_broken_inline_spans",
    "force_split_long_sentence",
]
