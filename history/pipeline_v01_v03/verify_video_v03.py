import bpy,json
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output_v03');s=bpy.context.scene
schedule=json.loads((OUT/'preview_schedule.json').read_text());s.render.fps=15;s.render.resolution_x=640;s.render.resolution_y=408;s.render.resolution_percentage=100
seq=s.sequence_editor_create();clip=seq.strips.new_movie('Verify',str(OUT/'Macuahuitl_v03_Preview.mp4'),1,1)
assert clip.frame_duration==len(schedule),(clip.frame_duration,len(schedule))
s.view_settings.view_transform='Standard'
for frame in [10,len(schedule)//2,len(schedule)-5]:
    s.frame_set(frame);s.render.filepath=str(OUT/f'video_check_{frame}.png');bpy.ops.render.render(write_still=True)
(OUT/'video_validation.json').write_text(json.dumps({'frames':clip.frame_duration,'fps':15,'duration_seconds':clip.frame_duration/15,'decoded_frames':[10,len(schedule)//2,len(schedule)-5]},indent=2))
print('VIDEO_V03_VERIFIED')
