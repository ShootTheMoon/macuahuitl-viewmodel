"""Lua 클립 행 <-> Blender 월드 행렬 변환 규칙 (v10 MAC_V10_AllClips 씬으로 검증, 오차 0).

검증 결과 (Attack1, 11프레임 × 9파트 = 99샘플):
  - 클립 프레임 k  <->  AllClips 씬 프레임 = 동작 마커 프레임 + k
  - Blender 쿼터니언 = (w, -x, z, y)            (Lua 는 게임 레벨 축)
  - Blender 이동량   = (-px, pz, py)             (posScale 는 게임 쪽에서만 곱함)
  - 모든 파트가 공통 회전 중심 P 기준 강체 변환:
        M_part = T(P + pos) · R(q) · T(-P) · T(rest_part)
    rest_part = mesh_contract.json 의 matrix_blender 이동값 (휴지 회전은 항등)
    → 파트 피벗을 어디에 두든 결과가 같다.
Blender(mathutils) 안에서 import 해서 쓴다.
"""
from mathutils import Matrix, Quaternion, Vector

PIVOT = Vector((0.0094, -0.0079, 1.0831))


def lua_to_delta(pos, q):
    """Lua (pos, quat wxyz) -> Blender 월드 델타 행렬 D.  M_part = D · T(rest_part)."""
    bpos = Vector((-pos[0], pos[2], pos[1]))
    bq = Quaternion((q[0], -q[1], q[3], q[2]))
    return Matrix.Translation(PIVOT + bpos) @ bq.to_matrix().to_4x4() @ Matrix.Translation(-PIVOT)


def delta_to_lua(D):
    """Blender 월드 델타 행렬 D -> Lua (pos, quat wxyz). lua_to_delta 의 역."""
    bq = D.to_quaternion().normalized()
    if bq.w < 0:
        bq.negate()
    # D = T(P + bpos) R T(-P)  ->  D.translation = P + bpos - R P
    bpos = D.translation - PIVOT + bq.to_matrix() @ PIVOT
    pos = (-bpos.x, bpos.z, bpos.y)
    q = (bq.w, -bq.x, bq.z, bq.y)
    return pos, q


def part_matrix(pos, q, rest_translation):
    return lua_to_delta(pos, q) @ Matrix.Translation(rest_translation)


def delta_from_world(M, rest_translation):
    """파트 월드 행렬(휴지 회전 항등 기준) -> 델타 D."""
    return M @ Matrix.Translation(rest_translation).inverted()
