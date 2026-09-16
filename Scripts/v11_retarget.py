"""v11 양손 팔 풀이 (Blender mathutils 안에서 실행).

두 가지 사용 방식:
  retarget_left  : v10 클립 그대로 + 스탠스 이동 + 왼팔만 손잡이로 IK (평타·이동 등 25개)
  author_clip    : 새로 만든 무기 궤적을 받아 양팔 모두 IK (막기 3종·연출 6개)

팔 1개 풀이 (solve_arm):
  1. 손 목표(그립) 델타 -> 손목 목표 = 목표 · 손 근위 관절
  2. 어깨 내밀기: 어깨↔손목 거리가 팔 길이 × REACH_RATIO 를 넘으면 초과분만큼(최대 SHOULDER_CAP)
     어깨를 손목 쪽으로 옮긴다. 초과량 곡선은 앞뒤 평활 (루프 클립은 주기 평활).
  3. 2본 IK: 팔꿈치는 원래 팔꿈치 방향(폴)을 유지.
  4. 위팔·아래팔은 원래 델타에 "축만 돌리는 최소 회전"을 곱해 원래 비틀림을 보존.
  5. 그립 가중치 w: 파트마다 원래 델타 ↔ IK 델타를 자기 근위 관절 기준으로 섞는다.
     w=0 이면 원래 그대로, w=1 이면 IK 그대로.
관절 정의 = v10 과 같음: 팔 조각 메시 주축(PCA) 끝점. 휴지 좌표 = 메시 로컬 + 계약 이동값.
"""
import math

from mathutils import Matrix, Vector

import v11_convention as cv

REACH_RATIO = 0.985
SHOULDER_CAP = 0.15
SIDES = {
    "L": ("MAC_L_UpperArm", "MAC_L_LowerArm", "MAC_L_Hand"),
    "R": ("MAC_R_UpperArm", "MAC_R_LowerArm", "MAC_R_Hand"),
}
# 양손 스탠스: 무기 + 오른팔 전체를 몸 중앙 쪽으로 옮기는 고정 이동 (Blender 월드, m).
STANCE_T = Vector((0.06, 0.02, 0.03))
WEAPON = ("MAC_Handle", "MAC_Body", "MAC_Obsidian")
RIGHT_AND_WEAPON = SIDES["R"] + WEAPON


# ---------------------------------------------------------------- 휴지 관절
def _pca_ends(points):
    n = len(points)
    c = sum(points, Vector()) / n
    cov = [[sum((p[i] - c[i]) * (p[j] - c[j]) for p in points) / n for j in range(3)] for i in range(3)]
    v = Vector((0.3, 1.0, 0.2))
    for _ in range(100):
        v = Vector([sum(cov[i][j] * v[j] for j in range(3)) for i in range(3)]).normalized()
    s = [(p - c).dot(v) for p in points]
    return c + v * min(s), c + v * max(s)


def rest_joints(mesh_of, contract_t, side="L"):
    """mesh_of(part) -> bpy Mesh, contract_t(part) -> Vector. 반환: 관절 dict (휴지 월드)."""
    up, lo, ha = SIDES[side]
    pts = {p: [v.co + contract_t(p) for v in mesh_of(p).vertices] for p in (up, lo, ha)}
    u1, u2 = _pca_ends(pts[up])
    l1, l2 = _pca_ends(pts[lo])
    h1, h2 = _pca_ends(pts[ha])
    hand_c = sum(pts[ha], Vector()) / len(pts[ha])
    S, Eu = (u1, u2) if (u1 - hand_c).length > (u2 - hand_c).length else (u2, u1)
    El, Wl = (l1, l2) if (l1 - Eu).length < (l2 - Eu).length else (l2, l1)
    Wh = h1 if (h1 - Wl).length < (h2 - Wl).length else h2
    E = (Eu + El) / 2
    W = (Wl + Wh) / 2
    return {"S": S, "Eu": Eu, "El": El, "Wl": Wl, "Wh": Wh, "E": E, "W": W,
            "L1": (S - E).length, "L2": (E - W).length}


# ---------------------------------------------------------------- 수학 도구
def rot_between(a, b):
    return a.normalized().rotation_difference(b.normalized()).to_matrix().to_4x4()


def about(point, R4):
    return Matrix.Translation(point) @ R4 @ Matrix.Translation(-point)


def blend_about(D0, D1, w, center):
    """두 델타를 center(휴지 월드 점) 기준으로 섞는다: 회전 slerp, center 의 월드 위치 lerp."""
    if w <= 0.0:
        return D0.copy()
    if w >= 1.0:
        return D1.copy()
    q = D0.to_quaternion().slerp(D1.to_quaternion(), w)
    p = (D0 @ center).lerp(D1 @ center, w)
    return Matrix.Translation(p) @ q.to_matrix().to_4x4() @ Matrix.Translation(-center)


