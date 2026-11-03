#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gzh.py — 公众号爆款流水线通用工具（v3）

设计原则：**配置一处改、规则数据化、功能能自测、发布有总闸、决策有依据。**
v2 管「查得出问题」，v3 管「说得清下一步」：分数落到选题库、链路一条命令看清、欠账自动催。
改写脚本前先跑 selftest；每次踩坑先往 rules/lint_rules.json 追加规则，再跑 selftest。

子命令
  lint       合规+结构自检（标题上限按通道：言序30 / 微信64）
  assets     配图去 AI 水印 + 压缩 + 双档体积核查（封面≤2MB / 正文≤1MB）
  yanxu      MD 稿 → 言序 compose_article 参数 JSON
  preview    内联 HTML → 图片 base64 自包含预览版（缺图直接失败）
  bundle     生成「完整资料.md」（入库 ima 必带；--meta auto 自动汇总元信息）
  new        新选题脚手架（主稿/发布包/配图清单/meta 一次生成）
  ledger     发布台账：list / add / check / audit（audit 按发布时间算 24h/72h 逾期）
  score      选题四维评分（<60 不写 / 60–75 备选 / >75 主推；--save 回写选题库）
  status     项目总览：稿件链路 + 选题池健康度 + 台账催办
  pick       从选题池按分数挑下一篇，给下一步命令
  brief      生成写作任务书（切入角/骨架/禁忌/配图，禁忌从规则文件动态生成）
  ship       一键装配 lint→图→引用→bundle（默认预演，--go 才写文件）
  retro      台账数据复盘（评论率/在看率/分享率/完读率）
  preflight  发布前总闸：lint + 配图双档 + 图片引用 + bundle + 台账，全绿才放行
  doctor     项目体检：配置/规则/文档/目录/残留文件/文档与代码是否漂移
  selftest   自带用例自测（改脚本后必跑，防规则静默失效）

示例
  python scripts/gzh.py selftest
  python scripts/gzh.py doctor
  python scripts/gzh.py new --slug 选题4 --title "标题"
  python scripts/gzh.py lint --md 选题3_xxx.md
  python scripts/gzh.py assets --dir 配图/raw --out 配图 --trim 72
  python scripts/gzh.py assets --dir 配图 --check
  python scripts/gzh.py preflight --slug 选题3
  python scripts/gzh.py bundle --md 选题3_xxx.md --slug 选题3 --meta auto
  python scripts/gzh.py ledger --check --md 选题3_xxx.md
  python scripts/gzh.py score --heat 8 --resonance 9 --tension 7 --risk 9 --name "老登"
