#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md2card-pro 批量处理工具 v1.0
==========================
批量将目录下的 Markdown 文件转换为图片，支持并发处理、进度显示、失败重试、智能标签等。

用法:
    # 基础用法
    python3 batch_md2card_pro.py ./articles/ --style ios

    # 并发处理（4进程）
    python3 batch_md2card_pro.py ./articles/ --style ios --workers 4

    # 指定输出目录 + 递归
    python3 batch_md2card_pro.py ./articles/ --output-dir ./images/ --recursive

    # 跳过已处理 + 失败重试
    python3 batch_md2card_pro.py ./articles/ --skip-existing --retries 2

    # 预览模式（不实际执行）
    python3 batch_md2card_pro.py ./articles/ --dry-run

    # 从文件名自动提取标签
    python3 batch_md2card_pro.py ./articles/ --auto-tag
"""
import os
import sys
import argparse
import subprocess
import re
import json
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime


def find_md2card_pro():
    """查找 md2card_pro.py 的位置"""
    local = Path(__file__).parent / "md2card_pro.py"
    if local.exists():
        return str(local)
    skill_paths = [
        Path.home() / ".super_doubao/super-doubao-runtime/workspace/.user_skills/md2card_pro/md2card_pro.py",
        Path.home() / ".super_doubao/super-doubao-runtime/workspace/skills/md2card_pro/md2card_pro.py",
        Path.home() / ".super_doubao/super-doubao-runtime/workspace/.user_skills/markdown-to-image/md2card_pro.py",
    ]
    for p in skill_paths:
        if p.exists():
            return str(p)
    print("错误：未找到 md2card_pro.py，请确保本脚本与 md2card_pro.py 在同一目录")
    sys.exit(1)


def auto_tag_from_filename(filename):
    """从文件名智能提取标签"""
    name = Path(filename).stem
    # 去除序号前缀
    name = re.sub(r'^\d+[_\-\s]', '', name)
    name = re.sub(r'^第[一二三四五六七八九十百千0-9]+[篇章节回部辑][_\-\s:]?', '', name)
    # 取第一个关键词（分隔符前）
    for sep in ['_', '-', '——', '，', ',', '：', ':']:
        if sep in name:
            tag = name.split(sep)[0].strip()
            if 2 <= len(tag) <= 8:
                return tag
    # 取前6个字
    return name[:6] if len(name) > 6 else name


def find_md_files(input_dir, recursive=False, pattern=None):
    """查找所有 Markdown 文件"""
    if recursive:
        md_files = sorted(input_dir.rglob("*.md"))
    else:
        md_files = sorted(input_dir.glob("*.md"))
    # 排除目录索引和说明文件
    md_files = [
        f for f in md_files
        if not f.name.startswith("00_")
        and "目录" not in f.name
        and "README" not in f.name.upper()
        and "说明" not in f.name
        and "index" not in f.name.lower()
    ]
    # 按模式过滤
    if pattern:
        md_files = [f for f in md_files if re.search(pattern, f.name)]
    return md_files


def process_single_file(args_tuple):
    """处理单个文件（用于多进程）"""
    md_file, out_prefix, md2card_pro, style, tag, engine, author, cover_title, cover_subtitle, retries, timeout, watermark, wm_pos, wm_opacity, wm_size, wm_color, wm_angle, wm_cover = args_tuple

    for attempt in range(1, retries + 1):
        try:
            cmd = [
                sys.executable, md2card_pro,
                str(md_file),
                str(out_prefix) + ".png",
                "--style", style,
                "--tag", tag,
                "--engine", engine,
            ]
            if author:
                cmd.extend(["--author", author])
            if cover_title:
                cmd.extend(["--cover-title", cover_title])
            if cover_subtitle:
                cmd.extend(["--cover-subtitle", cover_subtitle])
            if watermark:
                cmd.extend(["--watermark", watermark])
                cmd.extend(["--watermark-position", wm_pos])
                cmd.extend(["--watermark-opacity", str(wm_opacity)])
                cmd.extend(["--watermark-size", str(wm_size)])
                cmd.extend(["--watermark-color", wm_color])
                cmd.extend(["--watermark-angle", str(wm_angle)])
                if wm_cover:
                    cmd.append("--watermark-cover")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0:
                generated = list(out_prefix.parent.glob(f"{out_prefix.name}_*.png"))
                if not generated:
                    generated = [out_prefix.with_suffix(".png")] if out_prefix.with_suffix(".png").exists() else []
                return {
                    "status": "success",
                    "file": str(md_file),
                    "count": len(generated),
                    "attempt": attempt,
                }
            else:
                error_msg = result.stderr[-300:] if result.stderr else "未知错误"
                if attempt < retries:
                    time.sleep(2)
                    continue
                return {
                    "status": "failed",
                    "file": str(md_file),
                    "error": error_msg,
                    "attempt": attempt,
                }
        except subprocess.TimeoutExpired:
            if attempt < retries:
                time.sleep(2)
                continue
            return {
                "status": "failed",
                "file": str(md_file),
                "error": "处理超时",
                "attempt": attempt,
            }
        except Exception as e:
            if attempt < retries:
                time.sleep(2)
                continue
            return {
                "status": "failed",
                "file": str(md_file),
                "error": str(e),
                "attempt": attempt,
            }
    return {
        "status": "failed",
        "file": str(md_file),
        "error": "重试次数耗尽",
        "attempt": retries,
    }


def print_progress(current, total, filename, status=""):
    """打印进度条"""
    bar_width = 40
    filled = int(bar_width * current / total)
    bar = "█" * filled + "░" * (bar_width - filled)
    percent = current / total * 100
    status_str = f" [{status}]" if status else ""
    print(f"\r  [{bar}] {current}/{total} ({percent:.0f}%){status_str} {filename[:30]:<30}", end="", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="md2card-pro 批量处理工具 v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input_dir", help="包含 Markdown 文件的目录")
    parser.add_argument("--output-dir", default=None, help="输出目录（默认与输入目录相同）")
    parser.add_argument("--style", default="ios",
                        choices=["ios"],
                        help="图片风格：iOS 27 液态玻璃（唯一风格）")
    parser.add_argument("--tag", default="好书推荐", help="封面标签（默认：好书推荐）")
    parser.add_argument("--auto-tag", action="store_true",
                        help="从文件名自动提取标签（覆盖 --tag）")
    parser.add_argument("--author", default=None, help="作者署名")
    parser.add_argument("--cover-title", default=None, help="自定义封面标题")
    parser.add_argument("--cover-subtitle", default=None, help="自定义封面副标题")
    parser.add_argument("--watermark", default="@读书悦己", help="水印文字（默认 @读书悦己，设为 none 可关闭）；自动使用最佳配置（平铺+30度+低透明度）")
    parser.add_argument("--watermark-position", default="tile",
                        choices=["bottom-right", "bottom-left", "top-right", "top-left", "center", "tile"],
                        help="水印位置（默认 tile 平铺，防盗图效果最佳）")
    parser.add_argument("--watermark-opacity", type=float, default=0.15, help="水印透明度（默认 0.15，不影响阅读）")
    parser.add_argument("--watermark-size", type=int, default=32, help="水印字号（默认 32）")
    parser.add_argument("--watermark-color", default="#000000", help="水印颜色（默认黑色）")
    parser.add_argument("--watermark-angle", type=int, default=30, help="水印旋转角度（默认 30 度）")
    parser.add_argument("--watermark-cover", action="store_true", help="给封面也添加水印（默认仅内容页）")
    parser.add_argument("--recursive", action="store_true", help="递归处理子目录")
    parser.add_argument("--engine", default="auto",
                        choices=["auto", "chromium", "wkhtmltoimage"])
    parser.add_argument("--workers", type=int, default=1,
                        help="并发进程数（默认 1，建议 2-4）")
    parser.add_argument("--retries", type=int, default=1,
                        help="失败重试次数（默认 1）")
    parser.add_argument("--timeout", type=int, default=300,
                        help="单文件超时时间（秒，默认 300）")
    parser.add_argument("--skip-existing", action="store_true",
                        help="跳过已存在输出图片的文件")
    parser.add_argument("--pattern", default=None,
                        help="文件名过滤正则表达式")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅显示将处理的文件，不实际执行")
    parser.add_argument("--report", default=None,
                        help="生成处理报告 JSON 文件路径")
    parser.add_argument("--by-folder", action="store_true",
                        help="按文件名创建独立文件夹组织输出")
    parser.add_argument("--include-md", action="store_true",
                        help="在文件夹中包含 Markdown 源文件")
    parser.add_argument("--include-docx", action="store_true",
                        help="在文件夹中包含 Word 文档（需 pandoc）")
    parser.add_argument("--zip-all", default=None,
                        help="处理完成后整体打包为指定 ZIP 文件")

    args = parser.parse_args()

    # 水印开关：--watermark none 可关闭水印
    watermark_enabled = bool(args.watermark) and args.watermark.lower() not in ("none", "no", "off", "false", "0")
    effective_watermark = args.watermark if watermark_enabled else None

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"错误：目录不存在：{input_dir}")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    md2card_pro = find_md2card_pro()
    md_files = find_md_files(input_dir, args.recursive, args.pattern)
    # 保存原始文件列表（用于文件夹组织）
    all_md_files = list(md_files)

    if not md_files:
        print(f"错误：在 {input_dir} 中未找到 .md 文件")
        sys.exit(1)

    # 跳过已处理
    if args.skip_existing:
        before = len(md_files)
        md_files = [
            f for f in md_files
            if not list(output_dir.glob(f"{f.stem}_*.png"))
        ]
        skipped = before - len(md_files)
        if skipped > 0:
            print(f"  跳过 {skipped} 个已处理文件")

    print("\n" + "=" * 60)
    print("  md2card-pro 批量处理 v1.0")
    print("=" * 60)
    print(f"  输入目录：{input_dir}")
    print(f"  输出目录：{output_dir}")
    print(f"  风格：{args.style}")
    if args.auto_tag:
        print(f"  标签：自动从文件名提取")
    else:
        print(f"  标签：{args.tag}")
    print(f"  并发数：{args.workers}")
    print(f"  重试次数：{args.retries}")
    print(f"  找到 {len(md_files)} 个文件")
    print("=" * 60 + "\n")

    if args.dry_run:
        print("[预览模式] 将处理以下文件：\n")
        for i, f in enumerate(md_files, 1):
            tag = auto_tag_from_filename(f.name) if args.auto_tag else args.tag
            print(f"  {i:2d}. {f.relative_to(input_dir)}  →  标签: {tag}")
        print(f"\n  共 {len(md_files)} 个文件")
        return

    # 构造任务列表
    tasks = []
    for md_file in md_files:
        rel_path = md_file.relative_to(input_dir)
        out_prefix = output_dir / rel_path.with_suffix("")
        out_prefix.parent.mkdir(parents=True, exist_ok=True)
        tag = auto_tag_from_filename(md_file.name) if args.auto_tag else args.tag
        tasks.append((
            md_file, out_prefix, md2card_pro, args.style, tag,
            args.engine, args.author, args.cover_title, args.cover_subtitle,
            args.retries, args.timeout,
            effective_watermark, args.watermark_position, args.watermark_opacity,
            args.watermark_size, args.watermark_color, args.watermark_angle, args.watermark_cover,
        ))

    # 执行处理
    start_time = time.time()
    results = []
    success_count = 0
    failed_count = 0
    total_images = 0

    if args.workers > 1:
        # 并发处理
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(process_single_file, task): task[0] for task in tasks}
            for i, future in enumerate(as_completed(futures), 1):
                md_file = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    if result["status"] == "success":
                        success_count += 1
                        total_images += result["count"]
                        print_progress(i, len(tasks), md_file.name, "✓")
                    else:
                        failed_count += 1
                        print_progress(i, len(tasks), md_file.name, "✗")
                except Exception as e:
                    results.append({"status": "failed", "file": str(md_file), "error": str(e)})
                    failed_count += 1
                    print_progress(i, len(tasks), md_file.name, "✗")
    else:
        # 顺序处理
        for i, task in enumerate(tasks, 1):
            result = process_single_file(task)
            results.append(result)
            if result["status"] == "success":
                success_count += 1
                total_images += result["count"]
                print_progress(i, len(tasks), task[0].name, "✓")
            else:
                failed_count += 1
                print_progress(i, len(tasks), task[0].name, "✗")

    elapsed = time.time() - start_time
    print()  # 换行

    # 输出汇总
    print("\n" + "=" * 60)
    print("  批量处理完成！")
    print("=" * 60)
    print(f"  总文件数：{len(tasks)}")
    print(f"  成功：{success_count}")
    print(f"  失败：{failed_count}")
    print(f"  生成图片：{total_images} 张")
    print(f"  耗时：{elapsed:.1f} 秒")
    if len(tasks) > 0:
        print(f"  平均：{elapsed/len(tasks):.1f} 秒/文件")
    print(f"  输出目录：{output_dir}")
    print("=" * 60)

    # 输出失败详情
    if failed_count > 0:
        print("\n  失败文件详情：")
        print("  " + "-" * 56)
        for r in results:
            if r["status"] == "failed":
                fname = Path(r["file"]).name
                error = r.get("error", "未知")[:60]
                print(f"  ✗ {fname}")
                print(f"    原因：{error}")

    # 生成报告
    if args.report:
        report = {
            "timestamp": datetime.now().isoformat(),
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "style": args.style,
            "workers": args.workers,
            "total": len(tasks),
            "success": success_count,
            "failed": failed_count,
            "total_images": total_images,
            "elapsed_seconds": round(elapsed, 1),
            "results": results,
        }
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n  报告已保存：{args.report}")

    # 按文件夹组织输出
    if args.by_folder:
        print("\n" + "=" * 60)
        print("  按文件夹组织输出")
        print("=" * 60)
        organized_dir = output_dir / "_organized"
        organized_dir.mkdir(parents=True, exist_ok=True)
        folder_count = 0
        for md_file in all_md_files:
            stem = md_file.stem
            article_dir = organized_dir / stem
            article_dir.mkdir(parents=True, exist_ok=True)
            # 复制图片
            img_files = list(output_dir.glob(f"{stem}_*.png"))
            for img in img_files:
                import shutil
                shutil.copy2(img, article_dir / img.name)
            # 复制 Markdown 源文件
            if args.include_md:
                shutil.copy2(md_file, article_dir / md_file.name)
            # 生成 Word 文档
            if args.include_docx:
                try:
                    docx_file = article_dir / f"{stem}.docx"
                    subprocess.run(
                        ["pandoc", str(md_file), "-o", str(docx_file)],
                        capture_output=True, timeout=60
                    )
                except Exception:
                    pass
            if img_files or args.include_md or args.include_docx:
                folder_count += 1
        print(f"  已创建 {folder_count} 个独立文件夹")
        print(f"  输出目录：{organized_dir}")
        # 整体打包
        if args.zip_all:
            import shutil as _shutil
            zip_path = Path(args.zip_all)
            if not zip_path.is_absolute():
                zip_path = output_dir / zip_path
            zip_base = str(zip_path.with_suffix(""))
            _shutil.make_archive(zip_base, 'zip', root_dir=organized_dir)
            final_zip = Path(zip_base + ".zip")
            size_mb = final_zip.stat().st_size / (1024 * 1024)
            print(f"  已打包：{final_zip} ({size_mb:.1f} MB)")

    # 退出码
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
