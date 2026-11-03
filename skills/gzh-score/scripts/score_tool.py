#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
score_tool.py — 选题四维评分 + 写作任务书（独立分发版，零项目依赖）

两个子命令：
    score   选题四维评分（跨平台热度/共鸣面/情绪张力/风险可控），权重可配
    brief   生成写作任务书（切入角/骨架/禁忌/配图），选题库可选

设计要点
- 零第三方依赖，纯标准库；不 import 任何项目文件。
- score 的评分数学完全通用：四维各 0–10，权重默认 0.3/0.3/0.2/0.2，
  <60 不写 / 60–75 备选 / >75 主推；可用 --weights 覆盖。
- brief 的「本篇禁忌」来自 rules/lint_rules.json 的 error 级红线（与 lint 共用
  同一份单一真相源）；找不到时回退内嵌最小红线，离线可用。
- 支持独立于项目选题库使用：--name/--angle/--evidence 直接给；--topic-file
  可选，指向一份「选题库.md」按编号/关键词取切入角与佐证。

返回码：score 永远 0（评分不是合规拦截）；brief 找不到选题返回 1。
"""
import argparse
import datetime
import json
import os
import re
import sys

DEFAULT_WEIGHTS = {"heat": 0.3, "resonance": 0.3, "tension": 0.2, "risk": 0.2}

DEFAULT_LIMITS = {
    "title_yanxu": 30,
    "title_wechat": 64,
    "body_chars_min": 1200,
    "body_chars_max": 2000,
    "cover_kb": 2000,
    "body_kb": 1000,
    "imgs_min": 3,
    "imgs_max": 5,
}

# brief 禁忌兜底（与 lint 的 error 级红线一致的最小集；优先用 lint_rules.json 覆盖）
DEFAULT_RED_LINES = [
    ("涉政/涉稳", "涉政/涉稳一律不写，删掉整段"),
    ("诱导分享", "引导关注可以，诱导分享（不转不是/集赞/求扩散）不行，删"),
    ("标题党", "煽动蛊惑（速看/不看后悔/最后一天）必须删"),
    ("疗效断言", "健康类只写生活方式提醒，不下疗效结论"),
    ("隐私号段", "手机号/身份证号必须脱敏"),
    ("绝对化用语", "广告法风险，最/第一/唯一/100% 改限定表述"),
]


# ══════════════════════════ 评分 ══════════════════════════

def score_total(heat, resonance, tension, risk, weights=None):
    w = weights or DEFAULT_WEIGHTS
    total = (heat * 10 * w["heat"] + resonance * 10 * w["resonance"]
             + tension * 10 * w["tension"] + risk * 10 * w["risk"])
    verdict = "不写" if total < 60 else ("备选" if total <= 75 else "主推")
    return total, verdict


def cmd_score(args):
    dims = [("heat", "跨平台热度", args.heat), ("resonance", "共鸣面", args.resonance),
            ("tension", "情绪张力", args.tension), ("risk", "风险可控", args.risk)]
    w = DEFAULT_WEIGHTS
    if args.weights:
        try:
            parts = dict(kv.split("=") for kv in args.weights.split(","))
            w = {k: float(v) for k, v in parts.items()}
            assert set(w) == set(DEFAULT_WEIGHTS), "权重键必须覆盖 heat/resonance/tension/risk"
        except Exception as e:
            print(f"\u2717 --weights 解析失败：{e}")
            return 1
    for en, name, v in dims:
        if not (0 <= v <= 10):
            print(f"\u2717 {name} 需在 0–10 之间（当前 {v}）")
            return 1
    total, verdict = score_total(args.heat, args.resonance, args.tension, args.risk, w)
    print("=" * 46)
    print(f"选题评分  {args.name or '未命名'}")
    print("=" * 46)
    for en, name, v in dims:
        print(f"{name:<8}{v:>3}/10  ×{int(w[en] * 100)}%  → {v * 10 * w[en]:>5.1f}")
    print("-" * 46)
    print(f"总分 {total:.1f} / 100   →  {verdict}")
    print(f"结论线：<60 不写 · 60–75 备选 · >75 主推")
    if args.save:
        n = _topic_set_score(no=args.no, name=args.name, total=total,
                             path=args.topic_file)
        if n:
            print(f"· 已回写「分数」列" + (f" #{args.no}" if args.no else ""))
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


# ══════════════════════════ 选题库（可选）═════════════════════════

def _norm(s):
    s = re.sub(r"\s+", "", s or "")
    for a, b in (("\u201c", '"'), ("\u201d", '"'), ("\u2018", "'"), ("\u2019", "'")):
        s = s.replace(a, b)
    return s


def _topic_rows(path):
    if not path or not os.path.exists(path):
        return []
    rows = []
    for ln in open(path, encoding="utf-8").read().split("\n"):
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
            "status": re.split(r"[（(]", cells[4].replace("*", "").strip())[0].strip(),
            "score": float(m.group(0)) if m else None,
        })
    return rows


def _topic_set_score(no=None, name=None, total=None, path=None):
    if not path or not os.path.exists(path) or total is None:
        return 0
    lines = open(path, encoding="utf-8").read().split("\n")
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
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    return 1


# ══════════════════════════ 红线（brief 用）═════════════════════════

def _red_lines(rules_file=None):
    candidates = []
    if rules_file:
        candidates = [rules_file]
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(os.getcwd(), "rules", "lint_rules.json"),
            os.path.join(here, "rules", "lint_rules.json"),
            os.path.join(here, "..", "rules", "lint_rules.json"),
        ]
    for c in candidates:
        if c and os.path.exists(c):
            try:
                raw = json.load(open(c, encoding="utf-8"))
                seen, out = set(), []
                for r in raw.get("rules", []):
                    if r.get("sev") != "error" or not r.get("advice"):
                        continue
                    if r["advice"] in seen:
                        continue
                    seen.add(r["advice"])
                    out.append((r["cat"], r["advice"]))
                if out:
                    return out[:8]
            except Exception:
                pass
    return DEFAULT_RED_LINES


# ══════════════════════════ 任务书 ══════════════════════════

def cmd_brief(args):
    lim = DEFAULT_LIMITS
    hit = None
    if args.topic_file:
        rows = _topic_rows(args.topic_file)
        if args.no:
            hit = next((r for r in rows if r["no"] == args.no), None)
        elif args.topic:
            key = _norm(args.topic)
            hit = next((r for r in rows
                        if key and (key in _norm(r["name"]) or _norm(r["name"]) in key)), None)
    if not hit and not (args.name or args.topic):
        print("\u2717 至少要给 --name 或 --topic-file + --no/--topic")
        return 1
    name = args.name or (hit["name"] if hit else args.topic)
    no = args.no or (hit["no"] if hit else 0)
    angle = args.angle or (hit["angle"] if hit else "（自行补充切入角）")
    evidence = args.evidence or (hit["evidence"] if hit else "（自行补充跨平台佐证）")
    slug = args.slug or f"选题{no}" if no else "选题"
    out = args.out or f"{slug}_写作任务书.md"

    if os.path.exists(out) and not args.force:
        print(f"△ 已存在 {os.path.basename(out)}，确认要覆盖就加 --force")
        return 1

    reds = _red_lines(args.rules)
    red_md = "\n".join(f"- **{c}**：{a}" for c, a in reds) or "- 见 rules/lint_rules.json"
    score_txt = (f"{args.score:.0f} 分" if args.score is not None
                 else f"未评分 → 先跑 score --name \"{name}\" ... --save，再 brief --force 重生成")

    tpl = f"""# {name} · 写作任务书

