#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
expert.py —— 三端全能运营专家引擎（墨韵拆书卡 v1.8.0）

系统从「出内容」进化为「懂运营」：内置三端（微信视频号图文/头条微头条/小红书）
平台规则知识库 platforms.json，能针对任意一端的具体要求输出定制方案。

能力：
  规范  <平台>            查询某端运营规范（微信/头条/小红书/all）
  适配  <期目录> --platform 微信|头条|小红书|all
                          按端规则深度适配：发布方案+话题策略+封面建议+互动钩子+违禁预检
  复盘  <期目录> --data 数据.json
                          按端数据基准给出复盘建议（阅读/互动/收藏）
  排期                    输出三端一周发布排期建议

示例：
  python expert.py 规范 小红书
  python expert.py 适配 "C:/.../2024年度" --platform all
  python expert.py 排期
"""
import os, sys, json, re, glob, argparse
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
RULES = json.load(open(os.path.join(BASE, "platforms.json"), encoding="utf-8"))

ALIAS = {"微信": "weixin", "视频号": "weixin", "weixin": "weixin",
         "头条": "toutiao", "微头条": "toutiao", "toutiao": "toutiao",
         "小红书": "xhs", "xhs": "xhs", "all": "all"}

SENSITIVE_BASE = ["最好", "最强", "最热", "最火", "第一品牌", "全网第一", "唯一", "必读", "神作", "秒杀", "100%"]


def norm(t):
    return re.sub(r"[^\w\u4e00-\u9fff]", "", str(t).lower())


def load_issue(target):
    d = target if os.path.isdir(target) else os.path.dirname(os.path.abspath(target))
    return json.load(open(os.path.join(d, "books.json"), encoding="utf-8")), d


def cmd_rules(platform):
    keys = list(RULES) if platform == "all" else [platform]
    for k in keys:
        r = RULES[k]
        h = r["hard_rules"]
        print(f"\n══ {r['name']}（{r['nickname']}）══")
        print(f" 定位：{r['positioning']}")
        print(f" 硬规则：标题≤{h['title_max'] or '无'}字 | 图片≤{h['image_max']}张({h['image_ratio']}) | {h['desc_limit']}")
        print(f" 话题格式：{h['topic_format']}")
        print(f" 黄金时间：{' / '.join(r['best_time'])}")
        print(f" 风格：{r['style']}")
        print(f" 红线：{'；'.join(r['taboos'])}")
        print(f" 封面：{r['cover_rule']}")
        print(f" 互动：{r['interaction']}")
        print(f" 数据基准：{r['metrics']['good']}（核心指标：{r['metrics']['core']}）")
        print(f" 节奏：{r['cadence']}")


def precheck(text, platform):
    """按端违禁红线预检。"""
    r = RULES[platform]
    bad = [w for w in SENSITIVE_BASE if w in text]
    extra = [w for w in ("加V", "私信我", "微信号", "扫码") if w in text] if platform == "xhs" else []
    return bad + extra


def cmd_adapt(target, platform):
    keys = list(RULES) if platform == "all" else [platform]
    data, d = load_issue(target)
    books, issue, kind = data["books"], data.get("issue", ""), data.get("kind", "weekly")
    n = len(books)
    out_lines = [f"# 三端适配方案 · {issue}", ""]

    for k in keys:
        r = RULES[k]
        h = r["hard_rules"]
        t1, t2 = books[0]["title"], books[1]["title"] if n > 1 else books[0]["title"]
        q1 = (books[0].get("quote") or "").rstrip("。")
        q1 = (q1[:10] + "…") if len(q1) > 10 else q1
        when = {"weekly": "本周", "monthly": "本月", "annual": "这一年"}.get(kind, "本期")

        titles_by_platform = {
            "weixin": [f"{when}书单｜{n}本热销拆透", f"《{t1}》凭什么刷屏全网", f"{n}本好书，一张卡读懂"],
            "toutiao": [f"{when}书单来了！这{n}本被全网买爆", f"{n}本书读完，我最推荐《{t1}》", f"别乱买书：{when}最值得读的{n}本"],
            "xhs": [f"🔥{when}书单｜{n}本闭眼入", f"救命！这{n}本也太好读了", f"{n}张卡3分钟读懂{n}本书"],
        }[k]
        titles_by_platform = [t[:h["title_max"]] if h["title_max"] else t for t in titles_by_platform]

        topics = {
            "weixin": f"#拆书 #畅销书 #书单推荐 #{t1}",
            "toutiao": f"#书单推荐# #读书# #畅销书# #-{t1}#".replace("#-", "#"),
            "xhs": " ".join(["#书单推荐", "#读书博主", "#拆书", f"#{t1}", "#好书分享", "#阅读打卡", "#个人成长"][:10]),
        }[k]
        topics = " ".join(topics.split()[:10 if k == "xhs" else (6 if k == "weixin" else 4)])

        cover = {
            "weixin": r["cover_rule"].split("：")[1].split("，")[0] if "：" in r["cover_rule"] else "封面图",
            "toutiao": f"首图用 {sorted(glob.glob(os.path.join(d, '0[1-9]_*.jpg')))[0] if glob.glob(os.path.join(d, '0[1-9]_*.jpg')) else '01_书卡'}（信息量大的书卡）",
            "xhs": "首图建议做大字报封面：大号数字「8」+「本月书单」+痛点词，书卡做内页",
        }[k]

        hook = {
            "weixin": f"结尾一句：「想先读哪本？评论区告诉我。」（微信端不做诱导，克制即风格）",
            "toutiao": f"结尾必留二选一：「《{t1}》和《{t2}》只能带一本上荒岛，你选哪本？」（评论区互动决定二次推荐）",
            "xhs": f"结尾引导收藏：「先收藏，慢慢读。」（收藏权重最高）",
        }[k]

        out_lines += [f"## {r['name']}（{r['nickname']}）", "",
                      f"**发布时间建议**：{' / '.join(r['best_time'])}",
                      f"**标题候选（均≤{h['title_max'] or '无'}字，已过违禁预检）**："]
        for t in titles_by_platform:
            bad = precheck(t, k)
            out_lines.append(f"- {t}" + (f"　[❌含违禁:{','.join(bad)}]" if bad else "　[✅]"))
        out_lines += ["", f"**话题策略**：{topics}", f"**封面建议**：{cover}", f"**互动钩子**：{hook}",
                      f"**数据基准**：{r['metrics']['good']}（核心：{r['metrics']['core']}）", ""]
        full_text = open(os.path.join(d, "发布文案.md"), encoding="utf-8").read() if os.path.isfile(os.path.join(d, "发布文案.md")) else ""
        if full_text:
            bad_all = precheck(full_text, k)
            if bad_all:
                out_lines.append(f"- ⚠️ 该端红线预检命中：{','.join(set(bad_all))}（改用「热度领先」「口碑前列」等表述）")
        out_lines.append("")

    out = os.path.join(d, "三端适配方案.md")
    open(out, "w", encoding="utf-8").write("\n".join(out_lines))
    print(f"✅ 三端适配方案 → {out}")
    print(f"   覆盖：{'、'.join(RULES[k]['nickname'] for k in keys)}")


def cmd_review(target, data_path):
    data, d = load_issue(target)
    rev = json.load(open(data_path, encoding="utf-8"))
    out_lines = [f"# 三端数据复盘建议 · {data.get('issue','')}", ""]
    for plat_key, alias in [("weixin", "微信"), ("toutiao", "头条"), ("xhs", "小红书")]:
        r = RULES[plat_key]
        got = rev.get(alias) or rev.get(r["nickname"]) or {}
        views, likes, fav = got.get("views", 0), got.get("likes", 0), got.get("favorites", got.get("collects", 0))
        out_lines.append(f"## {r['nickname']}（实际：阅读 {views} / 点赞 {likes} / 收藏 {fav}）")
        if not views:
            out_lines.append("- 暂无数据：发布 72 小时后录入即可复盘。\n")
            continue
        rate = likes / max(views, 1) * 100
        out_lines.append(f"- 互动率 {rate:.2f}%（基准：{r['metrics']['good']}）")
        if plat_key == "weixin":
            out_lines.append("- 建议：" + ("转发达标，书卷气路线有效，保持节律。" if rate >= 3 else "转发偏低：下次标题换「悬念式」，并把最有共鸣的金句前置到描述第一行。"))
        elif plat_key == "toutiao":
            out_lines.append("- 建议：" + ("互动达标，二选一钩子有效。" if rate >= 0.5 else "评论偏低：下条把投票钩子放第一句，正文中段再补一次提问。"))
        else:
            out_lines.append("- 建议：" + ("收藏达标，利他清单感有效。" if fav / max(views, 1) * 100 >= 8 else "收藏偏低：首图改大字报（数字+痛点词），正文加「完整书单见评论区」引导收藏。"))
        out_lines.append("")
    out = os.path.join(d, "三端复盘建议.md")
    open(out, "w", encoding="utf-8").write("\n".join(out_lines))
    print(f"✅ 复盘建议 → {out}")


def cmd_schedule():
    today = datetime.now()
    plan = []
    for i in range(7):
        d = today + timedelta(days=i)
        wd = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][d.weekday()]
        items = []
        if wd == "周一":
            items.append("🤖 微信端正刊（自动出版 09:30 → 12:00 发布）")
            items.append("📕 小红书正刊（19:00-23:00 发布）")
        if wd in ("周三", "周六"):
            items.append("🗣 头条微头条互动钩子（二选一投票，18:00-21:00）")
        if wd == "周六":
            items.append("🔍 小红书长尾笔记（搜索关键词：书单/治愈/成长）")
        plan.append((d.strftime("%m-%d") + " " + wd, items))
    print("== 三端一周发布排期建议 ==")
    for day, items in plan:
        print(f"  {day}: " + ("；".join(items) if items else "休息/机动（可与读者互动）"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["规范", "适配", "复盘", "排期"])
    ap.add_argument("target", nargs="?", help="期目录（适配/复盘用）")
    ap.add_argument("--platform", default="all")
    ap.add_argument("--data", help="复盘数据 json")
    a = ap.parse_args()
    if a.cmd == "规范":
        plat = ALIAS.get((a.target or "").strip(), "all")
    else:
        plat = ALIAS.get(a.platform, "all")

    if a.cmd == "规范":
        cmd_rules(plat)
    elif a.cmd == "适配":
        if not a.target:
            print("适配需要期目录"); sys.exit(2)
        cmd_adapt(a.target, plat)
    elif a.cmd == "复盘":
        if not (a.target and a.data):
            print("复盘需要期目录与 --data 数据.json"); sys.exit(2)
        cmd_review(a.target, a.data)
    elif a.cmd == "排期":
        cmd_schedule()


if __name__ == "__main__":
    main()
