import bpy, math, json, os
from mathutils import Vector, Matrix, Quaternion
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output')
OUT.mkdir(exist_ok=True)
scene=bpy.context.scene
scene.render.fps=30
rig=bpy.data.objects['Armature']
base={p.name:p.matrix.copy() for p in rig.pose.bones}
original_names=list(base)
for n in ['Cube','Camera','Light']:
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
chars=[o for o in scene.objects if o.type=='MESH' and o.name.endswith('_Geo')]
weapons=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('WPN_')]
root=bpy.data.objects['WPN_Macuahuitl_A']
for im in bpy.data.images:
    if im.source=='FILE' and os.path.exists(im.filepath): im.pack()
def mat(name,col,metal=0,rough=.45):
    m=bpy.data.materials.new(name); m.diffuse_color=(*col,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*col,1)
    p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    return m
armmat=mat('Avatar_Graphite_Teal',(.045,.105,.115),.25)
for o in chars:
    o.data.materials.clear(); o.data.materials.append(armmat)
idle={'r':[-.255,-.305,1.085],'l':[.27,-.255,1.04],'d':[-.16,-.65,.74],'roll':-.12,'body':0}
def variant(**kw):
    p={k:(v.copy() if isinstance(v,list) else v) for k,v in idle.items()}; p.update(kw); return p
run=variant(r=[-.25,-.23,.98],l=[.23,-.28,1.03],d=[-.28,.45,.84],roll=.25)
guard=variant(r=[-.20,-.30,1.20],l=[.20,-.31,1.18],d=[.94,-.15,.25],roll=.05)
a1=variant(r=[.14,-.32,1.03],l=[.23,-.19,1.06],d=[.8,-.30,-.25],body=-.18)
a2=variant(r=[-.25,-.25,1.14],d=[-.8,-.35,.38],body=.15)
clips={
 'Draw':(40,[(0,variant(r=[-.23,.08,.83],d=[-.2,.5,-.6])),(.40,variant(r=[-.29,-.22,1.17],d=[-.4,-.4,.6])),(.67,variant(r=[-.25,-.32,1.10],d=[-.1,-.15,1],roll=.13)),(1,idle)]),
 'Idle':(61,[(0,idle),(1,idle)]),
 'RunStart':(13,[(0,idle),(1,run)]),
 'RunLoop':(25,[(0,run),(1,run)]),
 'RunStop':(13,[(0,run),(1,idle)]),
 'Attack1':(31,[(0,idle),(.24,variant(r=[-.32,-.15,1.20],d=[-.65,.2,.8],body=.13)),(.40,variant(r=[-.14,-.36,1.20],d=[.5,-.8,.1])),(.55,a1),(.72,a1),(1,idle)]),
 'Attack2':(31,[(0,idle),(.22,variant(r=[.12,-.29,1.10],d=[.95,.1,.25],body=-.18)),(.42,variant(r=[-.16,-.37,1.14],d=[-.7,-.7,.1])),(.59,a2),(.74,a2),(1,idle)]),
 'Attack3':(40,[(0,idle),(.30,variant(r=[-.14,-.15,1.38],l=[.06,-.24,1.27],d=[.15,.35,.96],body=.06)),(.43,variant(r=[-.10,-.37,1.15],l=[.12,-.31,1.11],d=[0,-1,.1],body=-.05)),(.56,variant(r=[-.09,-.33,.94],l=[.16,-.27,.99],d=[.1,-.4,-.9],body=-.12)),(.72,variant(r=[-.12,-.30,.98],d=[.1,-.5,-.65])),(1,idle)]),
 'BlockIn':(10,[(0,idle),(1,guard)]),
 'BlockHold':(31,[(0,guard),(1,guard)]),
 'BlockOut':(13,[(0,guard),(1,idle)])}
def sample(keys,t):
    for i in range(len(keys)-1):
        ta,a=keys[i]; tb,b=keys[i+1]
        if t<=tb+1e-8:
            u=max(0,min(1,(t-ta)/(tb-ta))); u=u*u*(3-2*u)
            return {k: list(Vector(a[k]).lerp(Vector(b[k]),u)) if isinstance(a[k],list) else a[k]*(1-u)+b[k]*u for k in a}
    return keys[-1][1]
def sword_q(d,roll):
    y=-Vector(d).normalized(); x=Vector((0,-1,0)); x=(x-y*x.dot(y)).normalized()
    if x.length<.1: x=Vector((1,0,0))
    z=x.cross(y).normalized(); x=y.cross(z).normalized()
    return Matrix((x,y,z)).transposed().to_quaternion() @ Quaternion((0,1,0),roll)
