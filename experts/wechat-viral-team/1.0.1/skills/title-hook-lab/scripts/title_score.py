#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""title_score.py — 公众号标题评测器（纯标准库，零依赖）

为什么不靠"我觉得这个标题挺好"：
  · 言序通道标题硬上限 30 字，草稿箱不给你改的机会
  · 微信 64 字，但超过 30 字在信息流里会被截断，读者看不到后半句钩子
  · "震惊/速看/必看"这类词不进推荐池，还可能被判标题党扣权
  · 好标题的结构能被拆出来：具体 + 钩子 + 情绪 + 不越线

用法：
    python title_score.py "标题一" "标题二" "标题三"
    python title_score.py --file 候选标题.txt          # 每行一条
    python title_score.py --channel wechat "标题"      # 微信原生编辑器口径 ≤64
    python title_score.py --json "标题"                # 机器可读

输出：每条标题的字数、钩子类型、五维得分、总分与结论、一条可执行的改法。
"""

import sys
import re
import json
import argparse

# ── 词表（可增补，加词即可，不用改逻辑）────────────────────────────────

# 年龄 / 身份标签：读者一眼认出"这说的是我"
IDENTITY = [
    "35岁", "40岁", "45岁", "50岁", "60岁", "70岁", "80后", "90后", "00后",
    "中年人", "老年人", "老人", "大爷", "大妈", "老头", "老太太",
    "打工人", "上班族", "宝妈", "全职妈妈", "应届生", "毕业生", "实习生",
    "程序员", "老师", "护士", "医生", "外卖员", "快递员", "司机", "网约车",
    "房东", "租客", "业主", "业主群", "保安", "保洁", "店员", "客服",
    "父母", "爸妈", "父亲", "母亲", "孩子", "独生女", "独生子", "小镇青年",
    "老板", "领导", "甲方", "乙方", "HR", "退休", "打工", "职工", "农民",
]

# 反差 / 转折：一句话里出现两种相反的处境
CONTRAST = ["但", "却", "反而", "其实", "原来", "没想到", "结果", "偏偏",
            "不是", "而是", "一边", "另一边", "以为", "谁知", "竟然", "居然"]

# 疑问 / 反问：让读者想开口
QUESTION = ["？", "?", "为什么", "凭什么", "怎么", "难道", "是不是", "谁", "多少",
            "要不要", "该不该", "能不能", "为啥"]

# 悬念 / 信息缺口：留一个必读的理由
SUSPENSE = ["真相", "原因", "答案", "没人告诉", "才知道", "揭秘", "背后",
            "后来", "下场", "代价", "潜规则", "内幕", "细节", "到底",
            "还没", "轮到", "迟早", "早晚", "等着", "有一天", "多久", "最后"]

# 利益 / 钱：能算账的标题转发率最高
BENEFIT = ["省", "多收", "少收", "涨价", "降价", "免费", "退钱", "赔偿", "罚款",
           "亏", "赚", "多少钱", "一个月", "一年", "块", "元", "工资", "房租",
           "押金", "账单", "扣费", "收费", "计费", "补贴", "报销"]

# 情绪张力：委屈、不服、荒诞、温情
EMOTION = ["委屈", "不服", "气", "笑", "哭", "心疼", "扎心", "难受", "离谱",
           "荒诞", "傲慢", "体面", "尊严", "底气", "寒心", "无奈", "心酸",
           "温柔", "暖", "破防", "尴尬", "丢人", "看不起", "高攀", "嫌弃"]

# 诱导 / 标题党：直接扣分，微信侧有被判低质的风险
CLICKBAIT = ["震惊", "速看", "速转", "紧急", "必看", "删前", "疯传", "炸了",
             "惊呆", "吓人", "太可怕", "不看后悔", "赶紧", "马上", "立刻",
             "史上最", "全网最", "第一", "唯一", "百分百", "绝对", "包治"]

# 绝对化 / 疗效：广告法与医疗合规红线
ABSOLUTE = ["根治", "治愈", "药到病除", "永不", "永久", "彻底解决", "零风险"]

# 具体性素材：数字、地名机构、具象物
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:岁|年|个月|天|小时|分钟|秒|块|元|万|亿|%|倍|次|条|张|杯|趟|公里|米|斤|人|单)")
ORG_WORDS = ["人民日报", "央视", "新华社", "法院", "检察院", "市监", "卫健委",
             "教育局", "住建局", "发改委", "民政", "工会", "消协", "12345",
             "地铁", "公交", "高铁", "医院", "学校", "物业", "平台", "公司"]
PLACE_WORDS = ["北京", "上海", "广州", "深圳", "杭州", "成都", "重庆", "武汉",
               "西安", "南京", "苏州", "长沙", "郑州", "合肥", "济南", "青岛",
               "东北", "县城", "农村", "小区", "商场", "写字楼", "医院", "地铁站"]
CONCRETE = ["停车", "外卖", "奶茶", "婚宴", "红包", "彩礼", "简历", "工位",
            "出租屋", "菜市场", "医院", "电梯", "楼道", "公交", "地铁", "饭桌",
            "酒桌", "病房", "养老院", "幼儿园", "家长群", "业主群", "相亲",
            "体检", "药", "盒饭", "快递", "账单", "手机", "短剧", "直播间"]

LIMITS = {"yanxu": 30, "wechat": 64}


def _hits(text, words):
    return [w for w in words if w in text]


def analyze(title, channel="yanxu"):
    t = title.strip()
    limit = LIMITS.get(channel, 30)
    n = len(re.sub(r"\s", "", t))

    # 1) 长度：16 到上限之间最好；太短没信息，太长会被截断
    if 16 <= n <= limit:
        length = 10
    elif 12 <= n < 16 or limit < n <= limit + 4:
        length = 7
    elif 8 <= n < 12 or limit + 4 < n <= limit + 12:
        length = 4
    else:
        length = 2

    # 2) 具体性：数字、机构、地名、具象物 —— 越具体越可信、越像真事
    nums = NUMBER_RE.findall(t)
    orgs = _hits(t, ORG_WORDS)
    places = _hits(t, PLACE_WORDS)
    things = _hits(t, CONCRETE)
    specific = min(10, 2 + len(nums) * 2 + len(orgs) * 2 + len(places) + len(things) * 1.5)
    specific = int(round(specific))

    # 3) 钩子结构：类型越多越立体（单一类型容易被同类标题淹没）
    hooks = {}
    if nums or re.search(r"\d", t):
        hooks["数字"] = "有具体数字，可信度高"
    if _hits(t, IDENTITY):
        hooks["身份"] = "对上了具体人群：" + "/".join(_hits(t, IDENTITY)[:3])
    if _hits(t, CONTRAST):
        hooks["反差"] = "有转折：" + "/".join(_hits(t, CONTRAST)[:3])
    if _hits(t, QUESTION):
        hooks["疑问"] = "抛了问题，逼读者想回答"
    if _hits(t, SUSPENSE):
        hooks["悬念"] = "留了信息缺口：" + "/".join(_hits(t, SUSPENSE)[:3])
    if _hits(t, BENEFIT):
        hooks["利益"] = "能算账：" + "/".join(_hits(t, BENEFIT)[:3])
    hook = min(10, len(hooks) * 2.5 + (1 if len(hooks) >= 3 else 0))

    # 4) 情绪张力
    emo = _hits(t, EMOTION)
    emotion = min(10, 2 + len(emo) * 2.5)

    # 5) 风险：诱导词、绝对化、标点滥用
    bait = _hits(t, CLICKBAIT)
    abso = _hits(t, ABSOLUTE)
    punct_hit = len(re.findall(r"[!！]{2,}|[?？]{2,}|[.。]{3,}", t))
    risk = max(0, 10 - len(bait) * 4 - len(abso) * 5 - punct_hit * 3)

    total = round((length * 0.15 + specific * 0.30 + hook * 0.30
                   + emotion * 0.15 + risk * 0.10) * 10, 1)

    if total >= 80:
        verdict = "优"
    elif total >= 70:
        verdict = "可用"
    elif total >= 55:
        verdict = "偏弱"
    else:
        verdict = "不宜"

    # 一条具体建议：补最弱的那一维
    parts = {"长度": length, "具体": specific, "钩子": hook,
             "情绪": emotion, "风险": (10 if risk >= 8 else risk)}
    weakest = min(parts, key=lambda k: parts[k])
    harness_hook = hook
    advice = {
        "长度": f"字数 {n}，不在 16–{limit} 的甜区；砍到 20 字上下，或补半句信息",
        "具体": "缺具体锚点（数字/地名/机构/具象物），读者不信；补一个可核对的细节",
        "钩子": ("结构太单一，只有一种钩子；加一层反差或数字，让标题有转折"
                 if harness_hook <= 2.5 else
                 "已有两种钩子，再加一层反差（却/反而）或利益（多少钱）会更立体"),
        "情绪": "读不出情绪，像通知不像人话；加一个能让人心里一动的词",
        "风险": "踩了诱导词或绝对化表述，可能被判标题党；换成陈述事实的说法",
    }[weakest]

    return {
        "title": t,
        "chars": n,
        "channel": channel,
        "limit": limit,
        "scores": {"length": length, "specific": specific,
                   "hooks": round(hook, 1), "emotion": round(emotion, 1),
                   "risk": risk},
        "hook_types": list(hooks.keys()),
        "hook_detail": hooks,
        "found": {"number": nums, "org": orgs, "place": places,
                  "concrete": things, "emotion": emo,
                  "clickbait": bait, "absolute": abso},
        "total": total,
        "verdict": verdict,
        "advice": advice,
    }


def print_one(idx, r):
    print(f"{idx}) {r['title']}")
    flag = "⚠️ 超长" if r["chars"] > r["limit"] else "✓"
    print(f"   {r['chars']} 字 / 上限 {r['limit']} {flag}   "
          f"总分 {r['total']}  {r['verdict']}")
    if r["hook_types"]:
        print(f"   钩子 {len(r['hook_types'])} 类：" + " · ".join(r["hook_types"]))
    s = r["scores"]
    print(f"   长度 {s['length']} / 具体 {s['specific']} / 钩子 {s['hooks']} "
          f"/ 情绪 {s['emotion']} / 风险 {s['risk']}")
    bad = r["found"]["clickbait"] + r["found"]["absolute"]
    if bad:
        print(f"   ⚠️ 风险词：{'/'.join(bad)}")
    print(f"   → {r['advice']}")
    print()


def selftest():
    """自检：改词表或权重后必须跑，否则规则可能静默失效。"""
    cases = []

    r = analyze("35岁怕优化，60岁怕负担：你笑\"老登\"的底气，还没轮到你")
    cases.append(("好标题应 ≥75 分", r["total"] >= 75, f"{r['total']} 分"))

    r = analyze("震惊！速看！不看后悔！！")
    cases.append(("标题党应 <50 分且风险 ≤4", r["total"] < 50 and r["scores"]["risk"] <= 4,
                  f"{r['total']} 分 / 风险 {r['scores']['risk']}"))

    long_t = "这是一条特别特别长的标题用来测试字数上限是否会被正确识别出来超过三十个字的情况"
    r = analyze(long_t)
    cases.append(("超 30 字应报超长", r["chars"] > r["limit"], f"{r['chars']} 字"))

    r = analyze("停车64分钟按2小时收费，人民日报点名多地改按分钟计费")
    cases.append(("带数字+机构+具象物应具体性 ≥8", r["scores"]["specific"] >= 8,
                  f"具体 {r['scores']['specific']}"))

    r = analyze("这条标题写得很长很长超过六十四个字的情况需要按微信通道来检查是否会被判定为超长标题从而无法直接粘贴到公众号后台的标题框里面去", "wechat")
    cases.append(("微信通道上限应为 64", r["limit"] == 64, f"上限 {r['limit']}"))

    ok = 0
    for name, good, detail in cases:
        print(f"{'✓' if good else '✗'} {name}（{detail}）")
        ok += 1 if good else 0
    print(f"\n{ok} passed / {len(cases) - ok} failed")
    return 0 if ok == len(cases) else 1


def main():
    ap = argparse.ArgumentParser(description="公众号标题评测器")
    ap.add_argument("titles", nargs="*", help="候选标题，可给多条横向比较")
    ap.add_argument("--file", help="从文本文件读候选标题（每行一条）")
    ap.add_argument("--channel", choices=["yanxu", "wechat"], default="yanxu",
                    help="yanxu=言序/草稿箱 ≤30 字；wechat=微信原生 ≤64 字")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--selftest", action="store_true", help="自检词表与权重是否仍生效")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    titles = list(args.titles)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            titles += [ln.strip() for ln in f
                       if ln.strip() and not ln.strip().startswith("#")]
    if not titles:
        ap.error("至少给一条标题，或用 --file 指定文件")

    results = [analyze(t, args.channel) for t in titles]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=1))
        return 0

    print(f"标题评测 · {len(results)} 条 · 通道 {args.channel}"
          f"（上限 {LIMITS[args.channel]} 字）")
    print("-" * 66)
    for i, r in enumerate(results, 1):
        print_one(i, r)

    if len(results) > 1:
        rank = sorted(range(len(results)), key=lambda i: -results[i]["total"])
        print("排序（高分在前）：")
        for pos, i in enumerate(rank, 1):
            print(f"  {pos}. {results[i]['total']:>5}  {results[i]['verdict']}  "
                  f"{results[i]['title'][:26]}")
        best = results[rank[0]]
        over = [r for r in results if r["chars"] > r["limit"]]
        if over:
            print(f"\n⚠️ {len(over)} 条超出 {LIMITS[args.channel]} 字，发不出去，"
                  f"必须改长度")
        print(f"\n建议主推：{best['title']}（{best['total']} 分）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
