#!/usr/bin/env python3
"""Compare two images and report objective difference metrics.

Usage:
    python compare_images.py BEFORE AFTER [--json OUT.json] [--heatmap OUT.png]
                             [--threshold 12] [--quiet]

Outputs SSIM, perceptual-hash distance, changed-pixel percentage and the bounding
box of the changed region. The bounding box answers the question that matters most
in a recheck: did the change land where it was supposed to, and did anything else
move?

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


def load(path: str, size: tuple[int, int] | None = None) -> Image.Image:
    img = Image.open(path).convert("RGB")
    if size and img.size != size:
        img = img.resize(size, Image.LANCZOS)
    return img


def to_gray(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("L"), dtype=np.float64)


def box_filter(arr: np.ndarray, radius: int) -> np.ndarray:
    """Uniform filter via summed-area table (keeps us numpy-only)."""
    pad = radius
    padded = np.pad(arr, pad, mode="edge")
    cum = padded.cumsum(axis=0).cumsum(axis=1)
    cum = np.pad(cum, ((1, 0), (1, 0)), mode="constant")
    k = 2 * radius + 1
    h, w = arr.shape
    total = (
        cum[k : k + h, k : k + w]
        - cum[0:h, k : k + w]
        - cum[k : k + h, 0:w]
        + cum[0:h, 0:w]
    )
    return total / (k * k)


def ssim(a: np.ndarray, b: np.ndarray, radius: int = 5) -> float:
    """Structural similarity with a uniform window. 1.0 == identical."""
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    mu_a, mu_b = box_filter(a, radius), box_filter(b, radius)
    saa = box_filter(a * a, radius) - mu_a * mu_a
    sbb = box_filter(b * b, radius) - mu_b * mu_b
    sab = box_filter(a * b, radius) - mu_a * mu_b
    num = (2 * mu_a * mu_b + c1) * (2 * sab + c2)
    den = (mu_a**2 + mu_b**2 + c1) * (saa + sbb + c2)
    return float(np.mean(num / den))


def phash(img: Image.Image, size: int = 32, keep: int = 8) -> int:
    """DCT-based perceptual hash. Robust to small rendering noise."""
    arr = np.asarray(img.convert("L").resize((size, size), Image.LANCZOS), dtype=np.float64)
    # 2D DCT-II via matrix multiplication
    n = size
    k = np.arange(n)
    basis = np.cos(np.pi * (2 * k[:, None] + 1) * k[None, :] / (2 * n))
    dct = basis.T @ arr @ basis
    low = dct[:keep, :keep].flatten()
    med = np.median(low[1:])  # ignore DC term
    bits = low > med
    out = 0
    for bit in bits:
        out = (out << 1) | int(bit)
    return out


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def changed_bbox(diff: np.ndarray, threshold: float):
    mask = diff > threshold
    if not mask.any():
        return None, 0.0
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    pct = float(mask.sum()) / mask.size * 100.0
    return (int(cols[0]), int(rows[0]), int(cols[-1]), int(rows[-1])), pct


def main() -> int:
    ap = argparse.ArgumentParser(description="Objective image comparison")
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--heatmap", dest="heatmap")
    ap.add_argument("--threshold", type=float, default=12.0,
                    help="per-pixel intensity delta counted as changed (0-255)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    before = load(args.before)
    after = load(args.after, size=before.size)
    resized = Image.open(args.after).size != before.size

    ga, gb = to_gray(before), to_gray(after)
    diff = np.abs(ga - gb)
    bbox, pct = changed_bbox(diff, args.threshold)

    result = {
        "before": args.before,
        "after": args.after,
        "size": list(before.size),
        "after_was_resized_to_match": resized,
        "ssim": round(ssim(ga, gb), 4),
        "phash_distance": hamming(phash(before), phash(after)),
        "changed_pixels_pct": round(pct, 3),
        "changed_bbox": list(bbox) if bbox else None,
        "max_pixel_delta": round(float(diff.max()), 1),
        "mean_pixel_delta": round(float(diff.mean()), 3),
    }
    result["identical"] = result["changed_pixels_pct"] == 0.0

    if args.heatmap:
        norm = np.clip(diff / max(diff.max(), 1e-6) * 255.0, 0, 255).astype(np.uint8)
        heat = np.stack([norm, np.zeros_like(norm), 255 - norm], axis=-1)
        base = np.asarray(after.convert("RGB"), dtype=np.float64) * 0.35
        blend = (base + heat.astype(np.float64) * 0.65).clip(0, 255).astype(np.uint8)
        Image.fromarray(blend).save(args.heatmap)
        result["heatmap"] = args.heatmap

    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump(result, fh, indent=2)
    if not args.quiet:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