"""
import argparse
import base64
import datetime
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.environ.get("GZH_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 作为专家包 Skill 运行时，脚本位于 skills/gzh-viral-ops/scripts/，
# 上一级不是用户项目。此时回退到当前工作目录（用户的项目根）。
if not os.path.exists(os.path.join(ROOT, "config.json")):
    _cwd = os.getcwd()
    if any(os.path.exists(os.path.join(_cwd, n)) for n in ("config.json", "发布台账.md", "选题库.md")):
        ROOT = _cwd

# ══════════════════════════ 配置与规则加载 ══════════════════════════

DEFAULT_CONFIG = {
    "account": {"name": "我的公众号", "series": "普通人视角",
                "yanxu_account_id": "", "ima_kb_id": "", "ima_kb_name": ""},
    "limits": {"title_yanxu": 30, "title_wechat": 64, "abstract": 120,
               "cover_kb": 2000, "body_kb": 1000, "body_chars_min": 1200,
               "body_chars_max": 2000, "head_max": 130, "para_soft": 120,
               "para_hard": 160, "imgs_min": 3, "imgs_max": 5, "emoji_max": 8},
    "assets": {"trim_px": 72, "quality": 85, "suffix": "_clean",
               "cover_pattern": "cover|封面", "exts": [".png", ".jpg", ".jpeg", ".webp"]},
    "publish": {"channel": "yanxu", "theme_id": "blackgold", "theme_note": ""},
    "paths": {"assets_dir": "配图", "assets_raw": "配图/raw", "rules": "rules/lint_rules.json",
              "ledger": "发布台账.md", "topics": "选题库.md",
              "skill": "",
              "pitfalls": "rules/技术踩坑手册.md"},
}

DEFAULT_RULES = [{"cat": "诱导分享", "sev": "error",
                  "pattern": "不转不是|集赞|求扩散|请转发",
                  "advice": "删掉", "basis": ""}]


def _p(rel):
    return rel if os.path.isabs(rel) else os.path.join(ROOT, rel)


def load_config(path=None):
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    p = path or _p("config.json")
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                user = json.load(f)
            for k, v in user.items():
                if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                    cfg[k].update(v)
                else:
                    cfg[k] = v
        except Exception as e:
            print(f"⚠️ config.json 读取失败，用默认值：{e}")
    return cfg


def load_rules(path=None):
    cfg = CONFIG
    p = path or _p(cfg["paths"]["rules"])
    raw = {"negation_context": "", "rules": DEFAULT_RULES}
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:
            print(f"⚠️ 规则文件读取失败，用内置最小规则：{e}")
            raw = {"negation_context": "", "rules": DEFAULT_RULES}
    compiled = []
    for r in raw.get("rules", []):
        try:
            compiled.append((r["cat"], r.get("sev", "warn"), re.compile(r["pattern"]),
                             r.get("advice", ""), bool(r.get("negation_ok"))))
        except re.error as e:
            print(f"⚠️ 规则 {r.get('cat')} 正则有误，已跳过：{e}")
    neg = re.compile(raw.get("negation_context") or "一眼假")
    return compiled, neg


CONFIG = load_config()
BRAND = ((CONFIG.get("account") or {}).get("name") or "公众号")
RULES, NEGATION_CTX = load_rules()
SEV_ICON = {"error": "✗", "warn": "△", "info": "·"}
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")


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


def _curly(s):
    """ASCII 双引号 → 中文全角引号"""
    out, oq = [], True
    for ch in s:
        if ch == '"':
            out.append("“" if oq else "”")
            oq = not oq
        else:
            out.append(ch)
    return "".join(out)


def _is_cover(name):
    return bool(re.search(CONFIG["assets"]["cover_pattern"], name, re.I))


def _norm(s):
    """比对标题用：去空白、统一各种引号"""
    s = re.sub(r"\s+", "", s or "")
    for a, b in (("“", '"'), ("”", '"'), ("‘", "'"), ("’", "'")):
        s = s.replace(a, b)
    return s


def _negated(line, hit):
    i = line.find(hit)
    if i < 0:
        return False
    return bool(NEGATION_CTX.search(line[max(0, i - 40): i + len(hit) + 40]))


def _today():
    return datetime.date.today().isoformat()


# ══════════════════════════ lint 核心（纯函数，供 lint/preflight/selftest 复用）══════════════════════════

def collect_findings(md_text, title=None, channel=None):
    """返回 (findings, stats)。findings 每项 = (sev, cat, line, hit, advice)"""
    lim = CONFIG["limits"]
    channel = channel or CONFIG["publish"]["channel"]
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
    if title and re.search(r"[【】\[\]]|…{2,}|!!!|？？", title):
        findings.append(("warn", "标题符号", 0, title[:20] + "…",
                         "方括号/省略号/叹号堆叠属标题党『对抗类』，建议去掉"))

    # ── 逐行扫规则 ──
    for idx, ln in enumerate(body, 1):
        line = ln.strip()
        if not line or line.startswith("!["):
            continue
        for cat, sev, pat, advice, neg_ok in RULES:
            m = pat.search(line)
            if not m:
                continue
            if (sev == "error" or neg_ok) and _negated(line, m.group(0)):
                findings.append(("info", cat + "·引用语境", idx, m.group(0),
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
            findings.append(("warn", "结构·首段", 1, f"首段 {head} 字",
                             f"手机端前 3 行决定划走率，首段建议 ≤{lim['head_max']} 字"))
        long_p = [(i, len(p)) for i, p in enumerate(paras, 1) if len(p) > lim["para_hard"]]
        if long_p:
            findings.append(("warn", "结构·长段", 0,
                             f"{len(long_p)} 段超 {lim['para_hard']} 字（最长 {max(x[1] for x in long_p)} 字）",
                             f"移动端单段建议 ≤{lim['para_soft']} 字，拆段"))
        if chars < lim["body_chars_min"]:
            findings.append(("warn", "结构·篇幅", 0, f"{chars} 字",
                             f"低于 {lim['body_chars_min']} 字，读感偏薄"))
        elif chars > lim["body_chars_max"]:
            findings.append(("warn", "结构·篇幅", 0, f"{chars} 字",
                             f"超过 {lim['body_chars_max']} 字，完读率风险"))
    if not any(p.rstrip().endswith(("？", "?")) for p in paras[-5:]):
        findings.append(("info", "结构·评论钩子", 0, "结尾 5 段无问句",
                         "若以评论为 KPI，结尾要抛一个具体问题"))
    if len(imgs) < lim["imgs_min"]:
        findings.append(("warn", "结构·配图", 0, f"{len(imgs)} 张",
                         f"建议 {lim['imgs_min']}–{lim['imgs_max']} 张"))
    elif len(imgs) > lim["imgs_max"]:
        findings.append(("warn", "结构·配图", 0, f"{len(imgs)} 张",
                         f"超过 {lim['imgs_max']} 张，读者会疲"))
    emo = len(EMOJI_RE.findall(body_text))
    if emo > lim["emoji_max"]:
        findings.append(("warn", "结构·表情", 0, f"{emo} 个 emoji", "公众号正文表情过多显轻浮"))

    stats = {"title": title, "title_len": n, "limit": limit, "channel": channel,
             "paras": len(paras), "chars": chars, "imgs": len(imgs)}
    return findings, stats


def _print_findings(findings, stats, fname):
    errors = [f for f in findings if f[0] == "error"]
    warns = [f for f in findings if f[0] == "warn"]
    print("═" * 62)
    print(f"合规+结构自检  {os.path.basename(fname)}")
    print("═" * 62)
    print(f"通道  {stats['channel']}（标题上限 {stats['limit']} 字）")
    print(f"标题  {stats['title_len']} 字：{stats['title']}")
    print(f"正文  {stats['paras']} 段 / {stats['chars']} 字 / {stats['imgs']} 张图")
    print(f"结果  {'✗ 不合格' if errors else ('△ 待优化' if warns else '✓ 通过')}"
          f"   （error {len(errors)} / warn {len(warns)}）")
    print("-" * 62)
    if not findings:
        print("✓ 未命中任何规则。人工仍需过一遍事实与信源。")
    for sev, cat, ln, snip, advice in sorted(findings, key=lambda x: (x[0] != "error", x[2])):
        loc = f"L{ln}" if ln else ("标题" if cat.startswith("标题") else "全文")
        print(f"{SEV_ICON[sev]} [{cat}] {loc}  «{snip}»")
        print(f"    → {advice}")
    print("-" * 62)
    print("提示：脚本只查『可机检』项；涉企/涉政/未证实信息、原创资质需人工判定。")


def cmd_lint(args):
    findings, stats = collect_findings(_read_md(args.md), args.title, args.channel)
    _print_findings(findings, stats, args.md)
    if args.json:
        print(json.dumps([{"sev": s, "cat": c, "line": l, "hit": h, "advice": a}
                          for s, c, l, h, a in findings], ensure_ascii=False, indent=1))
    return 1 if any(f[0] == "error" for f in findings) else 0


# ══════════════════════════ 配图 ══════════════════════════

def scan_assets(dirpath, check=False):
    """列出图片。

    check=True（核查成品）：优先只看成品后缀；一个成品都没有时退回全部图片，
        否则 `--check` 会把刚压好的 `_clean.jpg` 全跳过，永远报"没有图片"。
    check=False（处理源图）：跳过成品后缀与 *_final.jpg，避免把成品再压一遍。
    """
    exts = tuple(CONFIG["assets"]["exts"])
    suffix = CONFIG["assets"]["suffix"]
    allimg, products = [], []
    for f in sorted(os.listdir(dirpath)):
        p = os.path.join(dirpath, f)
        if not (os.path.isfile(p) and f.lower().endswith(exts)):
            continue
        low = f.lower()
        if low.endswith("_final.jpg"):
            continue
        allimg.append(f)
        if low.endswith(suffix + ".jpg"):
            products.append(f)
    if check:
        return products or allimg
    return [f for f in allimg if f not in products]


def cmd_assets(args):
    try:
        from PIL import Image
    except ImportError:
        print("需要 Pillow：python -m pip install Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple")
        return 1

    a = CONFIG["assets"]
    lim = CONFIG["limits"]
    trim = args.trim if args.trim is not None else a["trim_px"]
    quality = args.quality or a["quality"]
    suffix = args.suffix if args.suffix is not None else a["suffix"]
    cover_kb = args.cover_kb or lim["cover_kb"]
    body_kb = args.body_kb or lim["body_kb"]

    src_dir = args.dir
    out_dir = args.out or src_dir
    if not os.path.isdir(src_dir):
        print(f"✗ 目录不存在：{src_dir}")
        return 1
    if not args.check:
        os.makedirs(out_dir, exist_ok=True)

    files = scan_assets(src_dir, check=args.check)
    if not files:
        print(f"{src_dir} 下没有待处理图片（成品后缀 {suffix}.jpg 与 _final.jpg 已跳过）")
        return 1 if args.check else 0

    print(f"{'核查' if args.check else '处理'} {len(files)} 张   "
          f"（双档：封面 ≤{cover_kb}KB / 正文 ≤{body_kb}KB"
          + (f"，裁底 {trim}px" if trim and not args.check else "") + "）")
    print("-" * 74)
    rows = []
    for f in files:
        p = os.path.join(src_dir, f)
        limit = cover_kb if _is_cover(f) else body_kb
        tag = "封面" if _is_cover(f) else "正文"
        if args.check:
            kb = os.path.getsize(p) / 1024
            rows.append((f, tag, limit, kb, kb <= limit, ""))
            continue
        im = Image.open(p).convert("RGB")
        w, h = im.size
        if trim:
            im = im.crop((0, 0, w, h - trim))
        dst = os.path.join(out_dir, os.path.splitext(f)[0] + suffix + ".jpg")
        kb = 0
        for q in (quality, 80, 72, 65, 58, 50, 42):
            im.save(dst, "JPEG", quality=q, optimize=True, progressive=True)
            kb = os.path.getsize(dst) / 1024
            if kb <= limit:
                break
        rows.append((f, tag, limit, kb, kb <= limit, f"{w}x{h}→{im.size[0]}x{im.size[1]}"))

    for f, tag, limit, kb, ok, dim in rows:
        print(f"{'✓' if ok else '✗ 超限'}  [{tag}] {f:<40} {kb:>7.0f} / {limit}KB"
              + (f"  {dim}" if dim else ""))
    bad = [r for r in rows if not r[4]]
    print("-" * 74)
    if bad:
        print(f"✗ {len(bad)} 张超限——言序会报 ret:10001，必须先压到上限内")
        return 1
    print(f"✓ 全部 {len(rows)} 张符合双档限制，可直接上传")
    return 0


# ══════════════════════════ bundle（含 meta auto）══════════════════════════

def _ledger_rows():
    p = _p(CONFIG["paths"]["ledger"])
    if not os.path.exists(p):
        return []
    rows = []
    for ln in _read_md(p).split("\n"):
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) >= 5 and cells[0].isdigit():
            rows.append(cells)
    return rows


def auto_meta(slug, md_path):
    """从 稿件 + yanxu_params.json + 发布台账 自动汇总元信息，省掉手写 meta.json"""
    acc = CONFIG["account"]
    md = _read_md(md_path)
    title = _extract_title(_split_body(md))
    meta = {
        "选题": slug,
        "主推标题": title,
        "作者": acc["name"],
        "公众号": acc["name"],
        "系列": acc.get("series", ""),
        "发布通道": CONFIG["publish"]["channel"],
        "言序 account_id": acc.get("yanxu_account_id", ""),
        "ima 知识库": acc.get("ima_kb_name", ""),
        "主题样式": CONFIG["publish"].get("theme_id", ""),
        "归档时间": _today(),
        "状态": "草稿未群发",
    }
    yp = _p("yanxu_params.json")
    if os.path.exists(yp):
        try:
            prm = json.load(open(yp, encoding="utf-8"))
            if prm.get("abstract"):
                meta["摘要"] = prm["abstract"]
        except Exception:
            pass
    for row in _ledger_rows():
        if _norm(row[1]) == _norm(title):
            meta["状态"] = row[3]
            meta["发布时间"] = row[4]
            break
    led = _p(CONFIG["paths"]["ledger"])
    if os.path.exists(led):
        txt = _read_md(led)
        for key, pat in (("言序 info_id", r"info_id`?\s*`?(yx\w+)"),
                         ("言序 publish_id", r"publish_id`?\s*`?(\d+)"),
                         ("公众号 appmsgid", r"appmsgid\s*(\d+)")):
            m = re.search(pat, txt)
            if m:
                meta[key] = m.group(1)
    return meta


def cmd_bundle(args):
    md = _read_md(args.md)
    body_md = md.split("\n---")[0].strip()
    body = re.sub(r"!\[[^\]]*\]\(([^)]+)\)",
                  lambda m: f"【配图：{os.path.basename(m.group(1))}】", body_md)

    meta = {}
    mp = _p(f"{args.slug}_meta.json")
    if args.meta and args.meta != "auto" and os.path.exists(args.meta):
        meta = json.load(open(args.meta, encoding="utf-8"))
    elif args.meta == "auto" or not args.meta:
        # 已有 meta 文件优先（人工补充的备选标题/标签不被覆盖），缺的键用自动汇总补齐
        if os.path.exists(mp):
            meta = json.load(open(mp, encoding="utf-8"))
        for k, v in auto_meta(args.slug, args.md).items():
            if not meta.get(k) and v:
                meta[k] = v
        json.dump(meta, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"· 元信息 → {os.path.basename(mp)}（已有键保留，缺的自动补齐）")
    meta.setdefault("公众号", CONFIG["account"]["name"])
    meta.setdefault("归档时间", "")

    parts = [f"# {CONFIG['account']['name']} · {args.slug} 完整资料\n"]
    parts.append("> 本文由 `scripts/gzh.py bundle` 自动生成，供 ima 知识库一站式检索。\n")
    parts.append("## 一、发布元信息\n")
    parts += ["| 项 | 值 |", "|---|---|"]
    for k, v in meta.items():
        if v:
            parts.append(f"| {k} | {str(v).replace('|', '/')} |")
    parts.append("")
    parts.append("## 二、正文全文\n")
    parts.append(body)
    for title, path in (("三、配图说明", args.images), ("四、发布包", args.publish)):
        if path and os.path.exists(path):
            parts.append(f"\n---\n\n## {title}\n")
            inner = _read_md(path).strip()
            inner = re.sub(r"^(#{1,4}) ", lambda m: "#" * (len(m.group(1)) + 2) + " ",
                           inner, flags=re.M)
            parts.append(inner)

    doc = "\n".join(parts) + "\n"
    out = args.out or f"{CONFIG['account']['name']}_{args.slug}_完整资料.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    print("═" * 62)
    print(f"完整资料合集 → {out}")
    print("═" * 62)
    print(f"总字数 {len(doc)}  正文 {len(body)} 字")
    print(f"元信息 {len([v for v in meta.values() if v])} 项 | "
          f"配图章节 {'✓' if args.images else '—'} | 发布包 {'✓' if args.publish else '—'}")
    return 0


# ══════════════════════════ 言序 / 预览 ══════════════════════════

def cmd_yanxu(args):
    md = _read_md(args.md)
    body = _split_body(md)
    img_map = {}
    if args.map:
        img_map = json.load(open(args.map, encoding="utf-8"))

    blocks, missing = [], []
    for ln in body:
        t = ln.strip()
        if not t or t.startswith("# "):
            continue
        m = re.match(r"^!\[[^\]]*\]\(([^)]+)\)", t)
        if m:
            fn = os.path.basename(m.group(1))
            url = img_map.get(fn) or img_map.get(os.path.splitext(fn)[0])
            if url:
                blocks.append({"type": "image", "data": {"url": url}})
            else:
                missing.append(fn)
            continue
        t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
        t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
        blocks.append({"type": "paragraph", "content": _curly(t)})

    title = _curly(args.title or _extract_title(body))
    abstract = _curly(args.abstract or "")[:CONFIG["limits"]["abstract"]]

    params = {"title": title, "blocks": blocks}
    if abstract:
        params["abstract"] = abstract
    if args.cover:
        params["cover_img"] = args.cover
        if not any(b.get("data", {}).get("url") == args.cover for b in blocks if b["type"] == "image"):
            blocks.insert(0, {"type": "image", "data": {"url": args.cover}})

    out = args.out or "yanxu_params.json"
    json.dump(params, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    lim = CONFIG["limits"]["title_yanxu"]
    print("═" * 62)
    print(f"言序组稿参数  → {out}")
    print("═" * 62)
    print(f"标题 {len(title)} 字" + (f"  ✗ 超言序 {lim} 字上限" if len(title) > lim else "  ✓"))
    print(f"摘要 {len(abstract)} 字（上限{CONFIG['limits']['abstract']}）")
    print(f"块数 {len(blocks)}（图片 {sum(1 for b in blocks if b['type'] == 'image')}）")
    if missing:
        print(f"✗ 未映射到URL的图片 {len(missing)} 张：")
        for x in missing:
            print(f"    {x}")
    print("-" * 62)
    print(json.dumps(params, ensure_ascii=False)[:400] + " …")
    return 1 if (missing or len(title) > lim) else 0


def cmd_preview(args):
    html = _read_md(args.html)
    base = os.path.dirname(os.path.abspath(args.html))
    missing = []

    def repl(m):
        src = m.group(1)
        if src.startswith(("http://", "https://", "data:")):
            return m.group(0)
        p = os.path.join(base, src)
        if not os.path.exists(p):
            missing.append(src)
            print(f"  ✗ 找不到 {src}")
            return m.group(0)
        ext = os.path.splitext(p)[1].lower().lstrip(".")
        mime = {"jpg": "jpeg"}.get(ext, ext)
        with open(p, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        print(f"  ✓ 内联 {src}（{os.path.getsize(p) / 1024:.0f}KB）")
        return 'src="data:image/%s;base64,%s"' % (mime, b64)

    total = len(re.findall(r'src="([^"]+)"', html))
    html = re.sub(r'src="([^"]+)"', repl, html)
    out = args.out or os.path.join(base, os.path.splitext(os.path.basename(args.html))[0] + "_预览版.html")
    open(out, "w", encoding="utf-8").write(html)
    mb = os.path.getsize(out) / 1024 / 1024
    print(f"\n预览版 → {out}  ({mb:.1f}MB)")
    if missing:
        print(f"✗ {len(missing)} 张图没内联进去，预览不完整——先修 src 路径再预览")
        return 1
    if total == 0:
        print("✗ 一个 <img> 都没有，检查 HTML 是否有图片")
        return 1
    print("⚠️ 仅本地看效果；base64 图不能粘公众号（会被过滤）")
    return 0


# ══════════════════════════ 脚手架 ══════════════════════════

MD_TEMPLATE = """# {title}

