"""v11 양손 무게감 리타이밍 — v10 원본 클립을 느리게 다시 샘플링해 Work/Source/Clips 에 쓴다.

양손 대검은 무거우니까:
  평타류(10개) : 예비동작 ×1.5 · 휘두르기 ×1.2 · 타격 직후 2프레임 히트스톱 · 회수 ×1.4
                -> 감을 때 느리고, 내리칠 땐 빠르고, 맞은 뒤 무게에 끌려 천천히 돌아온다
  꺼내기·넣기·SprintDraw·SprintTwirl ×1.25, 막기 진입/해제 ×1.3 (균일)
  루프(Idle·Run·Walk·BlockHold·CrouchIdle), 이동 시작/정지, 웅크리기 진입/해제, 연출 120f 는 그대로
시간 곡선 = 매듭점을 지나는 단조 3차 보간(Fritsch–Carlson) -> 속도가 튀지 않는다.
첫/끝 프레임은 원본과 같다 (전환 호환). 타격 프레임은 원본 타격 프레임에 정확히 대응한다.

다른 스크립트(v11_batch · v11_block · v11_showcase)는 source_path() 로 이 결과를 읽는다.
시간 대응표는 Work/Source/timemap.json (out 프레임 <-> 원본 프레임).
"""
import json
import os
import shutil

import v11_io

V11 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V10 = os.path.join(os.path.dirname(V11), "Macuahuitl_Rework_v10")
SOURCE = os.path.join(V11, "Work", "Source")
TIMEMAP = os.path.join(SOURCE, "timemap.json")
FPS = 30.0

HEAVY = ("Attack1", "Attack2", "Attack3", "WalkAttack1", "WalkAttack2", "WalkAttack3",
         "SprintAttack1", "SprintAttack2", "SprintAttack3", "CrouchAttack")
HEAVY_WINDUP, HEAVY_SWING, HEAVY_RECOVER = 1.8, 1.3, 1.7
HITSTOP_FRAMES, HITSTOP_SRC = 4, 0.35
UNIFORM = {"Draw": 1.4, "Holster": 1.4, "SprintDraw": 1.4, "SprintTwirl": 1.4, "BlockIn": 1.45, "BlockOut": 1.45}
# 무게 레이어 (평타류): 무기 + 오른손을 오른손 그립점 기준으로 스윙 회전축을 따라 돌린다
#   예비 하중: 타격 전 스윙 반대 방향 최대 PRELOAD_DEG (0 과 타격 프레임에서 0)
#   밀고 나감: 히트스톱 동안 30% -> 4프레임 뒤 FOLLOW_DEG -> 끝 6프레임 전 0
PRELOAD_DEG, FOLLOW_DEG = 10.0, 14.0
# 버서커 무게 레이어 (v11.4): 손이 칼과 같이 내려가고 몸 전체가 가라앉는다
#   arc : 무기 + 오른손 이동 — 최고점에서 +ARC_RAISE 더 들고, 타격에서 ARC_DROP 아래 · ARC_FWD 앞으로, 회수하며 0
#   dip : 9개 파트 전부 이동 — 최고점 +1.2 cm, 타격 3프레임 뒤 −BODY_DIP, 천천히 복귀
ARC_RAISE, ARC_DROP, ARC_FWD, BODY_DIP = 0.04, 0.15, 0.06, 0.035
ARC_DROP_CLIP = {"CrouchAttack": 0.07}                   # 웅크린 자세는 이미 낮아 조금만
SHOWCASE_ARC = {"JumpSlam": 0.12, "UltAttack": 0.12}     # 원래 길이 연출에도 같은 레이어 (타격 = hitAt)


def _vec_keys(keys, x):
    from mathutils import Vector
    return Vector([_smooth_keys([(f, v[i]) for f, v in keys], x) for i in range(3)])


def _clean_keys(keys, n):
    out = []
    for f, v in keys:
        f = max(0, min(n - 1, int(round(f))))
        if out and f <= out[-1][0]:
            continue
        out.append((f, v))
    return out


