import bpy, math, os
from math import radians as rad

OUT_GLB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chair.glb")
OUT_PNG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chair_preview.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
CHAIR = bpy.data.collections.new("CHAIR"); scene.collection.children.link(CHAIR)
ENV   = bpy.data.collections.new("ENV");   scene.collection.children.link(ENV)
def link(ob, coll=CHAIR): coll.objects.link(ob); return ob

# ---------- 材质（命名规范：leather_main / leather_pip / plastic_dark / brass / wheel） ----------
def mat(name, base, rough, metallic=0.0, bump=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = (*base, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    if bump > 0:                       # 皮革颗粒：噪波→凹凸（全按类型接线，抗 5.x 改名）
        n = m.node_tree.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 900
        n.inputs["Detail"].default_value = 6
        bp = m.node_tree.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        m.node_tree.links.new(n.outputs["Factor"], bp.inputs["Height"])
        m.node_tree.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return m
    return m

M_LEATHER = mat("leather_main", (0.588, 0.322, 0.169), .48, bump=.25)
M_PIP     = mat("leather_pip",  (0.470, 0.250, 0.115), .50, bump=.25)
M_PLASTIC = mat("plastic_dark", (0.141, 0.114, 0.086), .55)
M_BRASS   = mat("brass",        (0.690, 0.553, 0.243), .30, metallic=.9)
M_WHEEL   = mat("wheel",        (0.090, 0.071, 0.031), .40)

def rounded_box(name, sx, sy, sz, r, pos, m, seg=4):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object
    ob.name = name; ob.scale = (sx, sy, sz); bpy.ops.object.transform_apply(scale=True)
    bevel = ob.modifiers.new("bev", "BEVEL"); bevel.width = r; bevel.segments = seg
    ob.location = pos; ob.data.materials.append(m); return link(ob)

def cyl(name, r1, r2, h, pos, m, rx=0.0, ry=0.0, rz=0.0, verts=24):
    # 5.2 起算子只支持单一 radius；原锥度差≤4mm，直接取大半径直柱
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=max(r1, r2), depth=h)
    ob = bpy.context.active_object; ob.name = name
    ob.location = pos; ob.rotation_euler = (rx, ry, rz)
    ob.data.materials.append(m); return link(ob)

def arc_shell(name, R, ang_deg, height, y_arc_center, z_center, thickness, m):
    """竖直弧形壳：凹面朝 -Y（坐者）。参数化网格 + solidify，绝无整圆筒。"""
    verts, faces = [], []
    n = 28
    a0, a1 = -rad(ang_deg/2), rad(ang_deg/2)
    for lvl, z in enumerate((z_center-height/2, z_center+height/2)):
        for i in range(n+1):
            t = a0 + (a1-a0)*i/n
            verts.append((R*math.sin(t), y_arc_center - R*math.cos(t), z))
    for i in range(n):
        faces.append((i, i+1, n+1+i+1, n+1+i))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new(name, me); link(ob)
    sol = ob.modifiers.new("sol", "SOLIDIFY"); sol.thickness = thickness
    ob.data.materials.append(m); return ob

# ---------- 建模（Blender Z-up，椅子面朝 -Y，背板在 +Y） ----------
rounded_box("seat_cushion", .52, .48, .13, .045, (0, 0, .47), M_LEATHER)
cyl("seat_tray", .235, .215, .026, (0, 0, .399), M_PLASTIC)
arc_shell("back_shell", .62, 92, .54, .75, .86, .06, M_LEATHER)
rounded_box("lumbar", .32, .06, .17, .025, (0, .135, .68), M_PIP)
neck = cyl("neck", .022, .028, .26, (0, .205, .51), M_PLASTIC); neck.rotation_euler = (rad(-10), 0, 0)
for sx in (-1, 1):
    cyl(f"arm_post_{'L' if sx<0 else 'R'}", .016, .019, .20, (sx*.27, -.02, .575), M_PLASTIC)
    rounded_box(f"arm_pad_{'L' if sx<0 else 'R'}", .055, .30, .032, .013, (sx*.27, -.02, .685), M_PIP)
cyl("gaslift", .024, .028, .33, (0, 0, .225), M_BRASS)
cyl("hub", .048, .054, .042, (0, 0, .052), M_PLASTIC)
for i in range(5):
    a = i/5 * 2*math.pi
    leg = rounded_box(f"leg_{i}", .31, .058, .03, .011, (math.sin(a)*.105, math.cos(a)*.105, .034), M_PLASTIC)
    leg.rotation_euler = (0, 0, math.pi/2 - a)
    cyl(f"caster_{i}", .027, .027, .02, (math.sin(a)*.245, math.cos(a)*.245, .027), M_WHEEL, rx=rad(90), rz=-a-math.pi/2)
    rounded_box(f"caster_fork_{i}", .055, .028, .03, .008, (math.sin(a)*.225, math.cos(a)*.225, .056), M_PLASTIC)

for ob in CHAIR.objects:                      # 圆柱/软包平滑着色
    if ob.type == 'MESH':
        for p in ob.data.polygons: p.use_smooth = True
        mod = ob.modifiers.new("asm", "SMOOTH_BY_ANGLE") if False else None
        try: bpy.context.view_layer.objects.active = ob; bpy.ops.object.shade_auto_smooth(angle=rad(40))
        except Exception: pass

# ---------- 预览渲染环境（不进 GLB） ----------
ground = bpy.ops.mesh.primitive_plane_add(size=8); ground = bpy.context.active_object
ground.location = (0, 0, 0); link(ground, ENV)
gm = bpy.data.materials.new("g"); gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (.32, .28, .23, 1)
gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = .9
ground.data.materials.append(gm)

def area(name, loc, rot, power, size=.8, color=(1, .93, .82)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.size = size; ld.color = color
    ob = bpy.data.objects.new(name, ld); ob.location = loc; ob.rotation_euler = rot; link(ob, ENV); return ob
area("key",   (1.8, -1.6, 2.0), (rad(52), 0, rad(35)), 320)
area("fill", (-2.2, -1.0, 1.3), (rad(62), 0, rad(-45)), 110)
area("rim",   (-.6, 2.6, 1.9), (rad(-58), 0, rad(180)), 160)

cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 40
cam = bpy.data.objects.new("cam", cam_d); cam.location = (1.45, -1.85, 1.05); link(cam, ENV)
cam.rotation_euler = (rad(74), 0, rad(37.5))
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 96
scene.cycles.use_denoising = True
try:
    scene.cycles.device = 'GPU'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'; prefs.get_devices()
    for d in prefs.devices: d.use = True
except Exception as e:
    print("GPU fallback CPU:", e)
scene.render.resolution_x = 1200; scene.render.resolution_y = 900
scene.render.filepath = OUT_PNG
bpy.ops.render.render(write_still=True)

# ---------- 导出 GLB（Draco） ----------
bpy.ops.object.select_all(action='DESELECT')
for ob in CHAIR.objects: ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB', use_selection=True,
    export_yup=True, export_draco_mesh_compression_enable=True,
    export_draco_mesh_compression_level=6)
print("EXPORTED", OUT_GLB, OUT_PNG, os.path.getsize(OUT_GLB))
