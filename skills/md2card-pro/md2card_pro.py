#!/usr/bin/env python3
"""
Markdown 转图片工具，支持数学公式和笔记本手账风格。
优先使用 Chromium headless 截图，备选 wkhtmltoimage。

用法:
    python3 md2card_pro.py input.md output.png
    python3 md2card_pro.py input.md output.png --style xiaohongshu --tag "育儿书单"
"""

import argparse
import os
import re
import shutil
import subprocess
import sys


# ══════════════════════════════════════════════════════════
# 笔记本手账风格 CSS
# ══════════════════════════════════════════════════════════

XHS_CSS = """
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html { background: #e8f4fd; }
  body {
    font-family: -apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background-color: #e8f4fd;
    background-image:
      linear-gradient(rgba(100, 170, 240, 0.15) 1px, transparent 1px),
      linear-gradient(90deg, rgba(100, 170, 240, 0.15) 1px, transparent 1px);
    background-size: 28px 28px;
    color: #2d2d2d;
    margin: 0 !important;
    max-width: none !important;
    padding: 50px !important;
    line-height: 1.8;
    font-size: 17px;
  }
  .xhs-card {
    background: #5ba4e8;
    border-radius: 36px;
    padding: 22px;
    box-shadow: 0 12px 40px rgba(91, 164, 232, 0.3);
    position: relative;
  }
  .xhs-card-inner {
    background: #ffffff;
    border-radius: 28px;
    padding: 50px 44px;
    position: relative;
  }
  h1 {
    font-size: 30px; font-weight: 800; color: #1a1a1a;
    line-height: 1.5; margin: 0 0 28px; text-align: center;
    letter-spacing: 1px; page-break-after: avoid;
  }
  h2 {
    font-size: 21px; font-weight: 700; color: #1a1a1a;
    margin: 30px 0 16px; padding: 8px 16px;
    background: linear-gradient(90deg, #fff3bf 0%, #ffec99 100%);
    border-radius: 8px; display: inline-block; line-height: 1.5;
    page-break-after: avoid; page-break-inside: avoid;
  }
  h3 {
    font-size: 18px; font-weight: 700; color: #2d2d2d;
    margin: 24px 0 12px; padding-left: 12px;
    border-left: 4px solid #5ba4e8; page-break-after: avoid;
  }
  p {
    margin: 0 0 20px; color: #333; text-align: justify;
    text-indent: 2em; line-height: 2.2; font-size: 17px;
  }
  strong {
    background: linear-gradient(180deg, transparent 58%, #ffe066 58%);
    font-weight: 700; color: #1a1a1a; padding: 0 1px;
  }
  em { color: #e8590c; font-style: normal; font-weight: 600; }
  ul, ol { margin: 12px 0 16px; padding-left: 2em; }
  li { margin: 8px 0; color: #333; line-height: 2.0; font-size: 17px; }
  li > p { text-indent: 0; margin: 4px 0; }
  blockquote {
    background: #f0f7ff; border-left: 4px solid #5ba4e8;
    border-radius: 0 10px 10px 0; padding: 14px 18px;
    margin: 18px 0; color: #495057; font-size: 16px;
    line-height: 1.8; page-break-inside: avoid;
  }
  blockquote p { text-indent: 0; margin: 6px 0; font-size: 16px; color: #495057; }
  code {
    background: #f1f3f5; padding: 2px 8px; border-radius: 6px;
    font-size: 15px; color: #495057;
    font-family: "SF Mono", Consolas, monospace; border: 1px solid #dee2e6;
  }
  pre {
    background: #1e1e1e; border-radius: 12px; padding: 20px;
    margin: 18px 0; overflow-x: auto; page-break-inside: avoid;
  }
  pre code {
    background: none; color: #b5e48c; padding: 0; border: none;
    font-size: 14px; line-height: 1.7;
  }
  table {
    width: 100%; border-collapse: collapse; margin: 18px 0;
    font-size: 15px; border-radius: 10px; overflow: hidden;
    page-break-inside: avoid;
  }
  th { background: #5ba4e8; color: white; padding: 12px 14px; text-align: left; font-weight: 600; }
  td { padding: 12px 14px; border-bottom: 1px solid #e9ecef; color: #333; }
  tr:nth-child(even) td { background: #f8f9fa; }
  a { color: #5ba4e8; text-decoration: none; border-bottom: 2px solid #a5d8ff; }
  hr {
    border: none; height: 2px;
    background: repeating-linear-gradient(90deg, #5ba4e8 0, #5ba4e8 8px, transparent 8px, transparent 16px);
    margin: 28px 0;
  }
  img { max-width: 100%; border-radius: 12px; margin: 16px 0; }
  p, li { orphans: 3; widows: 3; }
  /* 顶部进度条 */
  .ios-progress-bar {
    position: absolute; top: 0; left: 0;
    height: 4px; z-index: 10;
    border-radius: 0 0 4px 0;
  }
  /* 大号章节数字背景 */
  .ios-chapter-num {
    position: absolute; top: 16px; right: 28px;
    font-size: 130px; font-weight: 900;
    color: rgba(0,0,0,0.035); z-index: 1;
    pointer-events: none; line-height: 1;
    font-family: -apple-system, "SF Pro Display", sans-serif;
  }
  /* 首字放大 */
  .ios-content > p:first-of-type::first-letter,
  .ios-content > h2 + p::first-letter {
    float: left; font-size: 3.4em; line-height: 0.82;
    padding: 6px 12px 0 0; font-weight: 900;
  }
  /* 底部装饰线 */
  .ios-bottom-deco {
    position: absolute; bottom: 72px; left: 50%;
    transform: translateX(-50%);
    width: 140px; height: 3px;
    border-radius: 2px; z-index: 5;
  }
  /* 左侧渐变装饰条 */
  .ios-side-bar {
    position: absolute; left: 0; top: 60px; bottom: 80px;
    width: 4px; border-radius: 0 4px 4px 0; z-index: 3;
  }
  /* 继续阅读引导 - 固定在底部装饰线之上 */
  .ios-continue {
    position: absolute; bottom: 88px; left: 50%;
    transform: translateX(-50%);
    text-align: center;
    font-size: 15px; font-weight: 700;
    letter-spacing: 2px; opacity: 0.85; z-index: 5;
    white-space: nowrap;
  }
  .ios-continue-arrow {
    display: inline-block;
  }
  /* 章节标题左侧装饰条 */
  h2 {
    position: relative; padding-left: 24px;
  }
  h2::before {
    content: ''; position: absolute;
    left: 0; top: 50%; transform: translateY(-50%);
    width: 5px; height: 60%; border-radius: 3px;
  }
  /* 列表项装饰 */
  li::marker {
    font-weight: 700;
  }
  /* 引用块增强 */
  blockquote {
    position: relative; padding-left: 24px;
  }
  blockquote::before {
    content: '"'; position: absolute;
    top: -8px; left: 10px;
    font-size: 48px; font-weight: 900;
    opacity: 0.15; line-height: 1;
  }
  /* 最后一页互动引导 */
  .ios-cta {
    margin-top: auto; padding-top: 24px;
    text-align: center; z-index: 5;
  }
  .ios-cta-title {
    font-size: 18px; font-weight: 700;
    margin-bottom: 16px; letter-spacing: 1px;
  }
  .ios-cta-buttons {
    display: flex; justify-content: center; gap: 16px;
    margin-bottom: 14px;
  }
  .ios-cta-btn {
    display: flex; flex-direction: column;
    align-items: center; gap: 4px;
    padding: 10px 20px; border-radius: 16px;
    background: rgba(255,255,255,0.7);
    border: 1.5px solid; font-size: 14px;
    font-weight: 600; min-width: 72px;
  }
  .ios-cta-icon {
    font-size: 24px;
  }
  .ios-cta-share {
    font-size: 15px; font-weight: 600;
    opacity: 0.8; letter-spacing: 1px;
  }
  .ios-cta-large .ios-cta-title { font-size: 22px; margin-bottom: 20px; }
  .ios-cta-large .ios-cta-btn { padding: 14px 28px; font-size: 16px; min-width: 88px; }
  .ios-cta-large .ios-cta-icon { font-size: 30px; }
  .ios-cta-large .ios-cta-share { font-size: 17px; }
  .ios-cta-small .ios-cta-title { font-size: 16px; margin-bottom: 12px; }
  .ios-cta-small .ios-cta-btn { padding: 8px 16px; font-size: 13px; min-width: 64px; gap: 2px; }
  .ios-cta-small .ios-cta-icon { font-size: 20px; }
  .ios-cta-small .ios-cta-share { font-size: 13px; }
</style>
"""

XHS_COVER_CSS = """
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body {
    width: 1080px; height: 1440px; margin: 0; padding: 0; overflow: hidden;
    background-color: #e8f4fd;
    background-image:
      linear-gradient(rgba(100, 170, 240, 0.15) 1px, transparent 1px),
      linear-gradient(90deg, rgba(100, 170, 240, 0.15) 1px, transparent 1px);
    background-size: 28px 28px;
  }
  body {
    font-family: -apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    display: flex; justify-content: center; align-items: center; padding: 50px;
  }
  .cover-card {
    background: #5ba4e8; border-radius: 36px; padding: 22px;
    width: 100%; height: 100%;
    box-shadow: 0 12px 40px rgba(91, 164, 232, 0.3); position: relative;
  }
  .cover-inner {
    background: #ffffff; border-radius: 28px; width: 100%; height: 100%;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    padding: 50px 44px; position: relative;
  }
  .cover-tag {
    background: linear-gradient(180deg, #ffe066 0%, #ffd43b 100%);
    color: #1a1a1a; font-size: 22px; font-weight: 700;
    padding: 10px 28px; border-radius: 10px; margin-bottom: 44px;
    letter-spacing: 4px; box-shadow: 0 4px 12px rgba(255, 212, 59, 0.3);
  }
  .cover-title {
    font-size: 52px; font-weight: 900; color: #1a1a1a;
    line-height: 1.5; text-align: center; letter-spacing: 2px; margin-bottom: 40px;
  }
  .cover-subtitle {
    font-size: 22px; color: #666; line-height: 1.9;
    text-align: center; max-width: 760px; text-indent: 2em;
  }
  .cover-bottom {
    position: absolute; bottom: 44px; font-size: 18px;
    color: #adb5bd; letter-spacing: 4px;
  }
</style>
"""


