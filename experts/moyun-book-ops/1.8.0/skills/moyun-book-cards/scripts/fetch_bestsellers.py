#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_bestsellers.py —— 全网畅销书榜单抓取器（真·自动生成周报）

把京东 / 当当 / 微信读书等榜单做成结构化 fetcher，连「周报 Markdown」都省掉：
生成的周报可直接喂给 parse_weekly.py → 选前 8 → enrich → 出卡。

数据源（SOURCES 框架，可扩展）：
  - douban   : 豆瓣图书热门榜 book.douban.com/chart  —— 静态 HTML，用户本机直接 HTTP 抓取 ✅ 完整实现
  - jd       : 京东图书榜  —— 动态渲染 + 反爬，需带 cookie，已留扩展点（experimental）
  - dangdang : 当当畅销榜 —— 部分静态，已留扩展点（experimental）
  - weread   : 微信读书榜  —— 需登录态，已留扩展点（experimental）

兜底策略：真实抓取失败（限流 / 反爬 / 离线）或解析不足 8 本时，
自动回退到内置种子榜单（seeds/douban_hot_2026-10.json，真实快照），保证链路不崩。

输出（默认当前目录）：
  - 榜单快照-YYYY-MM-DD.json        原始抓取数据（含 source 标记，可审计）
  - 全网畅销书周报-YYYY-MM-DD.md    标准「综合热度 TOP20」表格，直接喂 parse_weekly.py

用法：
  python fetch_bestsellers.py                 # 自动抓取（失败回退种子）
  python fetch_bestsellers.py --seed          # 强制走种子榜单
  python fetch_bestsellers.py --source douban # 指定数据源
  python fetch_bestsellers.py --top 20        # 输出数量（默认 20）
  python fetch_bestsellers.py --out DIR       # 输出目录
