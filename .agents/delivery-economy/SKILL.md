---
name: delivery-economy
description: Optimise the final hand-off from the recipient's point of view — execution friction, dependency burden, package cleanliness, artefact count and runtime economy. Use whenever producing a ZIP, build, executable, release, deployable, asset pack, review package or anything handed to someone else to run. Use it before declaring a package ready, and whenever claiming a deliverable is complete, self-contained or ready to ship.
---

# Delivery economy

## The principle

**Judge the delivery from the recipient's perspective**, not from the size of the
artefact or the effort that went into it.

A 5 KB source package requiring a runtime the recipient does not have has more
friction than a 60 MB self-contained executable. A 70 MB single binary is cleaner
than a 70 MB folder holding hundreds of loose runtime files. Optimise the experience
of receiving it.

## 1. Execution friction

- How many steps from extraction to working software?
- Is the launch path obvious without being told?
- Does the README describe what is actually in the package?
- Are prerequisites explicit, and can the intended recipient reasonably meet them?

Prefer `extract → launch` whenever instant execution was requested.

## 2. Dependency burden

Identify every runtime, package manager, external tool, environment variable, API
key and OS feature required, and mark each mandatory or optional.

Do not claim "no installation required" if a runtime must already be present. That
claim is checked in the first thirty seconds and its failure colours everything else
in the hand-off.

## 3. Package cleanliness

Remove unless genuinely required: debug symbols and PDBs, logs, caches, temporary
and intermediate outputs, local machine metadata, unused assets, duplicate
libraries, editor and vendor tool folders, secrets and credentials, stale generated
files.

Inspect names and structure, not only source. A path containing a personal username
or an internal hostname is a hygiene failure regardless of what the file does.

## 4. Artefact economy

- Can many loose files become one clean executable or archive?
- Is every file needed to run, review or modify the project?
- Are source and runtime artefacts clearly separated?

Do not collapse files if it harms the reviewability the recipient actually needs.

## 5. Runtime economy

Distinct from packaging: unnecessary network requests, duplicate API calls, repeated
geolocation, excessive polling, unnecessary workers, process spawning where a native
API exists, duplicate asset loading, repeated computation, oversized media and
textures, redundant state, needless refresh frequency.

## 6. Appropriate reproducibility

Require only the level the task actually calls for. If source review was requested,
preserve enough source and configuration. If a runnable binary was requested,
prioritise runnability. If a reproducible release was required, preserve the exact
build configuration. Do not invent reproducibility requirements that nobody asked
for — they are expensive and they look like diligence, which is why they persist.

## 7. Avoid double-counting

Categorise each issue once unless distinct impacts are demonstrated:
- hundreds of loose files → package cleanliness / artefact economy
- redundant HTTP requests → runtime economy / code design
- missing runtime → execution friction / dependency burden


## 8. Consolidated pre-package pass

Do not repeatedly rebuild or repackage after each small cleanup unless packaging
itself is the defect under test. Once implementation acceptance is stable, perform
one consolidated pre-package pass:

1. remove debug/QA hooks and temporary instrumentation;
2. remove logs, caches and intermediate files;
3. verify README/prerequisites against the final contents;
4. scan hygiene/anonymisation requirements;
5. create the package once;
6. perform one final smoke/integrity check on that exact package.

If the final smoke check exposes a package-specific blocker, fix it and rebuild.
Do not otherwise churn the release artefact for optional polish.

## Release check

```
DELIVERY REVIEW
Execution path:     ...
Prerequisites:      ...
Required files:     ...
Unnecessary files:  ...
Package structure:  ...
Runtime issues:     ...
Hygiene:            ...
Recipient friction: LOW / MEDIUM / HIGH
Result:             PASS / PASS WITH NOTES / FAIL
```

## Stop condition

Stop when the package contains what the recipient needs, omits unnecessary, private
and debug artefacts, has an obvious use path, documents prerequisites accurately,
and carries no avoidable friction that materially affects the task.