# ══════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════
# iOS 27 液态玻璃风格 CSS
# ══════════════════════════════════════════════════════════
IOS_CSS = """
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html { background: #f0f0f5; }
  body {
    font-family: -apple-system, "SF Pro Display", "SF Pro Text", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background:
      radial-gradient(ellipse at 20% 20%, rgba(255,255,255,0.3) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 80%, rgba(255,200,180,0.25) 0%, transparent 50%),
      linear-gradient(155deg, #a8b8d8 0%, #b8a8d8 30%, #d8b8d8 60%, #e8c8b8 100%);
    background-attachment: fixed;
    color: #1c1c1e;
    margin: 0 !important;
    max-width: none !important;
    padding: 32px !important;
    line-height: 1.8;
    font-size: 17px;
    -webkit-font-smoothing: antialiased;
  }
  .ios-card {
    background: rgba(255, 255, 255, 0.88);
    backdrop-filter: blur(40px) saturate(220%);
    -webkit-backdrop-filter: blur(40px) saturate(220%);
    border-radius: 30px;
    border: 1px solid rgba(255, 255, 255, 0.95);
    box-shadow:
      0 32px 80px rgba(0, 0, 0, 0.12),
      0 12px 32px rgba(0, 0, 0, 0.08),
      0 4px 12px rgba(0, 0, 0, 0.04),
      inset 0 1.5px 0 rgba(255, 255, 255, 1),
      inset 0 -2px 8px rgba(0, 0, 0, 0.04),
      inset 2px 0 4px rgba(255, 255, 255, 0.3);
    padding: 40px 36px;
    position: relative;
    overflow: hidden;
  }
  .ios-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1.5px;
    background: linear-gradient(90deg, transparent 5%, rgba(255,255,255,0.95) 50%, transparent 95%);
  }
  .ios-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, transparent 40%, transparent 60%, rgba(0,0,0,0.03) 100%);
    pointer-events: none;
    border-radius: 30px;
  }
  h1 {
    font-size: 30px; font-weight: 800; color: #1c1c1e;
    line-height: 1.4; margin: 0 0 28px; text-align: center;
    letter-spacing: -0.5px; page-break-after: avoid;
  }
  h2 {
    font-size: 22px; font-weight: 700; color: #1c1c1e;
    margin: 28px 0 16px; padding: 12px 20px;
    background: linear-gradient(135deg, rgba(0, 122, 255, 0.12) 0%, rgba(88, 86, 214, 0.08) 100%);
    border-radius: 16px; display: inline-block; line-height: 1.4;
    box-shadow: 0 2px 8px rgba(0, 122, 255, 0.1), inset 0 1px 0 rgba(255,255,255,0.8);
    page-break-after: avoid; page-break-inside: avoid;
  }
  h3 {
    font-size: 19px; font-weight: 600; color: #3c3c43;
    margin: 22px 0 12px; padding-left: 14px;
    border-left: 3px solid #007AFF; page-break-after: avoid;
  }
  p {
    margin: 0 0 16px; color: #3c3c43; text-align: justify;
    text-indent: 2em; line-height: 1.85; font-size: 17px;
  }
  strong { color: #007AFF; font-weight: 700; }
  em { color: #ff9500; font-style: normal; font-weight: 600; }
  ul, ol { margin: 12px 0 16px; padding-left: 1.8em; }
  li { margin: 8px 0; color: #3c3c43; line-height: 1.8; font-size: 17px; }
  li > p { text-indent: 0; margin: 4px 0; }
  blockquote {
    background: rgba(0, 122, 255, 0.08);
    border-left: 4px solid #007AFF;
    border-radius: 0 14px 14px 0; padding: 14px 18px;
    margin: 18px 0; color: #3c3c43; font-size: 16px;
    line-height: 1.8; page-break-inside: avoid;
  }
  blockquote p { text-indent: 0; margin: 6px 0; font-size: 16px; color: #3c3c43; }
  code {
    background: rgba(118, 118, 128, 0.12);
    padding: 3px 8px; border-radius: 8px;
    font-size: 15px; color: #af52de;
    font-family: "SF Mono", Consolas, monospace;
  }
  pre {
    background: rgba(28, 28, 30, 0.92);
    border-radius: 16px; padding: 20px;
    margin: 18px 0; overflow-x: auto; page-break-inside: avoid;
  }
  pre code {
    background: none; color: #b5e48c; padding: 0;
    font-size: 14px; line-height: 1.7;
  }
  table {
    width: 100%; border-collapse: collapse; margin: 18px 0;
    font-size: 15px; border-radius: 14px; overflow: hidden;
    page-break-inside: avoid;
    background: rgba(255,255,255,0.5);
  }
  th { background: rgba(0, 122, 255, 0.85); color: white; padding: 12px 14px; text-align: left; font-weight: 600; }
  td { padding: 12px 14px; border-bottom: 1px solid rgba(0,0,0,0.06); color: #3c3c43; }
  tr:nth-child(even) td { background: rgba(255,255,255,0.4); }
  a { color: #007AFF; text-decoration: none; }
  hr {
    border: none; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,0,0,0.15), transparent);
    margin: 28px 0;
  }
  img { max-width: 100%; border-radius: 16px; margin: 16px 0; }
  p, li { orphans: 3; widows: 3; }
  /* 顶部进度条 */
  .ios-progress-bar {
    position: absolute; top: 0; left: 0;
    height: 4px; z-index: 10;
    border-radius: 0 0 4px 0;
  }
  /* 大号章节数字背景 */
  .ios-chapter-num {
    position: absolute; top: 16px; right: 28px;
    font-size: 130px; font-weight: 900;
    color: rgba(0,0,0,0.035); z-index: 1;
    pointer-events: none; line-height: 1;
    font-family: -apple-system, "SF Pro Display", sans-serif;
  }
  /* 首字放大 */
  .ios-content > p:first-of-type::first-letter,
  .ios-content > h2 + p::first-letter {
    float: left; font-size: 3.4em; line-height: 0.82;
    padding: 6px 12px 0 0; font-weight: 900;
  }
  /* 底部装饰线 */
  .ios-bottom-deco {
    position: absolute; bottom: 72px; left: 50%;
    transform: translateX(-50%);
    width: 140px; height: 3px;
    border-radius: 2px; z-index: 5;
  }
  /* 左侧渐变装饰条 */
  .ios-side-bar {
    position: absolute; left: 0; top: 60px; bottom: 80px;
    width: 4px; border-radius: 0 4px 4px 0; z-index: 3;
  }
  /* 继续阅读引导 - 固定在底部装饰线之上 */
  .ios-continue {
    position: absolute; bottom: 88px; left: 50%;
    transform: translateX(-50%);
    text-align: center;
    font-size: 15px; font-weight: 700;
    letter-spacing: 2px; opacity: 0.85; z-index: 5;
    white-space: nowrap;
  }
  .ios-continue-arrow {
    display: inline-block;
  }
  /* 章节标题左侧装饰条 */
  h2 {
    position: relative; padding-left: 24px;
  }
  h2::before {
    content: ''; position: absolute;
    left: 0; top: 50%; transform: translateY(-50%);
    width: 5px; height: 60%; border-radius: 3px;
  }
  /* 列表项装饰 */
  li::marker {
    font-weight: 700;
  }
  /* 引用块增强 */
  blockquote {
    position: relative; padding-left: 24px;
  }
  blockquote::before {
    content: '"'; position: absolute;
    top: -8px; left: 10px;
    font-size: 48px; font-weight: 900;
    opacity: 0.15; line-height: 1;
  }
  /* 最后一页互动引导 */
  .ios-cta {
    margin-top: auto; padding-top: 24px;
    text-align: center; z-index: 5;
  }
  .ios-cta-title {
    font-size: 18px; font-weight: 700;
    margin-bottom: 16px; letter-spacing: 1px;
  }
  .ios-cta-buttons {
    display: flex; justify-content: center; gap: 16px;
    margin-bottom: 14px;
  }
  .ios-cta-btn {
    display: flex; flex-direction: column;
    align-items: center; gap: 4px;
    padding: 10px 20px; border-radius: 16px;
    background: rgba(255,255,255,0.7);
    border: 1.5px solid; font-size: 14px;
    font-weight: 600; min-width: 72px;
  }
  .ios-cta-icon {
    font-size: 24px;
  }
  .ios-cta-share {
    font-size: 15px; font-weight: 600;
    opacity: 0.8; letter-spacing: 1px;
  }
  .ios-cta-large .ios-cta-title { font-size: 22px; margin-bottom: 20px; }
  .ios-cta-large .ios-cta-btn { padding: 14px 28px; font-size: 16px; min-width: 88px; }
  .ios-cta-large .ios-cta-icon { font-size: 30px; }
  .ios-cta-large .ios-cta-share { font-size: 17px; }
  .ios-cta-small .ios-cta-title { font-size: 16px; margin-bottom: 12px; }
  .ios-cta-small .ios-cta-btn { padding: 8px 16px; font-size: 13px; min-width: 64px; gap: 2px; }
  .ios-cta-small .ios-cta-icon { font-size: 20px; }
  .ios-cta-small .ios-cta-share { font-size: 13px; }
</style>
"""

