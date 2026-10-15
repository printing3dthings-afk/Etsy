from pathlib import Path
import json,numpy as np,trimesh
from pxr import Usd,UsdGeom,UsdShade,UsdUtils,Sdf,Gf,Vt
R=Path(__file__).resolve().parent.parent;O=R/'Chomp'
stage=Usd.Stage.CreateNew(str(R/'chomp_work/Chomp.usda'));UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z);UsdGeom.SetStageMetersPerUnit(stage,.001)
root=UsdGeom.Xform.Define(stage,'/Chomp');stage.SetDefaultPrim(root.GetPrim());report={}
for item in json.loads((O/'scene.json').read_text()):
 name=item['name'];rgb=item['rgb'];m=trimesh.load(O/(name+'.stl'))
 # Discard detached zero-volume boolean debris, preserving the complete solid.
 pieces=[c for c in m.split(only_watertight=False) if abs(c.volume)>0.001]
 m=trimesh.util.concatenate(pieces);m.export(O/(name+'.stl'))
 report[name]={'watertight':bool(m.is_watertight),'winding_consistent':bool(m.is_winding_consistent),'volume_mm3':float(m.volume)}
 name=name.replace('-','minus');p=UsdGeom.Mesh.Define(stage,'/Chomp/'+name);p.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(m.vertices.astype(np.float32)));p.CreateFaceVertexCountsAttr([3]*len(m.faces));p.CreateFaceVertexIndicesAttr(m.faces.flatten().tolist());p.CreateSubdivisionSchemeAttr('none')
 normals=m.vertex_normals.astype(np.float32);p.CreateNormalsAttr(Vt.Vec3fArray.FromNumpy(normals));p.SetNormalsInterpolation('vertex')
 mat=UsdShade.Material.Define(stage,'/Chomp/Materials/'+name);s=UsdShade.Shader.Define(stage,str(mat.GetPath())+'/Surface');s.CreateIdAttr('UsdPreviewSurface');s.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*rgb));s.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.55);mat.CreateSurfaceOutput().ConnectToSource(s.ConnectableAPI(),'surface');UsdShade.MaterialBindingAPI.Apply(p.GetPrim()).Bind(mat)
stage.GetRootLayer().Save();assert UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(stage.GetRootLayer().identifier),str(O/'Chomp_Phone_View.usdz'));assert Usd.Stage.Open(str(O/'Chomp_Phone_View.usdz'))
(O/'Geometry_Report.json').write_text(json.dumps(report,indent=2));print(report)
