# -*- coding: utf-8 -*-
"""微信图文号拆书卡片 · 中国古典淡雅风 (v4)
   - 封面与全部书卡统一为同一款中国古典淡雅风格，保持每期连续性
   - 宣纸暖米渐变 + 淡月 + 淡墨远山 + 双线册页边框 + 华文楷体/仿宋 + 朱砂印章
   - 书卡用每本主题单字小印（藏书印风），统一中见个性
   尺寸 1080x1350 (4:5)，可直接作为视频号/公众号图文配图上传。"""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# 期号 / 日期（可经命令行参数覆盖：python gen_cards_ios.py [books.json] [期号] [日期] [输出基目录]）
ISSUE = "第43周"
DATE  = "2026-10-22"
KIND  = "weekly"
SHORT = ISSUE
NOTE  = ""

W, H = 1080, 1350
MARGIN = 60
CW = W - 2 * MARGIN

FP_LIGHT = "C:/Windows/Fonts/msyhl.ttc"   # 细体
FP_REG   = "C:/Windows/Fonts/msyh.ttc"   # 常规
FP_BOLD  = "C:/Windows/Fonts/msyhbd.ttc" # 粗体
FP_KAI   = "C:/Windows/Fonts/STKAITI.TTF"   # 华文楷体（标题）
FP_FANG  = "C:/Windows/Fonts/STFANGSO.TTF"  # 华文仿宋（正文）
FP_SONG  = "C:/Windows/Fonts/simsun.ttc"    # 宋体（小字）

def F(size, style="reg"):
    p = {"light": FP_LIGHT, "reg": FP_REG, "bold": FP_BOLD,
         "kai": FP_KAI, "fang": FP_FANG, "song": FP_SONG}[style]
    return ImageFont.truetype(p, size)

# 字体加载容错（华文字体缺失时回退到系统楷体/仿宋/宋体）
def _font_ok(p):
    try:
        ImageFont.truetype(p, 12); return True
    except Exception:
        return False
if not _font_ok(FP_KAI):
    FP_KAI = "C:/Windows/Fonts/simkai.ttf"
if not _font_ok(FP_FANG):
    FP_FANG = "C:/Windows/Fonts/simfang.ttf"
if not _font_ok(FP_KAI):
    FP_KAI = FP_SONG
if not _font_ok(FP_FANG):
    FP_FANG = FP_SONG

# 文字色（玻璃面板上用深色，保证可读）
INK   = (28, 30, 38)
SUB   = (78, 82, 96)
MUTE  = (120, 124, 138)

# 中国古典淡雅风 文字色（封面与书卡统一）
INK_C  = (54, 46, 40)     # 主墨色
SUB_C  = (96, 86, 72)     # 次级
MUTE_C = (146, 132, 114)  # 辅助
RED    = (150, 42, 36)    # 朱砂

# ---------- 三种周期样式配置（周 / 月 / 年），统一中国古典淡雅风 ----------
KIND_CFG = {
    "weekly": {
        "header": "读 书 悦 己 · 全 网 畅 销 书 周 报",
        "title1": "全网畅销书", "title2": "拆书特辑",
        "show_date": True,
        "sub2": "{n} 本热销好书 · 深度拆解",
        "platform": "京东 · 当当 · 微信读书 · 得到 · 开卷 · 豆瓣 联合精选",
        "booklist_head": "— 本 期 书 目 —",
        "footer": "滑动查看更多 · 每周一更新",
        "cadence": "每周一更新",
    },
    "monthly": {
        "header": "读 书 悦 己 · 全 网 畅 销 书 月 报",
        "title1": "全网畅销书", "title2": "月度盘点",
        "show_date": False,
        "sub2": "{n} 本月精选 · 深度盘点",
        "platform": "综合各大平台畅销与口碑榜单 · 月度甄选",
        "booklist_head": "— 本 月 书 目 —",
        "footer": "滑动查看更多 · 每月初更新",
        "cadence": "每月初更新",
    },
    "annual": {
        "header": "读 书 悦 己 · 年 度 畅 销 书 榜",
        "title1": "年度畅销书", "title2": "年度书单",
        "show_date": False,
        "sub2": "{n} 全年精选 · 年度回顾",
        "platform": "综合各大平台畅销与口碑榜单 · 年度甄选",
        "booklist_head": "— 年 度 书 目 —",
        "footer": "滑动查看更多 · 每年初更新",
        "cadence": "每年初更新",
    },
}

