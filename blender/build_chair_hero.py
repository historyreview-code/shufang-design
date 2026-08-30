import bpy, math, os
from math import radians as rad

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "chair_hero.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# 导入高模转椅
bpy.ops.object.select_all(action='DESELECT')
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(BASE, "chair.glb"))
new = [o for o in bpy.data.objects if o not in before]
roots = [o for o in new if o.parent is None or o.parent not in new]
for r in roots:
    r.rotation_euler = (0, 0, rad(-28))          # 3/4 前侧展示角

# 地面：深色微抛光，出倒影
fm = bpy.data.materials.new("floor"); fm.use_nodes = True
fb = next(n for n in fm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
fb.inputs["Base Color"].default_value = (.085, .070, .055, 1)
fb.inputs["Roughness"].default_value = .22
fb.inputs["Metallic"].default_value = 0.0
fl = bpy.ops.mesh.primitive_plane_add(size=14); floor = bpy.context.active_object
floor.data.materials.append(fm)

# 摄影棚三点光
def area(name, loc, rot, power, size, color=(1, .95, .88)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.size = size
    ld.size_y = size * 1.3 if name == 'key' else size
    ld.color = color
    ob = bpy.data.objects.new(name, ld); ob.location = loc; ob.rotation_euler = rot
    scene.collection.objects.link(ob); return ob
area("key",   (1.7, -1.3, 1.85), (rad(50), 0, rad(42)), 420, 1.1)            # 主光暖
area("fill",  (-2.3, -0.9, 0.9), (rad(58), 0, rad(-50)), 80, 1.5, (.78, .85, 1.0))  # 冷副
area("rim",   (-0.7, 2.1, 2.05), (rad(-55), 0, rad(180)), 190, 0.9, (1, .88, .70))  # 顶部轮廓
w = bpy.data.worlds.new("w"); scene.world = w; w.use_nodes = True
wb = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
wb.inputs["Color"].default_value = (.020, .017, .015, 1)
wb.inputs["Strength"].default_value = 1

# 相机：低机位 3/4 前侧，f/3.5 焦点椅背
cd = bpy.data.cameras.new("cam"); cd.lens = 46
cd.dof.use_dof = True; cd.dof.aperture_fstop = 3.5; cd.dof.focus_distance = 1.95
cam = bpy.data.objects.new("cam", cd); cam.location = (-1.30, -1.72, 0.92)
scene.collection.objects.link(cam)
cam.rotation_euler = (rad(80), 0, rad(-37))
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 320
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 8
try:
    scene.cycles.device = 'GPU'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'; prefs.get_devices()
    for d in prefs.devices: d.use = True
except Exception as e:
    print("GPU fallback:", e)
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Punchy'
scene.view_settings.exposure = .55
scene.render.resolution_x = 2400; scene.render.resolution_y = 1500
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("CHAIR_HERO_DONE", OUT)
