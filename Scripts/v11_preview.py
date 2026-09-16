"""v11 미리보기: 클립 여러 개를 씬에 이어 붙여 키를 넣는다 (Blender 안에서 import).

미리보기 오브젝트 = V11_PREV_* (팔 6조각, ALL_* 메시 공유) + V11_WPN_Ctrl (무기 3파트의 부모).
클립 사이에는 hold 프레임을 둔다. 씬 마커 = 클립 이름. 반환: {마커: (시작 프레임, 끝 프레임)}.
키는 F-curve 에 한 번에 쓴다 (keyframe_insert 반복보다 훨씬 빠름 — 1451 프레임 타임라인용).
"""
import json
import os

import bpy
from mathutils import Matrix, Vector

import v11_convention as cv
import v11_io

V11 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = ["MAC_R_UpperArm", "MAC_R_LowerArm", "MAC_R_Hand", "MAC_L_UpperArm", "MAC_L_LowerArm", "MAC_L_Hand"]

# v10 MAC_V10_AllClips 와 같은 순서 (마커 이름, 모듈). hold 0 이면 프레임 번호도 v10 과 같다.
ALLCLIPS_ORDER = [
    ("Idle", "Idle"), ("FirstDraw", "Intro"), ("Draw", "Draw"), ("Holster", "Holster"), ("SprintDraw", "SprintDraw"),
    ("RunStart", "RunStart"), ("RunLoop", "RunLoop"), ("SprintTwirl", "SprintTwirl"),
    ("SprintAttack1", "SprintAttack1"), ("SprintAttack2", "SprintAttack2"), ("SprintAttack3", "SprintAttack3"),
    ("RunStop", "RunStop"), ("WalkStart", "WalkStart"), ("WalkLoop", "WalkLoop"),
    ("WalkAttack1", "WalkAttack1"), ("WalkAttack2", "WalkAttack2"), ("WalkAttack3", "WalkAttack3"), ("WalkStop", "WalkStop"),
    ("Attack1", "Attack1"), ("Attack2", "Attack2"), ("Attack3", "Attack3"),
    ("BlockIn", "BlockIn"), ("BlockHold", "BlockHold"), ("BlockOut", "BlockOut"),
    ("CrouchIn", "CrouchIn"), ("CrouchIdle", "CrouchIdle"), ("CrouchAttack", "CrouchAttack"), ("CrouchOut", "CrouchOut"),
    ("JumpSlam", "JumpSlam"), ("Transform", "Transform"), ("UltAttack", "UltAttack"), ("RareDraw", "RareDraw"),
]


def _contract():
    parts = json.load(open(os.path.join(V11, "mesh_contract.json"), encoding="utf-8"))["parts"]
    return {p["name"]: Vector(p["matrix_blender"][i][3] for i in range(3)) for p in parts}


def _write_track(obj, frames, mats):
    """행렬 목록을 location / rotation_quaternion 선형 키로 한 번에 쓴다."""
    obj.animation_data_clear()
    obj.rotation_mode = 'QUATERNION'
    locs, quats = [], []
    prev = None
    for M in mats:
        q = M.to_quaternion()
        if prev is not None and prev.dot(q) < 0:
            q.negate()
        prev = q
        locs.append(M.translation.copy())
        quats.append(q)
    action = bpy.data.actions.new(obj.name + "_V11Preview")
    ad = obj.animation_data_create()
    ad.action = action
    if hasattr(action, "slots") and hasattr(ad, "action_slot") and ad.action_slot is None:
        ad.action_slot = action.slots.new(id_type='OBJECT', name=obj.name)

    def curve(path, index):
        if hasattr(action, "fcurve_ensure_for_datablock"):
            return action.fcurve_ensure_for_datablock(obj, path, index=index)
        return action.fcurves.new(path, index=index)

    n = len(frames)
    for path, values, dims in (("location", locs, 3), ("rotation_quaternion", quats, 4)):
        for i in range(dims):
            fc = curve(path, i)
            fc.keyframe_points.add(n)
            co = []
            for f, v in zip(frames, values):
                co += [float(f), float(v[i])]
            fc.keyframe_points.foreach_set("co", co)
            fc.keyframe_points.foreach_set("interpolation", [1] * n)  # LINEAR
            fc.update()


