# Autarkia-Textkit

**Chinese chat text segmentation and set similarity** — turn one model reply into natural chat bubbles, and compare sets with names that state their actual denominator.

Extracted from the [Autarkia](https://qishihao.icu/projects/autarkia) agent runtime, where these rules were tuned against real QQ/Android chat behavior. See the [component roadmap](https://github.com/hakituo/Autarkia-tool/blob/main/ROADMAP.md).

## Why

Splitting a reply into chat bubbles is not `text.split("。")`. The rules here exist because each naive rule failed in production:

- **Sentence punctuation only splits after enough text.** Otherwise "啊。好。" becomes two robotic bubbles.
- **Ellipses are emotion, not punctuation.** `就是……戳废了` stays one bubble; `……哈？！` is never torn apart.
- **Brackets, quotes and math ranges are atomic.** `[1, 3]` does not become `[1` + `3]`.
- **Numbered lists become separate bubbles.** `1. ... 2. ... 3. ...` never breaks mid-item.
- **Emoji after punctuation sticks to the sentence.** `真的吗？😊` stays together.
- **Markdown structure survives.** Fenced code, tables, headings and `$$` lines are kept whole.
- **Model-copied timestamps are stripped.** `[今天 20:00] 早啊` -> `早啊`.
- **Trailing periods/commas are removed, ellipses preserved.**
- **Continuation words are merged back.** "然后..." does not start a lonely bubble.

Set similarity is included because "similarity" was implemented four times with different denominators in the runtime. Here the names are explicit:

| Function | Denominator | Use |
| --- | --- | --- |
| `intersection_over_max` | `max(|A|, |B|)` | tolerant overlap |
| `containment` | `min(|A|, |B|)` | "is the short text covered by the long one" |
| `jaccard` | `|A ∪ B|` | classic Jaccard |

## Install

```bash
pip install autarkia-textkit
```

Optional continuation-word POS detection:

```bash
pip install "autarkia-textkit[segmenter]"
```

Without `jieba`, a compact conjunction-prefix fallback is used.

## Quick start

```python
from autarkia_textkit import split_chat_message, split_for_display

split_chat_message("我觉得你今天真的特别辛苦，早点休息吧。明天还要早起呢。", min_split_len=10)
# ["我觉得你今天真的特别辛苦，早点休息吧", "明天还要早起呢"]

split_for_display("[今天 20:00] 好呀好呀。")
# ["好呀好呀"]

split_for_display("看这个：\n```python\nprint(1)\n```")
# ["看这个：", "```python\nprint(1)\n```"]
```

### Deterministic splitting

```python
import random
split_chat_message(text, comma_split_prob=0.2, rng=random.Random(7))
```

### Similarity

```python
from autarkia_textkit import char_ngrams, containment, intersection_over_max, jaccard

a = char_ngrams("外卖点了吗")
b = char_ngrams("外卖点好没")
containment(a, b)          # short text coverage
intersection_over_max(a, b) # max-denominator overlap
jaccard(a, b)              # union denominator
```

## Concepts

| Piece | Module | What it does |
| --- | --- | --- |
| `split_chat_message` | `autarkia_textkit.segmenter` | bubble splitting with all boundary rules |
| `clean_chat_text` | `autarkia_textkit.clean` | timestamp + trailing punctuation cleanup |
| `split_for_display` | `autarkia_textkit.clean` | clean -> group Markdown blocks -> split |
| `normalize_numbered_list` | `autarkia_textkit.numbered` | inline `1. 2. 3.` -> lines |
| `merge_continuation_chunks` | `autarkia_textkit.merge` | rejoin unnatural breaks |
| `repair_broken_inline_spans` | `autarkia_textkit.force` | rejoin split `**bold**` |
| `intersection_over_max` etc. | `autarkia_textkit.similarity` | set measures |

## Design notes

- **No channel coupling.** `preprocess` and `pass_through_markers` are parameters, so QQ-specific stripping or passthrough codes stay in the adapter.
- **One RNG seam.** `rng=` replaces the module-global `random`, making behavior testable.
- **Zero required dependencies.** `jieba` is an optional extra used only for POS-based continuation detection.

## The bigger picture

- Project page: <https://qishihao.icu/projects/autarkia>
- Runtime repository: <https://github.com/hakituo/Autarkia>
- This package: <https://github.com/hakituo/Autarkia-Textkit>
- Roadmap: <https://github.com/hakituo/Autarkia-tool/blob/main/ROADMAP.md>
- Author: Shihao Qi — <https://qishihao.icu>

## License

MIT
