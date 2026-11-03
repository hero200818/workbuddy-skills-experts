# -*- coding: utf-8 -*-
"""enrich.py — 极简书单 → 完整拆书数据（自动填内容引擎）
用法：
  python enrich.py lite.json            # lite.json: [{"title":"书名","author":"作者","cat?":"分类"}, ...]
  python enrich.py lite.json out.json   # 指定输出

逻辑：
  1. 每本书先查 library/<书名>.json —— 命中则直接复用（作者/分类以 lite 传入的优先覆盖）。
  2. 未命中 → 收集到 missing，由 LLM（本会话的 AI）生成后写回 library，下次复用。
  3. 输出可直接喂给 gen_cards_ios.py 的 books 数组（含 rec/points×3/quote/who）。
返回码：0=全部复用；2=有缺失需补全。
"""
import os, sys, json, re

BASE = os.path.dirname(os.path.abspath(__file__))
LIB  = os.path.join(BASE, "library")
os.makedirs(LIB, exist_ok=True)

def safe(name):
    return re.sub(r'[\\/:*?"<>|]', "_", name)

def norm(s):
    """归一化：去标点/空格、转小写，用于短名↔长全名的软匹配。"""
    return re.sub(r'[：:，,、\s（）()”“"\'’]', '', s or "").lower()

def load_lib(title):
    # 1) 精确匹配（文件名）
    p = os.path.join(LIB, safe(title) + ".json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    # 2) 软匹配：遍历库，按归一化包含关系（兼容「短名」与「书名：副标题」全名）
    nt = norm(title)
    if not nt:
        return None
    for fn in os.listdir(LIB):
        if not fn.endswith(".json"):
            continue
        try:
            e = json.load(open(os.path.join(LIB, fn), encoding="utf-8"))
        except Exception:
            continue
        cand = e.get("title") or e.get("file") or fn[:-5]
        nc = norm(cand)
        if nc and min(len(nc), len(nt)) >= 2 and (nc == nt or nc.startswith(nt) or nt.startswith(nc)):
            return e
    return None

def save_lib(entry):
    p = os.path.join(LIB, safe(entry["title"]) + ".json")
    entry.setdefault("created_at", "2026-10-27")
    json.dump(entry, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def enrich(lite):
    out, missing = [], []
    for b in lite:
        t = b.get("title")
        e = load_lib(t)
        if e:
            merged = {**e}
            for k, v in b.items():
                if not v:
                    continue
                if k == "title" and e.get("title"):
                    continue  # 显示标题以库内短名为准（避免长全名溢出卡片），lite 的 title 仅用于查库匹配
                merged[k] = v              # 作者/分类等元数据以 lite 传入的优先纠正
            merged.pop("used_in", None)
            merged.pop("created_at", None)
            out.append(merged)
        else:
            missing.append({"title": t, "author": b.get("author", ""), "cat": b.get("cat", "")})
    return out, missing

if __name__ == "__main__":
    lite_path = sys.argv[1]
    out_path  = sys.argv[2] if len(sys.argv) > 2 else "books.full.json"
    lite = json.load(open(lite_path, encoding="utf-8"))
    full, missing = enrich(lite)
    if full:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(full, f, ensure_ascii=False, indent=2)
    if missing:
        print(f"✅ 已复用 {len(full)} 本；❌ 待补全 {len(missing)} 本（写入 {out_path}.missing.json）：")
        print(json.dumps(missing, ensure_ascii=False, indent=2))
        json.dump(missing, open(out_path + ".missing.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        sys.exit(2)
    else:
        print(f"🎉 全部 {len(full)} 本均从内容库复用，已写出 {out_path}")
        sys.exit(0)