CLOSING = "。，、；：！？）》」』”’"
def wrap(text, font, max_w):
    out = []
    for para in text.split("\n"):
        line = ""
        for ch in para:
            if font.getlength(line + ch) <= max_w or (ch in CLOSING and line):
                line += ch
            else:
                out.append(line); line = ch
        out.append(line)
    return out

# ---------- 背景：多档渐变（纯 PIL，无需 numpy） ----------
def _color_at(stops, t):
    if t <= stops[0][0]:
        return stops[0][1]
    if t >= stops[-1][0]:
        return stops[-1][1]
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        if p0 <= t <= p1:
            k = (t - p0) / (p1 - p0)
            return tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(len(c0)))
    return stops[-1][1]

def vgradient(w, h, stops):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        col = _color_at(stops, y / (h - 1))
        d.line([(0, y), (w, y)], fill=col)
    return img

def vgradient_rgba(size, stops):
    w, h = size
    img = Image.new("RGBA", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        col = _color_at(stops, y / (h - 1))
        d.line([(0, y), (w, y)], fill=col)
    return img

def add_blobs(base_rgba, blobs, blur=150):
    layer = Image.new("RGBA", base_rgba.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for (cx, cy, r, col) in blobs:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (150,))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(layer, base_rgba)

# ---------- 玻璃面板 ----------
def glass_panel(img, box, radius=44, base_a=46, sheen_top=175):
    x0, y0, x1, y1 = box
    # 投影
    s = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(s).rounded_rectangle([x0, y0 + 26, x1, y1 + 26], radius=radius, fill=(0, 0, 0, 95))
    s = s.filter(ImageFilter.GaussianBlur(40))
    img = Image.alpha_composite(s, img)
    # 玻璃底
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=radius, fill=(255, 255, 255, base_a))
    # 顶部高光（仅面板内）
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    sheen = vgradient_rgba(img.size, [(0, (255, 255, 255, sheen_top)),
                                      (0.34, (255, 255, 255, 36)),
                                      (1, (255, 255, 255, 0))])
    img = Image.composite(sheen, img, mask)
    # 细边框 + 顶部内高光
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=radius, outline=(255, 255, 255, 165), width=2)
    d.line([x0 + radius, y0 + 3, x1 - radius, y0 + 3], fill=(255, 255, 255, 200), width=2)
    # 均匀微提亮（仅面板内），强化通透玻璃感
    lift = vgradient_rgba(img.size, [(0, (255, 255, 255, 14)), (1, (255, 255, 255, 14))])
    img = Image.composite(lift, img, mask)
    return img

def text_shadow(img, xy, text, font, fill, sh=(0, 0, 0, 110)):
    d = ImageDraw.Draw(img)
    d.text((xy[0] + 2, xy[1] + 2), text, font=font, fill=sh)
    d.text(xy, text, font=font, fill=fill)

