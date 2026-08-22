#!/usr/bin/env python3
"""
3D CAD Model & STL Generation Tool for Frank
Allows programmatic generation of custom 3D printable STL models (name keychains, custom containers, 3D text)
using SolidPython2 and Trimesh.
"""

import os
import sys
import trimesh
from solid2 import cube, sphere, cylinder, text, linear_extrude, rotate, translate

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "3d_models")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_keychain(name_text="Frank 3D", font_size=12, height=4):
    """Generate a custom personalized 3D keychain STL."""
    print(f"--> Generating 3D Keychain for: '{name_text}'...")
    
    # 1. Base plate
    length = len(name_text) * font_size * 0.7 + 25
    base = translate([-5, -5, 0])(cube([length, font_size * 1.5, height]))
    
    # 2. Keyring hole
    hole = translate([-2, font_size * 0.25, -1])(cylinder(r=3, h=height + 2))
    base_with_hole = base - hole
    
    # 3. 3D Text
    txt = linear_extrude(height=height + 2)(text(name_text, size=font_size))
    model = base_with_hole + txt
    
    scad_file = os.path.join(OUTPUT_DIR, f"keychain_{name_text.replace(' ', '_')}.scad")
    stl_file = os.path.join(OUTPUT_DIR, f"keychain_{name_text.replace(' ', '_')}.stl")
    
    model.save_as_scad(scad_file)
    print(f"✓ SCAD saved: {scad_file}")
    return scad_file

def inspect_stl(stl_path):
    """Inspect 3D STL mesh dimensions, volume, and printability."""
    if not os.path.exists(stl_path):
        print(f"❌ File not found: {stl_path}")
        return
    mesh = trimesh.load(stl_path)
    print(f"\n📦 STL Mesh Analysis: {os.path.basename(stl_path)}")
    print(f"  - Is Watertight (Manifold): {mesh.is_watertight}")
    print(f"  - Bounding Box Dimensions (mm): {mesh.extents}")
    print(f"  - Volume (cm3): {mesh.volume / 1000.0:.2f}")
    print(f"  - Surface Area (cm2): {mesh.area / 100.0:.2f}")

if __name__ == "__main__":
    text_param = sys.argv[1] if len(sys.argv) > 1 else "OnBrandCraftz"
    generate_keychain(text_param)
