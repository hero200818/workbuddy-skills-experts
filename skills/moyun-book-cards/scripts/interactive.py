#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
interactive.py —— 读者互动套件（墨韵拆书卡 v1.6.0）

让读者从"看完就走"变成"参与选题"：
  - 投票卡（1080×1350）：「下期拆哪本？」三选一（候选默认取趋势库新晋书，
    无趋势数据则取当期书单之外的档案书）
  - 书评征集卡（1080×1350）：金句 + 话题引导，征集读者短评
  - 互动数据模板（interactive_data.json）：记录投票数/投稿数，喂给 feedback.py 反哺闭环

用法：
  python interactive.py <期目录> [--cands 书名A 书名B 书名C]
输出：期目录/vote_下期投票.jpg、ask_书评征集.jpg、interactive_data.json
"""
import os, sys, json, re, argparse
from PIL import Image, ImageDraw

import gen_cards_ios as G
from gen_extra import classical_bg, center, kai_sp, seal, INK, SUB, MUTE, RED

PAPER = (249, 243, 230)


def _card_bg():
    return classical_bg()


def _title_block(d, cx, y, main, sub):
    center(d, cx, y, sub, G.F(26, "fang"), MUTE); y += 56
    kai_sp(d, cx, y, main, G.F(64, "kai"), INK, sp=10); y += 92
    return y


def vote_card(cands, issue, out_path):
    img = _card_bg()
    d = ImageDraw.Draw(img)
    cx = G.W // 2
    y = _title_block(d, cx, 150, "下 期 拆 哪 本", f"{issue} · 读者说了算")
    d.line([(cx - 150, y + 4), (cx + 150, y + 4)], fill=RED, width=2)
    y += 60
    for i, t in enumerate(cands, 1):
        bh = 150
        d.rounded_rectangle([120, y, 960, y + bh], radius=20,
                            fill=PAPER + (235,), outline=RED + (150,), width=2)
        # 选项字母圆
        r = 34
        d.ellipse([160, y + bh/2 - r, 160 + 2*r, y + bh/2 + r], fill=RED)
        fL = G.F(40, "kai")
        L = chr(ord("A") + i - 1)
        d.text((160 + r - d.textlength(L, font=fL)/2, y + bh/2 - fL.size*0.66),
               L, font=fL, fill=(247, 240, 228))
        # 书名（可两行）
        tl = G.wrap(t, G.F(42, "kai"), 560)[:2]
        ty = y + (bh - len(tl)*56) // 2 + 4
        for ln in tl:
            d.text((260, ty), ln, font=G.F(42, "kai"), fill=INK)
            ty += 56
        y += bh + 34
    y += 8
    center(d, cx, y, "评论区留下你的选项，得票最高的下期深拆", G.F(27, "fang"), SUB)
    center(d, cx, 1262, "墨 韵 拆 书 · 墨 韵 拆 书", G.F(24, "fang"), MUTE)
    seal(img, d, G.W - 92, 122, "書", 78)
    img.convert("RGB").save(out_path, quality=92)
    print(f"  [vote] {os.path.basename(out_path)}  选项：{' / '.join(cands)}")


def ask_card(book, out_path):
    img = _card_bg()
    d = ImageDraw.Draw(img)
    cx = G.W // 2
    y = _title_block(d, cx, 150, "读 书 征 稿", "你的一句话，可能上墙")
    y += 20
    q = "“" + (book.get("quote") or "") + "”"
    for ln in G.wrap(q, G.F(40, "kai"), G.CW - 200):
        kai_sp(d, cx, y, ln, G.F(40, "kai"), INK, sp=4); y += 56
    y += 16
    center(d, cx, y, f"——《{book['title']}》{book['author']}", G.F(28, "fang"), SUB)
    y += 90
    d.rounded_rectangle([140, y, 940, y + 250], radius=18,
                        fill=PAPER + (235,), outline=RED + (140,), width=2)
    center(d, cx, y + 66, "被这本书击中的那一刻，你在哪、在读什么？", G.F(30, "fang"), INK)
    center(d, cx, y + 126, "评论区写下你的「一句话书评」", G.F(30, "fang"), INK)
    center(d, cx, y + 190, "下期拆书卡将摘录最动人的三条", G.F(27, "fang"), SUB)
    center(d, cx, 1262, "墨 韵 拆 书 · 墨 韵 拆 书", G.F(24, "fang"), MUTE)
    seal(img, d, G.W - 92, 122, "書", 78)
    img.convert("RGB").save(out_path, quality=92)
    print(f"  [ask] {os.path.basename(out_path)}  引导书：《{book['title']}》")


def _norm(t):
    return re.sub(r"[^\w\u4e00-\u9fff]", "", str(t))


def _shorten(t):
    """长全名 → 档案/趋势中的规范短名（投票卡 42pt 需短名）。"""
    ai = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive_index.json")
    if os.path.isfile(ai):
        idx = json.load(open(ai, encoding="utf-8"))
        nt = _norm(t)
        best = None
        for e in idx.get("books", {}).values():
            ne = _norm(e["title"])
            if ne and (ne == nt or ne in nt) and len(ne) < len(t):
                if best is None or len(e["title"]) > len(best):
                    best = e["title"]
        if best:
            return best
    return t


def pick_candidates(data, n=3):
    """候选：优先趋势库新晋书 → 档案高频书（排除当期）→ 当期书。"""
    books = [b["title"] for b in data["books"]]
    cands = []
    tp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trend_report.md")
    if os.path.isfile(tp):
        txt = open(tp, encoding="utf-8").read()
        cands += [_shorten(t) for t in re.findall(r"《([^》]+)》", txt.split("## 名次飙升")[0] + txt.split("## 新晋上榜")[-1])
                  if _shorten(t) not in books and _shorten(t) not in cands]
    ai = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive_index.json")
    if os.path.isfile(ai) and len(cands) < n:
        idx = json.load(open(ai, encoding="utf-8"))
        for e in sorted(idx.get("books", {}).values(), key=lambda x: -x.get("count", 0)):
            if e["title"] not in books and e["title"] not in cands:
                cands.append(e["title"])
            if len(cands) >= n:
                break
    for b in books:
        if len(cands) >= n:
            break
        cands.append(b)
    return cands[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--cands", nargs="*", help="投票候选书名（默认自动挑）")
    args = ap.parse_args()
    d = args.target if os.path.isdir(args.target) else os.path.dirname(os.path.abspath(args.target))
    data = json.load(open(os.path.join(d, "books.json"), encoding="utf-8"))
    issue = str(data.get("issue", ""))
    safe = issue.replace("/", "_").replace("\\", "_")

    cands = args.cands or pick_candidates(data)
    vote_card(cands, issue, os.path.join(d, "vote_下期投票.jpg"))
    ask_card(data["books"][0], os.path.join(d, "ask_书评征集.jpg"))

    tpl = {"issue": issue, "vote": {t: 0 for t in cands}, "comments": [],
           "note": "投票数/书评投稿录入后，可复制到 feedback.py 的数据 JSON 参与反哺"}
    json.dump(tpl, open(os.path.join(d, "interactive_data.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"✅ 互动套件完成 → {d}（含 interactive_data.json 模板）")


if __name__ == "__main__":
    main()
