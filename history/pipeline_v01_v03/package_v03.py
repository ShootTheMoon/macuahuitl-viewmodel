from pathlib import Path
import zipfile,json
ROOT=Path(r'C:\Users\29\Desktop\blender2');OUT=ROOT/'output_v03'
files=[p for p in OUT.iterdir() if p.is_file() and p.suffix in ['.md','.json','.mp4','.wav']]
files += [OUT/'Macuahuitl_v03_Expanded.blend',OUT/'v03_ContactSheet.jpg']
files += list((OUT/'FBX').rglob('*.fbx'))
scripts=['build_macuahuitl_v02.py','build_macuahuitl_v03.py','fix_v03_hilt.py','export_v03.py','optimize_v03_export.py','export_v03_camera.py','roundtrip_v03.py','render_v03.py','compose_v03.py','encode_v03.py','verify_video_v03.py','audit_v03_meshes.py']
zip_path=OUT/'Macuahuitl_v03_Expanded_Package.zip'
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:z.write(p,str(p.relative_to(OUT)))
    for name in scripts:z.write(ROOT/name,'Scripts/'+name)
    z.write(ROOT/'assets/Macuahuitl/05_Documentation/WPN_Macuahuitl_A_Notes.md','Source_Credit/WPN_Macuahuitl_A_Notes.md')
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    print('PACKAGE_OK',len(z.namelist()),zip_path.stat().st_size)
