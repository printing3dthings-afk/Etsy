#!/bin/sh
# Rebuild the technique samplers (2026-11-14). See FACTS.md and
# data/knowledge_base/fdm_only_techniques.md. Run from the repo root.
set -e
D=openscad_models/technique_samplers
python3 - <<'PY'
import manifold3d as m3d, trimesh
D = "openscad_models/technique_samplers/parts"
trimesh.creation.cylinder(radius=10, height=15, sections=96).apply_translation([0, 0, 7.5]).export(f"{D}/texture_swatch.stl")
cyl = m3d.Manifold.cylinder(30, 20, 20, 128)
ribbed = cyl
for k in range(6):   # six radial slits, 0.001 mm wide, rim to r 4: each becomes a double-wall rib
    ribbed = ribbed - m3d.Manifold.cube([16, 0.001, 30.2]).translate([4, -0.0005, -0.1]).rotate([0, 0, 60 * k])
for name, m in (("vase_plain", cyl), ("vase_ribbed", ribbed)):
    g = m.to_mesh()
    trimesh.Trimesh(g.vert_properties[:, :3], g.tri_verts).export(f"{D}/{name}.stl")
PY
S=$D/parts/texture_swatch.stl:#B08A5A
# one depth, point spacing and scale for all three, so only the noise differs: 0.3 deep (the
# most a wall that carries load should get), 0.6 apart, scale 3
python3 tools/bambu_slice.py $S + $S + $S + $S -o $D/texture_sampler.gcode.3mf \
  --set fuzzy_skin_thickness=0.3 --set fuzzy_skin_point_distance=0.6 --set fuzzy_skin_scale=3 \
  --object-set 2:fuzzy_skin=external --object-set 2:fuzzy_skin_noise_type=classic \
  --object-set 3:fuzzy_skin=external --object-set 3:fuzzy_skin_noise_type=perlin \
  --object-set 4:fuzzy_skin=external --object-set 4:fuzzy_skin_noise_type=voronoi
for v in vase_ribbed vase_plain; do
  python3 tools/bambu_slice.py $D/parts/$v.stl:#7FB3C8 -o $D/$v.gcode.3mf \
    --set spiral_mode=1 --set slice_closing_radius=0 --set bottom_shell_layers=4 --set outer_wall_line_width=0.6
done
