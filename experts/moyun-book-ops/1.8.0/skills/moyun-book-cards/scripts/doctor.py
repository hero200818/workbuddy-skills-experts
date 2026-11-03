#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doctor.py —— 自诊断 + 自修复引擎（墨韵拆书卡 v1.7.0）

系统的「自我保健」：检查常见病灶并自动修复可修复项，输出 doctor_report.md。

检查项（★=可自动修复）：
  ★ 库条目字段缺失（quote_status / quote_note / source / created_at）→ 自动补默认值
  ★ 期目录孤儿图（无 books.json 的 jpg 目录残留）→ 报告并列出
  ★ 期目录旧图（不在发布清单中的数字前缀 jpg）→ 自动清理
  ★ books.json 与卡片文件数量不一致 → 报告
  ⚠ 超长标题（title>10 字）→ 预警（建议库内短名）
  ⚠ 重复书目（norm(title) 相同的多条目）→ 报告建议合并
  ★ 档案过期（archive_index 落后于实际期数）→ 自动重建

用法：
  python doctor.py            # 诊断 + 自动修复 + 报告
  python doctor.py --dry      # 只诊断不修复
"""
import os, sys, json, re, glob, shutil
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(BASE, "library")
CARD_ROOT = os.environ.get("MOYUN_CARD_ROOT", os.path.join(os.getcwd(), "畅销书拆书卡"))
FIXES, WARNS, INFOS = [], [], []


def norm(t):
    return re.sub(r"[^\w\u4e00-\u9fff]", "", str(t).lower())


def check_library(dry=False):
    for f in sorted(glob.glob(os.path.join(LIB, "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        t = d.get("title", "")
        changed = False
        if not d.get("quote_status"):
            known_ok = t in ("活着", "三体（全集）", "遥远的救世主", "蛤蟆先生去看心理医生",
                             "明朝那些事儿", "我与地坛", "长安的荔枝")
            d["quote_status"] = "excerpt" if known_ok else "paraphrase"
            d["quote_note"] = ("可证原文摘录" if known_ok else
                               "主旨转述，非逐字原文——引用时请勿标注为书中原句")
            changed = True
        if not d.get("source"):
            d["source"] = "早期内容库（源头待补档）"
            changed = True
        if not d.get("created_at"):
            d["created_at"] = datetime.now().strftime("%Y-%m-%d")
            changed = True
        if changed and not dry:
            json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            FIXES.append(f"库字段补全：《{t}》")
        if len(t) > 10:
            WARNS.append(f"超长标题：《{t}》（{len(t)}字），70pt 卡片可能换行，建议库内改短名")


def check_duplicates():
    seen = {}
    for f in sorted(glob.glob(os.path.join(LIB, "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        k = norm(d.get("title", ""))
        seen.setdefault(k, []).append(d.get("title"))
    for k, names in seen.items():
        if len(names) > 1:
            WARNS.append(f"疑似重复条目：{' / '.join(names)}（建议合并为一个 file）")


def check_periods(dry=False):
    n_periods = 0
    for p in sorted(os.listdir(CARD_ROOT)):
        d = os.path.join(CARD_ROOT, p)
        if not os.path.isdir(d):
            continue
        bj = os.path.join(d, "books.json")
        jpgs = sorted(f for f in os.listdir(d) if f.endswith(".jpg") and f[:2].isdigit())
        if not os.path.isfile(bj):
            if jpgs:
                WARNS.append(f"孤儿图目录：{p}/（{len(jpgs)} 张图无 books.json）")
            continue
        n_periods += 1
        try:
            data = json.load(open(bj, encoding="utf-8"))
        except Exception:
            WARNS.append(f"books.json 解析失败：{p}")
            continue
        books = data.get("books", [])
        expected = ["00_封面.jpg"] + [f"{i:02d}_{(b.get('file') or b['title'])}.jpg"
                                      for i, b in enumerate(books[:8], 1)]
        have = set(jpgs)
        want = set(os.path.basename(e) for e in expected)
        stale = have - want
        if stale and not dry:
            for s in stale:
                os.remove(os.path.join(d, s))
            FIXES.append(f"清理旧图 {len(stale)} 张：{p}")
        elif stale:
            WARNS.append(f"旧图待清理 {len(stale)} 张：{p}")
        missing = want - have
        if missing:
            WARNS.append(f"缺图 {len(missing)} 张：{p}（{sorted(missing)[:3]}…）" if len(missing) > 3
                         else f"缺图：{p}（{sorted(missing)}）")
    return n_periods


def check_archive(dry=False):
    idx_path = os.path.join(BASE, "archive_index.json")
    actual = sum(1 for p in os.listdir(CARD_ROOT)
                 if os.path.isfile(os.path.join(CARD_ROOT, p, "books.json")))
    recorded = 0
    if os.path.isfile(idx_path):
        recorded = json.load(open(idx_path, encoding="utf-8")).get("total_periods", 0)
    if recorded != actual:
        if not dry:
            subprocess = __import__("subprocess")
            subprocess.run([sys.executable, os.path.join(BASE, "archive.py")],
                           cwd=BASE, capture_output=True)
            FIXES.append(f"档案重建：{recorded} → {actual} 期")
        else:
            WARNS.append(f"档案过期（记录 {recorded} / 实际 {actual} 期）")
    else:
        INFOS.append(f"档案一致：{actual} 期")


def main():
    dry = "--dry" in sys.argv
    check_library(dry)
    check_duplicates()
    n = check_periods(dry)
    check_archive(dry)

    L = [f"# 自诊断报告（{datetime.now().strftime('%Y-%m-%d %H:%M')}）", "",
         f"- 检查范围：library 全库 + {n} 期书单目录 + 档案一致性",
         f"- 🔧 自动修复：{len(FIXES)} 项" + ("（--dry 未执行）" if dry else ""),
         f"- ⚠️ 预警（需人工决策）：{len(WARNS)} 项",
         f"- ℹ️ 正常：{len(INFOS)} 项", ""]
    if FIXES:
        L.append("## 自动修复明细")
        L += [f"- 🔧 {x}" for x in FIXES] + [""]
    if WARNS:
        L.append("## 预警明细")
        L += [f"- ⚠️ {x}" for x in WARNS] + [""]
    if INFOS:
        L.append("## 正常项")
        L += [f"- ✅ {x}" for x in INFOS]
    open(os.path.join(BASE, "doctor_report.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"🩺 自诊断完成：修复 {len(FIXES)} 项 | 预警 {len(WARNS)} 项 | 正常 {len(INFOS)} 项")
    print("报告：doctor_report.md")


if __name__ == "__main__":
    main()
