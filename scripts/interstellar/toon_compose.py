import json, sys, random, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
HERE = os.path.dirname(os.path.abspath(__file__)) + os.sep
P3 = os.environ.get('TOON_P3', '/workspace/blender/p3d/' if os.path.exists('/workspace/blender/p3d/') else HERE); OUT = P3 + 'toon_out/'
D = json.load(open(P3 + os.environ.get('TOON_DATA', 'rushe_notes.json'))); LO, HI = D['LO'], D['HI']
def set_tag(tag):
    global S, NOTES, BS, END
    S = D[tag]; NOTES = S['notes']; BS = S['bar_sec']; END = S['END']
set_tag(os.environ.get('TOON_TAG', 'full'))
WK = 0.0235; WHITES = [p for p in range(LO, HI + 1) if p % 12 not in (1, 3, 6, 8, 10)]
XL = -len(WHITES) * WK / 2; BWID = 0.6 * WK; WLEN, BLEN = 0.150, 0.095
isb = lambda p: p % 12 in (1, 3, 6, 8, 10)
def kx(p): return XL + (WHITES.index(p - 1) + 1) * WK if isb(p) else XL + (WHITES.index(p) + 0.5) * WK
NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
FD = os.environ.get('TOON_FONTS', HERE + 'fonts' + os.sep)
F = lambda s, n='PatrickHand-Regular.ttf': ImageFont.truetype(FD + n, int(s))
INK = (26, 20, 22); BG = (6, 6, 10)
THEME = os.environ.get('TOON_THEME', '')
SHADOW = os.environ.get('TOON_SHADOW', '1' if THEME == 'space' else '0') == '1'; SH_OP = float(os.environ.get('TOON_SH_OP', 0.45)); DSIGN = float(os.environ.get('TOON_DSIGN', 1))
if THEME == 'eva':
    import eva_theme as ET
elif THEME == 'space':
    import space_theme as ET
HC = {'R': ((64, 214, 232), (20, 120, 140)), 'L': ((255, 140, 170), (150, 50, 80))}
if THEME in ('eva', 'space'): HC = {'R': (ET.GREEN, ET.GREEN_D), 'L': (ET.ORANGE, ET.ORANGE_D)}
SKIN_LIT, SKIN_SH, SKIN_DEEP = np.array([250, 214, 186]), np.array([226, 168, 140]), np.array([196, 130, 112])

def jit(rng, a): return rng.uniform(-a, a)
def wobbly_rect(d, x0, y0, x1, y1, rng, fill, w, j=1.2):
    pts = [(x0 + jit(rng, j), y0 + jit(rng, j)), (x1 + jit(rng, j), y0 + jit(rng, j)),
           (x1 + jit(rng, j), y1 + jit(rng, j)), (x0 + jit(rng, j), y1 + jit(rng, j))]
    d.polygon(pts, fill=fill); d.line(pts + [pts[0]], fill=INK, width=w, joint='curve')

