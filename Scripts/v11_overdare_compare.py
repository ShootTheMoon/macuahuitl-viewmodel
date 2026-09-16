"""흑요석 감축 전(194k)·후(임포트용 FBX 28k) 같은 좌표계 비교 + 표면 오차.
blender.exe --background Macuahuitl_Rework_v11.blend --factory-startup --python v11_overdare_compare.py
-> Import_OVERDARE/QA/obsidian_before_after.png (위 원본, 아래 임포트용) · obsidian_deviation.json
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

V11 = r"C:\Users\29\Desktop\Macuahuitl\Macuahuitl_Rework_v11_TwoHand"
sys.path.insert(0, os.path.join(V11, "Scripts"))
import v11_overdare_import as imp  # noqa: E402

OUT = os.path.join(V11, "Import_OVERDARE", "QA")
FBX = os.path.join(V11, "Import_OVERDARE", "Meshes", "Macuahuitl_Viewmodel_v11_MAC_Obsidian.fbx")
os.makedirs(OUT, exist_ok=True)

me_a, center, ext = imp.baked_mesh("MAC_Obsidian")      # 원본, 경계상자 중심 기준
sc = bpy.data.scenes.new("_compare")
bpy.context.window_manager.windows and None
A = bpy.data.objects.new("orig", me_a)
sc.collection.objects.link(A)
before = set(bpy.data.objects)
with bpy.context.temp_override(scene=sc, view_layer=sc.view_layers[0]):
    bpy.ops.import_scene.fbx(filepath=FBX)
B = [o for o in bpy.data.objects if o not in before and o.type == 'MESH'][0]
if B.name not in sc.collection.objects:
    for c in B.users_collection:
        c.objects.unlink(B)
    sc.collection.objects.link(B)
B.location = (0, 0, 0)
B.rotation_euler = (0, 0, 0)
B.scale = (1, 1, 1)
sc.view_layers[0].update()


def world_verts(o):
    return [o.matrix_world @ v.co for v in o.data.vertices]


# FBX 임포트는 축/단위 변환을 오브젝트 행렬에 넣을 수 있어 메시 좌표를 원본에 직접 맞춘다 (경계상자 정렬)
vb = [v.co.copy() for v in B.data.vertices]
va = [v.co.copy() for v in me_a.vertices]
def bb(vs):
    mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
    return (mn + mx) / 2, mx - mn
ca, ea = bb(va)
cb, eb = bb(vb)
# 축 대응 찾기 (크기 순서가 같게) + 부호
order_a = sorted(range(3), key=lambda i: ea[i])
order_b = sorted(range(3), key=lambda i: eb[i])
perm = [0, 0, 0]
for ia, ib in zip(order_a, order_b):
    perm[ia] = ib
scale = sum(ea[i] for i in range(3)) / max(1e-9, sum(eb[perm[i]] for i in range(3)))
best = None
bvh_a = BVHTree.FromPolygons(va, [p.vertices for p in me_a.polygons])
import itertools
for signs in itertools.product((1, -1), repeat=3):
    mapped = [Vector([signs[i] * (v[perm[i]] - cb[perm[i]]) * scale + ca[i] for i in range(3)]) for v in vb[::97]]
    d = sum((bvh_a.find_nearest(p)[3] or 0) for p in mapped) / len(mapped)
    if best is None or d < best[0]:
        best = (d, signs)
signs = best[1]
for i, v in enumerate(B.data.vertices):
    co = vb[i]
    v.co = Vector([signs[k] * (co[perm[k]] - cb[perm[k]]) * scale + ca[k] for k in range(3)])
B.data.update()
vb2 = [v.co for v in B.data.vertices]
bvh_b = BVHTree.FromPolygons(vb2, [p.vertices for p in B.data.polygons])
d_ba = [bvh_a.find_nearest(p)[3] for p in vb2]
d_ab = [bvh_b.find_nearest(p)[3] for p in va[::5]]
dev = {
    "tris_before": sum(len(p.vertices) - 2 for p in me_a.polygons),
    "tris_after": sum(len(p.vertices) - 2 for p in B.data.polygons),
    "fbx_axis_perm": perm, "fbx_axis_signs": list(signs), "fbx_scale_to_blender": round(scale, 5),
    "decimated_to_original_mm": {"mean": round(sum(d_ba) / len(d_ba) * 1000, 3), "max": round(max(d_ba) * 1000, 3)},
    "original_to_decimated_mm": {"mean": round(sum(d_ab) / len(d_ab) * 1000, 3), "max": round(max(d_ab) * 1000, 3),
                                 "p99": round(sorted(d_ab)[int(len(d_ab) * 0.99)] * 1000, 3)},
    "weapon_length_m": round(max(ea), 3),
}
json.dump(dev, open(os.path.join(OUT, "obsidian_deviation.json"), "w"), indent=2)
print("DEV", json.dumps(dev))

# 렌더: 날 길이 축을 화면 가로로, 넓은 면이 카메라를 보게. 원본 위, 감축본 아래
long_ax = max(range(3), key=lambda i: ea[i])
thin_ax = min(range(3), key=lambda i: ea[i])
mid_ax = 3 - long_ax - thin_ax
axes = [Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))]
gap = ea[mid_ax] * 1.15
A.location = -ca + axes[mid_ax] * (gap / 2)
B.location = -ca - axes[mid_ax] * (gap / 2)
mat = bpy.data.materials.new("obs_cmp")
mat.use_nodes = True
bs = mat.node_tree.nodes["Principled BSDF"]
bs.inputs["Base Color"].default_value = (0.08, 0.09, 0.1, 1)
bs.inputs["Metallic"].default_value = 0.2
bs.inputs["Roughness"].default_value = 0.35
for o in (A, B):
    o.data.materials.clear()
    o.data.materials.append(mat)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
cam.data.type = 'ORTHO'
cam.data.ortho_scale = max(ea[long_ax], gap * 2) * 1.08
view = axes[thin_ax]
cam.location = view * 3.0
up = axes[mid_ax]
cam.rotation_euler = (-view).to_track_quat('-Z', 'Y').to_euler()
# up 방향 맞추기
q = (-view).to_track_quat('-Z', 'Y')
cur_up = q @ Vector((0, 1, 0))
ang = math.atan2(view.dot(cur_up.cross(up)), cur_up.dot(up))
from mathutils import Quaternion
cam.rotation_euler = (Quaternion(-view, -ang) @ q).to_euler() if abs(ang) > 1e-3 else q.to_euler()
for off, energy in ((view * 2 + up * 2, 300), (view * 2 - up * 1.5 + axes[long_ax], 150), (-view * 2 + up, 200)):
    L = bpy.data.objects.new("L", bpy.data.lights.new("L", 'AREA'))
    L.data.energy = energy
    L.data.size = 1.5
    L.location = off
    L.rotation_euler = (-off).to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(L)
w = bpy.data.worlds.new("w_cmp")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.03, 0.032, 0.036, 1)
sc.world = w
sc.camera = cam
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.render.filepath = os.path.join(OUT, "obsidian_before_after.png")
with bpy.context.temp_override(scene=sc, view_layer=sc.view_layers[0]):
    bpy.ops.render.render(write_still=True, scene=sc.name)
print("WROTE", sc.render.filepath)
