"""Build from the imported source, keeping the supplied ODA skeleton intact."""
import bpy, bmesh, math, json, random
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
ROOT=Path(r'C:\Users\29\Desktop\blender2')
# Reuse the established avatar IK and source-material import, not v02's baked clips.
source=(ROOT/'build_macuahuitl_v02.py').read_text(encoding='utf-8').split("manifest={'fps'")[0]
source=source.replace("output_v02", "output_v03")
source=source.replace("for side in ['Right','Left']:\n    o=bpy.data.objects", "open_hands={}\nfor side in ['Right','Left']:\n    o=bpy.data.objects",1)
source=source.replace("hand_from_mesh=b.matrix_local", "open_hands[side]=[v.co.copy() for v in o.data.vertices]\n    hand_from_mesh=b.matrix_local",1)
exec(compile(source,'v02_source_and_ik','exec'),globals())
OUT=ROOT/'output_v03'
# Recover unskinned source-space geometry at the exact original binding pose.
for b in rig.pose.bones:
    b.matrix=base[b.name]; bpy.context.view_layer.update()
wr,_=set_arm(rig,'Right',idle['r'])
hm=(q0@hand_offset).to_matrix().to_4x4(); hm.translation=wr*100
rig.pose.bones['RightHand'].matrix=hm; bpy.context.view_layer.update()
templates=[]
for o in weapons:
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=bpy.data.meshes.new_from_object(ev); me.transform(W.inverted()@o.matrix_world)
    templates.append((o.name,me))
for o in list(scene.objects):
    if o.type=='MESH' and '_WPN_' in o.name: bpy.data.objects.remove(o,do_unlink=True)
for tag in ['FP','TP']:
    for side in ['Right','Left']:
        ob=bpy.data.objects[tag+'_'+side+'Arm_Geo']
        ob.shape_key_add(name='Grip'); op=ob.shape_key_add(name='Open')
        for v,co in zip(op.data,open_hands[side]): v.co=co

metal=mat('Mechanism_Titanium',(.12,.16,.20),.85,.26)
gold=mat('Mechanism_Brass',(.62,.28,.07),.8,.28)
blue=mat('Can_Cobalt',(.015,.17,.66),.6,.25)
red=mat('Cylinder_Red',(.55,.025,.018),.55,.24)
paper=mat('Card_Ivory',(.9,.82,.60),.05,.5)
orange=mat('Ignition_Core',(1,.19,.008),.2,.25)
bs=orange.node_tree.nodes.get('Principled BSDF'); bs.inputs['Emission Color'].default_value=(1,.18,.006,1);bs.inputs['Emission Strength'].default_value=5

prop_names=['Weapon','PanelLeft','PanelRight','Can','Card','Cylinder']
prop_rigs={}; prop_meshes={}
def bind(ob,pr,bone):
    ob.data.transform(ob.matrix_world); ob.matrix_world=Matrix.Identity(4)
    vg=ob.vertex_groups.new(name=bone);vg.add(list(range(len(ob.data.vertices))),1,'REPLACE')
    mod=ob.modifiers.new('PropSkin','ARMATURE');mod.object=pr
    ob.parent=pr; ob.matrix_parent_inverse=Matrix.Identity(4)
    ob.name=pr.name[:2]+'_'+ob.name
    prop_meshes[pr.name[:2]].append(ob)
    return ob
def cube(name,pos,size,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.name=name;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    be=o.modifiers.new('Machined_Edges','BEVEL');be.width=.004;be.segments=2
    bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=be.name)
    return o
def cyl(name,pos,radius,depth,material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=radius,depth=depth,location=pos)
    o=bpy.context.object;o.name=name;o.data.materials.append(material);return o
