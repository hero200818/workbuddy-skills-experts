---
name: moyun-book-cards
version: 1.8.1
display_name: 墨韵拆书卡·三端运营专家
display_name_en: MoYun Book Cards
description: 「墨韵拆书卡」把任意书单/畅销书周报一键生成微信图文号（视频号图文）可直接上传的中国古典淡雅风拆书卡片——9 张 1080x1350 竖版九宫格 + 可直接复制的发布文案。支持「真·自动抓取」模式（一条命令抓榜单→选书→出卡）、「月度/年度盘点」模式（聚合历史各期自动生成盘点书单出卡）与「多平台分发」模式（一键生成微信视频号/头条微头条/小红书三平台适配文案与素材清单）。当用户说"出拆书卡""做微信书单图文""把周报变卡片""做月度/年度盘点""生成分发文案""做九宫格书单"时使用。支持周报/月报/年报三种周期版式。
description_zh: 「墨韵拆书卡」把任意书单/畅销书周报一键生成微信图文号（视频号图文）可直接上传的中国古典淡雅风拆书卡片——9 张 1080x1350 竖版九宫格 + 可直接复制的发布文案。支持「真·自动抓取」模式（一条命令抓榜单→选书→出卡）、「月度/年度盘点」模式（聚合历史各期自动生成盘点书单出卡）与「多平台分发」模式（一键生成微信视频号/头条微头条/小红书三平台适配文案与素材清单）。当用户说"出拆书卡""做微信书单图文""把周报变卡片""做月度/年度盘点""生成分发文案""做九宫格书单"时使用。支持周报/月报/年报三种周期版式。
description_en: MoYun Book Cards turns any book list or weekly bestseller report into nine 1080x1350 Chinese classical elegant-style book-review cards ready to upload to WeChat Channels image posts, plus ready-to-paste publish copy. An "auto-fetch" mode runs one command that scrapes public bestseller charts and renders cards; a "retrospective" mode aggregates past issues into monthly/annual roundup card sets; and a "distribution" mode generates ready-to-paste copy for WeChat Channels, Toutiao and Xiaohongshu with a material checklist. Use when the user says "make book cards", "turn this report into cards", "create a monthly/annual roundup" or "generate distribution copy". Supports weekly, monthly and annual report layouts.
---

# 墨韵拆书卡 · 中国古典淡雅风拆书卡片生成器

把一份书单（或畅销书周报/月报/年报）一键变成 **微信图文号 / 视频号图文** 可直接上传的拆书卡片：

- 9 张竖版图（1080×1350，4:5），正好卡满视频号图文 9 张上限（封面 1 + 书卡 8）；
- **封面与全部书卡统一为同一款「中国古典淡雅风」**，风格连续、品牌统一：
  - 宣纸暖米色渐变 + 淡月 + 淡墨远山（双层）+ 双线册页边框（外墨内朱）；
  - 标题用**华文楷体**、正文用**华文仿宋**，朱砂红「書」藏书印点睛；
  - 封面与书卡共用同一 `classical_bg()`，视觉语言完全一致；
  - 效果见 `assets/sample_00_封面.jpg`（封面）与 `assets/sample_01_书卡.jpg`（书卡）。
