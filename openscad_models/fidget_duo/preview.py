from pathlib import Path
import json,math
import numpy as np,trimesh
from trimesh.exchange.threemf import export_3MF
from pxr import Usd,UsdGeom,UsdShade,UsdUtils,Sdf,Gf,Vt
R=Path(__file__).resolve().parent;W=R/'work';scenes={}
for n in ['gecko','gecko_coupon','mushroom_base','mushroom_cap','switch_coupon','stem_coupon']:
 m=trimesh.load(R/(n+'.stl'));p=R/(n+'.3mf');p.write_bytes(export_3MF(trimesh.Scene(m)));assert np.allclose(trimesh.load(p).bounds,m.bounds,atol=.001)
def entry(n,m,rgb):
 m.export(W/(n+'_view.stl'));return {'name':n,'rgb':rgb}
gecko=[];T=np.eye(4)
for i,n in enumerate(['gecko_head']+[f'segment_{j}' for j in range(6)]):
 m=trimesh.load(W/(n+'.stl'))
 if i:
  pivot=[18+26*(i-1),0,4];rot=trimesh.transformations.rotation_matrix(math.radians(6),[0,0,1],pivot);T=T@rot
 m.apply_transform(T);gecko.append(entry(n,m,[.12,.43,.38]))
scenes['Pebble_Gecko']=gecko
base=trimesh.load(R/'mushroom_base.stl');base.apply_translation([0,0,-26]);base.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0]));cap=trimesh.load(R/'mushroom_cap.stl');cap.apply_translation([0,0,27.7])
hardware=trimesh.creation.box([13.9,13.9,8]);hardware.apply_translation([0,0,25]);stem=trimesh.creation.box([4,1.2,3.6]);stem.apply_translation([0,0,30.8]);hardware=trimesh.util.concatenate([hardware,stem])
scenes['Mushroom_Pop']=[entry('mushroom_base',base,[.88,.83,.70]),entry('mushroom_cap',cap,[.68,.23,.13]),entry('purchased_switch_reference',hardware,[.045,.05,.05])]
for title,items in scenes.items():
 stage=Usd.Stage.CreateNew(str(W/(title+'.usda')));UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z);UsdGeom.SetStageMetersPerUnit(stage,.001)
 root=UsdGeom.Xform.Define(stage,'/Model');stage.SetDefaultPrim(root.GetPrim())
 for item in items:
  name=item['name'];m=trimesh.load(W/(name+'_view.stl'));rgb=item['rgb'];p=UsdGeom.Mesh.Define(stage,'/Model/'+name)
  p.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(m.vertices.astype(np.float32)));p.CreateFaceVertexCountsAttr([3]*len(m.faces));p.CreateFaceVertexIndicesAttr(m.faces.flatten().tolist());p.CreateSubdivisionSchemeAttr('none');p.CreateNormalsAttr(Vt.Vec3fArray.FromNumpy(m.vertex_normals.astype(np.float32)));p.SetNormalsInterpolation('vertex')
  mat=UsdShade.Material.Define(stage,'/Model/Materials/'+name);s=UsdShade.Shader.Define(stage,str(mat.GetPath())+'/Surface');s.CreateIdAttr('UsdPreviewSurface');s.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*rgb));s.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.6);mat.CreateSurfaceOutput().ConnectToSource(s.ConnectableAPI(),'surface');UsdShade.MaterialBindingAPI.Apply(p.GetPrim()).Bind(mat)
 stage.GetRootLayer().Save();assert UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(stage.GetRootLayer().identifier),str(R/(title+'_Phone_View.usdz')));assert Usd.Stage.Open(str(R/(title+'_Phone_View.usdz')))
(W/'scenes.json').write_text(json.dumps(scenes));print('Six 3MF and two USDZ previews verified.')
