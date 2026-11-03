# MicroBlast · 微爆引擎

> 一个会**养人设、挑爆款、回评论、看数据**的短文 / 微头条自动化运营系统。
>
> 从「虚拟人设连续创作 → 智能选题 → 四维选稿 → 排期 → 评论运营 → 数据复盘」全闭环，
> 纯 Python 标准库实现，**零第三方依赖**，换个人设文件就能跑在任何内容平台。

---

## ✨ 它解决什么问题

一个人运营一个号，最累的不是写，是：
- 人设写着写着就崩了（今天说单身明天晒娃）；
- 发什么全靠拍脑袋，不知道哪条会爆；
- 评论区回不过来，回得像客服；
- 发完就忘，没有数据反哺下一条。

MicroBlast 把这套流程拆成可复用的脚本 + 方法论资产：
**让机器按"老周"这样的虚拟人设稳定量产，按爆款基因自动选今晚该发什么，再按评论类型生成贴脸的回复。**

## 🧰 功能模块

| 模块 | 脚本 | 作用 |
|---|---|---|
| 内容库引擎 | `content_engine.py` | 内容入库 / 状态机(pending·published·archived) / 记录数据 |
| 内容生成 | `content_generator.py` | 按人设+上下文批量生成短内容 |
| 爆款质检 | `quality_checker.py` | 去AI味、字数、钩子、人设一致性检查 |
| 智能选稿 | `smart_selector.py` | 按「星期几策略 + 时段 + 爆款基因分 + 评论潜力分」四维排序 |
| 排期规划 | `schedule_planner.py` | 一周分时段/分星期的发布排期 |
| 评论话术 | `comment_reply.py` | 按评论类型生成老周口吻回复 + 零评论破冰 |
| 续集爆款 | `followup_viral.py` | 为已验证爆款自动规划续集 |
| 数据看板 | `data_tracker.py` / `generate_dashboard.py` | 记录阅读/评论/点赞，出复盘面板 |

## 📁 目录结构

```
microblast/
├── personas/                 # 虚拟人设档案（换这里就是换个号）
│   └── P01.json              #   示例：老周，35岁北漂程序员
├── memory/                   # 人设生活记忆 / 事件线
├── content_library/P01/      # 内容库（246条示例短内容）
├── data/                     # 方法论资产
│   ├── viral_genes.json          # 爆款基因库
│   ├── comment_templates.json    # 分类评论话术模板
│   ├── content_deepening_standard.json  # 内容深化标准
│   └── schedule_plan.json         # 分时段排期策略
├── scripts/                  # 全部引擎脚本（纯标准库）
└── README.md
```

## 🚀 快速开始

环境要求：**Python 3.8+，无需 pip install 任何东西。**

```bash
# 1. 看内容库整体状态 / 待发多少条
python3 scripts/content_engine.py stats

# 2. 让选稿器按"今晚"挑一条最该发的
python3 scripts/smart_selector.py next --slot evening --exclude "上一条ID"

# 3. 给一条评论生成贴脸回复
python3 scripts/comment_reply.py reply "评论内容" 主题

# 4. 发布后标记并记录数据
python3 scripts/content_engine.py publish --id P01_d14_n1
python3 scripts/content_engine.py list --status pending
```

## 👤 换成你自己的号

1. 复制 `personas/P01.json` → `personas/P02.json`，改掉姓名/年龄/职业/收入/城市/口头禅；
2. 同步修改 `memory/P02_memory.json` 的故事线；
3. 所有脚本带 `--persona P02` 即可切到新号；
4. 在 `data/viral_genes.json` 里按你目标平台的爆款规律调权重。

## 🧭 平台适配

本系统原生于头条号/微头条，产出的是 150 字内、口语化、有钩子的短内容。
同一套脚本改人设与选题权重后，可直接用于：**公众号短文、小红书图文、知乎想法、微博、X 短帖**。
（浏览器抓评论/自动发布部分需对接对应平台的登录态或 API，脚本本身不含任何平台密钥。）

## 📜 License

MIT —— 可自由复制、修改、商用。保留作者声明即可。
