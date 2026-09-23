import bpy,json,math
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output_v03')
manifest=json.loads((OUT/'animation_manifest.json').read_text());expected={c['name']:c for c in manifest['clips']}
results=[]
for path in sorted((OUT/'FBX').glob('*/*.fbx')):
    for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
    for ac in list(bpy.data.actions):bpy.data.actions.remove(ac)
    bpy.ops.import_scene.fbx(filepath=str(path),use_anim=True)
    rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    assert len(rigs)==1,(path,len(rigs))
    r=rigs[0];want=22 if 'Character' in path.stem else 6
    assert len(r.data.bones)==want,(path,len(r.data.bones))
    item={'file':str(path.relative_to(OUT)),'bones':want}
    if not path.stem.endswith('_Model'):
        name=path.stem.rsplit('_',1)[0];ac=r.animation_data.action;span=ac.frame_range
        assert abs((span[1]-span[0])-(expected[name]['frames']-1))<.02,(path,list(span),expected[name]['frames'])
        for f in [span[0],(span[0]+span[1])/2,span[1]]:
            bpy.context.scene.frame_set(int(f))
            assert all(math.isfinite(v) for b in r.pose.bones for row in b.matrix for v in row),path
        item['frames']=expected[name]['frames']
    else:
        item['meshes']=sum(o.type=='MESH' for o in bpy.context.scene.objects)
        assert item['meshes']>0,path
        tris=0
        for ob in bpy.context.scene.objects:
            if ob.type=='MESH':ob.data.calc_loop_triangles();tris+=len(ob.data.loop_triangles)
        item['triangles']=tris
        if path.stem=='Props_Model':assert tris<30000,(path,tris)
    results.append(item)
    print('PASS',path.name,flush=True)
(OUT/'roundtrip_report.json').write_text(json.dumps({'passed':len(results),'files':results,'limitation':'FBX structure/duration/finite values verified; does not substitute for visual or OVERDARE runtime testing.'},indent=2))
print('ROUNDTRIP_V03_DONE',len(results))
