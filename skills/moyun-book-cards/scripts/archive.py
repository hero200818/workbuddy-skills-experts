#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
archive.py —— 拆书档案总览（墨韵拆书卡 v1.5.0）

扫描全部期目录，生成本地可检索的「拆书档案」：
  archive_index.json    结构化索引：书 → 期 → 图片/字段，期 → 书单
  拆书档案总览.md       人类可读总览：全书清单（含出场期数）、分类统计、每期目录

一句话可查："拆过哪些书""某本书在哪几期出现过""某个分类拆了多少本"。

用法：
  python archive.py                 # 全量重建
  python archive.py --query 活着    # 查某本书
  python archive.py --query 小说    # 查某分类
"""
import os, sys, json, re, argparse
from datetime import datetime

CARD_ROOT = os.environ.get("MOYUN_CARD_ROOT", os.path.join(os.getcwd(), "畅销书拆书卡"))
BASE = os.path.dirname(os.path.abspath(__file__))


def norm(t):
    return re.sub(r"[^\w\u4e00-\u9fff]", "", str(t))


def scan():
    periods, books = [], {}
    for name in sorted(os.listdir(CARD_ROOT)):
        p = os.path.join(CARD_ROOT, name)
        bj = os.path.join(p, "books.json")
        if not os.path.isfile(bj):
            continue
        try:
            data = json.load(open(bj, encoding="utf-8"))
        except Exception:
            continue
        imgs = sorted(f for f in os.listdir(p)
                      if f.endswith(".jpg") and f[:2].isdigit())
        periods.append({"issue": data.get("issue", name), "dir": name,
                        "date": data.get("date", ""), "kind": data.get("kind", "weekly"),
                        "n_books": len(data.get("books", [])), "n_images": len(imgs)})
        for b in data.get("books", []):
            k = norm(b.get("title", ""))
            if not k:
                continue
            e = books.setdefault(k, {"title": b.get("title"), "author": b.get("author", ""),
                                     "cat": b.get("cat", ""), "issues": [], "count": 0})
            e["issues"].append(data.get("issue", name))
            e["count"] += 1
    idx = {"updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
           "total_periods": len(periods), "total_books": len(books),
           "periods": periods, "books": books}
    json.dump(idx, open(os.path.join(BASE, "archive_index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return idx


def render_md(idx):
    lines = [f"# 拆书档案总览（更新于 {idx['updated']}）", "",
             f"共 **{idx['total_periods']} 期** · 去重 **{idx['total_books']} 本**。", ""]
    lines.append("## 一、全书出场榜（按出现次数）")
    for t, e in sorted(idx["books"].items(), key=lambda x: -x[1]["count"]):
        lines.append(f"- 《{e['title']}》{e['author']}｜{e['cat']}｜出场 **{e['count']} 次**"
                     f"（{'、'.join(e['issues'][:6])}{'…' if e['count'] > 6 else ''}）")
    lines.append("")
    cats = {}
    for e in idx["books"].values():
        cats[e["cat"] or "未分类"] = cats.get(e["cat"] or "未分类", 0) + 1
    lines.append("## 二、分类统计")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        lines.append(f"- {c}：{n} 本")
    lines.append("")
    lines.append("## 三、各期目录")
    for p in idx["periods"]:
        lines.append(f"- 《{p['issue']}》（{p['date']}｜{p['kind']}）—— {p['n_books']} 本书 · {p['n_images']} 张图 · 畅销书拆书卡/{p['dir']}/")
    open(os.path.join(BASE, "拆书档案总览.md"), "w", encoding="utf-8").write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query")
    args = ap.parse_args()
    idx = scan()
    render_md(idx)
    print(f"✅ 档案已更新：{idx['total_periods']} 期 / 去重 {idx['total_books']} 本")
    print("   - archive_index.json")
    print("   - 拆书档案总览.md")
    if args.query:
        q = norm(args.query)
        hits = [(e["title"], e["author"], e["cat"], e["count"], e["issues"])
                for k, e in idx["books"].items()
                if q in norm(e["title"]) or q in norm(e["cat"])]
        print(f"\n查询「{args.query}」：{len(hits)} 条")
        for t, a, c, n, iss in hits:
            print(f"  《{t}》{a}｜{c}｜出场{n}次：{'、'.join(iss)}")


if __name__ == "__main__":
    main()
