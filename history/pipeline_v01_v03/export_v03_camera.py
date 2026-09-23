import bpy,json
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output_v03');s=bpy.context.scene
manifest=json.loads((OUT/'animation_manifest.json').read_text());cam=bpy.data.objects['CAM_FirstPerson']
idle=next(c for c in manifest['clips'] if c['name']=='Idle');s.frame_set(idle['timeline_start']);base=cam.matrix_world.copy()
tracks={}
for c in manifest['clips']:
    frames=[]
    for f in range(c['frames']):
        s.frame_set(c['timeline_start']+f);m=base.inverted()@cam.matrix_world
        frames.append([round(v,7) for row in m for v in row])
    tracks[c['name']]=frames
(OUT/'camera_tracks.json').write_text(json.dumps({'fps':30,'convention':'Blender camera-local delta relative to Idle camera; metres; row-major 4x4. Convert axes before applying in engine.','preview_lens_mm':cam.data.lens,'clips':tracks},separators=(',',':')))
print('CAMERA_TRACKS_EXPORTED')
