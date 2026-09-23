import bpy
from mathutils import Matrix
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output_v03')
for ob in bpy.context.scene.objects:
    if ob.type=='MESH' and 'Internal_Chassis' in ob.name:
        for vertex in ob.data.vertices:vertex.co.x*=.18
    if ob.type=='MESH' and 'Core_Vent_' in ob.name:
        for vertex in ob.data.vertices:vertex.co.x*=.15
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Macuahuitl_v03_Expanded.blend'))
# Only prop model geometry changed. Existing animation files remain valid.
for tag in ['FP','TP']:
    pr=bpy.data.objects[tag+'_PropRig'];old=pr.location.copy();pr.location.x=0
    bpy.ops.object.select_all(action='DESELECT');pr.hide_set(False);pr.select_set(True);bpy.context.view_layer.objects.active=pr
    for ob in bpy.context.scene.objects:
        if ob.type=='MESH' and ob.parent==pr:ob.hide_set(False);ob.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(OUT/'FBX'/tag/'Props_Model.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
    pr.location=old
print('CORE_RECESSED')
