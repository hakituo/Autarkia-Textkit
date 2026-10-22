# AGENTS.md — Autarkia-Textkit（Autarkia 组件库系列）

给改动本仓库的 agent 看的说明书。读完应该能回答：这是什么、语义以谁为准、怎么验证、怎么发布。

## 这是什么

Autarkia 运行时组件库系列的第 4 个库：中文聊天消息切分（清洗、断句、编号列表、emoji 粘连、Markdown 结构保留、续接合并、强制长句分割）+ 集合相似度度量（IoMax / containment / Jaccard / ngram）。

- PyPI：<https://pypi.org/project/Autarkia-Textkit/>
- 系列路线图：<https://github.com/hakituo/Autarkia-tool/blob/main/ROADMAP.md>（**先读它**）
- 主运行时（语义权威源）：本地 `D:\AI\xiaoyou-public`，GitHub <https://github.com/hakituo/Autarkia>
- 作者站点：<https://qishihao.icu/projects/autarkia>

## 了解背景：先看主仓库的哪些文件

| 本库模块 | 主仓库源头（D:\AI\xiaoyou-public\） |
| --- | --- |
| `src/autarkia_textkit/rules.py` | `core\utils\text_segmenter_rules.py` |
| `src/autarkia_textkit/emoji.py` | `core\utils\text_segmenter_emoji.py` |
| `src/autarkia_textkit/clean.py` | `core\utils\text_segmenter_clean.py` |
| `src/autarkia_textkit/numbered.py` | `core\utils\text_segmenter_numbered.py` |
| `src/autarkia_textkit/merge.py` | `core\utils\text_segmenter_merge.py` |
| `src/autarkia_textkit/force.py` | `core\utils\text_segmenter_force.py` |
| `src/autarkia_textkit/segmenter.py` | `core\utils\text_segmenter_core.py` |
| `src/autarkia_textkit/similarity.py` | `core\utils\text_similarity.py` |
| `src/autarkia_textkit/__init__.py` | `core\utils\text_segmenter.py`（门面导出） |

宿主测试母本：`D:\AI\xiaoyou-public\tests\unit\test_text_segmenter*.py`、`test_text_similarity*.py`（按名检索）。

抽取时做过的通用化改造（不要再改回去）：
- 渠道预处理 / 透传标记 → `preprocess` 与 `pass_through_markers` 参数。
- 模块级 `random.random()` → 可注入 `rng`（默认仍用模块级 RNG，分布不变）。
- `jieba` 词性判断 → 可选依赖；未安装时使用紧凑连词前缀表兜底（`HAS_JIEBA` 标志）。
- 宿主 parity 脚本常量扫描 / Kotlin 对齐 → 删除（属宿主 CI）。
- 宿主 logger → 无日志依赖。

## 本仓库结构

```text
AGENTS.md                 本文件
src/autarkia_textkit/     包本体（import 名 autarkia_textkit）
tests/                    行为测试（纯函数，不跑网络）
pyproject.toml            hatchling；零必需依赖；可选 extra: jieba
```

## 硬规则

1. **零必需运行时依赖**。`jieba` 只能作为 optional extra，且必须有兜底路径。
2. **宿主 import 一个不许进 src/**：`config.*`、`core.*`、`clients.*` 一律禁止。
3. 断句常量（尾随标点、硬边界、省略号阈值、编号正则）改动属于行为变更，必须同步改测试。
4. 行为变更先改/加测试，全绿再提交。
5. **每次 `twine upload` 前必须递增 `pyproject.toml` 的 version**。
6. PyPI token 不进 git；只存在于 `%USERPROFILE%\.pypirc`。

## 命令（本机环境）

venv 与主库共用：`D:\AI\autarkia\.venv\`（Python 3.10）。

| 用途 | 命令 |
| --- | --- |
| 测试 | `$env:PYTHONPATH="src"; D:\AI\autarkia\.venv\Scripts\python -m pytest -q` |
| 测试（含 jieba 路径） | 先 `pip install jieba`，再跑同一命令 |
| 构建 | `D:\AI\autarkia\.venv\Scripts\python -m build --no-isolation` |
| 发布检查 | `D:\AI\autarkia\.venv\Scripts\python -m twine check dist\*` |
| 发布 | `$env:HTTP_PROXY="http://127.0.0.1:7897"; $env:HTTPS_PROXY=$env:HTTP_PROXY; D:\AI\autarkia\.venv\Scripts\python -m twine upload dist\* --non-interactive` |

**本机 pip 坑**：不加 `-i https://pypi.org/simple --proxy http://127.0.0.1:7897` 会报 `from versions: none`。**twine 坑**：不认 `--proxy`，走环境变量。

## 提交

- commit message 中文一句话；Windows 下写进临时文件用 `git commit -F` 防乱码。
- 改完自己提交并推送 `origin main`，不要停在"改好了"等确认。
- 推送前 `git status --porcelain` 确认只含本次任务涉及的文件。
