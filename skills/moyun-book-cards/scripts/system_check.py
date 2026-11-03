#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
system_check.py —— 一键健康检查中心（墨韵拆书卡 v1.7.0）

系统的「体检中心」：一条命令跑完 回归测试 → 真实性审计 → 自诊断自修复，
收集核心指标，输出 SYSTEM_REPORT.md + dashboard.html（可视化仪表盘），
并把本次体检写入 evolution_log.md（自我进化日志）。

用法：
  python system_check.py           # 全项体检（含出图测试，约 30-60 秒）
  python system_check.py --quick   # 快检（跳过回归测试的出图环节）
"""
import os, sys, json, glob, subprocess, re
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def collect_metrics():
    lib = [json.load(open(f, encoding="utf-8")) for f in glob.glob(os.path.join(BASE, "library", "*.json"))]
    idx_path = os.path.join(BASE, "archive_index.json")
    idx = json.load(open(idx_path, encoding="utf-8")) if os.path.isfile(idx_path) else {}
    deep = sum(1 for d in lib if d.get("long_review"))
    quoted = sum(1 for d in lib if d.get("quote_status"))
    excerpt = sum(1 for d in lib if d.get("quote_status") == "excerpt")
    src = sum(1 for d in lib if d.get("source"))
    return {
        "books": len(lib), "periods": idx.get("total_periods", 0),
        "total_entries": idx.get("total_books", 0),
        "deep_reviews": deep, "quote_tagged": quoted, "excerpt": excerpt,
        "quote_coverage": round(quoted / len(lib) * 100, 1) if lib else 0,
        "source_coverage": round(src / len(lib) * 100, 1) if lib else 0,
    }


def run(label, args):
    r = subprocess.run([PY] + args, cwd=BASE, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    ok = r.returncode == 0
    print(f"  {'✅' if ok else '❌'} {label}")
    return ok


def main():
    quick = "--quick" in sys.argv
    t0 = datetime.now()
    print("== 墨韵拆书 · 系统健康检查 ==")

    print("[1/4] 自诊断自修复（doctor）")
    ok_doctor = run("doctor.py", ["doctor.py"])
    doctor_rep = open(os.path.join(BASE, "doctor_report.md"), encoding="utf-8").read() \
        if os.path.isfile(os.path.join(BASE, "doctor_report.md")) else ""

    print("[2/4] 真实性审计（audit）")
    ok_audit = run("audit_data.py", ["audit_data.py"])

    print("[3/4] 回归测试（test_suite）" + ("（quick 跳过）" if quick else ""))
    if quick:
        ok_test, test_line = True, "quick 模式跳过"
    else:
        r = subprocess.run([PY, os.path.join(BASE, "test_suite.py")], cwd=BASE,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        ok_test = r.returncode == 0
        m = re.search(r"（(\d+) 项）", r.stdout or "")
        test_line = f"{'✅ 全部通过' if ok_test else '❌ 存在失败'}（{(m.group(1) if m else '?')} 项）"
        print(f"  {'✅' if ok_test else '❌'} 回归测试 {test_line}")

    print("[4/4] 指标收集")
    M = collect_metrics()
    health = sum([ok_doctor, ok_audit, ok_test]) / 3 * 100

    rep = [f"# 系统健康检查报告（{t0.strftime('%Y-%m-%d %H:%M')}）", "",
           f"## 总体健康度：{'🟢' if health == 100 else '🟡'} {health:.0f}%", "",
           "| 检查项 | 结果 |", "| --- | --- |",
           f"| 自诊断自修复（doctor） | {'✅' if ok_doctor else '❌'} |",
           f"| 真实性审计（audit） | {'✅' if ok_audit else '❌'} |",
           f"| 回归测试（test_suite） | {test_line} |", "",
           "## 核心指标", "",
           f"- 内容库：**{M['books']} 本**（去重出场 {M['total_entries']} 本 / {M['periods']} 期）",
           f"- 深度书评：{M['deep_reviews']} 本",
           f"- 金句标注覆盖率：{M['quote_coverage']}%（excerpt {M['excerpt']} 本）",
           f"- 来源标注覆盖率：{M['source_coverage']}%", ""]
    if os.path.isfile(os.path.join(BASE, "doctor_report.md")):
        rep += ["## 自诊断详情", "", doctor_rep]
    open(os.path.join(BASE, "SYSTEM_REPORT.md"), "w", encoding="utf-8").write("\n".join(rep))

    # 仪表盘
    dash = """<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>墨韵拆书 · 系统仪表盘</title><style>
body{font-family:system-ui,"Microsoft YaHei";margin:0;background:#f6f4ee;color:#2c2c2a}
header{background:#2c2c2a;color:#fff;padding:20px 24px}header h1{margin:0;font-size:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;padding:22px;max-width:1000px;margin:0 auto}
.card{background:#fff;border-radius:12px;padding:18px;box-shadow:0 1px 3px #0001;border-top:4px solid #993C1D}
.card .v{font-size:30px;font-weight:600}.card .l{color:#888780;font-size:13px;margin-top:4px}
.ok{border-top-color:#3B6D11}.foot{text-align:center;color:#888780;font-size:12px;padding:18px}
</style></head><body><header><h1>🩺 墨韵拆书 · 系统健康仪表盘</h1></header>
<div class="grid">
__CARDS__
</div><div class="foot">体检时间 __TIME__ · system_check.py v1.7.0 · 健康__HEALTH__</div></body></html>"""
    cards = [
        (f"{M['books']}", "内容库书目", "ok"), (f"{M['periods']}", "出版期次", "ok"),
        (f"{M['deep_reviews']}", "深度书评", ""), (f"{M['quote_coverage']}%", "金句标注覆盖率", "ok"),
        (f"{M['source_coverage']}%", "来源标注覆盖率", "ok"),
        (f"{health:.0f}%", "总体健康度", "ok" if health == 100 else ""),
    ]
    html = dash.replace("__CARDS__", "".join(
        f'<div class="card {c}"><div class="v">{v}</div><div class="l">{l}</div></div>' for v, l, c in cards
    )).replace("__TIME__", t0.strftime("%Y-%m-%d %H:%M")).replace("__HEALTH__", f"{health:.0f}%")
    open(os.path.join(BASE, "dashboard.html"), "w", encoding="utf-8").write(html)

    # 进化日志
    with open(os.path.join(BASE, "evolution_log.md"), "a", encoding="utf-8") as f:
        f.write(f"\n- **{t0.strftime('%Y-%m-%d %H:%M')}** 体检：健康度 {health:.0f}% | "
                f"库 {M['books']} 本 / {M['periods']} 期 / 深拆 {M['deep_reviews']} | "
                f"金句标注 {M['quote_coverage']}% | doctor修复见 doctor_report.md\n")

    print(f"\n🏥 体检完成，健康度 {health:.0f}%")
    print("  SYSTEM_REPORT.md | dashboard.html | evolution_log.md 已更新")


if __name__ == "__main__":
    main()
