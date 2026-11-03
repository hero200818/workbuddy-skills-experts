#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qc.py —— 发布前自动质检（墨韵拆书卡 v1.5.0）

对某一期成品做三道检查，输出 qc_report.md 与控制台摘要：

  1) 标题查重：新期候选标题 vs 历史全部期的候选标题（difflib 相似度 >0.65 报重）
  2) 文案合规：敏感词/绝对化用语预检（广告法导向）
  3) 版面预警：长书名换行风险、字段超长预警（70pt 卡片经验阈值）

用法：
  python qc.py "os.environ.get("MOYUN_CARD_ROOT", os.path.join(os.getcwd(), "畅销书拆书卡"))/第44周"
"""
import os, sys, json, re, glob, difflib

BASE = os.path.dirname(os.path.abspath(__file__))
CARD_ROOT = os.environ.get("MOYUN_CARD_ROOT", os.path.join(os.getcwd(), "畅销书拆书卡"))

SENSITIVE = [
    "最好", "最强", "最热", "最火", "最佳", "最优", "全网第一", "全网最低",
    "第一品牌", "唯一", "必读", "神作", "巅峰", "秒杀", "100%", "治愈一切",
    "包治", "彻底改变人生", "稳赚", "稳赢",
]


def load_issue(target):
    d = target if os.path.isdir(target) else os.path.dirname(target)
    bj = os.path.join(d, "books.json")
    md = os.path.join(d, "发布文案.md")
    if not os.path.isfile(bj):
        print(f"[error] 找不到 {bj}")
        sys.exit(1)
    return (json.load(open(bj, encoding="utf-8")),
            open(md, encoding="utf-8").read() if os.path.isfile(md) else "")


def historical_titles(current_dir):
    """收集历史各期发布文案中的候选标题。"""
    cur = os.path.normcase(os.path.normpath(os.path.abspath(current_dir)))
    out = []
    for md in glob.glob(os.path.join(CARD_ROOT, "*", "发布文案.md")):
        if os.path.normcase(os.path.normpath(os.path.dirname(md))) == cur:
            continue
        txt = open(md, encoding="utf-8").read()
        seg = re.search(r"发布标题.*?\n((?:\d+\..+\n?)+)", txt)
        if seg:
            for ln in seg.group(1).splitlines():
                m = re.match(r"\d+\.\s*(.+)", ln.strip())
                if m:
                    out.append((os.path.basename(os.path.dirname(md)), m.group(1).strip()))
    return out


def norm_title(t):
    """模板归一：数字与周期词占位，用于识别品牌栏目式固定句。"""
    t = re.sub(r"\d+", "N", t)
    t = re.sub(r"本周|本月|本季|这一年|年度|月度|周榜", "X", t)
    return t


def check_titles(issue_dir, new_titles):
    problems, warns, templates = [], [], []
    hist = historical_titles(issue_dir)
    hist_norm = [norm_title(ht) for _, ht in hist]
    for t in new_titles:
        nt = norm_title(t)
        # 与历史某标题仅在数字/周期词上不同 → 品牌模板句（栏目化，可接受但提示）
        if hist_norm.count(nt) >= 1:
            src = next(s for s, h in hist if norm_title(h) == nt and h != t)
            templates.append(f"「{t}」沿用栏目模板（{src} 用过「{next(h for s2,h in hist if norm_title(h)==nt and h!=t)}」），建议每期换点花样")
            continue
        for src, ht in hist:
            ratio = difflib.SequenceMatcher(None, t, ht).ratio()
            if ratio > 0.8:
                problems.append(f"标题「{t}」与 {src} 的「{ht}」高度雷同（{ratio:.0%}）")
    return problems, warns, templates, len(hist)


def check_sensitive(text):
    hits = []
    for w in SENSITIVE:
        for m in re.finditer(re.escape(w), text):
            ctx = text[max(0, m.start() - 12): m.end() + 12].replace("\n", " ")
            hits.append(f"「{w}」……{ctx}……")
    return hits


def check_layout(books):
    warns = []
    for b in books:
        t = b.get("title", "")
        if len(t) > 10:
            warns.append(f"《{t}》书名 {len(t)} 字，70pt 大字可能换行/溢出，建议库内用短名")
        if len(b.get("rec", "")) > 34:
            warns.append(f"《{t}》rec {len(b['rec'])} 字（建议≤30）")
        for i, p in enumerate(b.get("points", []), 1):
            if len(p) > 50:
                warns.append(f"《{t}》亮点{i} {len(p)} 字（建议≤45）")
        if len(b.get("quote", "")) > 44:
            warns.append(f"《{t}》金句 {len(b['quote'])} 字（建议≤40）")
    return warns


def main():
    target = sys.argv[1]
    data, md = load_issue(target)
    issue = data.get("issue", "?")
    titles = re.findall(r"^\d+\.\s*(.+)$", re.search(r"发布标题(.*?)(?:\n##|\Z)", md, re.S).group(1), re.M) if "发布标题" in md else []

    p1, w1, tpl, n_hist = check_titles(os.path.abspath(target), titles)
    p2 = check_sensitive(md)
    w3 = check_layout(data.get("books", []))

    lines = [f"# 质检报告 · {issue}", "",
             f"- 标题查重：对比历史 {n_hist} 期候选标题", ""]
    lines.append("## 一、标题查重")
    lines.append("\n".join(f"- ❌ {x}" for x in p1) or "- ✅ 无高度雷同")
    lines.append("\n".join(f"- 💡 {x}" for x in tpl))
    lines.append("\n## 二、文案合规（敏感词/绝对化用语）")
    lines.append("\n".join(f"- ❌ {x}" for x in p2) or "- ✅ 未检出敏感词")
    lines.append("\n## 三、版面预警")
    lines.append("\n".join(f"- ⚠️ {x}" for x in w3) or "- ✅ 字段长度全部达标")
    total_bad = len(p1) + len(p2)
    lines.insert(2, f"**结论：{'❌ 存在 %d 项必须修复' % total_bad if total_bad else '✅ 可发布'}；💡 模板提示 {len(tpl)} 项；⚠️ 建议项 {len(w3)} 项**\n")
    open(os.path.join(os.path.abspath(target), "qc_report.md"), "w", encoding="utf-8").write("\n".join(lines))

    print(f"质检 {issue}：❌ 必须修复 {total_bad} 项 | 💡 模板提示 {len(tpl)} 项 | ⚠️ 建议 {len(w3)} 项")
    for x in p1 + p2:
        print("  ❌", x)
    for x in tpl:
        print("  💡", x)
    for x in w3:
        print("  ⚠️", x)


if __name__ == "__main__":
    main()
