#!/usr/bin/env python3
"""Fix and upgrade all 10 faith SVG files with mixed typography."""
import os, math, cairosvg

SVG_DIR = "/home/user/Etsy/data/faith_pack/SVG"
PREVIEW_DIR = "/home/user/Etsy/data/faith_pack/previews"
os.makedirs(PREVIEW_DIR, exist_ok=True)

RECT_TAG = '  <rect width="800" height="800" fill="none"/>'

FONT_STYLE = '''    <style>
      @font-face { font-family: 'DancingScript'; src: url('/usr/local/share/fonts/DancingScript-Bold.ttf'); }
      @font-face { font-family: 'Oswald'; src: url('/usr/local/share/fonts/Oswald-Bold.ttf'); }
      @font-face { font-family: 'Playfair'; src: url('/usr/local/share/fonts/PlayfairDisplay-Bold.ttf'); }
      @font-face { font-family: 'PlayfairItalic'; src: url('/usr/local/share/fonts/PlayfairDisplay-Italic.ttf'); }
    </style>'''

def add_fonts(svg):
    if '<defs>' in svg:
        return svg.replace('<defs>\n', '<defs>\n' + FONT_STYLE + '\n', 1)
    font_block = f'  <defs>\n{FONT_STYLE}\n  </defs>'
    return svg.replace(RECT_TAG, RECT_TAG + '\n' + font_block)

def read_svg(name):
    with open(os.path.join(SVG_DIR, name)) as f:
        return f.read()

def write_svg(name, content):
    with open(os.path.join(SVG_DIR, name), 'w') as f:
        f.write(content)
    print(f"  Written: {name}")

def render(name):
    svg_path = os.path.join(SVG_DIR, name)
    out_path = os.path.join(PREVIEW_DIR, name.replace('.svg', '.png'))
    cairosvg.svg2png(url=svg_path, write_to=out_path, output_width=1200, output_height=1200)
    print(f"  Preview: {name.replace('.svg', '.png')}")

# ── FAITH 01: BE STILL ─────────────────────────────────────────────────────────
def fix_01():
    svg = add_fonts(read_svg('faith_01_be_still.svg'))
    old = ('  <line x1="310" y1="470" x2="490" y2="470" stroke="black" stroke-width="1.5"/>\n'
           '  <line x1="310" y1="490" x2="490" y2="490" stroke="black" stroke-width="1.5"/>\n'
           '  <text x="400" y="460" text-anchor="middle" font-family="Georgia, serif"\n'
           '        font-size="52" font-weight="bold" fill="black" letter-spacing="4">BE STILL</text>\n'
           '  <text x="400" y="505" text-anchor="middle" font-family="Georgia, serif"\n'
           '        font-size="18" fill="black" letter-spacing="6">AND KNOW THAT I AM GOD</text>\n'
           '  <text x="400" y="535" text-anchor="middle" font-family="Georgia, serif"\n'
           '        font-size="14" fill="black" letter-spacing="3">PSALM 46:10</text>')
    new = ('  <text x="400" y="458" text-anchor="middle" font-family="Oswald, Georgia, serif"\n'
           '        font-size="58" fill="black" letter-spacing="3">BE STILL</text>\n'
           '  <line x1="318" y1="469" x2="482" y2="469" stroke="black" stroke-width="1.5"/>\n'
           '  <text x="400" y="493" text-anchor="middle" font-family="DancingScript, cursive"\n'
           '        font-size="27" fill="black">and know that</text>\n'
           '  <text x="400" y="524" text-anchor="middle" font-family="Oswald, Georgia, serif"\n'
           '        font-size="30" fill="black" letter-spacing="2">I AM GOD</text>\n'
           '  <line x1="332" y1="534" x2="468" y2="534" stroke="black" stroke-width="1"/>\n'
           '  <text x="400" y="551" text-anchor="middle" font-family="PlayfairItalic, Georgia, serif"\n'
           '        font-size="13" fill="black" letter-spacing="3">PSALM 46:10</text>')
    assert old in svg, "faith_01 text block not found"
    write_svg('faith_01_be_still.svg', svg.replace(old, new))

