import math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
GREEN, GREEN_D = (70, 230, 255), (15, 90, 120)      # RH: neon cyan
ORANGE, ORANGE_D = (255, 178, 60), (140, 80, 10)     # LH: amber
CY = (90, 235, 255)
SECTIONS = [(1, 4, 'LAUNCH'), (5, 26, 'ORBIT'), (27, 50, 'TRAJECTORY'), (51, 54, 'SIGNAL'), (55, 70, 'APPROACH'), (71, 75, 'TESSERACT'),
            (76, 90, 'GARGANTUA'), (91, 99, 'EVENT HORIZON'), (100, 111, 'SLINGSHOT'), (112, 114, 'HOME')]
_bg = {}
def _base(W, H, KY, u):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    a = np.zeros((H, W, 3), np.float32)
    top, bot = np.array([4, 6, 18]), np.array([1, 1, 4]); yy = (y / H)[..., None]
    a += top * (1 - yy) + bot * yy
    def blob(cx, cy, r, col, k=1.0):
        d = ((x - cx) ** 2 + (y - cy) ** 2) / (r * r); return np.exp(-d)[..., None] * np.array(col) * k
    rng = np.random.RandomState(3)
    a += blob(W * 0.15, KY * 0.35, 420 * u, (70, 20, 90)) + blob(W * 0.85, KY * 0.15, 380 * u, (10, 40, 90))
    a += blob(W * 0.6, KY * 0.55, 300 * u, (60, 25, 70), 0.6)
    # wispy noise
    n = rng.rand(H // 16 + 2, W // 16 + 2).astype(np.float32)
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(30 * u))) / 255.0
    a *= (0.6 + 0.8 * n[..., None])
    # Gargantua: black disk + accretion ring glow
    cx, cy, R = W * 0.68, KY * 0.30, 120 * u
    r = np.sqrt((x - cx) ** 2 + ((y - cy)) ** 2)
    ring = np.exp(-((r - R * 1.15) / (14 * u)) ** 2) * 1.0 + np.exp(-((r - R * 1.15) / (60 * u)) ** 2) * 0.35
    a += ring[..., None] * np.array([255, 190, 110])
    disk_r = np.sqrt((x - cx) ** 2 + ((y - cy) * 6.5) ** 2)     # thin edge-on accretion disk
    a += (np.exp(-((disk_r - R * 2.1) / (R * 0.9)) ** 2) * (np.abs(y - cy) < R * 0.35))[..., None] * np.array([255, 160, 80]) * 0.8
    a *= np.where(r < R, 0.0, 1.0)[..., None]
    lens = np.exp(-((r - R * 1.02) / (4 * u)) ** 2); a += lens[..., None] * np.array([255, 235, 200])
    # small planet
    px, py, pr = W * 0.18, KY * 0.62, 55 * u
    pd = np.sqrt((x - px) ** 2 + (y - py) ** 2); inside = pd < pr
    shade = np.clip(((x - px) * -0.6 + (y - py) * -0.8) / pr * 0.7 + 0.45, 0.05, 1)
    a = np.where(inside[..., None], np.array([70, 110, 150]) * shade[..., None], a)
    a += (np.exp(-((pd - pr) / (6 * u)) ** 2))[..., None] * np.array([60, 140, 220]) * 0.6
    a[int(KY):] *= 0.25
    return a
def bg(W, H, t, KY, u):
    if (W, H) not in _bg:
        rng = np.random.RandomState(9)
        layers = [(rng.rand(int(W * H / d)) * W, rng.rand(int(W * H / d)) * H, s, sp) for d, s, sp in ((2500, 1, 6), (9000, 2, 18), (40000, 3, 45))]
        _bg[(W, H)] = (_base(W, H, KY, u), layers)
    a, layers = _bg[(W, H)]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for xs, ys, s, sp in layers:                                   # parallax stars drift downward
        yy = (ys + max(t, -3) * sp * u) % H
        for X, Y in zip(xs, yy):
            if Y > KY: continue
            b = 150 + int(100 * ((X * 7 + Y) % 1))
            r = s * u * 0.7; d.ellipse([X - r, Y - r, X + r, Y + r], fill=(b, b, min(255, b + 20)))
    return im
def section(bar):
    for a, b, n in SECTIONS:
        if a <= bar <= b: return n
    return ''
