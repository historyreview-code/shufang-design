import bpy, math, os, random
from math import radians as rad

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "cover_shelf_pano.png")
random.seed(31)

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

# ---------------- 古典胡桃木纹：直纹+扰动+清漆 ----------------
M_SHELF, sb = base_mat("shelf_classic", (0.26, 0.18, 0.115), .38)
snt = M_SHELF.node_tree
wave = snt.nodes.new("ShaderNodeTexWave")
wave.inputs["Scale"].default_value = 1.6
wave.inputs["Distortion"].default_value = 9
wave.inputs["Detail"].default_value = 3
wnoise = snt.nodes.new("ShaderNodeTexNoise"); wnoise.inputs["Scale"].default_value = 5
wramp = snt.nodes.new("ShaderNodeValToRGB")
wramp.color_ramp.elements[0].color = (.26, .18, .115, 1)
wramp.color_ramp.elements[1].color = (.38, .27, .17, 1)
mixw = snt.nodes.new("ShaderNodeMixRGB"); mixw.blend_type = 'MULTIPLY'; mixw.inputs["Fac"].default_value = .35
snt.links.new(wnoise.outputs["Fac"], mixw.inputs["Color1"])
snt.links.new(wave.outputs["Color"], mixw.inputs["Color2"])
snt.links.new(mixw.outputs["Color"], wramp.inputs["Fac"])
snt.links.new(wramp.outputs["Color"], sb.inputs["Base Color"])
sb.inputs["Coat Weight"].default_value = .22           # 清漆层
sb.inputs["Coat Roughness"].default_value = .25
wbump = snt.nodes.new("ShaderNodeBump"); wbump.inputs["Strength"].default_value = .06
snt.links.new(mixw.outputs["Color"], wbump.inputs["Height"])
snt.links.new(wbump.outputs["Normal"], sb.inputs["Normal"])
M_WALL, _ = base_mat("wall", (0.86, 0.83, .75), .9)
M_VASE, _ = base_mat("vase", (0.72, 0.64, 0.53), .55)
M_BRASS, _ = base_mat("brass", (0.690, 0.553, 0.243), .3, .9)

