"""v11 양손 리타깃 일괄 실행 (Blender 안에서 import).

원본은 항상 v10 폴더(Macuahuitl_Rework_v10/Clips)에서 읽고, v11 폴더 Clips 에 쓴다.
다시 돌려도 결과가 같다.

사용:
    import v11_batch
    report = v11_batch.run(names)          # names 생략 시 RETARGET 전체
"""
import copy
import json
import os

import bpy
from mathutils import Matrix, Vector

import v11_convention as cv
import v11_io
import v11_retarget as rt
import v11_retime

V11 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V10 = os.path.join(os.path.dirname(V11), "Macuahuitl_Rework_v10")
L3 = ("MAC_L_UpperArm", "MAC_L_LowerArm", "MAC_L_Hand")

STANDARD = [
    "RunStart", "RunLoop", "RunStop", "WalkStart", "WalkLoop", "WalkStop",
    "Attack1", "Attack2", "Attack3", "WalkAttack1", "WalkAttack2", "WalkAttack3",
    "SprintAttack1", "SprintAttack2", "SprintAttack3",
    "CrouchIn", "CrouchIdle", "CrouchAttack", "CrouchOut",
]
# 왼손 그립 가중치 키 (클립 프레임, 가중치). 사이 구간은 smootherstep.
# 근거: QA 분석 — 왼손↔손잡이 거리와 어깨 도달 초과량이 작아지는 구간에서 합류/이탈.
GRIP_KEYS = {
    "Draw": [(0, 0.0), (8, 0.0), (14, 1.0)],
    "Holster": [(0, 1.0), (6, 1.0), (12, 0.0)],
    "SprintDraw": [(0, 0.0), (17, 0.0), (23, 1.0)],
    "SprintTwirl": [(0, 1.0), (4, 1.0), (9, 0.0), (33, 0.0), (38, 1.0)],
}
# 왼손을 놓은 구간에 원래 v10 왼손 자리에서 이만큼 옮긴 곳으로 뺀다 (화면 아래·왼쪽, 큰 무기와 겹치지 않게)
TUCK = Vector((0.07, 0.06, -0.20))
# 게임 쪽 손 메시 교체 이벤트 (clip_manifest 에 추가): 가중치가 0 으로 내려가기 시작 = release, 1 에 닿음 = join
RETARGET = STANDARD + list(GRIP_KEYS)


def weights_from_keys(n, keys):
    def smoother(t):
        return t * t * t * (t * (t * 6 - 15) + 10)
    w = []
    for k in range(n):
        if k <= keys[0][0]:
            w.append(keys[0][1])
            continue
        if k >= keys[-1][0]:
            w.append(keys[-1][1])
            continue
        for (f0, w0), (f1, w1) in zip(keys, keys[1:]):
            if f0 <= k <= f1:
                t = 0.0 if f1 == f0 else (k - f0) / (f1 - f0)
                w.append(w0 + (w1 - w0) * smoother(t))
                break
    return w


def grip_keys(name, maps=None):
    """GRIP_KEYS(원본 v10 프레임 기준) -> 리타이밍된 클립 프레임 기준."""
    keys = GRIP_KEYS.get(name)
    if keys is None:
        return None
    maps = v11_retime.load_timemaps() if maps is None else maps
    if name not in maps:
        return list(keys)
    return [(int(round(maps[name].src_to_out(f))), w) for f, w in keys]


def grip_events(keys, duration, frames):
    """가중치 키 -> left_grip_release / left_grip_join 이벤트 (프레임, 시각)."""
    ev = []
    for (f0, w0), (f1, w1) in zip(keys, keys[1:]):
        if w0 > w1:
            ev.append({"frame": f0, "event": "left_grip_release", "strength": 1})
            ev.append({"frame": f0, "event": "hand_mesh", "hand": "L", "mesh": "Open"})
        elif w1 > w0:
            ev.append({"frame": f1, "event": "left_grip_join", "strength": 1})
            ev.append({"frame": f1, "event": "hand_mesh", "hand": "L", "mesh": "Grip"})
    for e in ev:
        e["time"] = round(e["frame"] * duration / max(frames - 1, 1), 4)
        e["frame"] += 1          # 매니페스트 규약: frame 은 1부터 (time = (frame-1)/30)
    return ev


