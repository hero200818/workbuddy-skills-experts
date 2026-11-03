#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小红书笔记数据诊断指标计算。

用法: python metrics.py notes.json

notes.json 格式:
{
  "notes": [
    {"title": "xxx", "date": "2026-10-20", "group": "小说线",
     "impr": 140, "views": 108, "ctr": 5.0, "likes": 5, "saves": 3,
     "comments": 2, "follows": 0},
    ...
  ]
}
字段: impr=曝光 views=观看 ctr=封面点击率%(数字) likes/saves/comments=互动 follows=涨粉 group=选题分组(可选)
输出: 汇总指标 + Top/Bottom 榜 + 分组对比，供诊断报告引用。
"""
import json
import sys


def pct(a, b):
    return round(a / b * 100, 2) if b else 0.0


def summarize(notes):
    n = len(notes)
    t = {k: sum(x.get(k, 0) for x in notes) for k in ("impr", "views", "likes", "saves", "comments", "follows")}
    inter = t["likes"] + t["saves"] + t["comments"]
    out = {
        "篇数": n,
        "总曝光": t["impr"],
        "单篇均曝光": round(t["impr"] / n, 1) if n else 0,
        "封面点击率均值%": round(sum(x.get("ctr", 0) for x in notes) / n, 2) if n else 0,
        "曝光到观看转化%": pct(t["views"], t["impr"]),
        "总互动": inter,
        "互动率_对曝光%": pct(inter, t["impr"]),
        "互动率_对观看%": pct(inter, t["views"]),
        "收藏点赞比": round(t["saves"] / t["likes"], 2) if t["likes"] else None,
        "每千曝光涨粉": pct(t["follows"], t["impr"]),
        "零评论占比%": pct(sum(1 for x in notes if x.get("comments", 0) == 0), n),
        "零涨粉占比%": pct(sum(1 for x in notes if x.get("follows", 0) == 0), n),
    }
    return out


def groups(notes):
    g = {}
    for x in notes:
        g.setdefault(x.get("group") or "未分组", []).append(x)
    rows = {}
    for name, items in g.items():
        k = len(items)
        inter = sum(x.get("likes", 0) + x.get("saves", 0) + x.get("comments", 0) for x in items)
        impr = sum(x.get("impr", 0) for x in items)
        rows[name] = {
            "篇数": k,
            "均曝光": round(impr / k, 0),
            "均点击率%": round(sum(x.get("ctr", 0) for x in items) / k, 2),
            "均互动": round(inter / k, 2),
            "涨粉合计": sum(x.get("follows", 0) for x in items),
            "每千曝光涨粉": pct(sum(x.get("follows", 0) for x in items), impr),
        }
    return rows


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    notes = data["notes"] if isinstance(data, dict) else data
    notes = sorted(notes, key=lambda x: x.get("impr", 0), reverse=True)

    print("== 汇总指标 ==")
    for k, v in summarize(notes).items():
        print(f"{k}: {v}")

    print("\n== 曝光 Top5 ==")
    for x in notes[:5]:
        print(f"  {x['title']}: 曝光{x.get('impr')} 点击率{x.get('ctr')}% 涨粉{x.get('follows')}")
    print("== 曝光 Bottom5 ==")
    for x in notes[-5:]:
        print(f"  {x['title']}: 曝光{x.get('impr')} 点击率{x.get('ctr')}% 涨粉{x.get('follows')}")

    print("\n== 互动 Top5 ==")
    for x in sorted(notes, key=lambda y: -(y.get("likes", 0) + y.get("saves", 0) + y.get("comments", 0)))[:5]:
        i = x.get("likes", 0) + x.get("saves", 0) + x.get("comments", 0)
        print(f"  {x['title']}: 互动{i} 涨粉{x.get('follows')}")

    print("\n== 涨粉 Top5 ==")
    for x in sorted(notes, key=lambda y: -y.get("follows", 0))[:5]:
        print(f"  {x['title']}: 涨粉{x.get('follows')} 曝光{x.get('impr')}")

    print("\n== 选题分组对比 ==")
    for name, r in groups(notes).items():
        print(f"  [{name}] " + " ".join(f"{k}:{v}" for k, v in r.items()))


if __name__ == "__main__":
    main()