# ---------------- 书本双材质（书脊布面烫金 / 纸页层叠） ----------------
bm = bpy.data.materials.new("book_pro"); bm.use_nodes = True
nt = bm.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
geo = nt.nodes.new("ShaderNodeNewGeometry")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(geo.outputs["Normal"], sep.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = -1.0; mr.inputs["From Max"].default_value = -0.72
mr.inputs["To Min"].default_value = 1.0;  mr.inputs["To Max"].default_value = 0.0
mr.clamp = True
nt.links.new(sep.outputs["Y"], mr.inputs[0])
tc = nt.nodes.new("ShaderNodeTexCoord")
oi = nt.nodes.new("ShaderNodeObjectInfo")
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
sr = nt.nodes.new("ShaderNodeValToRGB"); sr.color_ramp.interpolation = 'CONSTANT'
for i, (p, c) in enumerate([(.00, (.50, .20, .14)), (.18, (.19, .32, .26)), (.38, (.76, .55, .20)),
                            (.58, (.16, .25, .33)), (.78, (.86, .80, .68)), (1.0, (.38, .25, .15))]):
    e = sr.color_ramp.elements[i] if i < 2 else sr.color_ramp.elements.new(p)
    e.position = p; e.color = (*c, 1)
nt.links.new(oi.outputs["Random"], sr.inputs["Fac"])
sepO = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sepO.inputs[0])
gold_mr = nt.nodes.new("ShaderNodeMapRange")
gold_mr.inputs["From Min"].default_value = .06; gold_mr.inputs["From Max"].default_value = .10
gold_mr.inputs["To Min"].default_value = 1.0;  gold_mr.inputs["To Max"].default_value = 0.0
gold_mr.clamp = True
nt.links.new(sepO.outputs["Z"], gold_mr.inputs[0])
gold = nt.nodes.new("ShaderNodeMixRGB"); gold.blend_type = 'MIX'
gold.inputs["Color2"].default_value = (.78, .60, .25, 1)
nt.links.new(gold_mr.outputs["Result"], gold.inputs["Fac"])
nt.links.new(sr.outputs["Color"], gold.inputs["Color1"])
abz = nt.nodes.new("ShaderNodeMath"); abz.operation = 'ABSOLUTE'
nt.links.new(sepO.outputs["Z"], abz.inputs[0])
edge_mr = nt.nodes.new("ShaderNodeMapRange")
edge_mr.inputs["From Min"].default_value = .34; edge_mr.inputs["From Max"].default_value = .46
edge_mr.inputs["To Min"].default_value = .35;  edge_mr.inputs["To Max"].default_value = 1.0
edge_mr.clamp = True
nt.links.new(abz.outputs["Value"], edge_mr.inputs[0])
dark = nt.nodes.new("ShaderNodeMixRGB"); dark.blend_type = 'MULTIPLY'; dark.inputs["Fac"].default_value = 1.0
nt.links.new(edge_mr.outputs["Result"], dark.inputs["Fac"])
nt.links.new(gold.outputs["Color"], dark.inputs["Color2"])
mixm = nt.nodes.new("ShaderNodeMixRGB"); mixm.blend_type = 'MIX'
nt.links.new(mr.outputs["Result"], mixm.inputs["Fac"])
nt.links.new(pr.outputs["Color"], mixm.inputs["Color1"])
nt.links.new(dark.outputs["Color"], mixm.inputs["Color2"])
nt.links.new(mixm.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
bsdf.inputs["Roughness"].default_value = .58

# ---------------- 古典书架框架（全宽 3.5m，6 格） ----------------
SX0, SX1, ZT, D, YW = -1.75, 1.75, 2.62, .34, 1.86
cube("side_L", .045, D, ZT, (SX0+.0225, YW, ZT/2), M_SHELF, .003)
cube("side_R", .045, D, ZT, (SX1-.0225, YW, ZT/2), M_SHELF, .003)
cube("back", SX1-SX0, .022, ZT-.04, (0, YW+D/2, ZT/2), M_SHELF, 0)
LVL = [.42, .875, 1.33, 1.785, 2.24]
for z in LVL[1:]:
    cube(f"lv_{z}", SX1-SX0, .026, .028, (0, YW-.006, z), M_SHELF, .002)
    lip = cube(f"lip_{z}", SX1-SX0, .018, .014, (0, YW-D/2+.006, z+.021), M_SHELF, .003)  # 层板前沿线脚
# 竖向壁柱（6 格 5 根内隔 + 柱头柱脚）
NBAY = 6
inner = (SX1-SX0-.09)
bw = (inner - (NBAY-1)*.035) / NBAY
BX = []
for i in range(NBAY):
    bx0 = SX0+.045 + i*(bw+.035)
    BX.append((bx0+.02, bx0+.02+bw-.04))
for i in range(1, NBAY):
    xp = SX0+.045 + i*bw + (i-1)*.035 + .0175
    cube(f"pillar_{i}", .035, D-.02, LVL[-1]-LVL[0], (xp, YW, (LVL[0]+LVL[-1])/2), M_SHELF, .004)
    cube(f"phead_{i}", .05, D+.012, .035, (xp, YW-.006, LVL[-1]-.02), M_SHELF, .004)   # 柱头
    cube(f"pfoot_{i}", .05, D+.012, .03, (xp, YW-.006, LVL[0]+.015), M_SHELF, .004)    # 柱脚
# 基座两层叠涩
cube("plinth1", SX1-SX0+.10, D+.09, .085, (0, YW-.02, .042), M_SHELF, .004)
cube("plinth2", SX1-SX0+.18, D+.15, .05, (0, YW-.045, .1075), M_SHELF, .004)
# 顶冠三层出檐
cube("cor1", SX1-SX0+.10, D+.09, .06, (0, YW-.02, ZT+.03), M_SHELF, .004)
cube("cor2", SX1-SX0+.18, D+.15, .045, (0, YW-.045, ZT+.082), M_SHELF, .004)
cube("cor3", SX1-SX0+.24, D+.20, .035, (0, YW-.06, ZT+.122), M_SHELF, .004)
cube("base_cap", SX1-SX0, D, .06, (0, YW, .45+.03), M_SHELF, .002)   # 底柜台面

# ---------------- 书（按格填充，几何上不可能越界） ----------------
book_mesh = bpy.data.meshes.new("bookm")
import bmesh
bmm = bmesh.new(); bmesh.ops.create_cube(bmm, size=1); bmm.to_mesh(book_mesh); bmm.free()
ROWS = LVL + [ZT - .04]
for li in range(len(LVL)):
    z0, z1 = LVL[li] + (.06 if li == 0 else .018), ROWS[li+1]
    for (gx0, gx1) in BX:
        cursor = gx0
        while cursor < gx1 - .05:
            if random.random() < .14 and gx1 - cursor > .38:   # 横叠堆（剩余够宽才放）
                n2 = random.randint(3, 5); hh = random.uniform(.032, .048)
                for k in range(n2):
                    ob = bpy.data.objects.new(f"hb{li}{k}_{cursor:.2f}", book_mesh)
                    ob.scale = (random.uniform(.19, .26), random.uniform(.15, .18), hh)
                    ob.location = (cursor + .13, YW - .04, z0 + .012 + hh/2 + k*hh)
                    ob.rotation_euler = (0, 0, random.uniform(-.05, .05))
                    ob.data.materials.append(bm); link(ob)
                cursor += .30
            else:                                               # 直立书
                t = random.uniform(.022, .046)
                h = (z1 - z0 - .05) * random.uniform(.66, .96)
                ob = bpy.data.objects.new(f"b{li}_{cursor:.2f}", book_mesh)
                ob.scale = (t, .18, h)
                ob.location = (cursor + t/2, YW - .025, z0 + .012 + h/2)
                ob.rotation_euler = (0, 0, random.uniform(-.03, .03))
                ob.data.materials.append(bm); link(ob)
                cursor += t + (random.uniform(.01, .05) if random.random() < .26 else .004)
        # 每格偶发收尾摆件
        if random.random() < .18:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=14, radius=.07)
            v = bpy.context.active_object; v.name = f"vase{li}_{gx0:.1f}"
            v.scale = (1, 1, 1.3); v.location = (gx1-.08, YW-.045, z0+.014+.091)
            v.data.materials.append(M_VASE); link(v)

