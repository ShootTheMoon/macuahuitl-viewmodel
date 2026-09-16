"""v11 전환 20개 재생성.

v10 전환은 v6 그대로였고 끝점 자세가 클립 프레임과 0 cm 로 같았다 (v10 인계서 4절):
    Idle = Draw 끝, Run = RunStart 끝, Crouch = CrouchIn 끝, Block = BlockIn 끝, Holster = Draw 시작
v11 은 클립 자세가 바뀌었으므로:
  1. v10 전환 파일을 같은 파이프라인(스탠스 + 왼팔 IK)으로 리타깃 -> 경로 모양은 원본 유지
     (v10 에서 새 보간이 크게 휘었던 문제를 피함)
  2. 첫/끝 프레임을 v11 클립의 해당 자세 행과 정확히 같게 고정하고,
     그 보정량을 중간 프레임에 선형(회전 slerp)으로 나눠 준다
  3. Holster 로 들어가는 전환은 왼손 그립 1 -> 0, Holster 에서 나오는 전환은 0 -> 1
검증: v10 에서 전환 끝점 == 클립 자세 행 인지 먼저 확인해 보고서에 남긴다.
"""
import copy
import os

from mathutils import Matrix

import v11_batch
import v11_convention as cv
import v11_io
import v11_retarget as rt

STATES = ("Idle", "Run", "Crouch", "Block", "Holster")
# 상태 자세 = (클립, 프레임 인덱스)
POSE_SOURCE = {"Idle": ("Draw", -1), "Run": ("RunStart", -1), "Crouch": ("CrouchIn", -1),
               "Block": ("BlockIn", -1), "Holster": ("Draw", 0)}
PART_CENTER_JOINT = {"MAC_L_UpperArm": "S", "MAC_L_LowerArm": "El", "MAC_L_Hand": "Wh"}


def _clip(folder, name):
    return v11_io.read_clip(os.path.join(folder, "Clips", "ViewmodelAnimMaxico%s.lua" % name))


def _pose_row(folder, state):
    name, idx = POSE_SOURCE[state]
    return _clip(folder, name)["frames"][idx]


def _row_err_cm(r1, r2, parts):
    """두 행의 파트별 위치(공통 피벗 델타 이동) 최대 차이 cm."""
    worst = 0.0
    for i, p in enumerate(parts):
        o = 1 + i * 7
        D1 = cv.lua_to_delta(r1[o:o + 3], r1[o + 3:o + 7])
        D2 = cv.lua_to_delta(r2[o:o + 3], r2[o + 3:o + 7])
        worst = max(worst, (D1.translation - D2.translation).length * 100)
    return worst


def build(write=True):
    CT, J, G, man = v11_batch.context()
    report = {}
    for a in STATES:
        for b in STATES:
            if a == b:
                continue
            name = "Transition%sTo%s" % (a, b)
            fname = "ViewmodelAnimMaxico%s.lua" % name
            src_path = os.path.join(v11_batch.V10, "Transitions", fname)
            if not os.path.exists(src_path):
                continue
            src = v11_io.read_clip(src_path)
            parts = src["parts"]
            n = len(src["frames"])
            # v10 끝점 확인
            v10_check = [round(_row_err_cm(src["frames"][0], _pose_row(v11_batch.V10, a), parts), 3),
                         round(_row_err_cm(src["frames"][-1], _pose_row(v11_batch.V10, b), parts), 3)]
            # 1. 리타깃
            if b == "Holster":
                weights = [1.0 - k / (n - 1) for k in range(n)]
            elif a == "Holster":
                weights = [k / (n - 1) for k in range(n)]
            else:
                weights = [1.0] * n
            rows, _ = rt.retarget_left(src, v11_io.part_track, J, G, weights, right_joints=v11_batch.right_joints(CT),
                                       tuck=v11_batch.TUCK if "Holster" in (a, b) else None)
            ret = copy.deepcopy(src)
            rt.apply_rows(ret, rows)
            # 2. 끝점 고정 + 보정 분배
            tgt0 = _pose_row(v11_batch.V11, a)
            tgt1 = _pose_row(v11_batch.V11, b)
            new = copy.deepcopy(ret)
            for i, p in enumerate(parts):
                o = 1 + i * 7
                center = J[PART_CENTER_JOINT[p]] if p in PART_CENTER_JOINT else CT[p]
                R0 = cv.lua_to_delta(ret["frames"][0][o:o + 3], ret["frames"][0][o + 3:o + 7])
                R1 = cv.lua_to_delta(ret["frames"][-1][o:o + 3], ret["frames"][-1][o + 3:o + 7])
                T0 = cv.lua_to_delta(tgt0[o:o + 3], tgt0[o + 3:o + 7])
                T1 = cv.lua_to_delta(tgt1[o:o + 3], tgt1[o + 3:o + 7])
                E0 = T0 @ R0.inverted()
                E1 = T1 @ R1.inverted()
                for k in range(n):
                    t = k / (n - 1)
                    Rk = cv.lua_to_delta(ret["frames"][k][o:o + 3], ret["frames"][k][o + 3:o + 7])
                    c_world = Rk @ center
                    Ek = rt.blend_about(E0, E1, t, c_world) if 0 < k < n - 1 else (E0 if k == 0 else E1)
                    pos, q = cv.delta_to_lua(Ek @ Rk)
                    new["frames"][k][o:o + 3] = list(pos)
                    new["frames"][k][o + 3:o + 7] = list(q)
            new["frames"][0][1:] = list(tgt0[1:])
            new["frames"][-1][1:] = list(tgt1[1:])
            new["comments"] = ["-- Maxico%s : v11 two-hand — v10 전환 경로 리타깃 + 끝점을 v11 클립 자세에 고정" % name,
                               "--   v11_transitions.py 가 생성한다. 좌표 규약은 v11_convention.py 참고."]
            # 경로 휨 지표: 중간 프레임 무기 위치가 두 끝점 직선에서 벗어난 최대 거리 (cm)
            wi = parts.index("MAC_Handle")
            o = 1 + wi * 7
            P = [cv.lua_to_delta(r[o:o + 3], r[o + 3:o + 7]) @ CT["MAC_Handle"] for r in new["frames"]]
            line = P[-1] - P[0]
            dev = 0.0
            for k in range(1, n - 1):
                t = k / (n - 1)
                dev = max(dev, (P[k] - (P[0] + line * t)).length * 100)
            if write:
                v11_io.write_clip(os.path.join(v11_batch.V11, "Transitions", fname), new)
            report[name] = {"frames": n, "v10_endpoint_err_cm": v10_check,
                            "v11_endpoint_err_cm": [round(_row_err_cm(new["frames"][0], tgt0, parts), 4),
                                                    round(_row_err_cm(new["frames"][-1], tgt1, parts), 4)],
                            "weapon_path_dev_cm": round(dev, 1)}
    return report
