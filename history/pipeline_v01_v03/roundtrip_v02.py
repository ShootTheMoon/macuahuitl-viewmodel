from pathlib import Path
p=Path(r'C:\Users\29\Desktop\blender2')
source=(p/'roundtrip_macuahuitl.py').read_text(encoding='utf-8')
source=source.replace("blender2\\output'","blender2\\output_v02'")
source=source.replace("['Idle','Attack1','RunLoop','BlockHold']","['Draw','Idle','RunStart','RunLoop','RunStop','Attack1','Attack2','Attack3','BlockIn','BlockHold','BlockOut']")
source=source.replace("name!='Attack1'","name in ['Idle','RunLoop','BlockHold']")
exec(compile(source,'roundtrip_v02','exec'))