for tag in ['FP','TP']:
    data=bpy.data.armatures.new(tag+'_Props');pr=bpy.data.objects.new(tag+'_PropRig',data);scene.collection.objects.link(pr)
    bpy.context.view_layer.objects.active=pr;pr.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
    for name in prop_names:
        b=data.edit_bones.new(name);b.head=(0,0,0);b.tail=(0,.1,0)
        if name!='Weapon': b.parent=data.edit_bones['Weapon']
    bpy.ops.object.mode_set(mode='OBJECT'); pr.select_set(False);pr.location.x=0 if tag=='FP' else 2.8
    prop_rigs[tag]=pr;prop_meshes[tag]=[]
    for name,me in templates:
        if 'Handle' in name:
            ob=bpy.data.objects.new('Macuahuitl_Handle',me.copy());scene.collection.objects.link(ob);bind(ob,pr,'Weapon')
        else:
            for side,clear_inner in [('Left',False),('Right',True)]:
                mesh=me.copy();bm=bmesh.new();bm.from_mesh(mesh)
                bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,0,0),plane_no=(0,0,1),clear_inner=clear_inner,clear_outer=not clear_inner)
                bm.to_mesh(mesh);bm.free()
                ob=bpy.data.objects.new('Macuahuitl_'+side+'_'+name.split('_')[-1],mesh);scene.collection.objects.link(ob);bind(ob,pr,'Panel'+side)
    bind(cube('Internal_Chassis',(0,-.14,0),(.00504,.54,.065),metal),pr,'Weapon')
    for i in range(7):
        bind(cube('Core_Vent_'+str(i),(.0033,-.34+i*.052,0),(.0018,.016,.052),orange),pr,'Weapon')
    for x in [-.043,.043]:
        bind(cube('Rail',(0,-.13,x),(.043,.55,.01),gold),pr,'Weapon')
    bind(cyl('Blue_Can',(0,0,0),.033,.12,blue),pr,'Can')
    for z in [-.06,.06]:bind(cyl('Can_Rim',(0,0,z),.034,.005,metal),pr,'Can')
    bind(cube('Can_Label',(0,-.032,0),(.040,.003,.065),paper),pr,'Can')
    bind(cube('Card_Border',(0,0,0),(.092,.004,.14),red),pr,'Card')
    bind(cube('Card_Face',(0,.0028,0),(.081,.002,.128),paper),pr,'Card')
    # Readable geometric illustration, intentionally not extracted Apex artwork.
    bind(cube('Card_Sigil',(0,.005,.015),(.045,.002,.045),gold),pr,'Card')
    for z in [-.025,-.035,-.045]:bind(cube('Card_Print',(0,.005,z),(.055,.002,.002),metal),pr,'Card')
    bind(cyl('Red_Cylinder',(0,0,0),.035,.15,red),pr,'Cylinder')
    for z in [-.074,.074]:bind(cyl('Cylinder_Cap',(0,0,z),.037,.009,metal),pr,'Cylinder')
    bind(cube('Cylinder_Stripe',(0,-.035,0),(.034,.003,.09),gold),pr,'Cylinder')

def v(r=None,l=None,d=None,roll=0,body=0):
    return variant(r=r or idle['r'],l=l or idle['l'],d=d or idle['d'],roll=roll,body=body)
