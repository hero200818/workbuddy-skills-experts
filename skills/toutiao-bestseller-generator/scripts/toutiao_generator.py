#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
头条号爆款文章自动生成器
========================
功能：输入图书/电视剧/电影名称，自动批量生成符合头条号要求的爆款文章，
      并保存为 Markdown + Word + 图片（可选）到指定本地目录。

使用方法：
  1. 复制 config.example.yaml 为 config.yaml，填入你的 API Key
  2. 运行：python toutiao_generator.py "围城"
  3. 生成的文件保存在 output/ 目录下（可在 config.yaml 中修改）

依赖安装：
  pip install requests pyyaml python-docx pillow
  可选（图片生成）：安装 pandoc + chromium，以及 markpic 技能的 md2img.py
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    print("请先安装依赖：pip install pyyaml")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("请先安装依赖：pip install requests")
    sys.exit(1)


# ============================================================
# 配置管理
# ============================================================

class Config:
    """配置管理器"""

    def __init__(self, config_path="config.yaml"):
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            self._create_default_config()
        self.config = self._load_config()

    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = """# 头条号爆款文章生成器 - 配置文件
# ============================================

# API 配置（支持豆包API / OpenAI兼容API）
api:
  # 服务商：doubao（豆包）/ openai（OpenAI兼容）
  provider: "doubao"
  # API Key（必填）
  api_key: "你的API_KEY"
  # API 地址
  # 豆包：https://ark.cn-beijing.volces.com/api/v3
  # OpenAI：https://api.openai.com/v1
  base_url: "https://ark.cn-beijing.volces.com/api/v3"
  # 模型名称
  # 豆包：doubao-pro-32k / doubao-lite-32k 等
  # OpenAI：gpt-4o / gpt-3.5-turbo 等
  model: "doubao-pro-32k"
  # 生成参数
  temperature: 0.8
  max_tokens: 4000

# 生成配置
generation:
  # 每批生成文章数量
  article_count: 10
  # 每篇文章目标字数
  target_words: 3000
  # 文章风格：literature（文学/经典）/ history（历史）/ parenting（育儿）/ 
  #          selfhelp（成长）/ business（商业）/ science（科普）/ custom（自定义）
  style: "literature"
  # 是否自动生成图片（需要安装 markpic + pandoc + chromium）
  generate_images: true
  # 图片风格：ios（iOS液态玻璃）/ xiaohongshu（笔记本手账）/ default（默认长图）
  image_style: "ios"
  # 图片标签（封面文字）
  image_tag: "好书推荐"
  # 图片作者署名（封面底部，留空则不署名）
  image_author: "读读书悦悦己"

# 输出配置
output:
  # 输出目录（支持相对路径和绝对路径）
  output_dir: "./output"
  # 文件夹命名格式：{work} 为作品名，{date} 为日期
  folder_format: "{work}_{date}"
  # 是否生成 Word 文档
  generate_word: true
  # 是否生成 Markdown
  generate_markdown: true
  # 是否在每个文章文件夹中包含图片
  images_in_folder: true

# 写作规范（可根据需要调整）
writing_rules:
  # 标题公式：悬念式 / 反常识 / 数字清单 / 对比式 / 痛点式
  title_formula: "悬念式"
  # 开头方式：场景化 / 提问式 / 数据冲击 / 故事引入
  opening_style: "场景化"
  # 结尾方式：互动引导 / 金句总结 / 行动号召
  ending_style: "互动引导"
  # 是否引用原文
  quote_original: true
  # 去AI味（使用口语化表达）
  remove_ai_taste: true
"""
        self.config_path.write_text(default_config, encoding="utf-8")
        print(f"已创建默认配置文件：{self.config_path}")
        print("请编辑该文件，填入你的 API Key 后重新运行。")
        sys.exit(0)

    def _load_config(self):
        """加载配置"""
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get(self, key, default=None):
        """获取配置项"""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


# ============================================================
# 大模型 API 调用
# ============================================================

