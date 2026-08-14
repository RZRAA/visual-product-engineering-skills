---
name: semantic-acceptance
description: Verify that an implementation actually satisfies the requested outcome, using observed evidence rather than implementation intent. Use whenever explicit acceptance criteria exist, whenever closing out a task or phase, whenever external APIs or data are involved, whenever output must meet a count, state or behaviour, and whenever a package must be shown to run. Use it before reporting anything as done or complete, and especially when tempted to accept a result because the code plainly looks correct.
---

# Semantic acceptance

## The invariant

**Implementation intent is not acceptance evidence.**

The code describes what was asked of the machine. Acceptance is about what the
machine did. These come apart constantly, and fluent reporting hides the gap:

- `Take(7)` does not prove seven values were returned.
- HTTP 200 does not prove the payload is correct.
- A function being called does not prove it succeeded.
- An element being created does not prove correct placement.
- A CSS rule does not prove correct rendering.
- A test existing does not prove it passed.
- A file being written does not prove the package launches.
- A generated model existing does not prove resemblance to the reference.
- A prompt mentioning a subject does not prove the image depicts it.

## Procedure

### 1. Extract the criteria

Separate mandatory behaviours, mandatory artefacts, constraints, quality
preferences and optional enhancements. Do not invent additional mandatory
requirements — a review that grows the specification is not a review.

### 2. Map each criterion to observable evidence

The test is whether the evidence could have come out differently. Restating the
implementation cannot fail, so it proves nothing.

| Weak (restates implementation) | Strong (observable) |
|---|---|
| "The API asks for seven days." | "The response contains seven distinct forecast dates." |
| "The code has an async handler." | "The UI stayed responsive during a 3s delayed request." |
| "Alignment is set to centre." | "The probe reports 0.5px offset from parent centre." |
| "The export step runs." | "The output directory contains the 4 expected files." |

### 3. Verify independently

Prefer, in order: actual output, actual response shape, running the artefact,
inspecting the generated file, rendered evidence, count and state checks.

If independent verification is impossible, the status is UNVERIFIED. Not PASS.
An honest UNVERIFIED is useful information; a false PASS destroys the value of
every other status in the report.

### 4. Record an acceptance matrix

| Requirement | Implementation | Verification method | Observed evidence | Status |
|---|---|---|---|---|
| ... | ... | ... | ... | PASS / FAIL / PARTIAL / UNVERIFIED |

- **PASS** — demonstrated by evidence.
- **FAIL** — contradicted by evidence.
- **PARTIAL** — demonstrated in part; state which part.
- **UNVERIFIED** — insufficient evidence; state what would settle it.

Do not downgrade compliance because an optional feature is absent. Do not upgrade
non-compliance because the code is elegant.


## Verification economy

Acceptance should be rigorous without becoming one-test-per-criterion ceremony.

- Prefer one verification run that exercises and proves multiple criteria at once.
- Group checks by evidence source: one settled UI render may prove launch, visible
  data, record count, layout and clipping together; separate checks are only needed
  for behaviours that render evidence cannot prove.
- Resolve blockers serially when they invalidate downstream evidence.
- For non-blocking peer failures discovered from the same run, record the full
  acceptance gap first, batch compatible fixes, then re-run the shared verification.
- Do not re-run an unchanged check merely because another criterion was documented.
- After two consecutive fix/recheck cycles on the same feature, perform a fresh
  whole-state acceptance sweep before further isolated fixes.

The goal is **maximum acceptance coverage per meaningful run**, not maximum run count.

## Domain checks

**APIs and data** — verify actual record counts, date ranges, required fields
present, fallback behaviour, error behaviour and returned semantics. Never infer
endpoint behaviour from a parameter name or a limit argument.

**Visual requirements** — use rendered evidence and invoke `visual-acceptance`.
Verify the visible result, not the layout intent that was supposed to produce it.

**Generated images and 3D** — verify required subjects present, prohibited content
absent, composition and proportion requirements met, reference similarity where
required, and actual usability for the stated purpose.

**Packaging and execution** — verify expected files present, prohibited files
absent, the launch path works or is demonstrably reproducible, prerequisites match
the documentation, and package contents match the README.

## Anti-drift

Do not broaden acceptance criteria during review. Above-spec ideas are recorded as
**OPTIONAL QUALITY IMPROVEMENT** and are never scored as failures. This matters more
than it sounds: scope that grows during acceptance makes completion unreachable, and
teaches everyone downstream to discount the review.

## Stop condition

Stop when every explicit criterion is PASS, or is reported as FAIL, PARTIAL or
UNVERIFIED with the supporting evidence and what would resolve it.
