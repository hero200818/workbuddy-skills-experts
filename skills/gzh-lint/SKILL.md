---
name: gzh-lint
display_name: 公众号合规自检
display_name_en: WeChat Article Linter
description: "公众号文章合规与结构机检：双通道标题上限（言序30/微信64）、诱导分享、疗效断言、隐私号段、绝对化用语、混淆官方、未证实爆料、金融荐股、违规导流、正文外链、AI味套话/黑话等可机检红线，以及篇幅/段落/配图/emoji 结构体检。当用户要过合规/自查红线/lint稿件/标题超没超/去AI味/检查正文结构时使用。"
description_zh: 公众号文章合规与结构机检，覆盖微信通用红线与去AI味，双通道标题上限。
description_en: Lint WeChat articles for compliance red lines and structure issues.
agent_created: true
category: writing
version: "1.0.0"
metadata:
  author: "读读书悦悦己"
---

# 公众号合规自检（gzh-lint）

把一篇公众号文章（markdown）丢进来，机器先替你把「能机检的红线与结构问题」过一遍，发布前心里有底。

## 何时用
- 写完稿想自查：诱导分享、标题党、疗效断言、手机号/身份证、广告法绝对化、未证实爆料、金融荐股、违规导流、正文外链、AI 味套话黑话……
- 标题超没超（言序 30 字 / 微信 64 字按通道）、正文篇幅 / 段落 / 配图数 / emoji 数是否健康。

## 用法
```bash
# 默认微信通道（标题上限 64）
python scripts/lint_tool.py lint --md 稿件.md

# 言序直发（标题上限 30，超了发不进去）
python scripts/lint_tool.py lint --md 稿件.md --channel yanxu

# 机读结果（CI / 流水线用）
python scripts/lint_tool.py lint --md 稿件.md --json

# 内置自测
python scripts/lint_tool.py selftest
```

返回码：命中 error 级 → 1（拦截）；否则 0（warn 只提示，不拦）。

## 规则来源（单一真相源）
规则默认读取同目录或项目里的 `rules/lint_rules.json`（与流水线共用一份，改规则只改它）。找不到时回退内置 15 条通用规则（微信《运营规范》+ 去 AI 味），保证离线可用。可用 `--rules` 指定自定义规则文件。

## 边界
脚本只查「可机检」项。涉企 / 涉政 / 未证实信息的事实与信源、原创资质，仍需人工判定。

## 脱敏说明
本包不绑定任何具体公众号账号：无账号 id、无个人路径、无联系方式。标题上限等都是公众号 / 平台的通用规则，换个项目直接能用。