horizontal=v(r=[-.23,-.37,1.24],l=[.18,-.34,1.20],d=[.96,-.12,.10],roll=.3)
raised=v(r=[-.20,-.31,1.15],l=[.25,-.25,1.08],d=[-.30,-.5,.81],roll=.2)
under=v(r=[-.25,-.19,.82],l=[.25,-.16,.87],d=[-.7,-.5,.2],body=.1)
canpose=v(r=[-.08,-.34,1.23],l=[.22,-.32,1.09],d=[-.05,-.4,.92],roll=.2)
cardpose=v(r=[-.13,-.30,1.14],l=[.15,-.36,1.20],d=[-.2,-.8,.5],body=-.08)
clips.update({
 'Inspect1_Cylinder':(151,[(0,idle),(.14,horizontal),(.30,horizontal),(.38,dict(horizontal,l=[.17,-.38,1.22],roll=-.2)),(.55,dict(horizontal,l=[.17,-.38,1.22],roll=-.2)),(.70,horizontal),(.84,raised),(1,idle)]),
 'Inspect2_Flip':(106,[(0,idle),(.17,raised),(.32,v(r=[-.12,-.37,1.14],d=[-.8,-.3,.5])),(.63,v(r=[-.20,-.36,1.15],d=[.8,-.4,.3])),(.78,raised),(1,idle)]),
 'Inspect3_Can':(241,[(0,idle),(.12,horizontal),(.27,horizontal),(.38,canpose),(.55,canpose),(.64,v(r=[-.08,-.16,1.34],l=canpose['l'])),(.74,canpose),(.84,horizontal),(1,idle)]),
 'Inspect4_Display':(151,[(0,idle),(.18,horizontal),(.40,dict(horizontal,roll=1.45)),(.60,dict(horizontal,roll=-.8)),(.78,horizontal),(1,idle)]),
 'CrouchIn':(19,[(0,idle),(1,under)]),
 'CrouchIdle':(61,[(0,under),(1,under)]),
 'CrouchOut':(19,[(0,under),(1,idle)]),
 'InspectCards':(211,[(0,idle),(.10,under),(.24,cardpose),(.72,cardpose),(.88,under),(1,idle)]),
 'FirstDraw':(70,[(0,under),(.18,raised),(.40,horizontal),(.65,dict(horizontal,roll=-1.2)),(.83,raised),(1,idle)]),
 'CrouchAttack':(37,[(0,under),(.26,v(r=[-.32,-.13,.98],d=[-.9,.1,.2],body=.4)),(.38,v(r=[.03,-.4,.97],d=[.9,-.4,.02],body=-.45)),(.45,v(r=[.03,-.4,.97],d=[.9,-.4,.02],body=-.45)),(.67,v(r=[.08,-.29,.87],d=[.7,-.3,-.4],body=-.25)),(1,under)]),
 'JumpSlam':(55,[(0,idle),(.26,v(r=[-.07,-.11,1.47],l=[.06,-.20,1.39],d=[.05,.2,.98],body=.18)),(.44,v(r=[-.06,-.31,1.42],l=[.10,-.32,1.26],d=[0,-.65,.76])),(.51,v(r=[-.09,-.38,.96],l=[.09,-.30,1.05],d=[0,-.78,-.62],body=-.22)),(.56,v(r=[-.09,-.38,.96],l=[.09,-.30,1.05],d=[0,-.78,-.62],body=-.22)),(.72,under),(1,idle)]),
 'SprintTwirl':(43,[(0,run),(.22,v(r=[-.16,-.33,1.10],d=[.9,-.3,.1])),(.70,v(r=[-.20,-.31,1.06],d=[-.8,-.4,.2])),(1,run)]),
 'RareDraw':(64,[(0,under),(.22,raised),(.45,v(r=[-.14,-.32,1.17],d=[.8,-.2,.5])),(.76,raised),(1,idle)]),
 'SprintDraw':(37,[(0,under),(.27,v(r=[-.19,-.29,.97],d=[.9,-.2,.1])),(.63,raised),(1,run)]),
 'Holster':(25,[(0,idle),(.35,dict(raised,roll=-.5)),(1,under)])
})
# A readable pause follows the fast strike, rather than smoothing straight through it.
for name in ['Attack1','Attack2','Attack3']:
    n,keys=clips[name]; impact={'Attack1':.49,'Attack2':.48,'Attack3':.46}[name]
    idx=next(i for i,k in enumerate(keys) if abs(k[0]-impact)<.001)
    keys.insert(idx+1,(impact+.055,keys[idx][1]))

def envelope(t,a,b,c,d):
    def smooth(x): x=max(0,min(1,x));return x*x*(3-2*x)
    return smooth((t-a)/max(.0001,b-a))*(1-smooth((t-c)/max(.0001,d-c)))
def hand_world(r,side):
    m=r.pose.bones[side+'Hand'].matrix
    return m.translation*.01+m.to_quaternion()@grip_center
def weapon_matrix(r):
    hm=r.pose.bones['RightHand'].matrix;q=hm.to_quaternion()@hand_offset.inverted()
    m=q.to_matrix().to_4x4();m.translation=hand_world(r,'Right')-q@grip;return m
def transform(pos,q=None,scale=1):
    return Matrix.Translation(Vector(pos)) @ ((q or Quaternion()).to_matrix().to_4x4()) @ Matrix.Scale(scale,4)
def kobject(o,f):
    for path in ['location','rotation_euler','scale']:o.keyframe_insert(data_path=path,frame=f)
