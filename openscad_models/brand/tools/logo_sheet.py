"""Build OBC marks from obc_logo_options.scad (1-5) and obc_logo_options_2.scad
(6-10), measure each as an engraving (what a 0.42 mm bead can cut, and what
walls between cuts survive), and draw a comparison sheet.

    logo_sheet.py out.png [designs]        e.g. 6,7,8,9,10
    logo_sheet.py x measure 6,7"""
import json, subprocess, tempfile, sys
from pathlib import Path
import numpy as np, trimesh
from scipy import ndimage
from shapely import contains_xy
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/home/user/Etsy")
SCAD = ROOT / "openscad_models/brand/obc_logo_options.scad"
SCAD2 = ROOT / "openscad_models/brand/obc_logo_options_2.scad"
OUT = Path(sys.argv[1])
BEAD = 0.42
NAMES = {1: "Maker's Stamp", 2: "Scallop Badge", 3: "Ribbon", 4: "Happy O", 5: "Toolpath",
         6: "Heart O", 7: "Smile", 8: "Tiles", 9: "Cat O", 10: "Sparkle"}
BLURB = {1: "Heavy sans in a rounded frame,\nlike a potter's stamp.",
         2: "Rounded letters in a scalloped badge,\nlike a sticker.",
         3: "OBC knocked out of a ribbon banner,\nthe letters left standing.",
         4: "A round O with a kawaii face,\nthen BC.",
         5: "One even line with round ends,\nthe way the nozzle draws it.",
         6: "A clean wordmark whose O\nhides a heart.",
         7: "The word with a gentle smile\nunderneath.",
         8: "Letters knocked out of tiles,\na star in the fourth.",
         9: "A clean wordmark; the O\nwears two cat ears.",
         10: "A clean wordmark with a\nsparkle at the C's shoulder."}
# the playful detail's second colour, for screens only; never engraved
ACCENT = {6: (236, 112, 146), 7: (238, 122, 88), 8: (238, 122, 88), 9: (236, 140, 170), 10: (232, 170, 60)}

def polys(d, part="engrave"):
    with tempfile.TemporaryDirectory() as td:
        stl = Path(td) / "l.stl"
        r = subprocess.run(["openscad", "-D", f"design={d}", "-D", f'part="{part}"', "-o", str(stl),
                            str(SCAD2 if d >= 6 else SCAD)], capture_output=True, text=True)
        m = trimesh.load(str(stl), force="mesh")
    sec = m.section(plane_origin=[0, 0, 1], plane_normal=[0, 0, 1])
    # to_2D(np.eye(4)) keeps the world XY frame: left to choose, trimesh puts
    # every section in its own frame and an accent drawn over the word lands
    # beside the part it belongs to
    return sec.to_2D(to_2D=np.eye(4))[0].polygons_full

def raster(ps, px, pad):
    b = np.array([p.bounds for p in ps]); mn = b[:, :2].min(0) - pad; mx = b[:, 2:].max(0) + pad
    w, h = int((mx[0] - mn[0]) / px), int((mx[1] - mn[1]) / px)
    ys, xs = np.mgrid[0:h, 0:w]
    X, Y = mn[0] + xs * px, mx[1] - ys * px
    g = np.zeros((h, w), bool)
    for p in ps: g |= contains_xy(p, X, Y)
    return g, mn, mx

def opening(g, px):
    dt = ndimage.distance_transform_edt(g) * px
    core = dt >= BEAD / 2
    reach = ndimage.distance_transform_edt(~core) * px
    return g & (reach <= BEAD / 2), dt

def measure(d):
    ps = polys(d); px = 0.01
    g, mn, mx = raster(ps, px, 1.0)
    mn, mx = mn + 1.0, mx - 1.0
    kept, dt = opening(g, px)
    cut_lost = g & ~kept
    # walls: the plastic left between cuts, on a canvas padded 1 mm, so open
    # space round the mark counts as wide and only a narrow neck is lost
    wall = ~g
    wkept, _ = opening(wall, px)
    wall_lost = wall & ~wkept
    ridge = (dt == ndimage.maximum_filter(dt, size=3)) & (dt > 0)
    typ = 2 * np.median(dt[ridge])
    return dict(d=d, size=(round(mx[0] - mn[0], 1), round(mx[1] - mn[1], 1)),
                cut_lost_mm2=round(cut_lost.sum() * px * px, 3), cut_area=round(g.sum() * px * px, 1),
                wall_lost_mm2=round(wall_lost.sum() * px * px, 3), typ_beads=round(typ / BEAD, 2)), ps, (g, kept, cut_lost, wall_lost)

INK = (58, 40, 74); CREAM = (250, 246, 240); LAV = (196, 178, 222); MUTE = (120, 110, 130); RED = (214, 64, 64)
def font(sz, bold=False):
    f = ROOT / ("assets/fonts/Poppins-SemiBold.ttf" if bold else "assets/fonts/Poppins-Regular.ttf")
    return ImageFont.truetype(str(f), sz)

