#!/usr/bin/env python3
"""Inspect a texture for tiling artefacts and pipeline compliance.

Usage:
    python texture_check.py IMAGE [IMAGE...] [--json OUT.json] [--tile-threshold 3.0]

This provides a heuristic signal for some forms of repetition by looking for dominant peaks in the row and
column frequency spectra: a texture that repeats every N pixels produces a spike
that stands well above the surrounding noise floor. It can miss visually obvious repetition and must not be used as proof that a texture is repetition-free.

Also reports the mechanical checks that are cheap to get wrong — resolution,
power-of-two compliance, whether the alpha channel actually carries data, and the
seam delta between opposite edges for textures intended to tile seamlessly.

Requires: pillow, numpy
"""
from __future__ import annotations

import argparse
import json
import os
import sys

try:
    import numpy as np
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Missing dependency. Install with: pip install pillow numpy")


def is_pow2(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def dominant_period(profile: np.ndarray, threshold: float):
    """Find a repeating period in a 1D intensity profile via its spectrum."""
    p = profile - profile.mean()
    if np.allclose(p, 0):
        return None
    spec = np.abs(np.fft.rfft(p))
    spec[0] = 0.0
    lo = 2  # ignore ultra-low frequencies (gradients, not tiling)
    hi = max(lo + 2, len(profile) // 8)  # periods under 8px are grain, not tiling
    band = spec[lo:hi]
    if band.size < 4:
        return None
    peak_idx = int(np.argmax(band)) + lo
    peak = spec[peak_idx]
    noise = float(np.median(band[band > 0])) if (band > 0).any() else 0.0
    if noise <= 0:
        return None
    ratio = float(peak / noise)
    if ratio < threshold:
        return None
    return {
        "period_px": round(len(profile) / peak_idx, 2),
        "repeats_across_image": peak_idx,
        "peak_to_noise_ratio": round(ratio, 2),
    }


def seam_delta(arr: np.ndarray) -> dict:
    """Mean intensity difference between opposite edges — high values mean a visible seam when tiled."""
    left, right = arr[:, 0].astype(float), arr[:, -1].astype(float)
    top, bottom = arr[0, :].astype(float), arr[-1, :].astype(float)
    return {
        "horizontal_seam_delta": round(float(np.abs(left - right).mean()), 2),
        "vertical_seam_delta": round(float(np.abs(top - bottom).mean()), 2),
    }


def inspect(path: str, threshold: float) -> dict:
    img = Image.open(path)
    w, h = img.size
    gray = np.asarray(img.convert("L"), dtype=np.float64)

    row_profile = gray.mean(axis=1)  # varies down the image -> horizontal banding
    col_profile = gray.mean(axis=0)  # varies across the image -> vertical banding

    alpha_used = False
    if img.mode in ("RGBA", "LA"):
        a = np.asarray(img.convert("RGBA"))[..., 3]
        alpha_used = bool(a.min() < 250)

    out = {
        "file": path,
        "size": [w, h],
        "mode": img.mode,
        "format": img.format,
        "file_size_kb": round(os.path.getsize(path) / 1024, 1),
        "power_of_two": is_pow2(w) and is_pow2(h),
        "square": w == h,
        "alpha_channel_carries_data": alpha_used,
        "mean_luminance": round(float(gray.mean()), 2),
        "luminance_range": [round(float(gray.min()), 1), round(float(gray.max()), 1)],
        "contrast_std": round(float(gray.std()), 2),
        "vertical_banding": dominant_period(col_profile, threshold),
        "horizontal_banding": dominant_period(row_profile, threshold),
        "seam": seam_delta(gray),
    }

    flags = []
    if not out["power_of_two"]:
        flags.append("not power-of-two — advisory: verify whether the target pipeline benefits from or requires POT textures")
    if out["vertical_banding"]:
        flags.append(
            f"possible vertical repetition signal around ~{out['vertical_banding']['period_px']}px"
        )
    if out["horizontal_banding"]:
        flags.append(
            f"possible horizontal repetition signal around ~{out['horizontal_banding']['period_px']}px"
        )
    if img.mode in ("RGBA", "LA") and not alpha_used:
        flags.append("alpha channel present but fully opaque — wasted memory, drop to RGB")
    if out["contrast_std"] < 6:
        flags.append("very low contrast — may read as flat at texel density")
    if out["seam"]["horizontal_seam_delta"] > 20 or out["seam"]["vertical_seam_delta"] > 20:
        flags.append("high edge delta — will show a seam if tiled")
    out["flags"] = flags
    out["interpretation"] = "Diagnostic heuristics only; visually inspect the texture and any tiled material before acceptance."
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Texture inspection")
    ap.add_argument("images", nargs="+")
    ap.add_argument("--tile-threshold", type=float, default=6.0,
                    help="peak-to-noise ratio above which repetition is reported")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    results = [inspect(p, args.tile_threshold) for p in args.images]
    payload = results[0] if len(results) == 1 else {"textures": results}
    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump(payload, fh, indent=2)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
