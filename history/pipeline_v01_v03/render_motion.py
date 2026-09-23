import bpy
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output')
s=bpy.context.scene
s.render.resolution_x=640; s.render.resolution_y=360
s.cycles.samples=8; s.cycles.use_denoising=True
s.render.image_settings.file_format='PNG'
s.frame_step=2
for tag,cam in [('FP','CAM_FirstPerson'),('TP','CAM_ThirdPerson')]:
 s.camera=bpy.data.objects[cam]
 folder=OUT/('frames_'+tag); folder.mkdir(exist_ok=True)
 for f in range(1,390,2):
  s.frame_set(f); s.render.filepath=str(folder/f'{(f-1)//2:04}.png'); bpy.ops.render.render(write_still=True)
print('MOTION_RENDER_DONE')
