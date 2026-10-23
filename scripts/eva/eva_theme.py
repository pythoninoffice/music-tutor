import math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
GREEN, GREEN_D = (124, 255, 79), (40, 120, 30)
ORANGE, ORANGE_D = (255, 138, 31), (150, 70, 10)
PURPLE = (155, 92, 255); RED = (230, 30, 40)
SECTIONS = [(1, 12, 'INTRO'), (13, 27, 'VERSE'), (28, 30, 'WARNING'), (31, 38, 'CHORUS'), (39, 54, 'VERSE II'), (55, 62, 'CHORUS II'), (63, 70, 'FINAL CHORUS')]
CHORUS = set(range(31, 39)) | set(range(55, 71))
_bg = {}
def hexpts(cx, cy, r, rot=0):
    return [(cx + r * math.cos(math.radians(60 * i + 30 + rot)), cy + r * math.sin(math.radians(60 * i + 30 + rot))) for i in range(6)]
def bg(W, H, t, KY, u):
    if (W, H) not in _bg:
        y = np.linspace(0, 1, H)[:, None, None]
        top, bot = np.array([42, 20, 70]), np.array([8, 5, 16])
        a = (top * (1 - y) ** 1.2 + bot * (1 - (1 - y) ** 1.2)) * np.ones((1, W, 1))
        im = Image.fromarray(a.astype(np.uint8)); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        r = 46 * u; dx = r * math.sqrt(3); dy = r * 1.5
        for j in range(int(H / dy) + 2):
            for i in range(int(W / dx) + 2):
                cx = i * dx + (dx / 2 if j % 2 else 0); cy = j * dy
                fade = max(0.0, 1 - cy / (KY * 1.05))
                if fade <= 0: continue
                od.line(hexpts(cx, cy, r) + [hexpts(cx, cy, r)[0]], fill=(150, 90, 230, int(40 * fade)), width=max(1, int(1.5 * u)))
        im = im.convert('RGBA'); im.alpha_composite(ov); a = np.asarray(im.convert('RGB')).astype(np.float32)
        a[::4] *= 0.86                                            # scanlines
        _bg[(W, H)] = a
    a = _bg[(W, H)].copy()
    sy = (t * 140) % (H + 300) - 150                              # drifting scan band
    yy = np.arange(H)[:, None]; band = np.exp(-((yy - sy) / (60 * u)) ** 2)[..., None]
    a = a + band * np.array([25, 18, 40])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def section(bar):
    for a, b, n in SECTIONS:
        if a <= bar <= b: return n
    return ''
