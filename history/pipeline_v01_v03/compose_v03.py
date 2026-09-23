from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,wave,math,random,struct
OUT=Path(r'C:\Users\29\Desktop\blender2\output_v03')
font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',22)
small=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',16)
samples=['Inspect1_Cylinder','Inspect2_Flip','Inspect3_Can','Inspect4_Display','InspectCards','JumpSlam']
sheet=Image.new('RGB',(1280,6*396),(12,22,32));d=ImageDraw.Draw(sheet)
for row,name in enumerate(samples):
    for col,tag in enumerate(['FP','TP']):
        im=Image.open(OUT/f'check_{tag}_{name}.png').convert('RGB');sheet.paste(im,(col*640,row*396+36))
        d.text((col*640+16,row*396+7),f'{tag} / {name}',font=font,fill=(229,237,241))
sheet.save(OUT/'v03_ContactSheet.jpg',quality=92)
if not (OUT/'preview_schedule.json').exists():raise SystemExit()
schedule=json.loads((OUT/'preview_schedule.json').read_text());folder=OUT/'frames_preview';folder.mkdir(exist_ok=True)
for i,item in enumerate(schedule):
    im=Image.open(OUT/'frames_FP'/f'{i:04}.png').convert('RGB')
    canvas=Image.new('RGB',(640,408),(12,22,32));canvas.paste(im,(0,48));dr=ImageDraw.Draw(canvas)
    dr.text((15,7),'MACUAHUITL  /  V03',font=font,fill=(239,180,79))
    dr.text((15,30),item['clip']+'  |  FP animation study',font=small,fill=(195,214,224))
    canvas.save(folder/f'{i:04}.png')
# Synthetic timing cues, not source audio. Dry foley-style clicks, sweeps and impacts.
sr=22050;audio=[0.]*(int(len(schedule)/15*sr)+sr);rng=random.Random(31)
manifest=json.loads((OUT/'animation_manifest.json').read_text());index={c['name']:c for c in manifest['clips']}
first={}
for i,item in enumerate(schedule):first.setdefault(item['clip'],i)
for name,i in first.items():
    for e in index[name]['events']:
        start=int((i/15+(e['frame']-1)/30)*sr);kind=e['event'];dur=.28 if kind in ['whoosh','ignition','impact'] else .10
        for j in range(int(dur*sr)):
            t=j/sr;u=t/dur;noise=rng.uniform(-1,1)
            if kind=='whoosh':val=noise*math.sin(math.pi*u)**2*.11
            elif kind=='impact':val=(math.sin(2*math.pi*(85*t-75*t*t))*.45+noise*.16)*math.exp(-18*t)
            elif kind=='ignition':val=noise*.13*(1-u)
            else:val=(math.sin(2*math.pi*900*t)*.13+noise*.08)*math.exp(-55*t)
            if start+j<len(audio):audio[start+j]+=val*e.get('strength',1)
with wave.open(str(OUT/'Preview_Cues.wav'),'w') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(b''.join(struct.pack('<h',int(max(-1,min(1,x))*30000)) for x in audio))
print('COMPOSED',len(schedule))
