#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
review_page.py —— 成品审阅页（墨韵拆书卡 v1.6.0）

把某期成品打包成一个 HTML 审阅页：九宫格画廊（点击放大）+ 三平台文案切换
（marked 渲染）+ 每平台一键复制 + 标题工坊/质检结论摘要。
审阅从"翻文件夹"变成"开一个网页"。

用法：
  python review_page.py <期目录>
输出：期目录/review.html（图片用相对路径，本地直接打开即用）
"""
import os, sys, json, re, html

BASE = os.path.dirname(os.path.abspath(__file__))

TPL = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__ISSUE__ · 审阅页</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
<style>
 body{font-family:system-ui,"Microsoft YaHei",sans-serif;margin:0;background:#f6f4ee;color:#2c2c2a}
 header{padding:18px 28px;border-bottom:1px solid #0002;background:#fff}
 header h1{margin:0;font-size:20px}
 header .meta{color:#888780;font-size:13px;margin-top:4px}
 .qc{display:inline-block;margin-left:12px;padding:2px 10px;border-radius:12px;font-size:12px;background:#FAEEDA;border:1px solid #BA7517;color:#633806}
 .wrap{display:flex;flex-wrap:wrap;gap:24px;padding:24px 28px;align-items:flex-start}
 .gallery{flex:0 0 340px;display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
 .gallery img{width:100%;border-radius:8px;cursor:zoom-in;border:1px solid #0001;transition:.15s}
 .gallery img:hover{transform:scale(1.03)}
 .copy{flex:1;min-width:380px;background:#fff;border:1px solid #0002;border-radius:12px;overflow:hidden}
 .tabs{display:flex;border-bottom:1px solid #0001}
 .tabs button{flex:1;border:0;background:none;padding:12px;font-size:14px;cursor:pointer;color:#5F5E5A}
 .tabs button.on{color:#993C1D;font-weight:600;border-bottom:2px solid #993C1D;background:#fff}
 .body{padding:16px 20px;max-height:70vh;overflow:auto;font-size:14px;line-height:1.7}
 .bar{padding:10px 20px;border-top:1px solid #0001;display:flex;gap:10px;justify-content:flex-end}
 .bar button{border:1px solid #993C1D;background:#993C1D;color:#fff;border-radius:8px;padding:8px 18px;cursor:pointer;font-size:13px}
 .bar button.ghost{background:#fff;color:#993C1D}
 #lb{position:fixed;inset:0;background:#000c;display:none;align-items:center;justify-content:center;cursor:zoom-out}
 #lb img{max-width:92vw;max-height:94vh;border-radius:10px}
 .toast{position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:#2c2c2a;color:#fff;padding:9px 22px;border-radius:20px;font-size:13px;opacity:0;transition:.25s;pointer-events:none}
</style></head><body>
<header><h1>__ISSUE__ <span class="qc">__QC__</span></h1>
<div class="meta">__DATE__ · __N__ 本书 · __IMGS__ 张图 · 墨韵拆书卡 v1.6.0 审阅页</div></header>
<div class="wrap">
  <div class="gallery" id="gal"></div>
  <div class="copy">
    <div class="tabs" id="tabs"></div>
    <div class="body" id="body"></div>
    <div class="bar">
      <button class="ghost" onclick="copySel(0)">复制选中平台全文</button>
      <button onclick="copyRaw()">复制 Markdown 原文</button>
    </div>
  </div>
</div>
<div id="lb" onclick="this.style.display='none'"><img id="lbimg"></div>
<div class="toast" id="toast">已复制到剪贴板</div>
<script>
const IMGS = __IMGJSON__;
const DOCS = __DOCJSON__;
let sel = 0, raw = false;
const gal = document.getElementById("gal");
IMGS.forEach(f => { const im = new Image(); im.src = f; im.title = f;
  im.onclick = () => { document.getElementById("lbimg").src = f;
    document.getElementById("lb").style.display = "flex"; };
  gal.appendChild(im); });
const tabs = document.getElementById("tabs");
DOCS.forEach((d, i) => { const b = document.createElement("button");
  b.textContent = d.name; b.className = i ? "" : "on";
  b.onclick = () => { sel = i; [...tabs.children].forEach((x, j) =>
      x.className = j === i ? "on" : ""); render(); };
  tabs.appendChild(b); });
function render(){ const d = DOCS[sel]; const el = document.getElementById("body");
  if (raw) { el.innerHTML = "<pre style='white-space:pre-wrap'></pre>";
    el.querySelector("pre").textContent = d.text; }
  else { el.innerHTML = marked.parse(d.text); } }
function copySel(){ navigator.clipboard.writeText(DOCS[sel].text).then(toast); }
function copyRaw(){ raw = !raw; render(); toast(raw ? "已切换原文" : "已切换渲染"); }
function toast(m){ const t = document.getElementById("toast");
  t.textContent = m; t.style.opacity = 1; setTimeout(()=>t.style.opacity=0, 1500); }
render();
</script></body></html>"""


def md_text(path):
    if os.path.isfile(path):
        return open(path, encoding="utf-8").read()
    return ""


def qc_summary(d):
    p = os.path.join(d, "qc_report.md")
    if not os.path.isfile(p):
        return "未质检"
    head = open(p, encoding="utf-8").read().splitlines()
    for ln in head:
        if "结论" in ln:
            return re.sub(r"[*#]", "", ln).strip()[:60]
    return "已质检"


def main():
    d = sys.argv[1] if os.path.isdir(sys.argv[1]) else os.path.dirname(os.path.abspath(sys.argv[1]))
    data = json.load(open(os.path.join(d, "books.json"), encoding="utf-8"))
    imgs = sorted(f for f in os.listdir(d) if f.endswith(".jpg") and f[:2].isdigit())
    docs = [("微信视频号", os.path.join("分发包", str(data.get("issue", "")), "01_微信视频号图文.md")),
            ("头条微头条", os.path.join("分发包", str(data.get("issue", "")), "02_头条微头条.md")),
            ("小红书", os.path.join("分发包", str(data.get("issue", "")), "03_小红书笔记.md"))]
    pkg_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(d))), "2026-10-22-12-41-11")
    doc_list = []
    for name, rel in docs:
        p1 = os.path.join(pkg_root, rel)
        text = md_text(p1) or md_text(os.path.join(d, "发布文案.md"))
        doc_list.append({"name": name, "text": text})
    page = (TPL.replace("__ISSUE__", html.escape(str(data.get("issue", ""))))
               .replace("__DATE__", html.escape(str(data.get("date", ""))))
               .replace("__N__", str(len(data.get("books", []))))
               .replace("__IMGS__", str(len(imgs)))
               .replace("__QC__", html.escape(qc_summary(d)))
               .replace("__IMGJSON__", json.dumps(imgs, ensure_ascii=False))
               .replace("__DOCJSON__", json.dumps(doc_list, ensure_ascii=False)))
    out = os.path.join(d, "review.html")
    open(out, "w", encoding="utf-8").write(page)
    print(f"✅ 审阅页已生成：{out}（浏览器直接打开）")


if __name__ == "__main__":
    main()
