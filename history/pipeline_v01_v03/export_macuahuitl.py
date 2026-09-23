import bpy,json,math
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output')
scene=bpy.context.scene
manifest=json.loads((OUT/'animation_manifest.json').read_text())
report={'actions':{},'skeleton_bones':{},'note':'FBX roundtrip is verified separately; OVERDARE runtime validation remains pending.'}
for tag in ['FP','TP']:
    rig=bpy.data.objects[tag+'_ODA_Rig']
    report['skeleton_bones'][tag]=[b.name for b in rig.data.bones]
    tracks=list(rig.animation_data.nla_tracks)
    for tr in tracks: tr.mute=True
    saved_loc=rig.location.copy(); rig.location.x=0
    folder=OUT/'FBX'/tag; folder.mkdir(parents=True,exist_ok=True)
    for clip in manifest['clips']:
        name=clip['name']; action=bpy.data.actions['MX_'+tag+'_'+name]
        rig.animation_data.action=action
        if hasattr(rig.animation_data,'action_slot') and action.slots: rig.animation_data.action_slot=action.slots[0]
        scene.frame_start=1; scene.frame_end=clip['frames']; scene.frame_set(1)
        bpy.ops.object.select_all(action='DESELECT'); rig.hide_set(False); rig.select_set(True); bpy.context.view_layer.objects.active=rig
        bpy.ops.export_scene.fbx(filepath=str(folder/('MX_'+tag+'_'+name+'.fbx')),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_force_startend_keying=True,bake_anim_step=1,bake_anim_simplify_factor=0,axis_forward='-Z',axis_up='Y')
        endpoints=[]
        for f in [1,clip['frames']]:
            scene.frame_set(f); endpoints.append({b.name:b.matrix.copy() for b in rig.pose.bones})
        err=max(max(abs(endpoints[0][n][i][j]-endpoints[1][n][i][j]) for i in range(4) for j in range(4)) for n in endpoints[0])
        report['actions'][action.name]={'frames':clip['frames'],'loop_endpoint_matrix_error':err if clip['loop'] else None,'fbx_bytes':(folder/('MX_'+tag+'_'+name+'.fbx')).stat().st_size}
    # Skinned model exported in idle, with a single static pose sample.
    rig.animation_data.action=bpy.data.actions['MX_'+tag+'_Idle']; scene.frame_set(1)
    bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True)
    for o in list(scene.objects):
        if o.type=='MESH' and o.name.startswith(tag+'_') and (tag=='TP' or 'Arm_Geo' in o.name or 'WPN_' in o.name):
            o.hide_set(False); o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(folder/('MX_'+tag+'_Model.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
    rig.location=saved_loc; rig.animation_data.action=None
    for tr in tracks: tr.mute=False
scene.frame_start=1; scene.frame_end=389
for o in scene.objects:
    if o.name.startswith('FP_') and o.type=='MESH' and '_Geo' in o.name and 'Arm_Geo' not in o.name: o.hide_set(True)
scene.frame_set(49)
scene.camera=bpy.data.objects['CAM_FirstPerson']
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Macuahuitl_FP_TP_AnimationSet.blend'))
(OUT/'validation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for tag,frame in [('FP',49),('TP',49),('FP',197),('TP',197),('FP',338)]:
    scene.camera=bpy.data.objects['CAM_FirstPerson' if tag=='FP' else 'CAM_ThirdPerson']; scene.frame_set(frame)
    scene.render.filepath=str(OUT/f'preview_{tag}_{frame}.png'); bpy.ops.render.render(write_still=True)
print('EXPORTED',len(report['actions']),'clips and 2 skinned models')
