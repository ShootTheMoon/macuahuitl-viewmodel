"""v11 변신 발광 — 게임(OVERDARE)용 텍스처.

OVERDARE 에서는 MeshPart 색을 런타임에 칠해도 안 나오고, 투명도를 건드리면 하얗게 날아간다.
그래서 발광은 "문양이 빛나는 몸체 텍스처"를 미리 구워 두고, 게임이 몸체 사본을 바꿔 끼운다.

만드는 것:
  Import_OVERDARE/Textures/T_MAC_Body_Glow1_1024.png   문양 채움 0.35 (손잡이 쪽만)
  Import_OVERDARE/Textures/T_MAC_Body_Glow2_1024.png   채움 0.70
  Import_OVERDARE/Textures/T_MAC_Body_Glow3_1024.png   채움 1.00 (칼끝까지)
  Import_OVERDARE/QA/glow_textures_preview.png         원본 + 3단계 세로 비교

게임 쪽 약속:
  레벨 Workspace.Macuahuitl_Viewmodel 에 MAC_Body 사본 MAC_Body_Glow1~3 (MeshId 같음, TextureId 만 다름)
  ViewmodelController 가 MELEE.glowStage() 단계에 맞는 것 하나만 제자리에 두고 나머지는 화면 밖으로 치운다.

채움 방향 = 몸체 정점 속성 v11_blade_t (0 = 손잡이 끝, 1 = 칼끝), v11_glow.py 와 같은 규약.
실행: blender.exe --background Macuahuitl_Rework_v11.blend --factory-startup --python v11_glow_game.py
"""
import os

import bpy
import numpy as np

V11 = r"C:\Users\29\Desktop\Macuahuitl\Macuahuitl_Rework_v11_TwoHand"
OUT = os.path.join(V11, "Import_OVERDARE")
STAGES = (0.35, 0.70, 1.00)
FILL_SOFT = 0.04                              # 채움 경계 부드러움 (몸체 길이 비율)
GLOW_SRGB = np.array([1.0, 0.68, 0.31])       # v11_glow.GLOW_COLOR (1, .42, .08) 선형 -> sRGB
HOT_SRGB = np.array([1.0, 0.93, 0.70])        # 막 차오르는 앞머리
WOOD_DIM = 0.72                               # 채워진 구간 나무결을 살짝 눌러 문양이 도드라지게
HALO_RADIUS = 6                               # 문양 주변 번짐 (원본 2048 기준 px)
HALO_ALPHA = 0.35


def image_array(name):
    img = bpy.data.images[name]
    if img.packed_file is not None and not img.has_data:
        img.reload()
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)                 # 행 0 = UV v 0 (아래)


def blade_map(w, h):
    """텍셀마다 v11_blade_t 값 (UV 삼각형 래스터 + 섬 경계 번짐)."""
    me = bpy.data.objects["V11_MAC_Body"].data
    me.calc_loop_triangles()
    uv = np.empty(len(me.loops) * 2, dtype=np.float32)
    me.uv_layers["UVMap"].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    bt = np.empty(len(me.vertices), dtype=np.float32)
    me.attributes["v11_blade_t"].data.foreach_get("value", bt)
    out = np.full((h, w), -1.0, dtype=np.float32)
    for tri in me.loop_triangles:
        p = uv[list(tri.loops)] * np.array([w, h]) - 0.5
        t = bt[list(tri.vertices)]
        x0, x1 = int(max(0, np.floor(p[:, 0].min()))), int(min(w - 1, np.ceil(p[:, 0].max())))
        y0, y1 = int(max(0, np.floor(p[:, 1].min()))), int(min(h - 1, np.ceil(p[:, 1].max())))
        if x1 < x0 or y1 < y0:
            continue
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-9:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        l1 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
        l2 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        l3 = 1 - l1 - l2
        inside = (l1 >= -0.02) & (l2 >= -0.02) & (l3 >= -0.02)
        sub = out[y0:y1 + 1, x0:x1 + 1]
        sub[inside] = (l1 * t[0] + l2 * t[1] + l3 * t[2])[inside]
    for _ in range(12):
        empty = out < 0
        if not empty.any():
            break
        pad = np.pad(out, 1, mode="edge")
        nb = np.stack([pad[:-2, 1:-1], pad[2:, 1:-1], pad[1:-1, :-2], pad[1:-1, 2:]])
        good = nb >= 0
        n = good.sum(0)
        fill = empty & (n > 0)
        out[fill] = np.where(good, nb, 0).sum(0)[fill] / n[fill]
    out[out < 0] = 0
    return out


