"""Instagram reel for one Christmas village: title, one shot per building, the
whole village together. Frames are drawn with PIL and piped to ffmpeg.
    python3 reel.py victorian out.mp4
"""
import math, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

STYLE, OUT = sys.argv[1], sys.argv[2]
PREVIEW = [float(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else None
HERE = __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), '..', 'renders')
F = '/home/user/Etsy/fonts/'; AF = '/home/user/Etsy/assets/fonts/'
W, H, FPS = 1080, 1920, 30

V = dict(
    title=('The Victorian', 'Christmas Village'),
    sky=((10, 17, 34), (34, 54, 92)), ink=(246, 236, 214), accent=(240, 204, 132),
    ground_ink=(32, 44, 70), name_font=F + 'PlayfairDisplay-Bold.ttf',
    order=[('cottage', 'Cottage', 'A round brick cottage under a snowy cone roof'),
           ('toy_shop', 'Toy Shop', 'Two storeys of brick and a round corner tower'),
           ('townhouse', 'Townhouse', 'Three storeys, with a bow window up its front'),
           ('shop_house', 'Shop-House', 'A bow-window shop under a timbered upper floor'),
           ('coaching_inn', 'Coaching Inn', 'The widest of them, with a carriage archway'),
           ('clock_tower', 'Clock Tower', 'A square clock tower on a round brick drum'),
           ('santas_workshop', "Santa's Workshop", 'One big toy window, the toys raised on the glass'),
           ('church', 'Church', 'A spire, a bell tower and a rose window')])
G = dict(
    title=('The Gingerbread', 'Christmas Village'),
    sky=((30, 14, 22), (82, 36, 44)), ink=(252, 240, 226), accent=(255, 176, 140),
    ground_ink=(78, 40, 30), name_font=F + 'Fredoka-SemiBold.ttf',
    order=[('cottage', 'Cupcake Cottage', 'A fluted cupcake under a chocolate dome'),
           ('turret_house', 'Turret House', 'A round chocolate roof that curls into icing'),
           ('sweet_shop', 'Sweet Shop', 'A three-tier layer cake with a shop out front'),
           ('cocoa_cafe', 'Cocoa Café', 'A hot-cocoa mug with a little café beside it'),
           ('candy_cane_chapel', 'Candy Cane Chapel', 'A candy-cane tower on a gingerbread chapel'),
           ('cookie_clock_tower', 'Cookie Clock Tower', 'Stacked cookies and a frosted clock'),
           ('santas_workshop', "Santa's Workshop", 'A gingerbread workshop with a peppermint chimney')])
T = V if STYLE == 'victorian' else G
N = len(T['order'])

def font(p, s): return ImageFont.truetype(p, s)
f_eyebrow = font(AF + 'Poppins-SemiBold.ttf', 34)
f_title = font(T['name_font'], 92)
f_script = font(F + 'GreatVibes-Regular.ttf', 120)
f_name = font(T['name_font'], 100)
f_line = font(AF + 'Poppins-Regular.ttf', 34)
f_small = font(AF + 'Poppins-SemiBold.ttf', 26)
f_count = font(AF + 'Poppins-SemiBold.ttf', 32)

def ease_out(t): return 1 - (1 - t) ** 3
def ease_back(t, s=1.4): t -= 1; return t * t * ((s + 1) * t + s) + 1
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))

# sky: vertical gradient + vignette, drawn once
sky = Image.new('RGB', (W, H)); px = sky.load()
(r0, g0, b0), (r1, g1, b1) = T['sky']
for y in range(H):
    t = y / H
    for x in range(0, W):
        v = 1 - 0.35 * (((x - W / 2) / (W / 2)) ** 2)
        px[x, y] = (int((r0 + (r1 - r0) * t) * v), int((g0 + (g1 - g0) * t) * v), int((b0 + (b1 - b0) * t) * v))
sky = sky.convert('RGBA')
rng = random.Random(7)
stars = [(rng.uniform(0, W), rng.uniform(0, H * 0.45), rng.uniform(1, 2.6), rng.uniform(0, 6.28), rng.uniform(1.5, 4)) for _ in range(110)]
flakes = [dict(x=rng.uniform(0, W), y=rng.uniform(-H, H), r=rng.uniform(2, 6.5), v=rng.uniform(40, 120), ph=rng.uniform(0, 6.28),
               sw=rng.uniform(10, 40), front=rng.random() < 0.18) for _ in range(170)]
for f in flakes:
    if f['front']: f['r'] *= 2.0; f['v'] *= 1.8

def load_rgba(p): return Image.open(p).convert('RGBA')
heroes = [load_rgba(f'{HERE}/{STYLE}_{b}.png') for b, _, _ in T['order']]
lineup = load_rgba(f'{HERE}/lineup_{STYLE}.png')
ground = load_rgba(f'{HERE}/ground.png')

def place(img, scale, cy_bottom, alpha=1.0, dy=0):
    """Scale img about its centre to width W*scale; its bottom edge sits at cy_bottom."""
    w = int(W * scale); h = int(img.height * w / img.width)
    im = img.resize((w, h), Image.BILINEAR)
    if alpha < 1: im.putalpha(im.getchannel('A').point(lambda a: int(a * alpha)))
    return im, ((W - w) // 2, int(cy_bottom - h + dy))

def draw_stars(d, t):
    for x, y, r, ph, sp in stars:
        a = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(ph + t * sp))
        c = int(255 * a)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(c, c, int(c * 0.95), int(200 * a)))

