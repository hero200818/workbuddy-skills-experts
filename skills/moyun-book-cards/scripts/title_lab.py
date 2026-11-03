#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
title_lab.py —— 标题风格库 A/B（墨韵拆书卡 v1.6.0）

根治"40 期标题同一模板"：对一期书单，用五种风格各生成 2 条候选标题（均 ≤20 字），
并复用 qc 的归一化查重逻辑标记与历史期的重复风险，输出 title_lab.md。

风格：悬念式 / 数字冲击式 / 情感共鸣式 / 提问互动式 / 热点借势式

用法：
  python title_lab.py <期目录或books.json>     # 生成 5×2 候选 + 查重
"""
import os, sys, json, re, glob, difflib

BASE = os.path.dirname(os.path.abspath(__file__))
CARD_ROOT = os.environ.get("MOYUN_CARD_ROOT", os.path.join(os.getcwd(), "畅销书拆书卡"))
WHEN = {"weekly": "本周", "monthly": "本月", "annual": "今年"}


def norm_title(t):
    t = re.sub(r"\d+", "N", t)
    t = re.sub(r"本周|本月|本季|这一年|年度|月度|周榜", "X", t)
    return t


def load(target):
    d = target if os.path.isdir(target) else os.path.dirname(os.path.abspath(target))
    return json.load(open(os.path.join(d, "books.json"), encoding="utf-8")), d


def fit(s):
    """截断到 20 字以内（尽量在标点处断）。"""
    if len(s) <= 20:
        return s
    cut = s[:20]
    for p in ("，", "｜", "！", "？", "、"):
        i = cut.rfind(p)
        if i >= 10:
            return cut[:i]
    return cut


def gen_titles(books, kind):
    w = WHEN.get(kind, "本期")
    n = len(books)
    t1, t2 = books[0]["title"], books[1]["title"] if n > 1 else books[0]["title"]
    q1 = (books[0].get("quote") or "").rstrip("。")
    q1 = q1[:10] + "…" if len(q1) > 10 else q1
    vs_title = fit(f"《{t1}》VS《{t2}》带谁上荒岛")
    if "《" in vs_title[4:] and vs_title.count("《") != vs_title.count("》"):
        vs_title = "两本爆款只能带一本走"
    a1 = books[0]["author"]
    pools = {
        "悬念式": [
            f"全网都在买，{n}本里藏着什么",
            f"《{t1}》凭什么刷屏全网",
            f"第{n}本，我劝你别只看封面",
        ],
        "数字冲击式": [
            f"{w}{n}本爆款，3分钟拆完",
            f"{n}张卡读懂{n}本热销书",
            f"9图×{n}本，{w}书单天花板",
        ],
        "情感共鸣式": [
            f"「{q1}」——{a1}说透了",
            f"{w}书单：给心里缺角的人",
            f"《{t2}》看哭我，也救了我",
        ],
        "提问互动式": [
            f"这{n}本你读过几本？",
            vs_title,
            f"{w}买书不踩坑，先看这张卡",
        ],
        "热点借势式": [
            f"{w}全网书榜，我拆出了共识",
            f"榜单刷屏的{n}本，拆给你看",
            f"都在晒《{t1}》，我拆得更狠",
        ],
    }
    out = {}
    for style, tpl in pools.items():
        seen, lst = set(), []
        for s in tpl:
            s = fit(s)
            if s not in seen:
                seen.add(s)
                lst.append(s)
        out[style] = lst
    return out


def historical():
    cur_titles = []
    for md in glob.glob(os.path.join(CARD_ROOT, "*", "发布文案.md")):
        txt = open(md, encoding="utf-8").read()
        seg = re.search(r"发布标题.*?\n((?:\d+\..+\n?)+)", txt)
        if seg:
            for ln in seg.group(1).splitlines():
                m = re.match(r"\d+\.\s*(.+)", ln.strip())
                if m:
                    cur_titles.append(m.group(1).strip())
    return cur_titles


def dedupe_flag(title, hist):
    nt = norm_title(title)
    for h in hist:
        if norm_title(h) == nt:
            return "💡栏目模板"
        r = difflib.SequenceMatcher(None, title, h).ratio()
        if r > 0.8:
            return f"⚠️雷同{r:.0%}"
    return "✅"


def main():
    data, d = load(sys.argv[1])
    titles = gen_titles(data["books"], data.get("kind", "weekly"))
    hist = historical()
    lines = [f"# 标题工坊 · {data.get('issue','')}", "",
             f"> 五种风格 × 2-3 条，共 {sum(len(v) for v in titles.values())} 条候选；"
             f"已对历史 {len(hist)} 期标题查重。选一条直接用。", ""]
    for style, lst in titles.items():
        lines.append(f"## {style}")
        for t in lst:
            flag = dedupe_flag(t, hist)
            mark = "" if flag == "✅" else f"  [{flag}]"
            lines.append(f"- {t}（{len(t)} 字）{mark}")
        lines.append("")
    open(os.path.join(d, "title_lab.md"), "w", encoding="utf-8").write("\n".join(lines))
    print(f"✅ 标题工坊完成 → {os.path.join(d, 'title_lab.md')}")
    for style, lst in titles.items():
        print(f"  {style}: " + " / ".join(lst))


if __name__ == "__main__":
    main()
