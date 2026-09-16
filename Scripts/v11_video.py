"""v11 비교 영상: Motions_v10_vs_v11.mp4 (Blender 안에서 import, ffmpeg 외부 설치 불필요).

1. capture   : MAC_V10_AllClips / MAC_V11_AllClips 를 게임 카메라 뷰포트(Solid, 재질 색)로 PNG 시퀀스 캡처
               두 씬은 마커·프레임 번호가 같다 (1451 프레임, 30 fps)
2. compose   : V11_Video 씬(VSE) 에 v10 왼쪽 / v11 오른쪽 나란히 + 동작 이름 자막 -> H.264 MP4
둘 다 오래 걸리므로 bpy.app.timers 로 비동기 시작하고, 끝나면 QA/Video/_*.done 파일을 쓴다.
오류는 QA/Video/_log.txt 에 남긴다.
"""
import os
import time
import traceback

import bpy

V11 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_DIR = os.path.join(V11, "QA", "Video")
OUT_MP4 = os.path.join(V11, "Motions_v10_vs_v11.mp4")
SCENES = (("v10", "MAC_V10_AllClips"), ("v11", "MAC_V11_AllClips"))
PCT = 67  # 768x512 -> 514x343


def _log(msg):
    os.makedirs(VIDEO_DIR, exist_ok=True)
    with open(os.path.join(VIDEO_DIR, "_log.txt"), "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def _view3d(win):
    for area in win.screen.areas:
        if area.type == 'VIEW_3D':
            region = next(r for r in area.regions if r.type == 'WINDOW')
            return area, region
    raise RuntimeError("VIEW_3D 영역이 없습니다")


def capture(tag, scene_name):
    win = bpy.context.window_manager.windows[0]
    prev_scene = win.scene
    sc = bpy.data.scenes[scene_name]
    area, region = _view3d(win)
    sp = area.spaces.active
    saved = (sp.shading.type, sp.shading.color_type, sp.region_3d.view_perspective, sp.overlay.show_overlays,
             sc.render.filepath, sc.render.resolution_percentage, sc.render.image_settings.file_format)
    out_dir = os.path.join(VIDEO_DIR, tag)
    os.makedirs(out_dir, exist_ok=True)
    try:
        win.scene = sc
        sp.shading.type = 'SOLID'
        sp.shading.color_type = 'MATERIAL'
        sp.overlay.show_overlays = False
        sp.region_3d.view_perspective = 'CAMERA'
        sc.render.image_settings.file_format = 'PNG'
        sc.render.resolution_percentage = PCT
        sc.render.filepath = os.path.join(out_dir, "f_")
        with bpy.context.temp_override(window=win, area=area, region=region, scene=sc):
            bpy.ops.render.opengl(animation=True, view_context=True)
    finally:
        sp.shading.type, sp.shading.color_type, sp.region_3d.view_perspective, sp.overlay.show_overlays = saved[:4]
        sc.render.filepath, sc.render.resolution_percentage, sc.render.image_settings.file_format = saved[4:]
        win.scene = prev_scene
    return out_dir


def start_capture_async():
    def job():
        try:
            for tag, name in SCENES:
                t0 = time.time()
                capture(tag, name)
                _log("capture %s done in %.1fs" % (tag, time.time() - t0))
            open(os.path.join(VIDEO_DIR, "_capture.done"), "w").write("ok")
        except Exception:
            _log("capture FAILED\n" + traceback.format_exc())
            open(os.path.join(VIDEO_DIR, "_capture.failed"), "w").write(traceback.format_exc())
        return None
    for fn in ("_capture.done", "_capture.failed"):
        p = os.path.join(VIDEO_DIR, fn)
        if os.path.exists(p):
            os.remove(p)
    bpy.app.timers.register(job, first_interval=0.5)


def _strips(se):
    return se.strips if hasattr(se, "strips") else se.sequences


def _text(st, name, channel, start, end):
    """Blender 5.x: new_effect(..., frame_start, length) / 이전 판: frame_end."""
    try:
        return st.new_effect(name, 'TEXT', channel, frame_start=start, length=end - start)
    except TypeError:
        return st.new_effect(name, 'TEXT', channel, frame_start=start, frame_end=end)


def _style(t, text, size, location, anchor):
    t.text = text
    for attr, value in (("font_size", size), ("location", location), ("anchor_x", anchor), ("use_shadow", True)):
        if hasattr(t, attr):
            setattr(t, attr, value)


def compose(scene_name="V11_Video"):
    v11 = bpy.data.scenes["MAC_V11_AllClips"]
    sc = bpy.data.scenes.get(scene_name)
    if sc is not None:
        bpy.data.scenes.remove(sc)
    sc = bpy.data.scenes.new(scene_name)
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1060, 420, 100
    sc.render.fps = 30
    sc.frame_start, sc.frame_end = v11.frame_start, v11.frame_end
    se = sc.sequence_editor_create()
    st = _strips(se)
    for ch, (tag, _) in enumerate(SCENES, start=1):
        folder = os.path.join(VIDEO_DIR, tag)
        files = sorted(f for f in os.listdir(folder) if f.endswith(".png"))
        strip = st.new_image(tag, os.path.join(folder, files[0]), ch, 1, fit_method='ORIGINAL')
        for f in files[1:]:
            strip.elements.append(f)
        strip.transform.offset_x = -265 if tag == "v10" else 265
        strip.transform.offset_y = 20
    for ch, (tag, x) in enumerate((("v10 (one hand)", 0.03), ("v11 (two hand)", 0.53)), start=3):
        t = _text(st, tag, ch, sc.frame_start, sc.frame_end + 1)
        _style(t, tag, 22, (x, 0.93), 'LEFT')
    marks = sorted((m.frame, m.name) for m in v11.timeline_markers)
    for i, (f, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else sc.frame_end + 1
        t = _text(st, "cap_" + name, 5, f, end)
        _style(t, "%s  (%d f)" % (name, end - f), 26, (0.5, 0.04), 'CENTER')
    r = sc.render
    if hasattr(r.image_settings, "media_type"):   # Blender 5.x: 영상 출력은 media_type 을 먼저 VIDEO 로
        r.image_settings.media_type = 'VIDEO'
    r.image_settings.file_format = 'FFMPEG'
    r.ffmpeg.format = 'MPEG4'
    r.ffmpeg.codec = 'H264'
    r.ffmpeg.constant_rate_factor = 'MEDIUM'
    r.filepath = OUT_MP4
    return sc


BEAUTY_DIR = os.path.join(VIDEO_DIR, "beauty")
BEAUTY_MP4 = os.path.join(V11, "Motions_v11_heavy_glow.mp4")


def render_beauty(scene_name="MAC_V11_AllClips"):
    """전체 EEVEE 렌더(재질·조명·블룸 컴포지터) 를 PNG 시퀀스로."""
    sc = bpy.data.scenes[scene_name]
    win = bpy.context.window_manager.windows[0]
    prev = win.scene
    r = sc.render
    saved = (r.filepath, r.resolution_percentage, r.image_settings.file_format,
             getattr(r.image_settings, "media_type", None))
    os.makedirs(BEAUTY_DIR, exist_ok=True)
    try:
        win.scene = sc
        if hasattr(r.image_settings, "media_type"):
            r.image_settings.media_type = 'IMAGE'
        r.image_settings.file_format = 'PNG'
        r.resolution_percentage = 100
        r.filepath = os.path.join(BEAUTY_DIR, "f_")
        bpy.ops.render.render(animation=True, scene=sc.name)
    finally:
        r.filepath, r.resolution_percentage = saved[0], saved[1]
        r.image_settings.file_format = saved[2]
        win.scene = prev


def compose_single(folder=BEAUTY_DIR, out_mp4=BEAUTY_MP4, scene_name="V11_BeautyVideo",
                   marker_scene="MAC_V11_AllClips", title="v11 two-hand  |  heavy retime  |  glyph glow on Transform"):
    src = bpy.data.scenes[marker_scene]
    sc = bpy.data.scenes.get(scene_name)
    if sc is not None:
        bpy.data.scenes.remove(sc)
    sc = bpy.data.scenes.new(scene_name)
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = src.render.resolution_x, src.render.resolution_y + 60, 100
    sc.render.fps = 30
    sc.frame_start, sc.frame_end = src.frame_start, src.frame_end
    st = _strips(sc.sequence_editor_create())
    files = sorted(f for f in os.listdir(folder) if f.endswith(".png"))
    strip = st.new_image("beauty", os.path.join(folder, files[0]), 1, 1, fit_method='ORIGINAL')
    for f in files[1:]:
        strip.elements.append(f)
    strip.transform.offset_y = 30
    t = _text(st, "title", 2, sc.frame_start, sc.frame_end + 1)
    _style(t, title, 18, (0.02, 0.965), 'LEFT')
    marks = sorted((m.frame, m.name) for m in src.timeline_markers)
    for i, (f, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else sc.frame_end + 1
        t = _text(st, "cap_" + name, 3, f, end)
        _style(t, "%s   %d f  (%.2fs)" % (name, end - f, (end - f) / 30.0), 24, (0.5, 0.03), 'CENTER')
    r = sc.render
    if hasattr(r.image_settings, "media_type"):
        r.image_settings.media_type = 'VIDEO'
    r.image_settings.file_format = 'FFMPEG'
    r.ffmpeg.format = 'MPEG4'
    r.ffmpeg.codec = 'H264'
    r.ffmpeg.constant_rate_factor = 'HIGH'
    r.filepath = out_mp4
    return sc


def beauty_async(first_interval=3.0):
    def job():
        try:
            t0 = time.time()
            render_beauty()
            _log("beauty render done in %.1fs" % (time.time() - t0))
            t1 = time.time()
            sc = compose_single()
            bpy.ops.render.render(animation=True, scene=sc.name)
            _log("beauty compose done in %.1fs -> %s" % (time.time() - t1, BEAUTY_MP4))
            open(os.path.join(VIDEO_DIR, "_beauty.done"), "w").write(BEAUTY_MP4)
        except Exception:
            _log("beauty FAILED\n" + traceback.format_exc())
            open(os.path.join(VIDEO_DIR, "_beauty.failed"), "w").write(traceback.format_exc())
        return None
    for fn in ("_beauty.done", "_beauty.failed"):
        p = os.path.join(VIDEO_DIR, fn)
        if os.path.exists(p):
            os.remove(p)
    bpy.app.timers.register(job, first_interval=first_interval)


def compose_async():
    def job():
        try:
            t0 = time.time()
            sc = compose()
            bpy.ops.render.render(animation=True, scene=sc.name)
            _log("compose done in %.1fs -> %s" % (time.time() - t0, OUT_MP4))
            open(os.path.join(VIDEO_DIR, "_compose.done"), "w").write(OUT_MP4)
        except Exception:
            _log("compose FAILED\n" + traceback.format_exc())
            open(os.path.join(VIDEO_DIR, "_compose.failed"), "w").write(traceback.format_exc())
        return None
    for fn in ("_compose.done", "_compose.failed"):
        p = os.path.join(VIDEO_DIR, fn)
        if os.path.exists(p):
            os.remove(p)
    bpy.app.timers.register(job, first_interval=0.5)
