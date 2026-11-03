---
name: gzh-score
display_name: 选题评分与任务书
display_name_en: Topic Scoring & Brief
description: "公众号选题四维评分（跨平台热度/共鸣面/情绪张力/风险可控，权重默认0.3/0.3/0.2/0.2，低于60不写、60至75备选、高于75主推）与写作任务书生成。当用户要给选题打分/算选题分/判断选题值不值得写/生成写作任务书/出文章大纲骨架/列本篇禁忌时使用。"
description_zh: 选题四维评分 + 写作任务书生成，通用可配置。
description_en: Score WeChat topics on four dimensions and generate a writing brief.
agent_created: true
category: writing
version: "1.0.0"
metadata:
  author: "读读书悦悦己"
---

# 选题评分与任务书（gzh-score）

## 何时用
- 手里一堆选题，不知道先写哪个：四维打分排序。
- 定了选题，要一份写作任务书（切入角 / 骨架 / 禁忌 / 配图建议）。

## 用法
```bash
# 四维评分（各 0–10）
python scripts/score_tool.py score --heat 8 --resonance 9 --tension 7 --risk 9 --name 老登

# 自定义权重
python scripts/score_tool.py score --heat 8 --resonance 9 --tension 7 --risk 9 --weights heat=0.4,resonance=0.3,tension=0.2,risk=0.1

# 分数回写选题库（--topic-file 指向你的选题库 md）
python scripts/score_tool.py score --no 3 --heat 8 --resonance 9 --tension 7 --risk 9 --save --topic-file 选题库.md

# 生成写作任务书（可直接给参数，也可从选题库取切入角/佐证）
python scripts/score_tool.py brief --no 3 --topic-file 选题库.md --force
python scripts/score_tool.py brief --name 老登 --angle "用代际视角" --evidence "微博热搜#1" --force

# 内置自测
python scripts/score_tool.py selftest
```

## 评分口径
- 总分 = Σ(维度分 × 10 × 权重)，满分 100。
- <60 不写 · 60–75 备选 · >75 主推。
- 阈值与权重都是通用经验值，换赛道用 `--weights` 重设即可。

## 任务书的禁忌来源
「本篇禁忌」取自 `rules/lint_rules.json` 的 error 级红线（与 gzh-lint 共用）。找不到时用内置最小红线兜底。

## 脱敏说明
不绑定具体账号：无账号 id / 个人路径 / 联系方式。字数、标题上限、配图数都是通用默认值，直接可用。
