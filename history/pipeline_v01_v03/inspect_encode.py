import bpy
r=bpy.context.scene.render
for prop in r.bl_rna.properties:
 if any(x in prop.identifier for x in ['format','media','video','movie']): print(prop.identifier,prop.type,[(x.identifier,x.name) for x in prop.enum_items] if prop.type=='ENUM' else '')
for prop in r.image_settings.bl_rna.properties:
 if prop.type=='ENUM':print('IMAGE',prop.identifier,[(x.identifier,x.name) for x in prop.enum_items])
