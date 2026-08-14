# UI/UX and platform reference

Load when reviewing app screens, web/React interfaces, Windows desktop apps or
mobile apps. Judge what renders, not the properties intended to produce it.

## Contents
1. Core UI heuristics
2. Optical vs mathematical centring
3. Platform behaviour: web/React
4. Platform behaviour: mobile (incl. React Native/Expo)
5. Platform behaviour: Windows desktop
6. State coverage
7. Common false passes

---

## 1. Core UI heuristics

Check in roughly this order — earlier items dominate the impression, so a fix
further down rarely rescues a failure further up.

- **Hierarchy** — does the eye land on the primary action first?
- **Grouping** — do related controls read as related, by proximity before decoration?
- **Alignment** — do edges line up across the group, not just within it?
- **Spacing rhythm** — is the spacing scale consistent, or ad hoc per component?
- **Density and whitespace** — is anything crowded or marooned?
- **Label–control association** — is it unambiguous which label owns which control?
- **Primary vs secondary actions** — is the distinction visible without reading?
- **Clipping and truncation** — any ellipsis, cut glyph, or overlapped text?
- **Target sizes** — use the project/platform accessibility guidance. A 44×44 target is a useful touch-interface heuristic, not a universal desktop/web acceptance rule unless the platform or task establishes it.
- **Consistency** — does this screen match the rest of the product?
- **Visual noise** — is any decoration competing with content?
- **Discoverability** — is the next step apparent without instruction?
- **Loading, empty and error states** — do they exist at all, or only the happy path?

## 2. Optical vs mathematical centring

The single most common "it's centred though" dispute. Something can be
mathematically centred and read as off-centre when:

- the element has asymmetric internal padding (an icon on one side only);
- glyph bounding boxes differ from perceived weight (text with descenders, caps);
- a margin or a shadow contributes to the box but not to the perceived shape;
- a triangle, chevron or teardrop has its visual mass away from its box centre;
- an optical illusion from an adjacent heavy element pulls the perceived centre.

Resolve it with numbers, not opinion: `capture_web.py --probe` returns
`space_left_px` / `space_right_px` and offset from parent centre. If the box is
symmetric and it still reads wrong, that is a legitimate optical correction — say
so explicitly rather than "fixing" a value that was already correct.

## 3. Platform behaviour: web/React

- Breakpoint sweep — capture at least narrow / tablet / wide; most layout defects
  live between breakpoints rather than at them.
- Horizontal page scroll at narrow widths (almost always a bug).
- Modal, dropdown and tooltip positioning near viewport edges.
- Overflow containers: does content scroll, clip, or push the layout?
- Sticky and fixed elements overlapping content at short viewport heights.
- Theme switch: capture both light and dark, contrast is rarely preserved by default.
- Font fallback: does the layout hold if the webfont fails to load?

## 4. Platform behaviour: mobile

- Safe areas: notch, dynamic island, home indicator, rounded corners.
- Keyboard overlap: does the focused input stay visible when the keyboard opens?
- Small-screen worst case (approximately 360x640 logical) — not just the design device.
- Large text / accessibility scaling: does the layout survive 130–200% font scale?
- Scroll behaviour: bounce, over-scroll, pull-to-refresh conflicts.
- Landscape, if not locked.
- Density variation: capture the device context alongside the screenshot
  (`capture_android.sh` writes it automatically).
- For React Native specifically: shadow rendering, `overflow: hidden` behaviour and
  text vertical alignment all differ between iOS and Android. Verify on both; a
  single-platform capture is a single-platform claim.

## 5. Platform behaviour: Windows desktop

- DPI scaling at 100%, 125%, 150%, 200% — blurred or clipped chrome is the usual tell.
- Window resize down to minimum size, and maximised.
- Multi-monitor with mixed DPI.
- Native control consistency: does it look like a Windows app or a ported web page?
- Title bar, menu and system theme integration.

## 6. State coverage

A component reviewed only in its default state is reviewed at roughly a third of
its surface. Capture: default, hover, focus (keyboard focus ring specifically),
pressed/active, disabled, loading, error, empty, and long-content overflow.

`capture_web.py --state "hover:.btn,focus:input"` does the first few automatically.

Focus visibility is the most frequently missed: it is a keyboard-accessibility
requirement, not a polish item, and removing outlines without a replacement is a
requirement failure rather than a style choice.

## 7. Common false passes

- "The CSS says centred" — the box model says otherwise; measure it.
- "It looks fine on my viewport" — one viewport is not a responsive claim.
- "The colours match the tokens" — tokens can still fail contrast once composited.
- "The component renders" — rendering is not correct placement.
- "It works in one theme" — if the project supports another theme, its contrast and hierarchy can differ and should be checked separately.
