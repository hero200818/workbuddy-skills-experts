#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爆文引擎 BurstArticle Engine v1.0.0 - 固化清洗/目录/打包脚本
规则固化，不可修改：
  1. 删除 "## 备选标题" 小节
  2. 删除 "## 发布辅助信息" 小节
  3. 主标题精简至 <= 20 字
  4. 生成 00_总目录索引.md
  5. 打包 ZIP
"""
import argparse
import json
import os
import re
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

TITLE_MAX = 20
DROP_SECTIONS = ("备选标题", "发布辅助信息")
ILLEGAL = re.compile(r'[\\/:*?"<>|\r\n\t]')


def sanitize_filename(name: str) -> str:
    return ILLEGAL.sub("", name).strip(" .，。！？、；：")


def trim_title(title: str) -> str:
    title = title.strip()
    if len(title) <= TITLE_MAX:
        return title
    cut = title[:TITLE_MAX]
    return cut.rstrip(" ，。！？、；：—…·,.!?-")


def split_sections(text: str):
    """按行切分：返回 (标题行 or None, [(小节标题, 小节行列表), ...], 尾部杂项行)"""
    lines = text.splitlines()
    h1 = None
    body = lines
    for i, ln in enumerate(lines):
        if ln.startswith("# ") and not ln.startswith("## "):
            h1 = ln[2:].strip()
            body = lines[:i] + lines[i + 1:]
            break
    sections = []  # (header, [lines])
    current = None
    tail = []
    for ln in body:
        if ln.startswith("## "):
            if current:
                sections.append(current)
            current = (ln[3:].strip(), [])
        else:
            if current:
                current[1].append(ln)
            else:
                tail.append(ln)
    if current:
        sections.append(current)
    return h1, sections, tail


def clean_markdown(text: str):
    """返回 (清洗后文本, 精简后标题)"""
    h1, sections, tail = split_sections(text)
    kept = []
    for header, lines in sections:
        if header in DROP_SECTIONS or any(k in header for k in DROP_SECTIONS):
            continue
        kept.append("## " + header)
        kept.extend(lines)
    out_title = trim_title(h1) if h1 else ""
    parts = []
    if out_title:
        parts.append("# " + out_title)
    lead = [ln for ln in tail]
    while lead and not lead[0].strip():
        lead.pop(0)
    if lead:
        parts.append("")
        parts.extend(lead)
    if kept:
        parts.append("")
        parts.extend(kept)
    return "\n".join(parts).rstrip() + "\n", out_title


def scan_raw(raw_dir: str):
    """扫描原始稿，返回排序后的 [(编号int, 路径)]"""
    items = []
    if not os.path.isdir(raw_dir):
        return items
    for fn in os.listdir(raw_dir):
        m = re.match(r"^(\d+)_.*\.md$", fn)
        if m:
            items.append((int(m.group(1)), os.path.join(raw_dir, fn)))
    items.sort()
    return items


def run_status(workdir: str):
    raw_dir = os.path.join(workdir, "raw")
    raws = scan_raw(raw_dir)
    cleaned = [f for f in os.listdir(workdir)
               if re.match(r"^\d+_.+\.md$", f) and f != "00_总目录索引.md"]
    next_index = (raws[-1][0] + 1) if raws else 1
    print(json.dumps({
        "workdir": os.path.abspath(workdir),
        "raw": len(raws),
        "cleaned": len(cleaned),
        "next_index": next_index,
    }, ensure_ascii=False))


def run_clean(workdir: str, no_clean: bool = False):
    raw_dir = os.path.join(workdir, "raw")
    raws = scan_raw(raw_dir)
    if not raws:
        print(json.dumps({"error": "raw 目录为空或不存在", "raw_dir": os.path.abspath(raw_dir)},
                         ensure_ascii=False))
        sys.exit(1)

    entries = []  # (编号, 成品文件名, 标题)
    for idx, path in raws:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        if no_clean:
            h1 = None
            for ln in text.splitlines():
                if ln.startswith("# ") and not ln.startswith("## "):
                    h1 = ln[2:].strip()
                    break
            title = trim_title(h1 or os.path.splitext(os.path.basename(path))[0])
            content = text
        else:
            content, title = clean_markdown(text)
        fname = "%03d_%s.md" % (idx, sanitize_filename(title) or ("第%d篇" % idx))
        out_path = os.path.join(workdir, fname)
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        entries.append((idx, fname, title))

    # 总目录
    index_lines = ["# 《%s》爆文引擎 · 总目录索引" % (os.path.basename(workdir).replace("爆文引擎_", "", 1) or "爆文引擎"),
                   "",
                   "- 共 %d 篇 · 爆文引擎 BurstArticle Engine v1.0.0" % len(entries),
                   ""]
    for idx, fname, title in entries:
        index_lines.append("%d. [%s](%s)" % (idx, title, fname))
    with open(os.path.join(workdir, "00_总目录索引.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(index_lines) + "\n")

    # ZIP
    zip_path = os.path.abspath(workdir) + ".zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, fname, title in entries:
            zf.write(os.path.join(workdir, fname), os.path.basename(workdir) + "/" + fname)
        zf.write(os.path.join(workdir, "00_总目录索引.md"),
                 os.path.basename(workdir) + "/00_总目录索引.md")

    print(json.dumps({
        "total": len(entries),
        "index": os.path.abspath(os.path.join(workdir, "00_总目录索引.md")),
        "zip": zip_path,
        "first": entries[0][2] if entries else None,
        "last": entries[-1][2] if entries else None,
    }, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description="爆文引擎清洗/目录/打包脚本")
    ap.add_argument("--workdir", required=True, help="工作目录，如 爆文引擎_明朝那些事儿")
    ap.add_argument("--status", action="store_true", help="仅查看进度（JSON）")
    ap.add_argument("--no-clean", action="store_true", help="关闭清洗，保留原始稿")
    args = ap.parse_args()
    if args.status:
        run_status(args.workdir)
    else:
        run_clean(args.workdir, no_clean=args.no_clean)


if __name__ == "__main__":
    main()