class LLMClient:
    """大模型客户端"""

    def __init__(self, config):
        self.api_key = config.get("api.api_key")
        self.base_url = config.get("api.base_url")
        self.model = config.get("api.model")
        self.temperature = config.get("api.temperature", 0.8)
        self.max_tokens = config.get("api.max_tokens", 4000)
        self.provider = config.get("api.provider", "doubao")

        if not self.api_key or self.api_key == "你的API_KEY":
            print("错误：请在 config.yaml 中填入你的 API Key")
            sys.exit(1)

    def chat(self, system_prompt, user_prompt, max_retries=3):
        """调用聊天接口"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        url = f"{self.base_url}/chat/completions"

        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=120)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"  第 {attempt+1} 次调用失败：{e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    print(f"  调用失败，已重试 {max_retries} 次")
                    return None

    def generate(self, prompt, system_prompt=None):
        """生成内容"""
        if system_prompt is None:
            system_prompt = "你是一个资深的头条号爆款文章写手，擅长写有深度、有温度、能引发共鸣的文章。"
        return self.chat(system_prompt, prompt)


# ============================================================
# 文章生成器
# ============================================================

class ArticleGenerator:
    """文章生成器"""

    def __init__(self, llm_client, config):
        self.llm = llm_client
        self.config = config

    def generate_background(self, work_name):
        """生成作品背景资料"""
        print(f"[1/4] 正在检索《{work_name}》背景资料...")
        prompt = f"""请详细整理以下作品的背景资料，用于后续生成头条号爆款文章。

作品名称：{work_name}

请从以下维度整理：
1. 作品基本信息（作者、出版/上映时间、类型、地位）
2. 核心内容概述（不超过300字）
3. 主要人物介绍（5-8个核心人物，每人50字）
4. 经典情节/名场面（3-5个）
5. 主题思想与深层含义
6. 创作背景与时代意义
7. 社会影响与评价
8. 可延伸的话题角度（5-8个）

要求：信息准确，条理清晰，为后续文章生成提供充分素材。"""

        return self.llm.generate(prompt)

    def generate_topics(self, work_name, background, count=10):
        """生成选题规划"""
        print(f"[2/4] 正在规划 {count} 篇选题...")
        style = self.config.get("generation.style", "literature")

        style_desc = {
            "literature": "文学/经典类：侧重人物解读、主题分析、写作手法、现实共鸣",
            "history": "历史类：侧重事件还原、人物评说、制度分析、古今对比",
            "parenting": "育儿类：侧重实操方法、年龄特点、常见误区、案例分析",
            "selfhelp": "成长类：侧重认知升级、习惯养成、心态调整、行动指南",
            "business": "商业类：侧重商业模式、竞争分析、案例拆解、趋势洞察",
            "science": "科普类：侧重原理解释、现象解读、趣味知识、生活应用",
            "custom": "自定义风格"
        }.get(style, "通用风格")

        prompt = f"""基于以下作品资料，规划 {count} 篇头条号爆款文章的选题。

作品：{work_name}
风格：{style_desc}

【作品背景资料】
{background}

【选题要求】
1. 每篇选题包含：标题（爆款风格，带悬念/冲突/反常识）+ 核心角度（一句话）
2. 选题维度分布：人物解读35% + 情节分析15% + 观点深度25% + 背景延伸15% + 现实对比10%
3. 标题要符合头条号爆款调性：有悬念、有冲突、有数字、有情绪
4. 避免重复角度，覆盖不同读者群体
5. 每篇目标字数：{self.config.get('generation.target_words', 3000)}字

请按以下格式输出：
01. 【标题】—— 核心角度
02. 【标题】—— 核心角度
..."""

        result = self.llm.generate(prompt)
        return result

    def generate_article(self, work_name, background, topic, index):
        """生成单篇文章"""
        title_formula = self.config.get("writing_rules.title_formula", "悬念式")
        opening_style = self.config.get("writing_rules.opening_style", "场景化")
        ending_style = self.config.get("writing_rules.ending_style", "互动引导")
        target_words = self.config.get("generation.target_words", 3000)

        prompt = f"""请根据以下信息，写一篇符合头条号要求的爆款文章。

【作品】{work_name}
【选题】{topic}
【目标字数】{target_words}字

【作品背景资料】
{background}

【写作要求】
1. 标题：使用{title_formula}，有悬念/冲突/反常识，让人想点进来
2. 开头：使用{opening_style}，前3句话抓住读者注意力
3. 正文：
   - 分3-5个小节，每节有小标题
   - 有具体细节、有场景描写、有情感共鸣
   - 引用原文/原剧经典台词（如适用）
   - 语言口语化，去AI味，像跟朋友聊天
   - 有金句、有观点、有温度