# ---------- 主题（已统一中国古典淡雅风，以下 iOS 玻璃配色暂未使用，保留备查） ----------
# 每套：bg 渐变 stops, blobs 光晕, accent 强调色
THEMES = [
    # 0 封面
    {"bg": [(0, (49, 46, 129)), (0.55, (124, 58, 237)), (1, (219, 39, 119))],
     "blobs": [(180, 240, 360, (236, 72, 153)), (980, 500, 320, (56, 189, 248)), (560, 1180, 380, (167, 139, 250))],
     "accent": (236, 72, 153)},
    # 1 明朝那些事儿（琥珀黄）
    {"bg": [(0, (255, 209, 102)), (0.55, (255, 179, 71)), (1, (251, 133, 0))],
     "blobs": [(170, 230, 320, (255, 241, 118)), (950, 520, 300, (255, 159, 28)), (520, 1180, 360, (255, 122, 89))],
     "accent": (214, 107, 0)},
    # 2 三体（蓝青宇宙）
    {"bg": [(0, (37, 99, 235)), (0.55, (14, 165, 233)), (1, (6, 182, 212))],
     "blobs": [(180, 250, 340, (125, 211, 252)), (960, 540, 320, (56, 189, 248)), (540, 1170, 380, (99, 102, 241))],
     "accent": (3, 105, 161)},
    # 3 平凡的世界（翡翠绿）
    {"bg": [(0, (16, 185, 129)), (0.55, (52, 211, 153)), (1, (110, 231, 183))],
     "blobs": [(170, 240, 330, (187, 247, 208)), (970, 520, 300, (16, 185, 129)), (540, 1180, 360, (5, 150, 105))],
     "accent": (4, 120, 87)},
    # 4 长安的荔枝（番茄红）
    {"bg": [(0, (239, 68, 68)), (0.55, (244, 63, 94)), (1, (225, 29, 72))],
     "blobs": [(180, 250, 330, (253, 164, 175)), (960, 530, 310, (244, 63, 94)), (540, 1170, 360, (190, 18, 60))],
     "accent": (190, 18, 60)},
    # 5 遥远的救世主（紫罗兰）
    {"bg": [(0, (139, 92, 246)), (0.55, (168, 85, 247)), (1, (192, 132, 252))],
     "blobs": [(170, 240, 330, (216, 180, 254)), (970, 530, 310, (139, 92, 246)), (540, 1180, 360, (124, 58, 237))],
     "accent": (124, 58, 237)},
    # 6 活着（玫红）
    {"bg": [(0, (236, 72, 153)), (0.55, (244, 114, 182)), (1, (219, 39, 119))],
     "blobs": [(180, 250, 330, (249, 168, 212)), (960, 530, 310, (236, 72, 153)), (540, 1170, 360, (190, 24, 93))],
     "accent": (190, 24, 93)},
    # 7 第一性原理（靛蓝）
    {"bg": [(0, (79, 70, 229)), (0.55, (99, 102, 241)), (1, (129, 140, 248))],
     "blobs": [(170, 240, 330, (199, 210, 254)), (970, 530, 310, (79, 70, 229)), (540, 1180, 360, (67, 56, 202))],
     "accent": (67, 56, 202)},
    # 8 蛤蟆先生（青绿）
    {"bg": [(0, (20, 184, 166)), (0.55, (45, 212, 191)), (1, (94, 234, 212))],
     "blobs": [(180, 250, 330, (153, 246, 228)), (960, 530, 310, (20, 184, 166)), (540, 1170, 360, (13, 148, 136))],
     "accent": (13, 148, 136)},
]

def new_bg(theme):
    base = vgradient(W, H, theme["bg"]).convert("RGBA")
    return add_blobs(base, theme["blobs"])

