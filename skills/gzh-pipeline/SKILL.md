---
name: gzh-pipeline
display_name: 公众号爆款流水线
display_name_en: WeChat Viral Pipeline
description: >-
  「读读书悦悦己」公众号从热搜选题到草稿箱的一条龙流水线。当用户要"写公众号/写爆款/
  找选题/出稿/做成发布包/发草稿/入库ima/自查合规/体检项目/自检脚本"时使用。覆盖：八平台热搜抓取与去重筛选、
  按账号调性去AI味成稿、合规与结构自检（脚本化）、配图生成与去水印压缩、经言序发公众号草稿箱、
  全资料入库 ima 知识库、发布台账与数据回填，以及 doctor/selftest/preflight 三件套构成的自我进化闭环。
  触发词：公众号、爆款文章、选题、发布包、发草稿、公众号排版、入库ima、总闸、体检、自检、
  老登、读读书悦悦己。
description_zh: 公众号爆款全链路流水线：选题→成稿→自检→配图→发草稿→入库→复盘，配置单点化、规则数据化、带自测与发布总闸。
description_en: End-to-end WeChat Official Account viral content pipeline with scripted compliance checks, self-test and preflight gate.
metadata:
  author: "读读书悦悦己"
  version: "2.0.0"
---

# 公众号爆款流水线

把「选题 → 成稿 → 自检 → 配图 → 发草稿 → 入库 → 复盘」七步固定下来，每步都有脚本或明确清单，**不要临场重搓**。

## 开工前必读（30 秒，省 2 小时）

| 文件 | 读它是为了 |
|---|---|
| `config.json` | **唯一配置源**：标题上限/KB id/账号/体积档/后缀名，全在这里。改数字先改它 |
| `rules/lint_rules.json` | **规则数据**：想加检查项就追加一条，不用改 Python |
| `rules/创作规范与合规基线.md` | 账号调性、内容红线、标题规范、去AI味清单 |
| `rules/技术踩坑手册.md` | 言序/ima/公众号/ImageGen 的硬约束（**最贵的部分**） |
| `选题库.md` | 挑哪个选题、什么状态 |
| `发布台账.md` | 上篇数据如何、这次要改什么 |

**先盘点已有 Skill**（见踩坑手册第六节）：`wechat-publisher`（wenyan-cli，MD 一键发草稿，有主题渲染）、`wechat-article-pro`、`wechat-write`、`wechat-cover`、`wechat-article-visual-pack`。能用现成的别手搓。

---

## 四道硬门槛（每篇都必须过，别靠记性）

| # | 门槛 | 什么时候过 | 怎么验证 |
|---|---|---|---|
| 1 | **配图双档体积**：封面 ≤2MB / 正文图 ≤1MB | 上传前 | `gzh.py assets --dir 配图 --check` 必须全绿 |
| 2 | **标题 ≤30 字**（言序硬上限） | **写作时就守**，不等到发稿 | `gzh.py lint`（默认 yanxu 通道，超 30 直接 error） |
| 3 | **去 AI 水印** | **出图后立刻**，早于插正文 | `gzh.py assets --trim 72`；逐张 `ViewImage` 复核 |
| 4 | **完整资料一并入库** | 入 ima 前 | `gzh.py bundle` 先生成，再和其它文件一起 `add_knowledge` |

> 这四条以前靠我记得，现在都下沉成命令与规则。**门槛没过就别往下走。**

---

## 自检与进化闭环（先跑这几条，再动笔）

```bash
python scripts/gzh.py status      # 一眼看清：稿子到哪一步了、选题池什么状况、有没有欠数据
python scripts/gzh.py selftest    # 自测 32 例：改过脚本或规则，必须全绿
python scripts/gzh.py doctor      # 项目体检：配置/规则/文档/目录/残留/回填时效/评分覆盖
python scripts/gzh.py preflight --slug 选题N   # 发布总闸：一条命令把所有门槛串起来
```

**这套命令构成"自我进化"的闭环**，不是装饰：

| 环节 | 命令 | 防的是什么 |
|---|---|---|
| 规则可增长 | 往 `rules/lint_rules.json` 追一条 | 新踩的坑只写在文档里，下次照样犯 |
| 改动不退化 | `selftest` | 改了 lint 正则写错，规则静默失效，还以为在查 |
| 项目不腐烂 | `doctor` | 台账与稿件打架、凭证残留、目录缺件、文档数字漂移 |
| 执行不靠记性 | `preflight` | 漏跑某一步（水印没去/图超限/没入库/没登记） |
| 决策不靠感觉 | `pick` / `score --save` | 27 条选题靠眼缘挑，分数算完就丢，下次还得重来 |
| 欠账不忘记 | `ledger --audit` | 发完就忘，24h 数据没回填，下一篇还是拍脑袋 |