# ── FAITH 02: FAITH OVER FEAR ──────────────────────────────────────────────────
def fix_02():
    svg = add_fonts(read_svg('faith_02_faith_over_fear.svg'))
    svg = svg.replace('fill="black" opacity="0.12"', 'fill="black" opacity="0.3"')
    svg = svg.replace('fill="black" opacity="0.08"', 'fill="black" opacity="0.2"')
    svg = svg.replace(
        '<text x="400" y="325" text-anchor="middle" font-family="Georgia, serif" font-size="44" font-weight="bold" fill="white" letter-spacing="6">FAITH</text>',
        '<text x="400" y="327" text-anchor="middle" font-family="Oswald, Georgia, serif" font-size="50" fill="white" letter-spacing="8">FAITH</text>')
    svg = svg.replace(
        '<text x="400" y="515" text-anchor="middle" font-family="Georgia, serif" font-size="44" font-weight="bold" fill="white" letter-spacing="6">FEAR</text>',
        '<text x="400" y="517" text-anchor="middle" font-family="Oswald, Georgia, serif" font-size="50" fill="white" letter-spacing="8">FEAR</text>')
    svg = svg.replace(
        '<text x="400" y="462" text-anchor="middle" font-family="Georgia, serif" font-size="26" fill="black" letter-spacing="10">OVER</text>',
        '<text x="400" y="463" text-anchor="middle" font-family="Oswald, Georgia, serif" font-size="34" fill="black" letter-spacing="14">OVER</text>')
    write_svg('faith_02_faith_over_fear.svg', svg)

# ── FAITH 03: BLESSED ──────────────────────────────────────────────────────────
def fix_03():
    svg = add_fonts(read_svg('faith_03_blessed.svg'))
    old = ('  <text x="400" y="422" text-anchor="middle" font-family="Georgia, serif"\n'
           '        font-size="86" font-weight="bold" fill="black" letter-spacing="2">BLESSED</text>')
    new = ('  <text x="400" y="427" text-anchor="middle" font-family="Oswald, Georgia, serif"\n'
           '        font-size="82" fill="black" letter-spacing="1">BLESSED</text>')
    assert old in svg, "faith_03 text not found"
    write_svg('faith_03_blessed.svg', svg.replace(old, new))

# ── FAITH 04: GRACE UPON GRACE ─────────────────────────────────────────────────
def fix_04():
    svg = add_fonts(read_svg('faith_04_grace_upon_grace.svg'))
    old = ('  <text x="400" y="345" text-anchor="middle" font-family="Georgia, serif" font-style="italic" font-size="32" fill="black" letter-spacing="3">grace</text>\n'
           '  <text x="400" y="400" text-anchor="middle" font-family="Georgia, serif" font-size="72" font-weight="bold" fill="black" letter-spacing="5">UPON</text>\n'
           '  <text x="400" y="460" text-anchor="middle" font-family="Georgia, serif" font-style="italic" font-size="32" fill="black" letter-spacing="3">grace</text>\n'
           '  <text x="400" y="520" text-anchor="middle" font-family="Georgia, serif" font-size="14" fill="black" letter-spacing="6">JOHN  1:16</text>')
    new = ('  <text x="400" y="352" text-anchor="middle" font-family="DancingScript, cursive" font-size="44" fill="black">grace</text>\n'
           '  <text x="400" y="413" text-anchor="middle" font-family="Oswald, Georgia, serif" font-size="78" fill="black" letter-spacing="4">UPON</text>\n'
           '  <text x="400" y="470" text-anchor="middle" font-family="DancingScript, cursive" font-size="44" fill="black">grace</text>\n'
           '  <text x="400" y="524" text-anchor="middle" font-family="PlayfairItalic, Georgia, serif" font-size="15" fill="black" letter-spacing="5">JOHN  1:16</text>')
    assert old in svg, "faith_04 text not found"
    write_svg('faith_04_grace_upon_grace.svg', svg.replace(old, new))

