#!/usr/bin/env python3
"""
超级运营中枢 v1.0 - 一键驱动微爆工坊全系统（15个脚本统一入口）
用法：
  python3 scripts/super_hub.py status          # 系统体检（内容库/数据/覆盖率/定时任务提示）
  python3 scripts/super_hub.py daily           # 日常一条龙：体检+选稿+排期+数据
  python3 scripts/super_hub.py generate <主题> <数量>   # 生成并自动查重入库
  python3 scripts/super_hub.py gene <基因型> <数量>     # 爆款基因生成
  python3 scripts/super_hub.py pick [--day N] [--slot X] [--exclude ID]  # 智能选稿
  python3 scripts/super_hub.py plan [N]        # 智能排期
  python3 scripts/super_hub.py quality <ID>    # 质检
  python3 scripts/super_hub.py reply <评论> [主题]  # 评论回复草稿
  python3 scripts/super_hub.py analyze         # 数据优化分析
  python3 scripts/super_hub.py dashboard       # 刷新看板
  python3 scripts/super_hub.py optimize        # 超级优化器
"""
import json
import os
import subprocess
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")

def run(*args):
    """运行子脚本"""
    return subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, args[0])] + list(args[1:]),
        capture_output=True, text=True, encoding="utf-8"
    ).stdout

def cmd_status():
    """系统体检"""
    print("=" * 60)
    print("🧠 微爆工坊超级运营中枢 - 系统体检")
    print("=" * 60)

    # 1. 内容库
    out = run("content_engine.py", "stats")
    for line in out.splitlines():
        if "库存" in line or "待发布" in line.lower():
            print(f"📦 {line.strip()}")

    # 2. 数据（真实数据未采集时优雅降级）
    try:
        import csv
        rows = list(csv.DictReader(open(os.path.join(BASE, "references/perfomance_tracking.csv"), encoding="utf-8")))
        print(f"📊 数据样本: {len(rows)}条真实记录")
        opt = json.load(open(os.path.join(BASE, "references/optimizer_state.json"), encoding="utf-8"))
        print(f"🎯 最优题材: {opt['best_theme']} (点击率最优: {opt['best_ctr_theme']})")
    except FileNotFoundError:
        print("📊 数据样本: 暂无（发布后由 data_tracker 记录性能数据）")
    except Exception as e:
        print(f"📊 数据读取跳过: {e}")

    # 3. 覆盖率
    out = run("smart_selector.py", "analyze")
    lines = [l for l in out.splitlines() if "%" in l]
    for l in lines:
        print(f"📅 {l.strip()}")

    # 4. 评论快照
    try:
        snap = json.load(open(os.path.join(BASE, "references/comment_snapshot.json"), encoding="utf-8"))
        pending_c = [c for c in snap.get("comments", []) if c.get("status") == "新待回复"]
        print(f"💬 评论快照: {len(snap.get('comments', []))}条 (待回复{len(pending_c)})")
    except FileNotFoundError:
        print("💬 评论快照: 暂无（接入后台或手动录入后显示）")

    print("=" * 60)
    print("✅ 体检完成")

def cmd_daily():
    """日常一条龙"""
    print("🔄 日常一条龙启动...")
    cmd_status()
    print()
    print("📋 今日推荐（晚间档）:")
    print(run("smart_selector.py", "next", "--slot", "evening").strip())
    print()
    print("📅 未来3天排期:")
    print(run("schedule_planner.py", "next", "3").strip())

def cmd_generate(theme, count):
    print(run("content_generator.py", "save", theme, str(count)).strip())

def cmd_gene(gene, count):
    print(run("content_generator.py", "gene", gene, str(count)).strip())

def cmd_pick(day=None, slot=None, exclude=None):
    args = ["smart_selector.py", "next"]
    if day is not None: args += ["--day", str(day)]
    if slot: args += ["--slot", slot]
    if exclude: args += ["--exclude", exclude]
    print(run(*args).strip())

def cmd_plan(days):
    print(run("schedule_planner.py", "next", str(days)).strip())

def cmd_quality(cid):
    print(run("quality_checker.py", "check", cid).strip())

def cmd_reply(comment, theme=None):
    args = ["comment_reply.py", "reply", comment]
    if theme: args.append(theme)
    print(run(*args).strip())

def cmd_analyze():
    print(run("content_optimizer.py", "analyze").strip())

def cmd_dashboard():
    print(run("generate_dashboard.py").strip())

def cmd_optimize():
    print(run("super_optimizer.py").strip())

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "status": cmd_status()
    elif cmd == "daily": cmd_daily()
    elif cmd == "generate" and len(sys.argv) >= 4: cmd_generate(sys.argv[2], int(sys.argv[3]))
    elif cmd == "gene" and len(sys.argv) >= 4: cmd_gene(sys.argv[2], int(sys.argv[3]))
    elif cmd == "pick": cmd_pick()
    elif cmd == "plan": cmd_plan(int(sys.argv[2]) if len(sys.argv) > 2 else 7)
    elif cmd == "quality" and len(sys.argv) >= 3: cmd_quality(sys.argv[2])
    elif cmd == "reply" and len(sys.argv) >= 3: cmd_reply(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "analyze": cmd_analyze()
    elif cmd == "dashboard": cmd_dashboard()
    elif cmd == "optimize": cmd_optimize()
    else:
        print(f"❌ 未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