# 黄铜格栅托架（古典铜饰）
for gx0, gx1 in BX[:6:2]:
    br = cube(f"brass_{gx0:.1f}", .30, .02, .02, ((gx0+gx1)/2, YW-D/2-.008, LVL[2]-.014), M_BRASS, .004)

# ---------------- 地面/墙 ----------------
fm = bpy.data.materials.new("floor"); fm.use_nodes = True
fb = next(n for n in fm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
fb.inputs["Base Color"].default_value = (.30, .22, .145, 1)
fb.inputs["Roughness"].default_value = .45
bpy.ops.mesh.primitive_plane_add(size=16); fl = bpy.context.active_object
fl.data.materials.append(fm); link(fl)
cube("wall", 12, .18, 3.4, (0, 2.12, 1.7), M_WALL, 0)

# ---------------- 日光 ----------------
w = bpy.data.worlds.new("w"); scene.world = w; w.use_nodes = True
wb = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
wb.inputs["Color"].default_value = (.55, .62, .72, 1)
sun = bpy.data.lights.new("sun", 'SUN'); sun.energy = 4.0; sun.color = (1, .97, .92); sun.angle = rad(1.8)
so = bpy.data.objects.new("sun", sun); so.rotation_euler = (rad(-42), rad(10), rad(-18)); link(so)
def area(name, loc, rot, power, size, color=(1, .97, .90)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.size = size; ld.color = color
    ob = bpy.data.objects.new(name, ld); ob.location = loc; ob.rotation_euler = rot; return link(ob)
area("window", (3.2, -2.6, 1.9), (0, rad(62), rad(128)), 560, 2.6)
area("fill", (-3.0, -1.6, 1.6), (0, rad(-58), rad(-75)), 140, 2.0, (.80, .87, 1.0))

# ---------------- 相机全景 ----------------
cd = bpy.data.cameras.new("cam"); cd.lens = 30
cam = bpy.data.objects.new("cam", cd); cam.location = (0.38, -3.45, 1.30); link(cam)
cam.rotation_euler = (rad(90), 0, rad(-4.5))
scene.camera = cam

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
print("PANO_V2_DONE", OUT)
