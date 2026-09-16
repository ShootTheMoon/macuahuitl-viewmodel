"""v11 변신: 몸체 문양(나무 위 검은 기하 문양)이 손잡이 쪽부터 칼끝까지 차오르며 빛난다.

흐름 (게임 규약: 궁 버튼 -> Transform 재생 -> 강화 대기 -> 클릭 -> UltAttack)
  Transform  f0-39  꺼짐 (예비동작)
             f40-45 손잡이 쪽 문양에 불씨 (깜빡임)
             f45-53 문양이 칼끝까지 차오름 — 채움 값 = mesh_contract 변신 단계 비율
                    (0, .08, .22, .5, .78, 1.12, 1) 을 단계 시각 1.502~1.774초에 그대로 사용
             f54    transform_lock 섬광, 이후 강화 상태 맥동
  강화 대기  glow_hold: 세기 0.85 기준 ±0.1, 주기 1.33초 맥동 (게임이 UltAttack 까지 유지)
  UltAttack  맥동 -> 휘두르며 밝아짐 -> hitAt(1.5821초) 섬광 -> 칼끝부터 손잡이 쪽으로 빠지며 꺼짐
  나머지 동작 0

게임 전달물
  Textures/T_MAC_Body_GlowMask.png  문양 마스크 (MAC_Jade_body UV, 흰색 = 문양)
  effect_events.json "glow"         색·최대 세기·트랙 규약,  clips 의 glow_key 이벤트 (time, intensity, fill)
  fill 은 몸체 길이 방향 비율 (0 = 손잡이 끝, 1 = 칼끝, 1.12 = 넘침). 엔진이 fill 을 못 쓰면 intensity 만 써도 된다.
Blender 미리보기
  MAC_Jade_body / MAC_Jade_handle_copper 재질 노드 V11_* 가 V11_WPN_Ctrl["v11_glow"], ["v11_glow_fill"] 드라이버를 읽는다.
"""
import math
import os

import bpy

import v11_retime

V11 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30.0
GLOW_COLOR = (1.0, 0.42, 0.08)          # 달군 금빛 주황 (선형 RGB)
BODY_STRENGTH = 14.0                     # intensity 1 일 때 몸체 문양 방출 세기
COPPER_STRENGTH = 3.0                    # intensity 1 일 때 구리 장식 방출 세기
FILL_SOFT = 0.15                         # 채움 경계 부드러움 (몸체 길이 비율)
MASK_IMAGE = "T_MAC_Body_GlowMask"
BLADE_ATTR = "v11_blade_t"
HOLD_BASE, HOLD_AMP, HOLD_PERIOD = 0.85, 0.10, 40.0

STAGE_FILL = (0.0, 0.08, 0.22, 0.5, 0.78, 1.12, 1.0)
STAGE_T0, STAGE_T1 = 1.502, 1.774


# ------------------------------------------------------------------ 곡선
def _smooth(a, b, t):
    t = max(0.0, min(1.0, t))
    t = t * t * (3 - 2 * t)
    return a + (b - a) * t


def _lerp_keys(keys, x):
    if x <= keys[0][0]:
        return keys[0][1]
    for (x0, y0), (x1, y1) in zip(keys, keys[1:]):
        if x <= x1:
            return _smooth(y0, y1, (x - x0) / (x1 - x0))
    return keys[-1][1]


def hold_pulse(k):
    return HOLD_BASE + HOLD_AMP * math.sin(2 * math.pi * k / HOLD_PERIOD)


def transform_curve(k):
    """Transform 클립 프레임 k -> (intensity, fill)."""
    stage_frames = [(STAGE_T0 + (STAGE_T1 - STAGE_T0) * i / 6) * FPS for i in range(7)]
    fill = 0.0
    if k >= 40:
        fill = _lerp_keys([(40, 0.0), (44, 0.12), (stage_frames[0], 0.12)] +
                          [(f, max(v, 0.12)) for f, v in zip(stage_frames[1:], STAGE_FILL[1:])], k)
    flick = 0.0
    if 40 <= k < 46:
        flick = 0.12 * math.sin(k * 2.7) * math.sin(k * 1.3)
    # transform_lock = 매니페스트 frame 54 = 행 53 에서 섬광
    inten = _lerp_keys([(0, 0.0), (39, 0.0), (41, 0.25), (45, 0.4), (49, 0.85), (52, 1.0),
                        (53, 1.9), (56, 1.25), (63, 0.95), (72, HOLD_BASE)], k) + flick
    if k > 72:
        inten = hold_pulse(k - 72)
    return max(0.0, inten), fill