4. 结尾：使用{ending_style}，引导评论区互动
5. 整体：符合头条号调性，适合大众阅读，有传播力

请直接输出文章正文（包含标题），不要输出其他解释性文字。"""

        system_prompt = """你是一个拥有10年经验的头条号爆款写手，曾写出多篇10万+文章。
你深谙头条号算法和读者心理，擅长用口语化的表达写有深度的内容。
你的文章特点：有故事、有细节、有情感、有金句，让人读完想转发。
严格避免AI腔（不要"首先其次最后"、不要"综上所述"、不要空泛的排比）。"""

        return self.llm.generate(prompt, system_prompt)

    def generate_batch(self, work_name, count=10):
        """批量生成文章"""
        # 1. 生成背景
        background = self.generate_background(work_name)
        if not background:
            print("背景资料生成失败，请检查API配置")
            return []

        # 2. 生成选题
        topics_text = self.generate_topics(work_name, background, count)
        if not topics_text:
            print("选题规划生成失败")
            return []

        # 解析选题
        topics = self._parse_topics(topics_text)
        print(f"  已规划 {len(topics)} 篇选题")

        # 3. 批量生成文章
        print(f"[3/4] 正在批量生成 {len(topics)} 篇文章...")
        articles = []
        for i, topic in enumerate(topics, 1):
            print(f"  正在生成第 {i}/{len(topics)} 篇：{topic[:30]}...")
            article = self.generate_article(work_name, background, topic, i)
            if article:
                articles.append({
                    "index": i,
                    "topic": topic,
                    "content": article
                })
            else:
                print(f"  第 {i} 篇生成失败，跳过")
            time.sleep(1)  # 避免请求过快

        return articles

    def _parse_topics(self, topics_text):
        """解析选题文本"""
        topics = []
        for line in topics_text.strip().split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("0")):
                # 去掉序号
                if "." in line[:5]:
                    topic = line.split(".", 1)[1].strip()
                else:
                    topic = line
                topics.append(topic)
        return topics if topics else [topics_text]


# ============================================================
# 文件输出管理器
# ============================================================

class OutputManager:
    """文件输出管理器"""

    def __init__(self, config):
        self.config = config
        self.output_dir = Path(config.get("output.output_dir", "./output"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_work_folder(self, work_name):
        """创建作品文件夹"""
        date_str = datetime.now().strftime("%Y%m%d")
        folder_name = self.config.get("output.folder_format", "{work}_{date}").format(
            work=work_name, date=date_str
        )
        # 清理非法字符
        folder_name = "".join(c for c in folder_name if c not in r'\/:*?"<>|')
        work_dir = self.output_dir / folder_name
        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir

    def save_article(self, work_dir, article, work_name):
        """保存单篇文章（创建独立文件夹，包含md+docx+图片）"""
        index = article["index"]
        content = article["content"]

        # 从内容中提取标题
        title = self._extract_title(content)
        safe_title = "".join(c for c in title if c not in r'\/:*?"<>|')[:50]
        file_prefix = f"{index:02d}_{safe_title}"

        # 创建文章子文件夹
        article_dir = work_dir / f"{index:02d}_{safe_title}"
        article_dir.mkdir(exist_ok=True)

        saved_files = {"md": None, "docx": None, "images": []}

        # 保存 Markdown
        if self.config.get("output.generate_markdown", True):
            md_path = article_dir / f"{file_prefix}.md"
            md_path.write_text(content, encoding="utf-8")
            saved_files["md"] = str(md_path)
            print(f"    已保存 Markdown：{md_path.name}")

        # 保存 Word
        if self.config.get("output.generate_word", True):
            docx_path = article_dir / f"{file_prefix}.docx"
            if self._save_as_docx(content, docx_path):
                saved_files["docx"] = str(docx_path)
                print(f"    已保存 Word：{docx_path.name}")

        # 生成图片
        if self.config.get("generation.generate_images", False):
            images = self._generate_images(md_path if saved_files["md"] else None,
                                           article_dir, file_prefix)
            saved_files["images"] = images

        return saved_files

    def _extract_title(self, content):
        """从文章内容中提取标题"""
        for line in content.strip().split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
            elif line and not line.startswith("#"):
                return line[:50]
        return "未命名文章"

    def _save_as_docx(self, content, output_path):
        """保存为Word文档"""
        try:
            from docx import Document
            from docx.shared import Pt
            from docx.enum.text import WD_ALIGN_PARAGRAPH

            doc = Document()

            # 设置默认字体
            style = doc.styles["Normal"]
            style.font.name = "宋体"
            style.font.size = Pt(12)

            for line in content.split("\n"):
                line = line.rstrip()
                if not line:
                    doc.add_paragraph()
                    continue

                if line.startswith("# "):
                    p = doc.add_heading(line[2:], level=1)
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif line.startswith("## "):
                    doc.add_heading(line[3:], level=2)
                elif line.startswith("### "):
                    doc.add_heading(line[4:], level=3)
                elif line.startswith("- ") or line.startswith("* "):
                    doc.add_paragraph(line[2:], style="List Bullet")
                elif line.startswith("**") and line.endswith("**"):
                    p = doc.add_paragraph()
                    run = p.add_run(line.strip("*"))
                    run.bold = True
                else:
                    doc.add_paragraph(line)

            doc.save(str(output_path))
            return True
        except ImportError:
            print("    未安装 python-docx，尝试用 pandoc 转换...")
            return self._convert_with_pandoc(content, output_path)
        except Exception as e:
            print(f"    Word生成失败：{e}")
            return False

    def _convert_with_pandoc(self, content, output_path):
        """使用pandoc转换为Word"""
        try:
            # 先写临时md文件
            temp_md = output_path.with_suffix(".tmp.md")
            temp_md.write_text(content, encoding="utf-8")
            subprocess.run(
                ["pandoc", str(temp_md), "-o", str(output_path)],
                check=True, capture_output=True
            )
            temp_md.unlink()
            return True
        except Exception as e:
            print(f"    pandoc转换失败：{e}")
            return False

    def _find_run_markpic(self):
        """查找 WorkBuddy 适配启动器 run_markpic.py（已注入 PATH/venv/中文JSON）"""
        candidates = [
            Path.home() / ".workbuddy/bin/run_markpic.py",
            Path("./run_markpic.py"),
            Path.home() / ".super_doubao/super-doubao-runtime/workspace/.user_skills/bin/run_markpic.py",
        ]
        for p in candidates:
            if p.exists():
                return str(p)
        return None

    def _find_md2img(self):
        """查找 md2img.py（降级路径，含 WorkBuddy 实际安装位置与脚本同目录内置副本）"""
        candidates = [
            Path(__file__).resolve().parent / "md2img.py",  # 随包内置副本（发布包自包含）
            Path.home() / ".workbuddy/skills/markpic/md2img.py",
            Path("./md2img.py"),
            Path("../markpic/md2img.py"),
            Path.home() / ".super_doubao/super-doubao-runtime/workspace/.user_skills/markpic/md2img.py",
            Path.home() / ".super_doubao/super-doubao-runtime/workspace/skills/markpic/md2img.py",
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    def _generate_images(self, md_path, article_dir, file_prefix):
        """生成图片（调用MarkPic）

        优先使用 WorkBuddy 适配启动器 run_markpic.py（自动注入 Chromium/pandoc
        的 Windows 风格 PATH，并通过 UTF-8 JSON 传中文参数，规避 Git Bash 编码坑）；
        未找到启动器时降级为直接调用 md2img.py（同样使用 sys.executable 而非
        python3，并兼容 ~/.workbuddy/skills 安装位置）。
        """
        if not md_path or not Path(md_path).exists():
            return []

        article_dir = Path(article_dir)
        image_style = self.config.get("generation.image_style", "ios")
        image_tag = self.config.get("generation.image_tag", "好书推荐")
        author = (self.config.get("generation.image_author")
                  or self.config.get("output.author"))

        # 优先：WorkBuddy 适配启动器（最稳，已处理 Windows 适配）
        run_markpic = self._find_run_markpic()
        if run_markpic:
            import tempfile
            import json
            cfg = {
                "input": str(Path(md_path)),
                "output": str(article_dir / file_prefix),
                "style": image_style,
                "tag": image_tag,
            }
            if author:
                cfg["author"] = author
            cfg_path = article_dir / f".{file_prefix}_imgcfg.json"
            cfg_path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
            try:
                subprocess.run([sys.executable, run_markpic, str(cfg_path)],
                               capture_output=True, text=True, timeout=180)
                cfg_path.unlink(missing_ok=True)
                images = sorted(article_dir.glob(f"{file_prefix}_*.png"))
                print(f"    已生成 {len(images)} 张图片")
                return [str(img) for img in images]
            except Exception as e:
                print(f"    图片生成失败：{e}")
                return []

        # 降级：直接调用 md2img.py
        md2img = self._find_md2img()
        if not md2img:
            print("    未找到 md2img.py / run_markpic.py，跳过图片生成")
            return []

        try:
            output_prefix = article_dir / file_prefix
            cmd = [sys.executable, str(md2img), str(md_path), str(output_prefix),
                   "--style", image_style, "--tag", image_tag]
            if author:
                cmd += ["--author", author]
            subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            images = sorted(article_dir.glob(f"{file_prefix}_*.png"))
            print(f"    已生成 {len(images)} 张图片")
            return [str(img) for img in images]
        except Exception as e:
            print(f"    图片生成失败：{e}")
            return []

    def save_index(self, work_dir, articles, work_name):
        """保存目录索引"""
        index_path = work_dir / "00_目录索引.md"
        content = f"# 《{work_name}》头条号爆款文章合集\n\n"
        content += f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        content += f"> 文章数量：{len(articles)}篇\n\n"
        content += "## 文章目录\n\n"
        content += "| 序号 | 标题 | 核心角度 |\n|------|------|----------|\n"
        for art in articles:
            title = self._extract_title(art["content"])
            topic = art["topic"].replace("|", "/")
            content += f"| {art['index']:02d} | {title} | {topic} |\n"
        index_path.write_text(content, encoding="utf-8")
        print(f"  已保存目录索引：{index_path.name}")


# ============================================================
# 主程序
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="头条号爆款文章自动生成器")
    parser.add_argument("work_name", help="作品名称（图书/电视剧/电影）")
    parser.add_argument("-c", "--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("-n", "--count", type=int, help="生成文章数量（覆盖配置文件）")
    parser.add_argument("--no-images", action="store_true", help="不生成图片")
    parser.add_argument("--no-word", action="store_true", help="不生成Word文档")
    args = parser.parse_args()

    print("=" * 60)
    print("  头条号爆款文章自动生成器")
    print("=" * 60)
    print(f"  作品：{args.work_name}")
    print()

    # 加载配置
    config = Config(args.config)

    # 命令行参数覆盖
    if args.count:
        config.config["generation"]["article_count"] = args.count
    if args.no_images:
        config.config["generation"]["generate_images"] = False
    if args.no_word:
        config.config["output"]["generate_word"] = False

    # 初始化
    llm = LLMClient(config)
    generator = ArticleGenerator(llm, config)
    output_mgr = OutputManager(config)

    # 批量生成
    count = config.get("generation.article_count", 10)
    articles = generator.generate_batch(args.work_name, count)

    if not articles:
        print("没有生成任何文章，请检查API配置后重试")
        return

    # 保存文件
    print(f"[4/4] 正在保存 {len(articles)} 篇文章到本地...")
    work_dir = output_mgr.create_work_folder(args.work_name)
    print(f"  输出目录：{work_dir.absolute()}")

    for art in articles:
        print(f"  保存第 {art['index']} 篇...")
        output_mgr.save_article(work_dir, art, args.work_name)

    # 保存目录索引
    output_mgr.save_index(work_dir, articles, args.work_name)

    print()
    print("=" * 60)
    print(f"  全部完成！共生成 {len(articles)} 篇文章")
    print(f"  文件保存在：{work_dir.absolute()}")
    print("=" * 60)
    print()
    print("  每个文章文件夹包含：")
    print("    - Markdown 原文（.md）")
    print("    - Word 文档（.docx）")
    if config.get("generation.generate_images"):
        print("    - 配图（.png，封面+内容页+互动引导）")
    print()
    print("  发布时打开对应文件夹，复制正文、上传图片即可。")


if __name__ == "__main__":
    main()
