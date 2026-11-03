---
name: gzh-deliver
display_name: 公众号交付物构建
display_name_en: WeChat Article Deliverables
description: "公众号长文的主稿 md 到发布交付物的一键转换。当用户要生成纯文本版、出 HTML、做公众号终稿、转内联 HTML、生成预览版、预览文章效果、把 md 转成能发的稿时使用。四个产物一次性产出：纯文本版（去 md 语法）、公众号终稿 HTML（全内联样式，源码模式粘贴不变形）、内联 HTML（无注释可直接粘编辑器）、自包含预览版（图片 base64 内联，双击即看效果）。纯本地、零配置、与具体账号无关，任何写公众号长文的人都用得上。触发词：交付物、纯文本版、终稿 HTML、内联 HTML、预览版、md 转 html、公众号排版、出稿。"
description_zh: 主稿 md 一键转纯文本/终稿HTML/内联HTML/自包含预览版，全内联样式，换个项目直接能用。
description_en: Convert a WeChat long-form markdown into plain text, inlined HTML, and a self-contained preview.
category: writing
version: 1.0.0
author: 读读书悦悦己
agent_created: true
---

# 公众号交付物构建

主稿 markdown → 四个发布交付物。一步，不依赖任何账号、配置或网络。

## 什么时候用

- 写完一篇公众号长文（md），要出一份能粘进公众号后台"源码"模式的 HTML
- 要一份纯文本版做存档或二次编辑
- 要在浏览器里先看排版效果（不依赖起服务）
- 要一份干净的内联 HTML 交给排版工具或协作者

## 四个产物

| 文件 | 用途 |
|---|---|
| `<slug>_纯文本版.txt` | 去 md 语法，图片转「【配图：xxx.jpg】」占位，便于二次编辑/存档 |
| `<slug>_公众号终稿版.html` | 带使用说明注释，**样式全内联**，专为后台"源码"模式复制粘贴设计 |
| `<slug>_内联HTML版.html` | 同上但不带注释，可直接粘进编辑器或交给下游工具 |
| `<slug>_预览版.html` | 图片 base64 内联的**自包含**单文件，双击在浏览器看效果 |

## 用法

```bash
# 基本：输出到 md 同目录，前缀取文件名首段
python scripts/build_deliver.py 文章.md

# 显式指定前缀与输出目录（换项目也用这套）
python scripts/build_deliver.py 文章.md --prefix 选题28 --out-dir out

# 额外生成自包含预览版（图片 base64 内联，约 1MB）
python scripts/build_deliver.py 文章.md --preview
```

参数：

| 参数 | 默认 | 说明 |
|---|---|---|
| `md` | 必填 | 主稿路径（绝对或相对，相对基于当前目录解析） |
| `--prefix` | 文件名首段 | 输出文件前缀 |
| `--out-dir` | 与 md 同目录 | 输出目录 |
| `--cover-count` | 1 | 视作"封面"的前 N 张图：满宽；其余居中、限宽 480px |
| `--preview` | 关 | 额外生成 base64 自包含预览版 |

## 两个要点

### 1. 封面图与文中图的处理不同

脚本把前 `--cover-count` 张图当封面：**满宽**展示；其余当文中配图：**居中、限宽 480px**。
封面图通常更宽更有冲击，文中图塞太宽会挤。如果你的文章首图不是真正的封面（比如第一段后那张也是满宽），把 `--cover-count` 调到对应数量。

### 2. 预览版不能粘公众号

预览版里的图片是 base64 内联的，**公众号后台会过滤 base64 图**。它只用来本地看效果。
真正发布时要用的是 `_公众号终稿版.html`，并且先把图上传到素材库、替换每个 `<img>` 的 `src` 为素材库 URL（脚本注释里写了第几步）。

## 验收

跑完核对三件：

1. 三/四个文件都生成了（开 `--preview` 才有 `_预览版.html`）
2. 打开 `_公众号终稿版.html` 或 `_预览版.html`，确认标题/小标题/正文/署名样式正常、没漏图
3. `_纯文本版.txt` 里图片都变成了「【配图：xxx.jpg】」占位，没有残留 markdown 标记

## 环境

零依赖（标准库即可）。需要 Python 3.8+。不读任何项目配置文件。

注意：本 skill 的 `build_deliver.py` 是**唯一**实现——项目里 `gzh.py preview` 子命令也委托它，
不存在第二份 base64 逻辑。
