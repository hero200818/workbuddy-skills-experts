---
name: microblast
display_name: 微爆引擎
display_name_en: MicroBlast
description: 微头条与头条号爆款内容自动化运营系统，覆盖选稿、评论文案、批量生成、发布前质检、排期与数据复盘。当用户要选一条今晚该发的微头条、给评论写回复、批量生成微头条、做发布前质检、做排期或数据复盘，或提到微爆引擎、microblast、老周人设、微头条运营时使用。纯 Python 标准库实现，零第三方依赖。
description_zh: 一个会养人设、挑爆款、回评论、看数据的微头条自动化运营系统，选题到复盘全闭环，内置老周人设与 246 条示例内容。
description_en: End-to-end viral micro-post operations for Toutiao, covering persona drafting, smart picking, comment replies, scheduling and data review. Pure Python standard library, zero dependencies.
version: 1.0.4
author: "读读书悦悦己"
---

# 微爆引擎 MicroBlast · 微头条爆款运营系统

一个会**养人设、挑爆款、回评论、看数据**的短文与微头条自动化运营系统。
从「虚拟人设连续创作 → 智能选题 → 四维选稿 → 排期 → 评论运营 → 数据复盘」全闭环，
纯 Python 标准库实现，**零第三方依赖**，Python 3.8+ 即可运行。

内置人设：**P01 老周**（35 岁北漂程序员，含家庭、职场、朋友圈完整设定，246 条示例内容）。

## 一、环境（先确认）

- 本技能为**纯标准库**实现，无需 pip 安装任何依赖。
- **技能根目录** = 本 `SKILL.md` 所在目录，下文记作 `$SKILL`；所有命令都在 `$SKILL` 下执行。
- 解释器优先用 `python3`（或 `python`）。若系统没有，使用 WorkBuddy 客户端自带的 Python：
  - Windows：用户主目录下的 `.workbuddy/binaries/python/envs/default/Scripts/python.exe`
  - macOS 与 Linux：用户主目录下的 `.workbuddy/binaries/python/envs/default/bin/python`

```bash
cd "$SKILL"
PY="$(command -v python3 || command -v python)"
# 若上面为空，改用 WorkBuddy 自带 Python 的绝对路径
```

## 二、统一入口 super_hub.py（推荐先用这个）

```bash
"$PY" scripts/super_hub.py status                         # 系统体检（内容库 / 覆盖率 / 数据提示）
"$PY" scripts/super_hub.py daily                          # 日常一条龙：体检 + 选稿 + 排期
"$PY" scripts/super_hub.py pick --slot evening            # 智能选稿（按今天星期 + 时段 + 爆款基因分）
"$PY" scripts/super_hub.py pick --day 3 --slot night      # 指定星期 / 时段选稿
"$PY" scripts/super_hub.py reply "老周写得太真实了" 北漂   # 评论回复草稿（自动判断评论类型）
"$PY" scripts/super_hub.py quality P01_d12_n3             # 发布前质检（去 AI 味 / 字数 / 钩子 / 人设一致性）
"$PY" scripts/super_hub.py generate relative 5            # 批量生成并自动查重入库
"$PY" scripts/super_hub.py plan 7                         # 未来 7 天智能排期
"$PY" scripts/super_hub.py analyze                        # 数据优化分析（需先有性能数据）
"$PY" scripts/super_hub.py dashboard                      # 生成 dashboard.html 看板
"$PY" scripts/super_hub.py optimize                       # 超级优化器
```

## 三、单脚本直驱（hub 之上的细粒度控制）

```bash
# 内容库引擎
"$PY" scripts/content_engine.py stats                     # 内容库统计（总量 / 主题分布 / 字数）
"$PY" scripts/content_engine.py list --status pending     # 列出待发布
"$PY" scripts/content_engine.py publish --id P01_d14_n1   # 标记已发布并记录

# 智能选稿
"$PY" scripts/smart_selector.py next --slot evening       # 今晚该发哪条
"$PY" scripts/smart_selector.py analyze                   # 星期维度覆盖率分析

# 评论运营
"$PY" scripts/comment_reply.py reply "评论内容" 北漂      # 贴脸回复 + 零评论破冰

# 内容生成
"$PY" scripts/content_generator.py save relative 5        # 按主题批量生成并入库
"$PY" scripts/content_generator.py gene <基因类型> 3      # 按爆款基因生成

# 排期 / 质检 / 数据
"$PY" scripts/schedule_planner.py next 7                  # 7 天排期
"$PY" scripts/quality_checker.py check P01_d12_n3         # 单条质检
"$PY" scripts/data_tracker.py                             # 记录阅读 / 评论 / 点赞（生成性能数据）
"$PY" scripts/generate_dashboard.py                       # 生成 dashboard.html
```