> **铁律**：任何一次踩坑 → ① 写进 `rules/技术踩坑手册.md` ② 能机检的同时写进 `lint_rules.json` ③ 跑 `selftest` 确认新规则真的会触发。三步齐了才算"学会了"。

---

## 七步流程

### Step 1 · 选题

八平台并行抓取，去重合并后按规则筛：

- **可抓**：百度 `top.baidu.com/board?tab=realtime`、聚合站 `toupage.com/trend/{weibo,zhihu,toutiao}`（快手/小红书/微信在该站是 404，改用搜索）
- **剔除**：涉政外交军事 / 明星隐私 / 未证实谣言 / 过度丧向 / 健康疗效（健康只作轻量备选）
- **评分**：跨平台热度 30% + 共鸣面 30% + 情绪张力 20% + 风险可控 20%，>75 主推
  ```bash
  # --no 编号定位、--save 把总分回写选题库「分数」列，不用手抄
  python scripts/gzh.py score --no 21 --heat 7 --resonance 9 --tension 7 --risk 9 --save
  ```
  四项各 0–10 分，脚本出百分制与结论（<60 不写 / 60–75 备选 / >75 主推）
- **产出**：追加进 `选题库.md`，标 `待写`，**分数列一起填**
- **先问"该写哪条"**，别凭眼缘：
  ```bash
  python scripts/gzh.py pick --top 3     # 按分数排，告诉你下一篇写什么
  python scripts/gzh.py brief --no 21    # 生成写作任务书（切入角/骨架/禁忌/配图）
  ```
- **脚手架**：定了选题就直接开骨架，别手抄五个文件
  ```bash
  python scripts/gzh.py new --slug 选题4 --title "标题（≤30字）"
  # → 主稿 md + 发布包 + 配图清单 + meta.json + 配图/raw/
  ```

### Step 2 · 成稿

按 `rules/创作规范与合规基线.md` 的调性写。硬要求：

1. **开头 100 字内进具体场景**（一个视频/一条弹幕/一次对话），不铺垫、不升华
2. **第二人称**，像唠嗑；句子有长有短，允许停顿和废话
3. **至少 1 个具体细节**（原话、数字、动作），替代抽象抒情
4. **结尾抛一个人人有故事的具体问题**，不喊转发
5. 1200–1800 字，单段 ≤120 字
6. **标题在写作阶段就按 ≤30 字**（言序硬上限）。不要先写 32 字再临时删字——重写一遍钩子比砍两刀更顺。标题必须同时是「具体信息点 + 情绪钩子」，例：「35岁怕优化，60岁怕负担：…你还没轮到你」（29 字）

产出 `选题N_短标题.md`，首行 `# 标题`，正文到 `---` 为止（之后是运营配套，不进正文）。

### Step 3 · 自检（必跑，不跑不许发）

```bash
python scripts/gzh.py lint --md 选题N_xxx.md
```

`error` 必须清零；`warn` 逐条判断。标题上限按通道走：默认 `--channel yanxu`（≤30 字，超了直接 error），走微信原生编辑器可加 `--channel wechat`（≤64 字）。
**脚本只查可机检项**，事实/信源/原创资质仍需人工过一遍清单。

全部环节走完后再跑一次总闸，它会替你确认没有漏项：

```bash
python scripts/gzh.py preflight --slug 选题N
```

### Step 4 · 配图（**出图即去水印，不要等到发稿前**）

用 ImageGen 出图（封面 1536×1024 顶部留白，文中 1024×1024）：

- 风格提示词固定：`flat illustration, solid color blocks, clean simple shapes, no line sketch, warm beige and terracotta orange, no clear face, no readable text`
- 图片一律落 `配图/raw/`（源图，不上传），处理后的成品留 `配图/` 根目录

**出图后立刻跑**（ImageGen 右下角固定带「AI生成 WORKBUDDY」水印，必须在任何后续步骤之前裁掉）：

```bash
python scripts/gzh.py assets --dir 配图/raw --out 配图 --trim 72
```

这会一步完成：去水印（裁底 72px）+ 转 JPEG + 压到言序双档上限内（**封面 ≤2MB / 正文 ≤1MB**，按文件名含 `cover/封面` 自动判定档位）。

**上传前再核查一次**（只读，不做处理）：

```bash
python scripts/gzh.py assets --dir 配图 --check
```

必须全绿才能上传——否则言序报 `ret:10001`。
- 逐张 `ViewImage` 核对：无水印、风格统一、无可识别人脸