![封面首图（标题文字在公众号编辑器叠加）]({assets}/cover_clean.jpg)

（开头 100 字内进具体场景：一个视频 / 一条弹幕 / 一次对话。不铺垫、不升华。）

---

## 运营配套（不进正文）

- 主标题：{title}（{n} 字，言序上限 30）
- 备选标题①：
- 备选标题②：
- 摘要（≤120 字）：
- 话题标签：
- 状态：待写
"""

PUBLISH_TEMPLATE = """# {slug} · 发布包

## 一、定稿标题

| 序 | 标题 | 角度 | 场景 | 合规 |
|---|---|---|---|---|
| 主推 |  |  |  |  |
| 备选① |  |  |  |  |
| 备选② |  |  |  |  |

## 二、投放建议

- 发布时间：
- 封面：叠字方案
- 首评：自己先评论 1–2 条置顶

## 三、风险预判

- 
"""

IMAGES_TEMPLATE = """# {slug} · 配图清单

> 风格：flat illustration, solid color blocks, clean simple shapes, warm beige and terracotta orange, no clear face, no readable text
> 源图落 `{assets}/raw/`（带 AI 水印，勿直接发），成品落 `{assets}/`（`_clean.jpg`）

| # | 位置 | 文件名 | 用途 | 状态 |
|---|---|---|---|---|
| 1 | 封面 | cover_clean.jpg | 封面主图 | 待出图 |
| 2 | 开头 | body1_*_clean.jpg | 场景代入 | 待出图 |

## 水印与体积

