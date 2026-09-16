"""v11.4 RareDraw — 버서커식 두 손 옆으로 휘둘러 던지는 부메랑 (120프레임, 3.9667초).

비행 방향에 맞춘 던지기: 칼날을 수평으로 눕혀 두 손으로 오른쪽 뒤로 감았다가 몸을 돌려 오른쪽 -> 왼쪽으로 크게 휘두르며
두 손을 같이 놓는다. 부메랑은 휘두른 방향 그대로 왼쪽 앞으로 수평 회전하며 날아가 멀리서 돌아 오른쪽으로 되돌아온다.
두 손을 앞으로 뻗어 같이 받고, 무게에 몸째 끌려 들어왔다가 버틴다.

  row 0-12   두 손으로 들어 올리며 칼을 오른쪽으로 눕히기 시작
  row 12-28  오른쪽 뒤로 무겁게 감음 — 몸을 오른쪽으로 14° 비틀고 3 cm 가라앉음 (row 28 멈춤)
  row 28-40  몸을 풀며 오른쪽 -> 왼쪽 수평 휘두르기, 가속 (각속도 6 -> 20°/프레임)
  row 40     두 손 동시에 놓음 (release). 날아가는 속도·회전 = 휘두르던 속도·회전 그대로
  row 40-52  빈손이 휘두른 방향으로 따라 돌며 멈춤 (follow-through)
  row 52-76  빈손 준비 자세
  row 40-60  왼쪽 앞으로 수평 회전하며 날아감, 회전면을 카메라 쪽으로 기울임 -> row 60 turnaround (약 4 m)
  row 60-80  오른쪽으로 돌아 되돌아옴 (row 78 return_whoosh 로 오른쪽 가까이 지나감)
  row 76-88  두 손을 앞으로 뻗음 -> row 80-88 회전을 멈추며 손잡이를 손 쪽으로 세움 (pitch_up) -> row 88 두 손 같이 잡음
  row 88-119 무게로 몸째 끌려 들어오고 칼끝이 가라앉았다 버팀 -> 끝 자세 = v10 끝 + 스탠스
이벤트 프레임은 v10 과 같다 (release f41 · whoosh f43 · turnaround f61 · return_whoosh f79 · pitch_up f81 · catch f89).
좌표: Blender 월드 (게임 카메라 (-0.03, 0.31, 1.38) 가 -Y 를 봄, 화면 오른쪽 = -X, 위 = +Z).
"""
import copy
import json
import math
import os

import bpy
from mathutils import Matrix, Quaternion, Vector

import v11_batch
import v11_convention as cv
import v11_io
import v11_retarget as rt
import v11_retime

FRAMES = 120
RELEASE = 40
CATCH = 88
FPS = 30.0
UP = Vector((0.0, 0.0, 1.0))


def _flat(deg, z=0.03):
    a = math.radians(deg)
    return Vector((math.cos(a), math.sin(a), z)).normalized()


# (row, 오른손 그립 위치, 칼끝 방향) — 수평 휘두르기 각도 150° -> 310° (위에서 볼 때 반시계)
HAND_KEYS = [
    (12, (-0.10, -0.30, 1.10), (-0.60, 0.20, 0.77)),
    (22, (-0.21, -0.23, 1.07), (-0.82, 0.42, 0.40)),
    (28, (-0.24, -0.20, 1.03), _flat(150)),
    (32, (-0.22, -0.30, 1.05), _flat(175)),
    (35, (-0.13, -0.40, 1.09), _flat(215)),
    (38, (-0.02, -0.44, 1.11), _flat(270)),
    (RELEASE, (0.10, -0.42, 1.12), _flat(310)),
]
HOLD_ROWS = {0, 28}
FLAT_BLEND = (14, 28)                      # 이 구간에 날 넓은 면을 수평으로 눕힘
COM_MODEL = Vector((-0.15, 0.0, 0.0))      # 무기 무게중심 (모델 좌표)
FLIGHT_KEYS = [(50, (1.00, -1.60, 1.30)), (60, (0.20, -4.00, 1.55)), (70, (-1.10, -2.40, 1.45)), (78, (-0.55, -1.05, 1.35))]
BANK = 0.35                                # 회전축을 카메라(+Y) 쪽으로 기울이는 양
FOLLOW_RATES = [16, 12, 9, 6, 4, 2.5, 1.5, 0.8, 0.3, 0.1, 0.0, 0.0]   # row 41-52 빈손 따라 돌기 (°/프레임)
BODY_YAW = [(0, 0.0), (28, -14.0), (35, -2.0), (RELEASE, 10.0), (52, 8.0), (66, 0.0), (84, 0.0), (119, 0.0)]
BODY_DIP = [(0, 0.0), (28, -0.03), (38, 0.01), (46, 0.0), (CATCH, 0.0), (93, -0.05), (106, -0.01), (119, 0.0)]
SPINE = Vector((0.0, 0.18, 1.0))
ABSORB = [(CATCH, 0.0), (93, 1.0), (104, 0.45), (114, 0.0)]
ABSORB_PULL, ABSORB_DROP, ABSORB_DEG = 0.07, 0.10, 16.0