def ultattack_curve(k, hit_frame):
    """UltAttack 프레임 k -> (intensity, fill). 시작은 강화 대기와 같은 값."""
    if k <= hit_frame - 10:
        inten = _lerp_keys([(0, HOLD_BASE), (hit_frame - 10, 1.1)], k) + HOLD_AMP * 0.5 * math.sin(2 * math.pi * k / 20)
    elif k <= hit_frame:
        inten = _lerp_keys([(hit_frame - 10, 1.1), (hit_frame - 2, 1.6), (hit_frame, 2.8)], k)
    else:
        inten = _lerp_keys([(hit_frame, 2.8), (hit_frame + 4, 1.6), (hit_frame + 18, 0.9), (hit_frame + 45, 0.0)], k)
    fill = 1.0 if k <= hit_frame + 12 else _lerp_keys([(hit_frame + 12, 1.0), (hit_frame + 45, -0.15)], k)
    return max(0.0, inten), fill


def clip_curves():
    """{클립 이름: [(intensity, fill) 프레임별]}"""
    tr = [transform_curve(k) for k in range(120)]
    hit = 1.5821 * FPS
    ul = [ultattack_curve(k, hit) for k in range(120)]
    return {"Transform": tr, "UltAttack": ul}


def manifest_events(step=2):
    """clip_manifest 용 glow_key 이벤트 (프레임, 시각). 끝 프레임은 항상 포함."""
    out = {}
    for name, curve in clip_curves().items():
        n = len(curve)
        idx = sorted(set(list(range(0, n, step)) + [n - 1, 53 if name == "Transform" else int(round(1.5821 * FPS))]))
        evs = [{"frame": k + 1, "event": "glow_key", "intensity": round(curve[k][0], 3), "fill": round(curve[k][1], 3),
                "time": round(k / FPS, 4)} for k in idx]
        if name == "Transform":
            evs.append({"frame": n, "event": "glow_hold", "base": HOLD_BASE, "amplitude": HOLD_AMP,
                        "period_seconds": round(HOLD_PERIOD / FPS, 4), "fill": 1.0, "time": round((n - 1) / FPS, 4),
                        "until": "UltAttack start"})
        out[name] = evs
    return out


def effect_spec():
    return {
        "mask_texture": "Textures/%s.png" % MASK_IMAGE,
        "material": "MAC_Jade_body (emissive = color * intensity * max_strength * mask * fill_mask)",
        "secondary_material": "MAC_Jade_handle_copper (emissive = color * intensity * %.1f, no mask)" % COPPER_STRENGTH,
        "color_linear_rgb": list(GLOW_COLOR),
        "max_strength": BODY_STRENGTH,
        "fill_axis": "0 = handle end of MAC_Body, 1 = blade tip (fraction of body length); fill_mask = clamp((fill*1.2 - axis)/%.2f)" % FILL_SOFT,
        "stage_fill_source": "mesh_contract stages fractions %s at %.3f-%.3fs" % (list(STAGE_FILL), STAGE_T0, STAGE_T1),
        "hold": {"base": HOLD_BASE, "amplitude": HOLD_AMP, "period_seconds": round(HOLD_PERIOD / FPS, 4)},
        "tracks": "clips.Transform / clips.UltAttack glow_key events (linear interpolate); others 0",
    }


# ------------------------------------------------------------------ Blender 재질
def _node(nt, name, kind, loc):
    n = nt.nodes.get(name)
    if n is None:
        n = nt.nodes.new(kind)
        n.name = name
        n.label = name
    n.location = loc
    return n


def _drive(socket_owner_node, obj, prop):
    out = socket_owner_node.outputs[0]
    try:
        out.driver_remove("default_value")
    except Exception:
        pass
    fc = out.driver_add("default_value")
    d = fc.driver
    d.type = 'AVERAGE'
    for v in list(d.variables):
        d.variables.remove(v)
    var = d.variables.new()
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'OBJECT'
    var.targets[0].id = obj
    var.targets[0].data_path = '["%s"]' % prop


