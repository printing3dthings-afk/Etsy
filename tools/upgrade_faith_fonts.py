"""
Upgrade faith pack SVGs from Oswald/DancingScript/Playfair
to Cinzel Decorative / Great Vibes / Cormorant Garamond.
"""
import re, os

SVG_DIR = "data/faith_pack/SVG"
PREVIEW_DIR = "data/faith_pack/previews"

NEW_FONT_STYLE = '''    <style>
      @font-face { font-family: 'GreatVibes'; src: url('/usr/local/share/fonts/GreatVibes-Regular.ttf'); }
      @font-face { font-family: 'CinzelDec'; src: url('/usr/local/share/fonts/CinzelDecorative-Bold.ttf'); }
      @font-face { font-family: 'CinzelDecReg'; src: url('/usr/local/share/fonts/CinzelDecorative-Regular.ttf'); }
      @font-face { font-family: 'Cinzel'; src: url('/usr/local/share/fonts/Cinzel-Regular.ttf'); }
      @font-face { font-family: 'Cormorant'; src: url('/usr/local/share/fonts/CormorantGaramond-Bold.ttf'); }
      @font-face { font-family: 'CormorantItalic'; src: url('/usr/local/share/fonts/CormorantGaramond-BoldItalic.ttf'); }
    </style>'''

OLD_FONT_STYLE = re.compile(
    r'<style>.*?</style>', re.DOTALL
)

