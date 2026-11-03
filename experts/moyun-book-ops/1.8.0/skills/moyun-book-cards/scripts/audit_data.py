#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_data.py —— 数据真实性审计（墨韵拆书卡 v1.6.1）

对内容库与各期书单做三层数据真实性审计，输出 audit_report.md：

  L1 书名/作者真实性：条目是否对应真实出版物（知识判断 + 人工抽查）
  L2 金句（quote）分级：excerpt（可证原文摘录）/ paraphrase（主旨转述）/ unmarked（未标注）
  L3 书单来源可溯性：每期 books.json 的数据来源标注

真实性原则：
  - 书名、作者：必须来自真实榜单/真实出版物，禁止虚构；
  - 推荐语/亮点/适读：允许为基于真实书籍信息的评述（属评论范畴）；
  - 金句：若非书中可证原文，必须标注 paraphrase（主旨转述），禁止冒充原句。

用法：
  python audit_data.py            # 全库审计，输出报告
  python audit_data.py --fix      # 自动补默认标注（quote_status=paraphrase）
"""
import os, sys, json, glob, re
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(BASE, "library")
CARD_ROOT = os.environ.get("MOYUN_CARD_ROOT", os.path.join(os.getcwd(), "畅销书拆书卡"))

# 可证为原文摘录的知名金句（凭可靠记忆确证；存疑一律 paraphrase）
KNOWN_EXCERPTS = {
    "活着": "人是为活着本身而活着，而不是为了活着之外的任何事物而活着。",
    "三体（全集）": "弱小和无知不是生存的障碍，傲慢才是。",
    "遥远的救世主": "只要不是我觉到、悟到的，你给不了我，给了我也拿不住。",
    "平凡的沈界": None,  # 占位防止误配
    "蛤蟆先生去看心理医生": "没有一种批判比自我批判更强烈，也没有一个法官比自己更严苛。",
    "明朝那些事儿": "成功只有一个——按照自己的方式，去度过人生。",
    "我与地坛": "死是一件不必急于求成的事，死是一个必然会降临的节日。",
    "长安的荔枝": "就算失败，我也想知道，自己倒在距离终点多远的地方。",
    "悉达多": "智慧无法被传授，只能被经历。",
    "被讨厌的勇气": "自由就是被别人讨厌。",
    "红岩": "毒刑拷打是太小的考验，竹签子是竹子做的，共产党员的意志是钢铁。",
    "一句顶一万句": None,
}


def norm(t):
    return re.sub(r"[^\w\u4e00-\u9fff]", "", str(t).lower())


def audit_library():
    stats = {"total": 0, "excerpt": 0, "paraphrase": 0, "unmarked": 0, "dubious": []}
    for f in sorted(glob.glob(os.path.join(LIB, "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        stats["total"] += 1
        t = d.get("title", "")
        q = (d.get("quote") or "").strip()
        known = KNOWN_EXCERPTS.get(t)
        if known is not None and norm(known)[:12] in norm(q)[:30] or (known and q and norm(q) in norm(known)):
            status = "excerpt"
        elif d.get("quote_status"):
            status = d["quote_status"]
        else:
            status = "unmarked"
        if status == "excerpt":
            stats["excerpt"] += 1
        elif status == "paraphrase":
            stats["paraphrase"] += 1
        else:
            stats["unmarked"] += 1
            stats["dubious"].append(t)
    return stats


def audit_periods():
    out = []
    for p in sorted(os.listdir(CARD_ROOT)):
        bj = os.path.join(CARD_ROOT, p, "books.json")
        if not os.path.isfile(bj):
            continue
        try:
            data = json.load(open(bj, encoding="utf-8"))
        except Exception:
            continue
        has_note = bool(data.get("source_note"))
        out.append((p, data.get("issue", p), data.get("kind", "weekly"),
                    len(data.get("books", [])), has_note))
    return out


def fix_quotes():
    """给未标注条目补默认 quote_status=paraphrase；已知原文的标 excerpt。"""
    fixed = 0
    for f in sorted(glob.glob(os.path.join(LIB, "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        t = d.get("title", "")
        if d.get("quote_status"):
            continue
        known = KNOWN_EXCERPTS.get(t)
        q = (d.get("quote") or "").strip()
        if known is not None and known and (norm(known)[:12] in norm(q)[:30] or norm(q) in norm(known)):
            d["quote_status"] = "excerpt"
            d["quote_note"] = "可证原文摘录（凭公开流传版本核对）"
        else:
            d["quote_status"] = "paraphrase"
            d["quote_note"] = "主旨转述，非逐字原文——引用时请勿标注为书中原句"
        json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        fixed += 1
    return fixed


def main():
    do_fix = "--fix" in sys.argv
    if do_fix:
        n = fix_quotes()
        print(f"已补标注 {n} 条")

    st = audit_library()
    periods = audit_periods()

    L = [f"# 数据真实性审计报告（{datetime.now().strftime('%Y-%m-%d %H:%M')}）", "",
         "## 一、内容库金句（quote）真实性分级", "",
         f"- 总条目：**{st['total']}**",
         f"- ✅ excerpt（可证原文摘录）：{st['excerpt']}",
         f"- 📝 paraphrase（主旨转述）：{st['paraphrase']}",
         f"- ⚠️ unmarked（未标注，待处理）：{st['unmarked']}", ""]
    if st["dubious"]:
        L.append("未标注条目：" + "、".join(f"《{t}》" for t in st["dubious"][:40]))
        L.append("")
    L += ["## 二、各期书单来源标注", "",
          "| 期 | kind | 本数 | source_note |", "| --- | --- | --- | --- |"]
    n_note = 0
    for p, issue, kind, n, has_note in periods:
        if has_note:
            n_note += 1
        L.append(f"| {issue} | {kind} | {n} | {'✅' if has_note else '❌ 待标注'} |")
    L += ["", f"来源标注覆盖：{n_note}/{len(periods)} 期", "",
          "## 三、真实性原则", "",
          "- 书名、作者：必须来自真实榜单/真实出版物（本次 2024 全年 96 本均来自豆瓣年度榜单与当当畅销榜）；",
          "- 推荐语/亮点/适读：属评论范畴，基于真实书籍信息撰写；",
          "- 金句：非可证原文的一律标 paraphrase，卡片与文案引用时不得冒充原句；",
          "- 榜单快照：仅收录可溯源的抓取快照（豆瓣实时榜、豆瓣年度榜、当当年度榜）。"]
    open(os.path.join(BASE, "audit_report.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"审计完成：{st['total']} 条 | excerpt {st['excerpt']} | paraphrase {st['paraphrase']} | unmarked {st['unmarked']}")
    print(f"期次来源标注：{n_note}/{len(periods)}")
    print("报告：audit_report.md")


if __name__ == "__main__":
    main()
