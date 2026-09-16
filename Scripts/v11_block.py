"""v11 양손 막기 3종 (BlockIn · BlockHold · BlockOut) — 새 무기 궤적 + 양팔 IK.

v10 막기는 한손으로 칼날을 화면 왼쪽으로 눕혔다. 양손으로 쥐면 아래 손(왼손)이 폼멜 쪽이라
왼팔이 21 cm 이상 모자라므로, 칼날을 화면 오른쪽으로 두고 넓은 면을 정면으로 세운 자세로 바꾼다.

  BlockIn  : 시작 = v10 BlockIn 첫 프레임 + 스탠스 (전환과 맞음) → 막기 자세, 약간 넘쳤다 정착
  BlockHold: 막기 자세 + 미세 흔들림 (루프, 첫 = 끝)
  BlockOut : 막기 자세 → v10 BlockOut 끝 프레임 + 스탠스
길이·프레임 수는 v10 과 같다. 팔 기준(어깨 움직임·팔꿈치 방향)은 v10 막기 클립에서 가져온다.
"""
import copy
import math
import os

from mathutils import Euler, Matrix, Vector

import v11_batch
import v11_convention as cv
import v11_io
import v11_retarget as rt

# 막기 자세 (Blender 월드, v10 휴지 기준 카메라: 위치 (-0.032, 0.305, 1.375), 정면 -Y, 위 +Z)
BLOCK_GRIP_R = Vector((0.05, -0.30, 1.18))     # 오른손 그립 위치 (눈높이 20 cm 아래, 화면 가운데 약간 왼쪽)
BLOCK_BLADE_DIR = Vector((-0.80, -0.45, 0.35))  # 칼끝 방향: 화면 오른쪽(-X) + 멀리(-Y) + 위(+Z) 대각선 가드
BLOCK_FACE_DIR = Vector((0.0, -1.0, 0.0))       # 넓은 면(모델 Z) 이 향할 방향: 정면(상대 쪽)
SWAY_ROT_DEG = 1.2
SWAY_POS_M = 0.004


def weapon_rest():
    import bpy
    ctrl = bpy.data.objects["V11_WPN_Ctrl"]
    cr = ctrl["v11_rest_matrix"]
    CR = Matrix([cr[0:4], cr[4:8], cr[8:12], cr[12:16]])
    return CR  # 무기 제어 휴지 월드 (위치 = 오른손 그립점, 회전 = 모델 축)


def block_delta(CR, extra=Matrix.Identity(4)):
    """휴지 무기 -> 막기 자세 델타.
    모델 X(폼멜 방향) = -칼끝 방향, 모델 Z(두께) = 정면 쪽으로 직교화, 모델 Y = Z × X."""
    X = -BLOCK_BLADE_DIR.normalized()
    Z = BLOCK_FACE_DIR - X * BLOCK_FACE_DIR.dot(X)
    Z.normalize()
    Y = Z.cross(X)
    R_target = Matrix((X, Y, Z)).transposed().to_4x4()
    R_rest = CR.to_quaternion().to_matrix().to_4x4()
    return Matrix.Translation(BLOCK_GRIP_R) @ extra @ R_target @ R_rest.inverted() @ Matrix.Translation(-CR.translation)


def ease_in_out(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def back_out(t, s=1.2):
    t -= 1.0
    return t * t * ((s + 1) * t + s) + 1.0


def interp(D0, D1, t, center):
    """blend_about 의 t 범위 제한 없는 판 (넘침용)."""
    q = D0.to_quaternion().slerp(D1.to_quaternion(), max(0.0, min(1.0, t)))
    if t > 1.0:  # 넘침: 회전 차이를 조금 더 진행
        extra = D0.to_quaternion().rotation_difference(D1.to_quaternion())
        axis, ang = extra.to_axis_angle()
        from mathutils import Quaternion
        q = Quaternion(axis, ang * (t - 1.0)) @ D1.to_quaternion()
    p = (D0 @ center).lerp(D1 @ center, t)
    return Matrix.Translation(p) @ q.to_matrix().to_4x4() @ Matrix.Translation(-center)


def build(write=True):
    CT, JL, G, man = v11_batch.context()
    import bpy
    JR = rt.rest_joints(lambda p: bpy.data.objects["ALL_" + p].data, lambda p: CT[p], "R")
    CR = weapon_rest()
    center = CR.translation.copy()
    ST = Matrix.Translation(rt.STANCE_T)
    D_block = block_delta(CR)
    report = {}
    for name in ("BlockIn", "BlockHold", "BlockOut"):
        fname = "ViewmodelAnimMaxico%s.lua" % name
        src = v11_io.read_clip(v11_batch.v11_retime.source_path(fname))
        n = len(src["frames"])
        w_src = [ST @ cv.lua_to_delta(*r) for r in v11_io.part_track(src, "MAC_Handle")]
        Dw = []
        for k in range(n):
            t = k / (n - 1)
            if name == "BlockIn":
                Dw.append(interp(w_src[0], D_block, back_out(t, 1.0) if k < n - 1 else 1.0, center))
            elif name == "BlockHold":
                ph = 2 * math.pi * k / (n - 1)
                sway = Matrix.Translation(Vector((0, 0, SWAY_POS_M * math.sin(ph)))) @ \
                    about_center(center_after(D_block, center),
                                 Euler((math.radians(SWAY_ROT_DEG) * math.sin(ph + 0.9), 0,
                                        math.radians(SWAY_ROT_DEG * 0.6) * math.sin(2 * ph)), 'XYZ').to_matrix().to_4x4())
                Dw.append(sway @ D_block)
            else:
                Dw.append(interp(D_block, w_src[-1], ease_in_out(t), center))
        rows, diags = rt.author_clip(src, v11_io.part_track, Dw, JL, JR, G, [1.0] * n,
                                     loop=bool(man[name].get("loop")))
        new = copy.deepcopy(src)
        rt.apply_rows(new, rows)
        new["comments"] = ["-- Maxico%s : v11 two-hand — 양손 가로 막기 (칼날 화면 오른쪽, 넓은 면 정면)" % name,
                           "--   v11_block.py 가 생성한다. 좌표 규약은 v11_convention.py 참고."]
        if write:
            v11_io.write_clip(os.path.join(v11_batch.V11, "Clips", fname), new)
        seam = max(abs(a - b) for a, b in zip(new["frames"][0][1:], new["frames"][-1][1:])) if man[name].get("loop") else None
        report[name] = {"frames": n, "loop_seam": seam,
                        **{"%s_%s" % (s, k): (len(v) if isinstance(v, list) else round(v, 2)) for s, d in diags.items() for k, v in d.items()}}
    return report


def center_after(D, center):
    return D @ center


def about_center(point, R4):
    return Matrix.Translation(point) @ R4 @ Matrix.Translation(-point)
