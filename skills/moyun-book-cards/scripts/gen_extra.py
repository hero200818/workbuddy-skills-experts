#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_extra.py —— 版式扩展（墨韵拆书卡 v1.5.0）

在九宫格（1080×1350）之外，为每期成品补齐三套新媒体版式：
  - cover  公众号封面大图 1080×460（2.35:1，"读读书悦悦己"发文头图）
  - poster 单书推文海报    1080×1440（金句主视觉，适合单本深度推书）
  - square 方形朋友圈卡    1080×1080（轻量种草卡）

复用 gen_cards_ios 的中国古典淡雅风背景/字体/配色，风格与九宫格完全统一。
输出到期目录下（文件名不以数字开头，不会混入九宫格上传清单）。

用法：
  python gen_extra.py <期目录>                     # 只出封面
  python gen_extra.py <期目录> --book 长安的荔枝    # 封面 + 该书海报/方形卡
  python gen_extra.py <期目录> --all               # 封面 + 全部书海报/方形卡
"""
import os, sys, json, re, argparse
from PIL import Image, ImageDraw, ImageFilter

import gen_cards_ios as G   # 复用 vgradient / F / 颜色常量 / wrap

INK, SUB, MUTE, RED = G.INK_C, G.SUB_C, G.MUTE_C, G.RED


# ---------- 背景自足实现（与生成器 classical_bg 同款视觉） ----------
def _ink_ridge(img, color, alpha, top, blur):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(layer)
    dd.polygon(top + [(G.W, G.H), (0, G.H)], fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(layer, img)


def classical_bg(w=1080, h=1350, theme="classic"):
    try:
        from specials import THEMES
        th = THEMES.get(theme, THEMES["classic"])
        stops = th["stops"]
    except Exception:
        stops = [(0, (248, 242, 228)), (0.5, (243, 234, 214)), (1, (231, 220, 195))]
    img = G.vgradient(w, h, stops).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.ellipse([w - 270, 140, w - 50, 360], fill=(252, 248, 238, 150))
    img = _ink_ridge(img, (120, 124, 128), 40,
                     [(0, h*0.8), (200, h*0.756), (380, h*0.796), (560, h*0.74),
                      (760, h*0.804), (960, h*0.748), (1080, h*0.796)], 16)
    img = _ink_ridge(img, (66, 72, 78), 60,
                     [(0, h*0.92), (160, h*0.852), (360, h*0.922), (540, h*0.83),
                      (740, h*0.919), (920, h*0.848), (1080, h*0.911)], 22)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([46, 46, w - 46, h - 46], radius=10,
                        outline=(110, 100, 86, 200), width=2)
    d.rounded_rectangle([58, 58, w - 58, h - 58], radius=8,
                        outline=(150, 42, 36, 150), width=1)
    return img


# ---------- 小助手（与生成器内嵌实现同款） ----------
def center(d, cx, y, text, font, fill):
    w = d.textlength(text, font=font)
    d.text((cx - w / 2, y), text, font=font, fill=fill)
    return font.size


def kai_sp(d, cx, y, text, font, fill, sp=12):
    ws = [d.textlength(ch, font=font) for ch in text]
    total = sum(ws) + sp * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, ws):
        d.text((x, y), ch, font=font, fill=fill)
        x += w + sp


def seal(img, d, cx, cy, ch="書", size=88):
    d.rounded_rectangle([cx - size/2, cy - size/2, cx + size/2, cy + size/2],
                        radius=10, fill=RED)
    f = G.F(int(size * 0.56), "kai")
    w = d.textlength(ch, font=f)
    d.text((cx - w/2, cy - f.size * 0.62), ch, font=f, fill=(247, 240, 228))


def bg_crop(h, top=0, theme="classic"):
    """从竖版背景裁出高 h 的横/方片段。"""
    bg = classical_bg(theme=theme)
    top = max(0, min(top, G.H - h))
    return bg.crop((0, top, G.W, top + h))


def short_names(books, n=5):
    names = [(b.get("file") or b["title"]) for b in books[:n]]
    more = " 等" if len(books) > n else ""
    return " · ".join(names) + more


# ---------- 1) 公众号封面 1080×460 ----------
def make_cover(books, issue, date, out_path, theme="classic"):
    img = bg_crop(460, top=300, theme=theme)          # 取中上段：淡月与远山之间
    d = ImageDraw.Draw(img)
    cx = G.W // 2
    center(d, cx, 74, issue, G.F(30, "fang"), MUTE)
    kai_sp(d, cx, 130, "全网畅销书 · 拆书特辑", G.F(60, "kai"), INK, sp=10)
    center(d, cx, 226, "——", G.F(26, "reg"), MUTE)
    center(d, cx, 262, f"{short_names(books, 5)}", G.F(28, "fang"), SUB)
    center(d, cx, 316, f"{len(books)} 本好书 · 一本一张拆书卡 · 滑动读完", G.F(24, "fang"), MUTE)
    seal(img, d, G.W - 96, 96, "書", 76)
    img.convert("RGB").save(out_path, quality=92)
    print(f"  [cover] {os.path.basename(out_path)}")


# ---------- 2) 单书海报 1080×1440 ----------
def make_poster(book, issue, out_path, theme="classic"):
    img = classical_bg(theme=theme).resize((1080, 1440))
    d = ImageDraw.Draw(img)
    cx = G.W // 2
    y = 128
    center(d, cx, y, f"{issue} · 单书深读", G.F(28, "fang"), MUTE); y += 92
    tl = G.wrap(book["title"], G.F(92, "kai"), G.CW - 80)
    for ln in tl:
        kai_sp(d, cx, y, ln, G.F(92, "kai"), INK, sp=14); y += 118
    y += 16
    center(d, cx, y, f"著 · {book['author']}", G.F(34, "fang"), SUB); y += 56
    center(d, cx, y, book.get("cat", ""), G.F(30, "fang"), RED); y += 84

    # 金句主视觉
    q = "“" + book.get("quote", "") + "”"
    for ln in G.wrap(q, G.F(42, "kai"), G.CW - 140):
        kai_sp(d, cx, y, ln, G.F(42, "kai"), INK, sp=4); y += 60
    d.line([(cx - 190, y + 10), (cx + 190, y + 10)], fill=RED, width=2)
    y += 66

    center(d, cx, y, "拆 书 亮 点", G.F(34, "kai"), RED); y += 66
    for i, p in enumerate(book.get("points", []), 1):
        for j, ln in enumerate(G.wrap(p, G.F(29, "fang"), G.CW - 220)):
            prefix = f"{i}  " if j == 0 else "    "
            w = d.textlength(prefix, font=G.F(29, "fang"))
            if j == 0:
                d.text((cx - (G.CW - 220) / 2, y), prefix, font=G.F(29, "fang"), fill=RED)
            d.text((cx - (G.CW - 220) / 2 + w, y), ln, font=G.F(29, "fang"), fill=SUB)
            y += 44
        y += 16
    y += 30
    for ln in G.wrap("适读：" + book.get("who", ""), G.F(28, "fang"), G.CW - 160):
        center(d, cx, y, ln, G.F(28, "fang"), MUTE); y += 42
    # 页脚：浅色底带压在远山上，保证可读
    d.rectangle([0, 1352, 1080, 1440], fill=(243, 234, 214))
    center(d, cx, 1368, "墨 韵 拆 书 · 墨 韵 拆 书", G.F(26, "fang"), SUB)
    seal(img, d, G.W - 96, 148, "書", 84)
    img.convert("RGB").save(out_path, quality=92)
    print(f"  [poster] {os.path.basename(out_path)}")


# ---------- 3) 方形朋友圈卡 1080×1080 ----------
def make_square(book, out_path, theme="classic"):
    img = bg_crop(1080, top=135, theme=theme)         # 居中裁方
    d = ImageDraw.Draw(img)
    cx = G.W // 2
    y = 250
    tl = G.wrap(book["title"], G.F(76, "kai"), G.CW - 120)
    for ln in tl:
        kai_sp(d, cx, y, ln, G.F(76, "kai"), INK, sp=10); y += 104
    y += 20
    center(d, cx, y, f"著 · {book['author']}", G.F(30, "fang"), SUB); y += 88
    for ln in G.wrap(book.get("rec", ""), G.F(31, "fang"), G.CW - 200):
        center(d, cx, y, ln, G.F(31, "fang"), SUB); y += 48
    y += 44
    q = "“" + book.get("quote", "") + "”"
    for ln in G.wrap(q, G.F(38, "kai"), G.CW - 180):
        kai_sp(d, cx, y, ln, G.F(38, "kai"), INK, sp=4); y += 56
    y += 40
    for ln in G.wrap("适读：" + book.get("who", ""), G.F(26, "fang"), G.CW - 220):
        center(d, cx, y, ln, G.F(26, "fang"), MUTE); y += 40
    center(d, cx, 972, "墨 韵 拆 书 · 墨 韵 拆 书", G.F(24, "fang"), SUB)
    seal(img, d, G.W - 92, 128, "書", 76)
    img.convert("RGB").save(out_path, quality=92)
    print(f"  [square] {os.path.basename(out_path)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="期目录或 books.json")
    ap.add_argument("--book", help="书名或序号（1-based）")
    ap.add_argument("--all", action="store_true", help="全部书出海报+方形卡")
    ap.add_argument("--theme", default="classic", help="限定配色: classic/festive/rose/spring/autumn")
    args = ap.parse_args()

    d = args.target if os.path.isdir(args.target) else os.path.dirname(os.path.abspath(args.target))
    data = json.load(open(os.path.join(d, "books.json"), encoding="utf-8"))
    books, issue = data["books"], data.get("issue", "")
    date = data.get("date", "")

    make_cover(books, issue, date, os.path.join(d, "cover_公众号封面.jpg"), args.theme)
    sel = books
    if args.book:
        if str(args.book).isdigit():
            sel = [books[int(args.book) - 1]]
        else:
            sel = [b for b in books if args.book in b["title"]] or books[:1]
    elif not args.all:
        sel = []
    for b in sel:
        safe = re.sub(r'[\\/:*?"<>|]', "_", b.get("file") or b["title"])
        make_poster(b, issue, os.path.join(d, f"poster_{safe}.jpg"), args.theme)
        make_square(b, os.path.join(d, f"square_{safe}.jpg"), args.theme)
    print(f"✅ 版式扩展完成 → {d}")


if __name__ == "__main__":
    main()
