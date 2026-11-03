#!/usr/bin/env python3
"""
智能选稿器 v1.0 - 根据星期/时段/粉丝画像/爆款基因，自动从内容库挑选最优稿件
用法：
  python3 scripts/smart_selector.py next            # 推荐下一条（按当天星期智能选）
  python3 scripts/smart_selector.py next --day 3    # 指定星期（0=周日）
  python3 scripts/smart_selector.py next --slot evening  # 指定时段
  python3 scripts/smart_selector.py analyze          # 分析待发布池匹配度
"""
import json
import os
import sys
import glob
import re
from datetime import datetime
from collections import Counter

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(BASE_PATH, "references")

# ===== 星期题材策略（大数据验证，Python weekday(): 周一=0 ... 周日=6）=====
# themes 支持权重：{"题材": 权重}，默认权重1；权重越高的题材匹配时加分越多
WEEKDAY_STRATEGY = {
    0: {"name": "周一", "themes": {"人情世故": 2, "亲戚": 2, "同事": 1}, "desc": "周一：人情世故/亲戚/同事优先"},
    1: {"name": "周二", "themes": {"人情世故": 2, "职场": 1}, "desc": "周二：人情世故+职场"},
    2: {"name": "周三", "themes": {"轻松幽默": 2, "反转": 2, "有温度": 1}, "desc": "周三重点发力日！轻松幽默+反转+温度最易爆"},
    3: {"name": "周四", "themes": {"轻松幽默": 2}, "desc": "周四：轻松幽默"},
    4: {"name": "周五", "themes": {"轻松幽默": 2, "周末期待": 1}, "desc": "周五：轻松幽默+周末期待"},
    5: {"name": "周六", "themes": {"人情世故": 2, "亲戚": 2, "家庭日常": 1, "情感共鸣": 2, "北漂": 1}, "desc": "周六：周末家庭/情感场景多"},
    6: {"name": "周日", "themes": {"轻松幽默": 2, "家庭日常": 1, "周末期待": 1, "人情世故": 1, "情感共鸣": 1, "北漂": 1}, "desc": "周日：周末尾声，轻松+家庭向"},
}

# ===== 时段策略 =====
SLOT_STRATEGY = {
    "morning":   {"themes": {"通勤": 2, "地铁": 2, "早餐": 1, "上班": 1}, "desc": "早高峰碎片阅读"},
    "noon":      {"themes": {"外卖": 2, "午餐": 2, "午休": 1, "摸鱼": 1, "轻松": 1}, "desc": "午休下饭共鸣"},
    "evening":   {"themes": {"情感": 2, "感悟": 2, "扎心": 2, "日常": 1, "工资": 1, "人情世故": 1, "家庭": 1}, "desc": "晚间情绪敏感，共鸣最高"},
}

# ===== 爆款基因评分 =====
def viral_score(content):
    """按爆款基因给内容打分（0-40分）+ 评论潜力分（0-30分）"""
    s = 0
    # 3+数字
    nums = len(re.findall(r'\d+', content))
    if nums >= 3: s += 10
    elif nums >= 1: s += 5
    # 生理反应
    body = ['心里', '喉咙', '鼻子', '手心', '胃', '眼睛', '愣', '沉默', '发紧', '酸', '凉', '堵']
    if any(w in content for w in body): s += 10
    # 35岁锚点
    if '35' in content or '35岁' in content: s += 5
    # 结尾提问
    if content.rstrip().endswith(('吗？', '呢？', '吧？', '？')): s += 10
    # 对话感
    if '说' in content or '道' in content: s += 5
    return s

def comment_potential_score(content):
    """评论潜力分（0-30分）：评估内容引发评论的能力（钩子硬→评论多→互动好→展现高）"""
    c = content.rstrip()
    s = 0
    # ① 结尾钩子类型（5大钩子：吐槽/共鸣/好奇/利益/悬念反差）
    if c.endswith(('你们遇到过', '你们说', '你们有没有', '你们猜', '你们公司', '你们身边')):
        s += 10  # 吐槽/共鸣类钩子（给读者开口机会）
    elif c.endswith(('你们呢', '你们也是吗', '你们家也这样', '你们也这样吗')):
        s += 8   # 共鸣类钩子（"这说的就是我"）
    elif c.endswith(('吗？', '？')):
        s += 5   # 一般提问
    # ② 冲突/反转（评论的燃料）
    if any(w in content for w in ['居然', '反转', '没想到', '结果', '愣住', '最后', '却']):
        s += 7
    # ③ 一句话对话（读者可接话）
    if '说' in content and '说：' in content:
        s += 5
    elif '说' in content:
        s += 3
    # ④ 数字对比（评论区算账党最爱）
    nums = re.findall(r'\d+', content)
    if len(nums) >= 4:
        s += 5
    # ⑤ 身份反差（引发站队）
    if any(w in content for w in ['别人', '人家', '同事', '亲戚', '同龄人']):
        s += 3
    return min(s, 30)