> 由 `score_tool.py brief` 于 {_today()} 自动生成。选题或规则变了就重生成，**别手改**。
> 生成命令：`python score_tool.py brief --no {no} --force`

## 一、选题定位

| 项 | 内容 |
|---|---|
| 选题 | {name} |
| 编号 | #{no} |
| 四维总分 | {score_txt} |
| 跨平台佐证 | {evidence} |
| 切入角 | {angle} |
| 目标读者 | 25–45 岁普通读者，关心钱、工作、父母、身体 |
| 目标字数 | {lim['body_chars_min']}–{lim['body_chars_max']} 字 |
| 标题上限 | **{lim['title_yanxu']} 字**（言序通道，微信端 {lim['title_wechat']} 但以言序为准） |

## 二、结构骨架

1. **开头 3 行出场景**：具体时间、地点、一句对话。不铺垫、不讲道理、不写"随着…"
2. **共鸣段**：把读者自己的经历摊开，2–3 个带数字带时间的细节
3. **转折**：给一个反常识观察，最好有一句能被单独截图的话
4. **落点**：不喊口号。给一个今天就能做的小动作，或一句能带走的话
5. **结尾两问**：问具体、问得有得聊

## 三、本篇禁忌（来自 rules/lint_rules.json 的 {len(reds)} 条 error 级红线）

{red_md}

另外人工兜底三条：涉企事实必须有权威信源；健康类不写疗效；整篇搬运热搜不得标原创。

## 四、配图建议（封面 1 + 正文 {lim['imgs_max'] - 1} 张，共 {lim['imgs_max']} 张）