def hud(img, t, frac, bar, u, KY, BS, FD, X=None):
    W, H = img.size; ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    osw = lambda s: ImageFont.truetype(FD + 'Oswald-VF.ttf', int(s)); minc = lambda s: ImageFont.truetype(FD + 'ShipporiMincho-ExtraBold.ttf', int(s))
    pm = 26 * u
    # SYNC RATIO bar
    d.text((pm, pm), 'SYNC RATIO', font=osw(26 * u), fill=ORANGE)
    bx0, by0, bx1, by1 = pm + 150 * u, pm + 8 * u, W - pm - 120 * u, pm + 26 * u
    d.rectangle([bx0, by0, bx1, by1], outline=ORANGE, width=max(1, int(2 * u)))
    n = 40; segw = (bx1 - bx0 - 6 * u) / n
    for i in range(int(n * frac)):
        d.rectangle([bx0 + 3 * u + i * segw, by0 + 3 * u, bx0 + 3 * u + (i + 0.75) * segw, by1 - 3 * u], fill=GREEN)
    d.text((W - pm, pm), f'{frac * 100:5.1f}%', font=osw(30 * u), fill=GREEN, anchor='ra')
    # title + bar
    y2 = pm + 50 * u
    d.text((pm, y2), '残酷な天使のテーゼ', font=minc(40 * u), fill=(245, 240, 250))
    d.text((pm, y2 + 52 * u), f"CRUEL ANGEL'S THESIS  //  BAR {bar:02d}", font=osw(24 * u), fill=(200, 180, 230))
    # section caution box (right)
    sec = section(bar); col = RED if sec == 'WARNING' else ORANGE
    f = osw(30 * u); tw = d.textlength(sec, font=f); x1 = W - pm; x0 = x1 - tw - 70 * u; y0 = y2 + 4 * u; y1 = y0 + 50 * u
    d.rectangle([x0, y0, x1, y1], fill=(0, 0, 0, 170), outline=col, width=max(2, int(3 * u)))
    for k in range(6):                                           # stripes block
        sx = x0 + 6 * u + k * 9 * u
        d.polygon([(sx, y1 - 6 * u), (sx + 6 * u, y0 + 6 * u), (sx + 10 * u, y0 + 6 * u), (sx + 4 * u, y1 - 6 * u)], fill=col)
    d.text((x0 + 62 * u, (y0 + y1) / 2), sec, font=f, fill=col, anchor='lm')
    # WARNING run-up: blinking emergency band
    if sec == 'WARNING':
        on = int(t * 4) % 2 == 0; yb = KY * 0.42; hb = 90 * u
        d.rectangle([0, yb, W, yb + hb], fill=(RED[0], RED[1], RED[2], 150 if on else 70))
        for k in range(-2, int(W / (60 * u)) + 2):
            sx = k * 60 * u + (t * 200 * u) % (60 * u)
            d.polygon([(sx, yb), (sx + 26 * u, yb), (sx + 56 * u, yb + hb / 2), (sx + 26 * u, yb + hb), (sx, yb + hb), (sx + 30 * u, yb + hb / 2)], fill=(0, 0, 0, 110))
        d.text((W / 2, yb + hb / 2), 'EMERGENCY', font=osw(64 * u), fill=(255, 235, 230, 255 if on else 160), anchor='mm')
    # chorus downbeat hex flash
    if bar in CHORUS:
        age = t - BS[bar - 1]
        if 0 <= age < 0.6:
            al = int(200 * (1 - age / 0.6)); r = (120 + 380 * age) * u
            for rr, c in ((r, GREEN), (r * 0.7, PURPLE)):
                pts = hexpts(W / 2, KY - 260 * u, rr); d.line(pts + [pts[0]], fill=c + (al,), width=max(2, int(5 * u)))
    # legend
    ly = H - 64 * u; lx = pm
    for c, lab in ((GREEN, 'RIGHT HAND'), (ORANGE, 'LEFT HAND')):
        d.rectangle([lx, ly, lx + 34 * u, ly + 22 * u], fill=c, outline=(20, 10, 30), width=2)
        d.text((lx + 46 * u, ly + 11 * u), lab, font=osw(26 * u), fill=(220, 210, 235), anchor='lm'); lx += 230 * u
    img = img.convert('RGBA'); img.alpha_composite(ov)
    # title card (lead-in): NGE style
    if t < 0.6:
        al = 1.0 if t < -0.4 else max(0.0, (0.6 - t) / 1.0)
        card = Image.new('RGBA', (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rectangle([0, 0, W, H], fill=(0, 0, 0, int(225 * al)))
        wc = (255, 255, 255, int(255 * al))
        cd.text((70 * u, 470 * u), 'EPISODE:PIANO', font=minc(46 * u), fill=wc)
        cd.text((70 * u, 560 * u), '残酷な', font=minc(170 * u), fill=wc)
        cd.text((70 * u, 760 * u), '天使の', font=minc(170 * u), fill=wc)
        cd.text((70 * u, 960 * u), 'テーゼ', font=minc(210 * u), fill=wc)
        cd.line([70 * u, 1230 * u, W - 70 * u, 1230 * u], fill=(RED[0], RED[1], RED[2], int(255 * al)), width=int(4 * u))
        cd.text((W - 70 * u, 1260 * u), "A CRUEL ANGEL'S THESIS", font=minc(44 * u), fill=wc, anchor='ra')
        cd.text((W - 70 * u, 1320 * u), 'Shiro Sagisu  /  arr. Piano Squall', font=osw(28 * u), fill=(200, 190, 210, int(255 * al)), anchor='ra')
        img.alpha_composite(card)
    return img.convert('RGB')
