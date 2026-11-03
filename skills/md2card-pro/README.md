# md2card-pro · Markdown 转卡片图片增强版

将 Markdown 文件一键转换为 iOS 27 液态玻璃风格的高清精美 PNG 卡片图片，适配小红书爆款图文、公众号配图、知识卡片等场景。默认集成 `@读书悦己` 水印。

## 特性

- **iOS 27 液态玻璃**：半透明毛玻璃卡片 + 柔和渐变背景 + 通透折射 + 圆润边角
- **16 色鲜活循环**：内容页每页独立主题色，红绿色系不相邻
- **爆款封面**：智能短标题 + 热门徽章 + 双标签 + 引言框 + 关键词 + 元信息卡片
- **封面固定蓝色**：鲜亮宝蓝色主题 + 蓝紫渐变边框，永远不变
- **智能分页**：解析 Markdown 块结构，章节完整不截断
- **动态字号**：根据内容量自动调整最佳字号，满图显示（末页除外）
- **首字放大**：每章第一段首字 3.4em 主题色放大（Drop Cap）
- **进度指示**：顶部主题色进度条 + 右上角大号半透明章节数字
- **继续阅读**：非末页固定显示"继续阅读 →"引导
- **互动引导**：末页自动添加点赞/收藏/关注/转发，内容量智能调整尺寸
- **水印功能**：默认 `@读书悦己` 平铺水印，支持自定义文字/位置/透明度/字号/颜色/旋转
- **公式渲染**：支持 MathJax 数学公式
- **双引擎**：优先 Chromium headless，备选 wkhtmltoimage
- **批量处理**：支持多文件并发、按文件夹组织、自动生成 Word 文档、整体打包

## 快速开始

### 1. 安装依赖

```bash
bash install.sh
```

或手动安装：

```bash
sudo apt install pandoc chromium-browser
pip install pypandoc Pillow
```

### 2. 单文件转换

```bash
# 最简单：默认 iOS 风格 + 默认 @读书悦己 水印
python3 md2card_pro.py 文章.md 输出.png

# 自定义标签
python3 md2card_pro.py 文章.md 输出.png --tag "明朝那些事"

# 自定义水印文字
python3 md2card_pro.py 文章.md 输出.png --watermark "你的品牌名"

# 关闭水印
python3 md2card_pro.py 文章.md 输出.png --watermark none

# 自动打包（图片+md+docx）
python3 md2card_pro.py 文章.md 输出.png --zip --include-md --include-docx
```

### 3. 批量处理

```bash
# 并发处理 + 自动标签 + 按文件夹组织 + 包含md/docx + 整体打包
python3 batch_md2card_pro.py ./articles/ \
  --auto-tag --workers 4 \
  --by-folder --include-md --include-docx \
  --zip-all output.zip
```

## 水印功能

### 默认配置（已验证效果好）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--watermark` | `@读书悦己` | 水印文字，`none` 可关闭 |
| `--watermark-position` | `tile` | 位置：平铺/右下角/左下角/右上角/左上角/居中 |
| `--watermark-opacity` | `0.15` | 透明度 0.1-0.9 |
| `--watermark-size` | `32` | 字号（像素） |
| `--watermark-color` | `#000000` | 颜色（十六进制） |
| `--watermark-angle` | `30` | 旋转角度（度） |
| `--watermark-cover` | 关闭 | 给封面也加水印（默认仅内容页） |

### 水印示例

```bash
# 右下角品牌水印
python3 md2card_pro.py 文章.md 输出.png \
  --watermark "品牌名" --watermark-position bottom-right \
  --watermark-opacity 0.4 --watermark-size 40

# 平铺防盗图水印（推荐低透明度+旋转）
python3 md2card_pro.py 文章.md 输出.png \
  --watermark "@读书悦己" --watermark-position tile \
  --watermark-opacity 0.15 --watermark-angle 30
```

## 参数说明

### md2card_pro.py

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `md_file` | 输入 Markdown 文件路径（必填） | - |
| `image_file` | 输出图片路径（多图时作为前缀） | - |
| `--tag` | 封面标签文字 | `好书推荐` |
| `--author` | 作者署名（显示在封面） | 无 |
| `--cover-title` | 自定义封面标题 | 无 |
| `--cover-subtitle` | 自定义封面副标题 | 无 |
| `--engine` | `auto` / `chromium` / `wkhtmltoimage` | `auto` |
| `--html` | 保留中间 HTML 文件 | 不保留 |
| `--zip` | 自动打包生成的图片为 ZIP | 关闭 |
| `--include-md` | 打包时包含 Markdown 源文件 | 关闭 |
| `--include-docx` | 打包时包含 Word 文档 | 关闭 |
| `--watermark` | 水印文字（`none` 关闭） | `@读书悦己` |
| `--watermark-position` | 水印位置 | `tile` |
| `--watermark-opacity` | 水印透明度 | `0.15` |
| `--watermark-size` | 水印字号 | `32` |
| `--watermark-color` | 水印颜色 | `#000000` |
| `--watermark-angle` | 水印旋转角度 | `30` |
| `--watermark-cover` | 给封面也加水印 | 关闭 |

### batch_md2card_pro.py

| 参数 | 说明 |
|------|------|
| `input_dir` | 包含 Markdown 文件的目录（必填） |
| `--output-dir` | 输出目录 |
| `--tag` / `--auto-tag` | 固定标签 / 自动从文件名提取 |
| `--author` | 作者署名 |
| `--workers` | 并发进程数（默认 1，建议 2-4） |
| `--retries` | 失败重试次数（默认 1） |
| `--timeout` | 单文件超时秒数（默认 300） |
| `--skip-existing` | 跳过已处理文件 |
| `--pattern` | 文件名过滤正则 |
| `--by-folder` | 按文件名创建独立文件夹 |
| `--include-md` | 包含 Markdown 源文件 |
| `--include-docx` | 包含 Word 文档 |
| `--zip-all` | 整体打包为 ZIP |
| `--dry-run` | 预览模式 |
| `--report` | 生成处理报告 JSON |
| `--watermark` 系列 | 同单文件水印参数 |

## 目录结构

```
md2card-pro/
├── SKILL.md              # 技能说明文档（Agent 加载入口）
├── README.md             # 项目说明
├── md2card_pro.py        # 核心转换脚本
├── batch_md2card_pro.py  # 批量处理工具
├── install.sh            # 依赖安装脚本
└── bin/
    └── wkhtmltoimage     # 备选截图引擎（Linux 二进制）
```

## 系统要求

- Python 3.8+
- pandoc 2.0+
- Chromium / Google Chrome（首选）或 wkhtmltoimage（备选）
- Python 包：pypandoc, Pillow
