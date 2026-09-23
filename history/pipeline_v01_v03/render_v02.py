import bpy,json
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output_v02')
s=bpy.context.scene
manifest=json.loads((OUT/'animation_manifest.json').read_text())
schedule=[]
for c in manifest['clips']:
 for rep in range(3 if c['name']=='RunLoop' else 1):
  for f in range(1,c['frames']+1,2):schedule.append({'clip':c['name'],'frame':f})
 for _ in range(3):schedule.append({'clip':c['name'],'frame':c['frames']})
(OUT/'preview_schedule.json').write_text(json.dumps(schedule),encoding='utf-8')
s.render.resolution_x=640;s.render.resolution_y=360;s.cycles.samples=4;s.cycles.use_denoising=True
s.render.image_settings.file_format='PNG'
for tag,cam in [('FP','CAM_FirstPerson'),('TP','CAM_ThirdPerson')]:
 for ob in s.objects:
  if ob.type=='MESH' and ob.name.startswith(('FP_','TP_')):
   ob.hide_render=not ob.name.startswith(tag+'_') or (tag=='FP' and '_Geo' in ob.name and 'Arm_Geo' not in ob.name)
 s.objects['Preview_Ground_TP'].hide_render=(tag=='FP')
 r=bpy.data.objects[tag+'_ODA_Rig']
 for tr in r.animation_data.nla_tracks:tr.mute=True
 s.camera=bpy.data.objects[cam]
 folder=OUT/('frames_'+tag);folder.mkdir(exist_ok=True)
 for i,item in enumerate(schedule):
  a=bpy.data.actions['MX_'+tag+'_'+item['clip']];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
  s.frame_set(item['frame']);s.render.filepath=str(folder/f'{i:04}.png');bpy.ops.render.render(write_still=True)
 r.animation_data.action=None
 for tr in r.animation_data.nla_tracks:tr.mute=False
print('RENDER_V02_DONE',len(schedule))
