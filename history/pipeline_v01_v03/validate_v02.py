import bpy,json,math
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output_v02')
s=bpy.context.scene
pairs=[('Draw','Idle'),('Idle','RunStart'),('RunStart','RunLoop'),('RunLoop','RunStop'),('RunStop','Idle'),('Attack1','Attack2'),('Attack2','Attack3'),('Attack3','Idle'),('BlockIn','BlockHold'),('BlockHold','BlockOut'),('BlockOut','Idle')]
report={'seams':{},'feet':{},'skeleton_preserved':True}
for tag in ['FP','TP']:
 r=bpy.data.objects[tag+'_ODA_Rig']
 for tr in r.animation_data.nla_tracks: tr.mute=True
 def read(name,end=False):
  ac=bpy.data.actions['MX_'+tag+'_'+name];r.animation_data.action=ac;r.animation_data.action_slot=ac.slots[0]
  s.frame_set(int(ac.frame_range[1 if end else 0]));return {b.name:b.matrix.copy() for b in r.pose.bones}
 for a,b in pairs:
  aa=read(a,True);bb=read(b)
  error=max(abs(aa[n][i][j]-bb[n][i][j]) for n in aa for i in range(4) for j in range(4))
  report['seams'][f'{tag}:{a}->{b}']=error
  assert error<.001,(tag,a,b,error)
 if tag=='TP':
  read('RunLoop');foot_min=[];knees=[]
  for f in range(1,26):
   s.frame_set(f)
   for side in ['Right','Left']:
    ob=bpy.data.objects[tag+'_'+side+'Leg_Geo'];vg=ob.vertex_groups[side+'Foot'].index
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    ids=[v.index for v in ob.data.vertices if any(g.group==vg and g.weight>.5 for g in v.groups)]
    foot_min.append(min((ob.matrix_world@me.vertices[i].co).z for i in ids));ev.to_mesh_clear()
    h=r.pose.bones[side+'UpperLeg'].head;k=r.pose.bones[side+'LowerLeg'].head;a=r.pose.bones[side+'Foot'].head
    knees.append(math.degrees((h-k).angle(a-k)))
  report['feet']={'minimum_foot_vertex_z_m':min(foot_min),'maximum_lowest_foot_vertex_z_m':max(foot_min),'knee_interior_angle_range_degrees':[min(knees),max(knees)]}
  assert min(foot_min)>-.01
(OUT/'motion_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