def apply_arc_dip(clip, rows, hit, hold_end, grip_rest, drop=ARC_DROP):
    """반환: (행, 정보). hit/hold_end = 리샘플된 행 번호."""
    from mathutils import Matrix, Vector
    import v11_convention as cv
    parts = clip["parts"]
    n = len(rows)
    grip_parts = {"MAC_Handle", "MAC_Body", "MAC_Obsidian", "MAC_R_Hand"}
    oh = 1 + parts.index("MAC_Handle") * 7
    D = [cv.lua_to_delta(r[oh:oh + 3], r[oh + 3:oh + 7]) for r in rows]
    z = [(D[k] @ grip_rest).z for k in range(max(hit, 1))]
    peak = max(range(len(z)), key=lambda k: z[k])
    if peak < 2 or peak > hit - 2:
        peak = max(2, hit // 2)
    end = n - 7
    zero = (0.0, 0.0, 0.0)
    arc = _clean_keys([(0, zero), (peak, (0.0, 0.0, ARC_RAISE)), (hit, (0.0, -ARC_FWD, -drop)),
                       (hold_end, (0.0, -ARC_FWD, -drop)), (hold_end + 8, (0.0, -0.5 * ARC_FWD, -0.6 * drop)),
                       (end, zero), (n - 1, zero)], n)
    dip = _clean_keys([(0, zero), (peak, (0.0, 0.0, 0.012)), (hit, zero), (hit + 3, (0.0, 0.0, -BODY_DIP)),
                       (hit + 14, (0.0, 0.0, -0.3 * BODY_DIP)), (end, zero), (n - 1, zero)], n)
    out = []
    for k, r in enumerate(rows):
        a = _vec_keys(arc, k)
        d = _vec_keys(dip, k)
        r = list(r)
        for i, p in enumerate(parts):
            o = 1 + i * 7
            off = (a + d) if p in grip_parts else d
            if off.length < 1e-7:
                continue
            pos, q = cv.delta_to_lua(Matrix.Translation(off) @ cv.lua_to_delta(r[o:o + 3], r[o + 3:o + 7]))
            r[o:o + 3] = list(pos)
            r[o + 3:o + 7] = list(q)
        out.append(r)
    return out, {"peak": peak, "hit": hit, "drop_cm": round(drop * 100, 1)}


def _smooth_keys(keys, x):
    if x <= keys[0][0]:
        return keys[0][1]
    for (x0, y0), (x1, y1) in zip(keys, keys[1:]):
        if x <= x1:
            t = (x - x0) / (x1 - x0) if x1 > x0 else 1.0
            t = t * t * (3 - 2 * t)
            return y0 + (y1 - y0) * t
    return keys[-1][1]


def apply_heft(clip, rows, knots, grip_rest):
    """평타 리샘플 행에 무게 레이어를 더한다 (mathutils 필요). 반환: (행, 최대 각도)."""
    import math
    from mathutils import Matrix, Quaternion
    import v11_convention as cv
    parts = clip["parts"]
    moved = ("MAC_Handle", "MAC_Body", "MAC_Obsidian", "MAC_R_Hand")
    idx = {p: 1 + parts.index(p) * 7 for p in moved}
    oh = idx["MAC_Handle"]
    D = [cv.lua_to_delta(r[oh:oh + 3], r[oh + 3:oh + 7]) for r in rows]
    n = len(rows)
    h, hs = int(knots[2][0]), int(knots[3][0])
    rel = D[h].to_quaternion() @ D[max(h - 2, 0)].to_quaternion().inverted()
    axis, ang = rel.to_axis_angle()
    if ang < 1e-4:
        return rows, 0.0
    post = [(h, 0.0), (hs, 0.3 * FOLLOW_DEG), (min(hs + 4, n - 7), FOLLOW_DEG), (n - 7, 0.0)]

    def angle(k):
        if k <= h:
            return -PRELOAD_DEG * math.sin(math.pi * k / h) ** 2
        return _smooth_keys(post, k) if k < n - 7 else 0.0

    out, peak = [], 0.0
    for k, r in enumerate(rows):
        a = angle(k)
        peak = max(peak, abs(a))
        r = list(r)
        if abs(a) > 1e-6:
            g = D[k] @ grip_rest
            M = Matrix.Translation(g) @ Quaternion(axis, math.radians(a)).to_matrix().to_4x4() @ Matrix.Translation(-g)
            for p, o in idx.items():
                pos, q = cv.delta_to_lua(M @ cv.lua_to_delta(r[o:o + 3], r[o + 3:o + 7]))
                r[o:o + 3] = list(pos)
                r[o + 3:o + 7] = list(q)
        out.append(r)
    return out, peak


# ------------------------------------------------------------------ 단조 3차 보간
def _pchip(xs, ys):
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])

    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = max(j for j in range(n - 1) if xs[j] <= x)
        t = (x - xs[i]) / h[i]
        t2, t3 = t * t, t * t * t
        return ((2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h[i] * m[i]
                + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h[i] * m[i + 1])
    return f


def _event_frame(entry, kind):
    """매니페스트 이벤트 frame 은 1부터 센다 (time = (frame-1)/30). 반환은 0부터 센 클립 행 번호."""
    for e in entry["events"]:
        if e["event"] == kind:
            return e["frame"] - 1
    return None


def knots_for(name, entry):
    """(out 프레임, 원본 프레임) 매듭점. None = 리타이밍 안 함."""
    e = entry["frames"] - 1
    if name in HEAVY:
        w = _event_frame(entry, "whoosh")
        h = _event_frame(entry, "impact")
        a = round(w * HEAVY_WINDUP)
        s = a + round((h - w) * HEAVY_SWING)
        hs = s + HITSTOP_FRAMES
        end = hs + round((e - h) * HEAVY_RECOVER)
        return [(0, 0), (a, w), (s, h), (hs, h + HITSTOP_SRC), (end, e)]
    if name in UNIFORM:
        return [(0, 0), (round(e * UNIFORM[name]), e)]
    return None


class TimeMap:
    def __init__(self, knots):
        self.knots = [tuple(k) for k in knots]
        self.out_last = self.knots[-1][0]
        self.src_last = self.knots[-1][1]
        self._f = _pchip([k[0] for k in self.knots], [k[1] for k in self.knots])

    def out_to_src(self, x):
        return self._f(x)

    def src_to_out(self, s):
        """단조 증가 함수의 역 (이분 탐색). 매듭점 원본 프레임은 매듭 out 프레임 그대로."""
        for o, sv in self.knots:
            if abs(sv - s) < 1e-9:
                return float(o)
        lo, hi = 0.0, float(self.out_last)
        if s <= 0:
            return 0.0
        if s >= self.src_last:
            return hi
        for _ in range(60):
            mid = (lo + hi) / 2
            if self._f(mid) < s:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    def frames(self):
        return self.out_last + 1


def load_timemaps():
    if not os.path.exists(TIMEMAP):
        return {}
    return {k: TimeMap(v) for k, v in json.load(open(TIMEMAP, encoding="utf-8")).items()}


def source_path(fname, sub="Clips"):
    p = os.path.join(SOURCE, sub, fname)
    return p if os.path.exists(p) else os.path.join(V10, sub, fname)


def src_frame_to_out(name, frame, maps=None):
    maps = load_timemaps() if maps is None else maps
    return frame if name not in maps else maps[name].src_to_out(frame)


# ------------------------------------------------------------------ 리샘플
def _resample(clip, tm, blend):
    """blend(row_a, row_b, t) -> row  (파트별 보간은 호출 쪽이 제공: Blender mathutils 필요)."""
    rows = clip["frames"]
    out = []
    for j in range(tm.frames()):
        s = tm.out_to_src(j)
        i = min(int(s), len(rows) - 2)
        t = s - i
        if t < 1e-6:
            r = list(rows[i])
        elif t > 1 - 1e-6:
            r = list(rows[i + 1])
        else:
            r = blend(rows[i], rows[i + 1], t)
        r[0] = j / FPS
        out.append(r)
    return out


def build(blend_rows, grip_rest=None):
    """Work/Source/Clips 에 32개 클립(리타이밍된 것 + 그대로 복사) 과 timemap.json 을 쓴다.
    blend_rows: (clip, row_a, row_b, t) -> row.  grip_rest: 오른손 그립 휴지 월드점 (주면 평타에 무게 레이어).
    반환: 보고서."""
    manifest = {c["name"]: c for c in json.load(open(os.path.join(V10, "clip_manifest.json"), encoding="utf-8"))}
    os.makedirs(os.path.join(SOURCE, "Clips"), exist_ok=True)
    maps, report = {}, {}
    for entry in manifest.values():
        name = entry["name"]
        if name.startswith("Transition"):
            continue
        fname = "ViewmodelAnimMaxico%s.lua" % entry["module"].replace("Maxico", "")
        src_p = os.path.join(V10, "Clips", fname)
        dst_p = os.path.join(SOURCE, "Clips", fname)
        knots = knots_for(name, entry)
        if knots is None:
            if grip_rest is not None and name in SHOWCASE_ARC:
                clip = v11_io.read_clip(src_p)
                hit = int(round(dict(clip["fields"])["hitAt"] * FPS))
                clip["frames"], info = apply_arc_dip(clip, clip["frames"], hit, hit + 3, grip_rest, SHOWCASE_ARC[name])
                clip["comments"] = ["-- Maxico%s : v11 버서커 무게 레이어 원본 (v11_retime.py)" % name]
                v11_io.write_clip(dst_p, clip)
                report[name] = {"arc_dip": info}
            else:
                shutil.copyfile(src_p, dst_p)
            continue
        tm = TimeMap(knots)
        clip = v11_io.read_clip(src_p)
        new = dict(clip)
        new["frames"] = _resample(clip, tm, lambda a, b, t: blend_rows(clip, a, b, t))
        heft_peak = None
        if grip_rest is not None and name in HEAVY:
            new["frames"], heft_peak = apply_heft(clip, new["frames"], knots, grip_rest)
            new["frames"], _ = apply_arc_dip(clip, new["frames"], int(knots[2][0]), int(knots[3][0]), grip_rest,
                                             ARC_DROP_CLIP.get(name, ARC_DROP))
        dur = (tm.frames() - 1) / FPS
        fields = []
        for k, v in clip["fields"]:
            if k in ("duration", "full"):
                v = dur if abs(v - clip["fields"][0][1]) < 1e-3 else tm.src_to_out(v * FPS) / FPS
            elif k in ("hitAt", "cut", "jumpAt", "airHoldStart"):
                v = tm.src_to_out(v * FPS) / FPS
            fields.append((k, v))
        new["fields"] = fields
        new["comments"] = ["-- Maxico%s : v11 양손 무게감 리타이밍 원본 (v11_retime.py)" % name]
        v11_io.write_clip(dst_p, new)
        maps[name] = [list(k) for k in knots]
        report[name] = {"frames": [entry["frames"], tm.frames()],
                        "duration": [round(clip["fields"][0][1], 4), round(dur, 4)],
                        "fields": {k: round(v, 4) for k, v in fields if not isinstance(v, bool)}}
    json.dump(maps, open(TIMEMAP, "w", encoding="utf-8"), indent=2)
    return report


def retime_manifest_entry(entry, tm):
    """매니페스트 항목(v10) -> 리타이밍된 복사본."""
    e = json.loads(json.dumps(entry))
    e["frames"] = tm.frames()
    e["duration"] = round((tm.frames() - 1) / FPS, 4)
    for ev in e["events"]:
        k = int(round(tm.src_to_out(ev["frame"] - 1)))     # 1부터 센 frame -> 행 번호 -> 리타이밍
        ev["frame"] = k + 1
        if "time" in ev:
            ev["time"] = round(k / FPS, 4)
    for k in ("hitAt", "cut", "jumpAt", "airHoldStart"):
        if k in e:
            e[k] = round(tm.src_to_out(e[k] * FPS) / FPS, 4)
    e["v11_retime"] = {"knots_out_src": [list(k) for k in tm.knots], "v10_frames": entry["frames"], "v10_duration": entry["duration"]}
    return e


def retime_time(tm, t):
    return round(tm.src_to_out(t * FPS) / FPS, 4)