# ---------- 书籍数据 ----------
books = [
    {"title":"明朝那些事儿", "file":"明朝那些事儿", "author":"当年明月", "cat":"历史 · 通俗",
     "rec":"把明朝三百年，写成你舍不得放下的“故事会”。",
     "points":["用“人话”讲历史：把帝王将相还原成有脾气的普通人，权谋、党争、人性一目了然。",
               "暗线清晰：从朱元璋到崇祯，一条“制度如何走向僵化”的主线贯穿，读史即读组织。",
               "可迁移的史观：历史没有如果，但能帮你理解“当下为何如此”。"],
     "quote":"成功只有一个——按照自己的方式，去度过人生。",
     "who":"想轻松入门明史、喜欢在故事里看清人性与权谋的读者。"},

    {"title":"三体（全集）", "file":"三体", "author":"刘慈欣", "cat":"科幻 · 史诗",
     "rec":"一部把“人类在宇宙中的位置”写到脊背发凉的硬科幻。",
     "points":["宇宙社会学两条公理：生存是文明第一需要；物质总量不变——推导出“黑暗森林”。",
               "降维打击思维：高级文明用跨维度方式碾压，对应现实的“跨维度竞争”。",
               "给理性的敬畏：在宏大尺度下，道德与情感需要被重新校准。"],
     "quote":"弱小和无知不是生存的障碍，傲慢才是。",
     "who":"喜欢硬科幻、想训练宏大系统思维的读者。"},

    {"title":"平凡的世界", "file":"平凡的世界", "author":"路遥", "cat":"文学 · 现实",
     "rec":"普通人在时代洪流里，靠双手挣出尊严的奋斗之书。",
     "points":["双线叙事：孙少安（扎根土地办实业）与孙少平（走出去求精神）代表两种活法。",
               "苦难观：苦难不是勋章，而是被认真对待后的成长燃料。",
               "情感与责任：亲情、爱情、乡情在贫困中的真实重量。"],
     "quote":"生活不能等待别人来安排，要自己去争取和奋斗。",
     "who":"正在迷茫、需要被“普通人的韧性”鼓舞的年轻人。"},

    {"title":"长安的荔枝", "file":"长安的荔枝", "author":"马伯庸", "cat":"历史 · 小说",
     "rec":"一颗荔枝，写尽大唐基层小吏的生存“算术”。",
     "points":["“项目制”视角：把“贵妃想吃荔枝”拆成物流、成本、人脉的真实项目管理。",
               "体制内小人物的算计与良知：在规则夹缝里既要办成事，又要守住人。",
               "历史细节的想象力：用一滴水，照见盛唐的奢靡与危机。"],
     "quote":"就算失败，我也想知道，自己倒在距离终点多远的地方。",
     "who":"职场人、项目管理者，爱看“小人物撬动大系统”的故事。"},

    {"title":"遥远的救世主", "file":"遥远的救世主", "author":"豆豆", "cat":"商战 · 哲学",
     "rec":"一部把“文化属性”讲透的认知与商战奇书。",
     "points":["文化属性论：强势文化造就强者，弱势文化期待救主——命运藏在认知底层。",
               "“见路不走”：不盲从经验与潮流，只依客观条件做判断。",
               "杀富济贫的伦理之问：救赎究竟靠别人，还是靠自己。"],
     "quote":"所谓真经，就是能够达到寂空涅槃的究竟法门，可悟不可修。",
     "who":"想升级认知框架、思考商业与人性的读者。"},

    {"title":"活着", "file":"活着", "author":"余华", "cat":"文学 · 经典",
     "rec":"用最平静的笔，写最沉重的“为活着而活着”。",
     "points":["福贵的一生：从纨绔到孤身一人，苦难接踵却始终向前。",
               "活着本身即是意义：不是为外在目标，而是生命韧性的本能。",
               "叙述的克制：越不煽情，越让人鼻酸。"],
     "quote":"人是为活着本身而活着，而不是为了活着之外的任何事物而活着。",
     "who":"经历低谷、想重新理解“坚持”二字的人。"},

    {"title":"第一性原理", "file":"第一性原理", "author":"武从文", "cat":"成长 · 思维",
     "rec":"教普通人回到本质，把复杂问题想明白的决策手册。",
     "points":["拆解“第一性原理”：从特斯拉/马斯克案例讲清“回归最底层事实再推演”。",
               "对抗思维惯性：别被类比和经验绑架，先问“这事的真前提是什么”。",
               "可落地的思考清单：遇到难题时的五步拆解框架。"],
     "quote":"回到本质，答案往往比想象中简单。",
     "who":"做决策、带团队、想摆脱“凭感觉”的实干者。"},

    {"title":"蛤蟆先生去看心理医生", "file":"蛤蟆先生", "author":"罗伯特·戴博德", "cat":"心理 · 入门",
     "rec":"用童话外壳，讲透心理咨询与自我和解的入门书。",
     "points":["三种自我状态：儿童/父母/成人，关系困局多源于状态错位。",
               "人生坐标：你对自己和世界的看法，决定了你的剧本。",
               "情绪是信使：不逃避抑郁，而是借它看见真实需求。"],
     "quote":"没有一种批判比自我批判更强烈，也没有一个法官比自己更严苛。",
     "who":"想读懂情绪、改善关系、开始自我觉察的读者。"},
]

