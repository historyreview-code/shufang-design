import bpy, os
p = os.path.expanduser("~/创意编程探索/blender练习/04_自由女神像/statue_of_liberty.blend")
bpy.ops.wm.open_mainfile(filepath=p)
for o in bpy.data.objects:
    if o.type == 'MESH':
        d = o.dimensions
        print(f"OBJ {o.name} | type={o.type} | dims=({d.x:.2f},{d.y:.2f},{d.z:.2f}) | mats={[m.name for m in o.data.materials] if o.data.materials else []} | verts={len(o.data.vertices)}")
print("TOTAL_MESHES:", sum(1 for o in bpy.data.objects if o.type=='MESH'))
