#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
feedback.py —— 数据反馈闭环（墨韵拆书卡 v1.5.0）

把各期发布后的阅读数据录回 feedback.json，聚合出「书目权重 + 类别权重」，
生成 cat_weight.json 供 parse_weekly 选书打分加成——哪类书读者爱看，下期就多选哪类。

数据文件：
  feedback.json    {"issues": {"<期名>": {"date": "...", "books": {"<书名>": {"views": n, "likes": n}}}}}
  cat_weight.json  {"cats": {"<类别>": 权重-1~+2}, "books": {"<书名>": 权重0~+3}, "updated": ...}

权重模型（简洁可解释）：
  书目权重 = min(3, log10(views+1)/2) * (1 + 互动率)   互动率 = likes/max(views,1)
  类别权重 = 该类别全部书目的书目权重均值 - 全库均值（居中，范围约 -1~+2）

用法：
  python feedback.py record <期名> <数据.json>     # 录入：{"书名": {"views":5200,"likes":180}, ...}
  python feedback.py weight                       # 由 feedback.json 重算 cat_weight.json
  python feedback.py report                       # 查看当前数据与权重
  python feedback.py demo                         # 跑一遍演示计算（不写入任何文件）
"""
import os, sys, json, math
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
FB = os.path.join(BASE, "feedback.json")
CW = os.path.join(BASE, "cat_weight.json")


def load_fb():
    if os.path.exists(FB):
        return json.load(open(FB, encoding="utf-8"))
    return {"issues": {}}


def cmd_record(issue, data_path):
    payload = json.load(open(data_path, encoding="utf-8"))
    fb = load_fb()
    ent = fb["issues"].setdefault(issue, {"date": datetime.now().strftime("%Y-%m-%d"), "books": {}})
    for title, v in payload.items():
        old = ent["books"].get(title, {"views": 0, "likes": 0})
        old["views"] = old.get("views", 0) + int(v.get("views", 0))
        old["likes"] = old.get("likes", 0) + int(v.get("likes", 0))
        ent["books"][title] = old
    json.dump(fb, open(FB, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"✅ 已录入 {issue}：{len(payload)} 本的阅读数据")


def book_weight(views, likes):
    if views <= 0:
        return 0.0
    return round(min(3.0, math.log10(views + 1) / 2) * (1 + likes / max(views, 1)), 3)


def compute():
    fb = load_fb()
    bw, cat_pool = {}, {}
    for issue, ent in fb["issues"].items():
        for title, v in ent["books"].items():
            w = book_weight(int(v.get("views", 0)), int(v.get("likes", 0)))
            bw[title] = round(bw.get(title, 0) + w, 3)
    # 类别映射需要查内容库
    lib_dir = os.path.join(BASE, "library")
    title2cat = {}
    if os.path.isdir(lib_dir):
        for fn in os.listdir(lib_dir):
            if fn.endswith(".json"):
                try:
                    e = json.load(open(os.path.join(lib_dir, fn), encoding="utf-8"))
                    title2cat[e.get("title", "")] = e.get("cat", "")
                except Exception:
                    pass
    for t, w in bw.items():
        cat_pool.setdefault(title2cat.get(t, "未分类"), []).append(w)
    allv = [w for v in cat_pool.values() for w in v]
    avg = sum(allv) / len(allv) if allv else 0
    cats = {c: round(sum(v) / len(v) - avg, 3) for c, v in cat_pool.items()}
    return bw, cats


def cmd_weight():
    bw, cats = compute()
    out = {"cats": cats, "books": bw, "updated": datetime.now().strftime("%Y-%m-%d %H:%M")}
    json.dump(out, open(CW, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"✅ cat_weight.json 已更新：{len(bw)} 本书 / {len(cats)} 个类别")
    cmd_report()


def cmd_report():
    if os.path.exists(CW):
        w = json.load(open(CW, encoding="utf-8"))
        bw, cats = w.get("books", {}), w.get("cats", {})
    else:
        bw, cats = compute()
    print("— 书目权重 Top10 —")
    for t, v in sorted(bw.items(), key=lambda x: -x[1])[:10]:
        print(f"  {v:+.2f}  《{t}》")
    print("— 类别权重 —")
    for c, v in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {v:+.2f}  {c}")
    if not bw:
        print("（暂无数据：用 feedback.py record 录入各期阅读数据后，再跑 weight）")


def cmd_demo():
    demo = {"活着": {"views": 52000, "likes": 1800},
            "三体": {"views": 41000, "likes": 1500},
            "我的阿勒泰": {"views": 12000, "likes": 900}}
    bw, cats = {}, {}
    import tempfile
    old = None
    fb = load_fb()
    fb["issues"]["__demo__"] = {"date": "demo", "books": demo}
    globals()["_fb_tmp"] = fb
    # 临时替换 load
    saved = json.load(open(FB, encoding="utf-8")) if os.path.exists(FB) else None
    json.dump(fb, open(FB, "w", encoding="utf-8"), ensure_ascii=False)
    try:
        bw, cats = compute()
    finally:
        if saved is not None:
            json.dump(saved, open(FB, "w", encoding="utf-8"), ensure_ascii=False)
        else:
            os.remove(FB)
    print("【演示】若录入以下数据：", json.dumps(demo, ensure_ascii=False))
    print("— 演示书目权重 —")
    for t, v in sorted(bw.items(), key=lambda x: -x[1]):
        print(f"  {v:+.2f}  《{t}》")
    for c, v in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {v:+.2f}  {c}")
    print("（演示未写入任何文件；cat_weight.json 在真实数据录入后生成并自动生效）")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "record" and len(sys.argv) >= 4:
        cmd_record(sys.argv[2], sys.argv[3])
    elif cmd == "weight":
        cmd_weight()
    elif cmd == "demo":
        cmd_demo()
    else:
        cmd_report()
