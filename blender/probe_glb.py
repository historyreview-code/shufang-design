import bpy, os, mathutils
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), "chair.glb"))
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    zs = [(o.matrix_world @ mathutils.Vector(c)).z for c in o.bound_box]
    print(f"RANGE {o.name}: {min(zs):.3f} ~ {max(zs):.3f}")
print("SCAN_DONE")
