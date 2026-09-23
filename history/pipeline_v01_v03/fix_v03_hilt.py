"""Keep the original wooden tang fixed while the head panels unfold."""
import bpy,bmesh
from pathlib import Path
for ob in list(bpy.context.scene.objects):
    if ob.type!='MESH' or not ob.name.endswith('_Body') or 'Macuahuitl_' not in ob.name:continue
    tail=ob.copy();tail.data=ob.data.copy();tail.name=ob.name+'_FixedTang';bpy.context.scene.collection.objects.link(tail)
    for item,keep_tail in [(ob,False),(tail,True)]:
        bm=bmesh.new();bm.from_mesh(item.data)
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,.08,0),plane_no=(0,1,0),clear_inner=keep_tail,clear_outer=not keep_tail)
        bm.to_mesh(item.data);bm.free()
    tail.vertex_groups.clear();g=tail.vertex_groups.new(name='Weapon');g.add(list(range(len(tail.data.vertices))),1,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=r'C:\Users\29\Desktop\blender2\output_v03\Macuahuitl_v03_Expanded.blend')
print('FIXED_TANGS')
