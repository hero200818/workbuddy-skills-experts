# -*- coding: utf-8 -*-
"""auto_weekly.py — 榜单抓取 → 选书 → 补全 → 出卡 一条龙（全程无需手抄）

用法：
  python auto_weekly.py --fetch                 # 自动抓取榜单→生成周报→选前8→出卡
  python auto_weekly.py --fetch --seed          # 抓取走内置种子兜底（离线/限流）
  python auto_weekly.py --fetch 6              # 选前 6 本
  python auto_weekly.py 周报.md                 # 指定已有周报
  python auto_weekly.py 周报.md 8 --no-gen     # 只到 books.json，不出图

流程：
  1. （--fetch 时）fetch_bestsellers.py 抓榜单 → 生成 全网畅销书周报-YYYY-MM-DD.md
  2. parse_weekly.py 解析 TOP20 → 加权打分选前 N → lite_auto.json
  3. enrich.py 查 library/ 复用，缺失则退出并提示由 AI 补全后重跑
  4. 包成 <期号>_input.json 喂给 gen_cards_ios.py 出图

依赖：同目录的 fetch_bestsellers.py / parse_weekly.py / enrich.py / gen_cards_ios.py 与 library/
"""
import os, sys, re, json, glob, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
TODAY = __import__("datetime").date.today().strftime("%Y-%m-%d")


def run(cmd):
    print("›", " ".join(cmd))
    return subprocess.run(cmd, cwd=BASE).returncode


def find_latest_weekly():
    fs = sorted(glob.glob(os.path.join(BASE, "全网畅销书周报*.md")), reverse=True)
    return fs[0] if fs else None


def infer_issue(weekly_path):
    """从周报文件名推断期号与日期。"""
    base = os.path.basename(weekly_path)
    m = re.search(r"第\s*(\d+)\s*周", base)
    if m:
        return f"第{m.group(1)}周", TODAY
    dm = re.search(r"(\d{4})-(\d{2})-(\d{2})", base)
    if dm:
        d = dm.group(0)
        return f"周榜·{d}", d
    return "周榜", TODAY


def main():
    argv = sys.argv[1:]
    fetch = "--fetch" in argv
    seed = "--seed" in argv
    no_gen = "--no-gen" in argv
    argv = [a for a in argv if a not in ("--fetch", "--seed", "--no-gen")]

    weekly = None
    top_n = 8
    if argv and not argv[0].startswith("--"):
        weekly = argv[0]
        if len(argv) > 1:
            try:
                top_n = int(argv[1])
            except ValueError:
                pass

    lite = os.path.join(BASE, "lite_auto.json")
    full = os.path.join(BASE, "books.full.json")

    # 0) 抓取阶段
    if fetch:
        cmd = [PY, os.path.join(BASE, "fetch_bestsellers.py"), "--out", BASE]
        if seed:
            cmd.append("--seed")
        if run(cmd) != 0:
            print("❌ 抓取失败，且种子兜底也未成功"); sys.exit(1)
        weekly = find_latest_weekly()
        if not weekly:
            print("❌ 抓取后未找到周报 md"); sys.exit(1)

    if not weekly:
        weekly = find_latest_weekly()
    if not weekly:
        print("❌ 未找到周报，请传入路径或加 --fetch"); sys.exit(1)

    issue, date = infer_issue(weekly)
    safe_issue = re.sub(r'[\\/:*?"<>|]', "_", issue)

    # 1) 解析 + 选书
    p1 = [PY, os.path.join(BASE, "parse_weekly.py"), weekly, lite, str(top_n)]
    if run(p1) != 0:
        print("❌ 解析周报失败"); sys.exit(1)

    # 2) 补全内容库
    if run([PY, os.path.join(BASE, "enrich.py"), lite, full]) != 0:
        print("\n⚠️ 有书目内容库缺失，请让我（AI）按 .missing.json 补全并写回 library/ 后，"
              "重新执行本命令（去掉参数也行）即可自动出卡。")
        sys.exit(2)

    # 3) 包成生成器输入并出图
    books = json.load(open(full, encoding="utf-8"))
    wrap = {"issue": issue, "date": date, "kind": "weekly",
            "short": f"墨韵拆书 · {issue}",
            "note": "由 fetch_bestsellers 自动抓取榜单 + parse_weekly 选书 + enrich 内容库复用生成",
            "books": books}
    inp = os.path.join(BASE, f"{safe_issue}_input.json")
    json.dump(wrap, open(inp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ 已生成 {inp}（{len(books)} 本）")

    if no_gen:
        print("（--no-gen：已停止于 books.json，未出图）"); return

    out_base = os.path.abspath(os.path.join(BASE, "..", "畅销书拆书卡"))
    if run([PY, os.path.join(BASE, "gen_cards_ios.py"), inp, issue, date, out_base]) != 0:
        print("❌ 出图失败"); sys.exit(1)
    print(f"\n🎉 完成：{issue} 卡片已生成到 畅销书拆书卡/{safe_issue}/")


if __name__ == "__main__":
    main()
