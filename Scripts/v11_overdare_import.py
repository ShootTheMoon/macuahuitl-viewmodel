"""v11 -> OVERDARE 임포트용 무기 메시 3개 만들기.

실행 (둘 중 하나):
  Blender GUI 브리지 : import v11_overdare_import; v11_overdare_import.run()
  백그라운드         : blender.exe --background Macuahuitl_Rework_v11.blend --python v11_overdare_import.py

만드는 것 (Import_OVERDARE/):
  Meshes/Macuahuitl_Viewmodel_v11_MAC_Handle.fbx    손잡이 — 단색 재질 1개 (가죽 감개·구리·옥 합침)
  Meshes/Macuahuitl_Viewmodel_v11_MAC_Body.fbx      나무 몸체 — 기본색 텍스처 1024x256 포함
  Meshes/Macuahuitl_Viewmodel_v11_MAC_Obsidian.fbx  흑요석 — 삼각형 30,000 이하로 감축
  Textures/T_MAC_Body_BaseColor_1024.png           몸체 텍스처 (Studio 에서 따로 넣을 때)
  Textures/T_MAC_Body_GlowMask.png                 변신 발광 마스크 (나중 작업용)
  level_placement.json                             파트별 레벨 CFrame 위치·예상 Size·색·재질·삼각형 수

규칙:
  - 메시는 v11 휴지 자세 월드 좌표를 굽고, 원점 = 경계상자 중심 (Studio 가 MeshPart 피벗을 중심으로 잡음)
  - 레벨 위치 = 100 × (−x, z, y) + (1000.944095, −92.593801, 1230.791631)   (게임 ViewmodelConfig 주석과 같은 식)
  - 예상 Size(cm) = 100 × (|dx|, |dz|, |dy|)
  - FBX 설정은 v10 게임 메시를 뽑을 때와 같다 (v11_export.py)
"""
import json
import os

import bpy
import bmesh
from mathutils import Matrix, Vector

V11 = r"C:\Users\29\Desktop\Macuahuitl\Macuahuitl_Rework_v11_TwoHand"
OUT = os.path.join(V11, "Import_OVERDARE")
LEVEL_T = (1000.944095, -92.593801, 1230.791631)
MAX_TRIS = 30000
TARGET_TRIS = 29000
PREFIX = "Macuahuitl_Viewmodel_v11_"


def level_pos(v):
    return [round(100 * -v.x + LEVEL_T[0], 4), round(100 * v.z + LEVEL_T[1], 4), round(100 * v.y + LEVEL_T[2], 4)]


def to_srgb8(c):
    out = []
    for x in c[:3]:
        x = max(0.0, min(1.0, x))
        s = x * 12.92 if x <= 0.0031308 else 1.055 * (x ** (1 / 2.4)) - 0.055
        out.append(int(round(s * 255)))
    return out


