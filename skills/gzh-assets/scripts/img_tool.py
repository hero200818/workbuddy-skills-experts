# -*- coding: utf-8 -*-
"""img_tool.py — 公众号配图处理：去 AI 水印 + 分类压缩 + 双档体积核查

独立可用，只依赖 Pillow，不读任何项目配置文件。

用法：
    # 处理源图（裁底去水印 + 压到双档以内）
    python img_tool.py process --dir 配图/raw/选题28 --out 配图 --trim 96

    # 上传前核查成品
    python img_tool.py check --dir 配图

为什么需要它（三个坑，不做就会被坑）：
  1. 生图模型的 AI 水印位置**不固定**，不是每次都 50-65px。裁少了留着水印，
     裁多了切主体。--trim 必须按图实测，且裁完**必须打开看**。
  2. 公众号对封面和正文图有**两套体积上限**（封面 2MB / 正文 1MB），
     按一套压，另一套必然超。言序超限报 ret:10001，不是你图有问题。
  3. --dir 指向父目录会**全量重刷**，把已发布文章的成品图一起覆盖。
     一个选题一个子目录，跑之前先 ls 确认。

退出码：0 全部合规 / 1 有超限或缺图 / 2 环境缺 Pillow
"""
import argparse
import os
import re
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

EXTS = (".png", ".jpg", ".jpeg", ".webp")
COVER_PATTERN = r"cover|封面"
QUALITY_LADDER = (80, 72, 65, 58, 50, 42)


def is_cover(name):
    return bool(re.search(COVER_PATTERN, name, re.I))


def scan(dirpath, check=False, suffix="_clean"):
    """列出图片。

    check=True（核查成品）：优先只看成品后缀；一个成品都没有时退回全部图片，
        否则 --check 会把刚压好的 _clean.jpg 全跳过，永远报"没有图片"。
    check=False（处理源图）：跳过成品后缀与 *_final.jpg，避免把成品再压一遍。
    """
    allimg, products = [], []
    for f in sorted(os.listdir(dirpath)):
        p = os.path.join(dirpath, f)
        if not (os.path.isfile(p) and f.lower().endswith(EXTS)):
            continue
        low = f.lower()
        if low.endswith("_final.jpg"):
            continue
        allimg.append(f)
        if low.endswith(suffix + ".jpg"):
            products.append(f)
    if check:
        return products or allimg
    return [f for f in allimg if f not in products]


def check_dir(src_dir, cover_kb=2000, body_kb=1000, suffix="_clean"):
    files = scan(src_dir, check=True, suffix=suffix)
    if not files:
        print(f"{src_dir} 下没有成品图")
        return 1
    print(f"核查 {len(files)} 张   （双档：封面 ≤{cover_kb}KB / 正文 ≤{body_kb}KB）")
    print("-" * 74)
    bad = 0
    for f in files:
        kb = os.path.getsize(os.path.join(src_dir, f)) / 1024
        limit = cover_kb if is_cover(f) else body_kb
        tag = "封面" if is_cover(f) else "正文"
        ok = kb <= limit
        if not ok:
            bad += 1
        print(f"{'✓' if ok else '✗ 超限'}  [{tag}] {f:<40} {kb:>7.0f} / {limit}KB")
    print("-" * 74)
    if bad:
        print(f"✗ {bad} 张超限——言序会报 ret:10001，必须先压到上限内")
        return 1
    print(f"✓ 全部 {len(files)} 张符合双档限制，可直接上传")
    return 0


def process_dir(src_dir, out_dir, trim=72, quality=85, suffix="_clean",
                cover_kb=2000, body_kb=1000):
    if Image is None:
        print("需要 Pillow：python -m pip install Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple")
        return 2
    if not os.path.isdir(src_dir):
        print(f"✗ 目录不存在：{src_dir}")
        return 1
    os.makedirs(out_dir, exist_ok=True)

    files = scan(src_dir, check=False, suffix=suffix)
    if not files:
        print(f"{src_dir} 下没有待处理图片（成品后缀 {suffix}.jpg 与 _final.jpg 已跳过）")
        return 0

    print(f"处理 {len(files)} 张   "
          f"（双档：封面 ≤{cover_kb}KB / 正文 ≤{body_kb}KB"
          + (f"，裁底 {trim}px" if trim else "") + "）")
    print("-" * 74)
    rows = []
    for f in files:
        p = os.path.join(src_dir, f)
        limit = cover_kb if is_cover(f) else body_kb
        tag = "封面" if is_cover(f) else "正文"
        im = Image.open(p).convert("RGB")
        w, h = im.size
        if trim:
            if trim >= h:
                print(f"✗ {f} 高度只有 {h}px，裁不掉 {trim}px")
                return 1
            im = im.crop((0, 0, w, h - trim))
        dst = os.path.join(out_dir, os.path.splitext(f)[0] + suffix + ".jpg")
        kb = 0
        for q in (quality,) + QUALITY_LADDER:
            im.save(dst, "JPEG", quality=q, optimize=True, progressive=True)
            kb = os.path.getsize(dst) / 1024
            if kb <= limit:
                break
        rows.append((f, tag, limit, kb, kb <= limit,
                     f"{w}x{h}→{im.size[0]}x{im.size[1]}"))

    for f, tag, limit, kb, ok, dim in rows:
        print(f"{'✓' if ok else '✗ 超限'}  [{tag}] {f:<40} {kb:>7.0f} / {limit}KB"
              + (f"  {dim}" if dim else ""))
    bad = [r for r in rows if not r[4]]
    print("-" * 74)
    if bad:
        print(f"✗ {len(bad)} 张超限——言序会报 ret:10001，必须先压到上限内")
        return 1
    print(f"✓ 全部 {len(rows)} 张符合双档限制，可直接上传")
    print("⚠ 裁完务必打开图看一遍：水印位置不固定，按固定值盲裁必翻车")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="公众号配图去水印 / 压缩 / 双档核查")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("process", help="处理源图：裁底 + 压到双档以内")
    p.add_argument("--dir", required=True, help="源图目录（一个选题一个子目录）")
    p.add_argument("--out", default=None, help="输出目录，默认同 --dir")
    p.add_argument("--trim", type=int, default=72, help="从底部裁掉多少像素（默认 72，按图实测）")
    p.add_argument("--quality", type=int, default=85, help="起始 JPEG 质量（默认 85，超限自动降）")
    p.add_argument("--suffix", default="_clean", help="成品后缀（默认 _clean）")
    p.add_argument("--cover-kb", type=int, default=2000, help="封面体积上限 KB")
    p.add_argument("--body-kb", type=int, default=1000, help="正文图体积上限 KB")

    c = sub.add_parser("check", help="核查已有成品的双档体积")
    c.add_argument("--dir", required=True, help="成品目录")
    c.add_argument("--suffix", default="_clean", help="成品后缀（默认 _clean）")
    c.add_argument("--cover-kb", type=int, default=2000, help="封面体积上限 KB")
    c.add_argument("--body-kb", type=int, default=1000, help="正文图体积上限 KB")

    a = ap.parse_args(argv)
    if a.cmd == "check":
        return check_dir(a.dir, a.cover_kb, a.body_kb, a.suffix)
    return process_dir(a.dir, a.out or a.dir, a.trim, a.quality, a.suffix,
                       a.cover_kb, a.body_kb)


if __name__ == "__main__":
    sys.exit(main())
