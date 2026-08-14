#!/usr/bin/env python3
"""Combine many captures into a single labelled contact sheet.

Usage:
    python contact_sheet.py IMAGE [IMAGE...] --out SHEET.png [--cols 4]
                            [--labels] [--cell 320] [--bg 1E1E1E]

A turntable, a breakpoint sweep, or a state matrix (default/hover/focus/disabled)
is far cheaper to review as one image than as eight, and inconsistency across the
set becomes obvious in a way it never is when the frames are viewed one at a time.

Requires: pillow
"""
from __future__ import annotations

import argparse
import math
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    sys.exit("Missing dependency. Install with: pip install pillow")


def load_font(size: int):
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
    return ImageFont.load_default()


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a contact sheet")
    ap.add_argument("images", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cols", type=int, default=0, help="0 = auto (near-square grid)")
    ap.add_argument("--cell", type=int, default=320, help="max cell edge in px")
    ap.add_argument("--labels", action="store_true", help="caption each cell with its filename")
    ap.add_argument("--bg", default="1E1E1E", help="sheet background as RRGGBB")
    ap.add_argument("--gap", type=int, default=8)
    args = ap.parse_args()

    paths = [p for p in args.images if os.path.isfile(p)]
    if not paths:
        sys.exit("No readable images supplied.")

    cols = args.cols or max(1, min(len(paths), int(math.ceil(math.sqrt(len(paths))))))
    rows = math.ceil(len(paths) / cols)
    label_h = 20 if args.labels else 0
    font = load_font(12) if args.labels else None

    cw = ch = args.cell
    sheet_w = cols * cw + (cols + 1) * args.gap
    sheet_h = rows * (ch + label_h) + (rows + 1) * args.gap
    bg = tuple(int(args.bg[i : i + 2], 16) for i in (0, 2, 4))
    sheet = Image.new("RGB", (sheet_w, sheet_h), bg)
    draw = ImageDraw.Draw(sheet)

    for i, path in enumerate(paths):
        r, c = divmod(i, cols)
        x = args.gap + c * (cw + args.gap)
        y = args.gap + r * (ch + label_h + args.gap)
        img = Image.open(path).convert("RGB")
        img.thumbnail((cw, ch), Image.LANCZOS)
        sheet.paste(img, (x + (cw - img.width) // 2, y + (ch - img.height) // 2))
        if args.labels:
            name = os.path.basename(path)
            if len(name) > 42:
                name = name[:20] + "…" + name[-20:]
            draw.text((x + 2, y + ch + 3), name, fill=(200, 200, 200), font=font)

    sheet.save(args.out)
    print(f"{args.out}  {sheet.width}x{sheet.height}  {len(paths)} frames  {cols}x{rows} grid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
