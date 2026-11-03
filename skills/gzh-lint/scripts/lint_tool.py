#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lint_tool.py — 公众号文章合规 + 结构自检（独立分发版，零项目依赖）

与 gzh.py 的 `lint` 同名能力保持一致，但自包含、可独立运行：
    python lint_tool.py --md 稿件.md
    python lint_tool.py --md 稿件.md --channel yanxu --json

设计要点
- 零第三方依赖，纯标准库；不 import 任何项目文件。
- 规则默认读取与项目流水线「共用」的 rules/lint_rules.json（单一真相源）；
  找不到时回退内嵌的 DEFAULT_RULES（覆盖微信通用合规 + 去 AI 味），保证离线可用。
- 配置（limits）内嵌默认值，可用 --config 指向一份 JSON 覆盖。
- 双通道标题上限：言序 30 字 / 微信 64 字；封面 ≤2MB、正文 ≤1MB（体积核查见 assets 工具）。

返回码：命中 error 级 → 1；否则 0（warn 不影响退出码，但会列出）。
"""
import argparse
import json
import os
import re
import sys

# ══════════════════ 默认配置（可被 --config 覆盖）════════════════
DEFAULT_CONFIG = {
    "limits": {
        "title_yanxu": 30,
        "title_wechat": 64,
        "abstract": 120,
        "abstract_yanxu": 100,
        "cover_kb": 2000,
        "body_kb": 1000,
        "body_chars_min": 1200,
        "body_chars_max": 2000,
        "head_max": 130,
        "para_soft": 120,
        "para_hard": 160,
        "imgs_min": 3,
        "imgs_max": 5,
        "emoji_max": 8,
    },
    "assets": {"cover_pattern": "cover|封面"},
}

# 规则是公共知识（微信《运营规范》等），不含任何账号敏感信息。
# 内嵌一份完整默认，保证离线可用；优先用项目 rules/lint_rules.json 覆盖。
DEFAULT_RULES = {
    "negation_context": "一眼假|谣言|不实|辟谣|假的|别信|不能信|所谓|号称|声称|宣称|误区|骗人|忽悠|智商税|打着.{0,6}旗号|标题党|传说|网传|据说",
    "rules": [
        {"cat": "涉政红线", "sev": "error", "pattern": "台独|港独|藏独|疆独|法轮功|邪教|六四|颜色革命|群体性事件|政变|游行示威|上访|打砸抢", "advice": "涉政/涉稳一律不写，删掉整段", "basis": "运营规范4.12"},
        {"cat": "诱导分享", "sev": "error", "pattern": "不转不是|转发本文|集赞|分享后(?:继续|才能)看|求扩散|请转发|点在看|赞赏后可见", "advice": "删掉整句。引导关注可以，诱导分享不行", "basis": "运营规范3.3"},
        {"cat": "紧迫诱导", "sev": "error", "pattern": "速看|紧急(?:通知|扩散)|马上删|不看后悔|删前|最后一天|再不看就|抓紧时间", "advice": "标题党『煽动蛊惑类』，必须删", "basis": "标题党专项治理"},
        {"cat": "疗效断言", "sev": "error", "pattern": "治百病|根治|药到病除|抗癌|防癌|排毒|包治|立竿见影|三天见效|降血压|降血糖|增强免疫力|提高免疫力", "advice": "健康类只写生活方式提醒，不下疗效结论", "basis": "运营规范4.11.3"},
        {"cat": "隐私号段", "sev": "error", "pattern": "\\d{11}\\b|\\d{17}[\\dXx]\\b", "advice": "疑似手机号/身份证号，必须脱敏", "basis": "运营规范4.1"},
        {"cat": "绝对化用语", "sev": "warn", "pattern": "最(?:好|佳|强|有效|便宜|大)|第一名|唯一|100%|绝对|永久|史上最", "advice": "广告法风险，改限定表述", "basis": "广告法第九条"},
        {"cat": "混淆官方", "sev": "warn", "pattern": "官方通报|权威发布|官方(?:刚刚|紧急)|国务院通知|央视曝光|内部消息", "advice": "非官方不得模仿官方口吻", "basis": "标题党专项治理"},
        {"cat": "未证实爆料", "sev": "warn", "pattern": "网传|据传|听说|知情人(?:士)?透露|内部人士|小道消息", "advice": "转述必须交代来源与『未证实』，否则按谣言风险处理", "basis": "运营规范4.9", "negation_ok": True},
        {"cat": "金融荐股", "sev": "warn", "pattern": "荐股|必涨|翻倍|抄底|牛市来了|稳赚|带你买|建仓", "advice": "无证券投顾资质不得给投资建议", "basis": "证券法/广告法"},
        {"cat": "违规导流", "sev": "warn", "pattern": "扫码(?:关注|进群|加)|加(?:我)?微信|私信我领|回复.{0,4}领取", "advice": "公众号内不得引导站外，删掉", "basis": "运营规范"},
        {"cat": "正文外链", "sev": "warn", "pattern": "https?://", "advice": "公众号正文外链不可点、易被判导流；改为『文末留言区』或删", "basis": "运营规范"},
        {"cat": "虚假承诺", "sev": "warn", "pattern": "包过|稳赚|必中|零风险|稳赚不赔", "advice": "虚假承诺，删", "basis": "运营规范4.11"},
        {"cat": "AI味·套话", "sev": "warn", "pattern": "在这个.{0,6}的时代|不得不说|总而言之|综上所述|让我们一起|值得注意的是|众所周知|随着.{0,8}的发展|不难发现", "advice": "去AI味：删套话，直接进场景", "basis": "账号调性"},
        {"cat": "AI味·黑话", "sev": "warn", "pattern": "赋能|闭环|底层逻辑|抓手|颗粒度|对齐一下|组合拳|护城河|顶层设计|痛点|赛道", "advice": "去AI味：换成人话", "basis": "账号调性"},
        {"cat": "AI味·排比", "sev": "warn", "pattern": "既是.{0,12}也是|不仅.{0,16}更是|从.{0,10}到.{0,10}再到", "advice": "AI味排比堆砌，全文留一处即够", "basis": "账号调性"},
    ],
}

EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
SEV_ICON = {"error": "\u2717", "warn": "\u25b3", "info": "\u00b7"}


# ══════════════════════════ 通用小工具 ══════════════════════════

def _read_md(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _split_body(md):
    """正文 = 第一个单独成行的 --- 之前（之后是运营配套，不进正文）"""
    lines = md.split("\n")
    body = []
    for ln in lines:
        if ln.strip() == "---" and body:
            break
        body.append(ln)
    return body


def _extract_title(body):
    for ln in body:
        t = ln.strip()
        if t.startswith("# "):
            return t[2:].strip()
    return ""


def _norm(s):
    s = re.sub(r"\s+", "", s or "")
    for a, b in (("\u201c", '"'), ("\u201d", '"'), ("\u2018", "'"), ("\u2019", "'")):
        s = s.replace(a, b)
    return s


def _negated(line, hit, neg):
    i = line.find(hit)
    if i < 0:
        return False
    return bool(neg.search(line[max(0, i - 40): i + len(hit) + 40]))


# ══════════════════════════ 配置与规则加载 ══════════════════════════

def load_config(path=None):
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    if path and os.path.exists(path):
        try:
            user = json.load(open(path, encoding="utf-8"))
            if isinstance(user.get("limits"), dict):
                cfg["limits"].update(user["limits"])
            if isinstance(user.get("assets"), dict):
                cfg["assets"].update(user["assets"])
        except Exception as e:
            print(f"\u26a0\ufe0f config 读取失败，用默认值：{e}")
    return cfg


def load_rules(path=None):
    """优先：显式 --rules > 当前目录/脚本目录的 rules/lint_rules.json > 内嵌默认。"""
    candidates = []
    if path:
        candidates = [path]
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(os.getcwd(), "rules", "lint_rules.json"),
            os.path.join(here, "rules", "lint_rules.json"),
            os.path.join(here, "..", "rules", "lint_rules.json"),
            os.path.join(here, "..", "..", "rules", "lint_rules.json"),
        ]
    raw = None
    for c in candidates:
        if c and os.path.exists(c):
            try:
                raw = json.load(open(c, encoding="utf-8"))
                break
            except Exception:
                raw = None
    if raw is None:
        raw = DEFAULT_RULES
    compiled = []
    for r in raw.get("rules", []):
        try:
            compiled.append((r["cat"], r.get("sev", "warn"), re.compile(r["pattern"]),
                             r.get("advice", ""), bool(r.get("negation_ok"))))
        except re.error:
            continue
    neg = re.compile(raw.get("negation_context") or "\u4e00\u773c\u5047")
    return compiled, neg


# ══════════════════════════ lint 核心（纯函数）══════════════════════════

def collect_findings(md_text, title=None, channel=None, cfg=None, rules=None, neg=None):
    """返回 (findings, stats)。findings 每项 = (sev, cat, line, hit, advice)"""
    cfg = cfg or DEFAULT_CONFIG
    if rules is None:
        rules, neg = load_rules()
    neg = neg or re.compile("\u4e00\u773c\u5047")
    lim = cfg["limits"]
    channel = channel or "wechat"
    body = _split_body(md_text)
    body_text = "\n".join(body)
    title = title or _extract_title(body)
    findings = []

    # ── 标题 ──
    n = len(title)
    limit = lim["title_yanxu"] if channel == "yanxu" else lim["title_wechat"]
    if n == 0:
        findings.append(("error", "标题", 0, "未找到标题", "正文首行需为 `# 标题`"))
    elif n > limit:
        findings.append(("error", "标题长度", 0, f"{n} 字 / 上限 {limit}",
                         f"{channel} 通道上限 {limit} 字，超 {n - limit} 字"
                         + ("（言序直发会发不进去）" if channel == "yanxu" else "，需精简")))
    elif channel == "wechat" and n > lim["title_yanxu"]:
        findings.append(("warn", "标题长度", 0, f"{n} 字",
                         f"微信端够用，但改走言序需压到 {lim['title_yanxu']} 字内"))
    if title and re.search(r"[\u3010\u3011\[\]]|\u2026{2,}|!!!|\uff1f\uff1f", title):
        findings.append(("warn", "标题符号", 0, title[:20] + "\u2026",
                         "方括号/省略号/叹号堆叠属标题党『对抗类』，建议去掉"))

    # ── 逐行扫规则 ──
    for idx, ln in enumerate(body, 1):
        line = ln.strip()
        if not line or line.startswith("!["):
            continue
        for cat, sev, pat, advice, neg_ok in rules:
            m = pat.search(line)
            if not m:
                continue
            if (sev == "error" or neg_ok) and _negated(line, m.group(0), neg):
                findings.append(("info", cat + "\u00b7引用语境", idx, m.group(0),
                                 "命中词处于否定/引用句，确认是在举反例即可忽略"))
                continue
            findings.append((sev, cat, idx, m.group(0), advice))

    # ── 结构 ──
    paras = [l.strip() for l in body
             if l.strip() and not l.strip().startswith(("#", "![", ">", "---", "|"))]
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", body_text)
    chars = sum(len(p) for p in paras)

    if paras:
        head = len(paras[0])
        if head > lim["head_max"]:
            findings.append(("warn", "结构\u00b7首段", 1, f"首段 {head} 字",
                             f"手机端前 3 行决定划走率，首段建议 ≤{lim['head_max']} 字"))
        long_p = [(i, len(p)) for i, p in enumerate(paras, 1) if len(p) > lim["para_hard"]]
        if long_p:
            findings.append(("warn", "结构\u00b7长段", 0,
                             f"{len(long_p)} 段超 {lim['para_hard']} 字（最长 {max(x[1] for x in long_p)} 字）",
                             f"移动端单段建议 ≤{lim['para_soft']} 字，拆段"))
        if chars < lim["body_chars_min"]:
            findings.append(("warn", "结构\u00b7篇幅", 0, f"{chars} 字",
                             f"低于 {lim['body_chars_min']} 字，读感偏薄"))
        elif chars > lim["body_chars_max"]:
            findings.append(("warn", "结构\u00b7篇幅", 0, f"{chars} 字",
                             f"超过 {lim['body_chars_max']} 字，完读率风险"))
    if not any(p.rstrip().endswith(("\uff1f", "?")) for p in paras[-5:]):
        findings.append(("info", "结构\u00b7评论钩子", 0, "结尾 5 段无问句",
                         "若以评论为 KPI，结尾要抛一个具体问题"))
    if len(imgs) < lim["imgs_min"]:
        findings.append(("warn", "结构\u00b7配图", 0, f"{len(imgs)} 张",
                         f"建议 {lim['imgs_min']}\u2013{lim['imgs_max']} 张"))
    elif len(imgs) > lim["imgs_max"]:
        findings.append(("warn", "结构\u00b7配图", 0, f"{len(imgs)} 张",
                         f"超过 {lim['imgs_max']} 张，读者会疲"))
    emo = len(EMOJI_RE.findall(body_text))
    if emo > lim["emoji_max"]:
        findings.append(("warn", "结构\u00b7表情", 0, f"{emo} 个 emoji", "公众号正文表情过多显轻浮"))

    stats = {"title": title, "title_len": n, "limit": limit, "channel": channel,
             "paras": len(paras), "chars": chars, "imgs": len(imgs)}
    return findings, stats


def _print_findings(findings, stats, fname):
    errors = [f for f in findings if f[0] == "error"]
    warns = [f for f in findings if f[0] == "warn"]
    print("=" * 62)
    print(f"合规+结构自检  {os.path.basename(fname)}")
    print("=" * 62)
    print(f"通道  {stats['channel']}（标题上限 {stats['limit']} 字）")
    print(f"标题  {stats['title_len']} 字：{stats['title']}")
    print(f"正文  {stats['paras']} 段 / {stats['chars']} 字 / {stats['imgs']} 张图")
    print(f"结果  {'\u2717 不合格' if errors else ('\u25b3 待优化' if warns else '\u2713 通过')}"
          f"   （error {len(errors)} / warn {len(warns)}）")
    print("-" * 62)
    if not findings:
        print("\u2713 未命中任何规则。人工仍需过一遍事实与信源。")
    for sev, cat, ln, snip, advice in sorted(findings, key=lambda x: (x[0] != "error", x[2])):
        loc = f"L{ln}" if ln else ("标题" if cat.startswith("标题") else "全文")
        print(f"{SEV_ICON[sev]} [{cat}] {loc}  \u00ab{snip}\u00bb")
        print(f"    \u2192 {advice}")
    print("-" * 62)
    print("提示：脚本只查『可机检』项；涉企/涉政/未证实信息、原创资质需人工判定。")


def cmd_lint(args):
    cfg = load_config(args.config)
    rules, neg = load_rules(args.rules)
    findings, stats = collect_findings(_read_md(args.md), args.title, args.channel, cfg, rules, neg)
    _print_findings(findings, stats, args.md)
    if args.json:
        print(json.dumps([{"sev": s, "cat": c, "line": l, "hit": h, "advice": a}
                          for s, c, l, h, a in findings], ensure_ascii=False, indent=1))
    return 1 if any(f[0] == "error" for f in findings) else 0


# ══════════════════════════ 内置自测（移植 gzh.py 关键用例）══════════════════════════

def _selftest():
    T = "35岁怕优化，60岁怕负担：你笑\"老登\"的底气，还没轮到你"
    cases = [
        ("紧迫诱导应报 error", f"# {T}\n\n正文。\n\n不看后悔，速看。\n", "紧迫诱导"),
        ("诱导分享应报 error", f"# {T}\n\n正文。\n\n不转不是中国人。\n", "诱导分享"),
        ("疗效断言应报 error", f"# {T}\n\n正文。\n\n这个东西能治百病。\n", "疗效断言"),
        ("手机号应报 error", f"# {T}\n\n正文。\n\n联系我 {"138" + "1234" + "5678"} 。\n", "隐私号段"),
        ("辟谣引用不判 error", f"# {T}\n\n正文。\n\n转发\"空腹吃苹果治百病\"那种一眼假的文章。\n", "疗效断言·引用语境"),
        ("涉政应报 error", f"# {T}\n\n正文。\n\n网上在传某地发生了群体性事件。\n", "涉政红线"),
        ("超 30 字标题应报 error",
         "# " + "这是一条特别特别特别特别特别长的标题它一定超过三十个字了吧真的超了" + "\n\n正文。\n",
         "标题长度"),
        ("干净稿不应有 error",
         f"# {T}\n\n" + "\n\n".join(["前两天刷到个视频，两个小伙子在地铁上聊天。"] * 40) +
         "\n\n![图](配图/cover_clean.jpg)\n\n![图](配图/body1_subway_clean.jpg)\n\n"
         "![图](配图/body2_warm_clean.jpg)\n\n你第一次觉得父母老了，是哪个瞬间？\n",
         "无 error"),
    ]
    ok = fail = 0
    print("=" * 62)
    print("lint_tool 自测")
    print("=" * 62)
    for name, md, expect in cases:
        findings, _ = collect_findings(md, None, "yanxu")
        cats = {f[1] for f in findings}
        errs = [f for f in findings if f[0] == "error"]
        if expect == "无 error":
            good = not errs
        else:
            good = expect in cats and (expect.endswith("引用语境") or bool(errs))
        print(f"{'\u2713' if good else '\u2717'} {name}  → 命中 {sorted(cats) or '无'}")
        ok, fail = (ok + 1, fail) if good else (ok, fail + 1)
    # 通道默认与规则条数
    rules, _ = load_rules()
    good = len(rules) >= 10
    print(f"{'\u2713' if good else '\u2717'} 规则已编译（{len(rules)} 条 ≥10）")
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)
    print("-" * 62)
    print(f"{'\u2713 全部通过' if not fail else f'\u2717 {fail} 项失败'}   （{ok} passed / {fail} failed）")
    return 1 if fail else 0


# ══════════════════════════ 入口 ══════════════════════════

def main():
    ap = argparse.ArgumentParser(description="公众号文章合规+结构自检（独立版）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("lint", help="合规+结构自检")
    p.add_argument("--md", required=True)
    p.add_argument("--title")
    p.add_argument("--channel", choices=["yanxu", "wechat"], default="wechat")
    p.add_argument("--config", help="limits 覆盖 JSON（可选）")
    p.add_argument("--rules", help="规则文件 JSON（默认优先读 rules/lint_rules.json）")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("selftest", help="内置用例自测")
    p.set_defaults(func=lambda a: _selftest())

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
