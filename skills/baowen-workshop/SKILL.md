---
name: baowen-workshop
display_name: 爆文工坊
display_name_en: ViralForge
description: 头条号（今日头条创作者）从账号诊断到爆款成稿、到数据复盘与追爆的全链路运营系统。触发场景：用户给出头条号主页链接（toutiao.com/c/user/token/...）或账号名，要求"分析/诊断/看看这个号怎么样""怎么运营""激活/起号/盘活"；以及在已有账号上要求"写微头条/写爆款/出稿/写长文/回复评论/周复盘/日复盘/自动运营/定时发稿/追爆款/看后台数据"时使用。覆盖主页与后台真实数据采集、定位漂移与低质诊断、爆款人设与选题、100-150字微头条成稿、1200-1500字首发长文、评论回复话术、晚20:00黄金档排期、数据闭环与追爆机制、半自动定时任务配置（只出稿存草稿，不代用户点发布）。
description_zh: 头条号爆款内容自动化生产系统。把"诊断账号 → 定人设 → 出微头条与长文成稿 → 配评论话术 → 数据复盘 → 追爆款"串成一条流水线，用账号自己的真实数据决定写什么，帮你把"偶尔爆一条"变成"稳定出爆款"。
description_en: An end-to-end Jinri Toutiao (Toutiao) creator growth system. It audits an account, locks a persona, drafts viral micro-posts and long-form articles, supplies comment-reply scripts, and runs data-driven retrospectives with a hit-chasing loop — turning occasional viral hits into a repeatable pipeline. Publishing stays manual and in the user's hands.
examples_zh:
  - "帮我诊断一下这个头条号：toutiao.com/c/user/xxxxx"
  - "按爆文工坊给我写一条今天的微头条，走人情世故题材"
  - "把上周赞最高的那条微头条扩写成 1200 字首发长文"
examples_en:
  - "Audit this Toutiao account for me: toutiao.com/c/user/xxxxx"
  - "Write today's micro-post for me using the viral workshop playbook"
  - "Expand last week's top-liked micro-post into a 1,200-word debut article"
version: 1.0.0
author: "读读书悦悦己"
---

# 头条号爆款运营系统

本系统把一个头条号从「诊断 → 定位 → 成稿 → 发布排期 → 评论互动 → 数据复盘 → 追爆款」全链路跑通。
核心信条：**用该账号自己的真实数据决定写什么，不写正确的废话。**

## 先判断用户要做哪一类任务，再读对应参考文件

| 用户意图 | 必读参考 |
|---|---|
| 采集主页 / 看后台数据 | @references/collection-guide.md |
| 诊断账号、找问题 | @references/diagnosis-checklist.md |
| 写激活方案 / 改造账号 | @references/playbook-template.md |
| 写微头条成稿 | @references/proven-viral-cases.md + @references/title-and-hook-library.md |
| 写首发长文 | @references/article-playbook.md |
| 粉丝画像、双轮策略 | @references/fan-insights.md |
| 回复评论 | @references/comment-reply-library.md |
| 周复盘 / 日复盘 / 追爆 / 调权重 | @references/growth-loops.md |
| 配置定时任务 / 自动化 | @references/automation.md |
| 官方课程方法论 | @references/course-map.md |
| 节日热点选题 | @references/holiday-calendar.md |

## 一、诊断新账号

1. 按 @references/collection-guide.md 采集（用 `web.fetch` 渲染；`curl` 或未登录 API 必死，只返回 JS 空壳）。
2. 按 @references/diagnosis-checklist.md 过八项，分体裁看数据，识别定位漂移与「AI 批量生产」信号。
3. 按 @references/playbook-template.md 出方案：做减法 → 给逐字稿 → 给第一周 7 条成稿 → 给 30 天排期。

## 二、成稿铁律（已被真实账号爆款验证，必须遵守）

- **微头条 100-150 字**（实测均值 106 字最爆）；不要标题；一条只写一个生活切片。
- 结构：钩子（具体数字 / 冲突）→ 一句对话原话 → 一个身体反应（鼻子一酸 / 愣了半天 / 站十分钟）→ 一句轻感慨 → 开放式提问或 AB 选择。
- 题材权重：人情世故 > 钱与账 > 外卖日常 > 35 岁职场焦虑。
- **发布时间固定晚 20:00**（黄金互动窗 20:00-22:00，发后 1 小时内回完评论）。
- 标签 ≤3 个白名单；配图 3 张；发布勾选「首发」。
- 长文 1200-1500 字，数字 + 身份 + 冲突标题，声明首发吃动态分成（详见 @references/article-playbook.md）。

## 三、自动化运营边界

按 @references/automation.md 配置定时任务。**安全红线：系统只写稿并存后台草稿，永远不替用户点「发布」；只生成评论建议话术，永远不替用户回复。最后一键永远在用户手里。** 登录态过期就停下让用户重登，不硬闯。

## 四、数据闭环

每次复盘用浏览器读后台真实数据（展现 / 阅读 / 赞 / 评 / 涨粉），对照 @references/growth-loops.md 的阈值：赞 >100 追同结构、赞 >300 扩写长文、连续扑街回到已验证题材。结果写回运营台账，下次写稿优先高权重题材。批量数字可用 `scripts/tally.py` 统计，避免口算出错：

```
python3 scripts/tally.py --label 微头条赞 "3,5,47,12,151,4,939"
```

## 五、栏目排期（每周 7 条）

| 周几 | 栏目 | 题材方向 |
|---|---|---|
| 周一 / 周三 | 职场吐槽 | 35 岁焦虑、95 后领导、体检报告 |
| 周二 | 钱与账单 | 工资到账、房租、水电、信用卡 |
| 周四 | 人情往来 | 随礼、亲戚借钱、同事带早餐 |
| 周五 | 外卖日常 | 一个人吃饭、夜班便利店、骑手故事 |
| 周六 | 粉丝向年代 | 80/90 年代回忆，唤醒老粉 |
| 周日 | 纯提问帖 | 扎心情绪瞬间，拉评论 |

## 六、红线（必须遵守）

1. 每天最多 1 条，断更可以，烂发不行。
2. 标签 ≤3 个，只从白名单选。
3. 低流量旧内容不删不改，自然沉底。
4. 不互赞、不互粉、不买粉。
5. 不虚构极端惨事（大病 / 被裁跳楼）。
6. 不碰与内容无关的热点。
7. 自动化只做到「出稿待发布」，绝不代用户点发布。

## 适用平台

本系统以头条号为蓝本，其方法论（短切片、数字钩子、情绪共鸣、评论区运营）可平移到：公众号、小红书、知乎、B 站动态、抖音文案。
