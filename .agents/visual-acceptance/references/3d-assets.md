# 3D asset reference

Load when reviewing models, props, characters, environment pieces or textures.

## Review order

Review strictly in this order and stop at the first failure. Detail added on top of
a broken silhouette is wasted work, and reviewing it first is how that waste gets
approved.

1. **Silhouette** — the shape as a black cutout. Is it readable and distinctive at
   a glance? Would it be identifiable at thumbnail size?
2. **Overall proportion** — height/width relationship, and whether it matches the
   reference or the intended scale in world.
3. **Primary masses** — the two or three big forms and their relationship.
4. **Secondary forms** — subdivisions of the primary masses.
5. **Negative space** — the gaps are part of the read; are they intentional?
6. **Edge treatment** — bevels, wear, silhouette-breaking detail.
7. **Material response** — behaviour under light: roughness, metalness, sheen.
8. **Texture scale and repetition** — texel density consistency, visible tiling.
9. **Micro-detail** — last, and only once everything above is accepted.

A weak silhouette with a strong texture is still a weak asset.

## Measuring instead of guessing

Render a turntable and measure it:

```bash
blender -b asset.blend -P render_turntable.py -- --out .visual/t/after --frames 8
python contact_sheet.py .visual/t/after/*.png --out .visual/t/after/_sheet.png --labels
python silhouette.py .visual/t/after/turntable_00_000deg.png \
       --reference .visual/t/reference/front.png --json .visual/t/metrics/sil.json
```

Interpretation:
- `aspect_ratio_pct` beyond ±5% vs the reference is a proportion error a viewer will
  notice, even if neither render looks obviously wrong on its own.
- `widest_row_norm_from_top` shifting by more than ~0.05 moves where the mass reads —
  a common cause of "it looks right but feels wrong".
- `horizontal_symmetry_error` near zero on an asset intended to be hand-made or
  organic usually means it reads as manufactured.
- `top_to_bottom_width_ratio` captures taper directly; it is the fastest way to check
  that a silhouette redesign actually changed what it claimed to.

## Scale and world context

An asset reviewed in isolation has no scale. Render it next to a known-size
reference object, or state the dimensions from `mesh_stats.json` and compare them
against the intended in-world size. "Looks like a crate" and "is crate-sized" are
different findings.

## Topology and budget

From `mesh_stats.json`:
- Triangle count against the platform budget.
- Material count — on mobile this drives draw calls more than triangle count does.
- UV maps present at all, and a second set if lightmapping is intended.
- Non-manifold geometry, flipped normals, and n-gons where the pipeline forbids them.
- Dimensions non-zero on all three axes, and unit scale applied rather than baked
  into the object transform.

## Textures

Run `texture_check.py` on every map. Watch for:
- visible tiling bands (the script reports the period in pixels);
- inconsistent texel density between maps or between assets in the same set;
- a normal map that is not in the expected green channel convention (compare against
  a known-good asset — the flip is invisible until it lights wrongly);
- an alpha channel that is fully opaque (wasted memory);
- non-power-of-two resolutions **when the target pipeline specifically benefits from or requires power-of-two textures for compression, mipmapping, streaming or platform support**.
