# MD2Card Notebook Style Guide

This reference documents the visual design system of the blue notebook card theme.
Use it when adjusting the template or explaining the style to users.

## Design Concept

A friendly knowledge card that looks like a page torn from a spiral-bound
notebook. It combines a bright blue cover, yellow rings, a clean white page,
and a soft grid-paper background to create a learnable, shareable visual.

## Color Palette

| Token | Value | Usage |
|-------|-------|-------|
| `--cover-blue` | `#5ba8ff` | Outer notebook cover |
| `--cover-blue-dark` | `#4a9eff` | Links, accents |
| `--ring-yellow` | `#ffd845` | Spiral rings |
| `--card-bg` | `#ffffff` | Inner page background |
| `--notebook-bg` | `#eef6ff` | Page background |
| `--notebook-grid` | `#dbeafe` | Grid lines |
| `--text-primary` | `#1f2937` | Headings, bold text |
| `--text-secondary` | `#4b5563` | Body text |
| `--text-muted` | `#6b7280` | Captions, comments |
| `--inline-code-bg` | `#f3f4f6` | Inline code background |
| `--inline-code-text` | `#374151` | Inline code text |
| `--code-bg` | `#1a1a1a` | Code block background |
| `--code-text` | `#e5e7eb` | Code block default text |
| `--accent-green` | `#4ade80` | Markdown headings inside code blocks |
| `--tag-bg` | `#fde047` | Yellow pill highlight |
| `--tag-text` | `#1f2937` | Yellow pill text |

## Typography

- **H1**: 42px, weight 800, line-height 1.25
- **H2**: 28px, weight 700, line-height 1.35
- **H3**: 22px, weight 700, line-height 1.40
- **Body**: 20px, weight 400, line-height 1.80
- **Inline code**: 0.85em, weight 500
- **Code block**: 17px, weight 400, line-height 1.70

Font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial, sans-serif`

## Layout

- Card width: 800px
- Outer cover padding: 24px top/bottom, 32px right, 56px left
- Inner page padding: 48px 44px
- Card border radius: 32px
- Inner page border radius: 16px
- Spiral rings: 3 yellow pills, 44x18px, positioned absolutely on the left

## Special Markdown Syntax

### Yellow pill highlight

Use `==highlighted text==` to render a yellow pill badge, matching the
"Markdown 基础语法" label in the reference image.

Example:
```markdown
==Markdown 基础语法==
```

### Headings inside code blocks

Markdown headings shown inside code blocks are rendered in green (`#4ade80`),
matching the screenshot style where `# 一级标题` appears in green on a dark
background.

## Supported Markdown Elements

- Headings (H1–H3)
- Paragraphs and line breaks
- Bold and italic
- Inline code and fenced code blocks
- Ordered and unordered lists
- Blockquotes
- Horizontal rules
- Links
- Tables
- Images
