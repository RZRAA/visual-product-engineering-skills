# Visual and Product Engineering Skills

Reusable agent skills for building, reviewing and shipping software with strong
visual and product quality.

## Quick start

Each folder under `.agents/` is an independent skill. Copy the skill folders you
want into the skill directory used by your agent harness:

```text
your-project/
  .agents/
    skills/
      visual-evidence-capture/
      visual-acceptance/

personal-skill-root/
  visual-evidence-capture/
```

For a repository-scoped setup, copy from this package's `.agents/<skill-name>/`
to `your-project/.agents/skills/<skill-name>/`. For a personal setup, copy the
same folder into your harness's personal skill root. Keep each `SKILL.md` with
its adjacent `scripts/` and `references/` folders.

Once installed, ask your agent to use a skill by name, for example:

```text
Use visual-evidence-capture to inspect this screen, then use visual-acceptance
to judge it against the reference.
```

The skills are independent, so install only the ones useful to your workflow.

## Included skills

| Skill | What it does |
| --- | --- |
| `minimum-complete-solution` | Keeps the implementation as simple as possible while still meeting the real requirements. |
| `design-system-conformance` | Checks that UI work follows the project's existing tokens, components and spacing conventions. |
| `visual-evidence-capture` | Captures screenshots and renders, then measures geometry, diffs, silhouettes, textures and contrast where useful. |
| `visual-acceptance` | Reviews visual and spatial output from rendered evidence rather than implementation intent. |
| `semantic-acceptance` | Verifies that the delivered behaviour and artefacts satisfy the stated acceptance criteria. |
| `asset-pipeline` | Checks asset naming, resolution, formats, budgets and export conventions. |
| `delivery-economy` | Improves hand-off quality by reducing execution friction, unnecessary dependencies and package clutter. |

## Useful sequences

For a visual feature:

```text
minimum-complete-solution → design-system-conformance →
visual-evidence-capture → visual-acceptance → semantic-acceptance →
delivery-economy
```

For asset work:

```text
minimum-complete-solution → visual-evidence-capture → visual-acceptance →
asset-pipeline → delivery-economy
```

For non-visual work:

```text
minimum-complete-solution → semantic-acceptance → delivery-economy
```

## Optional dependencies

The prose skills do not require extra packages. The bundled helper scripts may
use the following tools:

- Python with `Pillow` and `numpy` for image and asset checks.
- Playwright and its Chromium browser for web capture.
- `adb` and an available Android device or emulator for Android capture.
- Blender on `PATH` for turntable renders.
- Windows PowerShell for desktop window capture on Windows.

Install only the dependencies for the scripts you plan to run. Resolve bundled
paths relative to the skill folder containing the relevant `SKILL.md`; do not
assume the current project directory contains the scripts.

## Evidence and acceptance

Rendered screenshots and images are the primary evidence for appearance.
Measurements are diagnostic aids and should not overrule what is visibly present.
When the required evidence cannot be produced, report the result as
`UNVERIFIED` rather than inferring success from the source code.

## Package layout

```text
.agents/
  asset-pipeline/
    SKILL.md
    scripts/
  delivery-economy/
    SKILL.md
  design-system-conformance/
    SKILL.md
  minimum-complete-solution/
    SKILL.md
  semantic-acceptance/
    SKILL.md
  visual-acceptance/
    SKILL.md
    references/
  visual-evidence-capture/
    SKILL.md
    scripts/
```

The `SKILL.md` frontmatter contains only the discovery name and description
needed by compatible harnesses. No personal or project-specific information is
required to use the package.
