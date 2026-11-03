#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_suite.py —— 全链路回归测试（墨韵拆书卡 v1.6.0）

seed 模式快速验证十环流水线的关键产物，改代码后跑一遍即知有没有改坏：
  1) 趋势库构建与产物          5) mini 出卡（2 本→临时目录）
  2) 档案重建与查询            6) 质检器可运行
  3) enrich 全复用（demo）      7) 标题工坊 / 口播脚本 / 审阅页产物
  4) 周报解析选书

用法：python test_suite.py    （exit 0 = 全部通过；输出 test_report.md）
"""
import os, sys, json, glob, subprocess, tempfile, shutil
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
CARD_ROOT = os.environ.get("MOYUN_CARD_ROOT", os.path.join(os.getcwd(), "畅销书拆书卡"))
RESULTS = []


def step(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(f"  {'✅' if ok else '❌'} {name}" + (f" — {detail}" if detail else ""))
    return ok


def run(args, **kw):
    return subprocess.run([PY] + args, cwd=BASE, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def main():
    print("== 墨韵拆书卡 · 回归测试 ==")

    # 1) 趋势库
    r = run(["trend.py", "build"])
    ok = r.returncode == 0 and os.path.isfile(os.path.join(BASE, "trend_store.json")) \
        and os.path.isfile(os.path.join(BASE, "trend_highlights.txt"))
    step("趋势库 build 与产物", ok)

    # 2) 档案
    r = run(["archive.py"])
    idx = json.load(open(os.path.join(BASE, "archive_index.json"), encoding="utf-8")) if r.returncode == 0 else {}
    step("档案重建（期数/书目>0）", idx.get("total_periods", 0) > 0 and idx.get("total_books", 0) > 0,
         f"{idx.get('total_periods', 0)} 期 / {idx.get('total_books', 0)} 本")

    # 3) enrich 全复用
    r = run(["enrich.py", "lite_demo.json", "test_books.json"])
    step("enrich 全复用（exit 0）", r.returncode == 0)

    # 4) 周报解析选书
    r = run(["parse_weekly.py", os.path.join(BASE, "全网畅销书周报-2026-10-27.md"),
             "test_lite.json", "8"])
    step("周报解析选书 8 本", r.returncode == 0 and os.path.isfile(os.path.join(BASE, "test_lite.json")))

    # 5) mini 出卡（2 本 → 临时目录）
    books = json.load(open(os.path.join(BASE, "test_books.json"), encoding="utf-8"))[:2]
    mini = {"issue": "回归测试期", "date": "test", "kind": "weekly",
            "short": "测试", "books": books}
    tmp = tempfile.mkdtemp(prefix="moyun_test_")
    inp = os.path.join(tmp, "input.json")
    json.dump(mini, open(inp, "w", encoding="utf-8"), ensure_ascii=False)
    r = run(["gen_cards_ios.py", inp, "回归测试期", "test", tmp])
    imgs = glob.glob(os.path.join(tmp, "*", "*.jpg"))
    ok = r.returncode == 0 and len(imgs) == 3 and "末笔" in r.stdout and "1180" in r.stdout
    step("mini 出卡（封面+2书卡，末笔<1180）", ok, f"{len(imgs)} 图")
    # 清理临时目录里的测试期（避免污染正式出卡根目录统计）
    if os.path.isdir(tmp):
        shutil.rmtree(tmp, ignore_errors=True)

    # 6) 质检器（对第44周，只验证可运行）
    p44 = os.path.join(CARD_ROOT, "第44周")
    if os.path.isdir(p44):
        r = run(["qc.py", p44])
        step("质检器运行", r.returncode == 0 and os.path.isfile(os.path.join(p44, "qc_report.md")))

        # 7) 配套产物
        run(["title_lab.py", p44])
        step("标题工坊产物", os.path.isfile(os.path.join(p44, "title_lab.md")))
        run(["speech_gen.py", p44])
        step("口播脚本产物", os.path.isfile(os.path.join(p44, "口播脚本.md")))
        run(["review_page.py", p44])
        step("审阅页产物", os.path.isfile(os.path.join(p44, "review.html")))
        run(["interactive.py", p44])
        step("互动套件产物", os.path.isfile(os.path.join(p44, "vote_下期投票.jpg")))

    # 汇总
    fails = [x for x in RESULTS if not x[1]]
    rep = [f"# 回归测试报告（{datetime.now().strftime('%Y-%m-%d %H:%M')}）", "",
           f"**结论：{'✅ 全部通过' if not fails else '❌ %d 项失败' % len(fails)}（{len(RESULTS)} 项）**", ""]
    for name, ok, detail in RESULTS:
        rep.append(f"- {'✅' if ok else '❌'} {name}" + (f" — {detail}" if detail else ""))
    open(os.path.join(BASE, "test_report.md"), "w", encoding="utf-8").write("\n".join(rep))
    print(f"\n{'🎉 全部通过' if not fails else '⚠️ 存在失败项'}，报告：test_report.md")
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