def theme_tags(d):
    """从主题字段+tags字段提取标签用于匹配"""
    t = d.get("theme", "") or ""
    tags = []
    # 读取显式 tags 字段（优先）
    for tag in d.get("tags", []) or []:
        tags.append(tag)
    for k in ["工资", "收入", "人情世故", "亲戚", "35", "外卖", "吃饭", "家庭", "亲情",
              "职场", "通勤", "地铁", "省钱", "国庆", "同事", "领导", "结婚", "房",
              "妈", "爸", "女友", "小林", "借钱", "同学", "聚会", "加班", "轻松", "幽默",
              "情感", "扎心", "孤独", "日常", "周末", "反转", "温度", "温暖", "健康", "失眠",
              "北漂", "感悟", "共鸣", "自嘲"]:
        if k in t:
            tags.append(k)
    # 基因型→题材映射（新爆款基因入库内容的 theme 是基因名，需要映射到选稿题材）
    gene_theme_map = {
        '发工资算账型': ['工资', '扎心'],
        '外卖共情型': ['外卖', '温暖'],
        '亲戚求助型': ['人情世故', '亲戚'],
        '国庆账单型': ['国庆', '工资', '扎心'],
        '职场对比型': ['职场', '对比', '扎心'],
        '家庭细节型': ['家庭', '情感', '温暖'],
        '情绪反差型': ['情感', '自嘲', '扎心'],
    }
    for gene_name, gene_tags in gene_theme_map.items():
        if gene_name in t:
            tags.extend(gene_tags)
    # 内容关键词补充
    c = d.get("content", "")
    for k in ["外卖", "地铁", "工资", "房租", "同事", "亲戚", "大姑", "爸妈", "小林", "女友", "沙县", "黄焖鸡"]:
        if k in c:
            tags.append(k)
    return set(tags)

def load_pending():
    items = []
    for p in glob.glob(os.path.join(LIB, "day*.json")):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("status") == "pending":
            items.append(d)
    return items

def pick(day=None, slot=None, exclude=None, count=3):
    """按策略挑出最匹配的N条"""
    items = load_pending()
    if exclude:
        items = [d for d in items if d["id"] not in exclude]

    if day is None:
        day = datetime.now().weekday()
    strategy = WEEKDAY_STRATEGY.get(day, WEEKDAY_STRATEGY[0])
    slot_info = SLOT_STRATEGY.get(slot, {"themes": {}})

    scored = []
    for d in items:
        tags = theme_tags(d)
        week_match = 0
        slot_match = 0
        for t, w in strategy["themes"].items():
            if any(tag in t for tag in tags):
                week_match += w
        for t, w in slot_info["themes"].items():
            if any(tag in t for tag in tags):
                slot_match += w
        # 综合：星期策略优先(权重3) + 时段策略(权重1.5) + 爆款基因分 + 评论潜力分
        total = week_match * 3 + slot_match * 1.5 + viral_score(d.get("content", "")) + comment_potential_score(d.get("content", ""))
        scored.append((total, d))

    scored.sort(key=lambda x: -x[0])
    return strategy, slot_info, scored[:count]

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "next"
    args = sys.argv[2:]

    if cmd == "next":
        day = None
        slot = None
        exclude = None
        if "--day" in args:
            day = int(args[args.index("--day") + 1])
        if "--slot" in args:
            slot = args[args.index("--slot") + 1]
        if "--exclude" in args:
            exclude = [x.strip() for x in args[args.index("--exclude") + 1].split(",")]
        strategy, slot_info, top = pick(day=day, slot=slot, exclude=exclude)

        print(f"📅 {'星期' + strategy['name']} | 策略: {strategy['desc']}")
        if slot:
            print(f"⏰ 时段[{slot}]: {slot_info['desc']}")
        print(f"\n🏆 推荐（按爆款基因+策略匹配排序）:\n")
        for i, (score, d) in enumerate(top[:3], 1):
            print(f"  #{i} [{score}分] {d['id']} | {d.get('theme','')}")
            print(f"     {d.get('content','')[:70]}...")
            print(f"     [字数{len(d.get('content',''))} | 钩子:{'✅' if d.get('content','').rstrip().endswith(('吗？','呢？','吧？','？')) else '❌'}]\n")

    elif cmd == "analyze":
        items = load_pending()
        print(f"待发布: {len(items)}条")
        print(f"\n爆款基因分布（40分制）:")
        scores = [viral_score(d.get("content", "")) for d in items]
        buckets = {"30-40分(爆款相)": 0, "20-29分(良好)": 0, "10-19分(一般)": 0, "0-9分(待优化)": 0}
        for s in scores:
            if s >= 30: buckets["30-40分(爆款相)"] += 1
            elif s >= 20: buckets["20-29分(良好)"] += 1
            elif s >= 10: buckets["10-19分(一般)"] += 1
            else: buckets["0-9分(待优化)"] += 1
        for k, v in buckets.items():
            bar = "█" * (v // 2)
            print(f"  {k}: {v}条 {bar}")
        print(f"\n平均爆款基因分: {sum(scores)/len(scores):.1f}/40")
        # 各星期策略匹配率
        print(f"\n各星期题材策略覆盖率:")
        for day, st in WEEKDAY_STRATEGY.items():
            matched = sum(1 for d in items if any(tag in t for t in st["themes"] for tag in theme_tags(d)))
            print(f"  {st['name']}: {matched}/{len(items)} ({matched/len(items)*100:.0f}%)")

if __name__ == "__main__":
    main()
