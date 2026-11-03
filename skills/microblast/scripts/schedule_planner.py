#!/usr/bin/env python3
"""
智能排期器 v1.0 - 按星期策略自动排出未来N天发布计划（避免同题材连续+优先爆款基因）
用法：
  python3 scripts/schedule_planner.py next 7            # 排出未来7天计划
  python3 scripts/schedule_planner.py next 7 --save     # 保存排期到 references/schedule_plan.json
  python3 scripts/schedule_planner.py show              # 查看已保存排期
"""
import json
import os
import sys
import glob
from datetime import datetime, timedelta

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(BASE_PATH, "references")

WEEKDAY_STRATEGY = {
    0: {"name": "周一", "themes": {"人情世故": 2, "亲戚": 2, "同事": 1}},
    1: {"name": "周二", "themes": {"人情世故": 2, "职场": 1}},
    2: {"name": "周三", "themes": {"轻松幽默": 2, "反转": 2, "有温度": 1}},
    3: {"name": "周四", "themes": {"轻松幽默": 2}},
    4: {"name": "周五", "themes": {"轻松幽默": 2, "周末期待": 1}},
    5: {"name": "周六", "themes": {"人情世故": 2, "亲戚": 2, "家庭日常": 1, "情感共鸣": 1}},
    6: {"name": "周日", "themes": {"轻松幽默": 2, "家庭日常": 1, "周末期待": 1, "人情世故": 1}},
}

def theme_tags(d):
    t = d.get("theme", "") or ""
    tags = set()
    for k in ["工资", "收入", "人情世故", "亲戚", "35", "外卖", "吃饭", "家庭", "亲情",
              "职场", "通勤", "地铁", "省钱", "国庆", "同事", "领导", "结婚", "房",
              "妈", "爸", "女友", "小林", "借钱", "同学", "聚会", "加班", "轻松", "幽默",
              "情感", "扎心", "孤独", "日常", "周末", "反转", "温度", "温暖", "健康", "失眠"]:
        if k in t:
            tags.add(k)
    c = d.get("content", "")
    for k in ["外卖", "地铁", "工资", "房租", "同事", "亲戚", "大姑", "爸妈", "小林", "女友", "沙县", "黄焖鸡"]:
        if k in c:
            tags.add(k)
    return tags

def viral_score(content):
    s = 0
    if len(re_find_digits(content)) >= 3: s += 10
    elif len(re_find_digits(content)) >= 1: s += 5
    body = ['心里', '喉咙', '鼻子', '手心', '胃', '眼睛', '愣', '沉默', '发紧', '酸', '凉', '堵']
    if any(w in content for w in body): s += 10
    if '35' in content: s += 5
    if content.rstrip().endswith(('吗？', '呢？', '吧？', '？')): s += 10
    if '说' in content or '道' in content: s += 5
    return s

def re_find_digits(content):
    import re
    return re.findall(r'\d+', content)

def load_pending():
    items = []
    for p in glob.glob(os.path.join(LIB, "day*.json")):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("status") == "pending":
            items.append(d)
    return items

def build_plan(days=7, start_date=None):
    items = load_pending()
    start_date = start_date or datetime.now()
    used_ids = set()
    used_themes_chain = []  # 记录最近3条题材，避免连续
    plan = []

    for offset in range(days):
        day = (start_date + timedelta(days=offset)).weekday()
        strategy = WEEKDAY_STRATEGY[day]
        date_str = (start_date + timedelta(days=offset)).strftime("%Y-%m-%d %A")

        # 对每个待选内容打分：星期匹配 + 爆款基因 - 题材连续惩罚
        scored = []
        for d in items:
            if d["id"] in used_ids:
                continue
            tags = theme_tags(d)
            week_match = sum(w for t, w in strategy["themes"].items() if any(tag in t for tag in tags))
            # 题材连续惩罚：如果该题材在最近2条出现过，扣分
            continuity_penalty = 0
            for recent in used_themes_chain[-2:]:
                if recent and tags & recent:
                    continuity_penalty += 8
            total = week_match * 3 + viral_score(d.get("content", "")) - continuity_penalty
            scored.append((total, d))

        if not scored:
            break
        scored.sort(key=lambda x: -x[0])
        best_score, best = scored[0]

        plan.append({
            "date": date_str,
            "weekday": strategy["name"],
            "content_id": best["id"],
            "theme": best.get("theme", ""),
            "score": round(best_score, 1),
            "length": best.get("content_length", 0),
        })
        used_ids.add(best["id"])
        used_themes_chain.append(theme_tags(best))
        if len(used_themes_chain) > 5:
            used_themes_chain.pop(0)

    return plan

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "next"
    if cmd == "next":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        plan = build_plan(days)
        print(f"📅 未来 {len(plan)} 天发布计划（智能排期：星期策略+爆款基因-题材连续惩罚）\n")
        print(f"{'日期':<22}{'星期':<6}{'内容ID':<14}{'得分':<6}{'题材'}")
        print("-" * 70)
        for p in plan:
            print(f"{p['date']:<22}{p['weekday']:<6}{p['content_id']:<14}{p['score']:<6}{p['theme'][:30]}")

        if "--save" in sys.argv:
            out = {"created": datetime.now().strftime("%Y-%m-%d %H:%M"), "plan": plan}
            with open(os.path.join(BASE_PATH, "references/schedule_plan.json"), "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 已保存到 references/schedule_plan.json")

        # 题材多样性统计
        from collections import Counter
        themes = Counter()
        for p in plan:
            t = p["theme"]
            for k in ["工资", "人情世故", "35", "外卖", "职场", "家庭", "省钱", "幽默"]:
                if k in t:
                    themes[k] += 1
                    break
            else:
                themes["其他"] += 1
        print(f"\n题材分布: " + " | ".join(f"{k}:{v}" for k, v in themes.most_common()))

    elif cmd == "show":
        path = os.path.join(BASE_PATH, "references/schedule_plan.json")
        if not os.path.exists(path):
            print("❌ 无已保存排期")
            return
        d = json.load(open(path, encoding="utf-8"))
        print(f"📅 已保存排期（{d['created']}）")
        for p in d["plan"]:
            print(f"  {p['date']} {p['content_id']} [{p['score']}分] {p['theme'][:25]}")

if __name__ == "__main__":
    main()