def apply_props(r,pr,name,t):
    wm=weapon_matrix(r);q=wm.to_quaternion();opening=0;release=0
    hidden=transform((0,0,-5),scale=.00001)
    can=hidden.copy();card=hidden.copy();cylinder=hidden.copy()
    if name in ['Inspect1_Cylinder','Inspect3_Can']:
        opening=envelope(t,.16,.28,.78,.90)
    if name=='Inspect1_Cylinder' and .30<t<.73:
        u=max(0,min(1,(t-.30)/.22));home=wm@Vector((.07,-.20,0));held=hand_world(r,'Left')+Vector((0,-.03,.10))
        take=envelope(t,.30,.52,.63,.73)
        pos=home.lerp(held,take);pos.z+=.16*math.sin(math.pi*u)
        cylinder=transform(pos,Quaternion((0,1,0),2*math.pi*u))
    if name in ['Inspect2_Flip','RareDraw','SprintTwirl']:
        a,b=(.25,.72) if name!='SprintTwirl' else (.16,.82)
        u=max(0,min(1,(t-a)/(b-a)));release=math.sin(math.pi*u)**.6
        center=hand_world(r,'Right')
        center+=Vector((.05*math.sin(2*math.pi*u),-.045*release,.22*release if name!='SprintTwirl' else .08*release))
        rot=Quaternion((0,1,0),2*math.pi*u*(2 if name=='Inspect2_Flip' else 1))@q
        wm=transform(center-rot@grip,rot)
    if name=='Inspect3_Can':
        take=envelope(t,.28,.38,.72,.83)
        support=hand_world(r,'Left')
        lq=sword_q([.15,-.50,.85],.35)
        lm=transform(support-lq@Vector((0,-.02,0)),lq)
        wpos=wm.translation.lerp(lm.translation,take);wq=wm.to_quaternion().slerp(lq,take)
        wm=transform(wpos,wq)
        if .26<t<.85:
            home=wm@Vector((0,-.17,.055));held=hand_world(r,'Right')+Vector((0,-.035,.10))
            can=transform(home.lerp(held,take),Quaternion((1,0,0),-.3-.6*envelope(t,.56,.64,.66,.73)))
    if name=='InspectCards':
        show=envelope(t,.12,.23,.76,.88)
        wm.translation.z-=.65*show
        if show>.001:
            pos=hand_world(r,'Left')+Vector((-.015,-.015,.055))
            flip=0
            for a in [.37,.55]:flip+=math.pi*envelope(t,a,a+.04,a+.07,a+.11)
            card=transform(pos,Quaternion((0,0,1),-.15+flip),show)
    if name=='Holster':wm.translation.z-=.35*t*t
    if name in ['Draw','FirstDraw','RareDraw','SprintDraw']:wm.translation.z-=.30*(1-envelope(t,0,.20,1,1.01))
    matrices={'Weapon':wm,'Can':can,'Card':card,'Cylinder':cylinder}
    for side,sign in [('Left',-1),('Right',1)]:
        pivot=Vector((0,.08,sign*.022))
        local=Matrix.Translation(pivot+Vector((.018*opening,0,sign*.07*opening)))@Quaternion((0,1,0),sign*.55*opening).to_matrix().to_4x4()@Matrix.Translation(-pivot)
        matrices['Panel'+side]=wm@local
    for n in prop_names:
        pb=pr.pose.bones[n];pb.matrix=matrices[n];bpy.context.view_layer.update()
        pb.rotation_mode='QUATERNION'
        for path in ['location','rotation_quaternion','scale']:pb.keyframe_insert(data_path=path)
    for side in ['Right','Left']:
        ob=bpy.data.objects[r.name[:2]+'_'+side+'Arm_Geo'];val=release if side=='Right' else .15
        if name=='InspectCards':val=.75 if side=='Right' else .25
        if name=='Inspect4_Display' and side=='Left':val=.5
        ob.data.shape_keys.key_blocks['Open'].value=val;ob.data.shape_keys.key_blocks['Open'].keyframe_insert('value')
    return wm,opening,release

def camera(name,pos,target,lens):
    d=bpy.data.cameras.new(name);c=bpy.data.objects.new(name,d);scene.collection.objects.link(c);c.location=pos
    c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_start=.025;return c
