import bpy,json
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output')
report={}
for tag in ['FP','TP']:
 for name in ['Idle','Attack1','RunLoop','BlockHold']:
  for obj in list(bpy.data.objects): bpy.data.objects.remove(obj,do_unlink=True)
  path=OUT/'FBX'/tag/f'MX_{tag}_{name}.fbx'
  bpy.ops.import_scene.fbx(filepath=str(path))
  rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
  assert len(rigs)==1
  r=rigs[0]; a=r.animation_data.action
  assert len(r.data.bones)==22 and a is not None
  endpoints=[]
  for f in a.frame_range:
   bpy.context.scene.frame_set(int(f)); endpoints.append({b.name:b.matrix.copy() for b in r.pose.bones})
  e=max(abs(endpoints[0][n][i][j]-endpoints[1][n][i][j]) for n in endpoints[0] for i in range(4) for j in range(4))
  if name!='Attack1': assert e<.001,(tag,name,e)
  report[f'{tag}_{name}']={'bones':22,'frame_range':list(a.frame_range),'loop_error':e if name!='Attack1' else None}
(OUT/'fbx_roundtrip_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
models={}
for tag,expected in [('FP',5),('TP',9)]:
 for obj in list(bpy.data.objects): bpy.data.objects.remove(obj,do_unlink=True)
 bpy.ops.import_scene.fbx(filepath=str(OUT/'FBX'/tag/f'MX_{tag}_Model.fbx'))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
 rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
 assert len(meshes)==expected and len(rigs)==1
 assert all(any(m.type=='ARMATURE' and m.object==rigs[0] for m in o.modifiers) for o in meshes)
 models[tag]={'meshes':len(meshes),'bones':len(rigs[0].data.bones),'all_meshes_skinned':True}
(OUT/'model_roundtrip_report.json').write_text(json.dumps(models,indent=2),encoding='utf-8')
print('ROUNDTRIP_PASS',len(report))
