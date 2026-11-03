#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_mindmap.py —— 深度拆书 · 一图读懂（墨韵拆书卡 v1.5.0）

为一本书生成「思维导图卡」1080×1350：书名 → 主干 → 三大亮点支柱 → 金句带 → 适读。
配合 library 中的 long_review（800字深度书评）使用：卡片引流，长文留人。

用法：
  python gen_mindmap.py <期目录或books.json> [--book 书名|序号] [--all]
输出：mindmap_<书名>.jpg（存到期目录）
"""
import os, sys, json, re, argparse
from PIL import Image, ImageDraw

import gen_cards_ios as G
from gen_extra import classical_bg, center, kai_sp, seal, INK, SUB, MUTE, RED

PAPER = (249, 243, 230)


def make_mindmap(book, issue, out_path):
    img = classical_bg()
    d = ImageDraw.Draw(img)
    cx = G.W // 2
    y = 104
    center(d, cx, y, f"{issue} · 一图读懂", G.F(26, "fang"), MUTE); y += 66

    # 书名
    for ln in G.wrap(book["title"], G.F(64, "kai"), G.CW - 120):
        kai_sp(d, cx, y, ln, G.F(64, "kai"), INK, sp=10); y += 86
    center(d, cx, y + 4, f"{book['author']} · {book.get('cat','')}", G.F(28, "fang"), SUB)
    neck = y + 58

    # 主干竖线
    d.line([(cx, neck), (cx, 896)], fill=RED + (170,), width=3)

    # 三大亮点胶囊
    boxes = [452, 648, 844]
    for (i, p), by in zip(enumerate(book.get("points", []), 1), boxes):
        bw, bh = 800, 132
        bx0, by0 = cx - bw // 2, by
        d.rounded_rectangle([bx0, by0, bx0 + bw, by0 + bh], radius=18,
                            fill=PAPER + (235,), outline=RED + (140,), width=2)
        # 序号朱圆
        r = 24
        d.ellipse([bx0 + 28, by0 + bh/2 - r, bx0 + 28 + 2*r, by0 + bh/2 + r], fill=RED)
        fnum = G.F(26, "kai")
        d.text((bx0 + 28 + r - d.textlength(str(i), font=fnum)/2, by0 + bh/2 - fnum.size*0.66),
               str(i), font=fnum, fill=(247, 240, 228))
        # 文字
        tx = bx0 + 100
        ty = by0 + (bh - 2) // 2 - 34
        lines = G.wrap(p, G.F(29, "fang"), bw - 150)[:2]
        if len(lines) == 1:
            ty = by0 + bh/2 - 20
        for ln in lines:
            d.text((tx, ty), ln, font=G.F(29, "fang"), fill=INK)
            ty += 42

    # 金句带
    qy = 1010
    d.rounded_rectangle([100, qy, 980, qy + 150], radius=16,
                        outline=RED + (150,), width=2)
    q = "“" + book.get("quote", "") + "”"
    qy2 = qy + 30
    for ln in G.wrap(q, G.F(34, "kai"), 800)[:3]:
        kai_sp(d, cx, qy2, ln, G.F(34, "kai"), INK, sp=2); qy2 += 46
    # 适读
    for ln in G.wrap("适读：" + book.get("who", ""), G.F(27, "fang"), G.CW - 200):
        center(d, cx, 1200, ln, G.F(27, "fang"), MUTE)
    center(d, cx, 1268, "深读长文见公众号 · 墨 韵 拆 书", G.F(24, "fang"), SUB)
    seal(img, d, G.W - 92, 120, "書", 80)
    img.convert("RGB").save(out_path, quality=92)
    print(f"  [mindmap] {os.path.basename(out_path)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--book")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    d = args.target if os.path.isdir(args.target) else os.path.dirname(os.path.abspath(args.target))
    data = json.load(open(os.path.join(d, "books.json"), encoding="utf-8"))
    books, issue = data["books"], data.get("issue", "")
    sel = books
    if args.book:
        sel = ([books[int(args.book)-1]] if str(args.book).isdigit()
               else [b for b in books if args.book in b["title"]] or books[:1])
    elif not args.all:
        sel = []
    for b in sel:
        safe = re.sub(r'[\\/:*?"<>|]', "_", b.get("file") or b["title"])
        make_mindmap(b, issue, os.path.join(d, f"mindmap_{safe}.jpg"))
    print("✅ 思维导图卡完成")


if __name__ == "__main__":
    main()
