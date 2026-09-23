"""Reduce only the exported obsidian parts to keep the combined prop under 30k tris."""
import bpy,json
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output_v03');s=bpy.context.scene
manifest=json.loads((OUT/'animation_manifest.json').read_text());s.frame_set(next(c['timeline_start'] for c in manifest['clips'] if c['name']=='Idle'))
report={}
for tag in ['FP','TP']:
    pr=bpy.data.objects[tag+'_PropRig'];pr.location.x=0
    bpy.ops.object.select_all(action='DESELECT');pr.hide_set(False);pr.select_set(True);bpy.context.view_layer.objects.active=pr
    total=0
    for ob in s.objects:
        if ob.type=='MESH' and ob.parent==pr:
            ob.hide_set(False);ob.select_set(True)
            if 'ObsidianBlades' in ob.name:
                mod=ob.modifiers.new('Export_LOD_90pct','DECIMATE');mod.ratio=.9;mod.use_collapse_triangulate=True
            ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();total+=len(me.loop_triangles);ev.to_mesh_clear()
    assert total<30000,total
    path=OUT/'FBX'/tag/'Props_Model.fbx'
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=True,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
    report[tag]={'exported_prop_triangles':total,'bytes':path.stat().st_size,'method':'Only obsidian parts decimated to 90%; high-resolution Blender source preserved.'}
(OUT/'export_lod_report.json').write_text(json.dumps(report,indent=2));print(report)
