#!/usr/bin/env python3
"""
pages_to_md.py — convert .pages → .docx (LibreOffice headless) → .md (pandoc).

Usage:
    python pages_to_md.py <file.pages>

Outputs both a .docx and a .md sidecar next to the original .pages file.
Useful for ingesting Apple Pages instructions into the school workflow.

Requires:
    - LibreOffice (installed at /Applications/LibreOffice.app)
    - pandoc (on PATH)
"""
import argparse
import subprocess
import sys
from pathlib import Path

SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pages_file", help=".pages file to convert")
    parser.add_argument("--keep-docx", action="store_true", help="Keep the intermediate .docx (default: yes)")
    args = parser.parse_args()

    pages_path = Path(args.pages_file).expanduser().resolve()
    if not pages_path.exists():
        sys.exit(f"❌ File not found: {pages_path}")
    if pages_path.suffix.lower() != ".pages":
        print(f"⚠️  Input doesn't end in .pages: {pages_path}", file=sys.stderr)

    if not Path(SOFFICE).exists():
        sys.exit(f"❌ LibreOffice not found at {SOFFICE}. Install with: brew install --cask libreoffice")

    out_dir = pages_path.parent

    print("🔄 Converting .pages → .docx via LibreOffice headless...")
    result = subprocess.run(
        [SOFFICE, "--headless", "--convert-to", "docx", "--outdir", str(out_dir), str(pages_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"❌ LibreOffice failed:\n{result.stderr}", file=sys.stderr)
        print("💡 Workaround: open the file in Pages.app, File → Export To → PDF/Word,", file=sys.stderr)
        print("   and drop the exported file into instructions/.", file=sys.stderr)
        sys.exit(1)

    docx_path = out_dir / (pages_path.stem + ".docx")
    if not docx_path.exists():
        sys.exit(f"❌ Expected output not found: {docx_path}")
    print(f"   ✓ {docx_path.name}")

    print("🔄 Converting .docx → .md via pandoc...")
    md_path = out_dir / (pages_path.stem + ".md")
    result = subprocess.run(
        ["pandoc", str(docx_path), "-o", str(md_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"⚠️  Pandoc warned:\n{result.stderr}", file=sys.stderr)
    if not md_path.exists():
        sys.exit(f"❌ Pandoc didn't produce {md_path}")
    print(f"   ✓ {md_path.name}")

    print(f"\n✅ Done. {docx_path.name} and {md_path.name} written next to the original.")


if __name__ == "__main__":
    main()