# iOS 每页独立主题配色（16种鲜活靓丽配色，红绿色系不相邻，整体液态玻璃风格不变）
IOS_THEMES = [
    {"primary": "#007AFF", "title": "#0040dd", "h2_bg": "rgba(0,122,255,0.12)", "h2_border": "rgba(0,122,255,0.22)",
     "bg1": "#a8d0ff", "bg2": "#b8c0ff", "bg3": "#d0b8ff", "bg4": "#e0d0ff"},
    {"primary": "#AF52DE", "title": "#6a1b9a", "h2_bg": "rgba(175,82,222,0.12)", "h2_border": "rgba(175,82,222,0.22)",
     "bg1": "#e0b8ff", "bg2": "#f0a8ff", "bg3": "#ffb8f0", "bg4": "#ffd0e8"},
    {"primary": "#FF2D55", "title": "#c2185b", "h2_bg": "rgba(255,45,85,0.10)", "h2_border": "rgba(255,45,85,0.20)",
     "bg1": "#ffb8c8", "bg2": "#ffa8d0", "bg3": "#ffc0e0", "bg4": "#ffd8e8"},
    {"primary": "#FF9500", "title": "#e65100", "h2_bg": "rgba(255,149,0,0.12)", "h2_border": "rgba(255,149,0,0.22)",
     "bg1": "#ffe0a8", "bg2": "#ffd090", "bg3": "#ffecb8", "bg4": "#fff5d0"},
    {"primary": "#5AC8FA", "title": "#0277bd", "h2_bg": "rgba(90,200,250,0.14)", "h2_border": "rgba(90,200,250,0.24)",
     "bg1": "#b0e8ff", "bg2": "#c0f0ff", "bg3": "#d0f4ff", "bg4": "#e0f8ff"},
    {"primary": "#34C759", "title": "#1b5e20", "h2_bg": "rgba(52,199,89,0.12)", "h2_border": "rgba(52,199,89,0.22)",
     "bg1": "#b0f0c0", "bg2": "#c0f8d0", "bg3": "#d0ffd8", "bg4": "#e0ffe8"},
    {"primary": "#A3CB38", "title": "#558b2f", "h2_bg": "rgba(163,203,56,0.14)", "h2_border": "rgba(163,203,56,0.24)",
     "bg1": "#e0f0b0", "bg2": "#e8f5c0", "bg3": "#f0f8d0", "bg4": "#f8fce0"},
    {"primary": "#FFCC00", "title": "#f57f17", "h2_bg": "rgba(255,204,0,0.14)", "h2_border": "rgba(255,204,0,0.24)",
     "bg1": "#fff5b0", "bg2": "#ffed90", "bg3": "#fff8c8", "bg4": "#fffce0"},
    {"primary": "#5856D6", "title": "#283593", "h2_bg": "rgba(88,86,214,0.12)", "h2_border": "rgba(88,86,214,0.22)",
     "bg1": "#c8c8f5", "bg2": "#d8c0f8", "bg3": "#e0d0ff", "bg4": "#ece0ff"},
    {"primary": "#FF3B30", "title": "#b71c1c", "h2_bg": "rgba(255,59,48,0.10)", "h2_border": "rgba(255,59,48,0.20)",
     "bg1": "#ffc0b8", "bg2": "#ffb0a8", "bg3": "#ffd0c8", "bg4": "#ffe0d8"},
    {"primary": "#00BFFF", "title": "#01579b", "h2_bg": "rgba(0,191,255,0.14)", "h2_border": "rgba(0,191,255,0.24)",
     "bg1": "#b0e8ff", "bg2": "#c0eeff", "bg3": "#d0f4ff", "bg4": "#e0f8ff"},
    {"primary": "#00C7BE", "title": "#00695c", "h2_bg": "rgba(0,199,190,0.12)", "h2_border": "rgba(0,199,190,0.22)",
     "bg1": "#a8f0ec", "bg2": "#b8f5f0", "bg3": "#c8f8f4", "bg4": "#d8fffc"},
    {"primary": "#7B68EE", "title": "#4527a0", "h2_bg": "rgba(123,104,238,0.12)", "h2_border": "rgba(123,104,238,0.22)",
     "bg1": "#d0c8ff", "bg2": "#dcc0ff", "bg3": "#e8d8ff", "bg4": "#f0e8ff"},
    {"primary": "#FF6B9D", "title": "#ad1457", "h2_bg": "rgba(255,107,157,0.12)", "h2_border": "rgba(255,107,157,0.22)",
     "bg1": "#ffc8dc", "bg2": "#ffb8d0", "bg3": "#ffd0e4", "bg4": "#ffe0ec"},
    {"primary": "#D980FA", "title": "#6a1b9a", "h2_bg": "rgba(217,128,250,0.12)", "h2_border": "rgba(217,128,250,0.22)",
     "bg1": "#f0d0ff", "bg2": "#f8c0ff", "bg3": "#fcd8ff", "bg4": "#fee8ff"},
    {"primary": "#FF6348", "title": "#bf360c", "h2_bg": "rgba(255,99,72,0.10)", "h2_border": "rgba(255,99,72,0.20)",
     "bg1": "#ffc8b8", "bg2": "#ffb8a8", "bg3": "#ffd0c0", "bg4": "#ffe0d0"},
]

IOS_COVER_CSS = """
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body {
    width: 1080px; height: 1440px; margin: 0; padding: 0; overflow: hidden;
    background:
      radial-gradient(ellipse at 12% 12%, rgba(255,255,255,0.5) 0%, transparent 35%),
      radial-gradient(ellipse at 88% 88%, rgba(100,149,237,0.45) 0%, transparent 40%),
      radial-gradient(ellipse at 50% 30%, rgba(0,102,255,0.2) 0%, transparent 50%),
      radial-gradient(ellipse at 30% 70%, rgba(153,51,255,0.15) 0%, transparent 45%),
      linear-gradient(155deg, #3d8bff 0%, #4d7aff 20%, #6a5cff 45%, #7d4dff 70%, #8c33ff 100%);
    font-family: -apple-system, "SF Pro Display", "PingFang SC", sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  body {
    display: flex; justify-content: center; align-items: center; padding: 36px;
  }
  .ios-cover-card {
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(48px) saturate(240%);
    -webkit-backdrop-filter: blur(48px) saturate(240%);
    border-radius: 40px;
    border: 1.5px solid rgba(255, 255, 255, 0.95);
    box-shadow:
      0 40px 100px rgba(0, 0, 0, 0.16),
      0 16px 40px rgba(0, 0, 0, 0.1),
      0 6px 16px rgba(0, 0, 0, 0.05),
      inset 0 2px 0 rgba(255, 255, 255, 1),
      inset 0 -3px 12px rgba(0, 0, 0, 0.04),
      inset 3px 0 8px rgba(255, 255, 255, 0.3);
    width: 100%; height: 100%;
    display: flex; flex-direction: column;
    justify-content: flex-start; align-items: center;
    padding: 48px 44px 40px;
    position: relative; overflow: hidden;
  }
  .ios-cover-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(145deg, rgba(255,255,255,0.2) 0%, transparent 35%, transparent 65%, rgba(0,0,0,0.03) 100%);
    pointer-events: none;
    border-radius: 40px;
  }
  .ios-cover-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2.5px;
    background: linear-gradient(90deg, transparent 6%, rgba(255,255,255,0.95) 50%, transparent 94%);
  }
  /* 装饰圆形 */
  .ios-cover-deco-circle {
    position: absolute; border-radius: 50%;
    border: 2px dashed; opacity: 0.15; z-index: 0;
  }
  .ios-cover-deco-circle.c1 {
    width: 200px; height: 200px;
    top: -60px; right: -60px;
  }
  .ios-cover-deco-circle.c2 {
    width: 140px; height: 140px;
    bottom: 120px; left: -50px;
  }
  .ios-cover-num {
    position: absolute; top: 32px; right: 40px;
    font-size: 90px; font-weight: 900;
    opacity: 0.1; line-height: 1;
    font-family: -apple-system, "SF Pro Display", sans-serif;
    z-index: 1;
  }
  /* 热门徽章 */
  .ios-cover-hot {
    color: white; font-size: 16px; font-weight: 800;
    padding: 6px 18px; border-radius: 100px;
    letter-spacing: 1px; margin-bottom: 16px;
    z-index: 2;
  }
  .ios-cover-top {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 24px; z-index: 2;
  }
  .ios-cover-top-line {
    width: 44px; height: 1.5px;
  }
  .ios-cover-top-label {
    font-size: 14px; font-weight: 700;
    letter-spacing: 5px; text-transform: uppercase;
  }
  .ios-cover-tag-row {
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 28px; z-index: 2;
  }
  .ios-cover-tag {
    color: white; font-size: 24px; font-weight: 800;
    padding: 12px 36px; border-radius: 100px;
    letter-spacing: 2px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.3);
  }
  .ios-cover-badge {
    color: white; font-size: 14px; font-weight: 800;
    padding: 6px 16px; border-radius: 100px;
    letter-spacing: 1px;
  }
  .ios-cover-short-title {
    font-size: 82px; font-weight: 900;
    line-height: 1.25; text-align: center;
    letter-spacing: 2px; margin-bottom: 16px;
    z-index: 2; max-width: 960px;
  }
  .ios-cover-title {
    font-size: 38px; font-weight: 700;
    line-height: 1.5; text-align: center;
    letter-spacing: 0.5px; margin-bottom: 28px;
    z-index: 2; max-width: 920px;
    color: #3c3c43;
  }
  .ios-cover-intro {
    font-size: 20px; color: #48484a; line-height: 1.9;
    text-align: center; max-width: 840px;
    padding: 20px 28px; margin-bottom: 28px;
    border-radius: 18px; z-index: 2;
    border-left: 4px solid;
    border-right: 4px solid;
  }
  .ios-cover-keywords {
    display: flex; gap: 10px; flex-wrap: wrap;
    justify-content: center; margin-bottom: 28px;
    z-index: 2;
  }
  .ios-cover-kw {
    font-size: 17px; font-weight: 700;
    padding: 8px 22px; border-radius: 100px;
    border: 1.5px solid;
  }
  .ios-cover-meta-card {
    display: flex; align-items: center;
    background: rgba(255,255,255,0.7);
    border-radius: 22px; padding: 20px 40px;
    margin-bottom: 20px; z-index: 2;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    border: 1px solid rgba(255,255,255,0.9);
  }
  .ios-cover-meta-item {
    display: flex; flex-direction: column;
    align-items: center; padding: 0 28px;
  }
  .ios-cover-meta-num {
    font-size: 30px; font-weight: 900;
    line-height: 1.2;
  }
  .ios-cover-meta-label {
    font-size: 13px; color: #8e8e93;
    margin-top: 3px; letter-spacing: 1px;
  }
  .ios-cover-meta-divider {
    width: 1px; height: 40px;
    background: rgba(0,0,0,0.1);
  }
  .ios-cover-guide {
    font-size: 17px; font-weight: 700;
    letter-spacing: 3px; margin-bottom: auto;
    z-index: 2;
  }
  .ios-cover-bottom-line {
    width: 100px; height: 2.5px;
    border-radius: 2px; margin-bottom: 14px;
    z-index: 2;
  }
  .ios-cover-author {
    font-size: 16px; font-weight: 600;
    color: #636366; letter-spacing: 1px;
    margin-bottom: 12px; z-index: 2;
    padding: 6px 20px; border-radius: 100px;
    background: rgba(255,255,255,0.6);
    border: 1px solid rgba(0,0,0,0.05);
  }
  .ios-cover-bottom {
    display: flex; align-items: center; gap: 10px;
    font-size: 17px; color: rgba(60, 60, 67, 0.5);
    letter-spacing: 4px; font-weight: 600;
    z-index: 2;
  }
  .ios-cover-arrow {
    font-size: 18px;
  }
</style>
"""

