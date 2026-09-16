"""v11 연출 6개 (120프레임) — 양손 전환.

분석 결과 (QA 수치, 스탠스 적용 후 왼팔 도달 초과량):
  Idle · UltAttack · JumpSlam : 최대 8~11 cm  -> 리타깃(스탠스 + 왼팔 IK)으로 충분
  Transform · FirstDraw       : 전개 순간 무기를 한손으로 높이 들어 27~41 cm 초과
                                -> 양팔 IK + "도달 보정" (초과 구간에만 무기를 몸 쪽으로 당김)
  RareDraw                    : 양손 감기 -> 왼손 먼저 놓기 -> f41 투척(오른손 놓기) -> f89 오른손 캐치 -> 왼손 재파지
길이·이벤트 프레임·hitAt·jumpAt 등은 v10 과 같다. 첫/끝 프레임은 v10 + 스탠스와 같다(전환과 맞음).
"""
import copy
import os

from mathutils import Matrix, Vector

import bpy

import v11_batch
import v11_convention as cv
import v11_io
import v11_retarget as rt

MODULE = {"Idle": "Idle", "FirstDraw": "Intro", "Transform": "Transform",
          "UltAttack": "UltAttack", "JumpSlam": "JumpSlam", "RareDraw": "RareDraw"}
RETARGET_ONLY = ("Idle", "UltAttack", "JumpSlam")
# (오른손 가중치 키, 왼손 가중치 키) — 프레임, 가중치. 사이 구간 smootherstep.
AUTHOR = {
    "Transform": ([(0, 1.0)], [(0, 1.0)]),
    "FirstDraw": ([(0, 0.0), (24, 0.0), (32, 1.0)], [(0, 0.0), (30, 0.0), (38, 1.0)]),
}
# RareDraw 는 v11.2 부터 v11_raredraw.py (두 손 8자 휘돌리기) 가 만든다
CORRECTION_MARGIN = 1.08
CORRECTION_RADIUS = 6


def _smooth_vectors(vecs, radius):
    n = len(vecs)
    out = []
    for k in range(n):
        acc = Vector()
        wsum = 0.0
        for j in range(max(0, k - radius), min(n, k + radius + 1)):
            w = 1.0 - abs(j - k) / (radius + 1)
            acc += vecs[j] * w
            wsum += w
        out.append(acc / wsum)
    # 보정이 필요했던 프레임에서는 평활 때문에 줄어들지 않게 원래 크기 이상 유지
    return [o if o.length >= v.length else v for o, v in zip(out, vecs)]


def reach_correction(Dw, src, JL, G, window):
    """왼팔 도달 초과(어깨 내밀기 상한 초과분)만큼 무기를 왼쪽 어깨 쪽으로 당긴다. window[k]=True 인 프레임만."""
    tu = [cv.lua_to_delta(*r) for r in v11_io.part_track(src, "MAC_L_UpperArm")]
    limit = (JL["L1"] + JL["L2"]) * rt.REACH_RATIO + rt.SHOULDER_CAP
    shifts = []
    for k, D in enumerate(Dw):
        S = tu[k] @ JL["S"]
        Wt = D @ G @ JL["Wh"]
        e = (Wt - S).length - limit
        shifts.append((S - Wt).normalized() * e * CORRECTION_MARGIN if (window[k] and e > 0) else Vector())
    shifts = _smooth_vectors(shifts, CORRECTION_RADIUS)
    shifts[0] = Vector()
    shifts[-1] = Vector()
    return [Matrix.Translation(s) @ D for s, D in zip(shifts, Dw)], max(s.length for s in shifts)


def build(names=None, write=True):
    names = names or [n for n in MODULE if n != "RareDraw"]
    CT, JL, G, man = v11_batch.context()
    JR = rt.rest_joints(lambda p: bpy.data.objects["ALL_" + p].data, lambda p: CT[p], "R")
    ST = Matrix.Translation(rt.STANCE_T)
    report = {}
    for name in names:
        fname = "ViewmodelAnimMaxico%s.lua" % MODULE[name]
        src = v11_io.read_clip(v11_batch.v11_retime.source_path(fname))
        n = len(src["frames"])
        loop = bool(man[name].get("loop"))
        info = {"frames": n, "loop": loop}
        if name in RETARGET_ONLY:
            rows, diag = rt.retarget_left(src, v11_io.part_track, JL, G, [1.0] * n, loop=loop, right_joints=JR)
            info["L"] = {k: (len(v) if isinstance(v, list) else round(v, 2)) for k, v in diag.items()}
            tag = "스탠스 + 왼팔 IK"
            wl = [1.0] * n
        else:
            keys_r, keys_l = AUTHOR[name]
            wr = v11_batch.weights_from_keys(n, keys_r)
            wl = v11_batch.weights_from_keys(n, keys_l)
            Dw = [ST @ cv.lua_to_delta(*r) for r in v11_io.part_track(src, "MAC_Handle")]
            window = [wr[k] > 0.5 and wl[k] > 0.5 for k in range(n)]
            Dw, pull = reach_correction(Dw, src, JL, G, window)
            rows, diags = rt.author_clip(src, v11_io.part_track, Dw, JL, JR, G, wl, wr, loop=loop)
            info["weapon_pull_max_cm"] = round(pull * 100, 1)
            info.update({s: {k: (len(v) if isinstance(v, list) else round(v, 2)) for k, v in d.items()} for s, d in diags.items()})
            info["grip_events_L"] = v11_batch.grip_events(keys_l, src["fields"][0][1], n)
            tag = "양팔 IK + 도달 보정 + 그립 가중치"
        new = copy.deepcopy(src)
        rt.apply_rows(new, rows)
        new["comments"] = ["-- Maxico%s : v11 two-hand 연출 120f — v10 동작 기반 %s" % (MODULE[name], tag),
                           "--   v11_showcase.py 가 생성한다. 좌표 규약은 v11_convention.py 참고."]
        # 첫/끝 프레임 무기 = v10 + 스탠스 확인 (전환 호환)
        w_src = [ST @ cv.lua_to_delta(*r) for r in v11_io.part_track(src, "MAC_Handle")]
        w_new = [cv.lua_to_delta(*r) for r in rows["MAC_Handle"]]
        info["weapon_first_last_err_cm"] = [round((w_new[i].translation - w_src[i].translation).length * 100, 3) for i in (0, -1)]
        if loop:
            info["loop_seam"] = max(abs(a - b) for a, b in zip(new["frames"][0][1:], new["frames"][-1][1:]))
        if write:
            v11_io.write_clip(os.path.join(v11_batch.V11, "Clips", fname), new)
        report[name] = info
    return report