# ---------- 命令行输入：books.json 优先，否则用内置 books ----------
def _load_input():
    global ISSUE, DATE, books, KIND, SHORT, NOTE
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = json.load(f)
        ISSUE = data.get("issue", ISSUE)
        DATE  = data.get("date", DATE)
        KIND  = data.get("kind", "weekly")
        SHORT = data.get("short", ISSUE)
        NOTE  = data.get("note", "")
        books = data["books"]
        print(f"  已载入 books.json：{len(books)} 本，期号 {ISSUE}，类型 {KIND}")
    else:
        if len(sys.argv) > 2:
            ISSUE = sys.argv[2]
        if len(sys.argv) > 3:
            DATE = sys.argv[3]
        KIND = "weekly"
        SHORT = ISSUE
        NOTE = ""

_load_input()

# 输出基目录：第 4 个参数指定则用它，否则落到统一归档根 畅销书拆书卡
if len(sys.argv) > 4:
    BASE = sys.argv[4]
else:
    BASE = r"C:\Users\Administrator\WorkBuddy\畅销书拆书卡"
OUT = os.path.join(BASE, ISSUE)
os.makedirs(OUT, exist_ok=True)

# ---------- 渲染：书卡（中国古典淡雅风 · 与封面完全统一） ----------
def _draw_seal(d, x, y, ch, size=80):
    """朱砂藏书小印（统一古典印风）。"""
    d.rounded_rectangle([x, y, x + size, y + size], radius=10, fill=RED)
    _draw_center(d, x + size / 2, y + size / 2 - 24, ch, F(50, "kai"), (250, 240, 230))