# Per-file overrides: (old_text, new_text) tuples applied after global font swap
OVERRIDES = {
    # faith_01: BE STILL / and know that / I AM GOD / PSALM 46:10
    "faith_01_be_still.svg": [
        ('font-family="Oswald, Georgia, serif"\n        font-size="50"', 'font-family="CinzelDec, serif"\n        font-size="44"'),
        ('font-family="Oswald, Georgia, serif"\n        font-size="28"', 'font-family="Cinzel, serif"\n        font-size="26"'),
        ('font-family="DancingScript, cursive"\n        font-size="24"', 'font-family="GreatVibes, cursive"\n        font-size="20"'),
        ('font-family="PlayfairItalic, Georgia, serif"\n        font-size="12"', 'font-family="CormorantItalic, serif"\n        font-size="13"'),
    ],
    # faith_02: FAITH / OVER / FEAR banners
    "faith_02_faith_over_fear.svg": [
        ('font-family="Oswald, Georgia, serif" font-size="50"', 'font-family="CinzelDec, serif" font-size="40"'),
        ('font-family="Oswald, Georgia, serif" font-size="34"', 'font-family="Cinzel, serif" font-size="32"'),
    ],
    # faith_03: BLESSED medallion
    "faith_03_blessed.svg": [
        ('font-family="Oswald, Georgia, serif"\n        font-size="72"', 'font-family="CinzelDec, serif"\n        font-size="64"'),
    ],
    # faith_04: grace / UPON / grace / JOHN 1:16
    "faith_04_grace_upon_grace.svg": [
        ('font-family="DancingScript, cursive" font-size="36"', 'font-family="GreatVibes, cursive" font-size="30"'),
        ('font-family="Oswald, Georgia, serif" font-size="82"', 'font-family="CinzelDec, serif" font-size="74"'),
        ('font-family="PlayfairItalic, Georgia, serif" font-size="15"', 'font-family="CormorantItalic, serif" font-size="16"'),
    ],
    # faith_05: SHE IS CLOTHED IN / STRENGTH / AND DIGNITY / PROVERBS 31:25
    "faith_05_she_is_clothed.svg": [
        ('font-family="Playfair, Georgia, serif" font-size="20"', 'font-family="Cormorant, serif" font-size="20"'),
        ('font-family="Oswald, Georgia, serif" font-size="60"', 'font-family="CinzelDec, serif" font-size="54"'),
        ('font-family="Playfair, Georgia, serif" font-size="22"', 'font-family="Cormorant, serif" font-size="22"'),
        ('font-family="PlayfairItalic, Georgia, serif" font-size="14"', 'font-family="CormorantItalic, serif" font-size="15"'),
    ],
    # faith_06: With God / ALL THINGS / ARE POSSIBLE · MATTHEW
    "faith_06_with_god.svg": [
        ('font-family="DancingScript, cursive" font-size="27"', 'font-family="GreatVibes, cursive" font-size="22"'),
        ('font-family="Oswald, Georgia, serif" font-size="40"', 'font-family="CinzelDec, serif" font-size="36"'),
        ('font-family="PlayfairItalic, Georgia, serif" font-size="15"', 'font-family="CormorantItalic, serif" font-size="16"'),
    ],
    # faith_07: THE / JOY / OF THE LORD / IS MY STRENGTH / NEHEMIAH
    "faith_07_joy.svg": [
        ('font-family="Playfair, Georgia, serif" font-size="22"', 'font-family="Cormorant, serif" font-size="22"'),
        ('font-family="Oswald, Georgia, serif" font-size="76"', 'font-family="CinzelDec, serif" font-size="68"'),
        ('font-family="Playfair, Georgia, serif" font-size="17"', 'font-family="Cormorant, serif" font-size="18"'),
        ('font-family="PlayfairItalic, Georgia, serif" font-size="13"', 'font-family="CormorantItalic, serif" font-size="14"'),
    ],
    # faith_08: arc text + center text
    "faith_08_i_can.svg": [
        ('font-family="Oswald, sans-serif" font-size="28"', 'font-family="Cinzel, serif" font-size="22"'),
        ('font-family="PlayfairItalic, sans-serif" font-size="17"', 'font-family="CormorantItalic, serif" font-size="18"'),
        ('font-family="Playfair, sans-serif" font-size="22"', 'font-family="Cormorant, serif" font-size="22"'),
        ('font-family="Oswald, sans-serif" font-size="58"', 'font-family="CinzelDec, serif" font-size="52"'),
        ('font-family="Playfair, sans-serif" font-size="26"', 'font-family="Cormorant, serif" font-size="26"'),
    ],
    # faith_09: PROVERBS 31 / WOMAN / virtuous·strong·chosen / ref
    "faith_09_proverbs31.svg": [
        ('font-family="Playfair, Georgia, serif" font-size="18"', 'font-family="Cormorant, serif" font-size="18"'),
        ('font-family="Oswald, Georgia, serif" font-size="76"', 'font-family="CinzelDec, serif" font-size="68"'),
        ('font-family="DancingScript, cursive" font-size="21"', 'font-family="GreatVibes, cursive" font-size="18"'),
        ('font-family="PlayfairItalic, Georgia, serif" font-size="13"', 'font-family="CormorantItalic, serif" font-size="14"'),
    ],
    # faith_10: TRUST IN / the Lord / WITH ALL / YOUR HEART / PROVERBS 3:5
    "faith_10_trust.svg": [
        ('font-family="Playfair, Georgia, serif" font-size="24"', 'font-family="Cormorant, serif" font-size="24"'),
        ('font-family="DancingScript, cursive" font-size="36"', 'font-family="GreatVibes, cursive" font-size="30"'),
        ('font-family="Oswald, Georgia, serif" font-size="62"', 'font-family="CinzelDec, serif" font-size="56"'),
        ('font-family="Playfair, Georgia, serif" font-size="26"', 'font-family="Cormorant, serif" font-size="26"'),
        ('font-family="PlayfairItalic, Georgia, serif" font-size="13"', 'font-family="CormorantItalic, serif" font-size="14"'),
    ],
}

def upgrade_svg(filename):
    path = os.path.join(SVG_DIR, filename)
    with open(path) as f:
        content = f.read()
    
    # Replace font style block
    content = OLD_FONT_STYLE.sub(NEW_FONT_STYLE, content)
    
    # Apply per-file overrides
    overrides = OVERRIDES.get(filename, [])
    for old, new in overrides:
        if old in content:
            content = content.replace(old, new)
        else:
            print(f"  WARNING: '{old[:50]}...' not found in {filename}")
    
    with open(path, 'w') as f:
        f.write(content)
    return path

# Process all 10
files = [f for f in sorted(os.listdir(SVG_DIR)) if f.endswith('.svg')]
for fname in files:
    print(f"Upgrading {fname}...")
    upgrade_svg(fname)

print("\nAll SVGs upgraded.")