## 四、可用主题键（generate 的 theme_key）

`salary`（工资 / 收入） · `relative`（人情世故 / 亲戚） · `age35`（35 岁危机） · `takeout`（外卖日常） · `family`（家庭亲情） · `humor`（轻松幽默） · `national`（国民话题） · `workplace`（职场） · `contrast`（职场对比）

## 五、目录结构与数据资产

技能根目录（即 `SKILL.md` 所在目录）只有三类内容：`SKILL.md`、`scripts/`、`references/`。

引擎脚本（`scripts/`，共 15 个，全部为纯标准库 Python）：

- scripts/super_hub.py — 统一入口，编排全部能力
- scripts/content_engine.py — 内容库状态机（统计 / 列表 / 发布标记）
- scripts/smart_selector.py — 四维智能选稿
- scripts/content_generator.py — 按主题与爆款基因批量生成
- scripts/comment_reply.py — 评论分类与回复生成
- scripts/schedule_planner.py — 分时段智能排期
- scripts/quality_checker.py — 发布前质检（去 AI 味 / 字数 / 钩子 / 人设一致性）
- scripts/data_tracker.py — 性能数据录入
- scripts/generate_dashboard.py — 生成数据看板
- scripts/content_optimizer.py — 数据优化与策略迭代
- scripts/super_optimizer.py — 超级优化器
- scripts/backfill_data.py — 后台数据补录
- scripts/backfill_library.py — 内容库补录
- scripts/restore_day57.py — 历史批次恢复
- scripts/followup_viral.py — 爆款追更

数据资产（`references/`，扁平存放、无子目录）：

- references/P01.json — 虚拟人设档案（老周：身份、家庭、职场、语言风格）
- references/P01_memory.json — 人设生活记忆与事件线（保证连载连贯）
- references/viral_genes.json — 爆款基因库（钩子、情绪、结构基因）
- references/comment_templates.json — 评论话术模板库
- references/content_deepening_standard.json — 内容深化标准
- references/schedule_plan.json — 排期策略与排期结果
- references/day12_num1.json — 单条内容样本；内容库共 246 个同规则文件，命名规则为 `day{天}_num{序号}.json`，状态机 pending / published / archived
- references/perfomance_tracking.csv — 性能数据表（表头已就绪，发布后由 data_tracker.py 追加记录）
- references/PROJECT.md — 项目方法论与原始说明
- references/LICENSE.txt — 许可说明
- references/requirements.txt — 依赖说明（本技能零依赖）

> 新增内容由 `generate` 自动写入 `references/`；该目录下不再创建子目录，脚本按相对技能根目录的路径读取数据。

## 六、使用规则与注意事项

- **当前仅 P01（老周）人设**已接线：内容库、人设、记忆都指向 P01。换号时在 references 目录下新增对应的人设与记忆文件，并把脚本里的编号改掉即可。
- **数据类功能（`analyze` / `dashboard` / `optimize`）需先有性能数据**：发布后用 `data_tracker.py` 记录。无数据时 `analyze` 会提示「暂无数据」，`status` 会优雅降级而非报错。
- `generate` 会自动查重，已存在相似内容不会重复入库。
- 脚本只处理本地文件，**不含任何平台密钥**；自动发布、抓取评论需自行对接对应平台登录态或 API。

## 七、试试这样用

- 用微爆引擎选一条今晚发的微头条
- 给这条评论写个老周风格的回复：老周写得太真实了
- 批量生成 5 条人情世故题材的微头条
- 给 P01_d12_n3 做发布前质检
- 帮我排明天到周五的发布时间
