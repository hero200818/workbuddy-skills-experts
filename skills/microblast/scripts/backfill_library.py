#!/usr/bin/env python3
"""回填后台实际发布内容到内容库（统一管理历史发布）"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(BASE, "references")

# 后台实际发布·无内容库ID的高价值内容（来源：头条号后台作品管理 2026-10-21 抓取）
# content 字段：有完整原文的用原文；无原文的写标题摘要并标注"正文见后台"（不编造）
items = [
    {"n": 1,  "date": "2026-08-26", "theme": "35岁/扎心", "title": "地铁叫叔叔", "metrics": {"views": 2887, "comments": 11, "likes": 0},
     "content": "下班地铁上一个小姑娘站起来说叔叔您坐吧，我说我才35不是老人。小姑娘脸一红说对不起我看您头发白了以为您年纪大了。我笑了笑说没事你坐吧。扶着扶手看玻璃里的倒影鬓角有几根白头发。35岁在小姑娘眼里已经是叔叔了。我妈说你爸35岁时你都10岁了。35岁还在挤地铁被人叫叔叔。你们第一次被叫叔叔阿姨是什么时候？"},
    {"n": 2,  "date": "2026-09-01", "theme": "职场/工资", "title": "时薪28对比外卖员", "metrics": {"views": 3816, "comments": 0, "likes": 0},
     "content": "发工资那天又算账：月薪除 22 天除 10 小时，时薪 28。楼下常给我送餐的那哥们随口说\"我今天跑了 14 单，挣 300 多\"。我沉默了。我没瞧不起他，我是瞧不起自己——读了四年书，坐办公室吹空调，时薪被风吹雨淋的兄弟吊打。还不敢辞职，因为我有房租、有花呗、有不敢病。有没有同款，越算越觉得自己\"白读了\"的？"},
    {"n": 3,  "date": "2026-09-01", "theme": "职场/扎心", "title": "秒回领导", "metrics": {"views": 4864, "comments": 0, "likes": 3},
     "content": "（后台实际发布内容，正文见头条号后台作品管理）标题：秒回领导"},
    {"n": 4,  "date": "2026-09-01", "theme": "职场/工资", "title": "工资三年没动", "metrics": {"views": 6086, "comments": 0, "likes": 2},
     "content": "（后台实际发布内容，正文见头条号后台作品管理）标题：工资三年没动"},
    {"n": 5,  "date": "2026-10-03", "theme": "国庆/人情世故", "title": "国庆婚礼随礼", "metrics": {"views": 102057, "comments": 0, "likes": 1},
     "content": "（后台实际发布内容，正文见头条号后台作品管理）标题：国庆婚礼随礼（10万+展现）"},
    {"n": 6,  "date": "2026-10-03", "theme": "国庆/人情世故", "title": "国庆婚礼·二版", "metrics": {"views": 31870, "comments": 0, "likes": 7},
     "content": "（后台实际发布内容，正文见头条号后台作品管理）标题：国庆婚礼（第二版本，3.2万展现）"},
    {"n": 7,  "date": "2026-10-09", "theme": "国庆/账单", "title": "国庆账单6100", "metrics": {"views": 106573, "comments": 18, "likes": 56},
     "content": "（后台实际发布内容，正文见头条号后台作品管理）标题：国庆账单6100（10.7万展现/1.2万阅读/18评论中型爆款）"},
    {"n": 8,  "date": "2026-10-12", "theme": "35岁/职场", "title": "周一早会叫叔", "metrics": {"views": 3314, "comments": 0, "likes": 0},
     "content": "（后台实际发布内容，正文见头条号后台作品管理）标题：周一早会叫叔"},
    {"n": 9,  "date": "2026-10-13", "theme": "35岁/社交", "title": "同学聚会", "metrics": {"views": 2523, "comments": 0, "likes": 1},
     "content": "今天同学聚会，大家都在聊房子车子孩子。张三买了二套房，李四换了辆宝马，王五孩子上了重点小学。我端着杯子坐在角落，插不上话。有人问我周明你在北京混得怎么样。我说就那样，打工。他说别谦虚了，北京肯定混得好。我笑了笑喝了杯酒。散会我去坐地铁，看着地铁上的人群，突然觉得我们已经不是一个世界的人了。"},
    {"n": 10, "date": "2026-10-14", "theme": "人情世故/借钱", "title": "室友借10万", "metrics": {"views": 6312, "comments": 0, "likes": 3},
     "content": "（后台实际发布内容，正文见头条号后台作品管理）标题：室友借10万（高阅读618）"},
    {"n": 11, "date": "2026-10-14", "theme": "职场/人情世故", "title": "带早餐", "metrics": {"views": 4063, "comments": 3, "likes": 2},
     "content": "（后台实际发布内容，正文见头条号后台作品管理）标题：同事带早餐（评论3）"},
    {"n": 12, "date": "2026-10-16", "theme": "外卖/温度", "title": "沙县老板", "metrics": {"views": 2095, "comments": 0, "likes": 0},
     "content": "（后台实际发布内容，正文见头条号后台作品管理）标题：沙县老板"},
    {"n": 13, "date": "2026-10-18", "theme": "外卖/共情", "title": "外卖迟到", "metrics": {"views": 2728, "comments": 0, "likes": 0},
     "content": "（后台实际发布内容，正文见头条号后台作品管理）标题：外卖迟到（高阅读159）"},
]

os.makedirs(LIB, exist_ok=True)
# 找最大day，避免覆盖
max_day = 56
for fn in os.listdir(LIB):
    if fn.startswith("day") and "_" in fn:
        try:
            d = int(fn.split("_")[1].lstrip("day") if fn.startswith("day") else 0)
            max_day = max(max_day, d)
        except Exception:
            pass

start_day = max_day + 1
count = 0
for it in items:
    day = start_day
    num = it["n"]
    rec = {
        "id": f"P01_d{day:02d}_n{num}",
        "day": day,
        "number": num,
        "title": it["title"],
        "theme": it["theme"],
        "hook_type": "评论钩子",
        "image_suggestion": "暖色调氛围感图片",
        "content": it["content"],
        "content_length": len(it["content"]),
        "status": "published",
        "published_date": it["date"],
        "deep_version_version": "后台回填",
        "created_at": it["date"],
        "auto_generated": False,
        "metrics": it["metrics"],
        "structure": "历史实际发布内容回填",
        "note": "头条号后台实际发布·无内容库ID，2026-10-21补录统一管理"
    }
    path = os.path.join(LIB, f"day{day:02d}_num{num}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    count += 1
    print(f"  ✅ {rec['id']}  {it['date']} {it['theme']:<8} 展现{it['metrics']['views']}")

print(f"\n✅ 回填完成：{count} 条后台实际发布内容已入库（day{start_day}-day{start_day}），状态=published")
