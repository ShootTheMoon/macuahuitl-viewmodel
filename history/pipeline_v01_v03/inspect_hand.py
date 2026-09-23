import bpy,json
from pathlib import Path
r=bpy.data.objects['Armature'];o=bpy.data.objects['RightArm_Geo']
idx=o.vertex_groups['RightHand'].index
ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
verts=[]
for v in o.data.vertices:
 if any(g.group==idx and g.weight>.5 for g in v.groups):
  world=o.matrix_world@mesh.vertices[v.index].co
  verts.append({'i':v.index,'p':list(world),'local':list(r.pose.bones['RightHand'].matrix.inverted()@r.matrix_world.inverted()@world)})
print(json.dumps(verts))
Path(r'C:\Users\29\Desktop\blender2\output_v02\hand_vertices.json').write_text(json.dumps(verts,indent=2))
