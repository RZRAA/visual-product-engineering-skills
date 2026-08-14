---
name: visual-acceptance
description: Judge visual and spatial output from rendered evidence rather than from the code that produced it. Use whenever reviewing or accepting UI, screens, layouts, web or React interfaces, desktop and mobile apps, game UI or scenes, 3D assets, textures, object silhouettes, or generated and edited images. Use it before declaring a visual defect fixed, before accepting a screenshot or render, and whenever tempted to conclude that something looks right because the code says it should. Also use it when comparing output against a mock-up, reference or intended design.
---

# Visual acceptance

## The invariant

**See first. Explain second. See the whole state before fixing one part.**

Rendered evidence outranks implementation intent. The failure mode this exists to
prevent is reasoning backwards from the code to what the screen must look like —
which produces confident, fluent, wrong reviews.

- Mathematical centring does not prove visual centring.
- Expected transforms do not prove an object looks correctly positioned.
- A prompt containing the right nouns does not prove the image matches the request.
- A code change does not prove a visual defect is fixed.

If no rendered evidence exists, get some — use `visual-evidence-capture`. If it
genuinely cannot be produced, the correct output is UNVERIFIED, not a guess dressed
as a finding.

## Sequence

Observe → Sweep → Measure → Compare → Interpret → Batch → Act → Recheck.

The ordering carries the whole method. Jumping from observation straight to
explanation is what produces plausible causes for problems that were never
correctly described in the first place. Acting after the first visible defect is
the second failure mode: it creates avoidable `check → fix → check` loops and hides
related defects that could have been corrected together.

### Verification economy rule

**Resolve blockers serially. Resolve peer defects in batches.**

A **blocker** prevents meaningful downstream inspection: parse/build failure, app
not launching, capture unavailable, corrupt/missing data shape, or another defect
that makes later observations unreliable. Fix a blocker immediately and recheck.

A **peer defect** is independently observable from the same stable evidence state.
Do not edit after finding the first peer defect. Complete the sweep, inventory all
peer defects, group compatible corrections, then make one batch and recheck once.

### 1. Observe

Describe only what is visibly present, before any theory about why.

Good: "The action buttons sit high relative to the visual centre of the footer."
Good: "The lower third of the object is wider than in the reference."
Not yet: "The margin is wrong." / "The transform was applied twice."

Separate fact from judgement, state uncertainty plainly, and do not invent
precision. When configuration and visible evidence disagree, the evidence wins —
the disagreement is itself the finding.

### 2. Sweep

Before changing implementation, complete a whole-state review of everything that
can be judged from the current stable evidence. Do not stop inspection because one
defect has already been found.

Build a compact inventory:

```text
CURRENT DEFECT INVENTORY

Requirement failures
1. ...

Visual defects
1. ...
2. ...

Optional polish
1. ...
```

Exceptions: if the first defect is a blocker, resolve it before continuing because
the remaining state cannot yet be trusted.

### 3. Measure

Turn impressions into numbers wherever a script can do it. This is where a
text-based agent gains real advantage over eyeballing: it reads measurements well
even when it judges pixels poorly.

| Question | Tool |
|---|---|
| Did anything move, and where? | `compare_images.py` — SSIM, changed-region bbox |
| Is the spacing/alignment/contrast actually right? | `capture_web.py --probe` — real box geometry |
| Are the proportions right? | `silhouette.py` — aspect, mass bands, symmetry |
| Does the texture band or tile badly? | `texture_check.py` |
| Is the text legible? | `contrast.py` |

These diagnostics live in `visual-evidence-capture`. Resolve that skill's bundled resources relative to its own skill directory. Where no useful measurement is possible,
express relationships approximately and label them as approximate — an honest
estimate beats a fabricated figure.

### 4. Compare

State EXPECTED, ACTUAL, DELTA. "Looks wrong" is not a comparison and cannot be
acted on or verified by anyone else.

If EXPECTED is not written down anywhere, derive it explicitly from the reference
or brief before continuing, and say that is what you have done. Reviewing against
an unstated standard is how preference gets scored as failure.

### 5. Interpret

Only now open the implementation. Rank candidate causes — most likely, plausible
alternative, less likely — and prefer causes that directly explain the measured
delta rather than causes that are merely present in the code.

### 6. Batch

Group defects by root cause and compatibility before editing. Batch independent,
low-risk corrections discovered from the same evidence state. Do not combine
unrelated high-risk changes merely to reduce run count.

Examples that normally belong in one batch:
- several spacing/alignment adjustments from the same screenshot;
- multiple labels or clipping fixes;
- several style corrections whose causes are already understood;
- multiple acceptance defects corrected by one shared data-shape fix.

### 7. Act

Choose the smallest **batch of changes** that targets the inventoried discrepancies.
Preserve accepted parts, avoid unrelated refactors, avoid unsolicited redesign, and
keep above-spec polish separate from required corrections. Optional polish should
normally be consolidated into at most one polish pass unless iterative refinement
was explicitly requested.

### 8. Recheck

Recheck at a **meaningful verification boundary**, not automatically after every
low-risk edit. Capture again when:
- a blocker has been removed;
- a change invalidates the evidence or assumptions used for later diagnosis;
- a high-risk change could alter several downstream behaviours;
- a compatible fix batch is complete; or
- final visual acceptance is being established.

Prefer one capture that validates several fixes and criteria at once. Compare against
both the prior state and intended state, and inspect the changed region for collateral
regression.

An implementation change with no fresh evidence at the appropriate acceptance
boundary remains UNVERIFIED, not accepted.

### Two-cycle reset rule

After **two consecutive fix/recheck cycles on the same feature**, stop making isolated
corrections. Perform a fresh whole-state diagnostic sweep, rebuild the defect
inventory and reassess root causes before another edit. This prevents local patching
from replacing diagnosis.

## Classify every finding

Mixing these categories is what turns a review into an argument.

- **REQUIREMENT FAILURE** — violates the explicit task.
- **VISUAL DEFECT** — wrong relative to the intended output or reference.
- **QUALITY IMPROVEMENT** — optional polish, outside the agreed scope.
- **UNVERIFIED** — insufficient evidence to judge.

Design preference is not benchmark failure. If it was not asked for and is not
implied by the reference, it is a QUALITY IMPROVEMENT no matter how strongly held.

## Domain references

Load only the one that matches the surface under review:

- `references/ui-and-platform.md` — UI/UX heuristics plus web, React, Windows and
  mobile platform behaviour (breakpoints, safe areas, DPI, keyboard, states)
- `references/game-ui.md` — HUD and in-game interface under motion
- `references/3d-assets.md` — silhouette-first review order, proportion, materials,
  texture scale
- `references/image-generation.md` — generated and edited images, reference matching

## Report format

```
VISUAL REVIEW

Evidence:      <capture path, viewport/render settings>
Observation:   <what is visibly present>
Defect sweep:  <all requirement failures, peer defects, optional polish>
Measurement:   <numbers, with source script>
Expected:      <intended state, and where it comes from>
Actual:        <what rendered>
Delta:         <the concrete difference>
Likely causes: 1. ... 2. ...
Fix batch:      <compatible corrections grouped for one pass>
Correction:    <smallest batch targeting the deltas>
Recheck:       PASS / PARTIAL / FAIL / UNVERIFIED
```

## Stop condition

Stop when the requested visual outcome is evidenced, no requirement-level visual
defect remains, and everything still outstanding is explicitly labelled as optional
quality improvement. Continuing past that point is redesign, not acceptance.
