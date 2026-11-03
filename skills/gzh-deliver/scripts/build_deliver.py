# -*- coding: utf-8 -*-
"""交付物构建：从主稿 md 生成纯文本版 / 公众号终稿 HTML / 内联 HTML。

纯本地、零依赖、与具体项目无关——任何写公众号长文的人都用得上。

用法：
    python build_deliver.py 文章.md                    # 输出到 md 同目录，前缀取文件名首段
    python build_deliver.py 文章.md --prefix 选题28
    python build_deliver.py 文章.md --out-dir out --cover-count 1

产物（都在 --out-dir 下，默认与输入 md 同目录）：
    <prefix>_纯文本版.txt      去 md 语法，图片转「【配图：xxx.jpg】」占位
    <prefix>_公众号终稿版.html  带使用说明注释，样式全内联
    <prefix>_内联HTML版.html    不带注释，可直接粘进编辑器

样式来源：公众号素排版（全内联），适配后台「源码」模式复制粘贴。
"""
import argparse
import io
import os
import re
import sys

FONT = ("-apple-system,BlinkMacSystemFont,'Helvetica Neue','PingFang SC',"
        "'Microsoft YaHei',sans-serif")


def read_md(path):
    return io.open(path, encoding="utf-8").read().strip().split("\n")


def to_plain(lines):
    """纯文本版：去图片标记、去 md 语法，保留段落。"""
    out = []
    for ln in lines:
        s = ln.strip()
        if not s:
            out.append("")
            continue
        m = re.match(r"^!\[[^\]]*\]\(([^)]+)\)$", s)
        if m:
            out.append(f"【配图：{os.path.basename(m.group(1))}】")
            continue
        s = re.sub(r"^#{1,3}\s*", "", s)
        s = s.replace("**", "")
        out.append(s)
    txt = "\n".join(out)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip() + "\n"


def to_html(lines, with_note=True, cover_count=1, title=""):
    body = []
    img_i = 0
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", s)
        if m:
            alt, src = m.group(1), m.group(2)
            alt_short = alt.split("（")[0].split("(")[0]
            if img_i < cover_count:
                img_i += 1
                body.append(
                    '<!-- 封面首图：替换为素材库URL -->\n'
                    '<section style="padding:0 0 22px;">\n'
                    f'<img src="{src}" alt="{alt_short}" '
                    'style="width:100%;max-width:680px;height:auto;'
                    'border-radius:8px;display:block;">\n</section>')
            else:
                body.append(
                    f'<!-- 文中配图：{alt_short}，替换为素材库URL -->\n'
                    '<section style="text-align:center;padding:6px 0 22px;">\n'
                    f'<img src="{src}" alt="{alt_short}" '
                    'style="width:100%;max-width:480px;height:auto;'
                    'border-radius:8px;display:inline-block;">\n</section>')
            continue
        if s.startswith("# "):
            t = s[2:].strip()
            body.append(
                f'<h1 style="font-size:22px;font-weight:700;color:#1f1f1f;'
                f'line-height:1.45;text-align:center;padding:0 0 24px;">{t}</h1>')
            continue
        if s.startswith("## "):
            t = s[3:].strip()
            body.append(
                f'<h2 style="font-size:19px;font-weight:700;color:#1f1f1f;'
                f'line-height:1.5;padding:26px 0 14px;">{t}</h2>')
            continue
        t = re.sub(r"\*\*(.+?)\*\*",
                   r'<strong style="font-weight:700;color:#1f1f1f;">\1</strong>', s)
        if t.startswith("—— "):
            body.append(
                f'<p style="padding:26px 0 0;text-align:right;color:#6b6b6b;'
                f'font-size:15px;">{t}</p>')
            continue
        body.append(f'<p style="padding:0 0 18px;">{t}</p>')

    n_img = sum(1 for ln in lines if re.match(r"^!\[", ln.strip()))
    note = f"""<!-- ========== 公众号终稿版 · 使用说明 ==========
1. 本文件样式全部内联，专为公众号后台「源码」模式 / 浏览器复制粘贴设计，排版不会变形。
2. 发布前请先把 {n_img} 张图上传到公众号「素材库」，拿到图片 URL，替换下面每个 <img> 的 src。
   （src 现为本地相对路径「配图/xxx.jpg」，仅用于本地浏览器预览，公众号不认本地路径。）
3. 封面不压字：标题 {len(title) if title else '?'} 字，留白作构图用。
4. 文件末尾无「投放辅助」区块，可直接发布。
================================================= -->

""" if with_note else ""
    return note + (
        f'<section style="font-family:{FONT};font-size:17px;line-height:1.85;'
        'color:#2f2f2f;padding:6px 4px;">\n\n' + "\n\n".join(body) + "\n\n</section>\n")


