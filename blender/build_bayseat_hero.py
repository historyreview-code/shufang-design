import bpy, math, os, random
from math import radians as rad

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "bayseat_hero.png")
random.seed(5)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def link(ob):
    for c in list(ob.users_collection):
        if c is not scene.collection: c.objects.unlink(ob)
    if ob.name not in scene.collection.objects:
        scene.collection.objects.link(ob)
    return ob
def base_mat(name, base, rough, metallic=0.0, bump_amp=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    if bump_amp > 0:
        nt = m.node_tree
        n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 480
        n.inputs["Detail"].default_value = 4
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump_amp
        nt.links.new(n.outputs["Factor"], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

def rbox(name, sx, sy, sz, r, pos, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object; ob.name = name
    ob.scale = (sx, sy, sz); bpy.ops.object.transform_apply(scale=True)
    bv = ob.modifiers.new("bev", "BEVEL"); bv.width = r; bv.segments = 5
    ob.location = pos; ob.rotation_euler = rot
    ob.data.materials.append(m); return link(ob)

M_WOOD  = base_mat("wood_walnut", (0.30, 0.205, 0.125), .42)
M_FLOOR = base_mat("floor", (0.40, 0.28, 0.175), .4)
M_LINEN = base_mat("linen", (0.87, 0.81, 0.69), .92, bump_amp=.35)
M_PIL1  = base_mat("pil_rust", (0.52, 0.24, 0.14), .9, bump_amp=.3)
M_PIL2  = base_mat("pil_must", (0.72, 0.52, 0.16), .9, bump_amp=.3)
M_PIL3  = base_mat("pil_pine", (0.19, 0.34, 0.28), .9, bump_amp=.3)
M_CUP   = base_mat("porcelain", (0.93, 0.91, 0.86), .22)
M_BRASS = base_mat("brass", (0.690, 0.553, 0.243), .3, .9)
M_SHEER = base_mat("sheer", (1.0, 0.97, 0.90), .55)
M_SHEER.node_tree.nodes["Principled BSDF"] if False else None
sb = next(n for n in M_SHEER.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
sb.inputs["Alpha"].default_value = .42
M_SHEER.blend_method = 'BLEND'

# ---------- 窗台座体 + 坐榻（窗台向 -Y 外飘） ----------
rbox("bay_body", 2.4, .58, .42, .006, (0, -.30, .21), M_WOOD)
rbox("bay_seatwood", 2.46, .62, .045, .005, (0, -.30, .4475), M_WOOD)
rbox("cushion", 2.16, .50, .13, .05, (0, -.30, .535), M_LINEN, rot=(0, 0, 0))
# 三只抱枕斜倚
for x, m, ang in [(-.72, M_PIL1, -.38), (.02, M_PIL2, -.30), (.74, M_PIL3, -.42)]:
    p = rbox(f"pillow_{x}", .34, .13, .34, .09, (x, -.34, .76), m, rot=(ang, 0, random.uniform(-.08, .08)))
# 针织毯：搭右角 + 垂落
rbox("throw_top", .55, .40, .022, .008, (.82, -.26, .612), M_PIL1, rot=(0, 0, rad(7)))
rbox("throw_drap", .42, .022, .34, .008, (.86, -.10, .47), M_PIL1, rot=(0, 0, rad(4)))
# 托盘 + 杯碟（左侧）
bpy.ops.mesh.primitive_cylinder_add(radius=.17, depth=.028, vertices=28)
tr = bpy.context.active_object
tr = bpy.context.active_object; tr.name = "tray"; tr.location = (-.62, -.30, .575)
tr.data.materials.append(M_WOOD); link(tr)
bpy.ops.mesh.primitive_cylinder_add(radius=.036, depth=.072, vertices=18)
cup = bpy.context.active_object
cup = bpy.context.active_object; cup.name = "cup"; cup.location = (-.62, -.33, .625)
cup.data.materials.append(M_CUP); link(cup)
bpy.ops.mesh.primitive_cylinder_add(radius=.052, depth=.011, vertices=20)
sc = bpy.context.active_object
sc = bpy.context.active_object; sc.name = "saucer"; sc.location = (-.62, -.33, .592)
sc.data.materials.append(M_CUP); link(sc)

# ---------- 地板（室内侧） ----------
fm = bpy.data.materials.new("floor"); fm.use_nodes = True
fb = next(n for n in fm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
fb.inputs["Base Color"].default_value = (.40, .28, .175, 1)
fb.inputs["Roughness"].default_value = .42
bpy.ops.mesh.primitive_plane_add(size=14)
fl = bpy.context.active_object; fl.location = (0, 1.8, 0)
fl.data.materials.append(fm); link(fl)

# ---------- 窗外：亮天空板 + 窗框剪影 ----------
em = bpy.data.materials.new("sky"); em.use_nodes = True
eb = next(n for n in em.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
eb.inputs["Emission Color"].default_value = (1.0, .93, .80, 1)
eb.inputs["Emission Strength"].default_value = 7.0
sky = bpy.ops.mesh.primitive_plane_add(size=1); sky = bpy.context.active_object
sky.name = "skypad"; sky.scale = (7, 5, 1); sky.location = (0, -4.6, 2.0)
sky.rotation_euler = (rad(90), 0, 0); sky.data.materials.append(em); link(sky)
for i, vx in enumerate((-1.05, -.35, .35, 1.05)):      # 窗框竖梃剪影
    rbox(f"mullion_{i}", .045, .06, 2.1, .004, (vx, -.68, 1.32), M_WOOD, (0, 0, 0))
rbox("sill_front", 2.5, .05, .035, .004, (0, -.615, .435), M_WOOD)

# ---------- 纱帘两片（竖褶波浪） ----------
def sheer(name, x):
    nseg = 30
    verts, faces = [], []
    for zi, z in enumerate((.42, 1.38, 2.30)):
        for xi in range(nseg+1):
            t = xi/nseg
            px = x + t*.52
            py = -.50 + math.sin(t*21 + x*3)*.045
            verts.append((px, py, z))
    for zi in range(2):
        for xi in range(nseg):
            a = zi*(nseg+1)+xi
            faces.append((a, a+1, a+nseg+2, a+nseg+1))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(M_SHEER)
    return link(ob)
sheer("sheer_L", -.92); sheer("sheer_R", .40)

# ---------- 灯光 ----------
sun = bpy.data.lights.new("sun", 'SUN'); sun.energy = 3.2; sun.color = (1, .93, .80); sun.angle = rad(1.6)
so = bpy.data.objects.new("sun", sun); so.location = (0, -3, 2.4); link(so)
so.rotation_euler = (rad(-28), rad(12), rad(8))         # 从窗外斜射入室
w = bpy.data.worlds.new("w"); scene.world = w; w.use_nodes = True
wb = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
wb.inputs["Color"].default_value = (.06, .055, .06, 1)
def area(name, loc, rot, power, size, color=(1, .95, .88)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.size = size; ld.color = color
    ob = bpy.data.objects.new(name, ld); ob.location = loc; ob.rotation_euler = rot
    return link(ob)
area("roomfill", (1.6, 1.9, 1.7), (rad(-42), 0, rad(165)), 120, 1.8)

# ---------- 相机 ----------
cd = bpy.data.cameras.new("cam"); cd.lens = 35
cd.dof.use_dof = True; cd.dof.aperture_fstop = 3.2; cd.dof.focus_distance = 2.0
cam = bpy.data.objects.new("cam", cd); cam.location = (0.25, 1.95, 1.12); link(cam)
cam.rotation_euler = (rad(83.5), 0, rad(180))
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
scene.view_settings.exposure = .6
scene.render.resolution_x = 2400; scene.render.resolution_y = 1500
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("BAYSEAT_HERO_DONE", OUT)
