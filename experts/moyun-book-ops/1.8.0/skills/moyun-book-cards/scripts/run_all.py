#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_all.py —— 全链路一条龙（墨韵拆书卡 v1.5.0）

抓榜 → 选书 → 补全 → 出卡 → 版式扩展 → 分发文案 → 质检 → 趋势沉淀 → 档案更新，
一条命令跑完整个"杂志社"。配合 WorkBuddy 定时任务实现每周全自动出版。

用法：
  python run_all.py                # 全链路（联网抓榜，失败自动种子兜底）
  python run_all.py --seed         # 离线模式（走内置真实种子榜单）
  python run_all.py --top 6        # 选前 6 本
  python run_all.py --no-extra     # 不出海报/导图等扩展版式

任一环节失败即停并明确报告；enrich 遇库外书（返回码 2）会列出待补清单，
由 AI 补全写回 library/ 后重跑即可。
"""
import os, sys, json, subprocess, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
CARD_ROOT = os.environ.get("MOYUN_CARD_ROOT", os.path.join(os.getcwd(), "畅销书拆书卡"))


def run(label, args, check=True, capture=False):
    print(f"\n========== {label} ==========")
    r = subprocess.run([PY] + args, cwd=BASE,
                       capture_output=capture, text=True,
                       encoding="utf-8", errors="replace")
    if capture and r.stdout:
        print(r.stdout.strip()[-2000:])
    if r.returncode != 0 and check:
        if capture and r.stderr:
            print(r.stderr.strip()[-1500:])
        print(f"❌ {label} 失败（exit {r.returncode}），全链路中止。")
        sys.exit(r.returncode)
    return r


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", action="store_true", help="离线模式：走内置种子榜单")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--no-extra", action="store_true", help="不出海报/思维导图扩展版式")
    ap.add_argument("--no-distribute", action="store_true", help="不生成分发包")
    args = ap.parse_args()

    date_str = datetime.date.today().strftime("%Y-%m-%d")
    print(f"★★★ 墨韵拆书 · 全链路自动出版 {date_str} ★★★")

    # 1) 抓榜生成周报
    fetch_args = ["fetch_bestsellers.py"] + (["--seed"] if args.seed else []) + ["--out", BASE]
    run("① 榜单抓取", fetch_args, capture=True)
    report = os.path.join(BASE, f"全网畅销书周报-{date_str}.md")
    if not os.path.exists(report):
        import glob
        cands = sorted(glob.glob(os.path.join(BASE, "全网畅销书周报-*.md")))
        if not cands:
            print("❌ 无周报可用"); sys.exit(2)
        report = cands[-1]
    print(f"周报：{os.path.basename(report)}")

    # 2) 解析选书
    lite = os.path.join(BASE, "lite_auto.json")
    run("② 解析 TOP20 + 加权选书", ["parse_weekly.py", report, lite, str(args.top)], capture=True)

    # 3) 内容库补全
    full = os.path.join(BASE, "books.full.json")
    r = run("③ enrich 内容库复用", ["enrich.py", lite, full], check=False)
    if r.returncode == 2:
        miss = full + ".missing.json"
        names = [b["title"] for b in json.load(open(miss, encoding="utf-8"))] if os.path.exists(miss) else []
        print("⚠️ 发现库外书，待 AI 补全后重跑：", "、".join(names))
        sys.exit(2)

    # 4) 出九宫格
    books = json.load(open(full, encoding="utf-8"))
    n_wk = datetime.date.today().isocalendar()[1]
    issue = f"第{n_wk}周"
    inp = os.path.join(BASE, f"{issue}_input.json")
    json.dump({"issue": issue, "date": date_str, "kind": "weekly",
               "short": f"墨韵拆书 · {issue}", "note": "run_all 全自动生成", "books": books},
              open(inp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    run("④ 九宫格出卡", ["gen_cards_ios.py", inp, issue, date_str, CARD_ROOT], capture=True)
    period_dir = os.path.join(CARD_ROOT, issue)

    # 5) 扩展版式 + 思维导图（示范第一本）
    if not args.no_extra and books:
        run("⑤ 版式扩展（公众号封面/海报/方形）",
            ["gen_extra.py", period_dir, "--book", books[0]["title"]], capture=True)
        run("⑥ 深度拆书思维导图",
            ["gen_mindmap.py", period_dir, "--book", books[0]["title"]], capture=True)

    # 6) 分发文案
    if not args.no_distribute:
        run("⑦ 三平台分发文案", ["distribute.py", period_dir], capture=True)

    # 7) 质检
    run("⑧ 自动质检", ["qc.py", period_dir], capture=False)

    # 8) 趋势沉淀 + 档案更新
    run("⑨ 榜单趋势库", ["trend.py", "build"], capture=True)
    run("⑩ 拆书档案更新", ["archive.py"], capture=True)

    print(f"\n🎉 全链路完成！本期《{issue}》已就绪：")
    print(f"   九宫格  → {period_dir}")
    if not args.no_distribute:
        print(f"   分发包  → 分发包/{issue}/")
    print("   剩下最后一步：爷爷审阅后，到各平台客户端点击发布。")


if __name__ == "__main__":
    main()
