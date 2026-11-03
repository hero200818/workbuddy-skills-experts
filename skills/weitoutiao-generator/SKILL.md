---
name: weitoutiao-generator
description: 批量生成符合今日头条（头条号）微头条规范、具备爆款潜质的微头条内容，覆盖选题挖掘、标题/正文生成、排版优化、敏感词与平台规则校验、爆款潜力评分、批量导出。当用户需要生成头条号微头条、批量产出爆款文案、头条内容运营素材、微头条标题与正文、或按头条推荐机制做内容分发时使用。
agent_created: true
---

# 微头条爆款批量生成器（Weitoutiao Generator）

## Overview

本技能提供一个自包含的 Python 工具链，从「选题 → 标题/正文生成 → 排版 → 合规校验 → 爆款评分 → 批量导出」全流程自动生成可直接发布的微头条内容。工具链内置在 `scripts/weitoutiao-generator/`，无需联网即可产出模板化内容；接入大模型后质量可进一步提升。

核心目标：让产出契合今日头条微头条受众偏好与推荐机制（点击率、完读率、互动率是分发核心信号）。

## When to Use

- 用户要求「生成头条微头条 / 批量微头条 / 头条号爆款文案」。
- 用户需要头条号日常内容运营素材、多选题批量产出。
- 用户希望内容符合头条平台规范（字数、话题标签、合规）并具备爆款潜力。
- 用户希望对已有选题做标题与正文扩写、排版与校验。

## Quick Start

工具链位于 `scripts/weitoutiao-generator/`。运行前确保依赖就绪（仅需 `pyyaml`）：

```bash
# 在隔离 venv 中安装依赖（推荐，避免污染用户环境）
VENV="C:/Users/Administrator/.workbuddy/binaries/python/envs/default"
PY="$VENV/Scripts/python.exe"
"$PY" -m pip install pyyaml   # 若尚未安装

# 进入技能脚本目录并生成（默认 12 条，导出 json/csv/md/txt）
cd "<skill_dir>/scripts/weitoutiao-generator"
"$PY" main.py --count 12
```

`<skill_dir>` 为技能安装目录：`~/.workbuddy/skills/weitoutiao-generator/`（用户级）。

## 命令行参数

| 参数 | 说明 | 默认 |
|------|------|------|
| `--count N` | 生成条数 | 12 |
| `--category 类目` | 限定单个类目（科技/情感/职场/美食/健康/教育/财经/社会/娱乐/生活） | 全部 |
| `--formats csv excel md json` | 导出格式组合（可多个） | json csv md txt |
| `--output-dir 路径` | 输出目录 | `output/` |
| `--llm` | 启用大模型后端（需先配置 `config.yaml` 的 `llm.api_key`） | 关闭（用模板） |
| `--no-validate` | 跳过合规校验 | 开启校验 |
| `--seed N` | 随机种子，保证可复现 | 随机 |

示例：
```bash
"$PY" main.py --category 科技 --count 5 --output-dir ./run_tech
"$PY" main.py --llm --count 20 --formats json md
```

## 工具链结构（scripts/weitoutiao-generator/）

- `main.py` — CLI 主控，编排全流程。
- `src/topics.py` — 选题挖掘：10 大类目权重抽样、去重、热点角度组合。
- `src/generator.py` — 生成引擎：10 套爆款标题公式（每选题 3 候选）+ 钩子→展开→金句→互动正文，按类目匹配 emoji。
- `src/validator.py` — 合规校验：广告法极限词安全改写（`极致→很` 等）、站外引流/违法/虚假宣传拦截、标题与篇幅规则检查。
- `src/scorer.py` — 爆款潜力评分：标题力/情绪/价值/互动/篇幅/排版 6 维 0-100 分 + 潜力标签。
- `src/formatter.py` — 排版优化与发布文本组装。
- `src/exporter.py` — 批量导出 JSON / CSV / Markdown / TXT。
- `src/llm_backend.py` — 可插拔大模型后端（OpenAI 兼容，失败自动回退模板）。
- `data/topics_seed.json` — 选题种子库（可按账号复盘数据替换）。
- `data/templates.json` — 标题公式与正文结构模板库。
- `data/sensitive_words.txt` — 合规敏感词库（||LEVEL 格式）。
- `config.yaml` — 类目权重、篇幅、平台规则、LLM、导出等全部可调。
- `output/` — 内置样例产出（4 种格式），供参考。

## 配置要点（config.yaml）

- `category_weights`：各类目抽样权重，按需提高目标受众相关类目。
- `rules.title`、`rules.body`：标题≤28 字、正文 100-300 字（最优 280）等平台友好篇幅。
- `rules.topics_tag`：自动注入 `#话题#` 双井号标签数量（默认 2-3）。
- `llm`：填 `api_key` 并加 `--llm` 启用；不填则纯模板生成，零成本。

## 头条爆款与推荐机制要点（领域知识）

- **标题**：≤28 字利于前端展示与点击；用「数字、冲突、悬念、反差、身份代入」等钩子公式。
- **正文**：100-300 字最佳，短段落 + 空行提升可读性完读率；结尾强互动（提问/投票/关注引导）拉升互动率——这是头条分发核心信号。
- **话题标签**：`#话题#` 进入推荐池，默认 2-3 个，不要堆砌。
- **配图**：建议 3-6 张，提升点击与停留。
- **发布时段**：config 内置黄金时段建议（早 7-9、午 12-14、晚 18-22）。

## 合规要点

- 严重违规（站外引流、违法、虚假宣传、未证实医疗断言）直接拦截剔除。
- 极限词（`极致/顶级/国家级/绝无仅有` 等）自动改写为安全表达，避免被判定违规限流。
- 校验结果为 WARN 的内容仍可发布，但应在对外前人工复核。

## Operational Notes

- 纯模板模式零成本、可离线；大模型模式需自备 API key。
- 产出文件默认落在 `output/`，同名会覆盖，建议用 `--output-dir` 区分批次。
- 扩展内容：直接编辑 `data/topics_seed.json`（替换为真实爆款复盘选题）与 `data/templates.json`（补充标题钩子）。