def _math(nt, name, op, loc, clamp=False):
    n = _node(nt, name, 'ShaderNodeMath', loc)
    n.operation = op
    n.use_clamp = clamp
    return n


def bake_blade_attribute():
    """V11_MAC_Body 정점에 칼 길이 방향 비율 속성 (0 손잡이 끝 -> 1 칼끝)."""
    from mathutils import Vector
    ob = bpy.data.objects["V11_MAC_Body"]
    ctrl = bpy.data.objects["V11_WPN_Ctrl"]
    cr = ctrl["v11_rest_matrix"]
    from mathutils import Matrix
    CR = Matrix([cr[0:4], cr[4:8], cr[8:12], cr[12:16]])
    rest = CR @ ob.matrix_parent_inverse @ ob.matrix_basis
    tip = (rest.to_quaternion() @ Vector((0, 0, 0))) if False else None
    model_x = (bpy.data.objects["V11_WPN_Root"].matrix_world.to_quaternion() @ Vector((1, 0, 0))).normalized()
    tip_dir = -model_x                                   # 모델 -X = 칼끝 방향
    me = ob.data
    R = rest.to_3x3()
    proj = [(R @ v.co).dot(tip_dir) for v in me.vertices]
    lo, hi = min(proj), max(proj)
    attr = me.attributes.get(BLADE_ATTR) or me.attributes.new(BLADE_ATTR, 'FLOAT', 'POINT')
    attr.data.foreach_set("value", [(p - lo) / (hi - lo) for p in proj])
    me.update()
    return {"length_m": round(hi - lo, 4)}


def setup_materials():
    ctrl = bpy.data.objects["V11_WPN_Ctrl"]
    for prop in ("v11_glow", "v11_glow_fill"):
        if prop not in ctrl:
            ctrl[prop] = 0.0
    info = bake_blade_attribute()

    m = bpy.data.materials["MAC_Jade_body"]
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    # 원본 glb 가 색 텍스처를 노멀맵에 넣어 둬서 나무가 금속처럼 번들거림 -> 연결만 끊음 (노드는 남김)
    for l in list(nt.links):
        if l.to_node.type == 'NORMAL_MAP' or l.from_node.type == 'NORMAL_MAP':
            nt.links.remove(l)
    x0, y0 = bsdf.location.x - 900, bsdf.location.y - 500
    mask = _node(nt, "V11_GlowMask", 'ShaderNodeTexImage', (x0, y0))
    mask.image = bpy.data.images[MASK_IMAGE]
    attr = _node(nt, "V11_BladeT", 'ShaderNodeAttribute', (x0, y0 - 300))
    attr.attribute_type = 'GEOMETRY'
    attr.attribute_name = BLADE_ATTR
    glow = _node(nt, "V11_Glow", 'ShaderNodeValue', (x0, y0 - 450))
    fill = _node(nt, "V11_Fill", 'ShaderNodeValue', (x0, y0 - 550))
    _drive(glow, ctrl, "v11_glow")
    _drive(fill, ctrl, "v11_glow_fill")
    f_scale = _math(nt, "V11_FillScale", 'MULTIPLY', (x0 + 200, y0 - 550)); f_scale.inputs[1].default_value = 1.2
    f_sub = _math(nt, "V11_FillSub", 'SUBTRACT', (x0 + 380, y0 - 450))
    f_div = _math(nt, "V11_FillDiv", 'DIVIDE', (x0 + 560, y0 - 450), clamp=True); f_div.inputs[1].default_value = FILL_SOFT
    m1 = _math(nt, "V11_MaskFill", 'MULTIPLY', (x0 + 560, y0 - 150))
    m2 = _math(nt, "V11_MaskGlow", 'MULTIPLY', (x0 + 740, y0 - 250))
    st = _math(nt, "V11_Strength", 'MULTIPLY', (x0 + 900, y0 - 250)); st.inputs[1].default_value = BODY_STRENGTH
    col = _node(nt, "V11_GlowColor", 'ShaderNodeRGB', (x0 + 740, y0 - 450))
    col.outputs[0].default_value = (*GLOW_COLOR, 1.0)
    L = nt.links.new
    L(fill.outputs[0], f_scale.inputs[0])
    L(f_scale.outputs[0], f_sub.inputs[0])
    L(attr.outputs["Fac"], f_sub.inputs[1])
    L(f_sub.outputs[0], f_div.inputs[0])
    L(mask.outputs["Color"], m1.inputs[0])
    L(f_div.outputs[0], m1.inputs[1])
    L(m1.outputs[0], m2.inputs[0])
    L(glow.outputs[0], m2.inputs[1])
    L(m2.outputs[0], st.inputs[0])
    L(st.outputs[0], bsdf.inputs["Emission Strength"])
    L(col.outputs[0], bsdf.inputs["Emission Color"])

    c = bpy.data.materials["MAC_Jade_handle_copper"]
    nt = c.node_tree
    cb = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    cg = _node(nt, "V11_Glow", 'ShaderNodeValue', (cb.location.x - 500, cb.location.y - 400))
    _drive(cg, ctrl, "v11_glow")
    cs = _math(nt, "V11_Strength", 'MULTIPLY', (cb.location.x - 300, cb.location.y - 400)); cs.inputs[1].default_value = COPPER_STRENGTH
    cc = _node(nt, "V11_GlowColor", 'ShaderNodeRGB', (cb.location.x - 300, cb.location.y - 600))
    cc.outputs[0].default_value = (*GLOW_COLOR, 1.0)
    nt.links.new(cg.outputs[0], cs.inputs[0])
    nt.links.new(cs.outputs[0], cb.inputs["Emission Strength"])
    nt.links.new(cc.outputs[0], cb.inputs["Emission Color"])
    return info