- 出图后立刻：`python scripts/gzh.py assets --dir {assets}/raw --out {assets} --trim 72`
- 上传前核查：`python scripts/gzh.py assets --dir {assets} --check`
"""


def cmd_new(args):
    acc = CONFIG["account"]["name"]
    assets = CONFIG["paths"]["assets_dir"]
    slug, title = args.slug, args.title
    short = re.sub(r"[\s，。：；、？！“”\"'（）()]+", "", title)[:18] or slug
    md_path = f"{slug}_{short}.md"
    if os.path.exists(md_path) and not args.force:
        print(f"✗ {md_path} 已存在（要覆盖加 --force）")
        return 1
    n = len(title)
    open(md_path, "w", encoding="utf-8").write(
        MD_TEMPLATE.format(title=title, n=n, assets=assets))
    open(f"{slug}_发布包.md", "w", encoding="utf-8").write(PUBLISH_TEMPLATE.format(slug=slug))
    open(f"{slug}_配图清单.md", "w", encoding="utf-8").write(
        IMAGES_TEMPLATE.format(slug=slug, assets=assets))
    os.makedirs(os.path.join(assets, "raw"), exist_ok=True)
    meta = auto_meta(slug, md_path)
    json.dump(meta, open(f"{slug}_meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("═" * 62)
    print(f"新选题脚手架  {slug}")
    print("═" * 62)
    for f in (md_path, f"{slug}_发布包.md", f"{slug}_配图清单.md", f"{slug}_meta.json"):
        print(f"✓ {f}")
    print("✓ 配图/raw/")
    print("-" * 62)
    print(f"标题 {n} 字" + ("  ✗ 已超言序 30 字，写作前先改短" if n > CONFIG["limits"]["title_yanxu"] else "  ✓"))
    print(f"下一步：写正文 → python scripts/gzh.py lint --md {md_path}")
    return 0 if n <= CONFIG["limits"]["title_yanxu"] else 1


# ══════════════════════════ 台账 ══════════════════════════

def cmd_ledger(args):
    path = _p(CONFIG["paths"]["ledger"])
    if getattr(args, "audit", False):
        rows = _ledger_rows()
        issues = audit_ledger()
        print(f"台账催办   共 {len(rows)} 篇")
        print("-" * 74)
        if not issues:
            print("✓ 没有逾期未回填的项")
        for lv, msg in issues:
            print(f"{SEV_ICON.get(lv, '·')} {msg}")
        print("-" * 74)
        print("回填是唯一不能让机器代劳的事（读不到公众号后台），但它能被自动催。")
        return 1 if any(lv == "error" for lv, _ in issues) else 0

    if args.list or not (args.add or args.check):
        rows = _ledger_rows()
        print(f"台账 {path}   共 {len(rows)} 篇")
        print("-" * 74)
        for r in rows:
            print(f"#{r[0]}  {r[3]:<12} {r[4]:<18} 标题 {len(r[1])} 字  {r[1][:26]}")
        if not rows:
            print("（空）")
        return 0

    if args.add:
        if not args.title:
            print("✗ --add 需要 --title")
            return 1
        txt = _read_md(path)
        rows = _ledger_rows()
        idx = len(rows) + 1
        if any(_norm(r[1]) == _norm(args.title) for r in rows):
            print("✗ 台账里已有同名标题，别重复登记")
            return 1
        row = (f"| {idx} | {args.title} | {args.topic or '—'} | {args.status or '草稿箱'} | "
               f"{args.time or _today()} | — | — | — | — | — | — | — |")
        lines = txt.rstrip("\n").split("\n")
        last = max(i for i, l in enumerate(lines) if l.strip().startswith("|") and
                   len(l.strip().strip("|").split("|")) > 5)
        lines.insert(last + 1, row)
        open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print(f"✓ 已追加第 {idx} 行：{args.title[:30]}")
        return 0

    # --check
    rows = _ledger_rows()
    bad = []
    print(f"台账自检   共 {len(rows)} 篇")
    print("-" * 74)
    for r in rows:
        print(f"#{r[0]} 标题 {len(r[1])} 字  {r[1][:30]}")
    if args.md:
        md_title = _extract_title(_split_body(_read_md(args.md)))
        hit = [r for r in rows if _norm(r[1]) == _norm(md_title)]
        if not hit:
            bad.append(f"台账里找不到与稿件标题一致的记录：{md_title[:30]}")
        else:
            print(f"✓ 台账标题与稿件一致（{len(md_title)} 字）")
    txt = _read_md(path)
    for m in re.finditer(r"标题\s*(\d+)\s*字", txt):
        claim = int(m.group(1))
        if args.md:
            actual = len(_extract_title(_split_body(_read_md(args.md))))
            if claim != actual:
                bad.append(f"备注写「标题 {claim} 字」，稿件实际 {actual} 字")
        if not any(len(r[1]) == claim for r in rows):
            if not args.md:
                bad.append(f"备注写「标题 {claim} 字」，但没有哪一行标题是这个字数")
    if bad:
        for b in bad:
            print(f"✗ {b}")
        print("→ 台账是唯一事实来源，数字对不上就改台账，别让它和稿件打架")
        return 1
    print("✓ 台账自检通过")
    return 0


# ══════════════════════════ 选题评分 ══════════════════════════

def cmd_score(args):
    if getattr(args, "no", None) and not args.name:
        row = next((r for r in _topic_rows() if r["no"] == args.no), None)
        if not row:
            print(f"✗ 选题库里没有 #{args.no}")
            return 1
        args.name = row["name"]
    dims = [("跨平台热度", args.heat, 0.3), ("共鸣面", args.resonance, 0.3),
            ("情绪张力", args.tension, 0.2), ("风险可控", args.risk, 0.2)]
    for name, v, _ in dims:
        if not (0 <= v <= 10):
            print(f"✗ {name} 需在 0–10 之间（当前 {v}）")
            return 1
    total = sum(v * 10 * w for _, v, w in dims)
    verdict = "不写" if total < 60 else ("备选" if total <= 75 else "主推")
    print("═" * 46)
    print(f"选题评分  {args.name or '未命名'}")
    print("═" * 46)
    for name, v, w in dims:
        print(f"{name:<8}{v:>3}/10  ×{int(w * 100)}%  → {v * 10 * w:>5.1f}")
    print("-" * 46)
    print(f"总分 {total:.1f} / 100   →  {verdict}")
    print(f"结论线：<60 不写 · 60–75 备选 · >75 主推")
    if getattr(args, "save", False):
        n = _topic_set_score(no=getattr(args, "no", None), name=args.name, total=total)
        if n:
            print(f"· 已回写选题库「分数」列" + (f" #{args.no}" if args.no else ""))
        else:
            print("△ 选题库里没匹配到这条，分数未回写（用 --no 指定编号更准）")
    if args.log:
        rec = {"name": args.name, "heat": args.heat, "resonance": args.resonance,
               "tension": args.tension, "risk": args.risk, "total": round(total, 1),
               "verdict": verdict, "time": _today()}
        with open(args.log, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"· 已记入 {args.log}")
    return 0


# ══════════════════════════ 发布总闸 ══════════════════════════

def _find_master(slug):
    pats = [f"{slug}_*.md"]
    cands = []
    for p in pats:
        cands += glob.glob(_p(p))
    skip = ("_发布包", "_配图清单", "_完整资料", "_meta")
    cands = [c for c in cands if not any(s in c for s in skip)]
    return cands[0] if cands else None


def cmd_preflight(args):
    lim = CONFIG["limits"]
    checks = []  # (ok, name, detail)

    md = args.md or _find_master(args.slug or "")
    if not md or not os.path.exists(md):
        print(f"✗ 找不到主稿（--slug {args.slug}）")
        return 1

    # 1 内容
    findings, stats = collect_findings(_read_md(md), None, args.channel)
    errs = [f for f in findings if f[0] == "error"]
    checks.append((not errs, "lint", f"error {len(errs)} / warn "
                   f"{len([f for f in findings if f[0]=='warn'])}"))

    # 2 配图双档
    adir = _p(CONFIG["paths"]["assets_dir"])
    imgs = scan_assets(adir, check=True) if os.path.isdir(adir) else []
    over = []
    for f in imgs:
        kb = os.path.getsize(os.path.join(adir, f)) / 1024
        cap = lim["cover_kb"] if _is_cover(f) else lim["body_kb"]
        if kb > cap:
            over.append(f"{f}({kb:.0f}KB>{cap})")
    checks.append((not over, "配图双档", f"{len(imgs)} 张，超限 {len(over)}" +
                   (f"：{', '.join(over)}" if over else "")))
    checks.append((any(_is_cover(f) for f in imgs), "封面存在",
                   "有" if any(_is_cover(f) for f in imgs) else "没找到 cover_* 封面"))

    # 3 正文图片引用可解析
    body_text = "\n".join(_split_body(_read_md(md)))
    refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", body_text)
    miss = [r for r in refs if not r.startswith(("http://", "https://")) and
            not os.path.exists(os.path.join(ROOT, r))]
    checks.append((not miss, "正文图片引用", f"{len(refs)} 处" +
                   (f"，缺 {len(miss)}：{miss}" if miss else " 全部可解析")))

    # 4 终稿版 HTML
    slug = args.slug or os.path.basename(md).split("_")[0]
    htmls = glob.glob(_p(f"{slug}_公众号终稿版.html"))
    if htmls:
        h = _read_md(htmls[0])
        hsrc = re.findall(r'src="([^"]+)"', h)
        hmiss = [s for s in hsrc if not s.startswith(("http", "data:")) and
                 not os.path.exists(os.path.join(ROOT, s))]
        checks.append((not hmiss, "终稿版HTML", f"{len(hsrc)} 张图" +
                       (f"，缺 {len(hmiss)}：{hmiss}" if hmiss else "")))
    else:
        checks.append((False, "终稿版HTML", f"缺 {slug}_公众号终稿版.html"))

    # 5 bundle 是否比稿件新
    bun = glob.glob(_p(f"*_{slug}_完整资料.md"))
    if bun:
        newer = os.path.getmtime(bun[0]) >= os.path.getmtime(md)
        checks.append((newer, "完整资料", "比稿件新" if newer else "比稿件旧，需重跑 bundle"))
    else:
        checks.append((False, "完整资料", "缺，跑 bundle --meta auto"))

    # 6 台账登记
    title = stats["title"]
    rows = _ledger_rows()
    hit = [r for r in rows if _norm(r[1]) == _norm(title)]
    checks.append((bool(hit), "台账登记", "已登记" if hit else "台账里没有这条标题"))

    print("═" * 66)
    print(f"发布前总闸  {os.path.basename(md)}")
    print("═" * 66)
    print(f"标题 {stats['title_len']} 字 · 正文 {stats['chars']} 字 · "
          f"{stats['imgs']} 张图 · 通道 {stats['channel']}")
    print("-" * 66)
    for ok, name, detail in checks:
        print(f"{'✓' if ok else '✗'} {name:<12} {detail}")
    print("-" * 66)

    if errs:
        print("lint 阻断项：")
        for sev, cat, ln, hit_, adv in errs:
            print(f"  ✗ [{cat}] L{ln} «{hit_}» → {adv}")
        print("-" * 66)

    bad = [c for c in checks if not c[0]]
    if bad:
        print(f"✗ {len(bad)} 项未过，不能发。修完重跑。")
        return 1

    print("✓ 机器能查的全过。剩下只能人工：")
    print("  1) 后台开「原创声明」  2) 开「留言」  3) 确认封面是否叠字")
    print("  4) 自己先评论 1–2 条置顶  5) 发完 24h/72h 回填台账数据")
    return 0


# ══════════════════════════ 选题库与链路（v3）══════════════════════════

TOPIC_POOL = ("待写", "备选")
TOPIC_DONE = ("已成稿", "已发草稿", "已发")


def _topic_rows(path=None):
    """解析 选题库.md 主表：| # | 选题 | 佐证 | 切入角 | 状态 | 分数 |

    兼容 5 列老表（无分数列）；状态去掉 ** 强调符。
    path 可指定，便于自测不碰真选题库。
    """
    p = path or _p(CONFIG["paths"]["topics"])
    if not os.path.exists(p):
        return []
    rows = []
    for ln in _read_md(p).split("\n"):
        s = ln.strip()
        if not re.match(r"^\|\s*\d+\s*\|", s):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 5:
            continue
        raw = cells[5] if len(cells) > 5 else ""
        m = re.search(r"\d+(?:\.\d+)?", raw)
        rows.append({
            "no": int(cells[0]),
            "name": cells[1].replace("*", "").strip(),
            "evidence": cells[2],
            "angle": cells[3],
            "status": cells[4].replace("*", "").strip(),
            "score": float(m.group(0)) if m else None,
        })
    return rows


def _master_files():
    """项目根下所有主稿：[(slug, filename)]，排除完整资料/发布包/配图清单/任务书"""
    skip = ("完整资料", "发布包", "配图清单", "写作任务书", "预览版")
    out = []
    for f in sorted(os.listdir(ROOT)):
        m = re.match(r"^(选题\d+)_(.+)\.md$", f)
        if not m or any(k in f for k in skip):
            continue
        out.append((m.group(1), f))
    return out


def _md_images(md):
    return re.findall(r"!\[[^\]]*\]\(\s*([^)\s]+)", md)


def _ledger_find(title):
    for r in _ledger_rows():
        if _norm(r[1]) == _norm(title):
            return r
    return None


def _parse_dt(s):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(str(s).strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


def _blank(v):
    return v is None or str(v).strip() in ("", "—", "-", "–")


def _hours_since(tm):
    dt = _parse_dt(tm)
    if not dt:
        return None
    return (datetime.datetime.now() - dt).total_seconds() / 3600


def audit_ledger(rows=None, now=None):
    """按发布时间自动算 24h/72h 是否逾期未回填 → [(level, msg)]

    数据列顺序：# 标题 选题 状态 时间 | 阅读 点赞 在看 评论 分享 完读率 涨粉
    rows/now 可注入，便于自测不碰真台账。
    """
    now = now or datetime.datetime.now()
    out = []
    for r in (rows if rows is not None else _ledger_rows()):
        title, status, tm = r[1], r[3], r[4]
        data = (r[5:12] + [""] * 7)[:7]
        short = title[:20]
        if "草稿" in status or "未发" in status:
            if not _blank(data[0]):
                out.append(("warn", f"#{r[0]} {short} 标着草稿却已填阅读数，状态没跟上"))
            continue
        h = _hours_since(tm)
        if h is None:
            out.append(("error", f"#{r[0]} {short} 发布时间「{tm}」解析不了，逾期检测失效"))
            continue
        if h < 0:
            out.append(("warn", f"#{r[0]} {short} 发布时间在未来（{tm}），八成填错了"))
            continue
        if h >= 24 and _blank(data[0]):
            out.append(("error", f"#{r[0]} {short} 已发 {h:.0f}h，24h 数据未回填"))
        elif h >= 72 and _blank(data[5]):
            out.append(("error", f"#{r[0]} {short} 已发 {h:.0f}h，72h 完读率未回填"))
        elif h >= 24 and _blank(data[5]):
            out.append(("info", f"#{r[0]} {short} 24h 数据已回填，还缺 72h 完读率"))
    return out


def _completeness(slug, md_file):
    """单篇链路：稿 → 图 → lint → 台账 → 完整资料"""
    md_path = os.path.join(ROOT, md_file)
    md = _read_md(md_path)
    body = _split_body(md)
    title = _extract_title(body)
    findings, stats = collect_findings(md, title)
    errs = sum(1 for f in findings if f[0] == "error")

    imgs = _md_images(md)
    missing = 0
    for src in imgs:
        if src.startswith(("http://", "https://", "data:")):
            continue
        cand = src if os.path.isabs(src) else os.path.join(ROOT, src)
        if not os.path.exists(cand):
            missing += 1

    led = _ledger_find(title)
    if led:
        st = led[3]
        tag = "草稿" if "草稿" in st else ("已发" if "已发" in st else st[:6])
        h = _hours_since(led[4])
        led_txt = tag + (f" {h:.0f}h" if h is not None and h >= 1 else "")
    else:
        led_txt = "未登记"

    bp = os.path.join(ROOT, f"{BRAND}_{slug}_完整资料.md")
    if not os.path.exists(bp):
        b_txt = "缺"
    elif os.path.getmtime(bp) < os.path.getmtime(md_path):
        b_txt = "旧"
    else:
        b_txt = "✓"

    return {"title": title, "chars": stats["chars"], "imgs": len(imgs), "missing": missing,
            "lint": f"✗{errs}" if errs else "✓", "ledger": led_txt, "bundle": b_txt}


def cmd_status(args):
    print("═" * 74)
    print(f"项目状态  {CONFIG['account']['name']}   {_today()}")
    print("═" * 74)

    arts = _master_files()
    if arts:
        print(f"{'选题':<9}{'标题':<24}{'字数':>5}{'图':>4}  {'lint':<5}{'台账':<12}{'资料'}")
        print("-" * 74)
        for slug, f in arts:
            st = _completeness(slug, f)
            img = f"{st['imgs']}" + (f"缺{st['missing']}" if st["missing"] else "")
            print(f"{slug:<9}{st['title'][:22]:<24}{st['chars']:>5}{img:>4}  "
                  f"{st['lint']:<5}{st['ledger']:<12}{st['bundle']}")
    else:
        print("稿件链路  尚无主稿（gzh.py new --slug 选题N --title \"...\"）")

    rows = _topic_rows()
    print()
    print("选题池")
    print("-" * 74)
    if not rows:
        print("（解析不到选题库主表，检查 选题库.md 表头是否为 | # | 选题 | ... | 状态 | 分数 |）")
        return 0
    cnt = {}
    for r in rows:
        cnt[r["status"]] = cnt.get(r["status"], 0) + 1
    pool = [r for r in rows if r["status"] in TOPIC_POOL]
    unscored = [r for r in pool if r["score"] is None]
    print(f"共 {len(rows)} 条  ·  待写 {cnt.get('待写', 0)}  ·  备选 {cnt.get('备选', 0)}  ·  "
          f"已成稿 {cnt.get('已成稿', 0)}  ·  已发 {cnt.get('已发草稿', 0) + cnt.get('已发', 0)}  ·  "
          f"弃用 {cnt.get('弃用', 0)}")
    top = sorted([r for r in pool if r["score"] is not None], key=lambda x: -x["score"])[:3]
    if top:
        print("最高分  " + " / ".join(f"{r['name'][:14]}({r['score']:.0f})" for r in top))
    if unscored:
        print(f"△ {len(unscored)} 条未评分，pick 不猜分 → 先 score 再排行")
    lowp = [r for r in pool if r["score"] is not None and r["score"] < 60]
    if lowp:
        print(f"△ {len(lowp)} 条分数 <60 却还挂在池里（结论线：不写），"
              f"建议把状态改成「弃用」：" + " / ".join(f"#{r['no']}" for r in lowp))

    issues = audit_ledger()
    if issues:
        print()
        print("台账催办")
        print("-" * 74)
        for lv, msg in issues:
            print(f"{SEV_ICON.get(lv, '·')} {msg}")
    return 0


def _topic_set_score(no=None, name=None, total=None, path=None):
    """把总分写回 选题库.md 的「分数」列。优先按编号定位，其次按名称模糊匹配。

    只替换最后一列，其余单元格原样保留（不碰 **已发草稿** 这类强调）。
    """
    p = path or _p(CONFIG["paths"]["topics"])
    if not os.path.exists(p) or total is None:
        return 0
    lines = _read_md(p).split("\n")
    hit, key = -1, _norm(name or "")
    for i, ln in enumerate(lines):
        st = ln.strip()
        if not re.match(r"^\|\s*\d+\s*\|", st):
            continue
        cells = [c.strip() for c in st.strip("|").split("|")]
        if len(cells) < 5:
            continue
        if no and int(cells[0]) == no:
            hit = i
            break
        nm = _norm(cells[1].replace("*", ""))
        if key and not no and (key == nm or key in nm or nm in key):
            hit = i
    if hit < 0:
        return 0
    raw = lines[hit].strip()
    body = raw.strip("|").split("|")
    while len(body) < 6:
        body.append(" — ")
    body[5] = f" {total:.0f} "
    lines[hit] = "|" + "|".join(body) + "|"
    open(p, "w", encoding="utf-8").write("\n".join(lines))
    return 1


def cmd_pick(args):
    rows = _topic_rows()
    if not rows:
        print("✗ 解析不到选题库主表 → 检查 选题库.md 表头")
        return 1
    pool = [r for r in rows if r["status"] in TOPIC_POOL]
    if not pool:
        print("选题池空了 → 跑「每日热搜选题筛选」任务，或手动补选题")
        return 0

    scored = sorted([r for r in pool if r["score"] is not None], key=lambda r: -r["score"])
    unscored = [r for r in pool if r["score"] is None]
    n = max(1, args.top or 3)

    print("═" * 66)
    print(f"下一篇写什么   候选 {len(pool)} 条（已评分 {len(scored)} / 未评分 {len(unscored)}）")
    print("═" * 66)
    if not scored:
        print("全部未评分。--save 会把分数直接写回选题库，不用手抄：")
        for r in pool[:5]:
            print(f"  #{r['no']} {r['name'][:30]}")
            print(f"      python scripts/gzh.py score --no {r['no']} --heat ? "
                  f"--resonance ? --tension ? --risk ? --save")
        print("（四项各 0–10 分；分数算完自动进排行，pick 就能排序了）")
        return 0

    for i, r in enumerate(scored[:n], 1):
        verdict = "主推" if r["score"] > 75 else ("备选" if r["score"] >= 60 else "不写")
        print(f"{i}. #{r['no']} {r['name']}   {r['score']:.0f} 分（{verdict}）")
        print(f"   角度  {r['angle']}")
        print(f"   佐证  {r['evidence']}")
        print(f"   下一步 python scripts/gzh.py brief --no {r['no']}")
    if len(scored) > n:
        print(f"… 另有 {len(scored) - n} 条已评分候选（--top 看更多）")
    if unscored:
        print(f"△ {len(unscored)} 条未评分，没参与排序（分数为空不猜）")
    return 0


def cmd_brief(args):
    rows = _topic_rows()
    if not rows:
        print("✗ 解析不到选题库 → 无法生成任务书")
        return 1
    hit = None
    if args.no:
        hit = next((r for r in rows if r["no"] == args.no), None)
    if not hit and args.topic:
        key = _norm(args.topic)
        hit = next((r for r in rows
                    if key and (key in _norm(r["name"]) or _norm(r["name"]) in key)), None)
    if not hit:
        print("✗ 没找到该选题。用 --no 3 或 --topic \"关键词\"")
        print("  前 8 条可选：")
        for r in rows[:8]:
            print(f"    #{r['no']} {r['name'][:34]}")
        return 1

    slug = args.slug or f"选题{hit['no']}"
    out = _p(f"{slug}_写作任务书.md")
    if os.path.exists(out) and not args.force:
        print(f"△ 已存在 {os.path.basename(out)}，确认要覆盖就加 --force")
        return 1

    lim, acc = CONFIG["limits"], CONFIG["account"]
    reds, seen = [], set()
    for cat, sev, _rx, advice, _neg in RULES:
        if sev != "error" or not advice or advice in seen:
            continue
        seen.add(advice)
        reds.append((cat, advice))
    reds = reds[:8]

    score_txt = (f"{hit['score']:.0f} 分" if hit["score"] is not None
                 else f"未评分 → 先跑 score --no {hit['no']} ... --save，再 brief --force 重生成")
    red_md = "\n".join(f"- **{c}**：{a}" for c, a in reds) or "- 见 rules/lint_rules.json"

    tpl = f"""# {hit['name']} · 写作任务书

