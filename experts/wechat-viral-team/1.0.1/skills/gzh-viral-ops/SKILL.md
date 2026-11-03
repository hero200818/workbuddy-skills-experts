---
name: gzh-viral-ops
description: "WeChat Official Account viral content pipeline: bootstrap the project scaffold, score and pick topics, generate a writing brief, lint against WeChat operation rules, trim AI watermarks and compress images, assemble an inline-HTML post, push to the drafts box via Yanxu, archive to ima knowledge base, and review 24h/72h data. Use whenever the task involves 公众号 writing, 选题, 爆款, 标题, 配图, 排版, 发草稿, 数据复盘."
---

# 公众号爆文流水线

> 这套流程把「选题 → 成稿 → 自检 → 配图 → 装配 → 发布 → 复盘」串成一条带命令的链。
> 设计原则：**配置一处改、规则数据化、功能能自测、发布有总闸、决策有依据。**
> 凡是能变成规则的，就不要靠灵感；凡是能机检的，就不要靠记性。

## 0 · 先确认工作目录

脚本会自动定位项目根：

1. 优先用环境变量 `GZH_ROOT`
2. 否则用脚本上两级目录（若那里有 `config.json`，说明脚本就在项目内）
3. 否则回退到**当前工作目录**（只要它含 `config.json` / `选题库.md` / `发布台账.md` 之一）

**已有项目**（例如 `~/Documents/my-account`）：
直接 `cd` 进去再调脚本，不要复制一份新的。

**全新项目**：把 `templates/project/` 下的内容复制到工作目录，再跑一次自测确认环境：

```bash
cp -r <skill>/templates/project/. ./        # config.json / rules/ / 选题库.md / 发布台账.md
mkdir -p 配图 配图/raw
python <skill>/scripts/gzh.py selftest      # 期望 29 passed / 0 failed
```

`config.json` 里的 `account.yanxu_account_id`、`ima_kb_id` 是自带填充的，换号时必须改。

> 下文命令一律简写为 `python scripts/gzh.py`。若脚本不在项目内，换成实际路径即可。

## 1 · 七步流水线

### Step 1 · 看清战场

```bash
python scripts/gzh.py status
```

一眼看清：每篇稿走到哪一步（字数/图/lint/台账/资料）、选题池多少条、有没有欠数据。**别跳过这步直接写稿。**

### Step 2 · 定选题

```bash
python scripts/gzh.py pick --top 3      # 按分数排，给三候选
```

四维加权：热度 30% / 共鸣 30% / 张力 20% / 风险 20%，脚本出百分制。

**必须用命令算，不许心算。** 新选题入库后立刻回写分数：

```bash
python scripts/gzh.py score --no 21 --heat 7 --resonance 9 --tension 7 --risk 9 --save
```

结论线：<60 不写；60–75 备选；>75 主推。**风险分 <5 一律不写，不看总分。**

打分档位见 `references/scoring-rubric.md`。

### Step 3 · 出任务书

```bash
python scripts/gzh.py brief --no 21
```

产出写作任务书：切入角、结构骨架、禁忌清单（**从 `rules/lint_rules.json` 动态生成**，加规则任务书自动多一条）、配图方案、目标字数。

**任务书先给人看，别闷头写完再说。**

### Step 4 · 成稿

按任务书写正文。三稿制：
1. 写完整稿（先把话说清楚，别管文采）
2. 逐条划掉 AI 味清单（见 `references/compliance-baseline.md` 第五节）
3. 把抽象句换成具体动作或原话

标题写作阶段就按 **30 字**写，不要先写 32 字再砍——砍两刀容易把钩子砍断。公式见 `references/title-and-hook-library.md`。

### Step 5 · 自检

```bash
python scripts/gzh.py lint --md 选题N_xxx.md
```

`error` 必须清零，`warn` 逐条判断。标题通道：默认按言序 30 字；走微信原生编辑器加 `--channel wechat`（64 字）。

**脚本只查机检项。** 事实来源、原创资质、是否整篇搬运热搜——必须人工过一遍。

### Step 6 · 配图

```bash
python scripts/gzh.py assets --dir 配图/raw --out 配图 --trim 72   # 去水印 + 压缩
python scripts/gzh.py assets --dir 配图 --check                    # 双档核查
```

**出图立刻裁底去水印（至少 72px，位置不固定的图要 96px），裁完看一眼再往下走**，不要留到最后。封面 ≤2MB、正文图 ≤1MB，成品统一 `_clean.jpg`，源图归 `配图/raw/`。

