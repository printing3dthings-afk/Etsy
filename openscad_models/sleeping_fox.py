# Sleeping Fox -- curled, tail wrapped around, head tucked onto its own paws.
#
# THIS is the shape Blender should be asked for. Not "organic-looking" -- there
# is no describable swept, lofted or revolved profile anywhere in it, and the
# tail wrapping around the body and merging back into it is a topology CSG has
# to fake with a convex hull. Everything the form needs is what a voxel union
# plus a light smooth does natively: SOFT CONCAVE BLENDS everywhere two masses
# meet. A curled animal is nothing but those blends.
#
# Every step here is one this session already proved: bake -> join_all -> ONE
# voxel remesh to union with no Boolean modifier -> LAPLACIANSMOOTH with
# volume preservation -> decimate before the CGAL handoff. The flat base is a
# dimensioned cut and goes to OpenSCAD.
import bpy, mathutils, math

P = PARAMS
S = P.get("scale", 1.0)

def blob(p, r, sc=(1,1,1), rot=(0,0,0)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r*S, segments=44, ring_count=22,
                                         location=(p[0]*S, p[1]*S, p[2]*S))
    o = bpy.context.active_object
    o.scale = sc; o.rotation_euler = rot
    return bake(o)

parts = []
# ---- body: a fat comma, curled ----
parts.append(blob((0, 0, 26), 30, (1.10, 1.02, 0.78)))
parts.append(blob((-6, -16, 22), 24, (1.05, 1.0, 0.72)))

# ---- tail: sweeps out from the rump and wraps around the FRONT, ending
# beside the nose. The wrap is the point -- it comes back and merges into the
# body, which is where a hull() would bridge straight across instead.
tail = [(-26,-24,16,11.5), (-38,-8,15,10.5), (-40, 14,14,10.0),
        (-30, 30,13, 9.5), (-12, 38,13, 9.0), (  8, 36,13, 8.5),
        ( 24, 26,13, 8.0)]
for i in range(len(tail)-1):
    a, b = tail[i], tail[i+1]
    for k in range(6):
        t = k/6
        parts.append(blob(tuple(a[j]+(b[j]-a[j])*t for j in range(3)),
                          a[3]+(b[3]-a[3])*t))
parts.append(blob(tail[-1][:3], tail[-1][3]*1.15))          # the poof at the tip

# ---- head, tucked down and forward onto the curl ----
head_c = (10, 14, 34)
parts.append(blob(head_c, 19, (1.0, 0.95, 0.90)))
parts.append(blob((12, 27, 28), 10, (0.9, 1.25, 0.75)))     # muzzle, laid down
for sx in (1, -1):                                           # ears, folded back
    parts.append(blob((head_c[0]+sx*11, head_c[1]-5, head_c[2]+13), 7,
                      (0.55, 1.0, 1.15), (math.radians(-25), 0, math.radians(sx*22))))
# ---- front paws under the chin ----
for sx in (1, -1):
    parts.append(blob((10+sx*9, 30, 15), 7.5, (1.0, 1.25, 0.7)))

fox = join_all(parts, "sleepfox")
rm = fox.modifiers.new("rem", 'REMESH'); rm.mode='VOXEL'
rm.voxel_size = P.get("voxel", 0.8)
ls = fox.modifiers.new("lap", 'LAPLACIANSMOOTH')
ls.lambda_factor = P.get("lap", 0.14); ls.iterations = P.get("lap_iters", 4)
ls.use_volume_preserve = True
dec = fox.modifiers.new("dec", 'DECIMATE'); dec.ratio = P.get("dec", 0.35)
apply_all(fox)
print("PROBE tris:", len(fox.data.polygons), "dims:", [round(v,1) for v in fox.dimensions])
