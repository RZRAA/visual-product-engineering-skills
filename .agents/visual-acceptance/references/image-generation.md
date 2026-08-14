# Generated and edited image reference

Load when reviewing images produced by generation or editing tools, including
reference-matched work.

## The core failure

"Contains all the requested objects" is not the same as "matches the requested
image". A generation can include every named noun and still fail on composition,
camera, scale relationship, lighting and mood — which is usually what the request
was actually about. Review the arrangement, not the inventory.

## Checks

- **Subject identity** — is it the right subject, not merely a member of the right category?
- **Pose and gesture** — matches the described action, not just the described object.
- **Camera** — angle, height, distance, lens character.
- **Framing and crop** — what is in shot, what is cut, where the subject sits in frame.
- **Perspective** — consistent vanishing behaviour; no impossible convergence.
- **Composition** — where the eye lands and travels.
- **Relative scale** — objects sized correctly against each other. Frequently wrong
  in generated work and easy to overlook once the composition reads well.
- **Lighting direction and quality** — one coherent source unless otherwise briefed;
  shadows agreeing with it.
- **Colour relationships** — palette, temperature, saturation balance.
- **Material appearance** — do surfaces read as the stated material?
- **Environment** — setting matches, without contradicting the subject's context.
- **Unwanted additions** — extra limbs, duplicated objects, invented text, watermarks,
  stray anatomy. Check hands, teeth, reflections, and any repeated pattern.
- **Omitted requirements** — walk the original brief item by item; omission is
  quieter than error and much easier to miss.
- **Style consistency** — matches the established look of the set it belongs to.

## Reference matching

When a reference exists, compare in this order — earlier items dominate perception,
so a mismatch high in the list cannot be compensated further down:

1. composition
2. camera
3. silhouette
4. proportion
5. spatial relationships
6. lighting
7. colour and material
8. fine detail

`silhouette.py` works on generated images with a separable subject, and gives an
objective proportion delta against the reference rather than an impression of one.

## Iterating

When a generation misses, change one axis at a time. Rewriting the whole prompt
after each failure makes it impossible to tell what mattered, and tends to reintroduce
problems already solved.

- Record the seed and settings alongside every kept output; an unreproducible good
  result is worth much less than a reproducible adequate one.
- Fix composition and camera before style, and style before detail.
- Prefer editing a nearly-correct image over regenerating and hoping.
- Keep rejected variants until the set is accepted — they are the evidence for why
  the accepted one was chosen.

## Usability

The last check is not aesthetic: can the image actually be used for its stated
purpose? Resolution, aspect ratio, safe margins for overlaid text, background
separability for cut-out, and file format. An image that reviews well and cannot be
placed has failed.
