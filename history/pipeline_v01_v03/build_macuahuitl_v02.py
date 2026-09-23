import bpy, math, json, os
from mathutils import Vector, Matrix, Quaternion
from pathlib import Path
OUT=Path(r'C:\Users\29\Desktop\blender2\output_v02')
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
# Curl the original finger geometry in hand-local bind space, preserving topology,
# weights, and the 22-bone ODA skeleton. This is a fixed gripping mesh, not finger animation.
for side in ['Right','Left']:
    o=bpy.data.objects[side+'Arm_Geo']; b=rig.data.bones[side+'Hand']
    hand_from_mesh=b.matrix_local.inverted() @ rig.matrix_world.inverted() @ o.matrix_world
    mesh_from_hand=hand_from_mesh.inverted(); gi=o.vertex_groups[side+'Hand'].index
    for v in o.data.vertices:
        weight=next((g.weight for g in v.groups if g.group==gi),0)
        if weight<.5: continue
        p=hand_from_mesh@v.co
        # Four-finger span begins beyond the palm; wrap extension toward the palm.
        if p.x < -9.0:
            length=-p.x-9.0; theta=min(2.55,length/4.0)
            thickness=p.y+2.5
            p.x=-9.0-4.0*math.sin(theta)-thickness*.22*math.sin(theta)
            p.y=-2.5-4.0*(1-math.cos(theta))+thickness*.55
        p.z*=.78
        v.co=mesh_from_hand@p
idle={'r':[-.255,-.305,1.085],'l':[.27,-.255,1.04],'d':[-.16,-.65,.74],'roll':-.12,'body':0}
def variant(**kw):
    p={k:(v.copy() if isinstance(v,list) else v) for k,v in idle.items()}; p.update(kw); return p
run=variant(r=[-.25,-.20,1.02],l=[.23,-.22,1.06],d=[-.36,-.2,.91],roll=.15)
guard=variant(r=[-.20,-.30,1.20],l=[-.02,-.23,1.10],d=[.94,-.15,.25],roll=.05)
a1=variant(r=[.085,-.32,1.10],l=[.22,-.18,1.07],d=[.86,-.49,.02],body=-.28)
a2=variant(r=[-.28,-.25,1.12],d=[-.82,-.55,.17],body=.24)
clips={
 'Draw':(40,[(0,variant(r=[-.23,.08,.83],d=[-.2,.5,-.6],roll=-.7)),(.28,variant(r=[-.29,-.22,1.15],d=[-.8,-.45,.15],roll=-.8)),(.48,variant(r=[-.23,-.33,1.16],d=[-.10,-.5,.87],roll=.32)),(.66,variant(r=[-.26,-.29,1.06],d=[-.2,-.7,.68],roll=-.24)),(1,idle)]),
 'Idle':(61,[(0,idle),(1,idle)]),
 'RunStart':(13,[(0,idle),(1,run)]),
 'RunLoop':(25,[(0,run),(1,run)]),
 'RunStop':(13,[(0,run),(1,idle)]),
 'Attack1':(31,[(0,idle),(.23,variant(r=[-.31,-.15,1.20],d=[-.55,.1,.83],body=.20)),(.36,variant(r=[-.12,-.36,1.18],l=[.24,-.18,1.08],d=[.22,-.96,.12],body=-.10)),(.49,a1),(.64,variant(r=[.06,-.29,1.09],d=[.73,-.64,.24],body=-.23)),(.84,variant(r=[-.23,-.28,1.05],d=[-.29,-.8,.53],body=.025)),(1,idle)]),
 'Attack2':(31,[(0,idle),(.22,variant(r=[.10,-.28,1.17],d=[.92,-.1,.37],body=-.24)),(.35,variant(r=[-.11,-.38,1.17],d=[-.28,-.95,.08],body=.06)),(.48,a2),(.65,variant(r=[-.28,-.23,1.11],d=[-.73,-.6,.31],body=.19)),(.85,variant(r=[-.25,-.30,1.10],d=[-.1,-.67,.74],body=-.025)),(1,idle)]),
 'Attack3':(40,[(0,idle),(.28,variant(r=[-.15,-.12,1.36],l=[.12,-.20,1.27],d=[.13,.2,.97],body=.10)),(.38,variant(r=[-.11,-.32,1.27],l=[.13,-.30,1.12],d=[.1,-.86,.5],body=.02)),(.46,variant(r=[-.1,-.37,1.09],l=[.20,-.21,1.08],d=[.08,-.92,-.38],body=-.18)),(.60,variant(r=[-.10,-.30,1.05],d=[.15,-.7,-.7],body=-.15)),(.83,variant(r=[-.25,-.28,1.10],d=[-.15,-.4,.9],body=.025)),(1,idle)]),
 'BlockIn':(10,[(0,idle),(1,guard)]),
 'BlockHold':(31,[(0,guard),(1,guard)]),
 'BlockOut':(13,[(0,guard),(1,idle)])}