def set_arm(r,side,target):
    names=[side+'UpperArm',side+'LowerArm',side+'Hand']
    s=base[names[0]].translation*.01
    bh=base[names[1]].translation*.01; wh=base[names[2]].translation*.01
    l1=(bh-s).length; l2=(wh-bh).length
    v=Vector(target)-s; dist=max(.06,min(v.length,l1+l2-.003)); v.normalize(); w=s+v*dist
    pole=Vector((-.9 if side=='Right' else .9,.20,-.55)); pole=(pole-v*pole.dot(v)).normalized()
    along=(l1*l1-l2*l2+dist*dist)/(2*dist)
    e=s+v*along+pole*math.sqrt(max(0,l1*l1-along*along))
    for n,oldv,newv,head in [(names[0],bh-s,e-s,s),(names[1],wh-bh,w-e,e)]:
        q=oldv.rotation_difference(newv)
        m=q.to_matrix().to_4x4() @ base[n]; m.translation=head*100
        r.pose.bones[n].matrix=m; bpy.context.view_layer.update()
    hm=r.pose.bones[names[1]].matrix.to_quaternion().to_matrix().to_4x4()
    hm.translation=w*100
    r.pose.bones[names[2]].matrix=hm
    return w,hm
for p in rig.pose.bones: p.matrix=base[p.name]
wr,hm=set_arm(rig,'Right',idle['r'])
q0=sword_q(idle['d'],idle['roll'])
hand_offset=q0.inverted() @ hm.to_quaternion()
grip=Vector((0,.28,0))
W=q0.to_matrix().to_4x4(); W.translation=wr-q0@grip
root.matrix_world=W
bpy.context.view_layer.update()
# Bind weapon geometry to the existing right-hand bone; no extra skeleton bones.
for o in weapons:
    mw=o.matrix_world.copy(); o.parent=None; o.matrix_world=mw
    vg=o.vertex_groups.new(name='RightHand'); vg.add(list(range(len(o.data.vertices))),1,'REPLACE')
    # Geometry is converted below to rest-space so it deforms with the original skeleton.
    pose_world=rig.matrix_world @ rig.pose.bones['RightHand'].matrix
    rest_world=rig.matrix_world @ rig.data.bones['RightHand'].matrix_local
    o.data.transform(rest_world @ pose_world.inverted() @ o.matrix_world)
    o.matrix_world=Matrix.Identity(4)
    mod=o.modifiers.new('OVDR_RightHand_Skin','ARMATURE'); mod.object=rig
    o.parent=rig; o.matrix_parent_inverse=rig.matrix_world.inverted()
bpy.data.objects.remove(root,do_unlink=True)
rig.name='FP_ODA_Rig'
for o in chars+weapons: o.name='FP_'+o.name
fp_objects=chars+weapons
tp=rig.copy(); tp.data=rig.data.copy(); scene.collection.objects.link(tp); tp.name='TP_ODA_Rig'; tp.location.x=2.8
tp_objects=[]
for o in fp_objects:
    c=o.copy(); c.data=o.data.copy(); scene.collection.objects.link(c); c.name=o.name.replace('FP_','TP_',1)
    c.parent=tp; c.matrix_parent_inverse=o.matrix_parent_inverse.copy()
    for m in c.modifiers:
        if m.type=='ARMATURE': m.object=tp
    tp_objects.append(c)
for o in chars:
    if 'Arm_Geo' not in o.name: o.hide_render=True; o.hide_set(True)
