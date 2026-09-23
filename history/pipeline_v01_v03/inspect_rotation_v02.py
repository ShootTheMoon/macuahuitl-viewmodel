import bpy,json,math
from pathlib import Path
out=Path(r'C:\Users\29\Desktop\blender2\output_v02')
s=bpy.context.scene;report={}
for tag in ['FP','TP']:
 r=bpy.data.objects[tag+'_ODA_Rig']
 for tr in r.animation_data.nla_tracks:tr.mute=True
 for name in ['Draw','Attack1','Attack2','Attack3','RunLoop','BlockIn','BlockOut']:
  ac=bpy.data.actions['MX_'+tag+'_'+name];r.animation_data.action=ac;r.animation_data.action_slot=ac.slots[0]
  prev=None;peak=0
  for f in range(1,int(ac.frame_range[1])+1):
   s.frame_set(f);q=r.pose.bones['RightHand'].matrix.to_quaternion()
   if prev is not None:
    dot=max(-1,min(1,abs(q.dot(prev))));peak=max(peak,math.degrees(2*math.acos(dot)))
   prev=q
  report[tag+'_'+name]={'maximum_right_hand_rotation_per_frame_deg':peak}
  assert peak<90,(tag,name,peak)
(out/'rotation_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
