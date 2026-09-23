import bpy
r=bpy.data.objects['FP_ODA_Rig']
for tr in r.animation_data.nla_tracks: tr.mute=True
r.animation_data.action=bpy.data.actions['MX_FP_RunLoop']
poses=[]
for f in [1,25]:
 bpy.context.scene.frame_set(f); poses.append({b.name:b.matrix.copy() for b in r.pose.bones})
for n in poses[0]:
 e=max(abs(poses[0][n][i][j]-poses[1][n][i][j]) for i in range(4) for j in range(4))
 if e>.001: print(n,e,list(poses[0][n].translation),list(poses[1][n].translation))
