from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json
OUT=Path(r'C:\Users\29\Desktop\blender2\output_v02')
schedule=json.loads((OUT/'preview_schedule.json').read_text())
folder=OUT/'frames_compare';folder.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
gif=[]
for i,item in enumerate(schedule):
 im=Image.new('RGB',(1440,460),'#111a22');d=ImageDraw.Draw(im)
 for x,tag in [(0,'FP'),(720,'TP')]:
  im.paste(Image.open(OUT/f'frames_{tag}'/f'{i:04}.png').convert('RGB').resize((720,405)),(x,55))
  d.text((x+18,10),f'{"FIRST PERSON" if tag=="FP" else "THIRD PERSON"}  /  {item["clip"]}',font=font,fill='#edf5f5')
  d.text((x+18,35),f'v02  |  Source frame {item["frame"]} / 30 fps',font=small,fill='#8dbbbf')
 im.save(folder/f'{i:04}.png')
 gif.append(im.resize((960,307)))
gif[0].save(OUT/'Macuahuitl_v02_Preview.gif',save_all=True,append_images=gif[1:],duration=67,loop=0,optimize=False)
# Direct visual comparison at identical idle posture.
contact=Image.new('RGB',(1440,900),'#111a22');d=ImageDraw.Draw(contact)
for row,tag in enumerate(['FP','TP']):
 for col,version in enumerate(['output','output_v02']):
  p=OUT.parent/version/f'preview_{tag}_49.png';im=Image.open(p).resize((720,405));contact.paste(im,(col*720,row*450+45))
  d.text((col*720+18,row*450+12),f'{"v01 BEFORE" if col==0 else "v02 AFTER"}   |   {tag}',font=font,fill='white')
contact.save(OUT/'Before_After.jpg',quality=92)
print('COMPOSE_DONE',len(schedule))