def box_blur(m, r):
    k = 2 * r + 1
    c = np.pad(np.cumsum(np.pad(m, ((0, 0), (r, r)), mode="edge"), 1), ((0, 0), (1, 0)))
    m = (c[:, k:] - c[:, :-k]) / k
    c = np.pad(np.cumsum(np.pad(m, ((r, r), (0, 0)), mode="edge"), 0), ((1, 0), (0, 0)))
    return (c[k:] - c[:-k]) / k


def stage_rgb(base, mask, halo, blade, fill):
    lit = np.clip((fill - blade) / FILL_SOFT + 0.5, 0, 1)
    front = np.clip(1 - np.abs(blade - fill) / (FILL_SOFT * 2), 0, 1) * (1.0 if fill < 0.999 else 0.0)
    col = GLOW_SRGB * (1 - front[..., None]) + HOT_SRGB * front[..., None]
    rgb = base[..., :3] * (1 - lit[..., None] * (1 - WOOD_DIM))
    a = (halo * lit * HALO_ALPHA)[..., None]
    rgb = rgb * (1 - a) + col * a
    a = (mask * lit)[..., None]
    rgb = rgb * (1 - a) + col * a
    return np.clip(rgb, 0, 1)


def half(rgb):
    h, w = rgb.shape[:2]
    return rgb[:h // 2 * 2, :w // 2 * 2].reshape(h // 2, 2, w // 2, 2, 3).mean((1, 3))


def save_png(rgb, path):
    h, w = rgb.shape[:2]
    img = bpy.data.images.new("_tmp_glow_png", w, h, alpha=False)
    rgba = np.concatenate([rgb, np.ones((h, w, 1))], 2).astype(np.float32)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def run():
    base = image_array("Hardwood grain and reference geometric paint")
    mask = image_array("T_MAC_Body_GlowMask")[..., 0]
    h, w = base.shape[:2]
    assert mask.shape == (h, w), (mask.shape, base.shape)
    blade = blade_map(w, h)
    halo = np.clip(box_blur(mask, HALO_RADIUS) * 1.6, 0, 1)
    os.makedirs(os.path.join(OUT, "Textures"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "QA"), exist_ok=True)

    report = {"base_check": None, "stages": []}
    ref_path = os.path.join(OUT, "Textures", "T_MAC_Body_BaseColor_1024.png")
    if os.path.exists(ref_path):
        ref = bpy.data.images.load(ref_path, check_existing=False)
        r = np.empty(ref.size[0] * ref.size[1] * 4, dtype=np.float32)
        ref.pixels.foreach_get(r)
        r = r.reshape(ref.size[1], ref.size[0], 4)[..., :3]
        report["base_check"] = float(np.abs(half(base[..., :3]) - r).mean())
        bpy.data.images.remove(ref)

    rows = [half(base[..., :3])]
    for i, fill in enumerate(STAGES, 1):
        rgb = half(stage_rgb(base, mask, halo, blade, fill))
        path = os.path.join(OUT, "Textures", "T_MAC_Body_Glow%d_1024.png" % i)
        save_png(rgb, path)
        rows.append(rgb)
        lit = (blade <= fill)
        report["stages"].append({"file": os.path.basename(path), "fill": fill,
                                 "glyph_lit_frac": round(float((mask > 0.5)[lit].sum() / max(1, (mask > 0.5).sum())), 3)})
    gap = np.ones((6, rows[0].shape[1], 3)) * 0.1
    stack = [rows[0]]
    for r in rows[1:]:
        stack += [gap, r]
    save_png(np.concatenate(stack[::-1], 0), os.path.join(OUT, "QA", "glow_textures_preview.png"))
    report["blade_range"] = [float(blade.min()), float(blade.max())]
    return report


if __name__ == "__main__":
    print("GLOW_REPORT", run())