def hud(img, t, frac, bar, u, KY, BS, FD, X=None):
    W, H = img.size; ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    orb = lambda s: ImageFont.truetype(FD + 'Orbitron-VF.ttf', int(s)); osw = lambda s: ImageFont.truetype(FD + 'Oswald-VF.ttf', int(s))
    c1, c2 = CY + (220,), CY + (90,); lw = max(1, int(2 * u)); m = 18 * u
    # cockpit frame: corner brackets + bevelled top panel
    L = 70 * u
    for (x, y, sx, sy) in ((m, m, 1, 1), (W - m, m, -1, 1), (m, KY - 20 * u, 1, -1), (W - m, KY - 20 * u, -1, -1)):
        d.line([(x, y + sy * L), (x, y), (x + sx * L, y)], fill=c1, width=lw * 2)
    d.polygon([(m + 40 * u, m), (W - m - 40 * u, m), (W - m - 70 * u, m + 150 * u), (m + 70 * u, m + 150 * u)], fill=(4, 14, 24, 150), outline=c2)
    # title + bar
    d.text((W / 2, m + 34 * u), 'INTERSTELLAR', font=orb(40 * u), fill=(230, 250, 255, 240), anchor='mm')
    d.text((W / 2, m + 76 * u), f'MAIN THEME  ·  BAR {bar:03d}  ·  {section(bar)}', font=orb(18 * u), fill=c1, anchor='mm')
    # progress / mission timeline
    bx0, bx1, by = m + 110 * u, W - m - 110 * u, m + 115 * u
    d.line([bx0, by, bx1, by], fill=c2, width=lw)
    for i in range(11): xx = bx0 + (bx1 - bx0) * i / 10; d.line([xx, by - 5 * u, xx, by + 5 * u], fill=c2, width=lw)
    xx = bx0 + (bx1 - bx0) * min(1, frac); d.line([bx0, by, xx, by], fill=CY + (255,), width=lw * 2)
    d.polygon([(xx, by - 10 * u), (xx + 8 * u, by), (xx, by + 10 * u), (xx - 8 * u, by)], fill=ORANGE + (255,))
    d.text((bx0 - 10 * u, by), 'T+', font=orb(16 * u), fill=c1, anchor='rm'); d.text((bx1 + 10 * u, by), f'{frac * 100:4.1f}%', font=orb(16 * u), fill=c1, anchor='lm')
    # telemetry readouts (left/right side, just above keyboard)
    tt = max(t, 0.0); yb = KY - 190 * u
    left = [('VEL', f'{0.55 + 0.4 * frac:.3f} c'), ('DILATION', f'x{1 + 6 * frac ** 2:.2f}'), ('MET', f'{int(tt // 60):02d}:{tt % 60:05.2f}')]
    right = [('HDG', f'{(tt * 7.3) % 360:05.1f}°'), ('DIST', f'{max(0, 10.0 - 10 * frac):.2f} AU'), ('O2', '98.6%')]
    for i, (k, v) in enumerate(left):
        y = yb + i * 40 * u; d.text((m + 14 * u, y), k, font=orb(14 * u), fill=c2); d.text((m + 14 * u, y + 15 * u), v, font=orb(20 * u), fill=c1)
    for i, (k, v) in enumerate(right):
        y = yb + i * 40 * u; d.text((W - m - 14 * u, y), k, font=orb(14 * u), fill=c2, anchor='ra'); d.text((W - m - 14 * u, y + 15 * u), v, font=orb(20 * u), fill=c1, anchor='ra')
    # reticle around the black hole
    cx, cy, R = W * 0.68, KY * 0.30, 175 * u
    for k in range(4):
        a0 = 45 + 90 * k + (t * 8) % 360; d.arc([cx - R, cy - R, cx + R, cy + R], a0 - 18, a0 + 18, fill=c2, width=lw)
    d.text((cx + R * 0.75, cy + R * 0.8), 'GARGANTUA  M=1e8 M☉', font=orb(13 * u), fill=c2)
    # legend
    ly = H - 60 * u; lx = m + 20 * u
    for c, lab in ((GREEN, 'RIGHT HAND'), (ORANGE, 'LEFT HAND')):
        d.rectangle([lx, ly, lx + 34 * u, ly + 20 * u], fill=c, outline=(10, 20, 30), width=2)
        d.text((lx + 46 * u, ly + 10 * u), lab, font=orb(18 * u), fill=(200, 230, 240), anchor='lm'); lx += 260 * u
    img = img.convert('RGBA'); img.alpha_composite(ov)
    if t < 0.6:                                                   # title card
        al = 1.0 if t < -0.4 else max(0.0, (0.6 - t) / 1.0)
        card = Image.new('RGBA', (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rectangle([0, 0, W, H], fill=(0, 0, 0, int(200 * al)))
        wc = (240, 248, 255, int(255 * al)); yc = H * 0.38
        cd.text((W / 2, yc), 'I N T E R S T E L L A R', font=orb(70 * u), fill=wc, anchor='mm')
        cd.line([W * 0.18, yc + 60 * u, W * 0.82, yc + 60 * u], fill=CY + (int(220 * al),), width=lw)
        cd.text((W / 2, yc + 110 * u), 'Main Theme', font=orb(40 * u), fill=CY + (int(255 * al),), anchor='mm')
        cd.text((W / 2, yc + 170 * u), 'Hans Zimmer', font=osw(36 * u), fill=(220, 220, 230, int(255 * al)), anchor='mm')
        cd.text((W / 2, yc + 220 * u), 'arr. Patrik Pietschmann', font=osw(24 * u), fill=(170, 180, 200, int(230 * al)), anchor='mm')
        img.alpha_composite(card)
    return img.convert('RGB')
