"""v11 메시 출력: Meshes/Deploy_0/Macuahuitl.fbx + Macuahuitl_Base.fbx + mesh_contract.json 갱신.

v10 FBX 구조를 그대로 따른다 (v10 파일을 Blender 기본 FBX 임포터로 되읽어 확인, 오차 0):
  - 오브젝트 9개 이름 MAC_R/L_UpperArm·LowerArm·Hand, MAC_Handle·Body·Obsidian
  - 각 오브젝트 위치 = 계약 휴지 이동값, 회전·스케일 항등, 메시 = 휴지 월드 - 원점
  - 기본 축/단위 설정 export_scene.fbx
재질 이름: 팔 MAC_Jade_arms (v10 그대로), 몸체 MAC_Jade_body, 흑요석 MAC_Jade_edge,
          손잡이 MAC_Jade_handle(가죽 감개) + MAC_Jade_handle_copper / _jade / _leather.
사용: Blender 안에서 import 후 export() — 끝나면 되읽어 정점 오차를 돌려준다.
"""
import json
import os
import shutil

import bpy
import numpy as np
from mathutils import Matrix, Vector

V11 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = ["MAC_R_UpperArm", "MAC_R_LowerArm", "MAC_R_Hand", "MAC_L_UpperArm", "MAC_L_LowerArm", "MAC_L_Hand",
         "MAC_Handle", "MAC_Body", "MAC_Obsidian"]
WEAPON = ("MAC_Handle", "MAC_Body", "MAC_Obsidian")
MATERIALS = {"MAC_Handle": ["MAC_Jade_handle_copper", "MAC_Jade_handle_leather", "MAC_Jade_handle_jade", "MAC_Jade_handle"],
             "MAC_Body": ["MAC_Jade_body"], "MAC_Obsidian": ["MAC_Jade_edge"]}


def _rest_ctrl():
    cr = bpy.data.objects["V11_WPN_Ctrl"]["v11_rest_matrix"]
    return Matrix([cr[0:4], cr[4:8], cr[8:12], cr[12:16]])


def weapon_rest_origin(part):
    src = bpy.data.objects["V11_" + part]
    return (_rest_ctrl() @ src.matrix_parent_inverse @ src.matrix_basis).translation.copy()


def ensure_material_names():
    ours = {m for p in WEAPON for m in bpy.data.objects["V11_" + p].data.materials if m}
    for part, names in MATERIALS.items():
        me = bpy.data.objects["V11_" + part].data
        for i, target in enumerate(names):
            m = me.materials[i]
            if m.name == target:
                continue
            other = bpy.data.materials.get(target)
            if other is not None and other not in ours:
                other.name = target + "__v10"
            m.name = target


def export(check=True):
    contract_path = os.path.join(V11, "mesh_contract.json")
    contract = json.load(open(contract_path, encoding="utf-8"))
    CT = {p["name"]: Vector(p["matrix_blender"][i][3] for i in range(3)) for p in contract["parts"]}
    ensure_material_names()
    held = {}
    for n in NAMES:
        o = bpy.data.objects.get(n)
        if o is not None:
            o.name = n + "__v11hold"
            held[o.name] = n
    sc = bpy.data.scenes.new("V11_Export")
    win = bpy.context.window_manager.windows[0]
    prev = win.scene
    new_T, exp = {}, []
    try:
        for n in NAMES:
            if n in WEAPON:
                me = bpy.data.objects["V11_" + n].data
                loc = weapon_rest_origin(n)
                new_T[n] = loc
            else:
                me = bpy.data.objects["ALL_" + n].data          # 팔은 v10 기본 메시 그대로
                loc = CT[n]
            o = bpy.data.objects.new(n, me)
            o.location = loc
            sc.collection.objects.link(o)
            exp.append(o)
        win.scene = sc
        vl = sc.view_layers[0]
        for o in exp:
            o.select_set(True)
        out_path = os.path.join(V11, "Meshes", "Deploy_0", "Macuahuitl.fbx")
        with bpy.context.temp_override(window=win, scene=sc, view_layer=vl, selected_objects=exp, active_object=exp[0]):
            bpy.ops.export_scene.fbx(filepath=out_path, use_selection=True, object_types={'MESH'}, use_mesh_modifiers=True,
                                     mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False,
                                     path_mode='COPY', embed_textures=True)
        shutil.copyfile(out_path, os.path.join(V11, "Macuahuitl_Base.fbx"))
        expected = {o.name: np.array([list(o.matrix_world @ v.co) for v in o.data.vertices]) for o in exp}
    finally:
        for o in exp:
            bpy.data.objects.remove(o, do_unlink=True)
        for h, n in held.items():
            bpy.data.objects[h].name = n
        win.scene = prev
        bpy.data.scenes.remove(sc)
    errs = check_fbx(out_path, expected) if check else None
    for p in contract["parts"]:
        if p["name"] in new_T:
            t = new_T[p["name"]]
            p["matrix_blender"] = [[1.0, 0.0, 0.0, t.x], [0.0, 1.0, 0.0, t.y], [0.0, 0.0, 1.0, t.z], [0.0, 0.0, 0.0, 1.0]]
            p["level_origin_before_T_cm"] = [-t.x * 100, t.z * 100, t.y * 100]
    contract.setdefault("v11", {})["materials"] = {p: MATERIALS[p] for p in WEAPON} | {"arms": "MAC_Jade_arms"}
    json.dump(contract, open(contract_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return {"fbx": out_path, "size_mb": round(os.path.getsize(out_path) / 1e6, 2), "reimport_err": errs}


def check_fbx(path, expected):
    chk = bpy.data.scenes.new("V11_FBXCheck")
    win = bpy.context.window_manager.windows[0]
    prev = win.scene
    win.scene = chk
    before = set(bpy.data.objects.keys())
    mats_before = set(bpy.data.materials.keys())
    try:
        with bpy.context.temp_override(window=win, scene=chk, view_layer=chk.view_layers[0]):
            bpy.ops.import_scene.fbx(filepath=path)
        imp = [bpy.data.objects[k] for k in set(bpy.data.objects.keys()) - before]
        errs = {}
        for o in imp:
            base = o.name.split(".")[0]
            if base in expected and len(o.data.vertices) == len(expected[base]):
                W = np.array([list(o.matrix_world @ v.co) for v in o.data.vertices])
                errs[base] = round(float(np.abs(W - expected[base]).max()) * 100, 4)
            elif base in expected:
                errs[base] = "vertex count mismatch"
        for o in imp:
            bpy.data.objects.remove(o, do_unlink=True)
    finally:
        win.scene = prev
        bpy.data.scenes.remove(chk)
        for name in set(bpy.data.materials.keys()) - mats_before:
            m = bpy.data.materials.get(name)
            if m is not None and m.users == 0:
                bpy.data.materials.remove(m)
    return errs