def compose(name, meta, out, handp=None, linep=None):
    m = meta[name] if meta is not None else name; W, H, sc, cx, t, KY = m['W'], m['H'], m['scale'], m['cx'], m['t'], m['KYtop']
    port = H > W; u = W / 1080 if port else H / 720          # ui unit
    X = lambda x: W / 2 + (x - cx) * sc
    KF = KY + WLEN * sc; KB = KY + BLEN * sc
    pps = (H * 0.36 if port else H * 0.62)                    # px per second of fall
    img = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(img)
    rng = random.Random(7)                                    # stars
    if THEME in ('eva', 'space'): img = ET.bg(W, H, t, KY, u); d = ImageDraw.Draw(img)
    for _ in range(0 if THEME in ('eva', 'space') else int(W * H / 9000)):
        x, y = rng.uniform(0, W), rng.uniform(0, H); r = rng.choice([1.0, 1.2, 1.5, 1.5, 2.2, 3.0, 4.0]) * u
        tw = 0.55 + 0.45 * math.sin(t * rng.uniform(1, 3) + rng.uniform(0, 6)); c = int(120 + 135 * tw * rng.uniform(.5, 1))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(c, c, min(255, c + 10)))
    for _ in range(0 if THEME in ('eva', 'space') else int(W * H / 90000)):                       # a few sparkles
        x, y = rng.uniform(0, W), rng.uniform(0, KY - 40); r = rng.uniform(4, 8) * u
        d.line([x - r, y, x + r, y], fill=(230, 230, 240), width=max(1, int(u))); d.line([x, y - r, x, y + r], fill=(230, 230, 240), width=max(1, int(u)))
    # active notes
    act = {n[2]: n for n in NOTES if n[0] - 0.01 <= t < n[0] + n[1] - 0.02}
    # falling bars
    bl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(bl)
    fL, fN = (F(30 * u, 'Oswald-VF.ttf'), F(22 * u, 'Oswald-VF.ttf')) if THEME in ('eva', 'space') else (F(30 * u), F(24 * u, 'GochiHand-Regular.ttf'))
    for n in NOTES:
        st, du, p, fg, hd = n[0], n[1], n[2], n[3], n[4]
        y1 = KY - (st - t) * pps; y0 = KY - (st + du - t) * pps
        if y1 < 0 or y0 > KY: continue
        y1 = min(y1, KY); x = X(kx(p)); hw = (BWID if isb(p) else WK * 0.82) * sc / 2
        if x + hw < 0 or x - hw > W: continue
        c, ce = HC[hd]; rr = min(hw * 0.5, 12 * u)
        bd.rounded_rectangle([x - hw, y0, x + hw, y1], radius=rr, fill=c + (255,), outline=INK, width=max(2, int(3 * u)))
        if y1 - y0 > 14 * u: bd.rounded_rectangle([x - hw + 4 * u, y0 + 4 * u, x - hw + 9 * u, y1 - 6 * u], radius=2 * u, fill=(255, 255, 255, 90))
        if y1 - y0 > 34 * u:
            bd.text((x, y1 - 6 * u), NAMES[p % 12], font=fL, fill=INK, anchor='mb')
        if y1 - y0 > 66 * u and fg and fg != '?':
            r = 13 * u; cy = y1 - 50 * u
            bd.ellipse([x - r, cy - r, x + r, cy + r], fill=(255, 255, 255, 235), outline=INK, width=max(1, int(2 * u)))
            bd.text((x, cy + 1 * u), str(fg), font=fN, fill=INK, anchor='mm')
    img.paste(bl, (0, 0), bl)
    # keyboard (wobbly hand drawn)
    kr = random.Random(3); lw = max(2, int(3 * u))
    d.rectangle([0, KY - 6 * u, W, KY], fill=(30, 26, 30))
    for p in WHITES:
        x = X(kx(p)); x0, x1 = x - WK * sc / 2, x + WK * sc / 2
        if x1 < -5 or x0 > W + 5: continue
        if p in act:
            c = HC[act[p][4]][0]; fill = tuple(int(0.35 * 255 + 0.65 * v) for v in c)
        else: fill = (246, 242, 236)
        wobbly_rect(d, x0, KY, x1, KF, kr, fill, lw)
        d.line([x0 + 4 * u, KF - 10 * u, x1 - 4 * u, KF - 10 * u], fill=(205, 198, 192), width=max(1, int(2 * u)))
        if p % 12 == 0:
            d.text((x, KF - 16 * u), f'C{p // 12 - 1}', font=F(28 * u), fill=(70, 64, 70), anchor='mb')
    for p in range(LO, HI + 1):
        if not isb(p): continue
        x = X(kx(p)); x0, x1 = x - BWID * sc / 2, x + BWID * sc / 2
        if x1 < -5 or x0 > W + 5: continue
        fill = HC[act[p][4]][1] if p in act else (24, 22, 28)
        wobbly_rect(d, x0, KY - 2, x1, KB, kr, fill, lw, 0.8)
        d.line([x0 + 3 * u, KY + 6 * u, x0 + 3 * u, KB - 10 * u], fill=(90, 90, 100) if p not in act else (255, 255, 255), width=max(1, int(2 * u)))
    # glow on pressed keys + hit sparks
    gl = Image.new('RGB', (W, H), (0, 0, 0)); gd = ImageDraw.Draw(gl)
    for p, n in act.items():
        x = X(kx(p)); hw = WK * sc * 0.6; c = HC[n[4]][0]
        gd.ellipse([x - hw * 1.6, KY - 60 * u, x + hw * 1.6, KY + 26 * u], fill=c)
        gd.rectangle([x - hw * .8, KY - 3 * u, x + hw * .8, KY + 3 * u], fill=(255, 255, 255))
    gl = gl.filter(ImageFilter.GaussianBlur(22 * u))
    img = Image.fromarray(np.clip(np.asarray(img, np.int16) + np.asarray(gl, np.int16), 0, 255).astype(np.uint8))
    # hands: cel shading from data pass
    hp = np.asarray(Image.open(handp or OUT + name + '_hand.png').convert('RGBA')).astype(np.float32) / 255
    a = hp[..., 3]; lam = (hp[..., 0] * 2 - 1); nz = hp[..., 1] * 2 - 1
    lam = np.where(a > 0, lam / np.maximum(a, 1e-3), 0)
    sh = np.where(lam > 0.42, 0, np.where(lam > 0.05, 1, 2))
    col = np.where(sh[..., None] == 0, SKIN_LIT, np.where(sh[..., None] == 1, SKIN_SH, SKIN_DEEP)).astype(np.float32)
    rim = (nz < 0.25) & (a > 0.5); col[rim] = col[rim] * 0.93
    OCC = np.zeros_like(a, bool)
    bb = np.clip(hp[..., 2] / np.maximum(a, 1e-3), 0, 1); lb = np.where(bb <= 0.04045, bb / 12.92, ((bb + 0.055) / 1.055) ** 2.4)
    inside = a > 0.5; has_id = inside.any() and (lb[inside] < 0.98).mean() > 0.5
    idink = np.zeros_like(a)
    if has_id:
        sideL = lb >= 0.5; dep = np.where(inside, lb - 0.5 * sideL, 0)
        col[inside & sideL] *= np.array([1.015, 0.975, 0.94]); col[inside & ~sideL] = col[inside & ~sideL] * np.array([0.985, 1.0, 1.025]) + 6
        col = np.minimum(col, 255)
        lab = np.where(inside, np.where(sideL, 2, 1), 0).astype(np.uint8); L = Image.fromarray(lab)
        k = max(3, int(round(5 * u))) | 1
        e1 = np.asarray(L.filter(ImageFilter.MaxFilter(k))) != np.asarray(L.filter(ImageFilter.MinFilter(k)))
        kk = np.exp(-0.5 * (np.arange(-4, 5) / 1.5) ** 2); kk /= kk.sum()
        dq = np.apply_along_axis(lambda r: np.convolve(r, kk, 'same'), 1, dep) if False else dep
        dq = sum(kk[i] * np.roll(dq, i - 4, 1) for i in range(9)); dq = sum(kk[i] * np.roll(dq, i - 4, 0) for i in range(9)); gy, gx = np.gradient(dq); jump = np.hypot(gx, gy) > float(os.environ.get('TOON_JUMP', 0.0045))
        same = np.asarray(L.filter(ImageFilter.MaxFilter(3))) == np.asarray(L.filter(ImageFilter.MinFilter(3)))
        inner = jump & same & inside
        inner = np.asarray(Image.fromarray((inner * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
        idink = np.maximum(e1.astype(np.float32), inner * 0.9)
        if SHADOW:   # occlusion: pixels just beyond a depth step (farther surface next to a nearer finger)
            near = np.asarray(Image.fromarray((jump & inside).astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(max(3, int(9 * u)) | 1))) > 0
            loc = np.asarray(Image.fromarray(np.clip(dq * 255 / max(dq.max(), 1e-3), 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5 * u))).astype(np.float32) / 255 * max(dq.max(), 1e-3)
            OCC = near & inside & (dq > loc + 0.0008 * DSIGN) if DSIGN > 0 else near & inside & (dq < loc - 0.0008)
    if SHADOW:   # 2-tone cel: lit vs shadow band (finger sides via Nz, lambert, occlusion)
        ins = a > 0.5; bw = int(round(float(os.environ.get('TOON_BAND', 17)) * u))
        shifted = np.zeros_like(ins); dy = max(1, bw // 2); shifted[:-dy, :-bw] = ins[dy:, bw:]   # neighbour toward lower-right
        far = ins & ~np.asarray(Image.fromarray(shifted.astype(np.uint8) * 255).filter(ImageFilter.MinFilter(3))).astype(bool)
        if has_id: far |= ins & (lab != np.roll(np.roll(lab, -bw, 1), -dy, 0))   # other hand / gap on far side
        sb = (far | (nz < 0.70) | (lam < 0.60) | OCC) & ins
        sbm = np.asarray(Image.fromarray(sb.astype(np.uint8) * 255).filter(ImageFilter.ModeFilter(5))) > 0
        col[sbm] = col[sbm] * np.array([0.87, 0.78, 0.82])
        deep = sbm & ((nz < 0.6) | OCC | (lam < 0.4)); col[deep] = col[deep] * np.array([0.92, 0.88, 0.92])
        sh = sh * 0 + sbm.astype(sh.dtype) + deep.astype(sh.dtype)
    # wrist fade: fade alpha below key front edge
    yy = np.arange(H)[:, None]; f0 = KF + 30 * u; f1 = f0 + (260 * u if port else 120 * u)
    fade = np.clip((f1 - yy) / (f1 - f0), 0, 1); af = a * fade
    # outline: alpha edge + shading band edges + freestyle
    A = Image.fromarray((a * 255).astype(np.uint8))
    ed = np.asarray(A.filter(ImageFilter.MaxFilter(5 if port else 3))).astype(np.float32) / 255 - a
    band = np.asarray(Image.fromarray((sh * 100).astype(np.uint8)).filter(ImageFilter.FIND_EDGES)) > 40
    band = band & (np.asarray(A.filter(ImageFilter.MinFilter(5))) > 200)
    # shadow
    if SHADOW:
        shd = Image.fromarray((af * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9 * u))
        shd = shd.transform(shd.size, Image.AFFINE, (1, 0, -16 * u, 0, 1, -30 * u))
        base = np.asarray(img).astype(np.float32); s = np.asarray(shd)[..., None] / 255 * SH_OP
        base = base * (1 - s) + np.array([10, 12, 30]) * s
    else:
        shd = Image.fromarray((af * 150).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10 * u))
        shd = shd.transform(shd.size, Image.AFFINE, (1, 0, -14 * u, 0, 1, -18 * u))
        base = np.asarray(img).astype(np.float32); s = np.asarray(shd)[..., None] / 255
        base = base * (1 - 0.75 * s)
    hand = col.copy(); hand[band] = hand[band] * 0.78
    base = base * (1 - af[..., None]) + hand * af[..., None]
    ink = np.maximum(np.clip(ed * 1.6, 0, 1), idink) * fade
    base = base * (1 - ink[..., None]) + np.array(INK) * ink[..., None]
    try:
        import glob; lf = linep or glob.glob(OUT + str(name) + '_line_*.png')[0]
        ln = np.asarray(Image.open(lf).convert('RGBA')).astype(np.float32) / 255
        la = ln[..., 3:4] * fade[..., None] * 0.9
        base = base * (1 - la) + np.array(INK) * la
    except (IndexError, TypeError): pass
    img = Image.fromarray(base.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(img)
    # progress bar + labels
    if THEME in ('eva', 'space'):
        frac = m.get('frac', max(t, 0) / END); bar = min(max([i for i in range(len(BS)) if BS[i] <= t + 1e-6] or [0]) + 1, len(S.get('BARS') or BS[:-1]))
        img = ET.hud(img, t, frac, bar, u, KY, BS, FD)
        if out is None: return img
        img.save(out); return
    pm = 26 * u; ph = 10 * u; frac = m.get('frac', t / END)
    d.rounded_rectangle([pm, pm, W - pm, pm + ph], radius=ph / 2, fill=(70, 70, 78))
    d.rounded_rectangle([pm, pm, pm + (W - 2 * pm) * frac, pm + ph], radius=ph / 2, fill=(245, 245, 250))
    bar = min(max([i for i in range(len(BS)) if BS[i] <= t + 1e-6] or [0]) + 1, len(S.get('BARS') or BS[:-1]))
    d.text((pm, pm + ph + 12 * u), f"{S.get('title', 'Rush E')}  ·  bar {bar}", font=F(34 * u), fill=(235, 235, 240))
    ta = max(t, 0); tl = f'{int(ta // 60)}:{int(ta % 60):02d}'
    d.text((W - pm, pm + ph + 12 * u), tl, font=F(34 * u), fill=(170, 170, 180), anchor='ra')
    if port:
        lx = pm; ly = H - 70 * u
        for hd, lab in (('R', 'right hand'), ('L', 'left hand')):
            d.rounded_rectangle([lx, ly, lx + 34 * u, ly + 22 * u], radius=6 * u, fill=HC[hd][0], outline=INK, width=2)
            d.text((lx + 44 * u, ly + 11 * u), lab, font=F(30 * u), fill=(220, 220, 228), anchor='lm'); lx += 230 * u
    if out is None: return img
    img.save(out)

if __name__ == '__main__':
    meta = json.load(open(OUT + 'toon_meta.json'))
    for nm in (sys.argv[1:] or meta):
        compose(nm, meta, f'/workspace/toon/{nm}.png'); print('ok', nm)
