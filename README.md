# WorkBuddy 自建 Skill 与专家团合集

爷爷（读读书悦悦己）在 WorkBuddy 中自制的 Skill 和专家团存档，可直接复制到 `~/.workbuddy/skills/` 或通过 WorkBuddy 专家中心导入使用。

## 📦 skills/ — 17 个自建 Skill

| Skill | 用途 |
|---|---|
| toutiao-bestseller-generator | 微头条爆款批量生成器（核心流水线） |
| weitoutiao-generator | 微头条生成 |
| microblast | 爆款微头条内容引擎 |
| baokuan-note-factory | 爆款笔记工厂 |
| baowen-workshop | 报文/金句工坊 |
| burstarticle-engine | 爆文引擎 |
| gzh-pipeline | 公众号 md→图流水线（md2jpg） |
| gzh-assets | 公众号素材管理 |
| gzh-deliver | 公众号交付 |
| gzh-ima | 公众号 × IMA 知识库 |
| gzh-ledger | 公众号台账 |
| gzh-lint | 公众号文章质检 |
| gzh-score | 公众号文章评分 |
| wechat-book-cards | 微信读书卡片 |
| moyun-book-cards | 墨韵书卡 |
| md2card-pro | Markdown→知识卡片（需自装 wkhtmltoimage） |
| md2card-notebook-style | 笔记本风格知识卡片 |

> **md2card-pro 注意**：原目录捆绑的 `bin/wkhtmltoimage`（46MB）未收录，请从 [wkhtmltopdf 官网](https://wkhtmltopdf.org/downloads.html) 自行安装并放入 `bin/` 或加入 PATH。

## 👥 experts/ — 3 个自建专家团

| 专家团 | 版本 | 说明 |
|---|---|---|
| content-matrix-studio | 1.3.0 | 内容矩阵工作室 |
| moyun-book-ops | 1.8.0 | 墨韵图书运营 |
| wechat-viral-team | 1.0.1 | 公众号爆款团队 |

## 安装方式

- **Skill**：把 `skills/<名称>/` 整个目录复制到 `~/.workbuddy/skills/`，重启 WorkBuddy 技能面板即可识别（只需 SKILL.md 即可生效）。
- **专家团**：目录为 WorkBuddy 专家包格式（README + agents + skills），按版本号目录取最新版导入专家中心。

---
*由 WorkBuddy（小胖子）整理导出 · 2026-11-03*
