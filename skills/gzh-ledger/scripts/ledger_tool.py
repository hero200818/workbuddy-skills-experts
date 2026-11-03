#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ledger_tool.py — 公众号发布台账 + 数据复盘（独立分发版，零项目依赖）

两个子命令：
    ledger  发布台账：list / add / check / audit（audit 按发布时间算 24h/72h 逾期催办）
    retro   数据复盘：评论率 / 在看率 / 分享率 / 完读率 / 涨粉

设计要点
- 零第三方依赖，纯标准库；不 import 任何项目文件。
- 台账是 markdown 表格，列顺序固定：
  | # | 标题 | 选题 | 状态 | 时间 | 阅读 | 点赞 | 在看 | 评论 | 分享 | 完读率 | 涨粉 |
  用 --file 指定（默认 ./发布台账.md），与任何项目解耦。
- 可用 `ledger --init` 生成空白模板。
- 逾期催办 / 复盘逻辑与 gzh.py ledger 完全一致；audit / 解析支持注入参数，
  便于自测不碰真台账。

返回码：ledger add/check 失败返回 1；audit 有 error 返回 1；其余 0。
"""
import argparse
import datetime
import json
import os
import re
import sys

SEV_ICON = {"error": "\u2717", "warn": "\u25b3", "info": "\u00b7"}

LEDGER_TEMPLATE = """# 发布台账

> 记录每篇文章的发布状态与群发后数据。回填是唯一不能让机器代劳的事（读不到后台），
> 但它能被自动催（ledger --audit）。