| 位置 | 画面 | 注意 |
|---|---|---|
| 封面 | 单一主体、大色块、留白多 | ≤{lim['cover_kb']}KB，不叠中文字（AI 图无中文） |
| 开头后 | 呼应第一段的具象场景 | ≤{lim['body_kb']}KB |
| 共鸣段后 | 人物群像或生活细节 | ≤{lim['body_kb']}KB |
| 转折处 | 有对比感的画面 | ≤{lim['body_kb']}KB |
| 结尾前 | 收束情绪的空镜 | ≤{lim['body_kb']}KB |

## 五、写完就跑

```bash
python lint_tool.py lint --md {slug}_标题.md --channel yanxu
```

全绿后：新建配图 → 发草稿 → 开原创/开留言 → 台账登记 → 入库知识库。
"""
    open(out, "w", encoding="utf-8").write(tpl)
    print(f"\u2713 {os.path.basename(out)}  （选题 #{no}：{name[:26]}）")
    print(f"  下一步：照任务书第二节写，写完跑 lint")
    return 0


# ══════════════════════════ 工具 ══════════════════════════

def _today():
    return datetime.date.today().isoformat()


def _selftest():
    ok = fail = 0
    print("=" * 62)
    print("score_tool 自测")
    print("=" * 62)
    t, v = score_total(8, 9, 7, 9)
    good = abs(t - 83.0) < 0.05
    print(f"{'\u2713' if good else '\u2717'} 评分数学（8/9/7/9 → 83.0）实际 {t:.1f}")
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    w = DEFAULT_WEIGHTS
    good = abs(sum(w.values()) - 1.0) < 1e-9
    print(f"{'\u2713' if good else '\u2717'} 权重合计 1.0")
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    good = score_total(3, 3, 3, 3)[0] < 60
    print(f"{'\u2713' if good else '\u2717'} 低分判不写（四维也 3 → {score_total(3,3,3,3)[0]:.0f}）")
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    good = score_total(9, 9, 9, 9)[1] == "主推"
    print(f"{'\u2713' if good else '\u2717'} 高分判主推（四维也 9 → 主推）")
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    tmp = os.path.join(os.environ.get("TEMP", "."), "_score_topic_selftest.md")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("| # | 选题 | 佐证 | 角度 | 状态 | 分数 |\n"
                    "|---|------|------|------|------|------|\n"
                    "| 1 | 测试选题甲 | 微博#1 | 角度甲 | **已发草稿** | — |\n")
        n = _topic_set_score(no=1, total=81.0, path=tmp)
        back = open(tmp, encoding="utf-8").read()
        row = [l for l in back.split("\n") if l.strip().startswith("| 1 ")][0].strip()
        good = bool(n == 1 and row.endswith("| 81 |") and "**已发草稿**" in row
                    and len(row.strip("|").split("|")) == 6)
        print(f"{'\u2713' if good else '\u2717'} 分数回写选题库（{row[:44]}）")
    except Exception as e:
        good, row = False, f"{type(e).__name__}: {e}"
        print(f"\u2717 分数回写选题库 {row}")
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    print("-" * 62)
    print(f"{'\u2713 全部通过' if not fail else f'\u2717 {fail} 项失败'}   （{ok} passed / {fail} failed）")
    return 1 if fail else 0


# ══════════════════════════ 入口 ══════════════════════════

def main():
    ap = argparse.ArgumentParser(description="选题评分 + 写作任务书（独立版）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("score", help="选题四维评分")
    p.add_argument("--heat", type=float, required=True)
    p.add_argument("--resonance", type=float, required=True)
    p.add_argument("--tension", type=float, required=True)
    p.add_argument("--risk", type=float, required=True)
    p.add_argument("--name")
    p.add_argument("--no", type=int)
    p.add_argument("--weights", help="权重覆盖，如 heat=0.3,resonance=0.3,tension=0.2,risk=0.2")
    p.add_argument("--save", action="store_true", help="把总分写回 --topic-file 的「分数」列")
    p.add_argument("--topic-file", help="选题库 md（可选，--save 写回用）")
    p.add_argument("--log", help="追加记录到 jsonl")
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("brief", help="生成写作任务书")
    p.add_argument("--no", type=int)
    p.add_argument("--topic", help="选题关键词")
    p.add_argument("--name")
    p.add_argument("--angle")
    p.add_argument("--evidence")
    p.add_argument("--score", type=float, help="已评分数（仅展示用）")
    p.add_argument("--slug", help="输出文件名前缀，默认 选题N")
    p.add_argument("--out", help="输出路径，默认 {slug}_写作任务书.md")
    p.add_argument("--topic-file", help="选题库 md（可选，按 --no/--topic 取切入角与佐证）")
    p.add_argument("--rules", help="规则文件 JSON（默认优先读 rules/lint_rules.json）")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_brief)

    p = sub.add_parser("selftest", help="内置用例自测")
    p.set_defaults(func=lambda a: _selftest())

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
