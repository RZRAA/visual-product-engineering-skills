---
name: visual-evidence-capture
description: Produce and measure visual evidence — screenshots, renders, DOM geometry, image diffs, silhouette and texture diagnostics — so visual claims can be verified instead of inferred from implementation intent. Use this whenever a task involves UI, a screen, a layout, a rendered scene, a 3D asset, a texture, or a generated image and you need to prove what it actually looks like. Use it before closing any visual defect, before saying a visual fix worked, and whenever you are about to describe something visual you have not actually looked at. Also use it when a visual review would otherwise have to be reported as UNVERIFIED.
---

# Visual evidence capture

Most visual failures in agent work come from a single move: describing a rendered
result from the code that was supposed to produce it. This skill exists to make that
move unnecessary. Before reasoning about what something looks like, produce an
artefact that shows it, and where possible produce numbers that describe it.

Measurements are useful because they make some visual relationships reproducible, but
they are not a substitute for looking. The strategy is: **capture, inspect, measure
where useful, then reason from the combined evidence.**


## Bundled resource resolution

Resolve every bundled `scripts/` or `references/` path relative to **this skill's
directory** (the directory containing this `SKILL.md`). Do not assume the repository
working directory is the skill directory. In examples, `$SKILL_DIR` means that
directory; substitute the actual installed skill path supplied or discoverable by the
harness.

## Evidence directory

Write all evidence under a predictable path so later steps and other skills can find it:

```
.visual/<task-id>/
  before/          state prior to the change
  after/           state following the change
  reference/       mock-ups, references, intended state
  metrics/         JSON output from the measurement scripts
```

Keep filenames descriptive and stable across runs (`settings-screen-390x844.png`,
not `shot3.png`). Stable names make before/after diffing trivial.

## Step 1 — Capture

Pick the capture path that matches the surface. If a capture path is genuinely
unavailable, say so explicitly and mark the finding UNVERIFIED — do not substitute
an inference about the code.

| Surface | Command |
|---|---|
| Web / React / any localhost URL | `python "$SKILL_DIR/scripts/capture_web.py" <url> --out .visual/<task>/after --viewports 390x844,768x1024,1440x900` |
| React Native / Expo (web target) | `npx expo start --web`, then `capture_web.py` against the dev URL |
| Android device or emulator | `bash "$SKILL_DIR/scripts/capture_android.sh" .visual/<task>/after/screen.png` |
| iOS simulator | `xcrun simctl io booted screenshot .visual/<task>/after/screen.png` |
| Windows desktop app | `powershell -File "$SKILL_DIR/scripts/capture_window.ps1" -WindowTitle "<title>" -Out .visual/<task>/after/app.png` |
| 3D asset (Blender) | `blender -b <file.blend> -P "$SKILL_DIR/scripts/render_turntable.py" -- --out .visual/<task>/after --frames 8` |
| Game build | use the engine's headless/screenshot command; fall back to `capture_window.ps1` on a running build |
| Generated image | already a file — copy it into the evidence directory and go to Step 2 |

Multiple captures of the same thing (a turntable, a breakpoint sweep, a state matrix)
should be collapsed into one image before review:

```bash
python "$SKILL_DIR/scripts/contact_sheet.py" .visual/<task>/after/*.png --out .visual/<task>/after/_sheet.png --labels
```

One contact sheet costs far less context than eight separate images, and it makes
inconsistency across the set immediately visible.

**Then actually look at the file.** A capture that is never viewed is not evidence.
If the harness can read images, read them. If it cannot, measurement scripts can
verify only the criteria they directly represent. They do **not** become a general
replacement for visual inspection; every appearance-only finding that the metrics do
not directly prove stays UNVERIFIED.

## Step 2 — Measure

Measurements can turn a specific relationship such as padding asymmetry into reproducible diagnostic evidence. Run
whichever apply and save the JSON into `.visual/<task>/metrics/`.

