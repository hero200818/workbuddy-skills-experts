#!/usr/bin/env python3
"""修复 day57 冲突：恢复工资3条到 day57，回填13条移到 day59-60"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(BASE, "references")

# 1. 恢复工资3条（原文来自生成器输出，13500已统一为14200）
salary_items = [
    {"n": 1, "theme": "工资/收入", "title": "发工资后算账（续集1）",
     "content": "今天算了算账，这个月花了2500，工资就剩3200了。坐在工位上，我盯着记账软件发了半天呆。这个月还得吃饭通勤，我算了算，一天最多花50，不然月底肯定透支。35岁了，工资从5千涨到14200，存款还是没多少。不是不想存，是真存不下来。你们说，这日子怎么就过成了这样？"},
    {"n": 2, "theme": "工资/收入", "title": "发工资后算账（续集2）",
     "content": "今天算了算账，这个月花了3000，工资就剩1500了。坐在工位上，我盯着记账软件发了半天呆。35岁了，工资从5千涨到14200，存款还是没多少。不是不想存，是真存不下来。这个月还得吃饭通勤，我算了算，一天最多花50，不然月底肯定透支。你们发工资第几天开始吃土？"},
    {"n": 3, "theme": "工资/收入", "title": "发工资后交房租（续集3）",
     "content": "工资到手14200，交完房租3800，给家里2000，女朋友生日又花了3000。剩下3200，我看着余额，手心有点凉。我在北京10年，工资从3千涨到14200，可房租从800涨到3800，物价翻了一倍，存款还是那点。不是我抠，是真没办法。你们呢？"},
]

for it in salary_items:
    rec = {
        "id": f"P01_d57_n{it['n']}",
        "day": 57,
        "number": it["n"],
        "title": it["title"],
        "theme": it["theme"],
        "hook_type": "评论钩子",
        "image_suggestion": "暖色调氛围感图片",
        "content": it["content"],
        "content_length": len(it["content"]),
        "status": "pending",
        "deep_version_version": "3.0",
        "created_at": "2026-10-21",
        "auto_generated": True,
        "structure": "冲突-发展-留白三段式",
        "note": "发工资爆款99.8万展现续集·工资主题（best_theme）"
    }
    with open(os.path.join(LIB, f"day57_num{it['n']}.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 恢复 {rec['id']}（工资续集，待发布）")

# 2. 移动 day57_num4~13 → day59_num1~10 + day60_num1~3
moved = []
for src_n, (dst_day, dst_n) in enumerate(
    [(59, i) for i in range(1, 11)] + [(60, i) for i in range(1, 4)], start=4):
    src = os.path.join(LIB, f"day57_num{src_n}.json")
    if not os.path.exists(src):
        continue
    with open(src, encoding="utf-8") as f:
        rec = json.load(f)
    rec["id"] = f"P01_d{dst_day:02d}_n{dst_n}"
    rec["day"] = dst_day
    rec["number"] = dst_n
    dst = os.path.join(LIB, f"day{dst_day:02d}_num{dst_n}.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    os.remove(src)
    moved.append(f"{rec['id']} ← day57_num{src_n}")
    print(f"  ✅ 移动 day57_num{src_n} → {rec['id']}")

print(f"\n✅ 修复完成：工资3条在 day57，回填{len(moved)}条在 day59-60")
