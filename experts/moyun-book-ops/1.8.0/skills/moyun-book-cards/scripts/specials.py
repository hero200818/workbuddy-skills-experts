#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
specials.py —— 主题特辑引擎（墨韵拆书卡 v1.6.0）

内置「选题日历」：到点自动给出特辑策划案——主题名、匹配书目（从拆书档案挑）、
标题建议、限定封面文案。配合 gen_extra.py --theme 出限定配色封面。

用法：
  python specials.py                # 检查今天（±7 天窗口）命中的特辑
  python specials.py --list         # 列出全部选题日历
  python specials.py --plan 04-23   # 指定日期生成策划案
"""
import os, sys, json, re, argparse
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.path.join(BASE, "archive_index.json")

# 选题日历：(月-日, 特辑名, 主题关键词(匹配cat/书名), 封面副标题, 主题色)
SPECIALS = [
    ("01-01", "新年立志书单", ["成长", "思维", "习惯"], "新的一年，从这本书开始", "festive"),
    ("02-14", "爱与理解特辑", ["情感", "心理", "关系"], "读懂爱，先读懂自己", "rose"),
    ("03-08", "她们的声音", ["女性", "文学", "小说"], "她们写下的世界", "rose"),
    ("04-23", "世界读书日特辑", ["经典", "文学", "散文"], "读书日，把好书拆给你", "festive"),
    ("06-01", "童心书单", ["童书", "童话", "成长"], "给大小朋友的书单", "spring"),
    ("09-01", "开学季充电书单", ["学习", "思维", "成长"], "开学充电，先充大脑", "spring"),
    ("11-01", "深秋沉淀季", ["历史", "思想", "经典"], "深秋宜读书，沉淀一整年", "autumn"),
    ("12-25", "寒冬暖读书单", ["温情", "治愈", "文学"], "冬天最暖的是一本好书", "autumn"),
]

# 限定封面色板（gen_extra --theme 使用）
THEMES = {
    "classic": {"stops": [(0, (248, 242, 228)), (0.5, (243, 234, 214)), (1, (231, 220, 195))], "accent": (150, 42, 36)},
    "festive": {"stops": [(0, (250, 240, 226)), (0.5, (245, 224, 196)), (1, (232, 200, 160))], "accent": (170, 52, 40)},
    "rose":    {"stops": [(0, (249, 240, 240)), (0.5, (244, 224, 224)), (1, (232, 202, 204))], "accent": (166, 62, 84)},
    "spring":  {"stops": [(0, (243, 247, 236)), (0.5, (227, 237, 216)), (1, (204, 220, 192))], "accent": (90, 118, 52)},
    "autumn":  {"stops": [(0, (250, 244, 230)), (0.5, (244, 229, 202)), (1, (226, 202, 168))], "accent": (156, 90, 32)},
}


def hit_special(date=None, window=7):
    d0 = date or datetime.now()
    hits = []
    for md, name, kws, sub, theme in SPECIALS:
        m, dd = map(int, md.split("-"))
        sp = d0.replace(month=m, day=dd)
        if abs((sp - d0).days) <= window:
            hits.append({"date": md, "name": name, "keywords": kws,
                         "subtitle": sub, "theme": theme, "days": (sp - d0).days})
    return sorted(hits, key=lambda h: abs(h["days"]))


def load_books_pool():
    """从拆书档案取全部书（title/author/cat/count）。"""
    if not os.path.exists(ARCHIVE):
        return []
    idx = json.load(open(ARCHIVE, encoding="utf-8"))
    return sorted(idx.get("books", {}).values(),
                  key=lambda e: -e.get("count", 0))


def plan(hit, top=6):
    pool = load_books_pool()
    scored = []
    for e in pool:
        hay = e["cat"] + e["title"]
        k = sum(1 for kw in hit["keywords"] if kw in hay)
        if k:
            scored.append((k * 10 + min(e.get("count", 0), 5), e))
    scored.sort(key=lambda x: -x[0])
    picks = [e for _, e in scored[:top]]
    days = hit["days"]
    when = "今天" if days == 0 else (f"{days}天后" if days > 0 else f"{-days}天前")
    L = [f"# 特辑策划案 · {hit['name']}（{hit['date']}，{when}）",
         "", f"- 封面副标题：{hit['subtitle']}",
         f"- 限定主题色：{hit['theme']}（gen_extra.py --theme {hit['theme']}）", ""]
    if picks:
        L.append("## 主题书目候选（按相关度+出场热度）")
        for e in picks:
            L.append(f"- 《{e['title']}》{e['author']}｜{e['cat']}（出场 {e['count']} 次）")
    else:
        L.append("## 主题书目候选")
        L.append("- 档案中暂无强相关书目，可从下期榜单定向挑选")
    L += ["", "## 标题建议", "",
          f"1. {hit['subtitle']}｜{hit['name']}",
          f"2. {hit['name']}来了，这几本先读",
          f"3. 为什么人人都该在{hit['date'].split('-')[0]}月读这几本"]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--plan", help="指定 MM-DD 日期生成策划案")
    ap.add_argument("--out", help="策划案输出路径")
    args = ap.parse_args()

    if args.list:
        print("选题日历（±7 天自动触发）：")
        for md, name, kws, sub, theme in SPECIALS:
            print(f"  {md}  {name}（{'、'.join(kws)}）→ 主题色 {theme}")
        return
    if args.plan:
        m, dd = map(int, args.plan.split("-"))
        hits = hit_special(datetime(datetime.now().year, m, dd), window=0)
        if not hits:
            print(f"{args.plan} 不在日历中"); sys.exit(1)
    else:
        hits = hit_special()
        if not hits:
            print("未来 7 天无特辑。用 --list 查看全部日历。")
            return
    hit = hits[0]
    text = plan(hit)
    out = args.out or os.path.join(BASE, f"特辑策划_{hit['name']}.md")
    open(out, "w", encoding="utf-8").write(text)
    print(f"✅ 命中特辑：{hit['name']}（{hit['date']}，{'今天' if hit['days']==0 else str(abs(hit['days']))+'天后' if hit['days']>0 else str(abs(hit['days']))+'天前'}）")
    print(f"   策划案 → {out}")
    for ln in text.splitlines():
        if ln.startswith("- 《"):
            print("   ", ln)


if __name__ == "__main__":
    main()