- 每张书卡结构：书名（楷体大字）→ 著者/分类 → 一句话推荐（朱线夹持）→ 拆书亮点×3（朱色序号+墨色正文）→ 金句（题跋式）→ 适合谁读 → 页脚。
- 自动生成**发布文案.md**：3 个备选标题 + 可粘贴描述（含话题标签与互动引导）+ 逐卡文字备份。
- **微信图文号标题硬约束：发布标题必须 ≤20 字（中文/标点/数字均计 1 字）**，脚本已内置此规则。
- 三种周期版式：`weekly`（周报）/ `monthly`（月报）/ `annual`（年报），封面报头、书目栏与页脚自动切换。
- **极简书单 + 内容库**：只给书名+作者，AI 自动补全拆书文案并沉淀进 `library/` 内容库，生成一次、永久复用（`scripts/enrich.py`）。
- **月度/年度盘点**（`scripts/aggregate.py`）：自动扫描历史各期 `books.json`，按出现频次+近期热度聚合去重，一条命令生成盘点书单并出盘点卡（月报/年报版式自动切换）。
- **多平台分发**（`scripts/distribute.py`）：读任意一期成品，一键生成微信视频号/头条微头条/小红书三平台适配文案 + 素材清单与发布指引，输出到 `分发包/<期名>/`。
- **榜单趋势库**（`scripts/trend.py`）：把历期榜单沉淀成时间序列库，自动分析「新晋上榜 / 连续在榜 N 周 / 名次飙升」三类趋势亮点，可拼进发布文案，内容有差异化叙事。
- **自动质检**（`scripts/qc.py`）：标题与历史 40+ 期查重（品牌模板句智能识别）、广告法敏感词预检、长书名溢出预警，输出 qc_report.md。
- **版式扩展**（`scripts/gen_extra.py` + `scripts/gen_mindmap.py`）：公众号封面大图 1080×460、单书推文海报 1080×1440、方形朋友圈卡 1080×1080、深度拆书思维导图卡 1080×1350，风格与九宫格统一。
- **数据反馈闭环**（`scripts/feedback.py`）：录入各期阅读/点赞数据 → 自动聚合书目与类别权重 → parse_weekly 选书自动加成，用数据养选书。
- **拆书档案**（`scripts/archive.py`）：全期索引 + 档案总览，一句话查"拆过哪些书/某书出场几期/分类统计"。
- **全链路一条龙**（`scripts/run_all.py`）：抓榜→选书→补全→出卡→版式→分发→质检→趋势→档案 十环一条命令，配合定时任务实现每周全自动出版。
- **标题风格库 A/B**（`scripts/title_lab.py`）：五种风格（悬念/数字/情感/提问/热点）各生成 2-3 条 ≤20 字候选，带历史查重标记，根治模板复用。
- **口播视频脚本**（`scripts/speech_gen.py`）：一期文案自动转 1-2 分钟口播稿 + 分镜表（时间轴/口播词/画面卡片/拍摄提示），图文视频通吃。
- **主题特辑引擎**（`scripts/specials.py`）：内置选题日历（世界读书日/开学季等 8 个节点，±7 天自动命中），输出特辑策划案；`gen_extra.py --theme` 出限定配色封面（festive/rose/spring/autumn）。
- **读者互动套件**（`scripts/interactive.py`）：下期拆哪本投票卡（三选一自动挑候选）+ 书评征集卡 + 互动数据模板，读者参与选题。
- **成品审阅页**（`scripts/review_page.py`）：期目录 → review.html，九宫格画廊（点击放大）+ 三平台文案切换 + 一键复制 + 质检结论。
- **回归测试**（`scripts/test_suite.py`）：seed 模式断言全链路关键产物（出图/文案/质检/趋势/档案），改代码后跑一遍即知有没有改坏。
- **深度书评**：library 书目支持 `long_review` 字段（约 800 字深拆），配合 gen_mindmap 出思维导图卡实现"轻拆引流+深拆留人"；高频书已首批沉淀。

## 何时使用
- 用户有一份书单、畅销书周报/月报/年报，要变成可发布的图文号素材。
- 用户说"出拆书卡""做微信书单""把书单做成卡片""生成读书图文号九宫格"。
- 用户要求"封面/书卡统一风格""做成中国古典风/国风"。
- 用户说"做月度盘点""做年度书单""把这一年/这个月的卡片汇总成盘点"。
- 用户说"生成分发文案""发头条/小红书""多平台发布"。

## 执行步骤

### 1. 准备书单数据（七种模式）

**模式 -2（月度/年度盘点，v1.4.0 新增）：聚合历史各期自动生成盘点卡**

把历史上出过的各期卡片自动汇总成一份「月度盘点」或「年度盘点」：
```bash
python scripts/aggregate.py monthly                      # 近30天各期聚合 → 精选8本 → 月度盘点书单
python scripts/aggregate.py annual --year 2025           # 2025全年各期聚合 → 精选8本 → 年度盘点书单
python scripts/aggregate.py monthly --window 45 --top 6  # 自定义回看窗口与精选本数
```
- 自动扫描历史根目录（`畅销书拆书卡/`）下所有期的 `books.json`，按书名归一化去重；
- 打分 = 出现频次（跨期反复上榜的书优先）+ 最近出现日期（近期热度加权）；
- 自动跳过「盘点/demo/演示」类衍生期，避免盘点结果自我强化；
- 输出 `盘点_月度-YYYYMM.json` / `盘点_年度-YYYY.json`（`kind` 已自动设为 `monthly`/`annual`），直接喂 `gen_cards_ios.py` 出盘点卡；
- 受九宫格版式（封面+8书卡）约束，盘点默认精选 **8 本**，保证卡片与发布文案一致；
- 复用历史期已有的完整拆书数据，无需重新补全。

