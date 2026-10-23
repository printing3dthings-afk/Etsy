# Chomp — OnBrandCraftz visual design review

Actual 3D geometry based on Scott's selection of character concept 3. Coral rounded body, domed eyes, navy continuous tongue with cable notch and retaining lips, sculpted feet and integrated tall rear pocket. Approved OBC SVG recessed into the left foot underside.

This is a DESIGN REVIEW, not a released print package. The phone USDZ and front/rear PNG images show the actual modeled geometry. Chomp_Design.blend is the editable Blender master. Geometry_Report.json records individual mesh checks only. Parts currently overlap at assembly joints. Eye/glint manufacturing, clearances, actual phone seating, print orientation, supports and stability have not been engineered or validated. Do not print or sell this as a tested product.

Rebuild using Blender 4.4 Python: run OpenSCAD on chomp_work/brand.scad to create chomp_work/brand.stl, then run chomp_work/build.py with bpy available. Run chomp_work/preview.py using Python with trimesh, numpy and usd-core. Keep OBC.svg at the workspace root. Scripts resolve paths relative to their location and output into Chomp/.

Preview cleanup removes a detached zero-volume, two-triangle boolean artifact without changing the solid body. The Blender master retains the original boolean result. The next engineering pass should reconcile the master and exported geometry, create mating joints and validate the slicer before producing print files.
