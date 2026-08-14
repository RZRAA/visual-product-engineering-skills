---
name: asset-pipeline
description: Check that image, texture, model and icon assets meet the project's naming, resolution, format, budget and export conventions before they enter the repository. Use whenever adding, exporting, generating or reviewing art assets, textures, sprites, icons, app icons or 3D models, and whenever preparing an asset pack or build for a specific platform. Use it before committing any new asset and when a build is unexpectedly large or slow to load.
---

# Asset pipeline

Asset problems are cheap to prevent and expensive to discover. A wrongly named
texture, a 4096px icon, or an uncompressed PNG where a WebP belonged costs nothing
to fix on the day it is authored and costs a rebuild, a re-export and a scattered set
of reference updates three weeks later. This includes a cheap mechanical check, but profile defaults are heuristics rather
than universal project law. Run the checker, then interpret its findings against the
actual project and target platform.

## Run the checker first

```bash
python "$SKILL_DIR/scripts/check_assets.py" assets/ --profile mobile --json .visual/metrics/assets.json
```

Resolve `$SKILL_DIR` to the directory containing this `SKILL.md`; do not assume the
repository working directory contains `scripts/`. Profiles `mobile`, `desktop`,
`web`, `game-mobile`, and `game-desktop` provide starting heuristics. They are not
automatic acceptance criteria. Use `--strict-profile` only when the project has
adopted the selected profile/conventions as requirements. The checker reports
**ERROR / WARNING / INFO** so advisory optimisation findings do not fail an otherwise
valid asset.

## Naming

Pick the project's existing convention and hold to it; consistency matters more than
which convention it is. If none exists, `lowercase_snake_case` with a type suffix is
a defensible default:

```
crate_wooden_01_albedo.png
crate_wooden_01_normal.png
crate_wooden_01_roughness.png
icon_settings_24.svg
hero_banner_2x.webp
```

What actually causes trouble: spaces, capitals on case-sensitive build servers,
non-ASCII characters, scratch suffixes like `_draft_copy_2`, and inconsistent map
suffixes within one set (`_norm` in one place, `_normal` in another) which quietly
break automated material assignment.

## Resolution and density

- Provide the densities the platform expects: `@1x/@2x/@3x` for iOS, the `mdpi`
  through `xxxhdpi` ladder for Android, `1x/2x` for web.
- Do not ship an asset larger than its maximum display size. A 2048px image in a
  64px slot costs memory on every device that loads it, forever.
- Textures: prefer power-of-two **where the target engine/platform benefits from or requires it** for compression, mipmapping, streaming or compatibility. NPOT is not inherently a defect on modern pipelines; verify the actual target constraints.
- Icons: vector where the platform supports it. Rasterising a vector icon to one
  size is a decision that has to be remade at every future density.

## Format

| Use | Format |
|---|---|
| Photographic, web | WebP or AVIF; JPEG as fallback |
| Transparency, UI, screenshots | PNG, or WebP with alpha |
| Icons, logos, simple shapes | SVG |
| Game textures | Use the runtime/import format appropriate to the target engine and platform. Source PNG/TGA/etc. may be correct when the engine imports and compresses them for runtime; verify the built/runtime representation rather than banning source formats. |
| Animation | Sprite sheet or video, not a GIF, unless a GIF was specifically asked for |

Strip metadata on export. Camera EXIF, editor history and embedded colour profiles
add weight and occasionally leak file paths or location data.

## Budgets

State the budget before authoring, not after. Without a number, "too big" is an
opinion and the argument is unwinnable.

- Texture memory per scene or screen
- Triangle count per asset and per scene
- Material and draw-call count — on mobile this usually binds before triangles do
- Total bundle or download size
- Individual asset ceiling defined by the project/target. In the absence of a budget, large files may be flagged for review, but a heuristic threshold is not a failure criterion.

`render_turntable.py` writes `mesh_stats.json` with triangle, vertex and material
counts, which is the cheapest way to check a model against its budget.

## Texture sets

Every map in a set should share resolution and texel density unless there is a
stated reason — a 2048px albedo paired with a 512px normal produces detail that
appears and disappears with viewing distance.

Verify: correct normal-map channel convention for the engine, roughness and
metalness not accidentally inverted, alpha channel carrying real data rather than
fully opaque, and no visible tiling. `texture_check.py` in `visual-evidence-capture`
reports the last three directly.

## App icons and store assets

These have exact required sizes, and a build fails or a store submission is rejected
if one is missing. Generate the full set from one high-resolution master rather than
resizing by hand, keep the master in the repository, and check the safe area — most
platforms mask or round the corners, so detail near the edge disappears.

## Before committing

- Referenced from somewhere, or deliberately staged for imminent use
- Not a duplicate of an existing asset under a different name
- Source or master file preserved, or its absence noted
- Licence and provenance recorded for anything not authored in-house
- Not a temporary export that was never meant to ship

Orphaned assets accumulate silently and are the usual explanation for a bundle that
grew without anyone adding anything.

## Stop condition

Stop when no **project-defined hard error** remains, warnings have been assessed
against the actual target, every asset is referenced or deliberately staged as
appropriate, explicit budgets are met or an overrun is accepted, and required
provenance is recorded. Do not turn a generic profile heuristic into a task failure.
