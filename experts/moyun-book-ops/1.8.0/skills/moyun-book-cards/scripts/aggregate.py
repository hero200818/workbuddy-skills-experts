#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
aggregate.py —— 月度 / 年度盘点聚合器（墨韵拆书卡 v1.4.0）

把历史上各期「畅销书拆书卡/<期>/books.json」里的书目，按书名归一化去重，
累加「出现频次」与「最近出现日期」，汇总打分为一份「盘点书单」：
  - monthly：取最近 window 天（默认 30 天）内各期出现的书，按 频次+近期 选 top N（默认 8）
  - annual ：取指定年份（默认最新年份）内各期出现的书，按 频次+近期 选 top N（默认 12）

直接输出 gen_cards_ios.py 可消费的盘点 input（kind=monthly/annual），一条命令即出盘点卡。
复用历史已生成的完整拆书数据，无需重新补全。

用法：
  python aggregate.py monthly [--root ROOT] [--window 30] [--top 8] [--out OUT]
  python aggregate.py annual  [--root ROOT] [--year 2025] [--top 12] [--out OUT]
"""
import os, sys, json, re
from datetime import datetime, timedelta


# 默认历史根目录（与出卡目录一致）
DEFAULT_ROOT = os.environ.get("MOYUN_CARD_ROOT", os.path.join(os.getcwd(), "畅销书拆书卡"))


def parse_date(s):
    """把 books.json 里的 date 字段解析成 datetime；支持 2026-10-27 / 2026.10 / 2026-10 / 2026年10月。"""
    if not s:
        return None
    s = str(s).strip()
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        return datetime(int(m[1]), int(m[2]), int(m[3]))
    m = re.match(r"(\d{4})[.\-](\d{1,2})", s)
    if m:
        return datetime(int(m[1]), int(m[2]), 1)
    m = re.match(r"(\d{4})年(\d{1,2})月", s)
    if m:
        return datetime(int(m[1]), int(m[2]), 1)
    return None


def norm(t):
    """书名归一化：小写、去空白与标点，用于跨期合并同一本书。"""
    t = str(t).lower()
    t = re.sub(r"[\s\u3000]+", "", t)
    t = re.sub(r"[^\w\u4e00-\u9fff]", "", t, flags=re.UNICODE)
    return t


def load_periods(root):
    periods = []
    if not os.path.isdir(root):
        print(f"[warn] 历史根目录不存在：{root}")
        return periods
    for name in sorted(os.listdir(root)):
        # 跳过盘点/演示等衍生期，避免盘点结果自我强化进下一次聚合
        if re.search(r"盘点|demo|演示", name, re.IGNORECASE):
            continue
        p = os.path.join(root, name)
        bj = os.path.join(p, "books.json")
        if not os.path.isfile(bj):
            continue
        try:
            data = json.load(open(bj, encoding="utf-8"))
        except Exception:
            continue
        books = data.get("books", [])
        if not books:
            continue
        dt = parse_date(data.get("date")) or parse_date(name)
        periods.append({
            "name": name,
            "date": dt,
            "issue": data.get("issue", name),
            "books": books,
        })
    return periods


def book_score(b):
    """字段丰满度（取最完整的一条作 sample）。"""
    return sum(1 for k in ("title", "author", "cat", "rec", "points", "quote", "who") if b.get(k))


def aggregate(periods, mode, year=None, window_days=30, top=None):
    agg = {}
    for per in periods:
        dt = per["date"]
        for b in per["books"]:
            key = norm(b.get("title", ""))
            if not key:
                continue
            e = agg.get(key)
            if e is None:
                e = {"title": b.get("title"), "author": b.get("author"),
                     "count": 0, "dates": [], "sample": None}
                agg[key] = e
            e["count"] += 1
            if dt:
                e["dates"].append(dt)
            if e["sample"] is None or book_score(b) > book_score(e["sample"]):
                e["sample"] = b

    if mode == "monthly":
        valid = [p["date"] for p in periods if p["date"]]
        if not valid:
            return [], None, None
        ref = max(valid)
        lo = ref - timedelta(days=window_days)
        sel = []
        for k, e in agg.items():
            if not e["dates"]:
                continue
            in_win = any(lo <= d <= ref for d in e["dates"])
            if not in_win:
                continue
            last = max(e["dates"])
            score = e["count"] * 1000 + last.toordinal()
            sel.append((score, e))
        topn = top or 8
        sel.sort(key=lambda x: -x[0])
        chosen = [e["sample"] for _, e in sel[:topn]]
        return chosen, ref, lo

    else:  # annual
        if year is None:
            years = [d.year for p in periods if p["date"] for d in [p["date"]]]
            year = max(years) if years else None
        sel = []
        for k, e in agg.items():
            if not e["dates"]:
                continue
            if not any(d.year == year for d in e["dates"]):
                continue
            last = max(e["dates"])
            score = e["count"] * 1000 + last.toordinal()
            sel.append((score, e))
        # 受九宫格版式（封面+8书卡）约束，年度盘点同样精选 8 本，保证卡片与文案一致
        topn = top or 8
        sel.sort(key=lambda x: -x[0])
        chosen = [e["sample"] for _, e in sel[:topn]]
        return chosen, year, None


def build_input(mode, books, ref=None, year=None):
    if mode == "monthly":
        issue = f"月度盘点 · {ref.year}年{ref.month}月"
        date = f"{ref.year}-{ref.month:02d}"
        kind = "monthly"
        note = f"由 aggregate 自动汇总近 30 天各期（{len(books)} 本入选）生成"
    else:
        issue = f"{year} 年度盘点"
        date = str(year)
        kind = "annual"
        note = f"由 aggregate 自动汇总 {year} 全年各期（{len(books)} 本入选）生成"
    return {
        "issue": issue,
        "date": date,
        "kind": kind,
        "short": "墨韵拆书 · 盘点",
        "note": note,
        "books": books,
    }


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "monthly"
    if mode not in ("monthly", "annual"):
        print("mode 必须是 monthly 或 annual")
        sys.exit(2)

    root = DEFAULT_ROOT
    year = None
    window = 30
    top = None
    out = None
    i = 2
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == "--root":
            root = sys.argv[i + 1]; i += 2
        elif a == "--year":
            year = int(sys.argv[i + 1]); i += 2
        elif a == "--window":
            window = int(sys.argv[i + 1]); i += 2
        elif a == "--top":
            top = int(sys.argv[i + 1]); i += 2
        elif a == "--out":
            out = sys.argv[i + 1]; i += 2
        else:
            i += 1

    periods = load_periods(root)
    print(f"已加载 {len(periods)} 期历史数据（根目录：{root}）")
    if not periods:
        print("[error] 无可用历史数据，退出")
        sys.exit(1)

    books, ref_or_year, _ = aggregate(periods, mode, year=year, window_days=window, top=top)
    if not books:
        print("[error] 聚合结果为空（检查 --year / --window）")
        sys.exit(1)

    if mode == "monthly":
        inp = build_input(mode, books, ref=ref_or_year)
        tag = f"月度-{ref_or_year.year}{ref_or_year.month:02d}"
    else:
        inp = build_input(mode, books, year=ref_or_year)
        tag = f"年度-{ref_or_year}"

    out = out or f"盘点_{tag}.json"
    json.dump(inp, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ 已生成 {mode} 盘点书单：{len(books)} 本 → {out}")
    print(f"   期号：{inp['issue']}  |  版式：{inp['kind']}")
    for i, b in enumerate(books, 1):
        print(f"   {i:>2}. {b.get('title')}  —— {b.get('author')}")
    # 顺手把生成器命令行打印出来，方便直接出卡
    cwd = os.getcwd()
    print(f"\n下一步出卡：")
    print(f'  python gen_cards_ios.py "{out}" "{inp["issue"]}" "{inp["date"]}" "{DEFAULT_ROOT}"')


if __name__ == "__main__":
    main()
