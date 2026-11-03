---
name: md2card-pro
description: md2card-pro — Markdown 转卡片图片增强版。iOS 27 液态玻璃风格+16种鲜活配色循环+爆款封面+智能短标题+互动引导，新增水印功能（自定义文字/位置/透明度/旋转/平铺），支持批量处理、按文件夹组织、自动打包，优先 Chromium 截图。
---
# md2card-pro · Markdown 转卡片图片技能（增强版·支持水印）

将 Markdown 文件渲染为 iOS 27 液态玻璃风格的 PNG 卡片图片，适合小红书爆款图文、公众号配图、知识卡片等场景。优先使用 Chromium headless 截图。

## 何时使用
- 用户要求把 Markdown / 笔记 / 文档转成图片
- 需要生成小红书爆款图文风格的 3:4 竖版多图（含封面）
- 批量将多篇文章转换为配图
- 需要自动打包为 ZIP 方便下载

## 依赖安装
### 必需
```bash
sudo apt install pandoc
pip install Pillow pypandoc
```
### 截图引擎（推荐 Chromium）
```bash
sudo apt install chromium-browser
```

### Windows 环境（本机已配置，直接照抄）
本机为 Windows，pandoc 与 Chrome 已就绪，**不需要 sudo apt**。
Python 依赖装在隔离虚拟环境里，必须用该解释器运行脚本（系统默认可用的
`python` 是精简版，没有 Pillow / pypandoc）：

```bash
PY="C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
SKILL="C:/Users/Administrator/.workbuddy/skills/md2card-pro"

"$PY" "$SKILL/md2card_pro.py" 输入.md 输出.png --tag "标签"
"$PY" "$SKILL/batch_md2card_pro.py" ./articles/ --auto-tag --workers 4 --by-folder
```

- 引擎：自动命中 `C:\Program Files\Google\Chrome\Application\chrome.exe`，无需指定 `--engine`
- 自带 `bin/wkhtmltoimage` 是 **Linux 二进制，Windows 下不可用**，忽略即可，Chromium 已足够
- 公式渲染依赖 MathJax CDN，转含公式的文档时需要联网

## 使用方法
核心脚本为同目录下的 `md2card_pro.py`，批量处理使用 `batch_md2card_pro.py`。

### 基本用法
```bash
python3 md2card_pro.py 输入.md 输出.png
python3 md2card_pro.py 输入.md 输出.png --tag "标签名"
```
输出为多张 1080×1440（3:4）图片：`输出_1.png`（封面）、`输出_2.png`、`输出_3.png`...

### 作者署名与自定义封面
```bash
# 添加作者署名（显示在封面底部）
python3 md2card_pro.py 输入.md 输出.png --author "作者名"

# 自定义封面标题和副标题（不指定则从md中自动提取）
python3 md2card_pro.py 输入.md 输出.png --cover-title "自定义标题" --cover-subtitle "自定义副标题"
```

### 自动打包
```bash
# 打包生成的图片为 ZIP
python3 md2card_pro.py 输入.md 输出.png --zip

# 打包时包含 Markdown 源文件和 Word 文档
python3 md2card_pro.py 输入.md 输出.png --zip --include-md --include-docx
```

### 水印功能（默认 @读书悦己，已集成最佳配置）
```bash
# 最简单：不指定任何参数，默认添加 @读书悦己 水印
python3 md2card_pro.py 输入.md 输出.png

# 自定义水印文字
python3 md2card_pro.py 输入.md 输出.png --watermark "你的品牌名"

# 关闭水印
python3 md2card_pro.py 输入.md 输出.png --watermark none

# 自定义水印参数（如需调整）
python3 md2card_pro.py 输入.md 输出.png --watermark "作者名" \
  --watermark-position bottom-right --watermark-opacity 0.4 \
  --watermark-size 40 --watermark-color "#333333"

# 给封面也添加水印（默认仅内容页，保持封面美观）
python3 md2card_pro.py 输入.md 输出.png --watermark "品牌名" --watermark-cover
```

**默认配置**（已验证效果好）：
- 水印文字：@读书悦己
- 位置：平铺（tile）— 防盗图效果最佳
- 透明度：0.15 — 不影响阅读
- 字号：32px
- 旋转角度：30度
- 封面：默认不加水印
- 关闭方式：--watermark none

水印参数说明：
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--watermark` | 水印文字内容，不指定则不添加水印 | 无 |
| `--watermark-position` | 位置：`bottom-right`/`bottom-left`/`top-right`/`top-left`/`center`/`tile`(平铺) | `bottom-right` |
| `--watermark-opacity` | 透明度 0.1-0.9 | `0.3` |
| `--watermark-size` | 字号 | `36` |
| `--watermark-color` | 颜色（十六进制） | `#000000` |
| `--watermark-angle` | 旋转角度（平铺模式建议 30） | `0` |
| `--watermark-cover` | 给封面也添加水印 | 关闭（仅内容页） |

