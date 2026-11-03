# md2card-pro 技能安装说明

## 技能简介

md2card-pro 是一个将 Markdown 文件一键转换为 iOS 27 液态玻璃风格高清 PNG 卡片图片的技能，支持：

- iOS 27 液态玻璃风格（唯一风格）
- 16种鲜活配色循环（内容页）
- 爆款封面（智能短标题 + 热门徽章 + 元信息卡片）
- 封面固定宝蓝主题 + 蓝紫渐变边框
- 智能分页 + 动态字号（满图显示）
- 默认 `@读书悦己` 平铺水印（可自定义/关闭）
- 末页互动引导（点赞/收藏/关注/转发）
- 单文件打包（图片+md+docx）
- 批量处理（并发/按文件夹组织/整体打包）
- 双引擎（Chromium 优先 / wkhtmltoimage 备选）

## 安装方法

### 方法一：直接复制到技能目录（推荐）

将整个 `md2card-pro/` 目录复制到 Agent 的技能目录下：

```bash
# 复制到用户技能目录
cp -r md2card-pro/ ~/.super_doubao/super-doubao-runtime/workspace/.user_skills/

# 或复制到系统技能目录
cp -r md2card-pro/ ~/.super_doubao/super-doubao-runtime/workspace/.skills/
```

复制后，Agent 会自动识别 `SKILL.md` 并加载该技能。

### 方法二：在任意目录使用

不复制到技能目录也可以直接通过命令行调用：

```bash
python3 /path/to/md2card-pro/md2card_pro.py 输入.md 输出.png
```

## 依赖安装

### 必需依赖

```bash
# 系统依赖
sudo apt install pandoc chromium-browser

# Python 依赖
pip install pypandoc Pillow -i https://pypi.org/simple/
```

### 一键安装

```bash
bash md2card-pro/install.sh
```

### 备选引擎（可选）

技能自带 `bin/wkhtmltoimage` Linux 二进制，Chromium 不可用时自动回退。

## 使用方法

### 单文件转换

```bash
# 最简单：默认配置（iOS风格 + @读书悦己水印）
python3 md2card_pro.py 文章.md 输出.png

# 自定义标签
python3 md2card_pro.py 文章.md 输出.png --tag "明朝那些事"

# 关闭水印
python3 md2card_pro.py 文章.md 输出.png --watermark none

# 自定义水印
python3 md2card_pro.py 文章.md 输出.png --watermark "你的品牌名"

# 自动打包（图片+md+docx）
python3 md2card_pro.py 文章.md 输出.png --zip --include-md --include-docx
```

### 批量处理

```bash
# 基本批量处理
python3 batch_md2card_pro.py ./articles/ --auto-tag

# 完整批量处理（并发+按文件夹+包含源文件+整体打包）
python3 batch_md2card_pro.py ./articles/ \
  --auto-tag --workers 4 \
  --by-folder --include-md --include-docx \
  --zip-all output.zip
```

## 水印参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--watermark` | `@读书悦己` | 水印文字，`none` 关闭 |
| `--watermark-position` | `tile` | 位置：tile/bottom-right/bottom-left/top-right/top-left/center |
| `--watermark-opacity` | `0.15` | 透明度 0.1-0.9 |
| `--watermark-size` | `32` | 字号（像素） |
| `--watermark-color` | `#000000` | 颜色（十六进制） |
| `--watermark-angle` | `30` | 旋转角度（度） |
| `--watermark-cover` | 关闭 | 给封面也加水印 |

## 文件结构

```
md2card-pro/
├── SKILL.md              # 技能说明（Agent 加载入口，必须）
├── README.md             # 项目说明
├── INSTALL.md            # 安装说明（本文件）
├── md2card_pro.py        # 核心转换脚本
├── batch_md2card_pro.py  # 批量处理工具
├── install.sh            # 依赖安装脚本
└── bin/
    └── wkhtmltoimage     # 备选截图引擎（Linux 二进制，46MB）
```

## 系统要求

- Python 3.8+
- pandoc 2.0+
- Chromium / Google Chrome（首选）或 wkhtmltoimage（备选，已自带）
- Python 包：pypandoc, Pillow

## 验证安装

安装完成后，运行以下命令验证：

```bash
# 查看帮助
python3 md2card_pro.py --help

# 测试转换（需要一个测试用的 md 文件）
python3 md2card_pro.py test.md test_output.png
```

如果能正常显示帮助信息并生成图片，说明安装成功。

## 注意事项

1. **SKILL.md 是必须的**：Agent 通过识别 `SKILL.md` 文件来加载技能，不要删除或重命名
2. **name 字段**：`SKILL.md` 中的 `name: md2card-pro` 是技能的唯一标识，不要修改
3. **bin 目录**：`bin/wkhtmltoimage` 是备选引擎，建议保留（46MB）
4. **pypandoc 安装**：需使用官方 PyPI 源，清华镜像可能不可用
5. **Chromium 推荐**：公式渲染和复杂样式建议使用 Chromium，效果最佳