def sample(keys,t):
    for i in range(len(keys)-1):
        ta,a=keys[i]; tb,b=keys[i+1]
        if t<=tb+1e-8:
            u=max(0,min(1,(t-ta)/(tb-ta))); ease=u*u*(3-2*u)
            result={k: list(Vector(a[k]).lerp(Vector(b[k]),ease)) if isinstance(a[k],list) else a[k]*(1-ease)+b[k]*ease for k in a}
            # Continuous hand tangents through passing poses; no stop at every waypoint.
            for k in ['r','l']:
                prev=keys[max(0,i-1)]; nxt=keys[min(len(keys)-1,i+2)]
                va,vb=Vector(a[k]),Vector(b[k]); dt=tb-ta
                ma=(vb-Vector(prev[1][k]))/max(.001,tb-prev[0]) if i else Vector((0,0,0))
                mb=(Vector(nxt[1][k])-va)/max(.001,nxt[0]-ta) if i+1<len(keys)-1 else Vector((0,0,0))
                result[k]=list((2*u**3-3*u*u+1)*va+(u**3-2*u*u+u)*dt*ma+(-2*u**3+3*u*u)*vb+(u**3-u*u)*dt*mb)
            result['_q']=sword_q(a['d'],a['roll']).slerp(sword_q(b['d'],b['roll']),ease)
            return result
    return keys[-1][1]
def sword_q(d,roll):
    reference=Vector(idle['d']).normalized()
    y=-reference; x=Vector((0,-1,0)); x=(x-y*x.dot(y)).normalized()
    z=x.cross(y).normalized(); x=y.cross(z).normalized()
    frame=Matrix((x,y,z)).transposed().to_quaternion()
    return reference.rotation_difference(Vector(d).normalized()) @ frame @ Quaternion((0,1,0),roll)
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
hand_offset=Matrix(((0,-1,0),(0,0,1),(-1,0,0))).to_quaternion()
hm=(q0@hand_offset).to_matrix().to_4x4(); hm.translation=wr*100
rig.pose.bones['RightHand'].matrix=hm; bpy.context.view_layer.update()
grip_center=Vector((-8.3,-4.4,0))*.01
grip=Vector((0,.28,0))
W=q0.to_matrix().to_4x4(); W.translation=wr+(q0@hand_offset)@grip_center-q0@grip
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
def leg_pose(r,side,ankle,hip_drop):
    names=[side+'UpperLeg',side+'LowerLeg',side+'Foot']
    h=base[names[0]].translation*.01+Vector((0,0,-hip_drop))
    k0=base[names[1]].translation*.01; h0=base[names[0]].translation*.01
    a0=base[names[2]].translation*.01
    l1=(k0-h0).length; l2=(a0-k0).length
    vec=Vector(ankle)-h; dist=min(vec.length,l1+l2-.001); vec.normalize()
    a=h+vec*dist; pole=Vector((0,-1,0)); pole=(pole-vec*pole.dot(vec)).normalized()
    along=(l1*l1-l2*l2+dist*dist)/(2*dist)
    k=h+vec*along+pole*math.sqrt(max(0,l1*l1-along*along))
    for n,oldv,newv,head in [(names[0],k0-h0,k-h,h),(names[1],a0-k0,a-k,k)]:
        m=oldv.rotation_difference(newv).to_matrix().to_4x4()@base[n]; m.translation=head*100
        r.pose.bones[n].matrix=m; bpy.context.view_layer.update()
    for suffix in ['Foot','Foot_Nub']:
        n=side+suffix; m=base[n].copy(); m.translation+=(a-a0)*100
        r.pose.bones[n].matrix=m; bpy.context.view_layer.update()
def gait_ankle(side,t):
    phase=(t+(0 if side=='Right' else .5))%1.0
    if phase<.55:
        y=-.15+.30*phase/.55; lift=0
    else:
        u=(phase-.55)/.45; ease=u*u*(3-2*u)
        y=.15-.30*ease; lift=.15*math.sin(math.pi*u)**1.2
    return Vector((-.105 if side=='Right' else .105,y,.174+lift))
def pose(r,p,clip,t,tp_mode):
    for b in r.pose.bones:
        b.matrix=base[b.name]
        bpy.context.view_layer.update()
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
    q=(sword_q(p['d'],p['roll']) if clip=='RunLoop' else p.get('_q',sword_q(p['d'],p['roll']))) @ hand_offset
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
        run_weight=1 if clip=='RunLoop' else t*t*(3-2*t) if clip=='RunStart' else 1-t*t*(3-2*t) if clip=='RunStop' else 0
        hip_drop=.025+.025*run_weight
        if clip=='RunLoop': hip_drop+=.010*(1-math.cos(4*math.pi*t))
        if clip.startswith('Attack'): hip_drop+=.015*math.sin(math.pi*t)**2
        # Translate the entire upper skeleton together; legs solve to ground contacts.
        upper_names=['LowerTorso']+upper
        shifted={n:Matrix.Translation((0,0,-hip_drop*100))@r.pose.bones[n].matrix.copy() for n in upper_names}
        for n in upper_names: r.pose.bones[n].matrix=shifted[n]; bpy.context.view_layer.update()
        for side in ['Right','Left']:
            idle_ankle=base[side+'Foot'].translation*.01
            target=idle_ankle.lerp(gait_ankle(side,t if clip=='RunLoop' else 0),run_weight)
            leg_pose(r,side,target,hip_drop)
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
        if tag=='FP': manifest['clips'].append({'name':name,'frames':count,'duration':(count-1)/30,'loop':name in ('Idle','RunLoop','BlockHold'),'hit_frame': {'Attack1':12,'Attack2':12,'Attack3':19}.get(name)})
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
bpy.ops.mesh.primitive_plane_add(size=3,location=(2.8,0,-.005))
floor=bpy.context.object; floor.name='Preview_Ground_TP'; floor.data.materials.append(mat('Ground',(.035,.05,.06),0,.8))
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