def card_book(book, idx, total):
    img, d = classical_bg()
    cx = W // 2
    cfg = KIND_CFG[KIND]
    x = 110                       # 左对齐基线
    cw_text = CW - 100            # 文本可用宽

    # 报头
    _draw_center(d, cx, 100, "读 书 悦 己 · 拆 书 特 辑", F(27, "fang"), MUTE_C)
    d.line([cx - 250, 140, cx - 150, 140], fill=RED, width=2)
    d.line([cx + 150, 140, cx + 250, 140], fill=RED, width=2)

    # 书名（楷体，自动换行居中，字号加大更醒目）
    y = 188
    tlines = wrap(book["title"], F(70, "kai"), CW - 110)
    for ln in tlines:
        _draw_kai(d, cx, y, ln, F(70, "kai"), INK_C, sp=16); y += 84
    y += 22
    # 作者
    _draw_center(d, cx, y, f"著 · {book['author']}", F(32, "fang"), SUB_C); y += 52
    # 分类（朱色）
    _draw_center(d, cx, y, book["cat"], F(30, "fang"), RED); y += 50

    # 一句话推荐（引文，朱线夹持，居中）
    rl = wrap(book["rec"], F(30, "fang"), CW - 150)
    y += 6
    d.line([cx - 120, y, cx + 120, y], fill=RED, width=1); y += 18
    for ln in rl:
        _draw_center(d, cx, y, ln, F(30, "fang"), SUB_C); y += 44
    y += 8
    d.line([cx - 120, y, cx + 120, y], fill=RED, width=1); y += 28

    # 拆书亮点（左对齐，朱色序号 + 墨色正文）
    _draw_center(d, cx, y, "拆 书 亮 点", F(36, "kai"), RED); y += 56
    body = F(29, "fang")
    nums = ["一", "二", "三"]
    indent = d.textlength("一、", font=body)
    for i, pt in enumerate(book["points"]):
        d.text((x, y), f"{nums[i]}、", font=body, fill=RED)
        pl = wrap(pt, body, cw_text - indent)
        for ln in pl:
            d.text((x + indent, y), ln, font=body, fill=INK_C); y += 44
        y += 14

    # 金句（题跋式，朱线夹持，居中楷体）
    y += 8
    d.line([cx - 100, y, cx + 100, y], fill=RED, width=1); y += 16
    ql = wrap("“" + book["quote"] + "”", F(33, "kai"), CW - 150)
    for ln in ql:
        _draw_center(d, cx, y, ln, F(33, "kai"), INK_C); y += 48
    y += 16
    d.line([cx - 100, y, cx + 100, y], fill=RED, width=1); y += 28

    # 适合谁读（左对齐）
    who_f = F(29, "fang")
    wl = d.textlength("适读 · ", font=who_f)
    d.text((x, y), "适读 · ", font=who_f, fill=RED)
    wpl = wrap(book["who"], who_f, cw_text - wl)
    for ln in wpl:
        d.text((x + wl, y), ln, font=who_f, fill=SUB_C); y += 42

    # 右下角藏书小印（与封面统一用「書」）
    seal = 80
    sx = W - 58 - 28 - seal
    sy = H - 58 - 28 - seal
    _draw_seal(d, sx, sy, "書", seal)

    # 页脚
    d.line([cx - 160, H - 150, cx + 160, H - 150], fill=RED, width=1)
    _draw_center(d, cx, H - 132, cfg["footer"], F(25, "fang"), MUTE_C)

    img.convert("RGB").save(os.path.join(OUT, f"{idx:02d}_{book['file']}.jpg"), quality=92)
    print(f"  [{idx:02d}] {book['title']} 末笔 y={y} (底限 {H-170})")
    return img

# ---------- 渲染：封面（中国古典淡雅风 · 固定样式，保持每期连续） ----------
def _ink_ridge(img, color, alpha, top, blur):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(layer)
    dd.polygon(top + [(W, H), (0, H)], fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(layer, img)

def _draw_kai(d, cx, y, text, font, fill, sp=12):
    ws = [d.textlength(ch, font=font) for ch in text]
    total = sum(ws) + sp * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, ws):
        d.text((x, y), ch, font=font, fill=fill)
        x += w + sp

def _draw_center(d, cx, y, text, font, fill):
    w = d.textlength(text, font=font)
    d.text((cx - w / 2, y), text, font=font, fill=fill)

# ---------- 古典淡雅背景（封面/书卡共用，保证风格完全统一） ----------
def classical_bg():
    img = vgradient(W, H, [(0, (248, 242, 228)), (0.5, (243, 234, 214)), (1, (231, 220, 195))]).convert("RGBA")
    d = ImageDraw.Draw(img)
    # 淡月
    d.ellipse([W - 270, 140, W - 50, 360], fill=(252, 248, 238, 150))
    # 远山近山（淡墨）
    img = _ink_ridge(img, (120, 124, 128), 40,
                     [(0, 1080), (200, 1020), (380, 1075), (560, 1000), (760, 1085), (960, 1010), (1080, 1075)], 16)
    img = _ink_ridge(img, (66, 72, 78), 60,
                     [(0, 1242), (160, 1150), (360, 1245), (540, 1120), (740, 1240), (920, 1145), (1080, 1230)], 22)
    d = ImageDraw.Draw(img)
    # 双线册页边框
    d.rounded_rectangle([46, 46, W - 46, H - 46], radius=10, outline=(110, 100, 86, 200), width=2)
    d.rounded_rectangle([58, 58, W - 58, H - 58], radius=8, outline=(150, 42, 36, 150), width=1)
    return img, d

