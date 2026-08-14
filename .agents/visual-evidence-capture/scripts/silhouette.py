#!/usr/bin/env python3
"""Measure the silhouette of a rendered object or asset.

Usage:
    python silhouette.py IMAGE [--json OUT.json] [--reference REF.png]
                         [--bg auto|alpha|RRGGBB] [--tolerance 18] [--mask OUT.png]

Silhouette is judged before surface detail, so these are the first numbers to look
at on any asset. Comparing them against a reference render is the most objective
proportion check available — a taper or mass-distribution error shows up here even
when the render "looks about right".

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


def build_mask(path: str, bg: str, tolerance: float) -> np.ndarray:
    img = Image.open(path)
    if bg == "alpha" or (bg == "auto" and img.mode in ("RGBA", "LA")):
        alpha = np.asarray(img.convert("RGBA"))[..., 3]
        if alpha.min() < 250:
            return alpha > 16
    rgb = np.asarray(img.convert("RGB"), dtype=np.float64)
    if bg not in ("auto", "alpha"):
        ref = np.array([int(bg[i : i + 2], 16) for i in (0, 2, 4)], dtype=np.float64)
    else:
        corners = np.concatenate([rgb[0, 0], rgb[0, -1], rgb[-1, 0], rgb[-1, -1]]).reshape(4, 3)
        ref = corners.mean(axis=0)
    dist = np.sqrt(((rgb - ref) ** 2).sum(axis=-1))
    return dist > tolerance


def measure(mask: np.ndarray) -> dict:
    if not mask.any():
        return {"error": "empty mask — object not separable from background; try --bg or --tolerance"}
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    y0, y1, x0, x1 = int(rows[0]), int(rows[-1]), int(cols[0]), int(cols[-1])
    crop = mask[y0 : y1 + 1, x0 : x1 + 1]
    h, w = crop.shape

    ys, xs = np.nonzero(crop)
    cx, cy = float(xs.mean()), float(ys.mean())

    row_widths = crop.sum(axis=1)
    bands = np.array_split(row_widths, 3)
    band_means = [float(b.mean()) for b in bands]
    widest_row = int(np.argmax(row_widths))

    flipped = crop[:, ::-1]
    symmetry_err = float(np.mean(crop != flipped))

    frame_h, frame_w = mask.shape
    return {
        "bbox": [x0, y0, x1, y1],
        "bbox_size": [w, h],
        "aspect_ratio_w_over_h": round(w / h, 4),
        "fill_ratio_of_bbox": round(float(crop.sum()) / crop.size, 4),
        "fill_ratio_of_frame": round(float(mask.sum()) / mask.size, 4),
        "centroid_in_bbox_norm": [round(cx / max(w - 1, 1), 4), round(cy / max(h - 1, 1), 4)],
        "centroid_offset_from_bbox_centre_px": [round(cx - (w - 1) / 2, 2), round(cy - (h - 1) / 2, 2)],
        "band_mean_width_px": {
            "top_third": round(band_means[0], 2),
            "middle_third": round(band_means[1], 2),
            "bottom_third": round(band_means[2], 2),
        },
        "top_to_bottom_width_ratio": round(band_means[0] / max(band_means[2], 1e-6), 4),
        "widest_row_norm_from_top": round(widest_row / max(h - 1, 1), 4),
        "horizontal_symmetry_error": round(symmetry_err, 4),
        "touches_frame_edge": bool(x0 == 0 or y0 == 0 or x1 == frame_w - 1 or y1 == frame_h - 1),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Silhouette and proportion metrics")
    ap.add_argument("image")
    ap.add_argument("--reference", help="optional reference render to diff proportions against")
    ap.add_argument("--bg", default="auto", help="auto | alpha | RRGGBB")
    ap.add_argument("--tolerance", type=float, default=18.0)
    ap.add_argument("--mask", help="write the extracted mask for inspection")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    mask = build_mask(args.image, args.bg, args.tolerance)
    result = {"image": args.image, "subject": measure(mask)}

    if args.mask:
        Image.fromarray((mask * 255).astype(np.uint8)).save(args.mask)

    if args.reference:
        ref = measure(build_mask(args.reference, args.bg, args.tolerance))
        result["reference"] = ref
        s = result["subject"]
        if "error" not in s and "error" not in ref:
            result["delta_vs_reference"] = {
                "aspect_ratio": round(s["aspect_ratio_w_over_h"] - ref["aspect_ratio_w_over_h"], 4),
                "aspect_ratio_pct": round(
                    (s["aspect_ratio_w_over_h"] / ref["aspect_ratio_w_over_h"] - 1) * 100, 2
                ),
                "top_to_bottom_width_ratio": round(
                    s["top_to_bottom_width_ratio"] - ref["top_to_bottom_width_ratio"], 4
                ),
                "widest_row_norm_from_top": round(
                    s["widest_row_norm_from_top"] - ref["widest_row_norm_from_top"], 4
                ),
                "fill_ratio_of_bbox": round(s["fill_ratio_of_bbox"] - ref["fill_ratio_of_bbox"], 4),
                "note": "aspect_ratio_pct beyond +/-5 is a visible proportion error; "
                        "widest_row shift beyond 0.05 changes where the mass reads",
            }

    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump(result, fh, indent=2)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
