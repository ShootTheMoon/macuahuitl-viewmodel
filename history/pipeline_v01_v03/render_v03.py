import bpy,json,sys
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output_v03')
s=bpy.context.scene;manifest=json.loads((OUT/'animation_manifest.json').read_text())
s.render.resolution_x=640;s.render.resolution_y=360;s.cycles.samples=4;s.cycles.use_denoising=True
s.render.image_settings.file_format='PNG'
def view(tag):
    for ob in s.objects:
        if ob.type=='MESH' and ob.name.startswith(('FP_','TP_')):
            ob.hide_render=not ob.name.startswith(tag+'_') or (tag=='FP' and '_Geo' in ob.name and 'Arm_Geo' not in ob.name)
    s.objects['Preview_Ground_TP'].hide_render=(tag=='FP')
    s.camera=bpy.data.objects['CAM_FirstPerson' if tag=='FP' else 'CAM_ThirdPerson']
def frame(name,f):
    c=next(c for c in manifest['clips'] if c['name']==name);s.frame_set(c['timeline_start']+f-1)
if '--stills' in sys.argv:
    samples=[('Inspect1_Cylinder',65),('Inspect2_Flip',51),('Inspect3_Can',121),('InspectCards',64),('JumpSlam',28),('SprintTwirl',20),('Inspect4_Display',65)]
    for tag in ['FP','TP']:
        view(tag)
        for name,f in samples:
            frame(name,f);s.render.filepath=str(OUT/f'check_{tag}_{name}.png');bpy.ops.render.render(write_still=True)
else:
    names=['FirstDraw','Inspect1_Cylinder','Inspect2_Flip','Inspect3_Can','Inspect4_Display','InspectCards','SprintTwirl','Attack1','Attack2','JumpSlam','RareDraw']
    schedule=[]
    for name in names:
        c=next(c for c in manifest['clips'] if c['name']==name)
        for f in range(1,c['frames']+1,2):schedule.append({'clip':name,'frame':f})
    (OUT/'preview_schedule.json').write_text(json.dumps(schedule))
    view('FP');folder=OUT/'frames_FP';folder.mkdir(exist_ok=True)
    s.render.resolution_x=640;s.render.resolution_y=360
    for i,item in enumerate(schedule):
        frame(item['clip'],item['frame']);s.render.filepath=str(folder/f'{i:04}.png');bpy.ops.render.render(write_still=True)
print('V03_RENDER_DONE')
