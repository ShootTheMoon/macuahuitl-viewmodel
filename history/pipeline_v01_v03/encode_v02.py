import bpy,json
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output_v02')
files=sorted((OUT/'frames_compare').glob('*.png'))
s=bpy.context.scene;s.render.fps=15;s.render.resolution_x=1440;s.render.resolution_y=460;s.render.resolution_percentage=100
ed=s.sequence_editor_create();strip=ed.strips.new_image('FirstPerson_ThirdPerson',str(files[0]),1,1)
for f in files[1:]:strip.elements.append(f.name)
strip.frame_final_duration=len(files)
s.frame_start=1;s.frame_end=len(files)
s.render.image_settings.media_type='VIDEO';s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='MEDIUM'
s.view_settings.view_transform='Standard'
s.render.filepath=str(OUT/'Macuahuitl_v02_Preview.mp4')
bpy.ops.render.render(animation=True)
print('ENCODE_DONE')