def smooth_series(values, passes=2, alpha=0.35, loop=False):
    """앞뒤 지수 평활. loop=True 면 첫 프레임 = 끝 프레임(이음새) 인 주기 곡선으로 다룬다."""
    if loop and len(values) > 2:
        period = list(values[:-1])
        tripled = smooth_series(period * 3, passes, alpha, loop=False)
        mid = tripled[len(period):2 * len(period)]
        return mid + [mid[0]]
    out = list(values)
    for _ in range(passes):
        acc = out[0]
        for i in range(len(out)):
            acc = acc + (out[i] - acc) * alpha
            out[i] = max(out[i], acc) if values[i] > 0 else acc
        acc = out[-1]
        for i in range(len(out) - 1, -1, -1):
            acc = acc + (out[i] - acc) * alpha
            out[i] = max(out[i], acc) if values[i] > 0 else acc
    return out


def two_bone(S, Wt, L1, L2, pole_point):
    d = Wt - S
    dist = d.length
    dist_c = min(max(dist, abs(L1 - L2) + 1e-4), L1 + L2 - 1e-4)
    u = d.normalized()
    a = (L1 * L1 - L2 * L2 + dist_c * dist_c) / (2 * dist_c)
    h = math.sqrt(max(L1 * L1 - a * a, 0.0))
    pv = pole_point - S
    pv = pv - u * pv.dot(u)
    if pv.length < 1e-6:
        pv = u.orthogonal()
    return S + u * a + pv.normalized() * h, dist > L1 + L2


# ---------------------------------------------------------------- 팔 1개 풀이
# v11.3: 팔 메시는 v10 기본 그대로. 위팔의 잘린 어깨 끝이 게임 카메라에 들어오지 않도록
#        어깨를 내미는 방향을 프레임마다 고른다 (손목 쪽 / 아래 / 카메라 쪽 섞음).
# VIS[side](위팔 델타) -> 벌점 (0 = 잘린 끝이 화면 밖, 양수 = 화면 안으로 들어온 NDC 거리). v11_batch.setup_visibility() 가 채움.
VIS = {}
_DOWN = Vector((0.0, 0.0, -1.0))
_BACK = Vector((0.0, 1.0, 0.0))        # 카메라 쪽 (게임 카메라는 -Y 를 봄)


def _ik_pose(Du, Dl, S0, S, Wt, J):
    E_orig = (Du @ J["Eu"] + Dl @ J["El"]) / 2
    E_new, over = two_bone(S, Wt, J["L1"], J["L2"], E_orig)
    u0 = (Du @ J["Eu"]) - S0
    base_u = Matrix.Translation(S - S0) @ Du
    du_ik = about(S, rot_between(u0, E_new - S)) @ base_u
    base_l = Matrix.Translation(E_new - (Dl @ J["El"])) @ Dl
    v0 = (base_l @ J["Wl"]) - E_new
    dl_ik = about(E_new, rot_between(v0, Wt - E_new)) @ base_l
    return du_ik, dl_ik, over


def _shift_needed(P, d, R):
    b = P.dot(d)
    disc = b * b - P.length_squared + R * R
    if disc < 0:
        return None
    return max(b - math.sqrt(disc), 0.0)


def _choose_offset(Du, Dl, S0, Wt, J, R, vis, w):
    P = Wt - S0
    u = P.normalized()
    cands = []
    if P.length <= R:
        cands.append(Vector())
        if vis is not None:
            for d in (_DOWN, (_DOWN + _BACK).normalized(), _BACK):
                for s in (0.03, 0.06):
                    cands.append(d * s)
    else:
        dirs = [u] + [(u + _DOWN * a + _BACK * b).normalized() for a in (0.5, 1.0, 2.0) for b in (0.0, 0.5, 1.0)] \
            + [(u + _BACK * b).normalized() for b in (0.5, 1.0)]
        for d in dirs:
            s = _shift_needed(P, d, R)
            if s is not None:
                cands.append(d * min(s, SHOULDER_CAP))
        if not cands:
            cands.append(u * SHOULDER_CAP)
    best = None
    for O in cands:
        S = S0 + O
        short = max(0.0, (Wt - S).length - R)
        pen = 0.0
        if vis is not None:
            du_ik, _, _ = _ik_pose(Du, Dl, S0, S, Wt, J)
            pen = vis(blend_about(Du, du_ik, w, J["S"]))
        cost = pen * 1000.0 + short * 300.0 + O.length * 100.0
        if best is None or cost < best[0]:
            best = (cost, O)
    return best[1]