fp_cam=camera('CAM_FirstPerson',(0,.30,1.40),(0,-1,1.22),18)
tp_cam=camera('CAM_ThirdPerson',(4.8,-3.5,1.95),(2.8,0,.87),45)
cam_base=fp_cam.rotation_euler.copy()
scene.camera=fp_cam
world=bpy.data.worlds.new('Impact_Studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.025,.042,.07,1);world.node_tree.nodes['Background'].inputs[1].default_value=.6;scene.world=world
for name,pos,power,size in [('Key',(-2,-3,4),850,4),('Fill',(3,-1,2.5),500,3),('Rim',(1,2,3),1100,3)]:
    d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;d.energy=power;d.shape='DISK';d.size=size;o.rotation_euler=(Vector((1,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
floor=cube('Preview_Ground_TP',(2.8,0,-.03),(4,4,.05),mat('Floor',(.025,.04,.055),.3,.5))
fx={}
for tag in ['FP','TP']:
    fx[tag]=[]
    for i in range(25):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1)
        ob=bpy.context.object;ob.name=tag+'_FX_Ember_'+str(i);ob.data.materials.append(orange);fx[tag].append(ob)
events={}
def event_list(name,count):
    out=[]
    def add(t,kind,power=1):out.append({'frame':1+round(t*(count-1)),'event':kind,'strength':power})
    if name.startswith('Attack') or name in ['JumpSlam','CrouchAttack']:
        add(.32,'whoosh');add(.51 if name=='JumpSlam' else .46 if name=='Attack3' else .39 if name=='CrouchAttack' else .49,'impact',1.5 if name in ['JumpSlam','Attack3'] else 1)
    if name in ['Inspect1_Cylinder','Inspect3_Can']:add(.21,'mechanism_open');add(.32,'ignition');add(.83,'mechanism_close')
    if name=='Inspect1_Cylinder':add(.68,'catch')
    if name=='Inspect3_Can':add(.38,'can_pull');add(.65,'can_tilt');add(.76,'can_return');add(.89,'ignition')
    if name in ['Inspect2_Flip','SprintTwirl','RareDraw']:add(.30,'whoosh');add(.72 if name!='SprintTwirl' else .82,'catch')
    if name=='InspectCards':
        for t in [.23,.40,.58,.83]:add(t,'card_flick',.5)
    return out
manifest={'fps':30,'source_skeleton_bones':original_names,'prop_bones':prop_names,'clips':[],'status':'Authored adaptation; OVERDARE runtime integration pending','weapon_credit':'Macuahuitl Aztec Sword by patovg9; CC-BY; source supplied in assets'}
actions={};all_anim=[]
for tag,r in [('FP',rig),('TP',tp)]:
    pr=prop_rigs[tag]
    targets=[r,pr]+[bpy.data.objects[tag+'_'+s+'Arm_Geo'].data.shape_keys for s in ['Right','Left']]+fx[tag]+([fp_cam] if tag=='FP' else [])
    all_anim+=targets
    for name,(count,keys) in clips.items():
        for target in targets:
            target.animation_data_create();ac=bpy.data.actions.new('MX3_'+tag+'_'+name+'__'+target.name);ac.use_fake_user=True;target.animation_data.action=ac
            actions[(target.name,name)]=ac
        evs=event_list(name,count);tip_history=[]
        for f in range(1,count+1):
            scene.frame_set(f);t=(f-1)/(count-1);p=sample(keys,t)
            support=(name in ['Inspect4_Display','FirstDraw'] or (name=='Inspect1_Cylinder' and t<.30)) and .12<t<.85
            if support:
                sq=p.get('_q',sword_q(p['d'],p['roll']));hq=sq@hand_offset
                origin=Vector(p['r'])+hq@grip_center-sq@grip
                lq=sq@Quaternion((0,1,0),math.pi)@hand_offset
                target=origin+sq@Vector((0,-.13,0))-lq@grip_center
                weight=envelope(t,.12,.22,.72,.85)
                p['l']=list(Vector(p['l']).lerp(target,weight))
            gait='RunLoop' if name in ['SprintTwirl','SprintDraw'] else name
            pose(r,p,gait,t,tag=='TP')
            if tag=='TP' and name in ['CrouchIn','CrouchIdle','CrouchOut','CrouchAttack','InspectCards','JumpSlam']:
                weight=t if name=='CrouchIn' else 1-t if name=='CrouchOut' else envelope(t,.02,.16,.84,1) if name=='InspectCards' else 1
                dz=-.20*weight
                if name=='JumpSlam':dz=.23*math.sin(math.pi*min(1,t/.55)) if t<.55 else -.15*envelope(t,.5,.56,.64,.95)
                shifted={b.name:b.matrix.copy() for b in r.pose.bones if 'Leg' not in b.name and 'Foot' not in b.name and b.name!='Root'}
                for n,m in shifted.items():
                    m.translation.z+=dz*100;r.pose.bones[n].matrix=m;bpy.context.view_layer.update()
                for side in ['Right','Left']:leg_pose(r,side,base[side+'Foot'].translation*.01+Vector((0,0,max(0,dz))),.025-dz)
                for b in r.pose.bones:
                    for path in ['location','rotation_quaternion','scale']:b.keyframe_insert(data_path=path)
            if support:
                lh=r.pose.bones['LeftHand'];old=lh.matrix.copy()
                desired=(r.pose.bones['RightHand'].matrix.to_quaternion()@hand_offset.inverted()@Quaternion((0,1,0),math.pi)@hand_offset)
                rot=old.to_quaternion().slerp(desired,weight);m=rot.to_matrix().to_4x4();m.translation=old.translation;lh.matrix=m;bpy.context.view_layer.update()
                r.pose.bones['LeftHand001'].matrix=m;bpy.context.view_layer.update()
                for bn in ['LeftHand','LeftHand001']:
                    for path in ['location','rotation_quaternion','scale']:r.pose.bones[bn].keyframe_insert(data_path=path)
            wm,opening,release=apply_props(r,pr,name,t)
            if tag=='FP':
                pulse=sum(e['strength']*math.exp(-(f-e['frame'])/3)*math.sin((f-e['frame'])*2) for e in evs if e['event'] in ['impact','catch','ignition'] and 0<=f-e['frame']<15)
                fp_cam.rotation_euler=cam_base.copy();fp_cam.rotation_euler.z+=p['body']*.20+pulse*.025;fp_cam.rotation_euler.x+=pulse*.016
                fp_cam.location=(.008*pulse,.30,1.4+.008*pulse);kobject(fp_cam,f)
            ignition=0
            for e in evs:
                if e['event'] in ['impact','catch','ignition']:
                    age=(f-e['frame'])/30
                    if 0<=age<.42:ignition=max(ignition,(1-age/.42)*e['strength'])
            tip=wm@Vector((0,-.44,0))+Vector((0 if tag=='FP' else 2.8,0,0))
            tip_history.append(tip.copy())
            for i,ob in enumerate(fx[tag]):
                if i>=18:
                    lag=i-18;idx=len(tip_history)-1-lag
                    active=name.startswith('Attack') or name in ['JumpSlam','CrouchAttack','Inspect2_Flip','RareDraw','SprintTwirl']
                    if active and idx>0:
                        a=tip_history[idx];b=tip_history[idx-1];length=(a-b).length
                        ob.location=(a+b)*.5;ob.rotation_euler=(a-b).to_track_quat('Z','Y').to_euler() if length>.0001 else (0,0,0)
                        width=.014*(1-lag/8) if length>.025 else .00001
                        ob.scale=(width,width,max(.00001,length*.6))
                    else:ob.scale=(.00001,)*3
                    kobject(ob,f);continue
                phase=((f*.17+i*.618)%1);ang=i*2.399+f*.12
                reach=phase*.19*ignition
                ob.location=tip+Vector((math.cos(ang)*reach,math.sin(ang)*reach,phase*.23*ignition))
                sz=max(.00001,ignition*(1-phase)*(.032 if i<6 else .010))
                ob.scale=(sz,sz,sz*(2.5 if i<6 else 1));kobject(ob,f)
        for target in targets:target.animation_data.action=None
        if tag=='FP':
            manifest['clips'].append({'name':name,'frames':count,'duration':(count-1)/30,'loop':name in ['Idle','RunLoop','BlockHold','CrouchIdle'],'events':evs});events[name]=evs
        print('BAKED',tag,name,flush=True)
# Per-object synchronized tracks give a scrub-ready, editable master timeline.
cursor=1
for name,(count,_) in clips.items():
    scene.timeline_markers.new(name,frame=cursor)
    for target in all_anim:
        track=target.animation_data.nla_tracks.new();track.name=name
        strip=track.strips.new(name,cursor,actions[(target.name,name)]);strip.extrapolation='HOLD_FORWARD';strip.blend_type='REPLACE'
    for entry in manifest['clips']:
        if entry['name']==name:entry['timeline_start']=cursor
    cursor+=count+5
scene.frame_start=1;scene.frame_end=cursor-5
scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
floor.hide_render=True
for ob in scene.objects:
    if ob.name.startswith('TP_'):ob.hide_render=True
scene.frame_set(next(c['timeline_start']+110 for c in manifest['clips'] if c['name']=='Inspect3_Can'))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Macuahuitl_v03_Expanded.blend'))
(OUT/'animation_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
(OUT/'events.json').write_text(json.dumps(events,indent=2),encoding='utf-8')
print('V03_BUILT',len(clips),len(actions),flush=True)