### 批量处理模式
使用 `batch_md2card_pro.py` 批量处理目录下所有 Markdown 文件：

```bash
# 基本用法
python3 batch_md2card_pro.py ./articles/ --tag "好书推荐"

# 指定输出目录
python3 batch_md2card_pro.py ./articles/ --output-dir ./images/

# 自动从文件名提取标签
python3 batch_md2card_pro.py ./articles/ --auto-tag

# 按文件夹组织输出（每篇独立文件夹，含图片+md+docx）
python3 batch_md2card_pro.py ./articles/ --by-folder --include-md --include-docx

# 整体打包为 ZIP
python3 batch_md2card_pro.py ./articles/ --by-folder --zip-all output.zip

# 预览模式（仅显示将处理的文件，不实际执行）
python3 batch_md2card_pro.py ./articles/ --dry-run
```

批量模式特性：
- 自动扫描目录下所有 `.md` 文件
- 逐篇转换为图片，保持原文件名
- 支持并发处理（`--workers`）
- 支持按文件夹组织输出
- 支持包含 markdown 和 word 文档
- 支持整体打包为 ZIP
- 显示处理进度和成功/失败统计

### 参数说明
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `md_file` | 输入 Markdown 文件路径（必填） | - |
| `image_file` | 输出图片路径（多图模式下作为文件名前缀） | - |
| `--tag` | 封面标签文字 | `好书推荐` |
| `--author` | 作者署名（显示在封面） | 无 |
| `--cover-title` | 自定义封面标题 | 无 |
| `--cover-subtitle` | 自定义封面副标题 | 无 |
| `--engine` | 截图引擎：`auto` / `chromium` / `wkhtmltoimage` | `auto` |
| `--html` | 保留中间 HTML 文件路径 | 不保留 |
| `--zip` | 处理完成后自动打包生成的图片为 ZIP 文件 | 关闭 |
| `--include-md` | 打包时包含 Markdown 源文件（需配合 --zip） | 关闭 |
| `--include-docx` | 打包时包含 Word 文档（需配合 --zip，需 pandoc） | 关闭 |

## iOS 27 液态玻璃风格特性
- **液态玻璃卡片**：`backdrop-filter: blur(48px) saturate(240%)` 半透明白卡 + 高光边框 + 多层阴影
- **16种鲜活配色**：蓝/紫/粉/橙/青/绿/黄绿/黄/靛蓝/红/天蓝/薄荷/紫蓝/玫粉/紫粉/橙红，红绿色系不相邻
- **爆款封面**：热门徽章 + 双标签 + 智能短标题（超大渐变字体） + 原标题副标题 + 引言框 + 关键词 + 元信息卡片 + 引导文案 + 作者署名
- **封面固定蓝色主题**：鲜亮宝蓝色（`#0066FF`）+ 蓝紫渐变边框，永远不变
- **智能分页**：解析 Markdown 为块，估算高度后均匀分页，章节完整不截断
- **动态字号**：根据每页内容量反推最佳字号（16~28px），非末页目标填充率97%
- **首字放大**：每章第一段首字 3.4em 主题色放大（Drop Cap）
- **进度指示**：顶部主题色进度条 + 右上角大号半透明章节数字
- **精致页码**：底部毛玻璃胶囊 + 主题色文字 + 左右圆点装饰
- **继续阅读引导**：非末页固定显示"继续阅读 →"
- **互动引导**：最后一页自动添加点赞/收藏/关注/转发引导，内容量智能调整尺寸

## 支持的 Markdown 特性
- 标准 Markdown：标题、列表、表格、代码块、引用、链接、图片
- 语法高亮的代码块
- LaTeX 行内公式 `$E=mc^2$`
- LaTeX 块级公式 `$$...$$`

## 工作原理
1. **Markdown → HTML**：pandoc 转换，Chromium 引擎用 MathJax
2. **智能解析**：解析 Markdown 为块结构，估算高度后智能分页
3. **封面生成**：提取标题/引言，生成智能短标题，渲染爆款封面
4. **内容页渲染**：逐页渲染完整卡片，动态字号，16色循环
5. **后处理**：页码指示器、互动引导、裁剪到标准尺寸
6. **自动打包**：可选打包为 ZIP（含图片+md+docx）

## 文件结构
```
md2card_pro/
├── SKILL.md              # 本说明文档
├── md2card_pro.py             # 核心转换脚本
├── batch_md2card_pro.py       # 批量处理脚本
├── install.sh            # 依赖安装脚本
├── README.md             # 项目说明
└── bin/
    └── wkhtmltoimage     # 备选截图引擎（Linux二进制）
```

## 注意事项
- Chromium 引擎下公式渲染依赖 MathJax CDN，转换时需联网
- 多图模式输出多张图片，文件名格式为 `{前缀}_{序号}.png`
- 若文章过长导致超过 9 张，建议精简内容或分两篇笔记发布
- 批量模式下建议先用 `--dry-run` 预览，确认文件列表后再执行