# ── FAITH 05: SHE IS CLOTHED ───────────────────────────────────────────────────
def fix_05():
    svg = add_fonts(read_svg('faith_05_she_is_clothed.svg'))
    old = ('  <text x="400" y="335" text-anchor="middle" font-family="Georgia, serif" font-size="21" fill="black" letter-spacing="2">SHE IS CLOTHED IN</text>\n'
           '  <text x="400" y="382" text-anchor="middle" font-family="Georgia, serif" font-size="56" font-weight="bold" fill="black">STRENGTH</text>\n'
           '  <text x="400" y="432" text-anchor="middle" font-family="Georgia, serif" font-size="22" fill="black" letter-spacing="8">AND DIGNITY</text>\n'
           '  <text x="400" y="475" text-anchor="middle" font-family="Georgia, serif" font-size="15" fill="black" letter-spacing="4">PROVERBS  31:25</text>')
    new = ('  <text x="400" y="335" text-anchor="middle" font-family="Playfair, Georgia, serif" font-size="20" fill="black" letter-spacing="3">SHE IS CLOTHED IN</text>\n'
           '  <text x="400" y="386" text-anchor="middle" font-family="Oswald, Georgia, serif" font-size="60" fill="black" letter-spacing="1">STRENGTH</text>\n'
           '  <text x="400" y="432" text-anchor="middle" font-family="Playfair, Georgia, serif" font-size="22" fill="black" letter-spacing="6">AND DIGNITY</text>\n'
           '  <text x="400" y="476" text-anchor="middle" font-family="PlayfairItalic, Georgia, serif" font-size="14" fill="black" letter-spacing="4">PROVERBS  31:25</text>')
    assert old in svg, "faith_05 text not found"
    write_svg('faith_05_she_is_clothed.svg', svg.replace(old, new))

# ── FAITH 06: WITH GOD ─────────────────────────────────────────────────────────
def fix_06():
    svg = add_fonts(read_svg('faith_06_with_god.svg'))
    old = ('  <text x="400" y="677" text-anchor="middle" font-family="Georgia, serif" font-size="22" fill="black" letter-spacing="1">WITH GOD</text>\n'
           '  <text x="400" y="718" text-anchor="middle" font-family="Georgia, serif" font-size="34" font-weight="bold" fill="black" letter-spacing="3">ALL THINGS</text>\n'
           '  <text x="400" y="748" text-anchor="middle" font-family="Georgia, serif" font-size="16" fill="black" letter-spacing="5">ARE POSSIBLE  ·  MATTHEW 19:26</text>')
    new = ('  <text x="400" y="674" text-anchor="middle" font-family="DancingScript, cursive" font-size="27" fill="black">With God</text>\n'
           '  <text x="400" y="718" text-anchor="middle" font-family="Oswald, Georgia, serif" font-size="40" fill="black" letter-spacing="3">ALL THINGS</text>\n'
           '  <text x="400" y="748" text-anchor="middle" font-family="PlayfairItalic, Georgia, serif" font-size="15" fill="black" letter-spacing="3">ARE POSSIBLE  ·  MATTHEW 19:26</text>')
    assert old in svg, "faith_06 text not found"
    write_svg('faith_06_with_god.svg', svg.replace(old, new))