def card_cover(total):
    # 宣纸暖米色渐变
    img = vgradient(W, H, [(0, (248, 242, 228)), (0.5, (243, 234, 214)), (1, (231, 220, 195))]).convert("RGBA")
    d = ImageDraw.Draw(img)
    # 淡月
    d.ellipse([W - 270, 140, W - 50, 360], fill=(252, 248, 238, 150))
    # 远山近山（淡墨）
    img = _ink_ridge(img, (120, 124, 128), 40,
                     [(0, 1080), (200, 1020), (380, 1075), (560, 1000), (760, 1085), (960, 1010), (1080, 1075)], 16)
    img = _ink_ridge(img, (66, 72, 78), 60,
                     [(0, 1242), (160, 1150), (360, 1245), (540, 1120), (740, 1240), (920, 1145), (1080, 1230)], 22)
    d = ImageDraw.Draw(img)

    # 双线册页边框
    d.rounded_rectangle([46, 46, W - 46, H - 46], radius=10, outline=(110, 100, 86, 200), width=2)
    d.rounded_rectangle([58, 58, W - 58, H - 58], radius=8, outline=(150, 42, 36, 150), width=1)

    cfg = KIND_CFG[KIND]
    cx = W // 2

    # 报头
    _draw_center(d, cx, 92, cfg["header"], F(26, "fang"), MUTE_C)
    d.line([cx - 250, 132, cx - 150, 132], fill=RED, width=2)
    d.line([cx + 150, 132, cx + 250, 132], fill=RED, width=2)

    # 标题（楷体，两行，字距舒展）
    _draw_kai(d, cx, 196, cfg["title1"], F(78, "kai"), INK_C, sp=16)
    _draw_kai(d, cx, 300, cfg["title2"], F(78, "kai"), INK_C, sp=16)

    # 朱砂印章
    seal = 96
    sx, sy = cx - seal / 2, 416
    d.rounded_rectangle([sx, sy, sx + seal, sy + seal], radius=12, fill=RED)
    _draw_center(d, cx, sy + seal / 2 - 34, "書", F(60, "kai"), (250, 240, 230))

    # 副标题
    sub1 = f"{ISSUE} · {DATE}" if cfg["show_date"] else ISSUE
    _draw_center(d, cx, 556, sub1, F(32, "fang"), SUB_C)
    _draw_center(d, cx, 602, cfg["sub2"].format(n=total), F(30, "fang"), SUB_C)
    _draw_center(d, cx, 648, cfg["platform"], F(22, "fang"), MUTE_C)

    # 本期书目（自动取前 8 本，用短名 file 展示；超出则标注“等共 n 本”）
    _draw_center(d, cx, 726, cfg["booklist_head"], F(28, "fang"), RED)
    titles = [b.get("file", b["title"]) for b in books][:8]
    lx0, lx1 = 150, W - 150
    inner = lx1 - lx0
    gap = 70
    colw = (inner - gap) / 2
    c0 = lx0 + colw / 2
    c1 = lx0 + colw + gap + colw / 2
    gy = 780
    rh = 66
    for r in range(4):
        ry = gy + r * rh
        has = (r * 2) < len(titles)
        if r > 0 and has:
            d.line([lx0, ry - 14, lx1, ry - 14], fill=(150, 140, 122, 140), width=1)
        if not has:
            break
        for col, center in enumerate((c0, c1)):
            idx = r * 2 + col
            if idx >= len(titles):
                break
            t = titles[idx]
            _draw_center(d, center, ry, t, F(29, "fang"), INK_C)
    if total > 8:
        _draw_center(d, cx, gy + 4 * rh, f"…等共 {total} 本好书", F(26, "fang"), MUTE_C)

    # 页脚
    d.line([cx - 160, H - 150, cx + 160, H - 150], fill=RED, width=1)
    _draw_center(d, cx, H - 132, cfg["footer"], F(24, "fang"), MUTE_C)

    img.convert("RGB").save(os.path.join(OUT, "00_封面.jpg"), quality=92)
    return img

