import bpy, math, os, random
from math import radians as rad

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "cover_shelf_pano.png")
random.seed(21)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def link(ob):
    for c in list(ob.users_collection):
        if c is not scene.collection: c.objects.unlink(ob)
    if ob.name not in scene.collection.objects:
        scene.collection.objects.link(ob)
    return ob
def base_mat(name, base, rough, metallic=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    return m, b

def cube(name, sx, sy, sz, pos, m, bev=0.004):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object; ob.name = name
    ob.scale = (sx, sy, sz); bpy.ops.object.transform_apply(scale=True)
    if bev > 0:
        bv = ob.modifiers.new("bev", "BEVEL"); bv.width = bev; bv.segments = 3
    ob.location = pos; ob.data.materials.append(m); return link(ob)

# ---------------- 书本程序化材质：书脊布面+烫金带 / 纸页层叠 ----------------
bm = bpy.data.materials.new("book_pro"); bm.use_nodes = True
nt = bm.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
geo = nt.nodes.new("ShaderNodeNewGeometry")             # 世界法线
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(geo.outputs["Normal"], sep.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange")                 # ny<-0.75 ⇒ 书脊
mr.inputs["From Min"].default_value = -1.0
mr.inputs["From Max"].default_value = -0.72
mr.inputs["To Min"].default_value = 1.0
mr.inputs["To Max"].default_value = 0.0
mr.clamp = True
nt.links.new(sep.outputs["Y"], mr.inputs[0])

tc = nt.nodes.new("ShaderNodeTexCoord")
oi = nt.nodes.new("ShaderNodeObjectInfo")

# 纸页：高频层叠条纹（Object 坐标 Z）＋暖白渐变＋Bump
wave = nt.nodes.new("ShaderNodeTexWave")
wave.inputs["Scale"].default_value = 340
wave.inputs["Distortion"].default_value = 3.5
wave.inputs["Detail"].default_value = 2
nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
pr = nt.nodes.new("ShaderNodeValToRGB")
pr.color_ramp.elements[0].color = (.93, .90, .82, 1)
pr.color_ramp.elements[1].color = (.68, .62, .50, 1)
nt.links.new(wave.outputs["Fac"], pr.inputs["Fac"])
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = .3
nt.links.new(wave.outputs["Fac"], bp.inputs["Height"])

# 书脊：随机复古城书脊色 + 中央烫金带 + 上下深端带
sr = nt.nodes.new("ShaderNodeValToRGB"); sr.color_ramp.interpolation = 'CONSTANT'
spine_stops = [(.00, (.50, .20, .14)), (.18, (.19, .32, .26)), (.38, (.76, .55, .20)),
               (.58, (.16, .25, .33)), (.78, (.86, .80, .68)), (1.0, (.38, .25, .15))]
for i, (p, c) in enumerate(spine_stops):
    e = sr.color_ramp.elements[i] if i < 2 else sr.color_ramp.elements.new(p)
    e.position = p; e.color = (*c, 1)
nt.links.new(oi.outputs["Random"], sr.inputs["Fac"])
sepO = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sepO.inputs[0])
gold_mr = nt.nodes.new("ShaderNodeMapRange")            # |z|<0.06 ⇒ 金带
gold_mr.inputs["From Min"].default_value = .06
gold_mr.inputs["From Max"].default_value = .10
gold_mr.inputs["To Min"].default_value = 1.0
gold_mr.inputs["To Max"].default_value = 0.0
gold_mr.clamp = True
nt.links.new(sepO.outputs["Z"], gold_mr.inputs[0])
gold = nt.nodes.new("ShaderNodeMixRGB"); gold.blend_type = 'MIX'
gold.inputs["Color2"].default_value = (.78, .60, .25, 1)
nt.links.new(gold_mr.outputs["Result"], gold.inputs["Fac"])
nt.links.new(sr.outputs["Color"], gold.inputs["Color1"])
edge_mr = nt.nodes.new("ShaderNodeMapRange")            # 上下端带压暗
edge_mr.inputs["From Min"].default_value = .34
edge_mr.inputs["From Max"].default_value = .46
edge_mr.inputs["To Min"].default_value = .35
edge_mr.inputs["To Max"].default_value = 1.0
edge_mr.clamp = True
nt.links.new(absZ := None, None) if False else None
abz = nt.nodes.new("ShaderNodeMath"); abz.operation = 'ABSOLUTE'
nt.links.new(sepO.outputs["Z"], abz.inputs[0])
nt.links.new(abz.outputs["Value"], edge_mr.inputs[0])
dark = nt.nodes.new("ShaderNodeMixRGB"); dark.blend_type = 'MULTIPLY'
dark.inputs["Fac"].default_value = 1.0
nt.links.new(edge_mr.outputs["Result"], dark.inputs["Fac"])
nt.links.new(gold.outputs["Color"], dark.inputs["Color2"])

mixm = nt.nodes.new("ShaderNodeMixRGB"); mixm.blend_type = 'MIX'
nt.links.new(mr.outputs["Result"], mixm.inputs["Fac"])
nt.links.new(pr.outputs["Color"], mixm.inputs["Color1"])
nt.links.new(dark.outputs["Color"], mixm.inputs["Color2"])
nt.links.new(mixm.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
bsdf.inputs["Roughness"].default_value = .58

# ---------------- 场景 ----------------
M_SHELF, _ = base_mat("shelf_wood", (0.30, 0.21, 0.14), .42)
M_WALL, _  = base_mat("wall", (0.86, 0.83, .75), .9)     # 深色墙突出射灯洗墙
M_VASE, _  = base_mat("vase", (0.72, 0.64, 0.53), .55)

SX0, SX1 = -1.75, 1.75
ZB, ZT, D = .0, 2.62, .34
YW = 1.86
cube("side_L", .045, D, ZT, (SX0+.0225, YW, ZT/2), M_SHELF, .003)
cube("side_R", .045, D, ZT, (SX1-.0225, YW, ZT/2), M_SHELF, .003)
cube("back", SX1-SX0, .022, ZT, (0, YW+D/2, ZT/2), M_SHELF, 0)
LVL = [.42, .875, 1.33, 1.785, 2.24]
cube("base", SX1-SX0, D, LVL[0], (0, YW, LVL[0]/2), M_SHELF, .004)
cube("topcap", SX1-SX0, D, .04, (0, YW, ZT-.02), M_SHELF, .003)
for z in LVL[1:]:
    cube(f"lv_{z}", SX1-SX0, .026, .028, (0, YW-.006, z), M_SHELF, .002)
cube("plinth", SX1-SX0+.06, D+.05, .05, (0, YW-.01, .025), M_SHELF, .004)

# 地面
fm = bpy.data.materials.new("floor"); fm.use_nodes = True
fb = next(n for n in fm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
fb.inputs["Base Color"].default_value = (.22, .16, .11, 1)
fb.inputs["Roughness"].default_value = .5
fl = bpy.ops.mesh.primitive_plane_add(size=14); link(bpy.context.active_object)
bpy.context.active_object.data.materials.append(fm)

# 书（linked mesh）
book_mesh = bpy.data.meshes.new("bookm")
import bmesh
bmm = bmesh.new(); bmesh.ops.create_cube(bmm, size=1); bmm.to_mesh(book_mesh); bmm.free()
ROWS = LVL + [ZT - .04]
for li in range(len(LVL)):
    z0, z1 = LVL[li], ROWS[li+1]
    cursor = SX0 + .12
    while cursor < SX1 - .12:
        if random.random() < .14:                       # 横叠堆
            n2 = random.randint(3, 5); hh = random.uniform(.032, .048)
            for k in range(n2):
                ob = bpy.data.objects.new(f"hb{li}{k}_{cursor:.2f}", book_mesh)
                ob.scale = (random.uniform(.20, .27), random.uniform(.15, .18), hh)
                ob.location = (cursor + .13, YW - .045, z0 + .014 + hh/2 + k*hh)
                ob.rotation_euler = (0, 0, random.uniform(-.05, .05))
                ob.data.materials.append(bm); link(ob)
            cursor += .32
        else:                                           # 直立书
            t = random.uniform(.022, .046)
            h = (z1 - z0 - .07) * random.uniform(.66, .96)
            ob = bpy.data.objects.new(f"b{li}_{cursor:.2f}", book_mesh)
            ob.scale = (t, .18, h)
            ob.location = (cursor + t/2, YW - .028, z0 + .014 + h/2)
            ob.rotation_euler = (0, 0, random.uniform(-.03, .03))
            ob.data.materials.append(bm); link(ob)
            cursor += t + (random.uniform(.01, .06) if random.random() < .26 else .004)

# 陶瓷罐点缀（中段两层）
for cx, cz, s in [(-.55, LVL[2], .9), (.95, LVL[3], .7)]:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=.095*s)
    v = bpy.context.active_object; v.name = f"vase_{cx}"
    v.scale = (1, 1, 1.35); v.location = (cx, YW-.05, cz+.014+.095*s*1.2)
    v.data.materials.append(M_VASE); link(v)

cube("topbooks", .34, .19, .05, (SX0+.55, YW-.03, ZT+.025), M_SHELF, .004)
for o in [o for o in bpy.data.objects if o.name.startswith("vase_")]: pass
# ---------------- 灯光：日光书房，柔和洗墙 ----------------
w = bpy.data.worlds.new("w"); scene.world = w; w.use_nodes = True
wb = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
wb.inputs["Color"].default_value = (.55, .62, .72, 1)
wb.inputs["Strength"].default_value = 1

sp = bpy.data.lights.new("wash", 'SPOT')
sp.energy = 260; sp.color = (1, .96, .90)
sp.spot_size = rad(52); sp.spot_blend = .55; sp.shadow_soft_size = .09
spo = bpy.data.objects.new("wash", sp); spo.location = (0.1, -1.35, 2.92); link(spo)
spo.rotation_euler = (rad(-30), 0, 0)                   # 斜洗书架中段

sun = bpy.data.lights.new("rim", 'SUN'); sun.energy = 4.0; sun.color = (1, .97, .92)
rim = bpy.data.objects.new("rim", sun); rim.rotation_euler = (rad(-35), rad(18), rad(155)); link(rim)

# ---------------- 相机：50mm 长焦浅景深特写 ----------------
cd = bpy.data.cameras.new("cam"); cd.lens = 30
cam = bpy.data.objects.new("cam", cd); cam.location = (0.38, -3.35, 1.28); link(cam)
cam.rotation_euler = (rad(90), 0, rad(-4.5))
scene.camera = cam

# ---------------- Cycles ----------------
scene.render.engine = 'CYCLES'
scene.cycles.samples = 288
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
scene.view_settings.look = 'AgX - Base Contrast'
scene.view_settings.exposure = .3
scene.render.resolution_x = 2880; scene.render.resolution_y = 1800
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("SHELF_COVER_DONE", OUT)