**模式 -1（真·零输入·自动抓取，终极致省力）：榜单抓取 → 周报 → 选书 → 出卡 一条龙**

连「周报 Markdown」都不用准备——脚本直接抓取公开榜单生成周报，再走模式 0 链路：
```bash
python scripts/auto_weekly.py --fetch            # 抓取豆瓣榜单→生成周报→选前8→出卡
python scripts/auto_weekly.py --fetch --seed     # 离线/限流时走内置真实种子榜单兜底
python scripts/auto_weekly.py --fetch 6          # 选前 6 本
```
抓取器 `scripts/fetch_bestsellers.py`：
- 主数据源 **豆瓣图书热门榜**（静态 HTML，用户本机直接 HTTP 抓取，无需登录）；
- 京东 / 当当 / 微信读书 为可扩展源框架（动态渲染或需登录，已在 `SOURCES` 中预留扩展点）；
- 抓取失败 / 限流 / 离线时，自动回退到内置 `seeds/` 真实快照，保证链路不崩；
- 输出标准「综合热度 TOP20」周报 Markdown，可直接喂 `parse_weekly.py`，与模式 0 无缝衔接。
- **价值：一个周末的完整拆书卡，从「找榜单 → 整理 → 出卡」压缩成一条命令。**

**模式 0（全自动·周报驱动，推荐给周期更新）：一键从周报选书出卡**

若你有一份「全网畅销书周报」Markdown（含「综合热度 TOP20」表格：排名|书名|作者|类别|一句话），可一条命令完成「解析 → 加权选前 8 → 内容库补全 → 出卡」：
```bash
python scripts/auto_weekly.py                 # 自动取最新周报，出第N周卡片
python scripts/auto_weekly.py 周报.md 8       # 指定周报 + 选前 N 本
python scripts/auto_weekly.py 周报.md 8 --no-gen   # 只出 books.json 不出图
```
内部链路：
1. `parse_weekly.py` 解析 TOP20 表格 → 过滤「三部曲/合集」类 → 加权打分（基础分=21−名次，同类递减惩罚保证多样）→ 贪心选前 8 → `lite_auto.json`；
2. `enrich.py` 查 `library/` 复用已有拆书文案；若遇库里没有的书，脚本退出并提示，由 AI 生成写回 `library/`，**重跑即可自动出卡**；
3. 包成 `<期号>_input.json` 喂给 `gen_cards_ios.py` 出图。
- 价值：**零手抄数据**，周报一变，卡片自动跟着变。

**模式 A-（最省力，推荐）：极简书单 + 内容库自动补全**

只有书名和作者也能出卡。新建 `lite.json`（UTF-8）：
```json
[
  {"title": "活着", "author": "余华"},
  {"title": "长安的荔枝", "author": "马伯庸"},
  {"title": "置身事内", "author": "兰小欢", "cat": "经管 · 经济"}
]
```
然后运行补全引擎：
```bash
python scripts/enrich.py lite.json books.full.json
```
工作方式：
- 引擎先查 `scripts/library/` 内容库（每本书一个 JSON，含 rec/points×3/quote/who 完整拆书数据），命中则直接复用（lite 里显式给的 author/cat 优先覆盖）；
- 未命中的书输出到 `books.full.json.missing.json`，由 AI（LLM）阅读生成完整拆书数据后写回 `library/<书名>.json`，下次再遇到同一本书就秒复用；
- 重跑 enrich 直到返回码 0（全部复用），再包一层 `{"issue":..., "date":..., "kind":..., "books": [...]}` 喂给生成器（同模式 A）；
- **价值：手写一本书的拆书文案要几分钟，库命中后零成本——内容库越用越厚，长期复用。**
- 命名建议：`title` 用大众熟知的短名（如「置身事内」而非全名），卡片 70pt 大字单行更美观；`file` 同理用更短别名（如「三体」）。
- （可选）维护 `used_in` 字段记录每本书被哪些期使用过，便于盘点。

**模式 A（支持自动化/批量）：传入完整 books.json**

