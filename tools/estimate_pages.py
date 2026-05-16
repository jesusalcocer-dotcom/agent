#!/usr/bin/env python3
"""
estimate_pages.py — Rough page estimate from markdown.

Usage:
    python estimate_pages.py <markdown-file> [--font-size 11] [--spacing 1.5] [--page A4]

Counts words after stripping markdown syntax (headings, links, code blocks) and
applies a font/spacing heuristic to estimate pages.

This is a ROUGH estimate. Actual page count depends on whitespace, headings, lists,
tables, images, and the word processor's renderer. The downstream flow uses this
estimate to flag potential over-limit drafts; the user verifies in Word and asks
to compress or sends a screenshot of overflow.

Heuristic (Calibri-like font, A4 with ~2.5cm margins):
    1.0 spacing → ~440 words/page
    1.5 spacing → ~270 words/page
    2.0 spacing → ~220 words/page
"""
import argparse
import re
import sys
from pathlib import Path

# (font_size, spacing) → words per page. Calibrated for Calibri on A4 with 2.54cm margins.
WPP_TABLE = {
    (10, 1.0): 500, (10, 1.5): 310, (10, 2.0): 250,
    (11, 1.0): 440, (11, 1.15): 380, (11, 1.5): 270, (11, 2.0): 220,
    (12, 1.0): 400, (12, 1.15): 350, (12, 1.5): 250, (12, 2.0): 200,
}


def strip_markdown(text: str) -> str:
    """Remove markdown syntax to get prose for word counting."""
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)         # fenced code blocks
    text = re.sub(r'`[^`]+`', '', text)                              # inline code
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)          # HTML comments
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)                 # images
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)             # links (keep text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)       # heading markers
    text = re.sub(r'(\*\*|\*|__|_)', '', text)                       # emphasis markers
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)            # blockquote markers
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)   # unordered list bullets
    text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)   # ordered list markers
    text = re.sub(r'^\|.*\|$', '', text, flags=re.MULTILINE)         # table rows (rough)
    text = re.sub(r'^-{3,}\s*$', '', text, flags=re.MULTILINE)       # horizontal rules
    return text


def count_words(text: str) -> int:
    return len(re.findall(r'\b\w+\b', text))


def estimate_pages(words: int, font_size: int, spacing: float) -> tuple[float, int]:
    """Return (pages, words_per_page_used)."""
    wpp = WPP_TABLE.get((font_size, spacing))
    if wpp is None:
        # Fallback interpolation: base 270 at 11pt 1.5, scale by font and spacing
        wpp = int(270 * (11 / font_size) * (1.5 / spacing))
    return words / wpp, wpp


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("markdown", help="Markdown draft file")
    p.add_argument("--font-size", type=int, default=11, help="Font size in points (default: 11)")
    p.add_argument("--spacing", type=float, default=1.5, help="Line spacing (default: 1.5)")
    p.add_argument("--page", default="A4", help="Page size — informational only (default: A4)")
    p.add_argument("--limit", type=int, help="Page limit; warn if estimate exceeds")
    args = p.parse_args()

    path = Path(args.markdown).expanduser().resolve()
    if not path.exists():
        sys.exit(f"❌ File not found: {path}")

    raw = path.read_text(encoding="utf-8")
    prose = strip_markdown(raw)
    words = count_words(prose)
    pages, wpp = estimate_pages(words, args.font_size, args.spacing)

    print(f"📄 {path.name}")
    print(f"   Words (prose, no markdown): {words:,}")
    print(f"   Format: ~Calibri {args.font_size}pt, {args.spacing}x spacing, {args.page}")
    print(f"   Heuristic: ~{wpp} words/page")
    print(f"   📐 Estimated pages: {pages:.1f}")

    if args.limit:
        if pages > args.limit:
            over_by = pages - args.limit
            print(f"   ⚠️  OVER LIMIT by ~{over_by:.1f} pages ({pages:.1f} / {args.limit})")
            print(f"      Suggest compressing ~{int(over_by * wpp)} words.")
            sys.exit(2)
        else:
            slack = args.limit - pages
            print(f"   ✓ Within limit ({pages:.1f} / {args.limit}, slack ~{slack:.1f} pages)")

    print()
    print("   ⚠️  Rough estimate only. Verify in Word.")


if __name__ == "__main__":
    main()