def build(clip_names, hold=4, scene_name="MAC_V11_Rig", folder="Clips"):
    """clip_names: 모듈 이름 목록, 또는 (마커 이름, 모듈 이름) 쌍 목록."""
    CT = _contract()
    sc = bpy.data.scenes[scene_name]
    ctrl = bpy.data.objects["V11_WPN_Ctrl"]
    cr = ctrl["v11_rest_matrix"]
    CR = Matrix([cr[0:4], cr[4:8], cr[8:12], cr[12:16]])
    objs = {p: bpy.data.objects["V11_PREV_" + p[4:]] for p in ARMS}
    sc.timeline_markers.clear()
    ranges = {}
    frames = []
    mats = {p: [] for p in ARMS + ["ctrl"]}
    f = 1
    for item in clip_names:
        label, name = item if isinstance(item, (tuple, list)) else (item, item)
        path = os.path.join(V11, folder, "ViewmodelAnimMaxico%s.lua" % name)
        if not os.path.exists(path):
            path = os.path.join(V11, "Transitions", "ViewmodelAnimMaxico%s.lua" % name)
        clip = v11_io.read_clip(path)
        tracks = {p: v11_io.part_track(clip, p) for p in ARMS + ["MAC_Handle"]}
        n = len(clip["frames"])
        sc.timeline_markers.new(label, frame=f)
        start = f
        for k in list(range(n)) + [n - 1] * hold:
            for p in ARMS:
                mats[p].append(cv.part_matrix(*tracks[p][k], CT[p]))
            mats["ctrl"].append(cv.lua_to_delta(*tracks["MAC_Handle"][k]) @ CR)
            frames.append(f)
            f += 1
        ranges[label] = (start, start + n - 1)
    for p, o in objs.items():
        _write_track(o, frames, mats[p])
    _write_track(ctrl, frames, mats["ctrl"])
    sc.frame_start, sc.frame_end = 1, f - 1
    return ranges


def make_allclips(scene_name="MAC_V11_AllClips"):
    """MAC_V11_AllClips 씬: 무기·미리보기 컬렉션과 v10 게임 카메라/조명을 링크하고 32개 동작을 hold 0 으로 이어 붙인다."""
    rig = bpy.data.scenes["MAC_V11_Rig"]
    sc = bpy.data.scenes.get(scene_name) or bpy.data.scenes.new(scene_name)
    for cname in ("V11_Weapon", "V11_Preview"):
        col = bpy.data.collections[cname]
        if col.name not in sc.collection.children:
            sc.collection.children.link(col)
    for oname in ("ALL_GameCam", "ALL_Key", "ALL_Fill", "ALL_Rim", "ALL_MAC_QA_Key", "ALL_MAC_QA_Fill"):
        o = bpy.data.objects[oname]
        if o.name not in sc.collection.objects:
            sc.collection.objects.link(o)
    sc.camera = bpy.data.objects["ALL_GameCam"]
    sc.world = rig.world
    r, s0 = sc.render, rig.render
    r.engine = s0.engine
    r.resolution_x, r.resolution_y, r.resolution_percentage = s0.resolution_x, s0.resolution_y, 100
    r.fps = s0.fps
    sc.view_settings.view_transform = rig.view_settings.view_transform
    ranges = build(ALLCLIPS_ORDER, hold=0, scene_name=scene_name)
    rig.frame_start, rig.frame_end = sc.frame_start, sc.frame_end
    return sc, ranges


def render_frames(frames, prefix, camera="ALL_GameCam", scene_name="MAC_V11_Rig"):
    sc = bpy.data.scenes[scene_name]
    win = bpy.context.window_manager.windows[0]
    win.scene = sc
    prev = sc.camera
    sc.camera = bpy.data.objects[camera]
    files = []
    for fr in frames:
        sc.frame_set(fr)
        p = os.path.join(V11, "QA", "V11", "%s_f%04d.png" % (prefix, fr))
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        files.append(p)
    sc.camera = prev
    return files