def smooth_vectors(vs, radius=3, loop=False):
    n = len(vs)
    period = n - 1 if (loop and n > 2) else n
    out = []
    for k in range(n):
        acc, ws = Vector(), 0.0
        for j in range(k - radius, k + radius + 1):
            if loop and n > 2:
                jj = j % period
            elif 0 <= j < n:
                jj = j
            else:
                continue
            wt = radius + 1 - abs(j - k)
            acc += vs[jj] * wt
            ws += wt
        out.append(acc / ws)
    if loop and n > 2:
        out[-1] = out[0].copy()
    return out


def solve_arm(Du, Dl, Dh, Dh_grip, weights, J, loop=False, side=None):
    """Du/Dl/Dh: 원래 위팔·아래팔·손 델타 목록, Dh_grip: 손잡이 위 손 델타 목록.
    반환: (Du_f, Dl_f, Dh_f, 진단)"""
    n = len(Du)
    R = (J["L1"] + J["L2"]) * REACH_RATIO
    vis = VIS.get(side)
    Wt = [Dh_grip[k] @ J["Wh"] for k in range(n)]
    S0 = [Du[k] @ J["S"] for k in range(n)]
    offsets = [_choose_offset(Du[k], Dl[k], S0[k], Wt[k], J, R, vis, weights[k]) if weights[k] > 0 else Vector()
               for k in range(n)]
    offsets = smooth_vectors(offsets, loop=loop)
    Du_f, Dl_f, Dh_f = [], [], []
    diag = {"over_frames": [], "shoulder_shift_max_cm": 0.0, "wrist_gap_max_cm": 0.0, "elbow_gap_max_cm": 0.0,
            "cut_end_visible_frames": 0}
    for k in range(n):
        w = weights[k]
        if w <= 0.0:
            du, dl, dh = Du[k].copy(), Dl[k].copy(), Dh[k].copy()
        else:
            O = offsets[k]
            S = S0[k] + O
            short = (Wt[k] - S).length - R
            if short > 0 and O.length < SHOULDER_CAP:          # 평활로 모자라진 만큼만 손목 쪽으로 보충
                O = O + (Wt[k] - S).normalized() * min(short, SHOULDER_CAP - O.length)
                S = S0[k] + O
            du_ik, dl_ik, over = _ik_pose(Du[k], Dl[k], S0[k], S, Wt[k], J)
            if over:
                diag["over_frames"].append(k)
            diag["shoulder_shift_max_cm"] = max(diag["shoulder_shift_max_cm"], O.length * 100 * w)
            du = blend_about(Du[k], du_ik, w, J["S"])
            dl = blend_about(Dl[k], dl_ik, w, J["El"])
            dh = blend_about(Dh[k], Dh_grip[k], w, J["Wh"])
        if vis is not None and vis(du) > 0:
            diag["cut_end_visible_frames"] += 1
        diag["elbow_gap_max_cm"] = max(diag["elbow_gap_max_cm"], ((du @ J["Eu"]) - (dl @ J["El"])).length * 100)
        diag["wrist_gap_max_cm"] = max(diag["wrist_gap_max_cm"], ((dl @ J["Wl"]) - (dh @ J["Wh"])).length * 100)
        Du_f.append(du)
        Dl_f.append(dl)
        Dh_f.append(dh)
    return Du_f, Dl_f, Dh_f, diag


def _deltas(track):
    return [cv.lua_to_delta(*r) for r in track]