# ── FAITH 07: JOY ──────────────────────────────────────────────────────────────
def fix_07():
    svg = add_fonts(read_svg('faith_07_joy.svg'))
    old = ('  <text x="400" y="365" text-anchor="middle" font-family="Georgia, serif" font-size="26" fill="black" letter-spacing="6">THE</text>\n'
           '  <text x="400" y="428" text-anchor="middle" font-family="Georgia, serif" font-size="68" font-weight="bold" fill="black">JOY</text>\n'
           '  <text x="400" y="468" text-anchor="middle" font-family="Georgia, serif" font-size="22" fill="black" letter-spacing="3">OF THE LORD</text>\n'
           '  <text x="400" y="502" text-anchor="middle" font-family="Georgia, serif" font-size="17" fill="black" letter-spacing="2">IS MY STRENGTH</text>\n'
           '  <text x="400" y="533" text-anchor="middle" font-family="Georgia, serif" font-size="13" fill="black" letter-spacing="4">NEHEMIAH  8:10</text>')
    new = ('  <text x="400" y="332" text-anchor="middle" font-family="Playfair, Georgia, serif" font-size="22" fill="black" letter-spacing="6">THE</text>\n'
           '  <text x="400" y="400" text-anchor="middle" font-family="Oswald, Georgia, serif" font-size="76" fill="black" letter-spacing="2">JOY</text>\n'
           '  <text x="400" y="444" text-anchor="middle" font-family="Playfair, Georgia, serif" font-size="22" fill="black" letter-spacing="3">OF THE LORD</text>\n'
           '  <text x="400" y="474" text-anchor="middle" font-family="Playfair, Georgia, serif" font-size="17" fill="black" letter-spacing="2">IS MY STRENGTH</text>\n'
           '  <text x="400" y="504" text-anchor="middle" font-family="PlayfairItalic, Georgia, serif" font-size="13" fill="black" letter-spacing="3">NEHEMIAH  8:10</text>')
    assert old in svg, "faith_07 text not found"
    write_svg('faith_07_joy.svg', svg.replace(old, new))

# ── FAITH 08: I CAN ────────────────────────────────────────────────────────────
def fix_08():
    svg = add_fonts(read_svg('faith_08_i_can.svg'))
    # Fix arc radii
    svg = svg.replace(
        '<path id="topArc" d="M 100,400 A 300,300 0 0,1 700,400"/>',
        '<path id="topArc" d="M 140,400 A 260,260 0 0,1 660,400"/>')
    svg = svg.replace(
        '<path id="botArc" d="M 130,470 A 270,270 0 0,0 670,470"/>',
        '<path id="botArc" d="M 140,400 A 260,260 0 0,0 660,400"/>')
    # Upgrade arc text fonts
    svg = svg.replace(
        '  <text font-family="Georgia, serif" font-size="30" font-weight="bold" fill="black" letter-spacing="3">\n'
        '    <textPath href="#topArc" startOffset="50%" text-anchor="middle">I CAN DO ALL THINGS</textPath>\n'
        '  </text>',
        '  <text font-family="Oswald, Georgia, serif" font-size="28" fill="black" letter-spacing="4">\n'
        '    <textPath href="#topArc" startOffset="50%" text-anchor="middle">I CAN DO ALL THINGS</textPath>\n'
        '  </text>')
    svg = svg.replace(
        '  <text font-family="Georgia, serif" font-size="18" fill="black" letter-spacing="2">\n'
        '    <textPath href="#botArc" startOffset="50%" text-anchor="middle">PHILIPPIANS 4:13</textPath>\n'
        '  </text>',
        '  <text font-family="PlayfairItalic, Georgia, serif" font-size="17" fill="black" letter-spacing="2">\n'
        '    <textPath href="#botArc" startOffset="50%" text-anchor="middle">PHILIPPIANS 4:13</textPath>\n'
        '  </text>')
    # Shift center text up 20px + upgrade fonts
    old_c = ('  <text x="400" y="375" text-anchor="middle" font-family="Georgia, serif" font-size="24" fill="black" letter-spacing="3">THROUGH CHRIST</text>\n'
             '  <text x="400" y="432" text-anchor="middle" font-family="Georgia, serif" font-size="52" font-weight="bold" fill="black" letter-spacing="2">WHO</text>\n'
             '  <text x="400" y="485" text-anchor="middle" font-family="Georgia, serif" font-size="28" fill="black" letter-spacing="5">STRENGTHENS ME</text>')
    new_c = ('  <text x="400" y="355" text-anchor="middle" font-family="Playfair, Georgia, serif" font-size="22" fill="black" letter-spacing="4">THROUGH CHRIST</text>\n'
             '  <text x="400" y="412" text-anchor="middle" font-family="Oswald, Georgia, serif" font-size="58" fill="black" letter-spacing="2">WHO</text>\n'
             '  <text x="400" y="462" text-anchor="middle" font-family="Playfair, Georgia, serif" font-size="26" fill="black" letter-spacing="4">STRENGTHENS ME</text>')
    assert old_c in svg, "faith_08 center text not found"
    write_svg('faith_08_i_can.svg', svg.replace(old_c, new_c))