"""
import os, re, sys, json, argparse, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
SEEDS_DIR = os.path.join(BASE, "seeds")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://book.douban.com/",
}

# ---------------------------------------------------------------------------
# 各数据源适配器：每个返回 [{rank,title,author,cat,score,url}] 或 None（失败）
# ---------------------------------------------------------------------------
def fetch_douban_chart():
    """豆瓣图书热门榜：静态 HTML，正则解析。用户本机可直接抓。"""
    try:
        import requests
        r = requests.get("https://book.douban.com/chart", headers=HEADERS, timeout=15)
        if r.status_code != 200 or len(r.text) < 2000:
            return None
        html = r.text
    except Exception:
        return None

    # 书名：subject 链接且文本非空
    subj_re = re.compile(r'href="https://book\.douban\.com/subject/(\d+)/"[^>]*>([^<]+)</a>')
    titles = []
    seen = set()
    for sid, name in subj_re.findall(html):
        name = name.strip()
        if name and name not in seen and len(name) <= 40:
            seen.add(name)
            titles.append({"title": name, "url": f"https://book.douban.com/subject/{sid}/"})
    if len(titles) < 8:
        return None

    # 评分
    scores = re.findall(r'class="rating_nums">([\d.]+)</span>', html)
    # 类别（tag）
    cats = re.findall(r'class="tag">([^<]+)</span>', html)
    # 作者行（含「/ 出版社 / 年份」）
    authors = re.findall(r'<p[^>]*class="[^"]*author[^"]*"[^>]*>([^<]+)</p>', html)
    if not authors:
        authors = re.findall(r'/([^/<]+)/', html)  # 宽松兜底

    out = []
    for i, t in enumerate(titles[:20]):
        out.append({
            "rank": i + 1,
            "title": t["title"],
            "author": (authors[i].strip() if i < len(authors) else ""),
            "cat": (cats[i].strip() if i < len(cats) else "其他"),
            "score": (scores[i] if i < len(scores) else ""),
            "url": t["url"],
        })
    return out if len(out) >= 8 else None


def fetch_dangdang():
    """当当畅销总榜：bang.dangdang.com 静态区块，正则解析（结构变化则返回 None 走兜底）。"""
    try:
        import requests
        r = requests.get("http://bang.dangdang.com/books/bestsellers/01.00.00.00.00.00",
                         headers=HEADERS, timeout=15)
        if r.status_code != 200 or len(r.text) < 5000:
            return None
        html = r.text
    except Exception:
        return None
    items = re.findall(
        r'<div class="name"><a href="[^"]*"[^>]*>([^<]+)</a>', html)
    authors = re.findall(
        r'<div class="publisher_info">\s*(?:<a[^>]*>([^<]+)</a>)?', html)
    titles, seen = [], set()
    for t in items:
        t = t.strip()
        if t and t not in seen and len(t) <= 40:
            seen.add(t)
            titles.append(t)
    if len(titles) < 8:
        return None
    out = []
    for i, t in enumerate(titles[:20]):
        out.append({"rank": i + 1, "title": t,
                    "author": (authors[i].strip() if i < len(authors) else ""),
                    "cat": "当当畅销榜", "score": "", "url": ""})
    return out


def fetch_weread():
    """微信读书：公开排行页尝试（多数榜单需登录态；失败返回 None 走兜底）。"""
    try:
        import requests
        r = requests.get("https://weread.qq.com/web/bookList", headers=HEADERS, timeout=15)
        if r.status_code != 200 or len(r.text) < 3000:
            return None
        html = r.text
        items = re.findall(r'"title":"([^"]{1,40})"', html)
        titles, seen = [], set()
        for t in items:
            t = t.strip()
            if t and t not in seen and not re.search(r'[\x00-\x1f]', t):
                seen.add(t)
                titles.append(t)
        if len(titles) < 8:
            return None
        return [{"rank": i + 1, "title": t, "author": "", "cat": "微信读书",
                 "score": "", "url": ""} for i, t in enumerate(titles[:20])]
    except Exception:
        return None


def fetch_jd():
    """京东图书榜：动态渲染 + 反爬，需带登录 cookie 才能拿到完整榜单。
    这里仅留扩展点，默认不可用，靠种子兜底。"""
    return None  # TODO: 接入京东图书排行榜 JSON 接口（需 cookie / 签名）


SOURCES = {
    "douban": fetch_douban_chart,
    "jd": fetch_jd,
    "dangdang": fetch_dangdang,
    "weread": fetch_weread,
}

# 多源融合权重（可按平台权威性调整）
SOURCE_WEIGHTS = {"douban": 1.0, "dangdang": 0.9, "weread": 0.8, "jd": 0.9}
SOURCE_NAMES = {"douban": "豆瓣", "dangdang": "当当", "weread": "微信读书", "jd": "京东"}


def _norm(t):
    t = str(t).lower()
    return re.sub(r"[^\w\u4e00-\u9fff]", "", t)


def merge_sources(results):
    """多源加权融合：score = Σ 权重×(21-名次) + 多源同时上榜加成 5×(源数-1)。"""
    agg = {}
    for src, books in results.items():
        w = SOURCE_WEIGHTS.get(src, 0.8)
        for b in books:
            k = _norm(b["title"])
            if not k:
                continue
            e = agg.setdefault(k, {"title": b["title"], "author": b.get("author", ""),
                                   "cat": b.get("cat", "其他"), "sources": {}, "score": 0.0})
            if src not in e["sources"]:
                e["sources"][src] = b["rank"]
            e["score"] += w * (21 - b["rank"])
            if b.get("author") and not e["author"]:
                e["author"] = b["author"]
    for e in agg.values():
        e["score"] += 5 * (len(e["sources"]) - 1)
        if len(e["sources"]) > 1:
            e["cat"] = "多源热销"
    out = sorted(agg.values(), key=lambda x: -x["score"])[:20]
    for i, e in enumerate(out, 1):
        e["rank"] = i
        e["_src_str"] = " · ".join(f"{SOURCE_NAMES.get(s, s)}#{r}" for s, r in e["sources"].items())
    return out


# ---------------------------------------------------------------------------
# 种子兜底
# ---------------------------------------------------------------------------
def load_seed():
    # 取 seeds 目录里最新的一个种子文件
    files = sorted([f for f in os.listdir(SEEDS_DIR) if f.endswith(".json")])
    if not files:
        return None
    path = os.path.join(SEEDS_DIR, files[-1])
    try:
        data = json.load(open(path, encoding="utf-8"))
        books = data.get("books", [])
        for i, b in enumerate(books):
            b.setdefault("rank", i + 1)
        return books
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 输出：榜单快照 JSON + 标准周报 Markdown
# ---------------------------------------------------------------------------
def one_line(b):
    parts = []
    if b.get("score"):
        parts.append(f"评分{b['score']}")
    if b.get("cat"):
        parts.append(b["cat"])
    if b.get("_src_str"):
        parts.append(f"在榜 {b['_src_str']}")
    return " · ".join(parts)


def build_weekly_md(books, date_str, source_label):
    lines = []
    lines.append(f"# 全网畅销书周报 - {date_str}")
    lines.append("")
    lines.append("> 本榜由 fetch_bestsellers.py 自动抓取生成（数据源：%s），连人工周报都省掉。" % source_label)
    lines.append("")
    lines.append("## 综合热度 TOP20")
    lines.append("")
    lines.append("| 排名 | 书名 | 作者 | 类别 | 一句话 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for b in books:
        title = b["title"].replace("|", "／")
        author = (b.get("author") or "").replace("|", "／")
        cat = (b.get("cat") or "其他").replace("|", "／")
        lines.append(f"| {b['rank']} | {title} | {author} | {cat} | {one_line(b)} |")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", action="store_true", help="强制使用种子榜单")
    ap.add_argument("--source", default="douban", choices=list(SOURCES.keys()))
    ap.add_argument("--multi", action="store_true",
                    help="多源融合：抓取全部可用榜单加权合并（豆瓣/当当/微信读书）")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--out", default=BASE)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    stamp = datetime.date.today().strftime("%Y-%m-%d")

    books = None
    source_label = ""
    if not args.seed and args.multi:
        results = {}
        for src, fn in SOURCES.items():
            try:
                r = fn()
            except Exception:
                r = None
            if r:
                results[src] = r
                print(f"  ✅ {src}: 抓得 {len(r)} 本")
            else:
                print(f"  ➖ {src}: 不可用（反爬/限流/需登录），跳过")
        if results:
            books = merge_sources(results)
            source_label = "multi-live（多源加权融合：" + "、".join(
                f"{SOURCE_NAMES.get(s, s)}×{SOURCE_WEIGHTS.get(s, 0.8)}" for s in results) + "）"
    if not books and not args.seed:
        try:
            books = SOURCES[args.source]()
        except Exception:
            books = None
        if books:
            source_label = f"{args.source}-live（实时抓取）"
    if not books:
        books = load_seed()
        source_label = "seed（内置真实快照·离线兜底）"
    if not books:
        print("❌ 无可用数据源，且种子缺失。请检查 seeds/ 目录。")
        sys.exit(3)

    books = books[: args.top]

    # 写榜单快照
    snap = {"source": source_label, "fetched_at": stamp, "books": books}
    snap_path = os.path.join(args.out, f"榜单快照-{date_str}.json")
    json.dump(snap, open(snap_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 写标准周报
    md = build_weekly_md(books, date_str, source_label)
    md_path = os.path.join(args.out, f"全网畅销书周报-{date_str}.md")
    open(md_path, "w", encoding="utf-8").write(md)

    print(f"✅ 数据源：{source_label}")
    print(f"✅ 抓得 {len(books)} 本，已写入：")
    print(f"   - {snap_path}")
    print(f"   - {md_path}")
    print("   下一步：python parse_weekly.py \"%s\" lite_auto.json" % md_path)


if __name__ == "__main__":
    main()
