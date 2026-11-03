---
name: gzh-ledger
display_name: 发布台账与复盘
display_name_en: Publish Ledger & Retro
description: "公众号发布台账管理（list/add/check/audit 逾期催办）与群发后数据复盘（评论率/在看率/分享率/完读率/涨粉）。当用户要记发布台账/登记已发文章/催回填数据/查哪篇逾期没填/复盘阅读数据/算评论率时使用。"
description_zh: 公众号发布台账 + 数据复盘，markdown 表格，零依赖。
description_en: Manage a WeChat publish ledger and retro-analyze post metrics.
agent_created: true
category: writing
version: "1.0.0"
metadata:
  author: "读读书悦悦己"
---

# 发布台账与复盘（gzh-ledger）

## 何时用
- 发完一篇要登记：状态、时间、群发后阅读 / 点赞 / 在看 / 评论 / 分享 / 完读率 / 涨粉。
- 攒了几篇，想看哪篇逾期没回填数据，或复盘哪篇评论率高。

## 用法
```bash
# 生成空白台账模板（首次用）
python scripts/ledger_tool.py ledger --file 发布台账.md --init

# 登记一篇
python scripts/ledger_tool.py ledger --file 发布台账.md --add --title "标题" --topic 选题3 --status 已群发 --time 2026-10-28

# 逾期催办（按发布时间算 24h/72h，没回填就报）
python scripts/ledger_tool.py ledger --file 发布台账.md --audit

# 结构自检
python scripts/ledger_tool.py ledger --file 发布台账.md --check

# 数据复盘
python scripts/ledger_tool.py retro --file 发布台账.md

# 内置自测
python scripts/ledger_tool.py selftest
```

## 台账格式
markdown 表格，固定 12 列：`# | 标题 | 选题 | 状态 | 时间 | 阅读 | 点赞 | 在看 | 评论 | 分享 | 完读率 | 涨粉`。`--init` 会生成带表头的模板。

## 逾期催办逻辑
- 已群发且 ≥24h 没填阅读数 → error（提醒回填）
- 已群发且 ≥72h 没填完读率 → error
- 草稿箱篇目不参与催办（还没读者）

## 脱敏说明
不绑定具体账号：台账是你自己的记录文件，本工具只读写你指定的 `--file`，不含任何账号 id / 个人路径 / 联系方式。
