#!/usr/bin/env python3
"""Inspect an asset directory for mechanical problems and advisory pipeline risks.

Usage:
    python check_assets.py PATH [--profile mobile] [--strict-profile]
                                [--json OUT.json] [--max-kb 2048]
                                [--naming snake|kebab|any] [--quiet]

Profiles are starting heuristics, not universal acceptance criteria. By default,
profile/naming/budget findings are WARNINGs. Use --strict-profile only when the
selected profile and conventions have been adopted as project requirements.

Hard ERRORs are reserved for conditions that prevent reliable inspection (for
example an unreadable image), plus selected profile violations when strict mode is
explicitly requested.

Requires: pillow
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Missing dependency. Install with: pip install pillow")

PROFILES = {
    "mobile": {"max_edge": 2048, "max_kb": 1024, "prefer": {".webp", ".png", ".svg"},
               "discourage": {".bmp", ".tiff", ".gif"}, "prefer_pow2": False},
    "desktop": {"max_edge": 4096, "max_kb": 4096, "prefer": {".png", ".webp", ".svg"},
                "discourage": {".bmp", ".tiff"}, "prefer_pow2": False},
    "web": {"max_edge": 2560, "max_kb": 512, "prefer": {".webp", ".avif", ".svg"},
            "discourage": {".bmp", ".tiff", ".png"}, "prefer_pow2": False},
    "game-mobile": {"max_edge": 2048, "max_kb": 2048, "prefer": {".png", ".ktx2", ".astc"},
                    "discourage": {".bmp", ".gif"}, "prefer_pow2": True},
    "game-desktop": {"max_edge": 4096, "max_kb": 8192, "prefer": {".png", ".dds", ".ktx2"},
                     "discourage": {".bmp", ".gif"}, "prefer_pow2": True},
}

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif", ".gif", ".avif"}
MODEL_EXT = {".glb", ".gltf", ".fbx", ".obj", ".blend", ".usdz"}
VECTOR_EXT = {".svg"}

NAMING = {
    "snake": re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$"),
    "kebab": re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$"),
    "any": re.compile(r"^[^/\\]+$"),
}
VERSION_JUNK = re.compile(r"(final|copy|new|old|temp|tmp|untitled|v\d+|\(\d+\))", re.I)
DENSITY_SUFFIX = re.compile(r"@[234]x$|_[234]x$")


def is_pow2(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def digest(path: str) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def add(entry: dict, severity: str, code: str, message: str, source: str = "mechanical") -> None:
    entry["findings"].append({
        "severity": severity,
        "code": code,
        "source": source,
        "message": message,
    })


def convention_severity(strict: bool) -> str:
    return "ERROR" if strict else "WARNING"


def check_naming(entry: dict, stem: str, style: str, strict: bool) -> None:
    sev = convention_severity(strict)
    base = DENSITY_SUFFIX.sub("", stem)
    if style != "any" and not NAMING[style].match(base):
        add(entry, sev, "naming_convention", f"name does not match {style}-case convention", "project/profile convention")
    if " " in stem:
        add(entry, sev, "name_spaces", "name contains spaces", "project/profile convention")
    if any(ord(c) > 127 for c in stem):
        add(entry, "WARNING", "name_non_ascii", "name contains non-ASCII characters; verify target/toolchain compatibility", "compatibility heuristic")
    if VERSION_JUNK.search(stem):
        add(entry, "WARNING", "scratch_name", "name contains scratch wording (final, copy, temporary…)", "hygiene heuristic")


def inspect(path: str, profile_name: str | None, naming: str, max_kb_override: int, strict: bool) -> dict:
    profile = PROFILES.get(profile_name) if profile_name else None
    ext = os.path.splitext(path)[1].lower()
    stem = os.path.splitext(os.path.basename(path))[0]
    size_kb = round(os.path.getsize(path) / 1024, 1)
    entry = {"file": path, "ext": ext, "size_kb": size_kb, "findings": []}
    check_naming(entry, stem, naming, strict)

    if ext in VECTOR_EXT:
        entry["kind"] = "vector"
    elif ext in MODEL_EXT:
        entry["kind"] = "model"
    elif ext in IMAGE_EXT:
        entry["kind"] = "image"
        try:
            with Image.open(path) as img:
                w, h = img.size
                entry.update({"size": [w, h], "mode": img.mode, "format": img.format})
                entry["power_of_two"] = is_pow2(w) and is_pow2(h)
                if img.mode in ("RGBA", "LA"):
                    alpha = img.convert("RGBA").getchannel("A")
                    entry["alpha_carries_data"] = alpha.getextrema()[0] < 250
                    if not entry["alpha_carries_data"]:
                        add(entry, "INFO", "opaque_alpha", "alpha channel is fully opaque; RGB may reduce storage/runtime memory depending on the pipeline", "optimisation heuristic")
                if profile:
                    sev = convention_severity(strict)
                    if max(w, h) > profile["max_edge"]:
                        add(entry, sev, "profile_max_edge", f"{w}x{h} exceeds {profile_name} heuristic max edge {profile['max_edge']}px", "profile heuristic")
                    if profile["prefer_pow2"] and not entry["power_of_two"]:
                        add(entry, sev, "profile_pow2", "NPOT texture: verify whether the target engine/platform benefits from or requires power-of-two dimensions for compression, mipmaps or streaming", "profile heuristic")
                    if ext in profile["discourage"]:
                        pref = "/".join(sorted(profile["prefer"]))
                        add(entry, sev, "profile_format", f"{ext} is discouraged by the {profile_name} heuristic; consider {pref} if appropriate to the actual pipeline", "profile heuristic")
        except Exception as exc:
            add(entry, "ERROR", "unreadable_image", f"unreadable image: {exc}")
    else:
        entry["kind"] = "other"

    ceiling = max_kb_override or (profile["max_kb"] if profile else 0)
    if ceiling and size_kb > ceiling:
        sev = convention_severity(strict) if profile and not max_kb_override else ("ERROR" if strict else "WARNING")
        source = "explicit/profile budget" if strict else "size heuristic"
        add(entry, sev, "size_ceiling", f"{size_kb} KB exceeds {'explicit' if max_kb_override else profile_name} ceiling {ceiling} KB", source)

    # Backwards-friendly text list, while structured findings carry the semantics.
    entry["issues"] = [f"{f['severity']}: {f['message']}" for f in entry["findings"]]
    return entry


def main() -> int:
    ap = argparse.ArgumentParser(description="Asset pipeline diagnostic check")
    ap.add_argument("path")
    ap.add_argument("--profile", choices=sorted(PROFILES), help="optional advisory profile")
    ap.add_argument("--strict-profile", action="store_true", help="treat selected profile/naming/budget conventions as hard project requirements")
    ap.add_argument("--naming", default="any", choices=sorted(NAMING), help="project naming convention; default 'any' avoids inventing one")
    ap.add_argument("--max-kb", type=int, default=0, help="explicit per-file ceiling; advisory unless --strict-profile")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.path):
        sys.exit(f"Path does not exist: {args.path}")

    files = []
    if os.path.isfile(args.path):
        files = [args.path]
    else:
        for root, dirs, names in os.walk(args.path):
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__"}]
            files += [os.path.join(root, n) for n in names if not n.startswith(".")]

    entries = [inspect(f, args.profile, args.naming, args.max_kb, args.strict_profile) for f in files]
    entries = [e for e in entries if e["kind"] != "other" or e["findings"]]

    by_hash = defaultdict(list)
    for e in entries:
        try:
            by_hash[digest(e["file"])].append(e["file"])
        except OSError:
            continue
    duplicates = [paths for paths in by_hash.values() if len(paths) > 1]

    findings = [f for e in entries for f in e["findings"]]
    error_count = sum(1 for f in findings if f["severity"] == "ERROR")
    warning_count = sum(1 for f in findings if f["severity"] == "WARNING") + len(duplicates)
    info_count = sum(1 for f in findings if f["severity"] == "INFO")

    if error_count:
        result = "FAIL"
    elif warning_count:
        result = "PASS_WITH_WARNINGS"
    else:
        result = "PASS"

    report = {
        "path": args.path,
        "profile": args.profile,
        "strict_profile": args.strict_profile,
        "profiles_are_advisory_unless_strict": True,
        "naming_convention": args.naming,
        "explicit_size_ceiling_kb": args.max_kb or None,
        "files_checked": len(entries),
        "total_kb": round(sum(e["size_kb"] for e in entries), 1),
        "errors": error_count,
        "warnings": warning_count,
        "info": info_count,
        "duplicate_content": duplicates,
        "duplicate_content_severity": "WARNING",
        "largest": sorted(
            ({"file": e["file"], "size_kb": e["size_kb"]} for e in entries),
            key=lambda x: -x["size_kb"],
        )[:10],
        "assets_with_findings": [e for e in entries if e["findings"]],
        "clean": [e["file"] for e in entries if not e["findings"]],
        "result": result,
    }

    if args.json_out:
        os.makedirs(os.path.dirname(args.json_out) or ".", exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    if not args.quiet:
        print(json.dumps(report, indent=2))
    return 1 if result == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
