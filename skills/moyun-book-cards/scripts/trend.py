#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
trend.py —— 榜单趋势库（墨韵拆书卡 v1.5.0）

把历史「畅销书周报 TOP20 表格」与各期 books.json 沉淀成结构化时间序列库
（trend_store.json），并自动分析三类趋势亮点：

  - 新晋上榜：最近一期新进榜单的书
  - 连续在榜：连续 N 期都在榜的长青书
  - 名次飙升：本期比上期排名上升 ≥5 名的书

产出：
  trend_store.json        结构化快照库（可反复增量构建）
  trend_report.md         趋势详情报告
  trend_highlights.txt    ≤6 条亮点短句（可直接拼进发布文案）

用法：
  python trend.py build            # 构建/更新快照库并输出分析
  python trend.py analyze          # 只分析（用现有 store）
"""
import os, sys, json, re, glob
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(BASE, "trend_store.json")
CARD_ROOT = os.environ.get("MOYUN_CARD_ROOT", os.path.join(os.getcwd(), "畅销书拆书卡"))


def parse_date(s):
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", str(s).strip())
    return f"{int(m[1]):04d}-{int(m[2]):02d}-{int(m[3]):02d}" if m else None


def norm(t):
    t = str(t).lower()
    return re.sub(r"[^\w\u4e00-\u9fff]", "", t)


def scan_reports():
    """从周报 Markdown 解析 TOP20 表。"""
    recs = []
    for md in sorted(glob.glob(os.path.join(BASE, "全网畅销书周报-*.md"))):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(md))
        date = m.group(1) if m else None
        if not date:
            continue
        lines = open(md, encoding="utf-8").read().splitlines()
        in_tab = False
        for ln in lines:
            if "TOP20" in ln:
                in_tab = True
                continue
            if in_tab:
                cells = [c.strip() for c in ln.strip().strip("|").split("|")]
                if len(cells) >= 4 and re.match(r"^\d{1,2}$", cells[0]):
                    recs.append({"date": date, "source": "综合榜", "rank": int(cells[0]),
                                 "title": cells[1], "author": cells[2] if len(cells) > 2 else "",
                                 "cat": cells[3] if len(cells) > 3 else ""})
                elif in_tab and ln.startswith("#") and "TOP20" not in ln:
                    in_tab = False
    return recs


def scan_cards():
    """从各期 books.json 兜底补充（rank 记为 None，代表出过卡）。"""
    recs = []
    if not os.path.isdir(CARD_ROOT):
        return recs
    for name in sorted(os.listdir(CARD_ROOT)):
        if re.search(r"盘点|demo|演示", name, re.IGNORECASE):
            continue
        bj = os.path.join(CARD_ROOT, name, "books.json")
        if not os.path.isfile(bj):
            continue
        try:
            data = json.load(open(bj, encoding="utf-8"))
        except Exception:
            continue
        date = parse_date(data.get("date")) or parse_date(name)
        if not date:
            continue
        for i, b in enumerate(data.get("books", []), 1):
            recs.append({"date": date, "source": "出卡", "rank": i,
                         "title": b.get("title", ""), "author": b.get("author", ""),
                         "cat": b.get("cat", "")})
    return recs


def build_store():
    recs = scan_reports() + scan_cards()
    seen, uniq = set(), []
    for r in recs:
        if not r["title"]:
            continue
        key = (r["date"], r["source"], norm(r["title"]))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    uniq.sort(key=lambda r: r["date"], reverse=True)
    json.dump({"updated": datetime.now().strftime("%Y-%m-%d %H:%M"), "records": uniq},
              open(STORE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return uniq


def analyze(records):
    by_date = {}
    for r in records:
        by_date.setdefault(r["date"], {})[norm(r["title"])] = r
    dates = sorted(by_date.keys(), reverse=True)
    if not dates:
        return [], "无数据"
    cur, prev = by_date[dates[0]], (by_date[dates[1]] if len(dates) > 1 else {})

    def streak_of(key):
        n = 0
        for d in dates:
            if key in by_date[d]:
                n += 1
            else:
                break
        return n

    rising, streaks, fresh = [], [], []
    for key, r in cur.items():
        st = streak_of(key)
        if st >= 2:
            streaks.append((st, r))
        if prev and key not in prev:
            fresh.append(r)
        if prev and key in prev and r.get("rank") and prev[key].get("rank"):
            if prev[key]["rank"] - r["rank"] >= 5:
                rising.append((prev[key]["rank"], r))
    streaks.sort(key=lambda x: -x[0])
    rising.sort(key=lambda x: x[1]["rank"])
    return fresh, streaks, rising, dates[0]


def render(records):
    res = analyze(records)
    if len(res) == 2:
        return [], "无数据"
    fresh, streaks, rising, cur_date = res
    hl = []
    for st, r in streaks[:3]:
        hl.append(f"《{r['title']}》已连续 {st} 期在榜，稳坐长青位")
    for pr, r in rising[:2]:
        hl.append(f"《{r['title']}》从第 {pr} 名飙升至第 {r['rank']} 名，本周黑马")
    for r in fresh[:2]:
        hl.append(f"《{r['title']}》新晋上榜（第 {r['rank']} 名），值得关注")
    hl = hl[:6]

    lines = [f"# 榜单趋势报告（截至 {cur_date}）", "",
             f"> 快照库共 {len(records)} 条记录，覆盖 {len(set(r['date'] for r in records))} 个期次。", ""]
    lines.append("## 连续在榜（长青书）")
    for st, r in streaks[:8]:
        lines.append(f"- 《{r['title']}》—— 连续 **{st}** 期在榜（当前第 {r['rank']} 名）")
    lines.append("")
    lines.append("## 名次飙升（本周黑马）")
    if rising:
        for pr, r in rising[:5]:
            lines.append(f"- 《{r['title']}》—— 第 {pr} → 第 **{r['rank']}** 名")
    else:
        lines.append("- 本期无 ≥5 名的飙升")
    lines.append("")
    lines.append("## 新晋上榜")
    if fresh:
        for r in fresh[:5]:
            lines.append(f"- 《{r['title']}》（{r.get('author','')}）—— 首次进榜，第 {r['rank']} 名")
    else:
        lines.append("- 本期无新晋书目")
    open(os.path.join(BASE, "trend_report.md"), "w", encoding="utf-8").write("\n".join(lines))
    open(os.path.join(BASE, "trend_highlights.txt"), "w", encoding="utf-8").write(
        "\n".join(hl))
    return hl, cur_date


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    records = build_store() if cmd == "build" else json.load(open(STORE, encoding="utf-8"))["records"]
    hl, cur = render(records)
    print(f"✅ 快照库 {len(records)} 条记录（最新期 {cur}）")
    print("--- 趋势亮点（可拼进发布文案）---")
    for h in hl:
        print("  ·", h)


if __name__ == "__main__":
    main()