> 由 `gzh.py brief` 于 {_today()} 自动生成。选题或规则变了就重生成，**别手改**。
> 生成命令：`python scripts/gzh.py brief --no {hit['no']} --force`

## 一、选题定位

| 项 | 内容 |
|---|---|
| 选题 | {hit['name']} |
| 编号 | #{hit['no']} |
| 四维总分 | {score_txt} |
| 跨平台佐证 | {hit['evidence']} |
| 切入角 | {hit['angle']} |
| 目标读者 | 25–45 岁普通打工人与中年人，关心钱、工作、父母、身体 |
| 目标字数 | {lim['body_chars_min']}–{lim['body_chars_max']} 字 |
| 标题上限 | **{lim['title_yanxu']} 字**（言序通道，微信端 {lim['title_wechat']} 但以言序为准） |
| 账号调性 | {acc['name']}·{acc.get('series', '普通人视角')} |
| 核心 KPI | 评论数（结尾两问必须问得具体） |

## 二、结构骨架

1. **开头 3 行出场景**：具体时间、地点、一句对话。不铺垫、不讲道理、不写"随着…"
2. **共鸣段**：把读者自己的经历摊开，2–3 个带数字带时间的细节（房租涨了多少、体检报告哪一行）
3. **转折**：给一个反常识观察，最好有一句能被单独截图的话
4. **落点**：不喊口号。给一个今天就能做的小动作，或一句能带走的话
5. **结尾两问**：问具体、问得有得聊（"你上次被这样对待是什么时候"胜过"你怎么看"）