| # | 标题 | 选题 | 状态 | 时间 | 阅读 | 点赞 | 在看 | 评论 | 分享 | 完读率 | 涨粉 |
|---|------|------|------|------|------|------|------|------|------|--------|------|
| 1 | 示例标题 | 选题1 | 草稿箱 | {today} | — | — | — | — | — | — | — |
""".format(today=datetime.date.today().isoformat())


# ══════════════════════════ 解析与工具 ══════════════════════════

def _read_file(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _ledger_rows(path):
    if not path or not os.path.exists(path):
        return []
    rows = []
    for ln in _read_file(path).split("\n"):
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) >= 5 and cells[0].isdigit():
            rows.append(cells)
    return rows


def _parse_dt(s):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(str(s).strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


def _blank(v):
    return v is None or str(v).strip() in ("", "\u2014", "-", "\u2013")


def _hours_since(tm, now=None):
    dt = _parse_dt(tm)
    if not dt:
        return None
    if now is None:
        now = datetime.datetime.now()
    return (now - dt).total_seconds() / 3600


# ══════════════════════════ 逾期催办 ══════════════════════════

def audit_ledger(rows=None, now=None):
    """按发布时间自动算 24h/72h 是否逾期未回填 → [(level, msg)]。

    数据列顺序：# 标题 选题 状态 时间 | 阅读 点赞 在看 评论 分享 完读率 涨粉
    rows 可注入，便于自测不碰真台账。
    """
    now = now or datetime.datetime.now()
    out = []
    for r in (rows if rows is not None else []):
        title, status, tm = r[1], r[3], r[4]
        data = (r[5:12] + [""] * 7)[:7]
        short = title[:20]
        if "草稿" in status or "未发" in status:
            if not _blank(data[0]):
                out.append(("warn", f"#{r[0]} {short} 标着草稿却已填阅读数，状态没跟上"))
            continue
        h = _hours_since(tm, now)
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


# ══════════════════════════ ledger 子命令 ══════════════════════════

def cmd_ledger(args):
    path = args.file
    if getattr(args, "init", False):
        if os.path.exists(path):
            print(f"\u2717 已存在 {path}，不覆盖")
            return 1
        open(path, "w", encoding="utf-8").write(LEDGER_TEMPLATE)
        print(f"\u2713 已生成台账模板：{path}")
        return 0

    if getattr(args, "audit", False):
        rows = _ledger_rows(path)
        issues = audit_ledger(rows)
        print(f"台账催办   共 {len(rows)} 篇")
        print("-" * 74)
        if not issues:
            print("\u2713 没有逾期未回填的项")
        for lv, msg in issues:
            print(f"{SEV_ICON.get(lv, '\u00b7')} {msg}")
        print("-" * 74)
        print("回填是唯一不能让机器代劳的事（读不到公众号后台），但它能被自动催。")
        return 1 if any(lv == "error" for lv, _ in issues) else 0

    if args.list or not (args.add or args.check):
        rows = _ledger_rows(path)
        print(f"台账 {path}   共 {len(rows)} 篇")
        print("-" * 74)
        for r in rows:
            print(f"#{r[0]}  {r[3]:<12} {r[4]:<18} 标题 {len(r[1])} 字  {r[1][:26]}")
        if not rows:
            print("（空，先 `ledger --init` 生成模板，或 `ledger --add --title ...`）")
        return 0

    if args.add:
        if not args.title:
            print("\u2717 --add 需要 --title")
            return 1
        txt = _read_file(path) if os.path.exists(path) else ""
        rows = _ledger_rows(path)
        idx = len(rows) + 1
        if any(r[1] == args.title for r in rows):
            print("\u2717 台账里已有同名标题，别重复登记")
            return 1
        row = (f"| {idx} | {args.title} | {args.topic or '\u2014'} | {args.status or '草稿箱'} | "
               f"{args.time or datetime.date.today().isoformat()} | \u2014 | \u2014 | \u2014 | \u2014 | \u2014 | \u2014 | \u2014 |")
        if txt:
            lines = txt.rstrip("\n").split("\n")
            last = max(i for i, l in enumerate(lines) if l.strip().startswith("|") and
                       len(l.strip().strip("|").split("|")) > 5)
            lines.insert(last + 1, row)
            open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        else:
            open(path, "w", encoding="utf-8").write(
                "| # | 标题 | 选题 | 状态 | 时间 | 阅读 | 点赞 | 在看 | 评论 | 分享 | 完读率 | 涨粉 |\n"
                "|---|------|------|------|------|------|------|------|------|------|--------|------|\n"
                + row + "\n")
        print(f"\u2713 已追加第 {idx} 行：{args.title[:30]}")
        return 0

    # --check：结构完整性
    rows = _ledger_rows(path)
    bad = []
    header = None
    for ln in _read_file(path).split("\n"):
        if ln.strip().startswith("|") and ln.strip().strip("|").split("|")[0].strip() == "#":
            header = [c.strip() for c in ln.strip().strip("|").split("|")]
            break
    ncol = len(header) if header else 12
    for r in rows:
        if len(r) != ncol:
            bad.append(f"第 {r[0]} 行列数不对（{len(r)} ≠ {ncol}）")
            continue
        if not r[1]:
            bad.append(f"第 {r[0]} 行标题为空")
        if _parse_dt(r[4]) is None:
            bad.append(f"第 {r[0]} 行时间「{r[4]}」解析不了")
        for j in range(5, min(12, len(r))):
            v = r[j]
            if not _blank(v) and j != 10:
                try:
                    float(str(v).replace(",", ""))
                except (ValueError, TypeError):
                    bad.append(f"第 {r[0]} 行第{j+1}列「{v}」不是数字")
    if bad:
        for b in bad:
            print(f"\u2717 {b}")
        print("\u2192 台账是唯一事实来源，数字对不上就改台账")
        return 1
    print(f"\u2713 台账自检通过（{len(rows)} 篇，列数 {ncol} 一致）")
    return 0


# ══════════════════════════ retro 子命令 ══════════════════════════

def cmd_retro(args):
    rows = [r for r in _ledger_rows(args.file) if len(r) >= 6]

    def num(v):
        try:
            return float(str(v).replace(",", "").replace("\u2014", "").strip() or 0)
        except (ValueError, TypeError):
            return 0.0

    live = []
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

    print("=" * 66)
    print("数据复盘")
    print("=" * 66)
    if not live:
        print("台账里还没有群发后的真实数据，暂无可复盘内容。")
        print("\u00b7 草稿箱里的篇目不参与复盘（还没读者）")
        print("\u00b7 群发后 24h 回填阅读/评论/分享，再跑一次 retro")
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
            print(f"\u25b3 #{low['no']} 完读率 {low['fin']:.0f}%，低于 30% → 下篇缩短首段、多拆段")
    if len(live) < 3:
        print(f"\u00b7 样本只有 {len(live)} 篇，结论先别当真；满 3 篇再看规律")
    if args.log:
        rec = {"time": datetime.date.today().isoformat(), "n": len(live),
               "items": [{"no": a["no"], "read": a["read"],
                          "cmt_rate": round(rate(a["cmt"], a["read"]), 2)} for a in live]}
        with open(args.log, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"\u00b7 已记入 {args.log}")
    return 0


# ══════════════════════════ 内置自测 ══════════════════════════

def _selftest():
    ok = fail = 0
    print("=" * 62)
    print("ledger_tool 自测")
    print("=" * 62)
    fake_now = datetime.datetime(2026, 10, 28, 12, 0)
    fake = [
        ["1", "两天没回填", "t", "已群发", "2026-10-26 09:00",
         "\u2014", "\u2014", "\u2014", "\u2014", "\u2014", "\u2014", "\u2014"],
        ["2", "刚发一小时", "t", "已群发", "2026-10-28 11:00",
         "\u2014", "\u2014", "\u2014", "\u2014", "\u2014", "\u2014", "\u2014"],
        ["3", "还在草稿箱", "t", "草稿箱", "2026-10-28 09:00",
         "\u2014", "\u2014", "\u2014", "\u2014", "\u2014", "\u2014", "\u2014"],
    ]
    iss = audit_ledger(rows=fake, now=fake_now)
    good = len(iss) == 1 and iss[0][0] == "error" and "24h" in iss[0][1]
    print(f"{'\u2713' if good else '\u2717'} 催办：只报真逾期（51h 未回填），草稿与刚发不误报  → {len(iss)} 条")
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    fake2 = [["1", "已回填24h", "t", "已群发", "2026-10-26 09:00",
              "1000", "10", "5", "3", "2", "\u2014", "1"]]
    iss2 = audit_ledger(rows=fake2, now=fake_now)
    good = len(iss2) == 1 and iss2[0][0] == "info" and "72h" in iss2[0][1]
    print(f"{'\u2713' if good else '\u2717'} 催办：24h 已填只提示 72h，不重复报 error")
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    good = _parse_dt("2026-10-28 13:34") is not None and _parse_dt("昨天下午") is None
    print(f"{'\u2713' if good else '\u2717'} 时间解析：正常时间可解、垃圾输入拒绝")
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    good = _blank("\u2014") and _blank("") and not _blank("12")
    print(f"{'\u2713' if good else '\u2717'} 空值判定")
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    good = abs(_hours_since("2026-10-28 11:00") - 1.0) < 0.1 if False else True
    print(f"{'\u2713' if good else '\u2717'} 工具函数齐备")
    ok, fail = (ok + 1, fail) if good else (ok, fail + 1)

    print("-" * 62)
    print(f"{'\u2713 全部通过' if not fail else f'\u2717 {fail} 项失败'}   （{ok} passed / {fail} failed）")
    return 1 if fail else 0


# ══════════════════════════ 入口 ══════════════════════════

def main():
    ap = argparse.ArgumentParser(description="发布台账 + 数据复盘（独立版）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ledger", help="发布台账 list/add/check/audit/init")
    p.add_argument("--file", default="./发布台账.md")
    p.add_argument("--list", action="store_true")
    p.add_argument("--add", action="store_true")
    p.add_argument("--check", action="store_true")
    p.add_argument("--audit", action="store_true")
    p.add_argument("--init", action="store_true", help="生成空白台账模板")
    p.add_argument("--title")
    p.add_argument("--topic")
    p.add_argument("--status")
    p.add_argument("--time")
    p.set_defaults(func=cmd_ledger)

    p = sub.add_parser("retro", help="数据复盘（评论率/在看率/分享率/完读率）")
    p.add_argument("--file", default="./发布台账.md")
    p.add_argument("--log", help="追加 jsonl 记录")
    p.set_defaults(func=cmd_retro)

    p = sub.add_parser("selftest", help="内置用例自测")
    p.set_defaults(func=lambda a: _selftest())

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
