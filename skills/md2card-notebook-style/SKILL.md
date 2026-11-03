---
name: md2card-notebook-style
agent_created: true
description: Convert Markdown content into a shareable PNG image styled as a blue spiral-bound notebook knowledge card. Use when the user asks to turn Markdown into an image, create a knowledge card, generate a social-media-style Markdown picture, or apply a notebook/card theme to Markdown output.
---

# MD2Card Notebook Style

## Overview

This skill renders Markdown text as a high-resolution PNG image with a blue
spiral-bound notebook theme. The output mimics a friendly knowledge card:
bright blue cover, yellow binder rings, clean white page, yellow pill
highlights, and a dark code block style.

## When to Use This Skill

- The user says "把这段 Markdown 转成图片" or "Markdown 转图片".
- The user asks for a knowledge card, 知识卡片, 小红书风格图片, or shareable note image.
- The user references the MD2Card / MD2Card-style notebook theme.
- The user wants a Markdown document exported as a styled image.

## How to Use

### Step 1: Prepare the Markdown input

Write or receive the Markdown content. Save it as a `.md` file.

Supported syntax includes:

- `#` headings
- `**bold**`, `*italic*`
- `` `inline code` ``
- ` ``` ` fenced code blocks
- Lists, blockquotes, links, tables, images
- `==highlighted text==` for yellow pill badges

### Step 2: Run the renderer script

Use the bundled Python script:

```bash
python "<skill-root>/scripts/md2card.py" input.md [-o output.png] [--width 800]
```

Defaults:

- Output file: `<input>.png`
- Width: 800px
- Device scale factor: 2 (retina / high-resolution output)

### Step 3: Verify the output

Open the generated PNG and confirm the styling matches the notebook theme.
Adjust the Markdown or rerun with a different width if needed.

## Requirements

The renderer depends on the Python `markdown` package (for local conversion)
and Playwright with a Chromium browser (for the screenshot).

Install once with:

```bash
pip install markdown playwright
playwright install chromium
```

Markdown is converted locally by the `markdown` package, so the template does
NOT require any runtime CDN access. The only external dependency at render
time is Playwright launching Chromium.

If a dependency is missing, the script prints the relevant installation hint
and exits.

## Bundled Resources

- `assets/template.html` — The notebook card HTML/CSS template. Markdown is
  rendered to HTML by the Python script and injected into the template; no
  runtime CDN is required.
- `scripts/md2card.py` — The Python renderer that converts Markdown locally,
  injects it into the template, and screenshots it with Playwright.
- `references/style-guide.md` — Detailed color, typography, and layout specs.

## Customization Notes

- To change colors, edit the CSS variables at the top of
  `assets/template.html`.
- To change card width, use the `--width` CLI flag or adjust the `.notebook-card`
  CSS rule.
- The `==highlighted text==` syntax is a custom extension that renders a yellow
  pill badge.