**Compare two images** (after vs before, or after vs reference):
```bash
python "$SKILL_DIR/scripts/compare_images.py" before/screen.png after/screen.png --json metrics/diff.json --heatmap metrics/diff.png
```
Reports SSIM, perceptual hash distance, changed-pixel percentage, and the bounding
box of the changed region. The bounding box is the useful part: it tells you whether
a change landed where it was supposed to, and whether anything else moved.

**Measure real DOM geometry** (web/React — far more reliable than reading CSS):
```bash
python "$SKILL_DIR/scripts/capture_web.py" <url> --probe ".btn-primary,.footer,header nav" --json metrics/layout.json
```
Returns per-selector box, computed padding/margin asymmetry, optical vs mathematical
centre offset, overflow and clipping flags, and contrast ratio against the resolved
background. Use these numbers rather than asserting from the stylesheet.

**Measure a 3D asset or object silhouette:**
```bash
python "$SKILL_DIR/scripts/silhouette.py" after/turntable_00.png --json metrics/silhouette.json
```
Returns bounding box, aspect ratio, mass centroid, top/mid/bottom width ratios and
symmetry error. Silhouette is judged before detail, so these numbers are the first
thing to check on an asset — and comparing the same metrics against a reference
render is the most objective proportion check available.

**Check a texture:**
```bash
python "$SKILL_DIR/scripts/texture_check.py" texture_albedo.png --json metrics/texture.json
```
Uses frequency analysis to flag possible tiling bands and reports resolution, power-of-two status, alpha usage, seam deltas and colour range. Frequency results are heuristic: absence of a flag does not prove a texture has no visible repetition.

**Check text contrast** on any captured screen region:
```bash
python "$SKILL_DIR/scripts/contrast.py" after/screen.png --region 24,180,366,240 --json metrics/contrast.json
```


## Measurement interpretation guardrail

Treat script output as **diagnostic evidence**, not automatic acceptance truth.

- DOM geometry is strong evidence for box position/size, but not for perceived visual quality.
- Contrast calculated from computed colours or pixel clustering is an estimate when
  translucency, gradients, shadows, images or several foreground colours are present.
- Frequency analysis can detect some repetition but can miss visually obvious tiling.
- SSIM and changed-pixel metrics show difference, not whether the difference is good.
- Silhouette metrics describe shape properties, not style quality by themselves.

If a metric and direct visual evidence disagree, investigate the mismatch. Do not
discard a visible defect solely because a heuristic metric passes.

## Step 3 — Report

State the capture path used so the evidence is reproducible. Report relevant measurements alongside, not above, direct visual observation:

```
EVIDENCE
Captured: .visual/t-114/after/settings-390x844.png (Playwright, 390x844, DPR 2)
Compared against: .visual/t-114/reference/settings-mock.png

Measured:
- SSIM 0.83; changed region bbox (24,412)-(366,498)
- .btn-primary left padding 24px, right padding 16px (asymmetry 8px)
- Text contrast 3.1:1 against #F5EFE6 (below 4.5:1)

Unmeasured / by eye:
- Header spacing reads tighter than the reference

Verdict: PASS / PARTIAL / FAIL / UNVERIFIED
```

Keep measured facts separate from impressions. Both are legitimate; conflating them
is what makes a review unfalsifiable.

## Recheck discipline

A visual defect cannot be closed because the implementation changed. Capture again
after the change, compare against the before state, and confirm two things: the target
issue moved in the right direction, and the changed-region bounding box does not
extend into areas that were already accepted. Collateral regression is the most common
thing an agent misses, and the diff bounding box catches it almost for free.

If a recheck capture cannot be produced, report the change as UNVERIFIED. That is an
honest and useful status. A false PASS is not.

## Dependencies

Capture scripts need Playwright (`pip install playwright && playwright install chromium`)
for web, `adb` for Android, Blender on PATH for renders. Measurement scripts need only
Pillow and numpy. Each script prints an explicit install hint if a dependency is
missing, so a missing tool surfaces as a clear message rather than a silent skip.
