import bpy,json,math
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output_v03');s=bpy.context.scene
manifest=json.loads((OUT/'animation_manifest.json').read_text())
report={'character_bones':{},'clips':{},'finite':True,'runtime':'Not tested in OVERDARE'}
for tag in ['FP','TP']:
    r=bpy.data.objects[tag+'_ODA_Rig'];pr=bpy.data.objects[tag+'_PropRig']
    report['character_bones'][tag]=len(r.data.bones)
    folder=OUT/'FBX'/tag;folder.mkdir(parents=True,exist_ok=True)
    # Master timeline is already synchronized across all NLA channels.
    old_r=r.location.copy();old_p=pr.location.copy();r.location.x=0;pr.location.x=0
    samples={}
    for c in manifest['clips']:
        start=c['timeline_start'];end=start+c['frames']-1
        s.frame_start=start;s.frame_end=end
        for label,obj in [('Character',r),('Props',pr)]:
            bpy.ops.object.select_all(action='DESELECT');obj.hide_set(False);obj.select_set(True);bpy.context.view_layer.objects.active=obj
            path=folder/(c['name']+'_'+label+'.fbx')
            bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_force_startend_keying=True,bake_anim_step=1,bake_anim_simplify_factor=0,axis_forward='-Z',axis_up='Y')
            report['clips'][tag+'_'+c['name']+'_'+label]={'bytes':path.stat().st_size,'frames':c['frames']}
        data=[]
        for f in range(start,end+1):
            s.frame_set(f)
            mats={b.name:[round(v,7) for row in b.matrix for v in row] for b in pr.pose.bones}
            if not all(math.isfinite(v) for a in mats.values() for v in a):report['finite']=False
            data.append({'props':mats,'hand_open':{side:round(bpy.data.objects[tag+'_'+side+'Arm_Geo'].data.shape_keys.key_blocks['Open'].value,5) for side in ['Right','Left']}})
        samples[c['name']]=data
        print('EXPORTED',tag,c['name'],flush=True)
    s.frame_set(next(c['timeline_start'] for c in manifest['clips'] if c['name']=='Idle'))
    for label,obj in [('Character',r),('Props',pr)]:
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        for ob in s.objects:
            if ob.type=='MESH' and ob.parent==obj and (tag=='TP' or label=='Props' or 'Arm_Geo' in ob.name):
                ob.hide_set(False);ob.select_set(True)
        bpy.ops.export_scene.fbx(filepath=str(folder/(label+'_Model.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
    (OUT/(tag+'_prop_samples.json')).write_text(json.dumps({'fps':30,'coordinates':'Blender armature-local metres, row-major 4x4 matrices. No game placement offset applied.','clips':samples},separators=(',',':')),encoding='utf-8')
    r.location=old_r;pr.location=old_p
(OUT/'export_report.json').write_text(json.dumps(report,indent=2))
assert report['finite'] and all(v==22 for v in report['character_bones'].values())
print('EXPORT_V03_DONE',len(report['clips']))
