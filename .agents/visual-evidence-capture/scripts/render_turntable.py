#!/usr/bin/env python3
"""Render a turntable of a 3D asset from Blender, headless.

Usage:
    blender -b FILE.blend -P render_turntable.py -- --out DIR [--frames 8] [--res 640]
    blender -b -P render_turntable.py -- --import model.glb --out DIR

    # then collapse to one reviewable image:
    python contact_sheet.py DIR/*.png --out DIR/_sheet.png --labels

Renders the selected object (or everything, if nothing is selected) from evenly
spaced angles on a fitted orbit, with neutral three-point lighting and a flat
backdrop. The flat backdrop is deliberate: it makes the silhouette separable, so
`silhouette.py` can measure proportion from these frames directly.

Also writes mesh_stats.json — triangle count, vertex count, material and UV-map
counts, and dimensions — which is the cheapest possible check against a budget.

Requires: Blender on PATH (tested against 3.x/4.x).
"""
from __future__ import annotations

import json
import math
import os
import sys

try:
    import bpy
    from mathutils import Vector
except ImportError:  # pragma: no cover
    sys.exit("Run this inside Blender:\n"
             "  blender -b FILE.blend -P render_turntable.py -- --out DIR")


def argv_after_dashes() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def parse_args():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=".visual/turntable")
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--res", type=int, default=640)
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--elevation", type=float, default=18.0, help="camera elevation in degrees")
    ap.add_argument("--import", dest="import_path", help="import a .glb/.gltf/.fbx/.obj first")
    ap.add_argument("--bg", type=float, default=0.05, help="backdrop grey level 0-1")
    ap.add_argument("--engine", default="BLENDER_EEVEE_NEXT")
    return ap.parse_args(argv_after_dashes())


def import_model(path: str) -> None:
    ext = os.path.splitext(path)[1].lower()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext == ".obj":
        try:
            bpy.ops.wm.obj_import(filepath=path)   # Blender 4.x
        except AttributeError:
            bpy.ops.import_scene.obj(filepath=path)  # Blender 3.x
    else:
        sys.exit(f"Unsupported import format: {ext}")


def target_meshes():
    selected = [o for o in bpy.context.selected_objects if o.type == "MESH"]
    return selected or [o for o in bpy.data.objects if o.type == "MESH"]


def bounds(objects):
    corners = [obj.matrix_world @ Vector(c) for obj in objects for c in obj.bound_box]
    lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return lo, hi, (lo + hi) / 2, (hi - lo)


def mesh_stats(objects, size) -> dict:
    dg = bpy.context.evaluated_depsgraph_get()
    tris = verts = 0
    materials, uv_maps = set(), set()
    for obj in objects:
        mesh = obj.evaluated_get(dg).to_mesh()
        mesh.calc_loop_triangles()
        tris += len(mesh.loop_triangles)
        verts += len(mesh.vertices)
        uv_maps.update(l.name for l in mesh.uv_layers)
        materials.update(m.name for m in obj.data.materials if m)
        obj.evaluated_get(dg).to_mesh_clear()
    return {
        "objects": len(objects),
        "triangles": tris,
        "vertices": verts,
        "materials": sorted(materials),
        "material_count": len(materials),
        "uv_maps": sorted(uv_maps),
        "has_uvs": bool(uv_maps),
        "dimensions": [round(size.x, 4), round(size.y, 4), round(size.z, 4)],
        "note": "compare triangles and material_count against the target platform budget; "
                "material_count drives draw calls more than triangle count does on mobile",
    }


def build_lighting(centre: Vector, radius: float, bg: float) -> None:
    world = bpy.data.worlds.new("evidence_world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (bg, bg, bg, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.4
    bpy.context.scene.world = world

    for name, offset, energy, size in (
        ("key", Vector((1.2, -1.4, 1.3)), 4.0, 2.0),
        ("fill", Vector((-1.5, -0.8, 0.4)), 1.2, 3.0),
        ("rim", Vector((-0.4, 1.6, 1.0)), 2.5, 1.5),
    ):
        data = bpy.data.lights.new(name, type="AREA")
        data.energy = energy * (radius**2) * 12
        data.size = size * radius
        light = bpy.data.objects.new(name, data)
        light.location = centre + offset * radius * 2.4
        direction = centre - light.location
        light.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(light)


def main() -> int:
    args = parse_args()
    if args.import_path:
        import_model(args.import_path)

    meshes = target_meshes()
    if not meshes:
        sys.exit("No mesh objects found in the scene.")

    _, _, centre, size = bounds(meshes)
    radius = max(size.length / 2, 1e-4)

    scene = bpy.context.scene
    try:
        scene.render.engine = args.engine
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = args.res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    if hasattr(scene, "cycles"):
        scene.cycles.samples = args.samples

    build_lighting(centre, radius, args.bg)

    cam_data = bpy.data.cameras.new("evidence_cam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("evidence_cam", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam

    dist = radius * 3.2
    elev = math.radians(args.elevation)
    os.makedirs(args.out, exist_ok=True)

    frames = []
    for i in range(args.frames):
        theta = 2 * math.pi * i / args.frames
        cam.location = centre + Vector((
            math.cos(theta) * dist * math.cos(elev),
            math.sin(theta) * dist * math.cos(elev),
            dist * math.sin(elev),
        ))
        cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
        path = os.path.join(args.out, f"turntable_{i:02d}_{int(math.degrees(theta)):03d}deg.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        frames.append(path)

    stats = mesh_stats(meshes, size)
    stats["frames"] = frames
    stats["backdrop_grey"] = args.bg
    with open(os.path.join(args.out, "mesh_stats.json"), "w") as fh:
        json.dump(stats, fh, indent=2)

    print(json.dumps(stats, indent=2))
    print(f"\nRendered {len(frames)} frames to {args.out}")
    print(f"Next: python contact_sheet.py {args.out}/*.png --out {args.out}/_sheet.png --labels")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