def _b64_img(src, md_dir):
    """把本地图片转成 base64 data URI；找不到则返回原 src（当作外链）。"""
    for cand in (os.path.join(md_dir, src), src):
        if os.path.exists(cand):
            import base64
            ext = os.path.splitext(cand)[1].lower().lstrip(".")
            mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png",
                    "gif": "gif", "webp": "webp"}.get(ext, "jpeg")
            with open(cand, "rb") as f:
                data = base64.b64encode(f.read()).decode("ascii")
            return f"data:image/{mime};base64,{data}"
    return src


def to_preview(lines, md_dir, cover_count=1, title=""):
    """自包含预览版：图片 base64 内联，单文件双击即可在浏览器看效果。"""
    body = []
    img_i = 0
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", s)
        if m:
            alt, src = m.group(1), m.group(2)
            alt_short = alt.split("（")[0].split("(")[0]
            uri = _b64_img(src, md_dir)
            if img_i < cover_count:
                img_i += 1
                body.append(
                    f'<img src="{uri}" alt="{alt_short}" '
                    'style="width:100%;max-width:680px;height:auto;'
                    'border-radius:8px;display:block;margin:0 auto 22px;">')
            else:
                body.append(
                    f'<img src="{uri}" alt="{alt_short}" '
                    'style="width:100%;max-width:480px;height:auto;'
                    'border-radius:8px;display:inline-block;margin:6px auto 22px;">')
            continue
        if s.startswith("# "):
            t = s[2:].strip()
            body.append(
                f'<h1 style="font-size:22px;font-weight:700;color:#1f1f1f;'
                f'line-height:1.45;text-align:center;padding:0 0 24px;">{t}</h1>')
            continue
        if s.startswith("## "):
            t = s[3:].strip()
            body.append(
                f'<h2 style="font-size:19px;font-weight:700;color:#1f1f1f;'
                f'line-height:1.5;padding:26px 0 14px;">{t}</h2>')
            continue
        t = re.sub(r"\*\*(.+?)\*\*",
                   r'<strong style="font-weight:700;color:#1f1f1f;">\1</strong>', s)
        if t.startswith("—— "):
            body.append(
                f'<p style="padding:26px 0 0;text-align:right;color:#6b6b6b;'
                f'font-size:15px;">{t}</p>')
            continue
        body.append(f'<p style="padding:0 0 18px;">{t}</p>')
    return ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title or "预览"}</title></head><body style="margin:0;'
            'background:#f2f2f2;"><div style="max-width:680px;margin:0 auto;'
            f'background:#fff;padding:28px 22px;min-height:100vh;'
            f'font-family:{FONT};font-size:17px;line-height:1.85;'
            f'color:#2f2f2f;">' + "\n\n".join(body) +
            "\n\n</div></body></html>\n")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="从主稿 md 生成纯文本版 / 公众号终稿 HTML / 内联 HTML")
    ap.add_argument("md", help="主稿 markdown 路径（绝对或相对）")
    ap.add_argument("--prefix", help="输出文件前缀（默认取 md 文件名首段）")
    ap.add_argument("--out-dir", help="输出目录（默认与 md 同目录）")
    ap.add_argument("--cover-count", type=int, default=1,
                    help="视作封面的首图数量（默认 1）")
    ap.add_argument("--preview", action="store_true",
                    help="额外生成自包含预览版 HTML（图片 base64 内联，无需起服务即可打开）")
    a = ap.parse_args(argv)

    md = os.path.abspath(a.md)
    if not os.path.exists(md):
        print(f"✗ 找不到 {md}")
        return 1
    out_dir = os.path.abspath(a.out_dir) if a.out_dir else os.path.dirname(md)
    os.makedirs(out_dir, exist_ok=True)
    md_dir = os.path.dirname(md)

    slug = a.prefix or os.path.basename(md).split("_")[0].rsplit(".", 1)[0]
    lines = read_md(md)
    title = next((ln.strip()[2:] for ln in lines if ln.strip().startswith("# ")), "")

    plain = to_plain(lines)
    io.open(os.path.join(out_dir, f"{slug}_纯文本版.txt"), "w",
            encoding="utf-8", newline="\n").write(plain)
    print(f"纯文本版  {len(plain)} 字符 → {slug}_纯文本版.txt")

    html = to_html(lines, with_note=True, cover_count=a.cover_count, title=title)
    io.open(os.path.join(out_dir, f"{slug}_公众号终稿版.html"), "w",
            encoding="utf-8", newline="\n").write(html)
    print(f"终稿HTML  {len(html)} 字符 → {slug}_公众号终稿版.html")

    html2 = to_html(lines, with_note=False, cover_count=a.cover_count, title=title)
    io.open(os.path.join(out_dir, f"{slug}_内联HTML版.html"), "w",
            encoding="utf-8", newline="\n").write(html2)
    print(f"内联HTML  {len(html2)} 字符 → {slug}_内联HTML版.html")

    if a.preview:
        pv = to_preview(lines, md_dir, cover_count=a.cover_count, title=title)
        io.open(os.path.join(out_dir, f"{slug}_预览版.html"), "w",
                encoding="utf-8", newline="\n").write(pv)
        kb = len(pv.encode("utf-8")) // 1024
        print(f"预览版    {kb}KB → {slug}_预览版.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