def context():
    contract = json.load(open(os.path.join(V11, "mesh_contract.json"), encoding="utf-8"))
    CT = {p["name"]: Vector(p["matrix_blender"][i][3] for i in range(3)) for p in contract["parts"]}
    J = rt.rest_joints(lambda p: bpy.data.objects["ALL_" + p].data, lambda p: CT[p], "L")
    g = bpy.data.objects["V11_GRIP_L"]["v11_Lhand_delta_rest"]
    G = Matrix([g[0:4], g[4:8], g[8:12], g[12:16]])
    manifest = {c["name"]: c for c in json.load(open(os.path.join(V10, "clip_manifest.json"), encoding="utf-8"))}
    return CT, J, G, manifest


def setup_visibility(margin=0.02, scene="MAC_V11_AllClips", camera="ALL_GameCam"):
    """v11_retarget.VIS 설정: 위팔 잘린 어깨 끝(주축 끝 3 cm 정점) 이 게임 카메라 화면에 들어온 정도."""
    from bpy_extras.object_utils import world_to_camera_view
    CT = context()[0]
    sc = bpy.data.scenes[scene]
    cam = bpy.data.objects[camera]
    info = {}

    def make(side):
        J = rt.rest_joints(lambda p: bpy.data.objects["ALL_" + p].data, lambda p: CT[p], side)
        part = "MAC_%s_UpperArm" % side
        pts = [v.co + CT[part] for v in bpy.data.objects["ALL_" + part].data.vertices]
        ax = (J["S"] - J["Eu"]).normalized()
        s = [(p - J["Eu"]).dot(ax) for p in pts]
        top = max(s)
        cap = [p for p, x in zip(pts, s) if x > top - 0.03]
        info[side] = len(cap)

        def penalty(du):
            worst = 0.0
            for p in cap:
                v = world_to_camera_view(sc, cam, du @ p)
                if v.z <= 0:
                    continue
                inside = min(v.x + margin, 1 + margin - v.x, v.y + margin, 1 + margin - v.y)
                worst = max(worst, inside)
            return worst
        return penalty

    rt.VIS = {"R": make("R"), "L": make("L")}
    return info


_JR_CACHE = {}


def right_joints(CT):
    """오른팔 휴지 관절 (retarget_left 의 오른쪽 어깨 고정 IK 용)."""
    if "R" not in _JR_CACHE:
        _JR_CACHE["R"] = rt.rest_joints(lambda p: bpy.data.objects["ALL_" + p].data, lambda p: CT[p], "R")
    return _JR_CACHE["R"]


def joint_gaps(clip, J):
    tu, tl, th = (v11_io.part_track(clip, p) for p in L3)
    e = w = 0.0
    for k in range(len(clip["frames"])):
        Du, Dl, Dh = cv.lua_to_delta(*tu[k]), cv.lua_to_delta(*tl[k]), cv.lua_to_delta(*th[k])
        e = max(e, ((Du @ J["Eu"]) - (Dl @ J["El"])).length)
        w = max(w, ((Dl @ J["Wl"]) - (Dh @ J["Wh"])).length)
    return e, w


def run(names=None, write=True):
    names = names or RETARGET
    CT, J, G, manifest = context()
    maps = v11_retime.load_timemaps()
    report = {}
    for name in names:
        fname = "ViewmodelAnimMaxico%s.lua" % name
        src = v11_io.read_clip(v11_retime.source_path(fname))
        n = len(src["frames"])
        keys = grip_keys(name, maps)
        weights = weights_from_keys(n, keys) if keys else [1.0] * n
        loop = bool(manifest.get(name, {}).get("loop"))
        rows, diag = rt.retarget_left(src, v11_io.part_track, J, G, weights, loop=loop, right_joints=right_joints(CT),
                                      tuck=TUCK if keys else None)
        new = copy.deepcopy(src)
        rt.apply_rows(new, rows)
        tag = "양손 합류/이탈 가중치" if keys else "왼팔 IK"
        new["comments"] = ["-- Maxico%s : v11 two-hand — v10 무기 궤적 + 양손 스탠스 + %s" % (name, tag),
                           "--   v11_batch.py 가 생성한다. 좌표 규약은 v11_convention.py 참고."]
        if write:
            v11_io.write_clip(os.path.join(V11, "Clips", fname), new)
        seam = None
        if loop:
            seam = max(abs(a - b) for a, b in zip(new["frames"][0][1:], new["frames"][-1][1:]))
        ge, gw = joint_gaps(new, J)
        report[name] = {
            "frames": n, "loop": loop, "loop_seam": seam,
            "over_frames": len(diag["over_frames"]), "shoulder_max_cm": round(diag["shoulder_shift_max_cm"], 1),
            "elbow_gap_cm": round(ge * 100, 2), "wrist_gap_cm": round(gw * 100, 2),
            "grip_keys": keys, "grip_events": grip_events(keys, src["fields"][0][1], n) if keys else [],
        }
    return report
