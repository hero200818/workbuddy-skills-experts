#!/usr/bin/env python3
"""
MD2Card Notebook Style - Markdown to image renderer.

Converts a Markdown file into a PNG image using the blue notebook card
theme defined in assets/template.html.

Markdown is rendered to HTML locally with the `markdown` Python package,
so the template does NOT depend on any runtime CDN. The final screenshot
is taken with Playwright/Chromium.

Usage:
    python md2card.py input.md [-o output.png] [--width 800]

Dependencies:
    pip install markdown playwright
    playwright install chromium
"""

import argparse
import re
import sys
import tempfile
from pathlib import Path


def get_skill_dir() -> Path:
    """Return the skill root directory (where assets/ and scripts/ live)."""
    return Path(__file__).resolve().parent.parent


def load_template() -> str:
    """Load the notebook card HTML template."""
    template_path = get_skill_dir() / "assets" / "template.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template_path.read_text(encoding="utf-8")


def render_markdown_to_html(markdown_text: str) -> str:
    """Convert Markdown to HTML with the notebook theme conventions.

    - Uses the Python `markdown` package (no runtime CDN needed).
    - `==highlight==` becomes a yellow pill <mark>.
    - `# heading` lines inside ```markdown code blocks are wrapped in a
      green <span class="md-h"> to match the reference card style.
    """
    try:
        import markdown
    except ImportError as exc:
        raise RuntimeError(
            "The `markdown` package is not installed. Run:\n"
            "  pip install markdown"
        ) from exc

    # Protect fenced code blocks so ==...== inside them is not touched.
    code_blocks = []

    def _stash(m):
        code_blocks.append(m.group(0))
        return f"\x00{len(code_blocks) - 1}\x00"

    protected = re.sub(r"<pre[^>]*>.*?</pre>", _stash, markdown_text, flags=re.DOTALL)

    # Convert ==highlight== to a yellow pill before markdown parsing.
    protected = re.sub(r"==([^=\n]+)==", r"<mark>\1</mark>", protected)

    md = markdown.Markdown(
        extensions=["fenced_code", "tables", "sane_lists", "nl2br"]
    )
    html = md.convert(protected)

    # Restore code blocks.
    def _restore(m):
        return code_blocks[int(m.group(1))]

    html = re.sub(r"\x00(\d+)\x00", _restore, html)

    # Green heading lines inside markdown code blocks.
    def _highlight(m):
        full = m.group(0)
        if "language-markdown" in full or "language-md" in full:
            attr = m.group(1)
            content = m.group(2)
            content = re.sub(
                r"(?m)^(#+\s.*)$",
                r'<span class="md-h">\1</span>',
                content,
            )
            return f"<pre><code{attr}>{content}</code></pre>"
        return full

    html = re.sub(
        r"<pre><code([^>]*)>(.*?)</code></pre>", _highlight, html, flags=re.DOTALL
    )
    return html


def build_html(markdown_text: str) -> str:
    """Inject rendered Markdown into the template."""
    template = load_template()
    rendered = render_markdown_to_html(markdown_text)
    return template.replace("{{MARKDOWN_HTML}}", rendered)


def render_image(html_content: str, output_path: Path, width: int = 800) -> Path:
    """Render HTML to a PNG image using Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed. Run:\n"
            "  pip install playwright\n"
            "  playwright install chromium"
        ) from exc

    with tempfile.TemporaryDirectory() as tmpdir:
        html_file = Path(tmpdir) / "md2card.html"
        html_file.write_text(html_content, encoding="utf-8")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": 100, "deviceScaleFactor": 2}
            )
            page.goto(f"file:///{html_file.as_posix()}")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(300)

            height = page.evaluate("() => document.body.scrollHeight")
            page.set_viewport_size(
                {"width": width, "height": height, "deviceScaleFactor": 2}
            )
            page.wait_for_timeout(200)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(output_path), full_page=True)
            browser.close()

    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert Markdown to a blue notebook-style card image."
    )
    parser.add_argument("input", help="Path to the Markdown input file.")
    parser.add_argument(
        "-o", "--output", help="Path for the output PNG image. Defaults to <input>.png"
    )
    parser.add_argument(
        "--width", type=int, default=800, help="Viewport width in pixels (default: 800)."
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else input_path.with_suffix(".png")

    try:
        markdown_text = input_path.read_text(encoding="utf-8")
        html_content = build_html(markdown_text)
        render_image(html_content, output_path, width=args.width)
        print(f"Saved card image to: {output_path}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