def pose(r,p,clip,t,tp_mode):
    for b in r.pose.bones: b.matrix=base[b.name]
    bpy.context.view_layer.update()
    p={k:(v.copy() if isinstance(v,list) else v) for k,v in p.items()}
    bob=0
    if clip in ('Idle','BlockHold'):
        bob=.004*math.sin(2*math.pi*t)
    if clip=='RunLoop':
        bob=.012*math.sin(4*math.pi*t)
        p['r'][1]+=.025*math.sin(2*math.pi*t); p['l'][1]-=.03*math.sin(2*math.pi*t)
        p['roll']+=.07*math.sin(2*math.pi*t)
    p['r'][2]+=bob; p['l'][2]+=bob
    wr,hm=set_arm(r,'Right',p['r']); set_arm(r,'Left',p['l'])
    q=sword_q(p['d'],p['roll']) @ hand_offset
    hm=q.to_matrix().to_4x4(); hm.translation=wr*100; r.pose.bones['RightHand'].matrix=hm
    bpy.context.view_layer.update()
    for side in ['Right','Left']:
        r.pose.bones[side+'Hand001'].matrix=r.pose.bones[side+'Hand'].matrix.copy()
        bpy.context.view_layer.update()
    if tp_mode:
        # Whole upper-body rotation preserves arm chain continuity.
        twist=Quaternion((0,0,1),p['body']); pivot=Vector((0,0,79))
        T=Matrix.Translation(pivot) @ twist.to_matrix().to_4x4() @ Matrix.Translation(-pivot)
        upper=['UpperTorso01','UpperTorso02','Head','Head_Nub','RightUpperArm','RightLowerArm','RightHand','RightHand001','LeftUpperArm','LeftLowerArm','LeftHand','LeftHand001']
        mats={n:T@r.pose.bones[n].matrix.copy() for n in upper}
        for n in upper: r.pose.bones[n].matrix=mats[n]; bpy.context.view_layer.update()
        if clip=='RunLoop':
            for side,phase in [('Right',0),('Left',math.pi)]:
                angle=.48*math.sin(2*math.pi*t+phase)
                n=side+'UpperLeg'; b=r.pose.bones[n]; m=base[n].copy(); h=m.translation.copy()
                T=Matrix.Translation(h)@Quaternion((1,0,0),angle).to_matrix().to_4x4()@Matrix.Translation(-h)
                for suffix in ['UpperLeg','LowerLeg','Foot','Foot_Nub']:
                    n=side+suffix; r.pose.bones[n].matrix=T@base[n]; bpy.context.view_layer.update()
    for b in r.pose.bones:
        b.rotation_mode='QUATERNION'
        b.keyframe_insert(data_path='location'); b.keyframe_insert(data_path='rotation_quaternion'); b.keyframe_insert(data_path='scale')
manifest={'fps':30,'source_skeleton_bones':original_names,'clips':[],'status':'Blender-authored; OVERDARE import validation pending','weapon_credit':'Macuahuitl Aztec Sword by patovg9, Sketchfab 49c9a80a51ad417cb7ba2b6a2d06b9c9, CC-BY'}
actions={}
for r,tag in [(rig,'FP'),(tp,'TP')]:
    r.animation_data_create()
    for name,(count,keys) in clips.items():
        ac=bpy.data.actions.new('MX_'+tag+'_'+name); ac.use_fake_user=True; r.animation_data.action=ac
        for f in range(1,count+1):
            scene.frame_set(f); t=(f-1)/(count-1); pose(r,sample(keys,t),name,t,tag=='TP')
        actions[(tag,name)]=ac
        if tag=='FP': manifest['clips'].append({'name':name,'frames':count,'duration':(count-1)/30,'loop':name in ('Idle','RunLoop','BlockHold'),'hit_frame': {'Attack1':13,'Attack2':14,'Attack3':18}.get(name)})
    r.animation_data.action=None
# Sequential preview strips; individual actions remain directly editable.
cursor=1
for name,(count,keys) in clips.items():
    scene.timeline_markers.new(name,frame=cursor)
    for r,tag in [(rig,'FP'),(tp,'TP')]:
        track=r.animation_data.nla_tracks.new(); track.name='Preview_'+name
        st=track.strips.new('MX_'+tag+'_'+name,cursor,actions[(tag,name)]); st.extrapolation='HOLD_FORWARD'
    cursor+=count+8
scene.frame_end=cursor-8
def camera(name,pos,target,lens):
    d=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,d); scene.collection.objects.link(c)
    c.location=pos; c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler(); d.lens=lens; d.clip_start=.025
    return c
fp_cam=camera('CAM_FirstPerson',(0,.22,1.40),(0,-1,1.30),20)
tp_cam=camera('CAM_ThirdPerson',(4.8,-3.5,1.95),(2.8,0,.87),45)
scene.camera=fp_cam
world=bpy.data.worlds.new('Studio_Slate'); world.use_nodes=True; world.node_tree.nodes['Background'].inputs[0].default_value=(.022,.033,.047,1); world.node_tree.nodes['Background'].inputs[1].default_value=.5; scene.world=world
for name,pos,power,size in [('Key',(-2,-3,4),650,4),('Fill',(3,-1,2.5),400,3),('Rim',(1,2,3),800,3)]:
    d=bpy.data.lights.new(name,'AREA'); o=bpy.data.objects.new(name,d); scene.collection.objects.link(o); o.location=pos; d.energy=power; d.shape='DISK'; d.size=size; o.rotation_euler=(Vector((1,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES'; scene.cycles.samples=16
scene.render.resolution_x=960; scene.render.resolution_y=540; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.frame_set(49)
for area in (bpy.context.screen.areas if bpy.context.screen else []):
    if area.type=='VIEW_3D': area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Macuahuitl_FP_TP_AnimationSet.blend'))
(OUT/'animation_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('BUILT',len(actions),'actions',scene.frame_end,'preview frames')
