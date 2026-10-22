<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/hakituo/Autarkia-Textkit/main/autarkia-dark.svg">
    <img src="https://raw.githubusercontent.com/hakituo/Autarkia-Textkit/main/autarkia.svg" alt="Autarkia" width="300">
  </picture>
</p>

<p align="center">
  <b>Autarkia-Textkit</b><br>
  <sub>中文聊天消息切分 + 集合相似度 · Chinese chat bubble segmentation &amp; set similarity</sub>
</p>

<p align="center">
  <a href="https://pypi.org/project/Autarkia-Textkit/"><img alt="PyPI" src="https://img.shields.io/pypi/v/autarkia-textkit.svg"></a>
  <a href="https://pypi.org/project/Autarkia-Textkit/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/autarkia-textkit.svg"></a>
  <a href="https://github.com/hakituo/Autarkia-Textkit/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/hakituo/Autarkia-Textkit/actions/workflows/ci.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
</p>

<p align="center">
  <a href="#中文">简体中文</a> · <a href="#english">English</a>
</p>

---

## 中文

把模型**一段回复**切成**几条像人打出来的消息**，外加几个分母说得清的集合相似度函数。

来自长期在线的 [Autarkia](https://qishihao.icu/projects/autarkia) agent 运行时——那里的切分规则是对着真实 QQ / Android 聊天行为一条条调出来的。整个系列见[组件库路线图](https://github.com/hakituo/Autarkia-tool/blob/main/ROADMAP.md)。

### 为什么：切气泡不是 `text.split("。")`

下面每条规则都对应一次线上翻车：

- **标点要攒够字数才切**，否则「啊。好。」会变成两条机器人气泡。
- **省略号是情绪，不是句号**：`就是……戳废了` 保持一条，`……哈？！` 不会被撕开。
- **括号、引号、数学区间是原子**：`[1, 3]` 不会变成 `[1` + `3]`。
- **编号列表各自成条**，`1. … 2. … 3. …` 不会从条目中间断开。
- **标点后的 emoji 跟着句子走**：`真的吗？😊` 不拆。
- **Markdown 结构整体保留**：代码块、表格、标题、`$$` 行都不切。
- **模型抄进来的时间戳会清掉**：`[今天 20:00] 早啊` → `早啊`。
- **句尾的句号/逗号去掉，省略号保留**。
- **承接词合并回去**：以「然后…」开头的碎片不会单独成条。

相似度一起发，是因为运行时里「相似度」被不同分母实现了四遍。这里把分母写进函数名：

| 函数 | 分母 | 用途 |
| --- | --- | --- |
| `intersection_over_max` | `max(|A|, |B|)` | 宽容的重叠度 |
| `containment` | `min(|A|, |B|)` | 「短文本是否被长文本覆盖」 |
| `jaccard` | `|A ∪ B|` | 经典 Jaccard |

### 安装

```bash
pip install autarkia-textkit
```

可选的承接词词性判断：

```bash
pip install "autarkia-textkit[segmenter]"
```

没装 `jieba` 时自动退回一套紧凑的连词前缀兜底逻辑。

### 快速开始

```python
from autarkia_textkit import split_chat_message, split_for_display

split_chat_message("我觉得你今天真的特别辛苦，早点休息吧。明天还要早起呢。", min_split_len=10)
# ["我觉得你今天真的特别辛苦，早点休息吧", "明天还要早起呢"]

split_for_display("[今天 20:00] 好呀好呀。")
# ["好呀好呀"]

split_for_display("看这个：\n```python\nprint(1)\n```")
# ["看这个：", "```python\nprint(1)\n```"]
```

确定性切分（把随机源交出去）：

```python
import random
split_chat_message(text, comma_split_prob=0.2, rng=random.Random(7))
```

相似度：

```python
from autarkia_textkit import char_ngrams, containment, intersection_over_max, jaccard

a = char_ngrams("外卖点了吗")
b = char_ngrams("外卖点好没")
containment(a, b)           # 短文本覆盖度
intersection_over_max(a, b) # max 分母的重叠
jaccard(a, b)               # 并集分母
```

### 模块分工

| 组件 | 模块 | 做什么 |
| --- | --- | --- |
| `split_chat_message` | `autarkia_textkit.segmenter` | 全部边界规则下的气泡切分 |
| `clean_chat_text` | `autarkia_textkit.clean` | 时间戳与句尾标点清理 |
| `split_for_display` | `autarkia_textkit.clean` | 清理 → 归并 Markdown 块 → 切分 |
| `normalize_numbered_list` | `autarkia_textkit.numbered` | 行内 `1. 2. 3.` 摊成多行 |
| `merge_continuation_chunks` | `autarkia_textkit.merge` | 合并不自然的断点 |
| `repair_broken_inline_spans` | `autarkia_textkit.force` | 修复被切开的 `**粗体**` |
| `intersection_over_max` 等 | `autarkia_textkit.similarity` | 集合度量 |

### 设计说明

- **不绑渠道**：`preprocess` 与 `pass_through_markers` 都是参数，QQ 专有的清洗/透传标记留在适配层。
- **只有一个随机缝**：`rng=` 取代模块级 `random`，行为可测。
- **必需依赖为零**：`jieba` 只是可选 extra，且仅用于词性判断的承接词检测。

### 系列与链接

- 项目页：<https://qishihao.icu/projects/autarkia>
- 运行时仓库：<https://github.com/hakituo/Autarkia>
- 本包：<https://github.com/hakituo/Autarkia-Textkit>
- 组件库路线图：<https://github.com/hakituo/Autarkia-tool/blob/main/ROADMAP.md>
- 作者：Shihao Qi — <https://qishihao.icu>

### 许可

MIT

---

## English

Turn **one model reply** into **several messages that read like a human typed them** — plus set-similarity functions whose names state their actual denominator.

Extracted from the [Autarkia](https://qishihao.icu/projects/autarkia) agent runtime, where these rules were tuned against real QQ/Android chat behavior. See the [component roadmap](https://github.com/hakituo/Autarkia-tool/blob/main/ROADMAP.md).

### Why

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

### Install

```bash
pip install autarkia-textkit
```

Optional continuation-word POS detection:

```bash
pip install "autarkia-textkit[segmenter]"
```

Without `jieba`, a compact conjunction-prefix fallback is used.

### Quick start

```python
from autarkia_textkit import split_chat_message, split_for_display

split_chat_message("我觉得你今天真的特别辛苦，早点休息吧。明天还要早起呢。", min_split_len=10)
# ["我觉得你今天真的特别辛苦，早点休息吧", "明天还要早起呢"]

split_for_display("[今天 20:00] 好呀好呀。")
# ["好呀好呀"]

split_for_display("看这个：\n```python\nprint(1)\n```")
# ["看这个：", "```python\nprint(1)\n```"]
```

Deterministic splitting:

```python
import random
split_chat_message(text, comma_split_prob=0.2, rng=random.Random(7))
```

Similarity:

```python
from autarkia_textkit import char_ngrams, containment, intersection_over_max, jaccard

a = char_ngrams("外卖点了吗")
b = char_ngrams("外卖点好没")
containment(a, b)           # short text coverage
intersection_over_max(a, b) # max-denominator overlap
jaccard(a, b)               # union denominator
```

### Concepts

| Piece | Module | What it does |
| --- | --- | --- |
| `split_chat_message` | `autarkia_textkit.segmenter` | bubble splitting with all boundary rules |
| `clean_chat_text` | `autarkia_textkit.clean` | timestamp + trailing punctuation cleanup |
| `split_for_display` | `autarkia_textkit.clean` | clean -> group Markdown blocks -> split |
| `normalize_numbered_list` | `autarkia_textkit.numbered` | inline `1. 2. 3.` -> lines |
| `merge_continuation_chunks` | `autarkia_textkit.merge` | rejoin unnatural breaks |
| `repair_broken_inline_spans` | `autarkia_textkit.force` | rejoin split `**bold**` |
| `intersection_over_max` etc. | `autarkia_textkit.similarity` | set measures |

### Design notes

- **No channel coupling.** `preprocess` and `pass_through_markers` are parameters, so QQ-specific stripping or passthrough codes stay in the adapter.
- **One RNG seam.** `rng=` replaces the module-global `random`, making behavior testable.
- **Zero required dependencies.** `jieba` is an optional extra used only for POS-based continuation detection.

### The bigger picture

- Project page: <https://qishihao.icu/projects/autarkia>
- Runtime repository: <https://github.com/hakituo/Autarkia>
- This package: <https://github.com/hakituo/Autarkia-Textkit>
- Roadmap: <https://github.com/hakituo/Autarkia-tool/blob/main/ROADMAP.md>
- Author: Shihao Qi — <https://qishihao.icu>

### License

MIT