# ------------------------------------------------------------------ 미리보기 키
def key_preview(ranges, modules=None):
    """v11_preview.build 가 만든 V11_WPN_Ctrl 동작에 glow 곡선을 추가한다.
    ranges: {마커 이름: (시작, 끝)}. 강화 대기 구간(Transform 끝 ~ UltAttack 시작)이 붙어 있으면 맥동으로 채운다."""
    ctrl = bpy.data.objects["V11_WPN_Ctrl"]
    action = ctrl.animation_data.action
    curves = clip_curves()
    samples = {}
    for name, curve in curves.items():
        if name not in ranges:
            continue
        s, e = ranges[name]
        for k, v in enumerate(curve):
            samples[s + k] = v
    if "Transform" in ranges and "UltAttack" in ranges:
        t_end = ranges["Transform"][1]
        u_start = ranges["UltAttack"][0]
        for i, f in enumerate(range(t_end + 1, u_start)):
            samples[f] = (hold_pulse(120 - 72 + i), 1.0)
    frames = sorted(samples)
    all_first, all_last = bpy.context.scene.frame_start, bpy.context.scene.frame_end
    keys = {}
    prev = None
    for f in range(all_first, all_last + 1):
        v = samples.get(f, (0.0, 0.0))
        keys[f] = v
    for idx, prop in ((0, "v11_glow"), (1, "v11_glow_fill")):
        path = '["%s"]' % prop
        if hasattr(action, "fcurve_ensure_for_datablock"):
            fc = action.fcurve_ensure_for_datablock(ctrl, path)
            fc.keyframe_points.clear()
        else:
            fc = action.fcurves.find(path) or action.fcurves.new(path)
            fc.keyframe_points.clear()
        # 값이 변하는 곳만 키 (연속 0 구간은 경계만)
        pts = []
        fl = sorted(keys)
        for i, f in enumerate(fl):
            val = keys[f][idx]
            p = keys[fl[i - 1]][idx] if i > 0 else None
            nx = keys[fl[i + 1]][idx] if i + 1 < len(fl) else None
            if p is None or nx is None or not (abs(val - p) < 1e-6 and abs(val - nx) < 1e-6):
                pts.append((f, val))
        fc.keyframe_points.add(len(pts))
        co = []
        for f, val in pts:
            co += [float(f), float(val)]
        fc.keyframe_points.foreach_set("co", co)
        fc.keyframe_points.foreach_set("interpolation", [1] * len(pts))
        fc.update()
    return {"glow_frames": len(frames)}