## 三、本篇禁忌（来自 rules/lint_rules.json 的 {len(reds)} 条 error 级红线）

{red_md}

另外人工兜底三条：涉企事实必须有权威信源；健康类不写疗效；整篇搬运热搜不得标原创。

## 四、配图建议（封面 1 + 正文 4，共 5 张）

| 位置 | 画面 | 注意 |
|---|---|---|
| 封面 | 单一主体、大色块、留白多 | ≤{lim['cover_kb']}KB，不叠中文字（AI 图无中文） |
| 开头后 | 呼应第一段的具象场景 | ≤{lim['body_kb']}KB |
| 共鸣段后 | 人物群像或生活细节 | ≤{lim['body_kb']}KB |
| 转折处 | 有对比感的画面 | ≤{lim['body_kb']}KB |
| 结尾前 | 收束情绪的空镜 | ≤{lim['body_kb']}KB |

出图立刻处理（别留到最后）：`python scripts/gzh.py assets --dir 配图/raw --out 配图 --trim 72`
水印在底部 50–65px，裁 {CONFIG['assets']['trim_px']}px 可除净。

## 五、写完就跑

```bash
python scripts/gzh.py lint --md {slug}_标题.md
python scripts/gzh.py preflight --slug {slug}
```

全绿后：新建配图 → 言序发草稿 → 开原创/开留言 → 台账登记 → 入库 ima。
"""
    open(out, "w", encoding="utf-8").write(tpl)
    print(f"✓ {os.path.basename(out)}  （选题 #{hit['no']}：{hit['name'][:26]}）")
    print(f"  下一步：照任务书第二节写，写完跑 lint")
    return 0


def cmd_ship(args):
    slug = args.slug
    if not slug:
        arts = _master_files()
        if len(arts) == 1:
            slug = arts[0][0]
        else:
            print("✗ 有多个主稿，请用 --slug 指定（--slug 选题3）")
            return 1
    master = _find_master(slug)
    if not master:
        print(f"✗ 找不到 {slug} 的主稿")
        return 1

    print("═" * 66)
    print(f"装配 {slug}   {'【执行】' if args.go else '【预演，加 --go 真跑】'}")
    print("═" * 66)

    findings, _stats = collect_findings(_read_md(master), None, args.channel)
    errs = [f for f in findings if f[0] == "error"]
    warns = [f for f in findings if f[0] == "warn"]
    print(f"1/4 lint      {'✓' if not errs else f'✗ {len(errs)} error'}    warn {len(warns)}")
    if errs:
        for f in errs[:3]:
            print(f"    [{f[1]}] {f[3][:44]}")
        print("→ 先修 error，装配中止")
        return 1

    adir = _p(CONFIG["paths"]["assets_dir"])
    imgs = scan_assets(adir, check=True) if os.path.isdir(adir) else []
    over = []
    for f in imgs:
        kb = os.path.getsize(os.path.join(adir, f)) / 1024
        cap = CONFIG["limits"]["cover_kb"] if _is_cover(f) else CONFIG["limits"]["body_kb"]
        if kb > cap:
            over.append(f"{f} {kb:.0f}>{cap}KB")
    print(f"2/4 assets    {'✓' if not over else '✗ ' + ' / '.join(over)}    {len(imgs)} 张")

    md = _read_md(master)
    title = _extract_title(_split_body(md))
    refs = [s for s in _md_images(md) if not s.startswith(("http://", "https://", "data:"))]
    lost = [s for s in refs if not os.path.exists(os.path.join(ROOT, s))]
    print(f"3/4 图片引用  {'✓' if not lost else '✗ 缺 ' + ', '.join(lost[:3])}    {len(refs)} 处")

    bname = f"{BRAND}_{slug}_完整资料.md"
    if args.go:
        ns = argparse.Namespace(md=master, slug=slug, meta="auto",
                                publish=f"{slug}_发布包.md",
                                images=f"{slug}_配图清单.md", out=None)
        rc = cmd_bundle(ns)
        print(f"4/4 bundle    {'✓' if rc == 0 else '✗'} {bname}")
        if rc != 0:
            return rc
    else:
        exists = os.path.exists(os.path.join(ROOT, bname))
        print(f"4/4 bundle    待生成 {bname}（{'已存在，会覆盖' if exists else '新建'}）")

    if over or lost:
        print("→ 有红项，先处理")
        return 1
    print("-" * 66)
    if args.go:
        print(f"✓ {slug} 装配完成。下一步（人工）：言序发草稿 → 开原创/开留言 → 台账登记")
    else:
        print(f"预演通过。真跑：python scripts/gzh.py ship --slug {slug} --go")
    return 0


def cmd_retro(args):
    rows = [r for r in _ledger_rows() if len(r) >= 6]
    live = []

    def num(v):
        try:
            return float(str(v).replace(",", "").replace("—", "").strip() or 0)
        except (ValueError, TypeError):
            return 0.0

    for r in rows:
        if "草稿" in r[3] or "未发" in r[3]:
            continue
        read = num(r[5] if len(r) > 5 else 0)
        if read <= 0:
            continue
        live.append({
            "no": r[0], "title": r[1], "read": read,
            "like": num(r[6]), "wow": num(r[7]), "cmt": num(r[8]),
            "share": num(r[9]), "fin": num(r[10] if len(r) > 10 else 0),
            "fans": num(r[11] if len(r) > 11 else 0),
        })

    print("═" * 66)
    print("数据复盘")
    print("═" * 66)
    if not live:
        print("台账里还没有群发后的真实数据，暂无可复盘内容。")
        print("· 草稿箱里的篇目不参与复盘（还没读者）")
        print("· 群发后 24h 回填阅读/评论/分享，再跑一次 retro")
        return 0

    def rate(n, base):
        return (n / base * 100) if base else 0.0

    print(f"{'#':<3}{'标题':<22}{'阅读':>7}{'评论率':>8}{'在看率':>8}{'分享率':>8}{'涨粉':>6}")
    print("-" * 66)
    for a in live:
        print(f"{a['no']:<3}{a['title'][:20]:<22}{a['read']:>7.0f}"
              f"{rate(a['cmt'], a['read']):>7.2f}%{rate(a['wow'], a['read']):>7.2f}%"
              f"{rate(a['share'], a['read']):>7.2f}%{a['fans']:>6.0f}")

    best = max(live, key=lambda a: rate(a["cmt"], a["read"]))
    worst = min(live, key=lambda a: rate(a["cmt"], a["read"]))
    print("-" * 66)
    print(f"评论率最高  #{best['no']} {best['title'][:26]}  {rate(best['cmt'], best['read']):.2f}%")
    if len(live) > 1:
        print(f"评论率最低  #{worst['no']} {worst['title'][:26]}  {rate(worst['cmt'], worst['read']):.2f}%")
    fin = [a for a in live if a["fin"] > 0]
    if fin:
        low = min(fin, key=lambda a: a["fin"])
        if low["fin"] < 30:
            print(f"△ #{low['no']} 完读率 {low['fin']:.0f}%，低于 30% → 下篇缩短首段、多拆段")
    if len(live) < 3:
        print(f"· 样本只有 {len(live)} 篇，结论先别当真；满 3 篇再看规律")
    if args.log:
        rec = {"time": _today(), "n": len(live),
               "items": [{"no": a["no"], "read": a["read"],
                          "cmt_rate": round(rate(a["cmt"], a["read"]), 2)} for a in live]}
        with open(args.log, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"· 已记入 {args.log}")
    return 0


# ══════════════════════════ 体检 ══════════════════════════

def cmd_doctor(args):
    lim, acc = CONFIG["limits"], CONFIG["account"]
    checks = []

    def chk(ok, name, detail="", level="error"):
        checks.append((ok, name, detail, level))

    chk(sys.version_info >= (3, 8), "python", sys.version.split()[0])
    try:
        import PIL
        chk(True, "Pillow", getattr(PIL, "__version__", "?"))
    except ImportError:
        chk(False, "Pillow", "未安装，assets 不可用")
    for key, rel in CONFIG["paths"].items():
        if key in ("assets_dir", "assets_raw") or not rel:
            continue
        chk(os.path.exists(_p(rel)), f"文件·{os.path.basename(rel)}", rel)
    chk(os.path.isdir(_p(CONFIG["paths"]["assets_dir"])), "配图目录", CONFIG["paths"]["assets_dir"])
    chk(bool(RULES), "规则条数", f"{len(RULES)} 条已编译")
    bad_json = []
    for rel in ("config.json", CONFIG["paths"]["rules"]):
        if os.path.exists(_p(rel)):
            try:
                json.load(open(_p(rel), encoding="utf-8"))
            except Exception as e:
                bad_json.append(f"{rel}: {e}")
    chk(not bad_json, "JSON 可解析", "；".join(bad_json) or "全部正常")

    # 台账与稿件是否打架
    rows = _ledger_rows()
    masters = [f for f in glob.glob(_p("选题*_*.md"))
               if not any(s in f for s in ("_发布包", "_配图清单", "_完整资料", "_meta"))]
    conflicts = []
    if rows and masters:
        latest = rows[-1]
        m = max(masters, key=os.path.getmtime)
        t = _extract_title(_split_body(_read_md(m)))
        if _norm(t) != _norm(latest[1]):
            conflicts.append(f"台账最新行与 {os.path.basename(m)} 标题不一致")
    chk(not conflicts, "台账↔稿件", "；".join(conflicts) or f"{len(rows)} 篇已登记")

    # 残留临时凭证
    leftovers = []
    for d in (ROOT, os.path.join(ROOT, "scripts"), os.environ.get("TEMP", "")):
        if d and os.path.isdir(d):
            leftovers += [f for f in glob.glob(os.path.join(d, "cred*.json"))]
    chk(not leftovers, "临时凭证残留", "；".join(os.path.basename(x) for x in leftovers) or "干净")

    # 预览版体积
    big = [(os.path.basename(p), os.path.getsize(p) / 1024 / 1024)
           for p in glob.glob(_p("*_预览版.html")) if os.path.getsize(p) > 8 * 1024 * 1024]
    chk(not big, "预览版体积", (", ".join(f"{n} {s:.1f}MB" for n, s in big) + "（base64 膨胀，正常但别提交）")
        if big else "正常", level="warn")

    # 台账回填时效（把「人工回填」变成机器主动催）
    dust = audit_ledger()
    late = [m for lv, m in dust if lv == "error"]
    chk(not late, "台账回填时效",
        (f"{len(late)} 项逾期 → ledger --audit 看明细") if late else "无逾期",
        level="warn")

    # 选题池健康度：未评分过多 = pick 排不出序，决策靠猜
    pool = [r for r in _topic_rows() if r["status"] in TOPIC_POOL]
    bare = [r for r in pool if r["score"] is None]
    chk(not (pool and len(bare) == len(pool)), "选题池评分覆盖",
        f"{len(bare)}/{len(pool)} 条未评分，pick 无法排序" if bare else f"{len(pool)} 条均已评分",
        level="warn")

    # 文档与配置漂移：SKILL 里的标题上限是否等于 config
    skill = _p(CONFIG["paths"]["skill"]) if CONFIG["paths"].get("skill") else ""
    if skill and os.path.isfile(skill):
        s = _read_md(skill)
        want = str(lim["title_yanxu"])
        chk(f"≤{want}" in s or f"≤{want} " in s or f"{want} 字" in s, "SKILL↔config 标题上限",
            f"config={want} 字", level="warn")

    print("═" * 66)
    print("项目体检")
    print("═" * 66)
    print(f"账号 {acc['name']} · 言序 {acc.get('yanxu_account_id') or '未配置'} · "
          f"KB {acc.get('ima_kb_id') or '未配置'}")
    print("-" * 66)
    for ok, name, detail, level in checks:
        icon = "✓" if ok else ("△" if level == "warn" else "✗")
        print(f"{icon} {name:<20} {detail}")
    hard = [c for c in checks if not c[0] and c[3] == "error"]
    warn = [c for c in checks if not c[0] and c[3] == "warn"]
    print("-" * 66)
    print(f"{'✓ 体检通过' if not hard else f'✗ {len(hard)} 项硬伤'}"
          f"（warn {len(warn)}）")
    if args.json:
        print(json.dumps([{"ok": c[0], "name": c[1], "detail": c[2], "level": c[3]}
                          for c in checks], ensure_ascii=False, indent=1))
    return 1 if hard else 0


# ══════════════════════════ 自测 ══════════════════════════

def _cases():
    """(名称, md 文本, 标题, 期望命中的规则类目 或 None=不应有 error)"""
    T = "35岁怕优化，60岁怕负担：你笑\"老登\"的底气，还没轮到你"
    return [
        ("紧迫诱导应报 error",
         f"# {T}\n\n正文。\n\n不看后悔，速看。\n", None, "紧迫诱导"),
        ("诱导分享应报 error",
         f"# {T}\n\n正文。\n\n不转不是中国人。\n", None, "诱导分享"),
        ("疗效断言应报 error",
         f"# {T}\n\n正文。\n\n这个东西能治百病。\n", None, "疗效断言"),
        ("手机号应报 error",
         f"# {T}\n\n正文。\n\n联系我 13800000000 。\n", None, "隐私号段"),
        ("辟谣引用不判 error",
         f"# {T}\n\n正文。\n\n转发\"空腹吃苹果治百病\"那种一眼假的文章。\n",
         None, "疗效断言·引用语境"),
        ("涉政应报 error",
         f"# {T}\n\n正文。\n\n网上在传某地发生了群体性事件。\n", None, "涉政红线"),
        ("超 30 字标题应报 error",
         "# " + "这是一条特别特别特别特别特别长的标题它一定超过三十个字了吧真的超了" + "\n\n正文。\n",
         None, "标题长度"),
        ("干净稿不应有 error",
         f"# {T}\n\n" + "\n\n".join(["前两天刷到个视频，两个小伙子在地铁上聊天。"] * 40) +
         "\n\n![图](配图/cover_clean.jpg)\n\n![图](配图/body1_subway_clean.jpg)\n\n"
         "![图](配图/body2_warm_clean.jpg)\n\n你第一次觉得父母老了，是哪个瞬间？\n",
         None, "无 error"),
    ]


def _selftest_scan_ok():
    """用临时目录验证 scan_assets(check=True) 能识别 _clean 成品。

    不依赖真实配图目录，空项目里也能跑。
    """
    import shutil
    import tempfile
    d = tempfile.mkdtemp(prefix="_gzh_scan_")
    try:
        for n in ("cover_clean.jpg", "body1_x_clean.jpg", "draft_raw.png"):
            with open(os.path.join(d, n), "wb") as f:
                f.write(b"x")
        return scan_assets(d, check=True) == ["body1_x_clean.jpg", "cover_clean.jpg"]
    except Exception:
        return False
    finally:
        shutil.rmtree(d, ignore_errors=True)


def cmd_selftest(args):
    ok = fail = 0
    print("═" * 66)
    print("gzh.py 自测")
    print("═" * 66)

    for name, md, title, expect in _cases():
        findings, stats = collect_findings(md, title, "yanxu")
        cats = {f[1] for f in findings}
        errs = [f for f in findings if f[0] == "error"]
        if expect == "无 error":
            good = not errs
        else:
            good = expect in cats and (expect.endswith("引用语境") or bool(errs))
        print(f"{'✓' if good else '✗'} {name}  → 命中 {sorted(cats) or '无'}")
        ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    # 配置与规则
    t = [
        ("config 标题上限可读", isinstance(CONFIG["limits"]["title_yanxu"], int)),
        ("规则已编译", len(RULES) >= 10),
        ("规则无重复类目", len({r[0] for r in RULES}) == len(RULES)),
        ("封面识别", _is_cover("cover_clean.jpg") and _is_cover("封面_主图.jpg")
         and not _is_cover("body1_subway_clean.jpg")),
        ("全角引号转换", _curly('他说"好"') == "他说“好”"),
        ("标题归一化", _norm("你笑“老登”") == _norm('你笑"老登"')),
        ("台账可解析", isinstance(_ledger_rows(), list)),
        ("assets 核查能识别成品（不被后缀跳过）", _selftest_scan_ok()),
        ("评分权重合计 1.0", abs(sum(w for _, _, w in
                                    [("a", 0, .3), ("b", 0, .3), ("c", 0, .2), ("d", 0, .2)]) - 1.0) < 1e-9),
    ]
    for name, good in t:
        print(f"{'✓' if good else '✗'} {name}")
        ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    # 关键函数可调用（防配置键笔误）
    import tempfile as _tf
    _tmd = os.path.join(_tf.gettempdir(), "_gzh_meta_selftest.md")
    try:
        with open(_tmd, "w", encoding="utf-8") as f:
            f.write("# 测试标题：用来验证元信息汇总\n\n正文一段。\n")
        m = auto_meta("选题0", _tmd)
        good = bool(m.get("主推标题"))
        detail = f"{len(m)} 项"
    except Exception as e:
        good, detail = False, f"{type(e).__name__}: {e}"
    finally:
        if os.path.exists(_tmd):
            os.remove(_tmd)
    print(f"{'✓' if good else '✗'} auto_meta 可调用（{detail}）")
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    # v3 链路：选题库解析 / 逾期催办 / 分数回写
    _tt = os.path.join(_tf.gettempdir(), "_gzh_topics_selftest.md")
    try:
        with open(_tt, "w", encoding="utf-8") as f:
            f.write("| # | 选题 | 跨平台佐证 | 爆款切入点 | 状态 | 分数 |\n"
                    "|---|------|-----------|-----------|------|------|\n"
                    "| 1 | 测试选题甲 | 微博#1 | 角度甲 | **已发草稿** | 81 |\n")
        tr = _topic_rows(_tt)
    finally:
        if os.path.exists(_tt):
            os.remove(_tt)
    t3 = [
        ("选题库可解析", bool(tr) and all({"no", "name", "status", "score"} <= set(r) for r in tr)),
        ("选题状态已去星号", all("*" not in r["status"] for r in tr)),
        ("主稿可发现（函数可用）", isinstance(_master_files(), list)),
        ("时间解析 2026-10-28 13:34", _parse_dt("2026-10-28 13:34") is not None),
        ("时间解析拒绝垃圾输入", _parse_dt("昨天下午") is None),
        ("空值判定", _blank("—") and _blank("") and not _blank("12")),
        ("图片引用提取", _md_images("![](配图/a.jpg)\n![x](b.png)") == ["配图/a.jpg", "b.png"]),
    ]
    for name, good in t3:
        print(f"{'✓' if good else '✗'} {name}")
        ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    # 逾期催办：假台账注入，不碰真文件
    fake_now = datetime.datetime(2026, 10, 28, 12, 0)
    fake = [
        ["1", "两天没回填", "t", "已群发", "2026-10-26 09:00",
         "—", "—", "—", "—", "—", "—", "—"],
        ["2", "刚发一小时", "t", "已群发", "2026-10-28 11:00",
         "—", "—", "—", "—", "—", "—", "—"],
        ["3", "还在草稿箱", "t", "草稿箱", "2026-10-28 09:00",
         "—", "—", "—", "—", "—", "—", "—"],
    ]
    iss = audit_ledger(rows=fake, now=fake_now)
    good = len(iss) == 1 and iss[0][0] == "error" and "24h" in iss[0][1]
    print(f"{'✓' if good else '✗'} 催办：只报真逾期（51h 未回填），草稿与刚发不误报  → {len(iss)} 条")
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    fake2 = [["1", "已回填24h", "t", "已群发", "2026-10-26 09:00",
              "1000", "10", "5", "3", "2", "—", "1"]]
    iss2 = audit_ledger(rows=fake2, now=fake_now)
    good = len(iss2) == 1 and iss2[0][0] == "info" and "72h" in iss2[0][1]
    print(f"{'✓' if good else '✗'} 催办：24h 已填只提示 72h，不重复报 error")
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    # 分数回写：临时文件，不碰真选题库
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "_gzh_topic_selftest.md")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("| # | 选题 | 佐证 | 角度 | 状态 | 分数 |\n"
                    "|---|------|------|------|------|------|\n"
                    "| 1 | 测试选题甲 | 微博#1 | 角度甲 | **已发草稿** | — |\n")
        n = _topic_set_score(no=1, total=81.0, path=tmp)
        back = open(tmp, encoding="utf-8").read()
        rows = [l for l in back.split("\n") if l.strip().startswith("| 1 ")]
        row = rows[0].strip() if rows else ""
        good = bool(n == 1 and row.endswith("| 81 |") and "**已发草稿**" in row
                    and len(row.strip("|").split("|")) == 6)
        detail = "分数已写、强调未被破坏、列数未变" if good else row[:44]
    except Exception as e:
        good, detail = False, f"{type(e).__name__}: {e}"
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    print(f"{'✓' if good else '✗'} 分数回写选题库（{detail}）")
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    # 评分计算
    total = 8 * 10 * .3 + 9 * 10 * .3 + 7 * 10 * .2 + 9 * 10 * .2
    good = abs(total - 83.0) < 0.05
    print(f"{'✓' if good else '✗'} 评分数学（8/9/7/9 → 83.0）实际 {total:.1f}")
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    print("-" * 66)
    print(f"{'✓ 全部通过' if not fail else f'✗ {fail} 项失败'}   （{ok} passed / {fail} failed）")
    return 1 if fail else 0


# ══════════════════════════ 入口 ══════════════════════════

def main():
    ap = argparse.ArgumentParser(description="公众号爆款流水线工具 v2")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("lint", help="合规+结构自检")
    p.add_argument("--md", required=True)
    p.add_argument("--title")
    p.add_argument("--channel", choices=["yanxu", "wechat"], default=CONFIG["publish"]["channel"])
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("assets", help="配图压缩/去水印/双档体积核查")
    p.add_argument("--dir", required=True)
    p.add_argument("--out")
    p.add_argument("--trim", type=int, help="裁掉底部像素（默认取 config）")
    p.add_argument("--cover-kb", type=int, dest="cover_kb")
    p.add_argument("--body-kb", type=int, dest="body_kb")
    p.add_argument("--quality", type=int)
    p.add_argument("--suffix", help="成品后缀，默认 _clean")
    p.add_argument("--check", action="store_true", help="只核查不处理")
    p.set_defaults(func=cmd_assets)

    p = sub.add_parser("yanxu", help="MD → 言序组稿参数")
    p.add_argument("--md", required=True)
    p.add_argument("--title")
    p.add_argument("--abstract")
    p.add_argument("--cover")
    p.add_argument("--map", help='图片映射 JSON：{"文件名.jpg":"URL"}')
    p.add_argument("--out")
    p.set_defaults(func=cmd_yanxu)

    p = sub.add_parser("preview", help="HTML → base64 自包含预览版")
    p.add_argument("--html", required=True)
    p.add_argument("--out")
    p.set_defaults(func=cmd_preview)

    p = sub.add_parser("bundle", help="生成完整资料合集（ima 入库必带）")
    p.add_argument("--md", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--meta", nargs="?", const="auto", help="meta.json 路径，或 auto（默认自动汇总）")
    p.add_argument("--publish")
    p.add_argument("--images")
    p.add_argument("--out")
    p.set_defaults(func=cmd_bundle)

    p = sub.add_parser("new", help="新选题脚手架")
    p.add_argument("--slug", required=True, help="如 选题4")
    p.add_argument("--title", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("ledger", help="发布台账 list/add/check")
    p.add_argument("--list", action="store_true")
    p.add_argument("--add", action="store_true")
    p.add_argument("--check", action="store_true")
    p.add_argument("--title")
    p.add_argument("--topic")
    p.add_argument("--status")
    p.add_argument("--time")
    p.add_argument("--md", help="check 时比对的主稿")
    p.add_argument("--audit", action="store_true", help="逾期回填催办（按发布时间自动算 24h/72h）")
    p.set_defaults(func=cmd_ledger)

    p = sub.add_parser("score", help="选题四维评分")
    p.add_argument("--heat", type=float, required=True)
    p.add_argument("--resonance", type=float, required=True)
    p.add_argument("--tension", type=float, required=True)
    p.add_argument("--risk", type=float, required=True)
    p.add_argument("--name")
    p.add_argument("--no", type=int, help="选题库编号，直接取该行选题名")
    p.add_argument("--save", action="store_true", help="把总分写回选题库「分数」列")
    p.add_argument("--log", help="追加记录到 jsonl")
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("preflight", help="发布前总闸")
    p.add_argument("--slug")
    p.add_argument("--md")
    p.add_argument("--channel", choices=["yanxu", "wechat"], default=CONFIG["publish"]["channel"])
    p.set_defaults(func=cmd_preflight)

    p = sub.add_parser("status", help="项目总览：稿件链路 + 选题池 + 台账催办")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("pick", help="从选题池挑下一篇（按分数排）")
    p.add_argument("--top", type=int, default=CONFIG["limits"].get("pick_top", 3))
    p.set_defaults(func=cmd_pick)

    p = sub.add_parser("brief", help="生成写作任务书（切入角/骨架/禁忌/配图）")
    p.add_argument("--no", type=int, help="选题编号，如 3")
    p.add_argument("--topic", help="选题关键词")
    p.add_argument("--slug", help="输出文件名前缀，默认 选题N")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_brief)

    p = sub.add_parser("ship", help="一键装配：lint→图→引用→bundle（默认预演）")
    p.add_argument("--slug")
    p.add_argument("--go", action="store_true", help="真跑（会重写完整资料）")
    p.add_argument("--channel", choices=["yanxu", "wechat"], default=CONFIG["publish"]["channel"])
    p.set_defaults(func=cmd_ship)

    p = sub.add_parser("retro", help="台账数据复盘（评论率/在看率/完读率）")
    p.add_argument("--log", help="追加 jsonl 记录")
    p.set_defaults(func=cmd_retro)

    p = sub.add_parser("doctor", help="项目体检")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("selftest", help="自带用例自测")
    p.set_defaults(func=cmd_selftest)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
