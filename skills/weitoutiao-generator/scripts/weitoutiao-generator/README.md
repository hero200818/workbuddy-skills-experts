# 微头条爆款批量生成器

> 面向今日头条·微头条场景的自动化内容生产工具：选题挖掘 → 标题/正文生成 → 排版优化 → 敏感词与平台规则校验 → 爆款潜力评分 → 批量导出。

纯 Python、零外部依赖（仅需 `pyyaml`），可一键批量产出符合头条号受众偏好与推荐机制的微头条草稿。

## 特性

- **选题挖掘**：内置 10 大类目、30+ 选题种子，按权重随机抽样并去重，支持指定类目。
- **爆款公式**：10 套经过验证的标题公式（悬念/数字/反常识/共鸣/对比/故事/清单/警示…），每选题生成多个标题候选。
- **正文引擎**：钩子（3 秒抓人）→ 要点展开 → 金句 → 互动引导，按类目匹配 emoji，自动插入话题标签与配图建议。
- **合规校验**：广告法极限词自动改写、站外引流/违法/虚假宣传词拦截、标题与篇幅规则检查；严重违规自动剔除。
- **爆款评分**：从标题力 / 情绪 / 价值 / 互动 / 篇幅 / 排版 6 维度给出 0-100 分与「潜力标签」。
- **批量导出**：JSON（结构化，含评分与校验记录）、CSV（排程工具友好）、Markdown（可读）、TXT（发布草稿）。
- **可插拔 LLM**：配置 `llm.enabled=true` 后调用 OpenAI 兼容接口增强正文，失败自动回退模板引擎。

## 快速开始

```bash
# 1. 安装依赖（仅 pyyaml，已用隔离 venv）
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt

# 2. 按默认配置批量生成 12 条
python main.py

# 3. 指定类目 / 数量 / 格式
python main.py --count 20 --category 职场 --formats json,csv,md

# 4. 启用大模型后端（需先在 config.yaml 填 api_key 或设置环境变量 OPENAI_API_KEY）
python main.py --llm

# 5. 仅生成不校验
python main.py --no-validate
```

> 运行环境建议使用仓库内置的受管 Python：
> `C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe main.py`

## 目录结构

```
weitoutiao-generator/
├── config.yaml          # 主配置（类目权重、篇幅、平台规则、LLM、导出）
├── requirements.txt
├── main.py              # CLI 主控，编排全流程
├── src/
│   ├── data_loader.py   # 配置/选题/模板/敏感词加载
│   ├── topics.py        # 选题挖掘（权重抽样+去重+角度组合）
│   ├── generator.py     # 标题候选 + 正文组合引擎
│   ├── formatter.py     # 排版优化与发布文本组装
│   ├── validator.py     # 敏感词拦截 + 平台规则校验 + 极限词改写
│   ├── scorer.py        # 爆款潜力评分
│   ├── exporter.py      # JSON/CSV/MD/TXT 批量导出
│   └── llm_backend.py   # 可选大模型后端（OpenAI 兼容）
├── data/
│   ├── topics_seed.json # 选题种子库（可自由扩充）
│   ├── templates.json   # 标题公式/通用钩子/CTA/emoji/配图池
│   └── sensitive_words.txt  # 合规敏感词库（SEVERE/WARN）
└── output/              # 导出结果（自动生成）
```

## 关键设计说明

### 契合头条推荐机制
- **冷启动友好**：标题短（≤28 字）、正文 100-300 字利于完读率；结尾强互动引导（评论/点赞/关注）拉升互动率，这是头条分发的关键信号。
- **话题标签**：输出 `#话题#` 双井号格式，利于进入对应推荐池。
- **配图建议**：默认 3-6 张图，图文内容在微头条流中点击率更高。
- **发布时段**：`config.yaml` 内置黄金发布时段（早 7-9、午 12-13、晚 18-22）。

### 合规优先
- 广告法极限词（极致/顶级/100%/包治/根治…）自动改写为克制表达；
- 站外引流（加微信/公众号/二维码/扫码…）与违法内容（赌博/毒品/诈骗…）命中即拦截；
- 严格模式下命中严重违规直接剔除，保证产出可发布。

### 扩展方式
- **加选题**：在 `data/topics_seed.json` 追加条目（id/category/title_hint/keywords/emotion/body_type/hook/points/punchline/hashtags）。
- **加标题公式**：在 `data/templates.json` 的 `title_formulas` 增加模板，用 `{topic}` 占位。
- **换大模型**：配置 `llm.provider/base_url/api_key/model` 即可接入任意 OpenAI 兼容服务。

## 注意事项
- 本工具生成的是「草稿」，发布前建议人工终审一遍语气与事实准确性。
- 健康/理财类内容已做「个人体验，因人而异」等软性免责表述，避免虚假承诺。
- 评分与校验是「概率性」辅助，不代表平台实际推荐结果。