# ------------------------------------------------------------------ 도구
def _ctrl_rest():
    cr = bpy.data.objects["V11_WPN_Ctrl"]["v11_rest_matrix"]
    return Matrix([cr[0:4], cr[4:8], cr[8:12], cr[12:16]])


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _keys(keys, x):
    if x <= keys[0][0]:
        return keys[0][1]
    for (x0, y0), (x1, y1) in zip(keys, keys[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * _smooth((x - x0) / (x1 - x0))
    return keys[-1][1]


def pose_from_delta(D, CR):
    R = D.to_3x3() @ CR.to_3x3()
    return D @ CR.translation, -(R @ Vector((1, 0, 0))).normalized(), (R @ Vector((0, 0, 1))).normalized()


def delta_from_pose(g, d, n, CR):
    X = -d.normalized()
    Z = n - X * n.dot(X)
    Z.normalize()
    Y = Z.cross(X)
    Rt = Matrix((X, Y, Z)).transposed().to_4x4()
    Rr = CR.to_quaternion().to_matrix().to_4x4()
    return Matrix.Translation(g) @ Rt @ Rr.inverted() @ Matrix.Translation(-CR.translation)


def _hermite(keys, k):
    """keys: [(row, P, T)] — T 가 None 이면 Catmull-Rom 접선 (HOLD_ROWS·양 끝은 0)."""
    frames = [f for f, _, _ in keys]
    i = max(j for j in range(len(keys) - 1) if frames[j] <= k) if k < frames[-1] else len(keys) - 2

    def tan(j):
        f, P, T = keys[j]
        if T is not None:
            return T
        if f in HOLD_ROWS or j == 0 or j == len(keys) - 1:
            return P * 0.0
        return (keys[j + 1][1] - keys[j - 1][1]) / (keys[j + 1][0] - keys[j - 1][0])

    f0, p0, _ = keys[i]
    f1, p1, _ = keys[i + 1]
    h = f1 - f0
    t = (k - f0) / h
    t2, t3 = t * t, t * t * t
    return ((2 * t3 - 3 * t2 + 1) * p0 + (t3 - 2 * t2 + t) * h * tan(i)
            + (-2 * t3 + 3 * t2) * p1 + (t3 - t2) * h * tan(i + 1))


def _signed_angle(a, b, axis):
    return math.atan2(axis.dot(a.cross(b)), a.dot(b))


def _about(point, R4):
    return Matrix.Translation(point) @ R4 @ Matrix.Translation(-point)


# ------------------------------------------------------------------ 무기
def hand_phase(wsrc, CR):
    """row 0..RELEASE 무기 델타."""
    g0, d0, n0 = pose_from_delta(wsrc[0], CR)
    zero = Vector((0, 0, 0))
    gk = [(0, g0, zero)] + [(f, Vector(g), None) for f, g, _ in HAND_KEYS]
    dk = [(0, d0, zero)] + [(f, Vector(d).normalized(), None) for f, _, d in HAND_KEYS]
    dirs = [_hermite(dk, k).normalized() for k in range(RELEASE + 1)]
    n = n0.copy()
    normals = []
    for k in range(RELEASE + 1):
        if k > 0:
            n = dirs[k - 1].rotation_difference(dirs[k]) @ n
        n = (n - dirs[k] * n.dot(dirs[k])).normalized()
        normals.append(n.copy())
    a, b = FLAT_BLEND
    sign = 1.0 if normals[b].dot(UP) >= 0 else -1.0
    for k in range(a, RELEASE + 1):
        t = _smooth((k - a) / (b - a))
        target = UP * sign - dirs[k] * (UP * sign).dot(dirs[k])
        if target.length < 1e-4:
            continue
        target.normalize()
        ang = _signed_angle(normals[k], target, dirs[k]) * t
        normals[k] = (Quaternion(dirs[k], ang) @ normals[k]).normalized()
    out = [wsrc[0].copy()]
    for k in range(1, RELEASE + 1):
        out.append(delta_from_pose(_hermite(gk, k), dirs[k], normals[k], CR))
    return out


def flight_phase(hand, D_catch, CR, com_rest):
    """row RELEASE+1 .. CATCH-1 무기 델타 (CATCH 는 D_catch)."""
    CRr = CR.to_quaternion().to_matrix()

    def rot_of(D):
        return (D.to_3x3() @ CRr).to_quaternion()

    def delta_of(q, com):
        M = (q.to_matrix() @ CRr.inverted()).to_4x4()
        return Matrix.Translation(com) @ M @ Matrix.Translation(-com_rest)

    c40 = hand[RELEASE] @ com_rest
    v40 = c40 - hand[RELEASE - 1] @ com_rest
    c88 = D_catch @ com_rest
    path = [(RELEASE, c40, v40)] + [(f, Vector(p), None) for f, p in FLIGHT_KEYS] + [(CATCH, c88, Vector((0, 0.012, -0.004)))]
    # 휘두르던 각속도 (칼끝 방향이 UP 둘레로 돈 각)
    _, d39, _ = pose_from_delta(hand[RELEASE - 1], CR)
    _, d40, _ = pose_from_delta(hand[RELEASE], CR)
    w0 = math.degrees(_signed_angle(d39, d40, UP))

    def axis(k):
        return Vector((0.0, BANK * _smooth((k - RELEASE) / 15.0), 1.0)).normalized()

    def rate(k):
        if k <= 50:
            return w0 + (34.0 - w0) * _smooth((k - RELEASE) / 10.0)
        if k <= 74:
            return 34.0
        return 34.0 + (6.0 - 34.0) * _smooth((k - 74) / 12.0)

    q_catch = rot_of(D_catch)

    def spin(extra):
        q = rot_of(hand[RELEASE])
        qs = {}
        total = sum(rate(k) for k in range(RELEASE + 1, 81))
        for k in range(RELEASE + 1, CATCH + 1):
            r = rate(k) + (extra * rate(k) / total if k <= 80 else 0.0)
            q = Quaternion(axis(k), math.radians(r)) @ q
            qs[k] = q.copy()
        return qs

    qs = spin(0.0)
    A = axis(CATCH)
    tip_s = qs[CATCH] @ Vector((-1, 0, 0))
    tip_c = q_catch @ Vector((-1, 0, 0))
    ps = (tip_s - A * tip_s.dot(A)).normalized()
    pc = (tip_c - A * tip_c.dot(A)).normalized()
    delta = math.degrees(_signed_angle(ps, pc, A))
    qs = spin(delta)
    out = {}
    for k in range(RELEASE + 1, CATCH):
        q = qs[k]
        if k > 80:
            q = q.slerp(q_catch, _smooth((k - 80) / 8.0))
        out[k] = delta_of(q, _hermite(path, k))
    info = {"release_spin_deg_per_f": round(w0, 1), "align_extra_deg": round(delta, 1),
            "max_dist_m": round(max((_hermite(path, k) - Vector((-0.03, 0.31, 1.38))).length for k in range(RELEASE, CATCH)), 2),
            "release_speed_m_per_f": round(v40.length, 3)}
    return out, info


def absorb_phase(wsrc, CR):
    out = {}
    for k in range(CATCH, FRAMES):
        b = _keys(ABSORB, k)
        if b <= 1e-5:
            out[k] = wsrc[k].copy()
            continue
        g, d, _ = pose_from_delta(wsrc[k], CR)
        ax = d.cross(Vector((0, 0, -1)))
        R = Quaternion(ax.normalized(), math.radians(ABSORB_DEG * b)).to_matrix().to_4x4() if ax.length > 1e-5 else Matrix.Identity(4)
        out[k] = Matrix.Translation(Vector((0, ABSORB_PULL * b, -ABSORB_DROP * b))) @ _about(g, R) @ wsrc[k]
    return out


# ------------------------------------------------------------------ 빈손 · 몸
def ghost_hands(Dw, CR):
    ghost = [D.copy() for D in Dw]
    pivot = Vector((0.0, -0.05, 1.10))
    theta = 0.0
    for i, k in enumerate(range(RELEASE + 1, 53)):
        theta += FOLLOW_RATES[i]
        ghost[k] = Matrix.Translation(Vector((0, 0, -0.004 * (i + 1)))) @ \
            _about(pivot, Quaternion(UP, math.radians(theta)).to_matrix().to_4x4()) @ Dw[RELEASE]
    g52 = ghost[52]
    ready = Matrix.Translation(Vector((0.02, 0.04, -0.12))) @ Dw[0]
    reach = Matrix.Translation(Vector((0.0, -0.08, 0.03))) @ Dw[CATCH]
    c = CR.translation
    for k in range(53, CATCH):
        if k <= 66:
            ghost[k] = rt.blend_about(g52, ready, _smooth((k - 52) / 14.0), c)
        elif k <= 76:
            ghost[k] = ready.copy()
        elif k <= 84:
            ghost[k] = rt.blend_about(ready, reach, _smooth((k - 76) / 8.0), c)
        else:
            ghost[k] = rt.blend_about(reach, Dw[CATCH], _smooth((k - 84) / 4.0), c)
    return ghost


def body_track():
    out = []
    for k in range(FRAMES):
        yaw = math.radians(_keys(BODY_YAW, k))
        dip = _keys(BODY_DIP, k)
        out.append(Matrix.Translation(Vector((0, 0, dip))) @ _about(SPINE, Quaternion(UP, yaw).to_matrix().to_4x4()))
    return out


# ------------------------------------------------------------------ 빌드
def build(write=True):
    CT, JL, G, man = v11_batch.context()
    JR = rt.rest_joints(lambda p: bpy.data.objects["ALL_" + p].data, lambda p: CT[p], "R")
    CR = _ctrl_rest()
    ST = Matrix.Translation(rt.STANCE_T)
    com_rest = bpy.data.objects["V11_WPN_Root"].matrix_world @ COM_MODEL
    fname = "ViewmodelAnimMaxicoRareDraw.lua"
    src = v11_io.read_clip(v11_retime.source_path(fname))
    template = v11_io.read_clip(v11_retime.source_path("ViewmodelAnimMaxicoIdle.lua"))
    wsrc = [ST @ cv.lua_to_delta(*r) for r in v11_io.part_track(src, "MAC_Handle")]
    hand = hand_phase(wsrc, CR)
    absorb = absorb_phase(wsrc, CR)
    flight, finfo = flight_phase(hand, absorb[CATCH], CR, com_rest)
    Dw = [hand[k] if k <= RELEASE else (flight[k] if k < CATCH else absorb[k]) for k in range(FRAMES)]
    ghost = ghost_hands(Dw, CR)
    ones = [1.0] * FRAMES
    rows, diags = rt.author_clip(template, v11_io.part_track, Dw, JL, JR, G, ones, ones,
                                 grip_deltas=ghost, body=body_track())
    new = copy.deepcopy(src)
    rt.apply_rows(new, rows)
    new["comments"] = ["-- MaxicoRareDraw : v11 two-hand — 버서커식 두 손 수평 휘둘러 던지기 · 두 손 캐치 (비행 경로·회전 새로 제작)",
                       "--   v11_raredraw.py 가 생성한다. 좌표 규약은 v11_convention.py 참고."]
    if write:
        v11_io.write_clip(os.path.join(v11_batch.V11, "Clips", fname), new)
    W = [cv.lua_to_delta(*r) for r in v11_io.part_track(new, "MAC_Handle")]
    jump = max((W[k + 1] @ com_rest - W[k] @ com_rest).length for k in range(RELEASE - 3, CATCH + 3)) * 100
    return {"frames": FRAMES, **finfo,
            "max_com_step_cm_rows_37_91": round(jump, 1),
            "first_last_weapon_err_cm": [round((W[i].translation - wsrc[i].translation).length * 100, 3) for i in (0, -1)],
            "R": {k: (len(v) if isinstance(v, list) else round(v, 2)) for k, v in diags["R"].items()},
            "L": {k: (len(v) if isinstance(v, list) else round(v, 2)) for k, v in diags["L"].items()}}


def _hand_events():
    ev = [(RELEASE, "left_grip_release", {"strength": 1}),
          (RELEASE, "hand_mesh", {"hand": "L", "mesh": "Open"}), (RELEASE, "hand_mesh", {"hand": "R", "mesh": "Open"}),
          (CATCH, "hand_mesh", {"hand": "R", "mesh": "Grip"}), (CATCH, "hand_mesh", {"hand": "L", "mesh": "Grip"}),
          (CATCH, "left_grip_join", {"strength": 1}), (28, "heavy_windup", {"strength": 1})]
    return [dict(frame=r + 1, event=e, time=round(r / FPS, 4), **extra) for r, e, extra in ev]


def manifest_events():
    v10 = {c["name"]: c for c in json.load(open(os.path.join(v11_batch.V10, "clip_manifest.json"), encoding="utf-8"))}
    evs = [dict(e) for e in v10["RareDraw"]["events"]] + _hand_events()
    return sorted(evs, key=lambda e: e["frame"])


def effect_events():
    v10 = json.load(open(os.path.join(v11_batch.V10, "effect_events.json"), encoding="utf-8"))
    evs = [dict(e) for e in v10["clips"].get("RareDraw", [])]
    evs += [{"time": e["time"], **{k: v for k, v in e.items() if k not in ("frame", "time")}} for e in _hand_events()]
    evs.append({"time": round(CATCH / FPS, 4), "event": "camera_kick", "pitch_degrees": 0.8, "recover_seconds": 0.3})
    return sorted(evs, key=lambda e: e["time"])
