import bpy, importlib.util
print('FORMATS',[i.identifier for i in bpy.context.scene.render.image_settings.bl_rna.properties['file_format'].enum_items])
print('FFMPEG',hasattr(bpy.context.scene.render,'ffmpeg'))
print('SEQ',dir(bpy.context.scene.sequence_editor_create()))