total = len(books)
# 视频号图文上限 9 张：封面 + 最多 8 张书卡（多出部分仅在封面标注“等共 n 本”）
planned = ["00_封面.jpg"] + [f"{i:02d}_{b.get('file', b['title'])}.jpg" for i, b in enumerate(books[:8], 1)]
# 清理本次不会生成的旧图，避免上一期多本书残留
for fn in os.listdir(OUT):
    if fn.lower().endswith(".jpg") and fn not in planned:
        try: os.remove(os.path.join(OUT, fn))
        except OSError: pass
card_cover(total)
for i, b in enumerate(books[:8], start=1):
    card_book(b, i, total)
# 存档本期书单到输出目录，便于以后单独重跑某一期
import json as _json
_meta = {"issue": ISSUE, "date": DATE, "kind": KIND, "short": SHORT, "note": NOTE, "books": books}
with open(os.path.join(OUT, "books.json"), "w", encoding="utf-8") as _f:
    _json.dump(_meta, _f, ensure_ascii=False, indent=2)
print("OK images:", len(planned), "->", OUT, "| books.json 已存档")

# ---------- 自动生成发布文案（标题 ≤20 字，符合微信图文号限制，随周期自适应） ----------
def write_publish_md(books, issue, date, out_dir, kind="weekly", note=""):
    n = len(books)
    cfg = KIND_CFG[kind]
    cadence = cfg["cadence"]
    when = {"weekly": "本周", "monthly": "本月", "annual": "年度"}[kind]
    L = []
    L.append(f"# 全网畅销书 · 拆书特辑（{issue}）· 中国古典淡雅风图文号发布包\n")
    if note:
        L.append(f"> ⚠️ 备注：{note}\n")
    L.append("> 图片顺序（按此上传，共 9 张，视频号图文上限正好 9 张）：")
    L.append("> 00_封面 → " + " → ".join(f"{i:02d}_{b.get('file', b['title'])}" for i, b in enumerate(books[:8], 1)))
    L.append("> 风格：中国古典淡雅风，宣纸米色 + 华文楷体/仿宋 + 朱砂印章 + 淡墨远山 + 双线册页边框，封面与书卡统一一套样式。\n")
    L.append("## 一、发布标题（三选一，均 ≤20 字，符合微信图文号标题限制）")
    L.append(f"1. {issue}｜{n}本热销书拆读")
    L.append(f"2. {n}本好书，一张卡拆透")
    L.append(f"3. {when}热销{n}本，拆给你看\n")
    L.append("## 二、发布描述（可直接粘贴）")
    L.append(f"📚 {issue}全网畅销书拆书特辑来了！\n")
    L.append(f"本期综合各大平台最新榜单，挑出{n}本最热的书，一本一张中国古典淡雅风拆书卡：核心亮点×3、作者金句×1、适合谁读×1，滑动9张图3分钟读完👇\n")
    L.append("📖 本期拆解：")
    for b in books[:8]:
        L.append(f"《{b['title']}》——{b.get('rec','')}")
    L.append("")
    L.append(f"✅ 想先读哪本？评论区告诉我，下期拆给你看。")
    L.append(f"👉 关注我，{cadence}全网畅销书拆书。\n")
    tags = " ".join(["#拆书", "#畅销书", "#书单推荐"] + [f"#{b['title']}" for b in books[:3]])
    L.append(tags + "\n")
    L.append("## 三、每张卡片文字（便于改字复用）")
    L.append(f"封面：全网畅销书 · 拆书特辑 ｜ {issue} ｜ {n}本热销好书 · 深度拆解")
    for i, b in enumerate(books[:8], 1):
        L.append(f"{i:02d}《{b['title']}》{b['author']}｜{b['cat']}｜一句话：{b['rec']}｜金句：{b['quote']}")
    path = os.path.join(out_dir, "发布文案.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("  已生成发布文案：", path)

write_publish_md(books, ISSUE, DATE, OUT, KIND, NOTE)
