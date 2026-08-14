---
name: design-system-conformance
description: Check that UI work uses the project's existing design tokens, components and spacing scale instead of introducing new one-off values. Use whenever adding or modifying a screen, component or style, whenever a colour, spacing, radius, shadow or font size is about to be written as a literal, and whenever reviewing UI for consistency with the rest of the product. Use it before accepting any new component, and when a screen looks subtly different from its neighbours without an obvious cause.
---

# Design system conformance

Visual drift almost never arrives as one bad decision. It arrives as fifty
reasonable ones — a `16px` here, a slightly different green there — each defensible
alone and collectively producing a product that looks assembled rather than
designed. A screenshot review will not catch it, because every individual screen
looks fine. Only comparison against the token set catches it.

## 1. Find the system before writing any style

Do this before adding a single literal value. Look for, in rough order of authority:

- a token file — `tokens.json`, `theme.ts`, `tailwind.config.*`, `_variables.scss`,
  a `:root` custom-property block, a `ThemeData`, a `Resources.xaml`
- an existing component that already does something similar
- the spacing values actually in use across neighbouring files
- brand or style documentation in the repository

If no system exists, say so explicitly and use the values already most common in the
codebase rather than inventing a parallel set. Consistency with an unwritten
convention still beats a second convention.

## 2. Resolve every value to a token

For each of these, name the token you are using. If you cannot name one, that is the
finding — surface it rather than quietly writing a literal.

| Property | Typical question |
|---|---|
| Colour | Is this `primary`, `surface`, `muted`, or a new colour nobody approved? |
| Spacing | Does this fall on the scale (4/8/12/16/24…), or between steps? |
| Radius | Does the project have `sm/md/full`, and does this match a sibling component? |
| Shadow / elevation | Is this an existing level or a bespoke blur? |
| Font size and weight | Is this a defined text style, or a one-off? |
| Line height | Consistent with the type scale? |
| Border width | One value across the product, usually. |
| Motion duration and easing | Almost always a system value; almost always ignored. |
| Z-index / layering | Is there an ordering convention to respect? |
| Icon size and stroke | Mixed stroke weights are highly visible and rarely intended. |

## 3. Reuse before creating

Before building a new component, check whether an existing one covers the case with
a prop, a variant, or a small extension. Two components that do nearly the same
thing will diverge — that is not a risk, it is a certainty, and the divergence lands
on whoever maintains the product later.

When creating is genuinely right, match the conventions of its neighbours: file
location, naming, prop shape, variant naming, how it accepts styling overrides.

## 4. Report conformance findings

Keep a literal value only when there is a stated reason. Report each exception:

```
TOKEN CONFORMANCE
Conforming:   <values resolved to existing tokens>
New literals: <value, location, and why no token fits>
Proposed:     <new token needed, or the existing token that should be used instead>
Near-misses:  <values close to a token but not on it — usually accidental>
```

Near-misses are the most useful line in that report. A `15px` next to a `16px` token,
or `#1F4D3B` next to `#1F4D3A`, is nearly always a copy error rather than a decision,
and it is invisible to the eye but obvious in the token check.

## 5. Verify what rendered, not what was written

A token reference is not a rendered result. Opacity, blend modes, overlays, inherited
colour, dark-mode overrides and platform theming all sit between the token and the
pixel. Capture the screen and probe it — `visual-evidence-capture` reports the
resolved styles and a diagnostic contrast estimate. For simple opaque text/background
pairs this can be strong evidence; for translucency, gradients, imagery, shadows or
multi-colour content, confirm with direct rendered inspection or a more appropriate
accessibility tool.

This is where token conformance and accessibility meet: a pair of approved tokens can
still fail contrast once one is composited over the other at 60% opacity, and the
code review will pass it every time.

## 6. Themes and colour modes

If the project **supports or requires multiple themes or colour modes**, verify each
supported mode independently and use the project's existing theme tokens. Do not
introduce a dark mode, light mode or additional theme solely because this skill is
running. A missing theme is a requirement failure only when the project or task says
that theme should exist.

## Stop condition

Stop when values relevant to the requested change resolve to existing project tokens
or stated exceptions, no material near-miss remains unexplained, the rendered result
has been checked rather than inferred, and genuinely new tokens are proposed rather
than silently introduced. Do not fail a task for a design-system rule the project
does not actually have.