> 配图处理的完整要点（水印不固定 / 双档体积 / `--dir` 整目录全量重刷会覆盖已发布图）已抽成独立 skill **`gzh-assets`**，可直接调用 `scripts/img_tool.py`；本步骤的 `gzh.py assets` 只是薄封装，逻辑单份。

### Step 5 · 发草稿（言序）

```bash
# 1) 取一次性上传通道（每张图一个 ticket，不可复用）
#    mcp__yanxu__get_upload_channel  scene=cover / body
# 2) 上传
curl -s -F "file=@配图/xx_final.jpg" "https://toolsvip.cn/api/once/upload?ticket=<TICKET>"
# 3) 生成组稿参数（图片映射写 JSON：{"文件名.jpg":"返回的file_path"}）
python scripts/gzh.py yanxu --md 选题N_xxx.md \
  --title "<≤30字标题>" --abstract "<≤100字（言序 compose 上限，超了直接 exit 1，不会静默截断）>" \
  --cover "https://toolsvip.cn/static/cover/..." --map img_map.json
# 4) mcp__yanxu__compose_article  → 拿 info_id
# 5) mcp__yanxu__publish_article (account_id + info_id + theme_id) → 异步，去草稿箱肉眼确认
```

**关键约束**：标题 ≤30 字 · 正文图 ≤1MB · 封面 ≤2MB · 发布异步无查询接口 · **主题样式会被微信清洗，别期待排版效果**。

发完回来先登记台账，再走总闸复核：

```bash
python scripts/gzh.py ledger --add --title "<标题>" --topic "老登/年龄焦虑" --status "草稿箱"
python scripts/gzh.py ledger --check --md 选题N_xxx.md   # 台账标题/字数必须与稿件一致
```

### Step 6 · 入库 ima

目标库 `读读书悦悦己微信公众号原创文章` / `ima_kb_Aotxx8G5`。

**先自动生成「完整资料」，再一起上传**（否则以后在库里检索只能抓到零散片段）：

```bash
python scripts/gzh.py bundle --md 选题N_xxx.md --slug 选题N \
  --meta auto --publish 选题N_发布包.md --images 选题N_配图清单.md
# → 读读书悦悦己_选题N_完整资料.md（元信息 + 正文 + 配图说明 + 发布包 四合一）
# ⚠ 三个章节参数各管一节，缺哪个就静默少一节（不报错）。跑完必看末尾「配图章节 ✓ | 发布包 ✓」是否双勾
# ⚠ --images 要的是**配图清单 md 路径**，不是图片文件列表
# --meta auto：从稿件标题 + yanxu_params.json + 台账自动汇总，写进 选题N_meta.json；
#              已有 meta 文件里人工补的备选标题/标签不会被覆盖，只补缺的键
```

上传链路（**小文件普通 PUT 即可，不用装 SDK**）：

```
create_media(MCP) → 存 cred.json → python scripts/ima_put.py cred.json 文件 → add_knowledge(MCP)
```

入库清单（**8 类，缺一不可**）：
主稿 md、**完整资料 md**、纯文本 txt、终稿版 html、发布包 md、配图清单 md + 全部配图 jpg。
凭证文件用完即删。

- 其中「纯文本 txt / 终稿版 html / 预览版 html」由独立 skill **`gzh-deliver`** 的 `build_deliver.py` 从主稿 md 一键生成（含全内联样式 + base64 自包含预览），不在本流程里手写。
- 上表「上传链路」的 COS 上传（`ima_put.py`）已抽成独立 skill **`gzh-ima`**——核心坑是 COS 临时密钥签名多套一层 `StringToSign`，少一层就 403。

**改稿后刷新知识库**：同名 `file_name` + `duplicate_name_strategy=DUPLICATE_NAME_STRATEGY_REPLACE`，
原地覆盖不新增条目（`file_name` 要填库里已存在的名字）。

### Step 7 · 台账

`发布台账.md` 是**唯一事实来源**，别手写行——手写必错（上一版把 29 字写成 27 字，台账和稿件打架）。

```bash
python scripts/gzh.py ledger --list                    # 看全部
python scripts/gzh.py ledger --add --title "…" --topic "…" --status "草稿箱"
python scripts/gzh.py ledger --check --md 选题N_xxx.md  # 标题/字数一致性校验
```

24h / 72h 回填阅读、评论、分享、完读率，再回来看下一篇改什么。

---

## 决策与流转（v3，2026-10-28）

v2 解决"查得出问题"，v3 解决"知道下一步干什么"。六条命令把散落的四张表（选题库/稿件/配图/台账）连成一条链：

