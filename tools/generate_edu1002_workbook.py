"""
generate_edu1002_workbook.py — EDU1002, Kawaii Interactive Tracing Workbook
for Kids (Truck Zone theme).

Boys-appealing Cars/Trucks/Diggers sibling of EDU1001, built 2026-08-20 on
the same shared engine (generate_tracing_workbook.py) after Scott asked for
a boys-themed version alongside a request for an older-kids step-up (see
generate_edu1003_workbook.py). Same 71-page structure/content TYPES
(letters, numbers, shapes, sight words, math, reward chart, practice) --
only the theme, palette, and letter/count/fill-in wording differ from
EDU1001. See generate_tracing_workbook.py's module docstring for the shared
engine's real differentiator (genuine dashed-outline font-glyph tracing,
not a static coloring page) -- that differentiator applies here unchanged.

New palette, not a reuse of an existing CLAUDE.md catalog theme (Scott's
choice) -- "Truck Zone": safety orange + steel blue read as energetic and
vehicle/construction-coded without leaning on a tired plain-blue "boys"
cliche. Documented as Theme 13 in CLAUDE.md's Color Design System catalog
for future reuse.

Run standalone:
    python tools/generate_edu1002_workbook.py
"""
import sys
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.generate_tracing_workbook import build_tracing_workbook

EDU1002 = {
    "title": "Kawaii Tracing Workbook",
    "subtitle": "Truck Zone",
    "year": None,
    "theme": (1.0, 0.4196, 0.2078),      # #FF6B35 safety orange
    "accent": (0.1804, 0.3608, 0.5412),  # #2E5C8A steel blue
    "bg": (1.0, 0.9725, 0.9412),         # #FFF8F0 warm cream
    "dark": (0.1020, 0.1451, 0.1882),    # #1A2530 deep asphalt navy
    "sections": [
        "Welcome & Setup", "Dashboard / Home", "Workbook Index",
        "For Parents & Teachers",
        "Letter Tracing A-Z × 26", "Number Tracing 1-20 × 20",
        "Shape Tracing × 8", "Sight Words × 5",
        "Coloring & Counting Math × 4", "Reward Chart",
        "Practice Pages × 2",
    ],
    # Real vehicle/construction nouns, not invented -- same accuracy standard
    # as EDU1001's Dolch sight words. A few letters (N, X, Y) don't have a
    # clean single vehicle noun -- Nut/X-ray Truck/Yard are genuine real
    # words loosely in the garage/construction-site world rather than a
    # forced or made-up term, matching how EDU1001 also breaks theme for X
    # (Xylophone) since no alphabet set gets every letter "on theme."
    "letter_words": {
        "A": "Ambulance", "B": "Bulldozer", "C": "Crane", "D": "Digger",
        "E": "Excavator", "F": "Fire Truck", "G": "Garage", "H": "Helicopter",
        "I": "Ice Cream Truck", "J": "Jeep", "K": "Kart", "L": "Loader",
        "M": "Motorcycle", "N": "Nut", "O": "Off-Roader", "P": "Pickup Truck",
        "Q": "Quad", "R": "Racer", "S": "School Bus", "T": "Tow Truck",
        "U": "Utility Truck", "V": "Van", "W": "Wrecker", "X": "X-ray Truck",
        "Y": "Yard", "Z": "Zamboni",
    },
    "count_noun": "tire",
    "math_fill_noun_plural": "tires",
    "shape_examples": {
        "Circle": "a tire, a steering wheel, or a traffic light",
        "Square": "a toolbox, a window, or a road sign",
        "Triangle": "a caution sign, a crane's arm, or a traffic cone",
        "Rectangle": "a license plate, a truck bed, or a garage door",
        "Star": "a sheriff's badge, a shining headlight, or a shooting star",
        "Heart": "a bumper sticker, a keychain charm, or a love note",
        "Oval": "a racetrack, a headlight, or a football",
        "Diamond": "a road sign, a kite, or a baseball field",
    },
}


def main():
    path = build_tracing_workbook(
        pid="EDU1002",
        pcfg=EDU1002,
        cover_img_name="EDU1002_kids_tracing_truck_zone.png",
    )
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(path))
        print(f"EDU1002: {len(reader.pages)} pages, {path.stat().st_size / 1024:.0f} KB -> {path}")
    except Exception as e:
        print(f"EDU1002 saved to {path} (stats unavailable: {e})")


if __name__ == "__main__":
    main()
