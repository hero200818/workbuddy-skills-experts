# 头条号爆款文章自动生成器 - 使用说明

## 一、功能介绍

输入图书/电视剧/电影名称，自动批量生成符合头条号要求的爆款文章，并保存为 **Markdown + Word + 图片** 到你指定的本地文件夹。

生成的每篇文章独立存放于一个文件夹中，包含：
- `.md` 文件：Markdown原文，可直接复制
- `.docx` 文件：Word文档，可编辑修改
- `.png` 图片：爆款封面 + 内容配图 + 互动引导页（可选）

## 二、环境准备

### 2.1 安装 Python

确保你的电脑已安装 Python 3.8 或更高版本。
- 下载地址：https://www.python.org/downloads/
- 安装时勾选 "Add Python to PATH"

### 2.2 安装依赖

打开命令行（Windows按Win+R输入cmd，Mac打开终端），进入工具目录：

```bash
cd toutiao_auto_tool
pip install requests pyyaml python-docx pillow
```

### 2.3 （可选）安装图片生成依赖

如果需要自动生成配图，还需安装：

**Windows:**
```bash
# 安装 pandoc（下载安装包）
# 下载地址：https://pandoc.org/installing.html
# 安装 Chromium 或 Chrome 浏览器（一般已安装）
```

**Mac:**
```bash
brew install pandoc
# Chrome浏览器一般已安装
```

**Linux:**
```bash
sudo apt install pandoc chromium-browser
```

然后将 markpic 技能的 `md2img.py` 放到工具目录下（或在脚本中指定路径）。

## 三、获取 API Key

### 3.1 豆包API（推荐）

1. 访问火山引擎控制台：https://console.volcengine.com/ark
2. 注册/登录账号
3. 进入「模型推理」→「在线推理」
4. 创建推理接入点，获取 API Key
5. 选择模型：doubao-pro-32k（或其他模型）

### 3.2 OpenAI API

1. 访问 https://platform.openai.com/
2. 注册账号并充值
3. 进入 API Keys 页面，创建新的 Secret Key
4. 模型选择：gpt-4o 或 gpt-3.5-turbo

## 四、配置文件

1. 复制 `config.example.yaml` 为 `config.yaml`
2. 用记事本/文本编辑器打开 `config.yaml`
3. 填入你的 API Key
4. 根据需要修改其他配置（文章数量、输出目录、风格等）

**关键配置项说明：**

```yaml
api:
  api_key: "你的API_KEY"        # 必填，你的API密钥
  base_url: "https://ark.cn-beijing.volces.com/api/v3"  # API地址
  model: "doubao-pro-32k"       # 模型名称

generation:
  article_count: 10             # 生成几篇文章
  target_words: 3000            # 每篇目标字数
  style: "literature"           # 风格：literature/history/parenting等
  generate_images: true         # 是否生成图片

output:
  output_dir: "./output"        # 输出目录，可改为绝对路径
  # 例如 Windows: "C:/Users/你的用户名/Documents/头条文章"
  # 例如 Mac: "/Users/你的用户名/Documents/头条文章"
```

## 五、运行生成

### 5.1 基本用法

```bash
python toutiao_generator.py "围城"
```

### 5.2 指定文章数量

```bash
python toutiao_generator.py "大明王朝1566" -n 5
```

### 5.3 不生成图片（更快）

```bash
python toutiao_generator.py "养育男孩" --no-images
```

### 5.4 不生成Word

```bash
python toutiao_generator.py "三体" --no-word
```

### 5.5 指定配置文件

```bash
python toutiao_generator.py "红楼梦" -c my_config.yaml
```

## 六、输出目录结构

运行完成后，文件保存在 `output/作品名_日期/` 目录下：

```
output/
└── 围城_20260819/
    ├── 00_目录索引.md
    ├── 01_方鸿渐一个好人为什么过不好一生/
    │   ├── 01_方鸿渐一个好人为什么过不好一生.md      ← Markdown
    │   ├── 01_方鸿渐一个好人为什么过不好一生.docx    ← Word
    │   ├── 01_方鸿渐一个好人为什么过不好一生_1.png   ← 封面图
    │   ├── 01_方鸿渐一个好人为什么过不好一生_2.png   ← 内容图
    │   └── ...
    ├── 02_孙柔嘉她不是心机女是围城最清醒的人/
    │   └── ...
    └── ...
```

## 七、发布到头条号

1. 打开对应文章的文件夹
2. 双击 `.docx` 文件，全选复制正文
3. 登录头条号后台：https://mp.toutiao.com/
4. 点击「发表」→「文章」
5. 粘贴正文，修改标题
6. 上传 `_1.png` 作为封面
7. 依次上传其他图片作为文中配图
8. 选择分类、标签，点击发布

## 八、常见问题

**Q: 提示 "API Key 错误" 怎么办？**
A: 检查 config.yaml 中的 api_key 是否正确，是否有多余的空格。

**Q: 生成速度很慢？**
A: 每篇文章需要调用API生成，10篇大约需要5-10分钟。可以用 `--no-images` 跳过图片生成加快速度。

**Q: 图片没有生成？**
A: 检查是否安装了 pandoc 和 Chrome/Chromium，以及 md2img.py 的路径是否正确。

**Q: 可以修改文章风格吗？**
A: 在 config.yaml 中修改 `generation.style` 和 `writing_rules` 下的配置。

**Q: 如何批量生成多个作品？**
A: 可以写一个批处理脚本，多次调用 toutiao_generator.py。

## 九、批处理示例（Windows）

创建 `batch.bat` 文件：

```batch
@echo off
python toutiao_generator.py "围城"
python toutiao_generator.py "红楼梦"
python toutiao_generator.py "三国演义"
echo 全部完成！
pause
```

双击运行即可批量生成。

## 十、技术支持

如遇到问题，请检查：
1. Python 版本是否 >= 3.8
2. 依赖是否全部安装
3. API Key 是否正确
4. 网络是否正常（调用API需要联网）
