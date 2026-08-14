#!/usr/bin/env python3
"""Measure WCAG contrast in a captured screen region.

Usage:
    python contrast.py IMAGE [--region X0,Y0,X1,Y1] [--json OUT.json] [--large-text]

Given a region containing text on a background, this separates foreground from
background by luminance clustering and estimates a contrast ratio from the rendered pixels. That matters because the ratio between two declared token values is
not the ratio a user sees once opacity, overlays, blending or an image backdrop are
in play — and those are exactly the cases where contrast quietly fails.

With no --region the whole image is scanned in a grid and the worst-contrast cells
are reported, which is a fast way to find the problem area on a full screenshot.

Requires: pillow, numpy
"""
from __future__ import annotations

import argparse
import json
import sys

try:
    import numpy as np
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Missing dependency. Install with: pip install pillow numpy")


def rel_luminance(rgb: np.ndarray) -> float:
    c = np.asarray(rgb, dtype=np.float64) / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])


def ratio(fg: np.ndarray, bg: np.ndarray) -> float:
    l1, l2 = rel_luminance(fg), rel_luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def hexify(rgb: np.ndarray) -> str:
    return "#" + "".join(f"{int(round(v)):02X}" for v in rgb)


def split_region(arr: np.ndarray) -> dict:
    """Two-means split on luminance: the majority cluster is the background."""
    flat = arr.reshape(-1, 3).astype(np.float64)
    lum = flat @ np.array([0.2126, 0.7152, 0.0722])
    if lum.max() - lum.min() < 4:
        return {"flat_region": True, "colour": hexify(flat.mean(axis=0))}
    thresh = (lum.max() + lum.min()) / 2
    for _ in range(12):
        low, high = lum < thresh, lum >= thresh
        if not low.any() or not high.any():
            break
        new = (lum[low].mean() + lum[high].mean()) / 2
        if abs(new - thresh) < 0.01:
            break
        thresh = new
    low, high = lum < thresh, lum >= thresh
    if not low.any() or not high.any():
        return {"flat_region": True, "colour": hexify(flat.mean(axis=0))}
    dark_share = float(low.mean())
    fg_mask, bg_mask = (low, high) if dark_share < 0.5 else (high, low)
    # Background is broad and flat, so its mean is representative. Foreground text is
    # heavily antialiased, so its mean is pulled toward the background and can
    # understate the underlying stroke contrast. Use the most extreme 30% as a
    # diagnostic estimate rather than claiming exact semantic foreground recovery.
    bg = flat[bg_mask].mean(axis=0)
    fg_pixels, fg_lum = flat[fg_mask], lum[fg_mask]
    bg_lum = float(lum[bg_mask].mean())
    core = np.abs(fg_lum - bg_lum) >= np.percentile(np.abs(fg_lum - bg_lum), 70)
    fg = fg_pixels[core].mean(axis=0) if core.any() else fg_pixels.mean(axis=0)
    return {
        "flat_region": False,
        "foreground": hexify(fg),
        "background": hexify(bg),
        "foreground_pixel_share": round(min(dark_share, 1 - dark_share), 4),
        "contrast_ratio_estimate": round(ratio(fg, bg), 2),
    }


def grade(r: float, large: bool) -> dict:
    aa = 3.0 if large else 4.5
    aaa = 4.5 if large else 7.0
    return {
        "wcag_aa_threshold": aa,
        "wcag_aa": r >= aa,
        "wcag_aaa": r >= aaa,
        "text_size_assumed": "large (>=18.66px bold or 24px)" if large else "normal",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="WCAG contrast from rendered pixels")
    ap.add_argument("image")
    ap.add_argument("--region", help="X0,Y0,X1,Y1 — omit to scan the whole image in a grid")
    ap.add_argument("--grid", type=int, default=6, help="grid divisions when scanning")
    ap.add_argument("--large-text", action="store_true")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    img = Image.open(args.image).convert("RGB")
    arr = np.asarray(img)

    if args.region:
        x0, y0, x1, y1 = (int(v) for v in args.region.split(","))
        res = split_region(arr[y0:y1, x0:x1])
        result = {"image": args.image, "region": [x0, y0, x1, y1], **res}
        if not res.get("flat_region"):
            result.update(grade(res["contrast_ratio_estimate"], args.large_text))
    else:
        h, w = arr.shape[:2]
        cells = []
        for gy in range(args.grid):
            for gx in range(args.grid):
                y0, y1 = gy * h // args.grid, (gy + 1) * h // args.grid
                x0, x1 = gx * w // args.grid, (gx + 1) * w // args.grid
                r = split_region(arr[y0:y1, x0:x1])
                if r.get("flat_region") or r["foreground_pixel_share"] < 0.02:
                    continue  # empty or near-empty cell, nothing to judge
                cells.append({"region": [x0, y0, x1, y1], **r,
                              **grade(r["contrast_ratio_estimate"], args.large_text)})
        cells.sort(key=lambda c: c["contrast_ratio_estimate"])
        result = {
            "image": args.image,
            "cells_evaluated": len(cells),
            "worst_cells": cells[:5],
            "failing_aa": sum(1 for c in cells if not c["wcag_aa"]),
            "note": "diagnostic estimate only; grid cells or regions containing gradients, imagery, shadows, translucency or multiple foreground colours can misclassify foreground/background. Re-run with a targeted region and visually confirm any material finding.",
        }

    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump(result, fh, indent=2)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
