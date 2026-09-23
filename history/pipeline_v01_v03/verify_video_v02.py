import bpy,json
from pathlib import Path
out=Path(r'C:\Users\29\Desktop\blender2\output_v02')
s=bpy.context.scene;s.render.fps=15;s.render.resolution_x=1440;s.render.resolution_y=460;s.render.resolution_percentage=100
seq=s.sequence_editor_create();clip=seq.strips.new_movie('Verify',str(out/'Macuahuitl_v02_Preview.mp4'),1,1)
assert clip.frame_duration==217,clip.frame_duration
s.view_settings.view_transform='Standard';s.frame_set(126);s.render.filepath=str(out/'Video_Verification.png');bpy.ops.render.render(write_still=True)
(out/'video_validation.json').write_text(json.dumps({'frames':clip.frame_duration,'fps':15,'duration_seconds':clip.frame_duration/15,'decoded_frame':126},indent=2))
