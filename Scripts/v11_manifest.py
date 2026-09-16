"""v11 clip_manifest.json · effect_events.json 생성 (Blender 안에서 import, 다시 돌려도 결과 같음).

항상 v10 파일에서 출발한다:
  1. 리타이밍 (v11_retime timemap): frames · duration · 이벤트 프레임/시각 · hitAt · cut
  2. 부착점 Tip / Vent / Impact: 공통 회전 중심 P 기준 휴지 위치를 레벨 축 (-x, z, y) 로 변환
  3. 왼손 그립 이벤트: left_grip_release / left_grip_join + hand_mesh(hand L, Open/Grip)
  4. 변신 문양 발광 트랙 (v11_glow): Transform · UltAttack 의 glow 키 + glow_hold 규약
  5. role 문자열에 v11 처리 방식 기록 (원래 용도 설명은 보존)
"""
import copy
import json
import os

import bpy
from mathutils import Matrix

import v11_batch
import v11_convention as cv
import v11_retime
import v11_showcase

V11 = v11_batch.V11
V10 = v11_batch.V10
GRIP_EVENT_NAMES = ("left_grip_join", "left_grip_release", "hand_mesh")


def _level(v):
    return [round(-v.x, 6), round(v.z, 6), round(v.y, 6)]


def grip_event_table(by, maps):
    grip = {}
    for name in v11_batch.GRIP_KEYS:
        c = by[name]
        grip[name] = v11_batch.grip_events(v11_batch.grip_keys(name, maps), c["duration"], c["frames"])
    for name, (_, keys_l) in v11_showcase.AUTHOR.items():
        c = by[name]
        evs = v11_batch.grip_events(keys_l, c["duration"], c["frames"])
        if evs:
            grip[name] = evs
    return grip


def roles():
    r = {}
    heavy = " + heavy retime (wind-up x1.5, swing x1.2, 2f hit-stop, recovery x1.4)"
    for n in v11_batch.STANDARD:
        r[n] = "v11: two-hand — v10 weapon path + stance + left-arm IK" + (heavy if n in v11_retime.HEAVY else "")
    for n in v11_batch.GRIP_KEYS:
        r[n] = "v11: two-hand — v10 weapon path + stance + left-hand join/release, slowed x%.2f" % v11_retime.UNIFORM[n]
    r["BlockIn"] = "v11: two-hand diagonal guard (blade screen-right, flat forward), both arms IK, slowed x1.3"
    r["BlockHold"] = "v11: two-hand diagonal guard (blade screen-right, flat forward), both arms IK"
    r["BlockOut"] = r["BlockIn"]
    for n in v11_showcase.RETARGET_ONLY:
        r[n] = "v11: 120-frame showcase, two-hand (stance + left-arm IK)"
    r["Transform"] = "v11: 120-frame showcase, two-hand, reach-corrected weapon + both arms IK; body glyph glow ignites (see effect_events glow)"
    r["UltAttack"] = "v11: 120-frame showcase, two-hand; empowered glyph glow flashes at hit then drains"
    r["FirstDraw"] = "v11: 120-frame showcase, right-hand draw then left-hand join, reach-corrected"
    r["RareDraw"] = "hold attack cosmetic v11.3: heavy two-hand wind-up over the right shoulder, two-hand boomerang throw (v10 flight path), right catch with weight absorb, left re-grip"
    return r


def update():
    maps = v11_retime.load_timemaps()
    cr = bpy.data.objects["V11_WPN_Ctrl"]["v11_rest_matrix"]
    CR = Matrix([cr[0:4], cr[4:8], cr[8:12], cr[12:16]])

    # ---------------- clip_manifest.json
    man10 = json.load(open(os.path.join(V10, "clip_manifest.json"), encoding="utf-8"))
    man = [v11_retime.retime_manifest_entry(c, maps[c["name"]]) if c["name"] in maps else copy.deepcopy(c) for c in man10]
    by = {c["name"]: c for c in man}
    grip = grip_event_table(by, maps)
    role = roles()
    for c10, c in zip(man10, man):
        n = c["name"]
        base = c10.get("role")
        note = "v11: v10 transition path retargeted, endpoints pinned to v11 clip poses" if n.startswith("Transition") else role.get(n)
        if note:
            c["role"] = note if (not base or base.startswith("v10:")) else base + " | " + note
        if n in grip:
            c["events"] = [e for e in c["events"] if e["event"] not in GRIP_EVENT_NAMES] + [dict(e) for e in grip[n]]
            c["events"].sort(key=lambda e: e["frame"])
    import v11_raredraw
    by["RareDraw"]["events"] = v11_raredraw.manifest_events()
    by["RareDraw"]["role"] = role["RareDraw"]
    try:
        import v11_glow
        glow = v11_glow.manifest_events()
    except ImportError:
        glow = {}
    for n, evs in glow.items():
        by[n]["events"] = sorted(by[n]["events"] + evs, key=lambda e: e["frame"])
    json.dump(man, open(os.path.join(V11, "clip_manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # ---------------- effect_events.json
    ev = json.load(open(os.path.join(V10, "effect_events.json"), encoding="utf-8"))
    for n, tm in maps.items():
        for e in ev["clips"].get(n, []):
            if "time" in e:
                e["time"] = v11_retime.retime_time(tm, e["time"])
    for key, obj in (("Tip", "V11_ATT_Tip"), ("Vent", "V11_ATT_Vent"), ("Impact", "V11_ATT_Impact")):
        o = bpy.data.objects[obj]
        ev["attachments"][key]["rest_pivot_offset_m"] = _level((CR @ o.matrix_basis).translation - cv.PIVOT)
        ev["attachments"][key]["v11_note"] = "TwoHand model x=%.3f (scale 0.8); common-pivot-relative, level axes (-x, z, y)" % o["model_x"]
    for n, evs in grip.items():
        lst = ev["clips"].setdefault(n, [])
        lst[:] = [e for e in lst if e.get("event") not in GRIP_EVENT_NAMES] + \
                 [{"time": e["time"], **{k: v for k, v in e.items() if k not in ("frame", "time")}} for e in evs]
        lst.sort(key=lambda e: e["time"])
    ev["clips"]["RareDraw"] = v11_raredraw.effect_events()
    if glow:
        ev["glow"] = v11_glow.effect_spec()
        for n, evs in glow.items():
            lst = ev["clips"].setdefault(n, [])
            lst[:] = [e for e in lst if not e.get("event", "").startswith("glow")] + \
                     [{"time": e["time"], **{k: v for k, v in e.items() if k not in ("frame", "time")}} for e in evs]
            lst.sort(key=lambda e: e["time"])
    json.dump(ev, open(os.path.join(V11, "effect_events.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return {"retimed": {n: [by[n]["frames"], by[n]["duration"], by[n].get("hitAt")] for n in maps},
            "grip_events": {k: [(e["frame"], e["event"]) for e in v] for k, v in grip.items()},
            "glow_clips": list(glow)}