# ---------------------------------------------------------------- 사용 방식 1: 리타깃
def retarget_left(clip, part_track, J, grip_rest_delta, weights, pinned=(), stance=None, loop=False, right_joints=None,
                  tuck=None):
    """v10 클립 -> 스탠스 이동(무기·오른팔) + 왼팔 IK.
    tuck: 왼손을 놓은 구간(가중치 < 1) 에 원래 왼손을 이만큼 옮긴 곳으로 IK (큰 무기를 뚫고 지나가지 않게 화면 아래로 뺌).
    반환: (파트 행 dict {part: [(pos,q),...]} 9개, 진단 dict)"""
    ST = Matrix.Translation(STANCE_T if stance is None else stance)
    up, lo, ha = SIDES["L"]
    Dw = [ST @ D for D in _deltas(part_track(clip, "MAC_Handle"))]
    Du, Dl, Dh = (_deltas(part_track(clip, p)) for p in (up, lo, ha))
    if tuck is not None:
        TT = Matrix.Translation(tuck)
        grips = [blend_about(TT @ Dh[k], Dw[k] @ grip_rest_delta, weights[k], J["Wh"]) for k in range(len(Dh))]
        w_use = [1.0] * len(Dh)
    else:
        grips = [D @ grip_rest_delta for D in Dw]
        w_use = weights
    Du_f, Dl_f, Dh_f, diag = solve_arm(Du, Dl, Dh, grips, w_use, J, loop, side="L")
    rows = {p: [cv.delta_to_lua(ST @ D) for D in _deltas(part_track(clip, p))] for p in WEAPON}
    rows[up] = [cv.delta_to_lua(D) for D in Du_f]
    rows[lo] = [cv.delta_to_lua(D) for D in Dl_f]
    rows[ha] = [cv.delta_to_lua(D) for D in Dh_f]
    # v11.2: 오른쪽 어깨는 스탠스로 옮기지 않는다 (카메라에 붙어 위팔 끝이 보이던 원인).
    #        오른손만 스탠스를 따라가고 위팔·아래팔은 원래 어깨에서 IK 로 푼다.
    JR = right_joints
    if JR is not None:
        uR, lR, hR = SIDES["R"]
        Ru, Rl, Rh = (_deltas(part_track(clip, p)) for p in (uR, lR, hR))
        Ru_f, Rl_f, Rh_f, diag_r = solve_arm(Ru, Rl, Rh, [ST @ D for D in Rh], [1.0] * len(Rh), JR, loop, side="R")
        rows[uR] = [cv.delta_to_lua(D) for D in Ru_f]
        rows[lR] = [cv.delta_to_lua(D) for D in Rl_f]
        rows[hR] = [cv.delta_to_lua(D) for D in Rh_f]
        for k, v in diag_r.items():
            diag["R_" + k] = v
    else:
        for p in SIDES["R"]:
            rows[p] = [cv.delta_to_lua(ST @ D) for D in _deltas(part_track(clip, p))]
    return rows, diag


# ---------------------------------------------------------------- 사용 방식 2: 새 무기 궤적
def author_clip(template, part_track, weapon_deltas, JL, JR, grip_L, weights_L, weights_R=None,
                stance=None, loop=False, grip_deltas=None, body=None):
    """grip_deltas: 손이 따라갈 델타 (None 이면 무기). 던진 뒤 빈손 동작용.
    body: 프레임별 행렬 — 팔 기준 클립(어깨)에 먼저 곱한다 (몸 비틀기·가라앉기)."""
    """template: 팔 기준 클립(어깨 움직임·팔꿈치 방향·비틀림 출처, 프레임 수 = len(weapon_deltas)).
    weapon_deltas: 스탠스까지 포함한 새 무기 델타 목록. grip_L: 왼손 그립 휴지 델타.
    오른손 그립 휴지 델타 = 항등 (v10 휴지 자세에서 오른손이 이미 손잡이를 쥠).
    반환: (파트 행 dict 9개, {"L": 진단, "R": 진단})"""
    n = len(weapon_deltas)
    if len(template["frames"]) != n:
        raise ValueError("template 프레임 수(%d) != 무기 궤적 프레임 수(%d)" % (len(template["frames"]), n))
    ST = Matrix.Translation(STANCE_T if stance is None else stance)
    weights_R = weights_R or [1.0] * n
    rows = {p: [cv.delta_to_lua(D) for D in weapon_deltas] for p in WEAPON}
    diags = {}
    # v11.2: 오른쪽 어깨도 스탠스로 옮기지 않는다 (pre = 항등) — IK 가 손을 무기까지 데려간다
    for side, J, grip, weights, pre in (("R", JR, Matrix.Identity(4), weights_R, Matrix.Identity(4)),
                                        ("L", JL, grip_L, weights_L, Matrix.Identity(4))):
        up, lo, ha = SIDES[side]
        Du, Dl, Dh = ([(body[k] if body else Matrix.Identity(4)) @ pre @ D
                       for k, D in enumerate(_deltas(part_track(template, p)))] for p in (up, lo, ha))
        targets = grip_deltas if grip_deltas is not None else weapon_deltas
        Du_f, Dl_f, Dh_f, diag = solve_arm(Du, Dl, Dh, [D @ grip for D in targets], weights, J, loop, side=side)
        rows[up] = [cv.delta_to_lua(D) for D in Du_f]
        rows[lo] = [cv.delta_to_lua(D) for D in Dl_f]
        rows[ha] = [cv.delta_to_lua(D) for D in Dh_f]
        diags[side] = diag
    return rows, diags


def apply_rows(clip, rows):
    """clip['frames'] 의 해당 파트 열을 새 값으로 바꾼다 (제자리)."""
    for part, seq in rows.items():
        i = clip["parts"].index(part)
        o = 1 + i * 7
        for k, (pos, q) in enumerate(seq):
            r = clip["frames"][k]
            r[o:o + 3] = list(pos)
            r[o + 3:o + 7] = list(q)
    return clip
