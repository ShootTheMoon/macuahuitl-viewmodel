from pathlib import Path
from PIL import Image,ImageDraw
import json
out=Path(r'C:\Users\29\Desktop\blender2\output')
manifest=json.loads((out/'animation_manifest.json').read_text())
ranges=[];start=1
for c in manifest['clips']:
 ranges.append((start,start+c['frames']+7,c['name']));start+=c['frames']+8
frames=[]
for i in range(195):
 canvas=Image.new('RGB',(960,300),'#111a22')
 for x,tag in [(0,'FP'),(480,'TP')]:
  im=Image.open(out/f'frames_{tag}'/f'{i:04}.png').convert('RGB').resize((480,270))
  canvas.paste(im,(x,30))
 f=i*2+1; clip=next((n for a,b,n in ranges if a<=f<=b),'')
 draw=ImageDraw.Draw(canvas);draw.text((12,9),'FIRST PERSON  |  '+clip,fill='white');draw.text((492,9),'THIRD PERSON  |  '+clip,fill='white')
 frames.append(canvas)
frames[0].save(out/'Macuahuitl_FP_TP_Preview.gif',save_all=True,append_images=frames[1:],duration=[60 if i%3==0 else 70 for i in range(len(frames))],loop=0,optimize=False)
thumb=Image.new('RGB',(960,540),'#111a22')
for idx,(tag,f) in enumerate([('FP',49),('TP',49),('FP',338),('TP',197)]):
 im=Image.open(out/f'preview_{tag}_{f}.png').resize((480,270));thumb.paste(im,((idx%2)*480,(idx//2)*270))
thumb.save(out/'ContactSheet.jpg',quality=92)
print('PREVIEW_READY')
