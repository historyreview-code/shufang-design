import bpy, math, os, random
from math import radians as rad

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "cover.png")
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- 材质工具（全按类型接线，5.2 稳） ----------
def mat(name, base, rough, metallic=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    return m, b

M_FLOOR, _ = mat("floor", (0.43, 0.30, 0.19), .38)
M_WALL, _  = mat("wall", (0.80, 0.75, 0.66), .9)
M_SHELF, _ = mat("shelf", (0.314, 0.227, 0.157), .45)
M_DESK, _  = mat("desk", (0.541, 0.353, 0.20), .4)
M_GOLD, _  = mat("gold", (0.690, 0.553, 0.243), .3, .9)

def link(ob):
    for c in list(ob.users_collection):
        if c is not scene.collection: c.objects.unlink(ob)
    if ob.name not in scene.collection.objects:
        scene.collection.objects.link(ob)
    return ob
def cube(name, sx, sy, sz, pos, m, bev=0.006):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object; ob.name = name
    ob.scale = (sx, sy, sz); bpy.ops.object.transform_apply(scale=True)
    if bev > 0:
        bv = ob.modifiers.new("bev", "BEVEL"); bv.width = bev; bv.segments = 3
    ob.location = pos; ob.data.materials.append(m); return link(ob)

# ---------- 地板（程序化拼板） ----------
fm = bpy.data.materials.new("floorTex"); fm.use_nodes = True
fb = next(n for n in fm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
nt = fm.node_tree
brick = nt.nodes.new("ShaderNodeTexBrick")
brick.offset = .5; brick.inputs["Scale"].default_value = 1.0
brick.inputs["Mortar Size"].default_value = .006
brick.inputs["Color1"].default_value = (.45, .315, .195, 1)
brick.inputs["Color2"].default_value = (.38, .26, .158, 1)
brick.inputs["Mortar"].default_value = (.16, .10, .06, 1)
noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 8
mixc = nt.nodes.new("ShaderNodeMixRGB"); mixc.blend_type = 'MULTIPLY'; mixc.inputs["Fac"].default_value = .18
nt.links.new(brick.outputs["Color"], mixc.inputs["Color1"])
nt.links.new(noise.outputs["Color"], mixc.inputs["Color2"])
nt.links.new(mixc.outputs["Color"], fb.inputs["Base Color"])
fb.inputs["Roughness"].default_value = .34
plane = bpy.ops.mesh.primitive_plane_add(size=16); floor = bpy.context.active_object
floor.name = "floor"; floor.data.materials.append(fm); link(floor)

# ---------- 背景墙 + 通顶书架一段（3.2m） ----------
wall = cube("wall", 10, .18, 3.2, (0, 2.05, 1.6), M_WALL, 0)
SX0, SX1, SZ = -1.6, 1.6, 2.55
D = .32
cube("shelf_side_L", .04, D, SZ, (SX0+.02, 1.86, SZ/2), M_SHELF, 0)
cube("shelf_side_R", .04, D, SZ, (SX1-.02, 1.86, SZ/2), M_SHELF, 0)
cube("shelf_back",  SX1-SX0, .025, SZ, (0, 2.0, SZ/2), M_SHELF, 0)
cube("shelf_base",  SX1-SX0, D, .05, (0, 1.86, .42), M_SHELF, 0)
cube("shelf_top",   SX1-SX0, D, .05, (0, 1.86, SZ-.025), M_SHELF, 0)
LVL = [.42, .87, 1.29, 1.71, 2.13]
for z in LVL[1:]:
    cube(f"shelf_lv_{z}", SX1-SX0, .028, .03, (0, 1.86, z), M_SHELF, 0)

# 书本（linked mesh + Object Info Random 驱动复古城书脊色板）
sm = bpy.data.materials.new("book"); sm.use_nodes = True
sb = next(n for n in sm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
snt = sm.node_tree
oi = snt.nodes.new("ShaderNodeObjectInfo")
ramp = snt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = 'CONSTANT'
stops = [(.00, (.55, .23, .16)), (.20, (.21, .35, .29)), (.40, (.78, .58, .22)),
         (.60, (.18, .28, .35)), (.80, (.88, .83, .72)), (1.0, (.42, .28, .17))]
for i, (p, c) in enumerate(stops):
    e = ramp.color_ramp.elements[i] if i < 2 else ramp.color_ramp.elements.new(p)
    e.position = p; e.color = (*c, 1)
snt.links.new(oi.outputs["Random"], ramp.inputs["Fac"])
snt.links.new(ramp.outputs["Color"], sb.inputs["Base Color"])
sb.inputs["Roughness"].default_value = .62
book_mesh = bpy.data.meshes.new("book")
import bmesh
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(book_mesh); bm.free()
for li in range(len(LVL)-1):
    z0, z1 = LVL[li], LVL[li+1]
    cursor = SX0 + .10
    while cursor < SX1 - .15:
        roll = random.random()
        if roll < .12:                                # 横叠书堆
            hh = random.uniform(.03, .045); n2 = random.randint(3, 5)
            for k in range(n2):
                ob = bpy.data.objects.new(f"hb_{li}_{cursor:.2f}_{k}", book_mesh)
                ob.scale = (random.uniform(.19, .26), random.uniform(.15, .18), hh)
                ob.location = (cursor + .12, 1.83, z0 + hh/2 + k*hh + .015)
                ob.rotation_euler = (0, 0, random.uniform(-.06, .06))
                ob.data.materials.append(sm); link(ob)
            cursor += .30
        else:                                          # 直立书
            t = random.uniform(.022, .045); h = (z1 - z0 - .075) * random.uniform(.62, .95)
            ob = bpy.data.objects.new(f"b_{li}_{cursor:.2f}", book_mesh)
            ob.scale = (t, .175, h)
            ob.location = (cursor + t/2, 1.845, z0 + .015 + h/2)
            ob.rotation_euler = (0, 0, random.uniform(-.035, .035))
            ob.data.materials.append(sm); link(ob)
            cursor += t + (random.uniform(.005, .05) if random.random() < .3 else .004)

# ---------- 转椅（导入 Blender 高模 GLB） ----------
bpy.ops.object.select_all(action='DESELECT')
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(BASE, "chair.glb"))
new = [o for o in bpy.data.objects if o not in before]
roots = [o for o in new if o.parent is None or o.parent not in new]
for r in roots:
    r.rotation_euler = (0, 0, rad(-38))            # 面朝画面左前
    r.location = (0.92, -0.42, 0)

# ---------- 书桌一角 + 桌面书与杯 ----------
cube("desk_top", 1.7, .04, .85, (0.28, -1.12, .735), M_DESK)
desk = bpy.data.objects["desk_top"]; desk.rotation_euler = (rad(90), 0, 0)
for k, (dx, dz) in enumerate([(-.12, 0), (-.06, 0), (-.01, 0)]):
    ob = bpy.data.objects.new(f"deskbook_{k}", book_mesh)
    ob.scale = (.24, .17, .035)
    ob.location = (0.55+dx, -1.12, .775+k*.036)
    ob.rotation_euler = (0, 0, rad(random.uniform(-8, 8))); ob.data.materials.append(sm); link(ob)
cup = cyl = bpy.data.objects.new("cup", bpy.data.meshes.new("cupm"))
bm2 = bmesh.new(); bmesh.ops.create_cone(bm2, cap_ends=True, segments=20, radius1=.038, radius2=.032, depth=.09)
bm2.to_mesh(cup.data); bm2.free(); cup.location = (0.34, -1.02, .82)
cm = mat("cupg", (.90, .88, .82), .25)[0]; cup.data.materials.append(cm); link(cup)

# ---------- 灯光 ----------
def sun(name, rot, strength, color=(1, .85, .66)):
    ld = bpy.data.lights.new(name, 'SUN'); ld.energy = strength; ld.color = color
    ld.angle = rad(1.2)
    ob = bpy.data.objects.new(name, ld); ob.rotation_euler = rot; return link(ob)
sun("key_sun", (rad(58), 0, rad(-38)), 5.5)                    # 右上低角度暖阳
def area(name, loc, rot, power, size=1.4, color=(1, .93, .82)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.size = size; ld.color = color
    ob = bpy.data.objects.new(name, ld); ob.location = loc; ob.rotation_euler = rot; return link(ob)
area("window_fill", (3.2, -2.6, 1.8), (0, rad(62), rad(128)), 220, 2.0)
area("cool_fill",  (-3.0, -1.4, 1.5), (0, rad(-55), rad(-70)), 60, 1.6, (.72, .82, 1.0))
world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
wb = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
wb.inputs["Color"].default_value = (.055, .05, .055, 1)
wb.inputs["Strength"].default_value = 1.0

# 轻体积尘光（沿阳光路径的窄盒）
vm = bpy.data.materials.new("dust"); vm.use_nodes = True
vnt = vm.node_tree
for n in list(vnt.nodes):
    if n.type != 'OUTPUT_MATERIAL': vnt.nodes.remove(n)
pv = vnt.nodes.new("ShaderNodeVolumePrincipled")
pv.inputs["Density"].default_value = .012
pv.inputs["Anisotropy"].default_value = .35
outn = next(n for n in vnt.nodes if n.type == 'OUTPUT_MATERIAL')
vnt.links.new(pv.outputs["Volume"], outn.inputs["Volume"])
dust = cube("dustbox", 7, 7, 3.0, (0, 0, 1.5), vm, 0)
dust.visible_shadow = False; dust.visible_camera = False

# ---------- 相机（景深 f/2.8 焦点在椅背） ----------
cd = bpy.data.cameras.new("cam"); cd.lens = 33
cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.8
cd.dof.focus_distance = 2.1
cam = bpy.data.objects.new("cam", cd); cam.location = (-1.42, -2.25, 1.34); link(cam)
cam.rotation_euler = (rad(79.6), 0, rad(-27.5))
scene.camera = cam

# ---------- Cycles 渲染 ----------
scene.render.engine = 'CYCLES'
scene.cycles.samples = 224
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
scene.render.resolution_x = 2400; scene.render.resolution_y = 1500
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("COVER_DONE", OUT)