新建 `books.json`（UTF-8），结构：
```json
{
  "issue": "第44周",
  "date": "2026-10-26",
  "kind": "weekly",
  "books": [
    {"title":"书名", "file":"短文件名(无空格,长书名用缩写)",
     "author":"作者", "cat":"分类 · 子类",
     "rec":"一句话推荐(≤30字)",
     "points":["亮点1(≤45字)","亮点2(≤45字)","亮点3(≤45字)"],
     "quote":"金句(≤40字)",
     "who":"适合谁读(≤30字)"}
  ]
}
```
字段说明：
- `kind` 决定封面/文案的周期样式，三选一：`weekly`（封面标"第XX周 · 日期"，页脚"每周一更新"）、`monthly`（issue 形如"2026年10月"，页脚"每月初更新"）、`annual`（issue 形如"2026年度"，页脚"每年初更新"）。不填默认 `weekly`。
- 建议每期 8 本书（封面 1 + 书卡 8 = 9 张满图）；生成器硬约束为前 8 本出卡、文案列前 8 本，`books` 超过 8 本的部分会被忽略——月度/年度盘点请用模式 -2 的 `--top` 控制在 8 本内。
- `file` 用作图片文件名与封面短名（如《蛤蟆先生去看心理医生》用 `file:"蛤蟆先生"`）。
- （可选）`note`：如"数据未更新，本期沿用上期书单"，会标注在发布文案顶部。

**模式 B（手动）：直接编辑脚本内置书单**

打开 `scripts/gen_cards_ios.py`，在标注 `# 书籍数据` 的 `books` 列表中按同样的字段模板填书，然后不带参数运行（输出到脚本目录下 `畅销书拆书卡/第43周/`）。

### 2. 运行生成器

需要 Python 3 + Pillow（`pip install Pillow`）。Windows 下若系统装有华文楷体/华文仿宋会优先使用，缺失自动回退 simkai/simfang/simsun。

```bash
# 模式 A：传 json + 期号 + 日期 + 输出基目录（按期号自动分子文件夹，不覆盖往期）
python scripts/gen_cards_ios.py books.json "第44周" "2026-10-26" "输出目录"
# 月度 / 年度：仅 json 里 kind 与 期号 不同
python scripts/gen_cards_ios.py books.json "2026年10月" "2026-10-31" "输出目录"
python scripts/gen_cards_ios.py books.json "2026年度" "2026-12-31" "输出目录"
```

脚本行为：
- 打印每本书"末笔 y"用于排查溢出（应 < 1180）；
- 输出前自动清理本期目录中不用的旧 jpg；
- 自动生成 `发布文案.md`（3 个 ≤20 字标题 + 可粘贴描述 + 逐卡文字，随 `kind` 自适应）。

### 3. 展示结果
把 9 张 jpg 连同 `发布文案.md` 一次性展示给用户，提示上传顺序：封面 → 01 → … → 08。

### 4. 多平台分发（v1.4.0 新增）
对任意已出卡的期，一键生成三平台适配文案：
```bash
python scripts/distribute.py "输出目录/<期名>"     # 期目录或其中的 books.json 均可
```
输出到 `分发包/<期名>/`：
- `01_微信视频号图文.md`：标题（≤20字）+描述+话题+9图上传顺序；
- `02_头条微头条.md`：口语化短文案+序号书单+互动钩子+配图建议；
- `03_小红书笔记.md`：emoji 标题+种草正文+标签组+3:4 配图建议；
- `00_素材清单与发布指引.md`：图片清单+三平台发布步骤 checklist。
- 文案按 `kind` 自动切换语气（本周/本月/这一年）；三平台口吻差异化（视频号书卷气、头条互动体、小红书种草体）。
- 说明：真实上传/粘贴在各平台客户端完成（每平台约 5 分钟），素材与文案已全部备齐，做到"一键复制即发布"。

### 5. 出版流水线工具箱（v1.5.0 新增）
```bash
python scripts/run_all.py --seed        # 十环一条龙：抓榜→选书→补全→出卡→版式→分发→质检→趋势→档案
python scripts/trend.py build           # 榜单趋势库：新晋/连续在榜/飙升 亮点分析
python scripts/qc.py "<期目录>"          # 发布前质检：标题查重+敏感词+溢出预警
python scripts/gen_extra.py "<期目录>" --book 书名   # 公众号封面+单书海报+方形卡
python scripts/gen_mindmap.py "<期目录>" --book 书名 # 一图读懂思维导图卡（配合 library long_review 深度书评）
python scripts/feedback.py record 期名 数据.json && python scripts/feedback.py weight  # 阅读数据→选书权重
python scripts/archive.py --query 活着   # 拆书档案检索
```
- 库外书深度书评：为 library 中书目补写 `long_review`（约800字）字段，配合 gen_mindmap 出深度卡；
- fetch_bestsellers 支持 `--multi` 多源加权融合（豆瓣/当当/微信读书，权重 1.0/0.9/0.8，多源同时上榜额外加成）。