def snow_layer(t, front):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for f in flakes:
        if f['front'] != front: continue
        y = (f['y'] + f['v'] * t) % (H + 40) - 20
        x = (f['x'] + f['sw'] * math.sin(f['ph'] + t * 1.3)) % W
        r = f['r']; d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 170 if not front else 120))
    return lay.filter(ImageFilter.GaussianBlur(2.2 if front else 0.8))

def text_c(d, y, s, fnt, fill, alpha=1.0, track=0):
    if alpha <= 0: return
    col = fill + (int(255 * clamp(alpha)),)
    if track:
        widths = [d.textlength(ch, font=fnt) + track for ch in s]; x = (W - sum(widths) + track) / 2
        for ch, w in zip(s, widths): d.text((x, y), ch, font=fnt, fill=col); x += w
    else:
        d.text(((W - d.textlength(s, font=fnt)) / 2, y), s, font=fnt, fill=col)

INTRO, SEG, FIN = 2.6, 2.3, 4.2
total = INTRO + SEG * N + FIN
nframes = int(total * FPS)
ff = None if PREVIEW else subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT],
                      stdin=subprocess.PIPE)
GROUND = H + 40          # where the render's bottom edge sits
for i in (range(nframes) if not PREVIEW else [int(x * FPS) for x in PREVIEW]):
    t = i / FPS
    fr = sky.copy(); d = ImageDraw.Draw(fr); draw_stars(d, t)
    fr.alpha_composite(snow_layer(t, False))
    gim, gpos = place(ground, 1.0, GROUND); fr.alpha_composite(gim, gpos)
    over = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(over)
    ink, acc = T['ink'], T['accent']
    if t < INTRO:
        u = t / INTRO
        im, pos = place(lineup, 0.98 + 0.05 * u, GROUND, alpha=0.9 * ease_out(clamp(u * 2)) * clamp((INTRO - t) / 0.35), dy=40 * (1 - ease_out(u)))
        fr.alpha_composite(im, pos)
        a1 = ease_out(clamp((t - 0.15) / 0.6)); a2 = ease_out(clamp((t - 0.5) / 0.6)); a3 = ease_out(clamp((t - 1.0) / 0.6))
        text_c(od, 330 - 20 * (1 - a1), 'COMING SOON', f_eyebrow, acc, a1, track=8)
        text_c(od, 400 - 30 * (1 - a2), T['title'][0], f_title, ink, a2)
        text_c(od, 510 - 30 * (1 - a2), T['title'][1], f_title, ink, a2)
        text_c(od, 600 - 20 * (1 - a3), f'{N} buildings', f_line, ink, a3)
        honest_y = 660
    elif t < INTRO + SEG * N:
        k = int((t - INTRO) // SEG); u = (t - INTRO - k * SEG) / SEG; ts = t - INTRO - k * SEG
        b, name, line = T['order'][k]
        rise = ease_back(clamp(ts / 0.55)); fade = clamp(ts / 0.25)
        out = clamp((SEG - ts) / 0.22)                      # fade out at the end of the segment
        im, pos = place(heroes[k], 1.0 + 0.06 * u, GROUND, alpha=fade * out, dy=160 * (1 - rise))
        fr.alpha_composite(im, pos)
        a = ease_out(clamp((ts - 0.12) / 0.4)) * out
        text_c(od, 300, f'{k + 1} / {N}', f_count, acc, a, track=6)
        text_c(od, 350 + 24 * (1 - a), name, f_name, ink, a)
        a2 = ease_out(clamp((ts - 0.3) / 0.4)) * out
        text_c(od, 490 + 16 * (1 - a2), line, f_line, ink, a2)
        honest_y = 660
    else:
        ts = t - INTRO - SEG * N; u = ts / FIN
        a = ease_out(clamp(ts / 0.7))
        im, pos = place(lineup, 1.12 - 0.06 * ease_out(u), GROUND, alpha=a, dy=60 * (1 - a))
        fr.alpha_composite(im, pos)
        a1 = ease_out(clamp((ts - 0.4) / 0.6)); a2 = ease_out(clamp((ts - 0.9) / 0.6)); a3 = ease_out(clamp((ts - 1.5) / 0.6))
        text_c(od, 300 - 20 * (1 - a1), T['title'][0] + ' ' + T['title'][1], f_line, ink, a1)
        text_c(od, 360 - 20 * (1 - a2), 'Coming soon', f_script, acc, a2)
        text_c(od, 540, f'{N} buildings · OnBrandCraftz', f_small, ink, a3, track=2)
        honest_y = 660
    # honesty line, always on, over the snow
    text_c(od, honest_y, 'Rendered from the actual print files', f_small, ink, 0.55)
    fr.alpha_composite(over)
    fr.alpha_composite(snow_layer(t, True))
    if PREVIEW: fr.convert('RGB').save(f'{OUT}_{t:.1f}.jpg', quality=85); continue
    ff.stdin.write(fr.convert('RGB').tobytes())
if ff: ff.stdin.close(); ff.wait()
print('wrote', OUT, f'{total:.1f}s', nframes, 'frames')
