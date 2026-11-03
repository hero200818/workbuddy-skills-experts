# -*- coding: utf-8 -*-
"""parse_weekly.py — 周报 Markdown → 自动解析 TOP20 → 加权打分 → 选前 8 → 出 lite 书单
用法：
  python parse_weekly.py                         # 自动取 cwd 下最新的 全网畅销书周报*.md
  python parse_weekly.py 周报.md                 # 指定周报
  python parse_weekly.py 周报.md out.json        # 指定输出（默认 lite_auto.json）
  python parse_weekly.py 周报.md out.json 6      # 选前 N 本（默认 8）

解析入口：周报里的「综合热度 TOP20」表格（列：排名 | 书名 | 作者 | 类别 | 一句话）。
打分模型（让选出来的 8 本既热又多样）：
  · 基础分 = 21 - 名次           （第1名20分，第20名1分）
  · 过滤合集类：标题含「三部曲/合集/精选集/套装」且已在榜上有单本的，直接剔除
  · 同类递减惩罚：贪心时同一类别第 k 本额外 -3*(k-1)，避免 8 本全是一个类别
  · 同分按原名次优先
输出：lite_auto.json（[{title, author, cat}]），可直接喂 enrich.py → gen_cards_ios.py
"""
import os, sys, re, json, glob

BASE = os.path.dirname(os.path.abspath(__file__))


def find_latest():
    fs = sorted(glob.glob(os.path.join(BASE, "全网畅销书周报*.md")), reverse=True)
    if not fs:
        raise FileNotFoundError("未找到 全网畅销书周报*.md，请显式传入路径")
    return fs[0]


def parse_top20(md_text):
    """从 markdown 中抽取「综合热度 TOP20」表格的表体行。"""
    lines = md_text.splitlines()
    # 定位「综合热度」小节
    start = None
    for i, ln in enumerate(lines):
        if "综合热度" in ln and ("TOP" in ln.upper() or "Top" in ln or "top" in ln or "20" in ln):
            start = i
            break
    if start is None:
        for i, ln in enumerate(lines):
            if "综合热度" in ln or "热度 TOP" in ln:
                start = i
                break
    if start is None:
        raise ValueError("没找到「综合热度 TOP20」表格，无法解析")

    rows = []
    for ln in lines[start + 1:]:
        s = ln.strip()
        if not s:
            if rows:
                break  # 表格结束（空行且已采到行）
            continue
        if s.startswith("#"):
            break
        if not s.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 4:
            continue
        # 跳过表头 / 分隔行
        if cells[0] in ("排名", "rank", "") or set(cells[0]) <= set("-: "):
            continue
        rows.append(cells)
    return rows


def clean_rank(s):
    """'①' / '1' / '1.' / '第1' → 1"""
    m = re.search(r"\d+", s)
    return int(m.group()) if m else 999


COLLECTION_HINT = ("三部曲", "合集", "精选集", "套装", "全集")


def is_collection(title):
    return any(h in title for h in ("三部曲", "合集", "精选集", "套装"))


def to_books(rows):
    books = []
    for c in rows:
        rank = clean_rank(c[0])
        title = c[1].strip("《》 ").strip()
        author = c[2].strip("《》 ").strip() if len(c) > 2 else ""
        cat = c[3].strip() if len(c) > 3 else ""
        blurb = c[4].strip() if len(c) > 4 else ""
        books.append({"rank": rank, "title": title, "author": author,
                      "cat": cat, "blurb": blurb})
    return books


def _fb_weights():
    """读取阅读数据反馈权重（feedback.py 生成 cat_weight.json）；文件不存在时零影响。"""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cat_weight.json")
    if os.path.exists(p):
        try:
            w = json.load(open(p, encoding="utf-8"))
            return {"cats": w.get("cats", {}), "books": w.get("books", {})}
        except Exception:
            pass
    return {"cats": {}, "books": {}}


def score_select(books, top_n=8):
    # 1) 过滤合集类（其单本通常已在榜，避免重复出卡）
    known_titles = {b["title"] for b in books}
    filtered = []
    dropped = []
    for b in books:
        if is_collection(b["title"]):
            dropped.append((b["title"], "合集/三部曲类"))
            continue
        filtered.append(b)

    # 2) 贪心加权打分：基础分=21-rank，同类第k本 -3*(k-1)，阅读反馈权重 bonus
    fb = _fb_weights()
    ordered = sorted(filtered, key=lambda b: (-(21 - b["rank"]), b["rank"]))
    selected, cat_cnt = [], {}
    for b in ordered:
        if len(selected) >= top_n:
            break
        k = cat_cnt.get(b["cat"], 0)
        pen = 3 * k
        bonus = fb["cats"].get(b["cat"], 0) + fb["books"].get(b["title"], 0)
        b["_score"] = (21 - b["rank"]) - pen + bonus
        b["_pen"] = pen
        b["_fb"] = bonus
        selected.append(b)
        cat_cnt[b["cat"]] = k + 1

    # 若过滤后不足 top_n，从剩余补齐（按名次）
    if len(selected) < top_n:
        have = {id(b) for b in selected}
        for b in sorted(filtered, key=lambda x: x["rank"]):
            if len(selected) >= top_n:
                break
            if id(b) in have:
                continue
            bonus = fb["cats"].get(b["cat"], 0) + fb["books"].get(b["title"], 0)
            b["_score"] = 21 - b["rank"] + bonus
            b["_pen"] = 0
            b["_fb"] = bonus
            selected.append(b)

    selected.sort(key=lambda b: b["rank"])
    return selected, dropped


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else find_latest()
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "lite_auto.json")
    top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 8

    md = open(path, encoding="utf-8").read()
    rows = parse_top20(md)
    print(f"已解析 {len(rows)} 行 TOP 表（来源：{os.path.basename(path)}）")
    books = to_books(rows)
    selected, dropped = score_select(books, top_n)

    print("\n— 过滤掉的合集类 —")
    for t, r in dropped:
        print(f"  ✂ {t}  （{r}）")

    print(f"\n— 加权打分选出前 {len(selected)} 本（按名次）—")
    for b in selected:
        fb_s = f"，反馈+{b['_fb']}" if b.get("_fb") else ""
        pen_s = f"，同类惩罚 -{b['_pen']}" if b["_pen"] else ""
        print(f"  #{b['rank']:>2} {b['title']:<14} {b['author']:<10} "
              f"[{b['cat']}]  分={b['_score']}{pen_s}{fb_s}")

    lite = [{"title": b["title"], "author": b["author"], "cat": b["cat"]}
            for b in selected]
    json.dump(lite, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n✅ 已写出 lite 书单：{out}（{len(lite)} 本，可直接喂 enrich.py）")


if __name__ == "__main__":
    main()
