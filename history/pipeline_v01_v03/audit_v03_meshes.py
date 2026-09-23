import bpy,json
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output_v03');report={}
for tag in ['FP','TP']:
    items=[]
    for ob in bpy.context.scene.objects:
        if ob.type=='MESH' and ob.parent and ob.parent.name==tag+'_PropRig':
            ob.data.calc_loop_triangles();items.append({'name':ob.name,'vertices':len(ob.data.vertices),'triangles':len(ob.data.loop_triangles)})
    report[tag]={'parts':items,'triangles_total':sum(x['triangles'] for x in items),'vertices_total':sum(x['vertices'] for x in items)}
(OUT/'mesh_audit.json').write_text(json.dumps(report,indent=2))
print({tag:{k:v for k,v in r.items() if k!='parts'} for tag,r in report.items()})