def tri_count(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def rest_world(name):
    src = bpy.data.objects["V11_" + name]
    cr = bpy.data.objects["V11_WPN_Ctrl"]["v11_rest_matrix"]
    CR = Matrix([cr[0:4], cr[4:8], cr[8:12], cr[12:16]])
    return src, CR @ src.matrix_parent_inverse @ src.matrix_basis


ARMS = ["MAC_R_UpperArm", "MAC_R_LowerArm", "MAC_R_Hand", "MAC_L_UpperArm", "MAC_L_LowerArm", "MAC_L_Hand"]
ARM_COLOR = [60, 91, 95]            # 게임 레벨 팔 색 그대로


def contract_t(name):
    parts = json.load(open(os.path.join(V11, "mesh_contract.json"), encoding="utf-8"))["parts"]
    p = next(p for p in parts if p["name"] == name)
    return Vector([p["matrix_blender"][i][3] for i in range(3)])


def baked_mesh(name):
    """휴지 월드로 구운 메시 사본 + 경계상자 중심 (월드)."""
    if name in ARMS:
        src = bpy.data.objects["ALL_" + name]       # v10 기본 팔 메시 (게임에 있는 것과 같음)
        M = Matrix.Translation(contract_t(name))
    else:
        src, M = rest_world(name)
    me = src.data.copy()
    me.name = PREFIX + name
    me.transform(M)
    xs = [v.co for v in me.vertices]
    mn = Vector([min(v[i] for v in xs) for i in range(3)])
    mx = Vector([max(v[i] for v in xs) for i in range(3)])
    center = (mn + mx) / 2
    me.transform(Matrix.Translation(-center))
    me.update()
    return me, center, mx - mn


def single_material(me, mat):
    me.materials.clear()
    me.materials.append(mat)
    for p in me.polygons:
        p.material_index = 0


def body_material(tex_path):
    name = PREFIX + "MAC_Body_Mat"
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(tex_path, check_existing=True)
    img.colorspace_settings.name = 'sRGB'
    tex.image = img
    bsdf.inputs["Roughness"].default_value = 0.58
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def flat_material(name, rgba, metallic, roughness):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for l in list(bsdf.inputs["Base Color"].links):
        m.node_tree.links.remove(l)
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    m.diffuse_color = rgba
    return m


def decimate(me, target):
    """COLLAPSE 감축을 목표 삼각형 수 이하가 될 때까지 반복."""
    tmp = bpy.data.objects.new("_dec_tmp", me)
    sc = bpy.context.scene                         # 이미 depsgraph 가 있는 현재 씬에 잠깐 붙였다 뗀다 (저장 안 함)
    sc.collection.objects.link(tmp)
    try:
        for _ in range(6):
            t = tri_count(me)
            if t <= target:
                break
            mod = tmp.modifiers.new("dec", 'DECIMATE')
            mod.decimate_type = 'COLLAPSE'
            mod.ratio = max(0.02, target / t * 0.98)
            mod.use_collapse_triangulate = True
            dg = bpy.context.evaluated_depsgraph_get()
            dg.update()
            ev = tmp.evaluated_get(dg)
            new = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
            tmp.modifiers.clear()
            old = tmp.data
            tmp.data = new
            new.name = old.name
            me = new
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.update()
    finally:
        sc.collection.objects.unlink(tmp)
        bpy.data.objects.remove(tmp)
    return me


def export_fbx(obj, path):
    sc = bpy.data.scenes.new("_fbx_export")
    sc.collection.objects.link(obj)
    win = bpy.context.window_manager.windows[0] if bpy.context.window_manager.windows else None
    try:
        kw = dict(filepath=path, use_selection=False, object_types={'MESH'}, use_mesh_modifiers=True,
                  mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False, path_mode='COPY', embed_textures=True)
        if win is not None:
            prev = win.scene
            win.scene = sc
            try:
                with bpy.context.temp_override(window=win, scene=sc, view_layer=sc.view_layers[0]):
                    bpy.ops.export_scene.fbx(**kw)
            finally:
                win.scene = prev
        else:
            with bpy.context.temp_override(scene=sc, view_layer=sc.view_layers[0]):
                bpy.ops.export_scene.fbx(**kw)
    finally:
        sc.collection.objects.unlink(obj)
        bpy.data.scenes.remove(sc)


def run():
    os.makedirs(os.path.join(OUT, "Meshes"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "Textures"), exist_ok=True)

    # 몸체 텍스처 1024x256 (sRGB 기본색)
    # 원본 이미지(패킹됨)를 쓴다. 색공간 설정은 해석만 바꾸므로 PNG 로 저장되는 픽셀은 같다.
    src_img = bpy.data.images["Hardwood grain and reference geometric paint"]
    if src_img.packed_file is not None and not src_img.has_data:
        src_img.reload()
    small = src_img.copy()
    small.scale(1024, 256)
    tex_path = os.path.join(OUT, "Textures", "T_MAC_Body_BaseColor_1024.png")
    small.filepath_raw = tex_path
    small.file_format = 'PNG'
    small.save()
    bpy.data.images.remove(small)
    glow = bpy.data.images.get("T_MAC_Body_GlowMask")
    if glow is not None:
        g = glow.copy()
        g.filepath_raw = os.path.join(OUT, "Textures", "T_MAC_Body_GlowMask.png")
        g.file_format = 'PNG'
        g.save()
        bpy.data.images.remove(g)

    wrap = bpy.data.materials["MAC_Jade_handle"]
    wrap_bsdf = next(n for n in wrap.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    wrap_rgb = list(wrap_bsdf.inputs["Base Color"].default_value)
    obs = bpy.data.materials["MAC_Jade_edge"]
    obs_bsdf = next(n for n in obs.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    obs_rgb = list(obs_bsdf.inputs["Base Color"].default_value)

    # 게임 화면에서 너무 검게 뭉개지지 않도록 단색은 원래 재질보다 한 단계 밝힘 (기록: raw_srgb)
    plan = {
        "MAC_Handle": {"mat": flat_material(PREFIX + "MAC_Handle_Mat", (0.045, 0.040, 0.036, 1), 0.0, 0.7),
                       "level_color": [58, 54, 50], "level_material": "Plastic", "texture": None,
                       "raw_srgb": to_srgb8(wrap_rgb), "note": "가죽 감개 기준 단색. 구리 고리·옥 폼멜·구리 가면은 같은 색이 됨"},
        "MAC_Body": {"mat": body_material(tex_path), "level_color": [255, 255, 255], "level_material": "Plastic",
                     "texture": "Textures/T_MAC_Body_BaseColor_1024.png",
                     "note": "텍스처가 곱해지므로 Color 는 흰색. 텍스처가 안 붙으면 Color = [120, 72, 44]"},
        "MAC_Obsidian": {"mat": flat_material(PREFIX + "MAC_Obsidian_Mat", (0.028, 0.034, 0.040, 1), 0.2, 0.25),
                         "level_color": [46, 50, 56], "level_material": "Metal", "texture": None,
                         "raw_srgb": to_srgb8(obs_rgb), "note": "흑요석. 원래 색은 거의 검정이라 한 단계 밝힘"},
    }
    arm_mat = flat_material(PREFIX + "MAC_Arms_Mat", (0.045, 0.105, 0.115, 1), 0.0, 0.6)
    arm_plan = {n: {"mat": arm_mat, "level_color": ARM_COLOR, "level_material": "Plastic", "texture": None,
                    "note": "v10 기본 팔 메시 그대로 (게임에 있던 팔과 같은 모양)"} for n in ARMS}
    plan = {**arm_plan, **plan}
    report = {"formula": "level = 100 x (-x, z, y) + %s" % list(LEVEL_T), "parts": {}}
    for name, cfg in plan.items():
        me, center, ext = baked_mesh(name)
        tris_before = tri_count(me)
        single_material(me, cfg["mat"])
        if name == "MAC_Obsidian":
            me = decimate(me, TARGET_TRIS)
        tris = tri_count(me)
        obj = bpy.data.objects.new(PREFIX + name, me)
        path = os.path.join(OUT, "Meshes", PREFIX + name + ".fbx")
        export_fbx(obj, path)
        # 감축 뒤 경계상자가 바뀌었을 수 있으니 다시 잼 (메시는 중심 기준이라 오프셋만 더함)
        xs = [v.co for v in me.vertices]
        mn = Vector([min(v[i] for v in xs) for i in range(3)])
        mx = Vector([max(v[i] for v in xs) for i in range(3)])
        c2 = center + (mn + mx) / 2
        e2 = mx - mn
        report["parts"][name] = {
            "fbx": os.path.relpath(path, OUT).replace("\\", "/"),
            "asset_name_hint": PREFIX + name,
            "triangles": tris, "triangles_before": tris_before, "within_limit": tris <= MAX_TRIS,
            "level_cframe_position": level_pos(c2), "level_orientation": [0, 0, 0],
            "expected_size_cm": [round(100 * abs(e2.x), 3), round(100 * abs(e2.z), 3), round(100 * abs(e2.y), 3)],
            "level_color": cfg["level_color"], "level_material": cfg["level_material"], "texture": cfg["texture"],
            "note": cfg["note"], "fbx_mb": round(os.path.getsize(path) / 1e6, 2),
            "bbox_center_shift_after_decimate_cm": round((c2 - center).length * 100, 3),
        }
        if "raw_srgb" in cfg:
            report["parts"][name]["source_material_srgb"] = cfg["raw_srgb"]
        bpy.data.objects.remove(obj)
    for n in ARMS:
        report["parts"][n]["contract_rest_level_position"] = level_pos(contract_t(n))
    report["model"] = "Workspace.Macuahuitl_Viewmodel — all 9 MeshParts replaced (full re-import)"
    json.dump(report, open(os.path.join(OUT, "level_placement.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