# ── FAITH 09: PROVERBS 31 — COMPLETE REDESIGN ─────────────────────────────────
def fix_09():
    def starburst(cx, cy, r_out, r_in, n=8):
        pts = []
        for i in range(n * 2):
            a = math.radians(i * 180 / n - 90)
            r = r_out if i % 2 == 0 else r_in
            pts.append(f"{cx + r*math.cos(a):.1f},{cy + r*math.sin(a):.1f}")
        return f'  <polygon points="{" ".join(pts)}" fill="black"/>'

    WR = 232  # wreath radius
    flowers, dots, connectors = [], [], []
    for i in range(12):
        a = math.radians(i * 30 - 90)
        cx = 400 + WR * math.cos(a)
        cy = 400 + WR * math.sin(a)
        flowers.append(starburst(cx, cy, r_out=21, r_in=8))
        dots.append(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="white"/>')
        # connector diamond midway between this and next flower
        a2 = math.radians(i * 30 - 90 + 15)
        mx = 400 + WR * math.cos(a2)
        my = 400 + WR * math.sin(a2)
        sz = 5
        p1 = f"{mx + sz*math.cos(a2):.1f},{my + sz*math.sin(a2):.1f}"
        p2 = f"{mx + sz*math.cos(a2+math.pi/2):.1f},{my + sz*math.sin(a2+math.pi/2):.1f}"
        p3 = f"{mx - sz*math.cos(a2):.1f},{my - sz*math.sin(a2):.1f}"
        p4 = f"{mx + sz*math.cos(a2-math.pi/2):.1f},{my + sz*math.sin(a2-math.pi/2):.1f}"
        connectors.append(f'  <polygon points="{p1} {p2} {p3} {p4}" fill="black"/>')

    flower_block = '\n'.join(flowers + dots)
    connector_block = '\n'.join(connectors)

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">
  <title>Proverbs 31 Woman SVG</title>
  <rect width="800" height="800" fill="none"/>
  <defs>
    <style>
      @font-face {{ font-family: 'DancingScript'; src: url('/usr/local/share/fonts/DancingScript-Bold.ttf'); }}
      @font-face {{ font-family: 'Oswald'; src: url('/usr/local/share/fonts/Oswald-Bold.ttf'); }}
      @font-face {{ font-family: 'Playfair'; src: url('/usr/local/share/fonts/PlayfairDisplay-Bold.ttf'); }}
      @font-face {{ font-family: 'PlayfairItalic'; src: url('/usr/local/share/fonts/PlayfairDisplay-Italic.ttf'); }}
    </style>
  </defs>
  <!-- Wreath ring -->
  <circle cx="400" cy="400" r="{WR}" fill="none" stroke="black" stroke-width="1" stroke-dasharray="3,10"/>
  <!-- 12 starburst flowers -->
{flower_block}
  <!-- Connector diamonds -->
{connector_block}
  <!-- Inner frame -->
  <circle cx="400" cy="400" r="190" fill="none" stroke="black" stroke-width="3"/>
  <circle cx="400" cy="400" r="178" fill="none" stroke="black" stroke-width="1"/>
  <!-- Text -->
  <text x="400" y="353" text-anchor="middle" font-family="Playfair, Georgia, serif" font-size="18" fill="black" letter-spacing="5">PROVERBS 31</text>
  <line x1="300" y1="366" x2="500" y2="366" stroke="black" stroke-width="1.5"/>
  <text x="400" y="442" text-anchor="middle" font-family="Oswald, Georgia, serif" font-size="76" fill="black" letter-spacing="1">WOMAN</text>
  <line x1="280" y1="456" x2="520" y2="456" stroke="black" stroke-width="1.5"/>
  <text x="400" y="483" text-anchor="middle" font-family="DancingScript, cursive" font-size="21" fill="black">virtuous · strong · chosen</text>
  <text x="400" y="511" text-anchor="middle" font-family="PlayfairItalic, Georgia, serif" font-size="13" fill="black" letter-spacing="3">PROVERBS  31:10</text>
</svg>'''
    write_svg('faith_09_proverbs31.svg', svg)

# ── FAITH 10: TRUST ────────────────────────────────────────────────────────────
def fix_10():
    svg = add_fonts(read_svg('faith_10_trust.svg'))
    old = ('  <text x="400" y="315" text-anchor="middle" font-family="Georgia, serif" font-size="26" fill="black" letter-spacing="4">TRUST IN</text>\n'
           '  <text x="400" y="370" text-anchor="middle" font-family="Georgia, serif" font-size="30" fill="black" letter-spacing="3">THE LORD</text>\n'
           '  <text x="400" y="428" text-anchor="middle" font-family="Georgia, serif" font-size="58" font-weight="bold" fill="black">WITH ALL</text>\n'
           '  <text x="400" y="488" text-anchor="middle" font-family="Georgia, serif" font-size="28" fill="black" letter-spacing="4">YOUR HEART</text>\n'
           '  <text x="400" y="545" text-anchor="middle" font-family="Georgia, serif" font-size="14" fill="black" letter-spacing="5">PROVERBS  3:5</text>')
    new = ('  <text x="400" y="315" text-anchor="middle" font-family="Playfair, Georgia, serif" font-size="24" fill="black" letter-spacing="5">TRUST IN</text>\n'
           '  <text x="400" y="370" text-anchor="middle" font-family="DancingScript, cursive" font-size="36" fill="black">the Lord</text>\n'
           '  <text x="400" y="432" text-anchor="middle" font-family="Oswald, Georgia, serif" font-size="62" fill="black" letter-spacing="2">WITH ALL</text>\n'
           '  <text x="400" y="488" text-anchor="middle" font-family="Playfair, Georgia, serif" font-size="26" fill="black" letter-spacing="3">YOUR HEART</text>\n'
           '  <text x="400" y="544" text-anchor="middle" font-family="PlayfairItalic, Georgia, serif" font-size="13" fill="black" letter-spacing="4">PROVERBS  3:5</text>')
    assert old in svg, "faith_10 text not found"
    write_svg('faith_10_trust.svg', svg.replace(old, new))

# ── RUN ALL ────────────────────────────────────────────────────────────────────
print("=== Fixing all 10 faith SVGs ===")
for fn, name in [(fix_01,'01'),(fix_02,'02'),(fix_03,'03'),(fix_04,'04'),(fix_05,'05'),
                  (fix_06,'06'),(fix_07,'07'),(fix_08,'08'),(fix_09,'09'),(fix_10,'10')]:
    try:
        fn()
    except AssertionError as e:
        print(f"  ERROR faith_{name}: {e}")

print("\n=== Rendering previews ===")
files = [
    'faith_01_be_still', 'faith_02_faith_over_fear', 'faith_03_blessed',
    'faith_04_grace_upon_grace', 'faith_05_she_is_clothed', 'faith_06_with_god',
    'faith_07_joy', 'faith_08_i_can', 'faith_09_proverbs31', 'faith_10_trust'
]
for f in files:
    try:
        render(f + '.svg')
    except Exception as e:
        print(f"  RENDER ERROR {f}: {e}")

print("\n✓ Done!")