## 数据真实性规范（v1.6.1 新增，强制）
所有数据按三层分级，禁止臆造：
1. **书名/作者**：必须来自真实榜单（豆瓣年度榜/当当畅销榜等）或真实出版物，每期 books.json 的 `source_note` 字段记录来源；
2. **推荐语/亮点/适读**：属评论范畴，须基于真实书籍信息撰写，不得虚构情节；
3. **金句（quote）**：必须标注 `quote_status`——`excerpt`（可证原文摘录，可公开引用）/ `paraphrase`（主旨转述，禁止冒充书中原句）。
审计工具：`scripts/audit_data.py`（`--fix` 自动补标注，输出 audit_report.md）。发布文案与审阅页自动附带真实性声明。新增书目的金句默认 paraphrase，仅凭公开流传版本可证原句时才标 excerpt。

## 三端全能运营专家（v1.8.0 新增）
系统内置三端平台规则知识库 `platforms.json`（微信视频号图文/头条微头条/小红书：字数限制、话题格式、配图规范、黄金发布时间、风格定位、违禁红线、互动策略、数据基准），并进化为**运营专家引擎** `scripts/expert.py`：
- `python expert.py 规范 微信|头条|小红书|all`——查询任一端运营规范；
- `python expert.py 适配 <期目录> --platform all`——按端深度适配：标题候选（字数+违禁预检）、话题策略、封面建议、互动钩子、数据基准，输出三端适配方案.md；
- `python expert.py 复盘 <期目录> --data 数据.json`——按端数据基准（微信看转发/头条看评论/小红书看收藏）给出改进建议；
- `python expert.py 排期`——三端一周发布排期建议。
分发器 distribute.py 同步规则化：三端文案自动附「平台规则速览」（黄金时间/硬规则/红线/互动/数据基准）。

## 自我进化系统（v1.7.0 新增）
系统具备「检测→修复→验证→记录→调度」自闭环能力：
- `scripts/doctor.py`：自诊断+自动修复（库字段补全/旧图清理/档案一致性/超长标题与重复条目预警），输出 doctor_report.md；
- `scripts/system_check.py`：一键健康检查中心（自诊断→真实性审计→回归测试→指标收集），输出 SYSTEM_REPORT.md + dashboard.html 仪表盘，并写入 evolution_log.md 进化日志；
- 自动化闭环：每周出版/每月盘点后自动执行 system_check --quick，生产与体检同步完成。

## 输出目录配置（上架通用）
- 所有脚本默认输出到**当前工作目录**下的 `畅销书拆书卡/`；可用环境变量 `MOYUN_CARD_ROOT` 指定任意输出目录；
- 包内不含任何个人路径与个人信息（已通过 audit_data.py 同源的痕迹扫描验证）。

## 设计约定（如需微调）
- 背景统一：`classical_bg()`（宣纸渐变 + 淡月 + 远山 + 双线框），改风格只动这一处，封面与书卡全局生效。
- 印章：`_draw_seal()` 朱砂「書」印；想换字（如「读」「悦」）改调用处参数即可。
- 字体：华文楷体 `STKAITI.TTF`、华文仿宋 `STFANGSO.TTF`；缺失自动回退 `simkai.ttf`/`simfang.ttf`/`simsun.ttc`。
- 文字色：主墨 `INK_C (54,46,40)`、次 `SUB_C`、辅 `MUTE_C`、朱砂 `RED (150,42,36)`，均为模块级常量。
- 尺寸：常量 `W,H = 1080,1350`；改尺寸需同步检查换行宽度 `CW`。

## 数据获取建议（可选）
若用户没有现成书单，可先通过网络搜索聚合各大平台（京东/当当/微信读书/开卷/豆瓣等）当期畅销榜单，综合筛选 8 本，补全各字段后再走模式 A。若当期数据全部抓取失败，可读取最近一期 `books.json` 改期号/日期并追加 `note`，照常出卡。
