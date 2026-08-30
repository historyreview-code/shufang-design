import bpy, math, os

BASE = os.path.dirname(os.path.abspath(__file__))
STATUE = os.path.expanduser("~/创意编程探索/blender练习/04_自由女神像/statue_of_liberty.blend")
TERRA = (0.678, 0.376, 0.220, 1)          # 陶土色

def make_terracotta(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs["Base Color"].default_value = TERRA
    b.inputs["Roughness"].default_value = .72
    nt = m.node_tree
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 220
    n.inputs["Detail"].default_value = 6
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = .18
    nt.links.new(n.outputs["Factor"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], next(s for s in b.inputs if s.name == "Normal"))
    return m

def norm_origin(objs):
    """底部对齐 z=0、水平居中于原点"""
    import mathutils
    xs, ys, zs = [], [], []
    for o in objs:
        for v in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(v)
            xs.append(w.x); ys.append(w.y); zs.append(w.z)
    cx, cy, z0 = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2, min(zs)
    for o in objs:
        o.location.x -= cx; o.location.y -= cy; o.location.z -= z0

# ---------- 1. 自由女神（用户练习模型 → 陶土摆件 0.26m） ----------
bpy.ops.wm.open_mainfile(filepath=STATUE)
keep = [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith("Cube")]
terra = make_terracotta("terra_liberty")
for o in keep:
    o.data.materials.clear(); o.data.materials.append(terra)
norm_origin(keep)
h = max(o.dimensions.z for o in keep)
sc = 0.26 / h
for o in keep: o.scale = (sc, sc, sc)
bpy.ops.object.select_all(action='DESELECT')
for o in keep: o.select_set(True)
bpy.context.view_layer.objects.active = keep[0]
bpy.ops.export_scene.gltf(filepath=os.path.join(BASE, "decor_liberty.glb"),
    export_format='GLB', use_selection=True, export_yup=True)
print("LIBERTY_EXPORTED height", round(h*sc, 3))

# ---------- 2. 陶土猴头玩偶（Suzanne + 圆底座，总高 0.16m） ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
def link(ob): scene.collection.objects.link(ob); return ob
terra2 = make_terracotta("terra_monkey")
bpy.ops.mesh.primitive_monkey_add()
mk = bpy.context.active_object; mk.name = "monkey"
mk.scale = (.062, .062, .062); mk.location = (0, 0, .093)
mk.data.materials.append(terra2)
bpy.ops.mesh.primitive_cylinder_add(radius=.062, depth=.026, vertices=28)
bs = bpy.context.active_object; bs.name = "monkey_base"
bs.location = (0, 0, .013); bs.data.materials.append(terra2)
bpy.ops.object.select_all(action='DESELECT')
mk.select_set(True); bs.select_set(True)
bpy.context.view_layer.objects.active = mk
bpy.ops.export_scene.gltf(filepath=os.path.join(BASE, "decor_monkey.glb"),
    export_format='GLB', use_selection=True, export_yup=True)
print("MONKEY_EXPORTED")

for f in ("decor_liberty.glb", "decor_monkey.glb"):
    p = os.path.join(BASE, f)
    print("SIZE", f, os.path.getsize(p))