需要 Pillow；没装就先装（国内直连 PyPI 常超时，用镜像）：
```bash
pip install pillow -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Step 7 · 装配 · 发布 · 复盘

```bash
python scripts/gzh.py preflight --slug 选题N     # 总闸：6 项全绿才往下走
python scripts/gzh.py yanxu --md 选题N_xxx.md    # 生成言序参数 JSON
```

推送只到**草稿箱**。之后提醒用户三件事：开原创声明、开留言、自己先评论 1–2 条置顶。

台账登记与回填催办：

```bash
python scripts/gzh.py ledger --check --md 选题N_xxx.md
python scripts/gzh.py ledger --audit     # 按发布时间自动算 24h/72h 逾期
python scripts/gzh.py retro              # 评论率/在看率/分享率/完读率
```

## 2 · 命令速查

| 命令 | 解决什么 |
|---|---|
| `status` | 全局：每篇稿到哪一步、选题池健康度、欠数据 |
| `pick` | 按分排序，告诉你下一篇写什么 + 下一步命令 |
| `score --save` | 四维评分并回写选题库「分数」列 |
| `brief` | 生成写作任务书（禁忌从规则文件动态生成） |
| `new` | 新选题脚手架（主稿/发布包/配图清单/meta） |
| `lint` | 合规 + 结构自检 |
| `assets` | 去水印 / 压缩 / 双档核查 |
| `preview` | 内联 HTML → 图片 base64 自包含预览版 |
| `yanxu` | MD → 言序 compose_article 参数 JSON |
| `bundle` | 生成「完整资料.md」（入库必带，`--meta auto` 自动汇总） |
| `ship` | 一键装配 lint→图→引用→bundle（默认预演，`--go` 才写） |
| `preflight` | 发布总闸 |
| `ledger` | 台账 list / add / check / audit |
| `retro` | 数据复盘 |
| `doctor` | 项目体检（配置/规则/文档漂移/凭证残留） |
| `selftest` | 自测 29 例，**改脚本或规则后必跑** |

## 3 · 硬约束

| 项 | 值 |
|---|---|
| 标题（言序草稿箱） | ≤30 字 |
| 标题（微信原生） | ≤64 字 |
| 摘要 | ≤120 字 |
| 正文 | 1200–2000 字 |
| 首段 | ≤130 字 |
| 单段 | 软 120 / 硬 160 字 |
| 配图 | 3–5 张；封面 ≤2MB；正文图 ≤1MB |
| 水印 | ImageGen 出图底部必裁，**至少** 72px，裁完看图确认 |

## 4 · 参考文件

| 文件 | 读它是为了 |
|---|---|
| `references/compliance-baseline.md` | 内容红线、标题禁区、原创声明、去 AI 味清单 |
| `references/pitfalls.md` | 言序 / ima / 公众号编辑器 / ImageGen 的硬坑（**最贵的部分**） |
| `references/title-and-hook-library.md` | 标题公式、开头钩子、结构骨架 |
| `references/scoring-rubric.md` | 四维评分档位锚点、判例、常见偏分 |
| `references/visual-spec.md` | 配图数量位置、两档体积、去水印、提示词模板、验收清单 |
| `references/data-review.md` | 台账数据列、五个派生指标、回填时点、三看归因、常见误判 |
| `templates/project/` | 新项目骨架：config / 规则 / 选题库 / 台账 |

## 5 · 常见失误

1. **没 `status` 就开写** → 重复写已有稿，或写了一条分数 52 的选题
2. **标题先写 32 字再砍** → 钩子被砍断，重写一遍更顺
3. **忘了去水印** → 发出去读者一眼看到"AI生成"
4. **图超 1MB** → 言序上传报 `ret:10001`
5. **对言序主题有期待** → 微信端会清洗样式，最后是素排版
6. **开留言忘了** → 整篇的评论钩子白写
7. **改脚本不跑 `selftest`** → 正则失效只会"静默不查"，比报错更危险
8. **手填分数 / 手算字数** → 必错，用命令
9. **只改本地不刷知识库** → 库里还是旧版标题，检索时两套说法
10. **改表格列忘了改自动化** → 每日追加行会串列，表结构改动要三处同步

## 6 · 升级脚本时注意

`scripts/gzh.py` 是项目内版本的**可移植分支**，与项目版差异只有三处：

1. `ROOT` 增加了 `GZH_ROOT` 环境变量与工作目录回退
2. `_topic_rows(path=None)` 支持指定路径
3. 四条自测用例改为自足（用临时目录，不再依赖 `选题3` 和真实配图）

从项目同步新版时，这三处改动要重新打一遍，改完必跑 `selftest`。