| 命令 | 解决什么 | 典型用法 |
|---|---|---|
| `status` | 一条命令看清全项目：每篇稿到哪一步、选题池多少条、有没有欠数据 | 开工第一件事，别先问"我们写到哪了" |
| `pick` | 从选题池按分数排，直接说下一篇写哪条 + 下一步命令 | `pick --top 3` |
| `score --save` | 分数自动回写选题库，解决"算完就丢" | `score --no 21 --heat 7 --resonance 9 --tension 7 --risk 9 --save` |
| `brief` | 把选题变成可执行任务书（切入角/骨架/禁忌/配图/目标字数） | `brief --no 21`，禁忌清单从 lint_rules.json 动态生成 |
| `ledger --audit` | 按发布时间自动算 24h/72h 是否逾期未回填 | 已接进 `doctor`，周体检会自动催 |
| `ship` | 一键装配：lint → 图双档 → 图片引用 → bundle | 默认只预演，`--go` 才真写文件 |
| `retro` | 台账数据复盘：评论率/在看率/分享率/完读率 | 群发满 3 篇再看，样本不足会自己说"别当真" |

**链路心智模型**（记住这条就不会乱）：

```
热搜 → score --save → 选题库分数列 → pick → brief → 写稿 → lint → ship
                                                              ↓
                          台账 ← 发草稿 ← 言序 ← bundle ← 配图
                            ↓
                    ledger --audit（催回填）→ retro（找规律）→ 影响下一轮选题
```

> 机器能给"该写哪个、缺哪步"，给不了"这篇到底好不好"。分数是决策辅助，不是判决：风险分 <5 的一律不写，无论总分多高。

---

## 版本控制与自动化

**本地 git 仓库**（2026-10-28 建立，`main` 分支）。改坏了能回滚，这是整个项目唯一的 undo。

| 事 | 怎么做 |
|---|---|
| 阶段留档 | 每个里程碑后提交：成稿、过 preflight、发草稿、发布 |
| 打标记 | 发草稿后 `git tag 选题3-draft`，群发后 `git tag 选题3-live` |
| 回滚 | `git log --oneline` 找点 → `git checkout <sha> -- <文件>`，别用 `reset --hard` |
| 不进仓库 | `配图/raw/`（9MB 源图）、`*_预览版.html`（1MB 生成物）、`cred*.json`（含密钥） |

**两个定时任务**（已建，勿重复创建）：

- **每日热搜选题筛选** 08:00：抓八平台热榜 → 剔除红线 → 与选题库去重 → `score` 实算 → 只把主推/备选追加进 `选题库.md`。够不上分就报 0 条，不硬凑。
- **公众号项目周体检** 周日 20:00：`doctor` + `selftest` + `assets --check` + `ledger --check`，列出未回填数据与未完成待办，自动提交 git，最后指定下周该写哪篇。

两个任务都只写 `选题库.md` 与 git，**不动稿件正文、不改台账数字**。数据回填仍然只能人工做（读不到公众号后台）。

---

## 硬约束速查

| 项 | 限制 |
|---|---|
| 标题 | 微信 ≤64 · **言序 ≤30** |
| 摘要 | 微信后台 ≤120 · **言序 compose ≤100**（`gzh.py yanxu` 按 100 硬拦，超了 exit 1） |
| 正文图 / 封面 | ≤1MB / ≤2MB |
| 配图水印 | 必须裁底 72px 去掉 |
| 拒稿红线 | 涉政 · 明星隐私 · 谣言 · 疗效断言 · 诱导分享 · 违规导流 |
| 原创声明 | 整篇搬运热搜/合集**不得标原创**；营销内容不得标原创 |

## 常见失误（本 Skill 存在的理由）

1. **没盘点已装 Skill 就手搓** → 白走 iframe 点不中的弯路
2. **忘了言序 30 字上限** → 32 字标题发不进去，得临时删字
3. **忘了去水印** → 发出去读者一眼看到"AI生成"
4. **图超 1MB** → 上传报 `ret:10001`
5. **对言序主题有期待** → 微信清洗样式，最后是素排版
6. **开留言忘了** → 整篇的评论钩子白写
7. **改了脚本不跑 selftest** → 规则静默失效，以为在查其实没查
8. **产物命名三套** → 代码写 `_final.jpg`、文档讲 `_clean.jpg`、手上是 `cover_clean.jpg`，rename 就翻车（已统一为 `_clean`，由 config 管）
9. **台账手写数字** → 标题字数、appmsgid 手抄错，台账与稿件打架（改用 `ledger --add/--check`）
10. **只改本地不刷库** → ima 里还是旧版标题，检索时两套说法（同名 `REPLACE` 刷新）
11. **分数只在终端飘一眼** → 27 条选题挑哪条靠眼缘，第二天问"上次那条多少分"没人记得（`score --save` 落到选题库）
12. **发完就忘回填** → 数据不回，下一篇还是拍脑袋（`ledger --audit`，doctor 与周体检自动催）
