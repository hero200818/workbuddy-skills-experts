#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小红书 6 图笔记批量配图生成器（iOS 液态玻璃风）。

用法: python make_covers.py cover_spec.json

依赖: Pillow (pip install pillow)，中文字体（Windows: msyhbd.ttc/msyh.ttc；
      mac: PingFang.ttc；linux: 自动回退到文泉驿/思源黑体，可用 font_paths 覆盖）。

cover_spec.json 格式:
{
  "out_dir": "covers_out",
  "font_paths": ["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc"],
  "books": [
    {
      "dir": "01_书名",
      "pill": "《书名》",
      "palette": {"c1": [255,190,90], "c2": [230,120,40],
                   "fg": [90,45,10], "accent": [255,240,200],
                   "ona": [120,60,10], "tint": 46},
      "cover": ["主标题|第二行", "副标题"],
      "pages": [
        ["徽章文字", "标题行1|标题行2", "副行1|副行2|副行3"],
        ... 4 组 ...
      ],
      "end": ["互动卡标题|第二行", "副行1|副行2"]
    }, ...
  ]
}
约定: 文本中的 "|" 渲染为换行。每本书输出 6 张 jpg（1封面+4内容卡+1互动卡），
尺寸 1080x1440（3:4），可直接上传小红书图文笔记。
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1440

DEFAULT_FONTS_BOLD = [
    "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]
DEFAULT_FONTS_REG = [
    "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simsun.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]
_FONT_CACHE = {}


def _find(size, bold, paths):
    key = (size, bold, tuple(paths))
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    names = paths or (DEFAULT_FONTS_BOLD if bold else DEFAULT_FONTS_REG)
    for p in names:
        try:
            f = ImageFont.truetype(p, size)
            _FONT_CACHE[key] = f
            return f
        except Exception:
            continue
    raise RuntimeError(f"未找到可用中文字体: 尝试过 {names}；请在 spec 中提供 font_paths")


def font(size, bold=True, paths=None):
    return _find(size, bold, paths or [])


_dummy = ImageDraw.Draw(Image.new("RGB", (10, 10)))


def fit(text, maxw, start, bold=True, paths=None):
    s = start
    while s > 36:
        f = font(s, bold, paths)
        if _dummy.textlength(text, font=f) <= maxw:
            return f
        s -= 3
    return font(s, bold, paths)


def make(path, pal, badge, title, sub, pill, paths=None):
    img = Image.new("RGBA", (W, H))
    dr = ImageDraw.Draw(img)
    c1, c2 = pal["c1"], pal["c2"]
    for y in range(H):
        t = y / H
        col = (int(c1[0] + (c2[0] - c1[0]) * t),
               int(c1[1] + (c2[1] - c1[1]) * t),
               int(c1[2] + (c2[2] - c1[2]) * t), 255)
        dr.line([(0, y), (W, y)], fill=col)
    sweep = Image.new("RGBA", (W, H))
    sd = ImageDraw.Draw(sweep)
    for x in range(W):
        a = int(38 * (1 - x / W))
        sd.line([(x, 0), (x, H)], fill=(255, 255, 255, a))
    img = Image.alpha_composite(img, sweep)
    blobs = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(blobs)
    accent = pal["accent"]
    blob_cols = [(255, 255, 255), (255, 255, 255), tuple(accent), tuple(c2), tuple(c1)]
    pos = [(180, 260, 150), (930, 180, 110), (120, 1150, 130), (960, 1240, 170), (540, 720, 220)]
    for (cx, cy, r), col in zip(pos, blob_cols):
        bd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (70,))
    blobs = blobs.filter(ImageFilter.GaussianBlur(70))
    img = Image.alpha_composite(img, blobs)
    box = (80, 300, 1000, 1160)
    rad = 64
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [box[0] + 10, box[1] + 26, box[2] + 10, box[3] + 26], radius=rad, fill=(20, 20, 40, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(26))
    img = Image.alpha_composite(img, sh)
    region = img.crop(box).filter(ImageFilter.GaussianBlur(16))
    img.paste(region, box)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle(box, radius=rad, fill=(255, 255, 255, pal.get("tint", 46)))
    img = Image.alpha_composite(img, ov)
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(gl).rounded_rectangle(
        [box[0] + 8, box[1] + 8, box[2] - 8, box[1] + 150], radius=rad - 8, fill=(255, 255, 255, 34))
    img = Image.alpha_composite(img, gl)
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle(box, radius=rad, outline=(255, 255, 255, 200), width=3)
    fb = font(30, False, paths)
    bw = dr.textlength(badge, font=fb)
    bx = (W - bw) / 2
    dr.rounded_rectangle([bx - 30, 150, bx + bw + 30, 214], radius=32,
                         fill=(255, 255, 255, 90), outline=(255, 255, 255, 170), width=2)
    dr.text((bx, 166), badge, font=fb, fill=tuple(pal["fg"]) + (235,))
    tl = title.replace("|", "\n").split("\n")
    ft = fit(max(tl, key=len), 820, 96, True, paths)
    lh = int(ft.size * 1.42)
    sl = [s for s in sub.split("|") if s] if sub else []
    fs = font(38, False, paths)
    slh = 60
    total = len(tl) * lh + (40 + len(sl) * slh if sl else 0)
    y = 300 + (860 - total) // 2
    for ln in tl:
        w = dr.textlength(ln, font=ft)
        dr.text(((W - w) / 2 + 3, y + 3), ln, font=ft, fill=(30, 30, 50, 90))
        dr.text(((W - w) / 2, y), ln, font=ft, fill=tuple(pal["fg"]) + (255,))
        y += lh
    if sl:
        y += 40
        for ln in sl:
            w = dr.textlength(ln, font=fs)
            dr.text(((W - w) / 2, y), ln, font=fs, fill=tuple(pal["fg"]) + (200,))
            y += slh
    fp = font(36, True, paths)
    pw = dr.textlength(pill, font=fp)
    px = (W - pw) / 2
    dr.rounded_rectangle([px - 40, 1225, px + pw + 40, 1305], radius=40,
                         fill=tuple(pal["accent"]) + (235,), outline=(255, 255, 255, 160), width=2)
    dr.text((px, 1245), pill, font=fp, fill=tuple(pal["ona"]) + (255,))
    img.convert("RGB").save(path, quality=90)


def run(spec_path):
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    out_root = spec.get("out_dir", "covers_out")
    paths = spec.get("font_paths")
    n = 0
    for b in spec["books"]:
        d = os.path.join(out_root, b["dir"])
        os.makedirs(d, exist_ok=True)
        p = b["palette"]
        make(os.path.join(d, "1.jpg"), p, "每晚9点 · 一个好看的故事",
             b["cover"][0], b["cover"][1], b["pill"], paths)
        n += 1
        for i, (bdg, t, s) in enumerate(b["pages"], start=2):
            make(os.path.join(d, f"{i}.jpg"), p, bdg, t, s, b["pill"], paths)
            n += 1
        make(os.path.join(d, "6.jpg"), p, "评论区聊聊",
             b["end"][0], b["end"][1], b["pill"], paths)
        n += 1
    print(f"generated {n} images -> {out_root}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    run(sys.argv[1])