# 工具查找
# ══════════════════════════════════════════════════════════

def find_chromium():
    for name in ["chromium-browser", "chromium", "google-chrome", "chrome", "google-chrome-stable", "msedge"]:
        path = shutil.which(name)
        if path:
            return path
    for p in ["/usr/bin/chromium-browser", "/usr/bin/chromium", "/usr/bin/google-chrome"]:
        if os.path.isfile(p):
            return p
    # Windows paths
    for p in [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]:
        if os.path.isfile(p):
            return p
    return None


def find_wkhtmltoimage():
    env_path = os.environ.get("WKHTMLTOIMAGE")
    if env_path and os.path.isfile(env_path):
        return env_path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(script_dir, "bin", "wkhtmltoimage")
    if os.path.isfile(local_path):
        return local_path
    in_path = shutil.which("wkhtmltoimage")
    if in_path:
        return in_path
    for p in ["/usr/bin/wkhtmltoimage", "/usr/local/bin/wkhtmltoimage"]:
        if os.path.isfile(p):
            return p
    return None


def check_dependencies(engine):
    missing = []
    if not shutil.which("pandoc"):
        missing.append("pandoc (sudo apt install pandoc)")
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        missing.append("Pillow (pip install Pillow)")
    if engine in ("chromium", "auto") and not find_chromium():
        if engine == "chromium":
            missing.append("chromium (sudo apt install chromium-browser)")
    if engine in ("wkhtmltoimage", "auto") and not find_wkhtmltoimage():
        if engine == "wkhtmltoimage":
            missing.append("wkhtmltoimage (sudo apt install wkhtmltopdf)")
        try:
            import imgkit  # noqa: F401
        except ImportError:
            if engine == "wkhtmltoimage":
                missing.append("imgkit (pip install imgkit)")
    if engine == "auto" and not find_chromium() and not find_wkhtmltoimage():
        missing.append("截图引擎：安装 chromium-browser 或 wkhtmltopdf 任一即可")
    if missing:
        print("缺少以下依赖，请先安装：", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        sys.exit(1)


# ══════════════════════════════════════════════════════════
# Markdown → HTML
# ══════════════════════════════════════════════════════════

def markdown_to_html(md_file, html_file, engine="chromium", style="default"):
    import subprocess
    if engine == "wkhtmltoimage":
        extra_args = ["--mathml", "--standalone", "--embed-resources"]
    else:
        extra_args = ["--mathjax", "--standalone", "--embed-resources"]
    result = subprocess.run(
        ["pandoc", md_file, "-f", "markdown", "-t", "html"] + extra_args,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"pandoc 转换失败: {result.stderr}")
    html_content = result.stdout
    if style == "xiaohongshu":
        body_match = re.search(r"(<body[^>]*>)(.*?)(</body>)", html_content, re.DOTALL)
        if body_match:
            body_content = body_match.group(2)
            wrapped = (f'{body_match.group(1)}'
                       f'<div class="xhs-card">'
                       f'<div class="xhs-card-inner">{body_content}</div>'
                       f'</div>{body_match.group(3)}')
            html_content = html_content[:body_match.start()] + wrapped + html_content[body_match.end():]
        html_content = html_content.replace("</head>", XHS_CSS + "</head>")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    return html_file


def extract_title_and_intro(md_file):
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()
    title = "读书笔记"
    intro = ""
    lines = content.split("\n")
    for line in lines:
        m = re.match(r"^#{1,2}\s+(.+)", line)
        if m:
            title = m.group(1).strip()
            break
    found_title = False
    paragraphs = []
    for line in lines:
        if re.match(r"^#{1,2}\s+", line):
            found_title = True
            continue
        if found_title and line.strip() and not line.startswith("#"):
            paragraphs.append(line.strip())
            if len("".join(paragraphs)) > 100:
                break
    if paragraphs:
        intro = "".join(paragraphs)[:80]
        if len("".join(paragraphs)) > 80:
            intro += "..."
    return title, intro


def generate_cover_html(md_file, cover_html_file, tag="好书推荐"):
    title, intro = extract_title_and_intro(md_file)
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">{XHS_COVER_CSS}</head>
<body>
  <div class="cover-card">
    <div class="cover-inner">
      <div class="cover-tag">{tag}</div>
      <div class="cover-title">{title}</div>
      {"<div class='cover-subtitle'>" + intro + "</div>" if intro else ""}
      <div class="cover-bottom">✦ 滑动查看全文 ✦</div>
    </div>
  </div>
</body></html>"""
    with open(cover_html_file, "w", encoding="utf-8") as f:
        f.write(html)
    return cover_html_file


def generate_short_title(title):
    """从原标题智能生成精炼短标题，6-14字，吸引眼球"""
    import re
    # 预处理：去除序号前缀（第一篇：/ 第1章：/ 01_ 等）
    short = re.sub(r'^第[一二三四五六七八九十百千0-9]+[篇章节回部辑]_?[:：]?', '', title).strip()
    short = re.sub(r'^[0-9]+[_-]', '', short).strip()
    # 去除人名+冒号前缀（钱弘俶：/ 张三：等）
    if '：' in short and len(short.split('：')[0]) <= 6:
        parts = short.split('：', 1)
        if len(parts) > 1:
            short = parts[1].strip()
    # 策略1：提取"不是...是..."中的核心结论
    if '不是' in short and '，是' in short:
        s = short.split('，是')[-1].strip('，。！？、：: ')
        if 4 <= len(s) <= 14:
            return s
    if '不是' in short and '是' in short:
        parts = short.split('是')
        if len(parts) >= 2:
            s = parts[-1].strip('，。！？、：: ')
            if 4 <= len(s) <= 14:
                return s
    # 策略2：问号后取回答/结论
    if '？' in short:
        after_q = short.split('？')[-1].strip('，。！？、：: ')
        if 4 <= len(after_q) <= 14:
            return after_q
    # 策略3：去除疑问词前缀，取逗号前核心
    prefixes = ['为什么', '怎么', '如何', '怎样', '到底', '究竟', '原来', '其实', '揭秘']
    for p in prefixes:
        if short.startswith(p):
            short = short[len(p):]
            break
    if '，' in short:
        short = short.split('，')[0]
    short = short.strip('？?，,。.！!、：: ')
    # 去除首尾引号
    short = short.strip('"\'')
    if len(short) > 14:
        short = short[:14]
    if len(short) < 4:
        short = title[-10:]
    return short


def generate_ios_cover_html(md_file, cover_html_file, tag="iOS 笔记", author=None, custom_title=None, custom_subtitle=None):
    title, intro = extract_title_and_intro(md_file)
    short_title = generate_short_title(title)
    # 支持自定义标题和副标题
    if custom_title:
        title = custom_title
    if custom_subtitle:
        intro = custom_subtitle
    # 封面固定使用鲜亮宝蓝色主题
    theme = {
        "primary": "#0066FF", "title": "#0033CC",
        "h2_bg": "rgba(0,102,255,0.12)", "h2_border": "rgba(0,102,255,0.25)",
    }
    # 计算字数和阅读时间
    try:
        with open(md_file, "r", encoding="utf-8") as f:
            md_text = f.read()
        char_count = len(re.sub(r"[#*\-\[\]()>`]", "", md_text).strip())
        read_min = max(1, char_count // 400)
        # 统计章节数（## 开头的行）
        section_count = len([l for l in md_text.split("\n") if l.startswith("## ")])
        if section_count == 0:
            section_count = max(1, char_count // 500)
    except Exception:
        char_count = 0
        read_min = 3
        section_count = 5

    # 转义 HTML 特殊字符
    import html as html_mod
    title_esc = html_mod.escape(title)
    short_title_esc = html_mod.escape(short_title)
    intro_esc = html_mod.escape(intro[:120] + ("..." if len(intro) > 120 else ""))
    tag_esc = html_mod.escape(tag)

    # 关键词（从标题提取）
    keywords = []
    for kw in ["深度解读", "历史真相", "人物故事", "干货满满", "历史科普", "独家视角"]:
        if len(keywords) < 4:
            keywords.append(kw)

    # 作者署名 HTML
    author_html = f'<div class="ios-cover-author">✍️ {html_mod.escape(author)}</div>' if author else ''

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
{IOS_COVER_CSS}
</head>
<body>
  <div class="ios-cover-card">
    <!-- 装饰圆形 -->
    <div class="ios-cover-deco-circle c1" style="border-color: {theme['primary']};"></div>
    <div class="ios-cover-deco-circle c2" style="border-color: {theme['primary']};"></div>

    <!-- 热门徽章 -->
    <div class="ios-cover-hot" style="background: linear-gradient(135deg, #FF3B30, #FF6B6B);">🔥 爆款长文</div>

    <!-- 顶部标签 -->
    <div class="ios-cover-top">
      <div class="ios-cover-top-line" style="background: {theme['primary']};"></div>
      <div class="ios-cover-top-label" style="color: {theme['primary']};">深度长文</div>
      <div class="ios-cover-top-line" style="background: {theme['primary']};"></div>
    </div>

    <!-- 标签行 -->
    <div class="ios-cover-tag-row">
      <div class="ios-cover-tag" style="background: linear-gradient(135deg, {theme['primary']}, #0044CC);">{tag_esc}</div>
      <div class="ios-cover-badge" style="background: linear-gradient(135deg, #FF9500, #FF6B00);">精选</div>
    </div>

    <!-- 短标题 -->
    <div class="ios-cover-short-title" style="background: linear-gradient(135deg, {theme['primary']}, #0033CC, #5856D6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">{short_title_esc}</div>

    <!-- 原标题 -->
    <div class="ios-cover-title">{title_esc}</div>

    <!-- 引言框 -->
    <div class="ios-cover-intro" style="background: rgba(0,102,255,0.08); border-left-color: {theme['primary']}; border-right-color: {theme['primary']};">{intro_esc}</div>

    <!-- 关键词 -->
    <div class="ios-cover-keywords">
      {"".join(f'<span class="ios-cover-kw" style="color: {theme["primary"]}; border-color: rgba(0,102,255,0.3); background: rgba(0,102,255,0.06);">{kw}</span>' for kw in keywords)}
    </div>

    <!-- 元信息卡片 -->
    <div class="ios-cover-meta-card">
      <div class="ios-cover-meta-item">
        <div class="ios-cover-meta-num" style="color: {theme['primary']};">{char_count}</div>
        <div class="ios-cover-meta-label">字</div>
      </div>
      <div class="ios-cover-meta-divider"></div>
      <div class="ios-cover-meta-item">
        <div class="ios-cover-meta-num" style="color: {theme['primary']};">{read_min}</div>
        <div class="ios-cover-meta-label">分钟阅读</div>
      </div>
      <div class="ios-cover-meta-divider"></div>
      <div class="ios-cover-meta-item">
        <div class="ios-cover-meta-num" style="color: {theme['primary']};">{section_count}</div>
        <div class="ios-cover-meta-label">章节</div>
      </div>
    </div>

    <!-- 引导文案 -->
    <div class="ios-cover-guide" style="color: {theme['primary']};">✦ 干货满满 · 建议收藏 ✦</div>

    {author_html}

    <!-- 底部 -->
    <div class="ios-cover-bottom-line" style="background: linear-gradient(90deg, transparent, {theme['primary']}, transparent);"></div>
    <div class="ios-cover-bottom">
      <span class="ios-cover-arrow">↓</span>
      <span>滑动查看全文</span>
      <span class="ios-cover-arrow">↓</span>
    </div>
  </div>
</body>
</html>"""

    with open(cover_html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    return cover_html_file


def _is_background_pixel(r, g, b):
    if r >= 225 and g >= 235 and b >= 245:
        return True
    if r >= 250 and g >= 250 and b >= 250:
        return True
    return False


def _draw_notebook_rings(img):
    """在图片左侧绘制活页圆环（分页后统一绘制，确保位置一致）。"""
    from PIL import Image, ImageDraw, ImageFilter
    w, h = img.size
    draw = ImageDraw.Draw(img)
    ring_w, ring_h = 48, 18
    x = 28
    positions = [int(h * 0.18), int(h * 0.39), int(h * 0.61), int(h * 0.82)]
    for cy in positions:
        shadow = Image.new('RGBA', (ring_w + 8, ring_h + 8), (0,0,0,0))
        sd = ImageDraw.Draw(shadow)
        sd.ellipse([4, 5, ring_w + 4, ring_h + 5], fill=(0,0,0,40))
        shadow = shadow.filter(ImageFilter.GaussianBlur(2))
        img.paste(shadow, (x - 2, cy - ring_h//2 - 1), shadow)
        for i in range(ring_h):
            t = i / ring_h
            r = int(255 - 20 * t)
            g = int(224 - 50 * t)
            b = int(102 - 50 * t)
            draw.ellipse([x, cy - ring_h//2 + i, x + ring_w, cy - ring_h//2 + i + 1], fill=(r, g, b))
        draw.ellipse([x, cy - ring_h//2, x + ring_w, cy + ring_h//2], outline=(232, 162, 0), width=2)
        hole_x = x + ring_w - 4
        hole_r = 6
        draw.ellipse([hole_x - hole_r, cy - hole_r, hole_x + hole_r, cy + hole_r],
                    fill=(91, 164, 232), outline=(74, 144, 217), width=2)
    return img


def _add_page_number(img, page_num):
    from PIL import ImageDraw, ImageFont
    w, h = img.size
    draw = ImageDraw.Draw(img)
    font = None
    for font_path in [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, 24)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()
    text = f"— {page_num} —"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (w - tw) // 2
    y = h - 52
    pad_x, pad_y = 18, 7
    draw.rounded_rectangle(
        [x - pad_x, y - pad_y, x + tw + pad_x, y + th + pad_y],
        radius=14, fill=(255, 255, 255)
    )
    draw.text((x, y), text, fill=(140, 140, 140), font=font)
    return img


def _add_ios_page_indicator(img, page_num, total_pages, primary_color="#007AFF"):
    """iOS 风格页面指示器：精致毛玻璃胶囊 + 主题色边框 + 左右圆点装饰。"""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    w, h = img.size
    # 解析主题色
    pr = int(primary_color[1:3], 16)
    pg = int(primary_color[3:5], 16)
    pb = int(primary_color[5:7], 16)
    
    # 胶囊尺寸和位置（装饰线在 bottom:72px，页码在其下方）
    capsule_w = 180
    capsule_h = 42
    cx = (w - capsule_w) // 2
    cy = h - 52
    
    # 创建半透明层绘制阴影和背景
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    
    # 胶囊阴影
    shadow_layer = Image.new('RGBA', (capsule_w + 20, capsule_h + 12), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_layer)
    sd.rounded_rectangle([10, 6, capsule_w + 10, capsule_h + 6],
                         radius=capsule_h // 2, fill=(0, 0, 0, 35))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(6))
    overlay.paste(shadow_layer, (cx - 10, cy - 6), shadow_layer)
    
    # 毛玻璃胶囊背景（白色半透明）
    od.rounded_rectangle([cx, cy, cx + capsule_w, cy + capsule_h],
                         radius=capsule_h // 2, fill=(255, 255, 255, 210))
    # 主题色细边框
    od.rounded_rectangle([cx, cy, cx + capsule_w, cy + capsule_h],
                         radius=capsule_h // 2, outline=(pr, pg, pb, 120), width=1)
    # 顶部高光
    od.rounded_rectangle([cx + 2, cy + 1, cx + capsule_w - 2, cy + capsule_h // 2],
                         radius=capsule_h // 2 - 1, fill=(255, 255, 255, 60))
    
    # 左侧圆点（实心主题色）
    dot_r = 4
    dot_cx = cx + 28
    dot_cy = cy + capsule_h // 2
    od.ellipse([dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r],
               fill=(pr, pg, pb, 230))
    
    # 右侧圆点（半透明主题色）
    dot_cx2 = cx + capsule_w - 28
    od.ellipse([dot_cx2 - dot_r, dot_cy - dot_r, dot_cx2 + dot_r, dot_cy + dot_r],
               fill=(pr, pg, pb, 100))
    
    # 页码文字
    font = None
    for fp in ["/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
               "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 17)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()
    
    text = f"{page_num} / {total_pages}"
    bbox = od.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = cx + (capsule_w - tw) // 2
    ty = cy + (capsule_h - th) // 2 - 2
    od.text((tx, ty), text, fill=(pr, pg, pb, 240), font=font)
    
    # 合并到原图
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    img = img.convert('RGB')
    return img

def _fix_cover_bottom(image_file, target_height=1440):
    """修复封面底部白边并绘制活页环。"""
    try:
        from PIL import Image
        img = Image.open(image_file)
        if img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        if h > target_height:
            img = img.crop((0, 0, w, target_height))
        elif h < target_height:
            from PIL import Image as PILImage
            bg = PILImage.new("RGB", (w, target_height), (232, 244, 253))
            bg.paste(img, (0, 0))
            img = bg
        img = _draw_notebook_rings(img)
        img.save(image_file)
    except Exception:
        pass

        pass
def _trim_bottom_whitespace(image_file):
    try:
        from PIL import Image
        img = Image.open(image_file)
        if img.mode != "RGB":
            img = img.convert("RGB")
        width, height = img.size
        pixels = img.load()
        bottom = height
        for y in range(height - 1, -1, -1):
            row_is_bg = True
            for x in range(0, width, max(1, width // 80)):
                r, g, b = pixels[x, y]
                if not _is_background_pixel(r, g, b):
                    row_is_bg = False
                    break
            if not row_is_bg:
                bottom = y + 1
                break
        if bottom < height:
            bottom = min(height, bottom + 50)
            img.crop((0, 0, width, bottom)).save(image_file)
    except Exception:
        pass


def _add_watermark(image_file, watermark_text, position="bottom-right", opacity=0.3, size=36, color="#000000", angle=0):
    """给图片添加文字水印"""
    from PIL import Image, ImageDraw, ImageFont
    import math

    img = Image.open(image_file).convert("RGBA")
    w, h = img.size

    # 创建透明图层
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 尝试加载中文字体
    font = None
    font_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for fp in font_paths:
        if os.path.isfile(fp):
            try:
                font = ImageFont.truetype(fp, size)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()

    # 计算文字尺寸
    try:
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except Exception:
        text_w = len(watermark_text) * size
        text_h = size

    # 解析颜色
    if color.startswith("#"):
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
    else:
        r, g, b = 0, 0, 0
    alpha = int(255 * opacity)

    if position == "tile":
        # 平铺模式
        spacing_x = max(text_w + 80, 200)
        spacing_y = max(text_h + 60, 150)
        for y in range(0, h + spacing_y, spacing_y):
            for x in range(0, w + spacing_x, spacing_x):
                # 创建单独的文字图层用于旋转
                text_layer = Image.new("RGBA", (text_w + 20, text_h + 20), (0, 0, 0, 0))
                text_draw = ImageDraw.Draw(text_layer)
                text_draw.text((10, 10), watermark_text, font=font, fill=(r, g, b, alpha))
                if angle != 0:
                    text_layer = text_layer.rotate(angle, expand=True, resample=Image.BICUBIC)
                overlay.paste(text_layer, (x, y), text_layer)
    else:
        # 单个水印位置
        margin = 40
        if position == "bottom-right":
            x = w - text_w - margin
            y = h - text_h - margin
        elif position == "bottom-left":
            x = margin
            y = h - text_h - margin
        elif position == "top-right":
            x = w - text_w - margin
            y = margin
        elif position == "top-left":
            x = margin
            y = margin
        elif position == "center":
            x = (w - text_w) // 2
            y = (h - text_h) // 2
        else:
            x = w - text_w - margin
            y = h - text_h - margin

        if angle != 0:
            # 旋转模式
            text_layer = Image.new("RGBA", (text_w + 40, text_h + 40), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_layer)
            text_draw.text((20, 20), watermark_text, font=font, fill=(r, g, b, alpha))
            text_layer = text_layer.rotate(angle, expand=True, resample=Image.BICUBIC)
            tw, th = text_layer.size
            overlay.paste(text_layer, (x - (tw - text_w) // 2, y - (th - text_h) // 2), text_layer)
        else:
            draw.text((x, y), watermark_text, font=font, fill=(r, g, b, alpha))

    # 合并图层
    result = Image.alpha_composite(img, overlay)
    result = result.convert("RGB")
    result.save(image_file, quality=95)
    return image_file


def _zip_output_files(image_files, md_file=None, include_md=False, include_docx=False, zip_path=None):
    """将生成的图片打包为 ZIP 文件，可选包含 markdown 和 word 文档"""
    import zipfile
    import shutil
    import subprocess
    from pathlib import Path

    if not image_files:
        return None

    # 确定 zip 文件路径
    if zip_path is None:
        first_img = Path(image_files[0])
        base_name = first_img.stem
        # 去除末尾的 _1, _2 等序号
        import re
        base_name = re.sub(r'_\d+$', '', base_name)
        zip_path = first_img.parent / f"{base_name}.zip"
    else:
        zip_path = Path(zip_path)

    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 添加图片
        for img in image_files:
            img_path = Path(img)
            if img_path.exists():
                zf.write(img_path, img_path.name)

        # 添加 markdown 源文件
        if include_md and md_file:
            md_path = Path(md_file)
            if md_path.exists():
                zf.write(md_path, md_path.name)

        # 添加 word 文档
        if include_docx and md_file:
            md_path = Path(md_file)
            if md_path.exists():
                docx_path = md_path.with_suffix('.docx')
                try:
                    subprocess.run(
                        ["pandoc", str(md_path), "-o", str(docx_path)],
                        capture_output=True, timeout=60
                    )
                    if docx_path.exists():
                        zf.write(docx_path, docx_path.name)
                        try:
                            docx_path.unlink()
                        except OSError:
                            pass
                except Exception:
                    pass

    return str(zip_path)



def _is_page_blank(page, threshold=0.008):
    w, h = page.size
    pixels = page.load()
    non_bg = 0
    total = 0
    for y in range(0, h, 8):
        for x in range(0, w, 8):
            r, g, b = pixels[x, y]
            if not _is_background_pixel(r, g, b):
                non_bg += 1
            total += 1
    return total > 0 and (non_bg / total) < threshold


# ══════════════════════════════════════════════════════════
# HTML → 图片
# ══════════════════════════════════════════════════════════

def html_to_image(html_file, image_file, engine="chromium"):
    """将 HTML 转换为图片，根据引擎选择不同的实现"""
    if engine == "chromium":
        html_to_image_chromium(html_file, image_file)
    elif engine == "wkhtmltoimage":
        wkhtml_path = find_wkhtmltoimage()
        if not wkhtml_path:
            raise RuntimeError("未找到 wkhtmltoimage")
        import imgkit
        config = imgkit.config(wkhtmltoimage=wkhtml_path)
        imgkit.from_file(html_file, image_file, config=config, options={
            'width': 1080, 'quality': 95, 'enable-local-file-access': None
        })
    else:
        raise ValueError(f"不支持的引擎: {engine}")


def html_to_image_chromium(html_file, image_file, width=1080, height=15000, scale=1):
    chromium = find_chromium()
    abs_html = os.path.abspath(html_file)
    abs_img = os.path.abspath(image_file)
    cmd = [
        chromium, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars",
        f"--force-device-scale-factor={scale}",
        f"--window-size={width},{height}",
        "--virtual-time-budget=3000",
        f"--screenshot={abs_img}",
        f"file://{abs_html}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        cmd[1] = "--headless"
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"Chromium 截图失败: {result.stderr}")
    if not os.path.isfile(image_file):
        raise RuntimeError("Chromium 截图失败：未生成输出文件")


def parse_markdown_blocks(md_text):
    """解析 Markdown 为块结构，用于智能分页"""
    import re
    blocks = []
    # 按空行分割
    raw_blocks = re.split(r'\n\s*\n', md_text)
    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith("# "):
            blocks.append(("h1", block))
        elif block.startswith("## "):
            blocks.append(("h2", block))
        elif block.startswith("### "):
            blocks.append(("h3", block))
        elif block.startswith("```"):
            blocks.append(("code", block))
        elif block.startswith("> "):
            blocks.append(("quote", block))
        elif block.startswith("|"):
            blocks.append(("table", block))
        elif block.startswith("---") or block.startswith("***") or block.startswith("___"):
            blocks.append(("hr", block))
        elif re.match(r"^[-*]\s", block, re.MULTILINE) or re.match(r"^\d+\.\s", block, re.MULTILINE):
            blocks.append(("list", block))
        else:
            blocks.append(("p", block))
    return blocks


def _char_width(text):
    """估算文本的等效字符宽度（中文=2，英文/数字=1）。"""
    w = 0
    for c in text:
        if "\u4e00" <= c <= "\u9fff" or "\u3000" <= c <= "\u303f" or "\uff00" <= c <= "\uffef":
            w += 2
        else:
            w += 1
    return w


def estimate_block_height(block_type, block_content, content_width=860):
    """估算块的像素高度。content_width 为白色内页内容区宽度。"""
    chars_per_line = content_width // 16  # 16px 等效中文字宽

    def text_lines(text):
        w = _char_width(text)
        return max(1, (w + chars_per_line - 1) // chars_per_line)

    if block_type == "h1":
        return 60
    elif block_type == "h2":
        return 48
    elif block_type == "h3":
        return 40
    elif block_type == "code":
        lines = block_content.count("\n") + 1
        return min(lines * 24 + 36, 500)
    elif block_type == "quote":
        text = re.sub(r"^>\s?", "", block_content, flags=re.MULTILINE)
        return text_lines(text) * 28 + 28
    elif block_type == "list":
        lines = 0
        for item in re.split(r"\n(?=[-*]|\d+\.)", block_content):
            lines += text_lines(item)
        return lines * 35 + 14
    elif block_type == "table":
        rows = block_content.count("\n") + 1
        return rows * 38 + 18
    elif block_type == "hr":
        return 36
    else:  # p
        return text_lines(block_content) * 35 + 14


def paginate_blocks(blocks, max_height=1180):
    """智能均匀分页：先估算总页数，再按目标高度均匀分配内容。"""
    # 跳过第一个 h1
    skipped_h1 = False
    valid_blocks = []
    for bt, bc in blocks:
        if bt == "h1" and not skipped_h1:
            skipped_h1 = True
            continue
        valid_blocks.append((bt, bc))

    if not valid_blocks:
        return []

    # 计算每个块的高度和总高度
    heights = [estimate_block_height(bt, bc) for bt, bc in valid_blocks]
    total_h = sum(heights)

    # 估算需要的页数
    num_pages = max(1, (total_h + max_height - 1) // max_height)
    target_h = total_h / num_pages

    # 按目标高度均匀分配
    pages = []
    current_page = []
    current_h = 0
    i = 0
    while i < len(valid_blocks):
        bt, bc = valid_blocks[i]
        bh = heights[i]

        if current_h + bh > target_h * 1.15 and current_page:
            # 当前页已接近目标，且加上这个块会超出较多，换新页
            pages.append(current_page)
            current_page = []
            current_h = 0
            continue

        current_page.append((bt, bc))
        current_h += bh
        i += 1

    if current_page:
        pages.append(current_page)

    # 如果最后一页内容太少（<目标的40%），合并到上一页
    if len(pages) >= 2:
        last_h = sum(estimate_block_height(bt, bc) for bt, bc in pages[-1])
        if last_h < target_h * 0.4:
            pages[-2].extend(pages[-1])
            pages.pop()

    return pages


def _estimate_content_height(page_blocks, font_size=17, content_width=976):
    """估算给定字号下内容的总像素高度。"""
    chars_per_line = content_width // (font_size + 1)
    def text_lines(text):
        w = _char_width(text)
        return max(1, (w + chars_per_line - 1) // chars_per_line)
    total = 0
    for bt, bc in page_blocks:
        if bt == "h1":
            total += font_size * 2.2 + 16
        elif bt == "h2":
            total += (font_size + 5) * 1.6 + 24
        elif bt == "h3":
            total += (font_size + 2) * 1.5 + 18
        elif bt == "code":
            lines = bc.count("\n") + 1
            total += lines * (font_size * 1.5) + 36
        elif bt == "quote":
            text = re.sub(r"^>\s?", "", bc, flags=re.MULTILINE)
            total += text_lines(text) * (font_size * 1.55) + 28
        elif bt == "list":
            lines = 0
            for item in re.split(r"\n(?=[-*]|\d+\.)", bc):
                lines += text_lines(item)
            total += lines * (font_size * 1.7) + 14
        elif bt == "table":
            rows = bc.count("\n") + 1
            total += rows * (font_size * 2.2) + 20
        elif bt == "hr":
            total += 36
        else:
            total += text_lines(bc) * (font_size * 1.65) + (font_size * 0.75)
    return total


def render_page_image(page_blocks, output_path, page_num, total_pages, engine="chromium", style="xiaohongshu", theme_index=0):
    """将一页的块渲染为独立的完整卡片图片。"""
    import subprocess
    md_content = "\n\n".join(content for _, content in page_blocks)
    extra_args = ["--mathjax", "--standalone", "--embed-resources"]
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "html"] + extra_args,
        input=md_content, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"pandoc 转换失败: {result.stderr}")
    html_content = result.stdout

    if style == "ios":
        theme = IOS_THEMES[theme_index % len(IOS_THEMES)]
        is_last = (page_num == total_pages)
        available_h = 1300
        target_fill = 0.65 if is_last else 0.97
        best_fs = 19
        best_fill = 0
        for fs in range(16, 29):
            h = _estimate_content_height(page_blocks, fs)
            fill = h / available_h
            if (not is_last) and 0.94 <= fill <= 1.0:
                best_fs = fs
                best_fill = fill
                break
            if abs(fill - target_fill) < abs(best_fill - target_fill):
                best_fs = fs
                best_fill = fill
        use_center = is_last and best_fill < 0.6
        line_h = 2.0 if best_fs <= 18 else (1.95 if best_fs <= 20 else (1.9 if best_fs <= 23 else 1.85))
        p_margin = best_fs * 0.85
        center_css = "justify-content: center;" if use_center else ""
        theme_css = f"""
  body {{
    background:
      radial-gradient(ellipse at 20% 20%, rgba(255,255,255,0.3) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 80%, {theme['h2_bg']} 0%, transparent 50%),
      linear-gradient(155deg, {theme['bg1']} 0%, {theme['bg2']} 30%, {theme['bg3']} 60%, {theme['bg4']} 100%);
  }}
  h2 {{
    color: {theme['title']};
    background: linear-gradient(135deg, {theme['h2_bg']} 0%, {theme['h2_border']} 100%);
    border: 1px solid {theme['h2_border']};
  }}
  h3 {{ border-left-color: {theme['primary']}; color: {theme['title']}; }}
  strong {{ color: {theme['primary']}; }}
  blockquote {{ border-left-color: {theme['primary']}; }}
  a {{ color: {theme['primary']}; }}
  code {{ color: {theme['primary']}; }}
  .ios-progress-bar {{ background: linear-gradient(90deg, {theme['primary']}, {theme['h2_border']}); }}
  .ios-bottom-deco {{ background: linear-gradient(90deg, transparent, {theme['primary']}, transparent); }}
  .ios-continue {{ color: {theme['primary']}; }}
  .ios-side-bar {{ background: linear-gradient(180deg, {theme['primary']}, {theme['h2_border']}); }}
  .ios-content > p:first-of-type::first-letter,
  .ios-content > h2 + p::first-letter {{ color: {theme['primary']}; }}
  h2::before {{ background: linear-gradient(180deg, {theme['primary']}, {theme['h2_border']}); }}
  blockquote::before {{ color: {theme['primary']}; }}
  li::marker {{ color: {theme['primary']}; }}
  .ios-cta-title {{ color: {theme['title']}; }}
  .ios-cta-btn {{ border-color: {theme['h2_border']}; color: {theme['primary']}; background: {theme['h2_bg']}; }}
  .ios-cta-share {{ color: {theme['title']}; }}
"""
        dynamic_css = f"""
  body {{ font-size: {best_fs}px; }}
  p {{ font-size: {best_fs}px; line-height: {line_h}; margin-bottom: {p_margin:.0f}px; color: #111111; font-weight: 550; letter-spacing: 0.5px; }}
  li {{ font-size: {best_fs}px; line-height: {line_h}; color: #111111; font-weight: 550; letter-spacing: 0.5px; }}
  h2 {{ font-size: {best_fs + 6}px; margin: {best_fs * 1.1:.0f}px 0 {best_fs * 0.7:.0f}px; }}
  h3 {{ font-size: {best_fs + 3}px; }}
"""
        page_css = IOS_CSS.replace("</style>", theme_css + dynamic_css + f"""
  body {{ height: 1440px; overflow: hidden; }}
  .ios-card {{ min-height: 1376px; display: flex; flex-direction: column; {center_css} }}
</style>""")
        card_class = "ios-card"
    else:
        page_css = XHS_CSS.replace("</style>", """
  body { height: 1440px; overflow: hidden; }
  .xhs-card { min-height: 1340px; display: flex; flex-direction: column; }
  .xhs-card-inner { flex: 1; }
</style>""")
        card_class = "xhs-card\"><div class=\"xhs-card-inner"

    body_match = re.search(r"(<body[^>]*>)(.*?)(</body>)", html_content, re.DOTALL)
    if body_match:
        if style == "ios":
            progress = int(page_num / total_pages * 100)
            chapter_num = f"{page_num:02d}"
            is_last_page = (page_num == total_pages)
            cta_html = ""
            if is_last_page:
                if best_fill < 0.5:
                    cta_size = "large"
                elif best_fill < 0.7:
                    cta_size = "medium"
                else:
                    cta_size = "small"
                cta_html = (
                    '<div class="ios-cta ios-cta-' + cta_size + '">'
                    '<div class="ios-cta-title">✨ 觉得有用？点赞 + 收藏 + 关注，不迷路 ✨</div>'
                    '<div class="ios-cta-buttons">'
                    '<div class="ios-cta-btn"><span class="ios-cta-icon">👍</span><span>点赞</span></div>'
                    '<div class="ios-cta-btn"><span class="ios-cta-icon">⭐</span><span>收藏</span></div>'
                    '<div class="ios-cta-btn"><span class="ios-cta-icon">➕</span><span>关注</span></div>'
                    '</div>'
                    '<div class="ios-cta-share">📤 转发给身边有需要的朋友吧</div>'
                    '</div>'
                )
            # 非最后一页添加"继续阅读"引导
            continue_html = ""
            if not is_last_page:
                continue_html = '<div class="ios-continue">继续阅读 <span class="ios-continue-arrow">→</span></div>'
            wrapped = (f'{body_match.group(1)}'
                       f'<div class="{card_class}">'
                       f'<div class="ios-side-bar"></div>'
                       f'<div class="ios-progress-bar" style="width: {progress}%"></div>'
                       f'<div class="ios-chapter-num">{chapter_num}</div>'
                       f'<div class="ios-content">{body_match.group(2)}</div>'
                       f'{continue_html}'
                       f'{cta_html}'
                       f'<div class="ios-bottom-deco"></div>'
                       f'</div>{body_match.group(3)}')
        else:
            wrapped = (f'{body_match.group(1)}'
                       f'<div class="{card_class}">'
                       f'{body_match.group(2)}</div>{body_match.group(3)}')
        html_content = html_content[:body_match.start()] + wrapped + html_content[body_match.end():]
    html_content = html_content.replace("</head>", page_css + "</head>")

    html_file = output_path.replace(".png", "_tmp.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    html_to_image_chromium(html_file, output_path, width=1080, height=1500)
    os.remove(html_file)

    from PIL import Image
    img = Image.open(output_path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    if h > 1440:
        img = img.crop((0, 0, w, 1440))
    elif h < 1440:
        from PIL import Image as PILImage
        if style == "ios":
            bg = PILImage.new("RGB", (w, 1440), (118, 75, 162))
        else:
            bg = PILImage.new("RGB", (w, 1440), (232, 244, 253))
        bg.paste(img, (0, 0))
        img = bg

    if style == "ios":
        img = _add_ios_page_indicator(img, page_num, total_pages, theme["primary"])
    else:
        img = _draw_notebook_rings(img)
        img = _add_page_number(img, page_num)
    img.save(output_path, quality=95)
    return output_path


def split_to_xhs_pages(long_image, output_prefix, page_height=1440):
    from PIL import Image
    img = Image.open(long_image)
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    pages = []
    y = 0
    page_idx = 1
    content_height = page_height - 70  # 预留底部页码区域
    while y < h:
        target_bottom = y + content_height
        if target_bottom >= h:
            page = img.crop((0, y, w, h))
            if _is_page_blank(page):
                break
            from PIL import Image as PILImage
            bg = PILImage.new("RGB", (w, page_height), (232, 244, 253))
            bg.paste(page, (0, 0))
            page = bg
            y = h
        else:
            # 在 target_bottom ±50px 范围内找最长连续空白区域（行间距），在中间切割
            pixels = img.load()
            search_start = max(y + 100, target_bottom - 80)
            search_end = min(h, target_bottom + 80)
            # 计算每行非背景像素数
            row_scores = []
            for cy in range(search_start, search_end):
                non_bg = 0
                for x in range(0, w, 8):
                    r, g, b = pixels[x, cy]
                    if not _is_background_pixel(r, g, b):
                        non_bg += 1
                row_scores.append((cy, non_bg))
            # 找最长连续 non_bg < 30 的区域
            best_start = 0
            best_len = 0
            cur_start = 0
            cur_len = 0
            for i, (cy, score) in enumerate(row_scores):
                if score < 40:
                    if cur_len == 0:
                        cur_start = i
                    cur_len += 1
                    if cur_len > best_len:
                        best_len = cur_len
                        best_start = cur_start
                else:
                    cur_len = 0
            if best_len >= 2:
                # 在最长连续空白区域的中间切割
                mid_idx = best_start + best_len // 2
                best_y = row_scores[mid_idx][0]
            else:
                # 没有足够长的空白区域，找最接近 target_bottom 的低分行
                best_y = target_bottom
                best_score = float("inf")
                for cy, score in row_scores:
                    if score < best_score:
                        best_score = score
                        best_y = cy
            page = img.crop((0, y, w, best_y))
            if _is_page_blank(page):
                break
            y = best_y
        # 统一补白到 page_height，确保所有页面高度一致
        if page.height < page_height:
            from PIL import Image as PILImage
            bg = PILImage.new("RGB", (w, page_height), (232, 244, 253))
            bg.paste(page, (0, 0))
            page = bg
        page = _add_page_number(page, page_idx)
        page = _draw_notebook_rings(page)
        out_path = f"{output_prefix}_{page_idx}.png"
        page.save(out_path, quality=95)
        pages.append(out_path)
        page_idx += 1
    return pages


# ══════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Markdown 转图片（支持公式 & 笔记本手账风格）")
    parser.add_argument("md_file", nargs="?", help="输入 Markdown 文件路径（批量模式下不需要）")
    parser.add_argument("image_file", nargs="?", help="输出图片文件路径（.png）（批量模式下不需要）")
    parser.add_argument("--html", default=None, help="（可选）保留中间 HTML 文件路径")
    parser.add_argument("--engine", default="auto", choices=["auto", "chromium", "wkhtmltoimage"],
                        help="截图引擎（默认 auto）")
    parser.add_argument("--style", default="ios", choices=["ios"],
                        help="图片风格：iOS 27 液态玻璃（唯一风格）")
    parser.add_argument("--tag", default="好书推荐", help="封面标签（默认：好书推荐）")
    parser.add_argument("--author", default=None, help="作者署名（显示在封面）")
    parser.add_argument("--cover-title", default=None, help="自定义封面标题")
    parser.add_argument("--cover-subtitle", default=None, help="自定义封面副标题")
    parser.add_argument("--batch", default=None, help="批量模式：指定包含md文件的目录")
    parser.add_argument("--output-dir", default=None, help="输出目录（批量模式下使用）")
    parser.add_argument("--recursive", action="store_true", help="批量模式下递归处理子目录")
    parser.add_argument("--zip", action="store_true", help="处理完成后自动打包生成的图片为 ZIP 文件")
    parser.add_argument("--include-md", action="store_true", help="打包时包含 Markdown 源文件")
    parser.add_argument("--include-docx", action="store_true", help="打包时包含 Word 文档（需 pandoc）")
    parser.add_argument("--watermark", default="@读书悦己", help="水印文字（默认 @读书悦己，设为 none 可关闭）；自动使用最佳配置（平铺+30度+低透明度）")
    parser.add_argument("--watermark-position", default="tile",
                        choices=["bottom-right", "bottom-left", "top-right", "top-left", "center", "tile"],
                        help="水印位置（默认 tile 平铺，防盗图效果最佳）")
    parser.add_argument("--watermark-opacity", type=float, default=0.15, help="水印透明度 0.1-0.9（默认 0.15，不影响阅读）")
    parser.add_argument("--watermark-size", type=int, default=32, help="水印字号（默认 32）")
    parser.add_argument("--watermark-color", default="#000000", help="水印颜色（默认黑色 #000000）")
    parser.add_argument("--watermark-angle", type=int, default=30, help="水印旋转角度（默认 30 度，平铺模式最佳）")
    parser.add_argument("--watermark-cover", action="store_true", help="给封面也添加水印（默认仅内容页，保持封面美观）")
    args = parser.parse_args()

    # 水印开关：--watermark none 可关闭水印
    watermark_enabled = bool(args.watermark) and args.watermark.lower() not in ("none", "no", "off", "false", "0")

    # 批量模式
    if args.batch:
        print("批量模式请使用 batch_md2card_pro.py 脚本：")
        print(f"  python3 batch_md2card_pro.py {args.batch} --style {args.style}")
        if args.output_dir:
            print(f"  --output-dir {args.output_dir}")
        if args.recursive:
            print("  --recursive")
        return

    if not args.md_file or not args.image_file:
        parser.print_help()
        print("\n错误：非批量模式下必须指定 md_file 和 image_file")
        sys.exit(1)

    check_dependencies(args.engine)
    actual_engine = args.engine
    if actual_engine == "auto":
        actual_engine = "chromium" if find_chromium() else "wkhtmltoimage"

    base_dir = os.path.dirname(os.path.abspath(args.image_file)) or "."
    base_name = os.path.splitext(os.path.basename(args.image_file))[0]
    html_file = args.html or os.path.join(base_dir, f"{base_name}.html")
    os.makedirs(base_dir, exist_ok=True)

    # ── iOS 27 液态玻璃风格（唯一风格）──
    print(f"[1/3] 生成封面页（iOS 27 液态玻璃）...")
    cover_html = os.path.join(base_dir, f"{base_name}_cover.html")
    generate_ios_cover_html(args.md_file, cover_html, args.tag,
                             author=args.author,
                             custom_title=args.cover_title,
                             custom_subtitle=args.cover_subtitle)
    cover_img = os.path.join(base_dir, f"{base_name}_cover.png")
    html_to_image_chromium(cover_html, cover_img, width=1080, height=1500)
    # iOS 封面裁剪到 1440
    from PIL import Image as PILImage
    cim = PILImage.open(cover_img)
    if cim.height > 1440:
        cim.crop((0, 0, 1080, 1440)).save(cover_img)
        if not args.html:
            try:
                os.remove(cover_html)
            except OSError:
                pass

        print("[2/3] 智能解析章节与段落...")
        with open(args.md_file, "r", encoding="utf-8") as f:
            md_content = f.read()
        blocks = parse_markdown_blocks(md_content)
        pages = paginate_blocks(blocks)
        print(f"  共解析 {len(blocks)} 个内容块，分为 {len(pages)} 页")

        print("[3/3] 逐页渲染完整卡片...")
        result = []
        final_cover = os.path.join(base_dir, f"{base_name}_1.png")
        if cover_img != final_cover:
            if os.path.exists(final_cover):
                os.remove(final_cover)
            os.rename(cover_img, final_cover)
        # 封面水印（需指定 --watermark-cover）
        if watermark_enabled and args.watermark_cover:
            _add_watermark(final_cover, args.watermark, args.watermark_position,
                           args.watermark_opacity, args.watermark_size, args.watermark_color, args.watermark_angle)
            print("  封面已添加水印")
        result.append(final_cover)

        for i, page_blocks in enumerate(pages, 2):
            page_path = os.path.join(base_dir, f"{base_name}_{i}.png")
            render_page_image(page_blocks, page_path, i - 1, len(pages),
                              actual_engine, style="ios", theme_index=i - 2)
            # 内容页水印
            if watermark_enabled:
                _add_watermark(page_path, args.watermark, args.watermark_position,
                               args.watermark_opacity, args.watermark_size, args.watermark_color, args.watermark_angle)
            result.append(page_path)
            print(f"  第 {i-1} 页 / 共 {len(pages)} 页内容")

        print(f"\n完成！共生成 {len(result)} 张图片：")
        for p in result:
            print(f"  - {p}")
        # 自动打包
        if args.zip:
            zip_path = _zip_output_files(result, md_file=args.md_file, include_md=args.include_md, include_docx=args.include_docx)
            if zip_path:
                print(f"\n已打包为 ZIP: {zip_path}")
        return




if __name__ == "__main__":
    main()
