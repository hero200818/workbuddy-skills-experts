#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
头条号文章自动发布工具
======================
功能：读取本地生成的文章（Markdown/Word + 图片），自动登录并发布到头条号。

使用方法：
  1. 安装依赖：pip install playwright && playwright install chromium
  2. 首次运行：python toutiao_publisher.py --login
     （会打开浏览器，手动登录头条号，登录成功后按回车保存登录态）
  3. 发布文章：python toutiao_publisher.py --folder ./output/围城_20260819/01_方鸿渐/
  4. 批量发布：python toutiao_publisher.py --batch ./output/围城_20260819/

注意：
  - 首次使用必须先运行 --login 保存登录态
  - 发布前请仔细检查文章内容，脚本默认保存为草稿（可加 --publish 直接发布）
  - 头条号页面结构可能变化，如遇错误请更新选择器
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("请先安装依赖：")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)


# ============================================================
# 配置
# ============================================================

TOUTIAO_URL = "https://mp.toutiao.com/"
PUBLISH_URL = "https://mp.toutiao.com/profile_v4/graphic/publish"
COOKIE_FILE = Path(__file__).parent / "toutiao_cookies.json"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)


# ============================================================
# 头条号发布器
# ============================================================

class ToutiaoPublisher:
    """头条号自动发布器"""

    def __init__(self, headless=False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        """启动浏览器"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.page = self.context.new_page()
        print("  浏览器已启动")

    def close(self):
        """关闭浏览器"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("  浏览器已关闭")

    def save_cookies(self):
        """保存登录态（cookies）"""
        cookies = self.context.cookies()
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f"  登录态已保存到：{COOKIE_FILE}")

    def load_cookies(self):
        """加载登录态"""
        if not COOKIE_FILE.exists():
            print("  未找到登录态，请先运行 --login")
            return False
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        self.context.add_cookies(cookies)
        print("  登录态已加载")
        return True

    def login(self):
        """手动登录并保存cookies"""
        print("\n[登录流程]")
        print("  正在打开头条号后台...")
        self.page.goto(TOUTIAO_URL, wait_until="domcontentloaded")
        time.sleep(3)

        print("\n" + "=" * 50)
        print("  请在浏览器中手动登录头条号")
        print("  登录成功后，回到这里按回车键继续...")
        print("=" * 50)
        input()

        # 验证是否登录成功
        self.page.goto(TOUTIAO_URL, wait_until="domcontentloaded")
        time.sleep(2)

        # 检查是否还在登录页
        if "login" in self.page.url.lower():
            print("  登录似乎未成功，请重试")
            return False

        self.save_cookies()
        print("  登录成功！")
        return True

    def check_login(self):
        """检查是否已登录"""
        self.page.goto(TOUTIAO_URL, wait_until="domcontentloaded")
        time.sleep(2)
        if "login" in self.page.url.lower():
            return False
        return True

    def read_article(self, folder_path):
        """读取文章文件夹内容"""
        folder = Path(folder_path)
        if not folder.exists():
            print(f"  文件夹不存在：{folder}")
            return None

        # 查找Markdown文件
        md_files = list(folder.glob("*.md"))
        if not md_files:
            print(f"  未找到Markdown文件：{folder}")
            return None

        md_file = md_files[0]
        content = md_file.read_text(encoding="utf-8")

        # 提取标题
        title = self._extract_title(content)
        body = self._remove_title(content)

        # 查找图片
        images = sorted(folder.glob("*.png"))
        # 第一张作为封面，其余作为内容图
        cover = images[0] if images else None
        content_images = images[1:] if len(images) > 1 else []

        print(f"  文章标题：{title}")
        print(f"  正文字数：{len(body)}字")
        print(f"  封面图：{cover.name if cover else '无'}")
        print(f"  内容配图：{len(content_images)}张")

        return {
            "title": title,
            "body": body,
            "cover": cover,
            "content_images": content_images,
            "folder": folder
        }

    def _extract_title(self, content):
        """从Markdown中提取标题"""
        for line in content.strip().split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return content.split("\n")[0][:50]

    def _remove_title(self, content):
        """移除标题行"""
        lines = content.split("\n")
        if lines and lines[0].strip().startswith("# "):
            return "\n".join(lines[1:]).strip()
        return content

    def publish_article(self, article, publish=False):
        """发布单篇文章"""
        print(f"\n[发布文章] {article['title']}")

        try:
            # 打开发布页面
            print("  打开发布页面...")
            self.page.goto(PUBLISH_URL, wait_until="domcontentloaded")
            time.sleep(3)

            # 如果跳转到登录页，说明登录态失效
            if "login" in self.page.url.lower():
                print("  登录态已失效，请重新运行 --login")
                return False

            # 填写标题
            print("  填写标题...")
            self._fill_title(article["title"])
            time.sleep(1)

            # 填写正文
            print("  填写正文...")
            self._fill_body(article["body"])
            time.sleep(2)

            # 上传封面
            if article["cover"]:
                print("  上传封面...")
                self._upload_cover(article["cover"])
                time.sleep(2)

            # 上传内容配图（在正文中插入）
            if article["content_images"]:
                print(f"  插入 {len(article['content_images'])} 张内容图...")
                self._insert_content_images(article["content_images"])
                time.sleep(2)

            # 截图保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = SCREENSHOT_DIR / f"preview_{timestamp}.png"
            self.page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"  预览截图已保存：{screenshot_path.name}")

            if publish:
                # 直接发布
                print("  点击发布...")
                self._click_publish()
                print("  发布成功！")
            else:
                # 保存草稿
                print("  保存为草稿...")
                self._save_draft()
                print("  已保存为草稿，请登录头条号后台查看和发布")

            return True

        except Exception as e:
            print(f"  发布失败：{e}")
            # 保存错误截图
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_path = SCREENSHOT_DIR / f"error_{timestamp}.png"
            try:
                self.page.screenshot(path=str(error_path), full_page=True)
                print(f"  错误截图已保存：{error_path.name}")
            except:
                pass
            return False

    def _fill_title(self, title):
        """填写标题"""
        # 头条号标题输入框选择器（可能需要根据实际页面调整）
        selectors = [
            'input[placeholder="请输入文章标题"]',
            'input[placeholder*="标题"]',
            '.article-title input',
            'textarea[placeholder*="标题"]',
        ]
        for selector in selectors:
            try:
                elem = self.page.wait_for_selector(selector, timeout=3000)
                if elem:
                    elem.click()
                    elem.fill(title)
                    return
            except:
                continue
        # 兜底：尝试tab定位
        self.page.keyboard.press("Tab")
        self.page.keyboard.type(title)

    def _fill_body(self, body):
        """填写正文"""
        # 头条号正文编辑器通常是富文本编辑器
        # 方法1：找到contenteditable元素
        selectors = [
            '.ProseMirror',
            '[contenteditable="true"]',
            '.editor-content',
            '.article-content',
        ]
        for selector in selectors:
            try:
                elem = self.page.wait_for_selector(selector, timeout=3000)
                if elem:
                    elem.click()
                    # 清空原有内容
                    self.page.keyboard.press("Control+A")
                    self.page.keyboard.press("Backspace")
                    # 逐行输入（模拟人工输入）
                    lines = body.split("\n")
                    for i, line in enumerate(lines):
                        if line.strip():
                            self.page.keyboard.type(line.strip())
                        if i < len(lines) - 1:
                            self.page.keyboard.press("Enter")
                    return
            except:
                continue

        # 兜底：直接用JS设置内容
        self.page.evaluate(f"""
            (function() {{
                const editors = document.querySelectorAll('[contenteditable="true"]');
                if (editors.length > 0) {{
                    editors[0].innerText = {json.dumps(body)};
                }}
            }})()
        """)

    def _upload_cover(self, cover_path):
        """上传封面图"""
        # 头条号封面上传通常是点击上传按钮，然后选择文件
        # 这里使用文件上传input
        try:
            file_input = self.page.query_selector('input[type="file"]')
            if file_input:
                file_input.set_input_files(str(cover_path))
            else:
                # 尝试点击上传按钮
                upload_btns = self.page.query_selector_all('button:has-text("上传"), .upload-btn, [class*="upload"]')
                if upload_btns:
                    upload_btns[0].click()
                    time.sleep(1)
                    file_input = self.page.query_selector('input[type="file"]')
                    if file_input:
                        file_input.set_input_files(str(cover_path))
        except Exception as e:
            print(f"    封面上传遇到问题：{e}")

    def _insert_content_images(self, images):
        """在正文中插入图片"""
        for img_path in images:
            try:
                # 点击图片上传按钮
                img_btns = self.page.query_selector_all('[class*="image"], [title*="图片"], button:has-text("图片")')
                if img_btns:
                    img_btns[0].click()
                    time.sleep(1)
                # 上传文件
                file_inputs = self.page.query_selector_all('input[type="file"]')
                if file_inputs:
                    # 使用最后一个file input（通常是正文图片上传）
                    file_inputs[-1].set_input_files(str(img_path))
                    time.sleep(2)
                # 移动光标到末尾
                self.page.keyboard.press("Control+End")
                self.page.keyboard.press("Enter")
            except Exception as e:
                print(f"    图片 {img_path.name} 插入失败：{e}")

    def _click_publish(self):
        """点击发布按钮"""
        publish_selectors = [
            'button:has-text("发布")',
            '.publish-btn',
            '[class*="publish"] button',
        ]
        for selector in publish_selectors:
            try:
                btn = self.page.wait_for_selector(selector, timeout=3000)
                if btn and btn.is_visible():
                    btn.click()
                    time.sleep(2)
                    # 确认发布
                    confirm_btns = self.page.query_selector_all('button:has-text("确认"), button:has-text("确定")')
                    if confirm_btns:
                        confirm_btns[0].click()
                    return
            except:
                continue

    def _save_draft(self):
        """保存草稿"""
        draft_selectors = [
            'button:has-text("存草稿")',
            'button:has-text("保存草稿")',
            '.draft-btn',
        ]
        for selector in draft_selectors:
            try:
                btn = self.page.wait_for_selector(selector, timeout=3000)
                if btn and btn.is_visible():
                    btn.click()
                    return
            except:
                continue
        # 兜底：使用快捷键
        self.page.keyboard.press("Control+S")

    def read_article_flat(self, md_path):
        """读取扁平结构单篇：.md 与同名 *_N.png 在同一目录（AI 手动产出常用）"""
        md = Path(md_path)
        if not md.exists():
            print(f"  文件不存在：{md}")
            return None
        content = md.read_text(encoding="utf-8")
        title = self._extract_title(content)
        body = self._remove_title(content)
        images = sorted(md.parent.glob(f"{md.stem}_*.png"))
        cover = images[0] if images else None
        content_images = images[1:] if len(images) > 1 else []
        print(f"  文章标题：{title}")
        print(f"  正文字数：{len(body)}字")
        print(f"  封面图：{cover.name if cover else '无'}")
        print(f"  内容配图：{len(content_images)}张")
        return {
            "title": title,
            "body": body,
            "cover": cover,
            "content_images": content_images,
            "folder": md.parent,
        }

    def batch_publish(self, base_folder, publish=False):
        """批量发布（兼容两种目录结构）

        A) 子文件夹模式：base/01_xxx/01_xxx.md + *.png  （generator 自动产出）
        B) 扁平模式：    base/01_xxx.md + base/01_xxx_*.png（AI 手动产出/配图）
        """
        base = Path(base_folder)
        if not base.exists():
            print(f"  目录不存在：{base}")
            return

        # 收集文章来源：数字开头的子目录 或 数字开头的 .md 文件
        sources = []
        for it in sorted(base.iterdir()):
            if it.is_dir() and it.name[:2].isdigit():
                sources.append(("dir", it))
            elif it.is_file() and it.suffix.lower() == ".md" and it.stem[:2].isdigit():
                sources.append(("file", it))

        if not sources:
            print("  未找到文章（支持子文件夹或扁平 .md 结构）")
            return

        print(f"\n找到 {len(sources)} 篇文章")

        success_count = 0
        for i, (kind, path) in enumerate(sources, 1):
            print(f"\n--- 第 {i}/{len(sources)} 篇 ---")
            if kind == "dir":
                article = self.read_article(str(path))
            else:
                article = self.read_article_flat(str(path))
            if article:
                if self.publish_article(article, publish=publish):
                    success_count += 1
            time.sleep(3)  # 避免操作过快

        print(f"\n批量发布完成：成功 {success_count}/{len(sources)} 篇")


