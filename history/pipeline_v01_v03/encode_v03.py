import bpy
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output_v03');s=bpy.context.scene
files=sorted((OUT/'frames_preview').glob('*.png'));ed=s.sequence_editor_create()
st=ed.strips.new_image('V03_Preview',str(files[0]),1,1)
for f in files[1:]:st.elements.append(f.name)
st.frame_final_duration=len(files)
ed.strips.new_sound('Synthetic_Cues',str(OUT/'Preview_Cues.wav'),2,1)
s.frame_start=1;s.frame_end=len(files);s.render.fps=15;s.render.resolution_x=640;s.render.resolution_y=408;s.render.resolution_percentage=100
s.render.image_settings.media_type='VIDEO';s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='MEDIUM';s.render.ffmpeg.audio_codec='AAC'
s.render.filepath=str(OUT/'Macuahuitl_v03_Preview.mp4');s.view_settings.view_transform='Standard';bpy.ops.render.render(animation=True)
print('ENCODED',len(files),len(files)/15)