def draw_mark(ps, box, colour, bg=None, circle=False, fit=0.72, acc=None, acc_colour=None):
    W, H = box
    img = Image.new("RGB", box, bg or CREAM)
    dr = ImageDraw.Draw(img)
    if circle:
        dr.ellipse([0, 0, W - 1, H - 1], fill=LAV)
    b = np.array([p.bounds for p in ps]); mn = b[:, :2].min(0); mx = b[:, 2:].max(0)
    s = fit * min(W / (mx[0] - mn[0]), H / (mx[1] - mn[1]))
    cx, cy = (mn + mx) / 2
    hi = Image.new("L", (W * 3, H * 3), 0); hd = ImageDraw.Draw(hi)
    def tf(pts): return [(3 * (W / 2 + (x - cx) * s), 3 * (H / 2 - (y - cy) * s)) for x, y in pts]
    for p in ps:
        hd.polygon(tf(p.exterior.coords), fill=255)
        for i in p.interiors: hd.polygon(tf(i.coords), fill=0)
    m = hi.resize((W, H), Image.LANCZOS)
    img.paste(Image.new("RGB", box, colour), (0, 0), m)
    if acc:
        ha = Image.new("L", (W * 3, H * 3), 0); hd = ImageDraw.Draw(ha)
        for p in acc:
            hd.polygon(tf(p.exterior.coords), fill=255)
            for i in p.interiors: hd.polygon(tf(i.coords), fill=0)
        img.paste(Image.new("RGB", box, acc_colour), (0, 0), ha.resize((W, H), Image.LANCZOS))
    return img

def engraved_view(masks, box):
    g, kept, cut_lost, wall_lost = masks
    h, w = g.shape
    rgb = np.zeros((h, w, 3), np.uint8); rgb[:] = (226, 222, 216)          # the plastic
    rgb[kept] = (120, 112, 104)                                            # cut, printed
    rgb[cut_lost] = RED; rgb[ndimage.binary_dilation(wall_lost, iterations=3)] = RED
    im = Image.fromarray(rgb)
    im.thumbnail(box, Image.LANCZOS)
    out = Image.new("RGB", box, (226, 222, 216)); out.paste(im, ((box[0] - im.width) // 2, (box[1] - im.height) // 2))
    return out

if len(sys.argv) > 2 and sys.argv[2] == "measure":
    for d in [int(x) for x in sys.argv[3].split(",")]:
        print(measure(d)[0])
    sys.exit()
COL, MARGIN = 520, 40
DESIGNS = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [1, 2, 3, 4, 5]
rows = []
res = []
for d in DESIGNS:
    m, ps, masks = measure(d); res.append(m)
    rows.append((d, ps, polys(d, "accent") if d in ACCENT else None, masks, m))
H = 1500
sheet = Image.new("RGB", (MARGIN * 2 + COL * 5, H), CREAM)
sd = ImageDraw.Draw(sheet)
sd.text((MARGIN, 30), "OBC — five marks" if DESIGNS[0] == 1 else "OBC — five more: professional, with one fun detail", font=font(46, True), fill=INK)
sd.text((MARGIN, 92), "Each is drawn once in OpenSCAD: the logo you see is the cutter the printer gets. Bottom row: the mark as engraved 0.8 mm into a print at its real size, magnified; red would be anything a 0.4 mm nozzle could not make.",
        font=font(20), fill=MUTE)
for i, (d, ps, acc, masks, m) in enumerate(rows):
    x = MARGIN + i * COL
    ac = ACCENT.get(d)
    sd.text((x + 10, 160), f"{d}  {NAMES[d]}", font=font(30, True), fill=INK)
    sd.multiline_text((x + 10, 205), BLURB[d], font=font(19), fill=MUTE, spacing=4)
    sheet.paste(draw_mark(ps, (COL - 30, 420), INK, acc=acc, acc_colour=ac), (x + 5, 280))
    ic = draw_mark(ps, (230, 230), (255, 255, 255), bg=CREAM, circle=True, fit=0.62, acc=acc, acc_colour=ac)
    sheet.paste(ic, (x + 10, 730))
    sheet.paste(draw_mark(ps, (230, 230), (255, 255, 255), bg=INK, fit=0.7, acc=acc, acc_colour=ac), (x + 260, 730))
    sd.text((x + 10, 968), "shop icon", font=font(17), fill=MUTE); sd.text((x + 260, 968), "on dark", font=font(17), fill=MUTE)
    sheet.paste(engraved_view(masks, (COL - 30, 300)), (x + 5, 1010))
    ok = m["cut_lost_mm2"] < 0.1 and m["wall_lost_mm2"] < 0.1
    v = "prints clean" if ok else "loses detail"
    sd.text((x + 10, 1325), f"smallest: {m['size'][0]} × {m['size'][1]} mm · {v}", font=font(19, True), fill=INK if ok else RED)
    sd.text((x + 10, 1355), f"strokes {m['typ_beads']} beads typical · lost {m['cut_lost_mm2']} mm² cut, {m['wall_lost_mm2']} mm² wall",
            font=font(16), fill=MUTE)
sd.text((MARGIN, 1420), "Smallest = the size measured here; any larger prints too, any smaller has not been checked. For comparison, today's mark (OBC in Montserrat Black, 17.6 × 5.1 mm) measures clean the same way.",
        font=font(19), fill=MUTE)
sheet.save(OUT)
print(json.dumps(res, indent=1))