# ============================================================
# 主程序
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="头条号文章自动发布工具")
    parser.add_argument("--login", action="store_true", help="登录并保存登录态")
    parser.add_argument("--folder", type=str, help="发布单篇文章（指定文章文件夹路径）")
    parser.add_argument("--batch", type=str, help="批量发布（指定作品根目录）")
    parser.add_argument("--publish", action="store_true", help="直接发布（默认仅保存草稿）")
    parser.add_argument("--headless", action="store_true", help="无头模式（不显示浏览器）")
    args = parser.parse_args()

    print("=" * 60)
    print("  头条号文章自动发布工具")
    print("=" * 60)

    publisher = ToutiaoPublisher(headless=args.headless)

    try:
        publisher.start()

        if args.login:
            # 登录流程
            publisher.login()

        elif args.folder:
            # 单篇发布
            if not publisher.load_cookies():
                print("请先运行 --login 登录")
                return
            if not publisher.check_login():
                print("登录态失效，请重新运行 --login")
                return
            article = publisher.read_article(args.folder)
            if article:
                publisher.publish_article(article, publish=args.publish)

        elif args.batch:
            # 批量发布
            if not publisher.load_cookies():
                print("请先运行 --login 登录")
                return
            if not publisher.check_login():
                print("登录态失效，请重新运行 --login")
                return
            publisher.batch_publish(args.batch, publish=args.publish)

        else:
            parser.print_help()
            print("\n使用示例：")
            print("  1. 首次登录：python toutiao_publisher.py --login")
            print("  2. 发布单篇：python toutiao_publisher.py --folder ./output/围城_20260819/01_方鸿渐/")
            print("  3. 批量发布：python toutiao_publisher.py --batch ./output/围城_20260819/")
            print("  4. 直接发布（非草稿）：加 --publish 参数")

    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        publisher.close()


if __name__ == "__main__":
    main()
