import sys, os, subprocess, wave, numpy as np, mido
from PIL import Image, ImageDraw, ImageFont
os.chdir('/workspace/axelf')
import make
BPM = float(sys.argv[1]) if len(sys.argv) > 1 else 120
TAG = sys.argv[2] if len(sys.argv) > 2 else 'tutorial'
SPB = 60.0 / BPM
NM = ['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B']
def name(p): return NM[p % 12] + str(p // 12 - 1)
STR = ['C','G','D','A']; OPEN = [36, 43, 50, 57]
# 1st position cello fingering: pitch -> (string index, finger label, semitones above open)
FING = {45:(1,'1',2), 48:(1,'4',5), 50:(2,'0',0), 52:(2,'1',2), 53:(2,'2',3), 54:(2,'3',4),
        55:(2,'4',5), 57:(3,'0',0), 58:(3,'b1',1), 62:(3,'4',5)}
SCOL = [(170,110,230), (70,150,255), (60,200,110), (255,150,40)]
DARK = [tuple(int(c*0.55) for c in s) for s in SCOL]

blocks = [(['A1','A2','A3','A4'], 'Main theme (1/2)'), (['A1','A2','A3','A4'], 'Main theme (2/2)'),
          (['B9','B10','B9','B12'], 'Middle part (1/2)'), (['B9','B10','B9','B12'], 'Middle part (2/2)'),
          (['A1','A2','A3e','END1','END2'], 'Ending')]
notes = []; sections = []; t = 0
for names, label in blocks:
    sections.append((t, label)); make.seq = []
    for p, d in make.events([getattr(make, n) for n in names]):
        if p is not None:
            g = min(30, int(round(d*480))//6) / 480
            notes.append((t, d - g, p))
        t += d
total_beats = t

# ---------- MIDI + audio ----------
m = mido.MidiFile(ticks_per_beat=480); tr = mido.MidiTrack(); m.tracks.append(tr)
tr.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))
tr.append(mido.Message('program_change', program=42, channel=0))
tr.append(mido.Message('control_change', control=91, value=60))
last = 0
for s, d, p in notes:
    a, b = int(round(s*480)), int(round((s+d)*480))
    tr.append(mido.Message('note_on', note=p, velocity=100, time=a-last))
    tr.append(mido.Message('note_off', note=p, velocity=0, time=b-a)); last = b
mid = f'axelf_cello_{int(BPM)}bpm.mid'; m.save(mid)
raw = f'cello_{int(BPM)}bpm_raw.wav'; wav = f'cello_{int(BPM)}bpm.wav'
subprocess.run(['fluidsynth','-ni','-q','-g','1.0','-r','44100','-F',raw,'/usr/share/sounds/sf2/FluidR3_GM.sf2',mid], check=True)
with wave.open(raw) as w:
    ch = w.getnchannels(); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
a *= (32767 * 10**(-1/20)) / np.abs(a).max()      # normalize to -1 dBFS peak
with wave.open(wav, 'wb') as w:
    w.setnchannels(ch); w.setsampwidth(2); w.setframerate(44100); w.writeframes(a.astype(np.int16).tobytes())

# ---------- layout ----------
W, H, FPS = 1280, 720, 30
HEAD = 110; HIT = 560
LX0, LW = 40, 175               # 4 lanes
PXB = 120
F = lambda s, b=True: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if b else ''), s)
f_num, f_nm, f_sec = F(24), F(18), F(24)
# fingerboard panel (vertical, nut at top, player's view: C G D A left->right)
FBX0, FBX1, FBY0, FBY1 = 830, 1170, 228, 700
SX = [FBX0 + 55 + i*(FBX1-FBX0-110)/3 for i in range(4)]
SEMI = 62                       # px per semitone along string
def spot(si, semi):
    return SX[si], FBY0 + 18 + (semi - 0.5)*SEMI if semi else FBY0 - 4

bg = Image.new('RGB', (W, H), (24,26,34)); d = ImageDraw.Draw(bg)
d.rectangle([0,0,W,HEAD], fill=(14,15,20))
d.text((16, 12), 'Axel F – cello tutorial', font=F(26), fill=(255,255,255))
d.text((16, 48), f'♩ = {int(BPM)}' + ('   (slow practice)' if BPM < 100 else '') + '   ·   1st position, no shifts', font=F(18, False), fill=(190,190,200))
d.text((16, 78), '0 open · 1 index · 2 middle · 3 ring · 4 pinky · b1 = 1st finger stretched back', font=F(15, False), fill=(170,170,180))
for i in range(4):
    x = LX0 + i*LW
    d.rectangle([x+3, HEAD, x+LW-3, HIT], fill=(30,33,43))
    d.line([x+LW/2, HEAD, x+LW/2, HIT], fill=DARK[i], width=2)
d.line([LX0, HIT, LX0+4*LW, HIT], fill=(220,60,60), width=3)
# fingerboard
d.text(((FBX0+FBX1)/2, 132), 'Left hand – 1st position', font=F(20), fill=(255,255,255), anchor='mm')
d.polygon([(FBX0+15, FBY0), (FBX1-15, FBY0), (FBX1, FBY1), (FBX0, FBY1)], fill=(30,24,20), outline=(90,70,55))
d.rectangle([FBX0+10, FBY0-10, FBX1-10, FBY0], fill=(230,220,190))   # nut
for semi, lab in ((1,'b1'),(2,'1'),(3,'2'),(4,'3'),(5,'4')):
    y = spot(0, semi)[1]
    d.line([FBX0+20, y, FBX1-20, y], fill=(60,52,45), width=1)
    d.text((FBX0-6, y), lab, font=F(16), fill=(150,140,130), anchor='rm')
d.text((FBX0-6, FBY0-5), '0', font=F(16), fill=(150,140,130), anchor='rm')
for i in range(4):
    d.line([SX[i], FBY0-10, SX[i], FBY1], fill=(200,200,200), width=5-i)
    d.text((SX[i], FBY0-28), STR[i], font=F(22), fill=SCOL[i], anchor='mm')
# finger spots for every note used (faint)
for p, (si, fl, semi) in FING.items():
    if semi:
        x, y = spot(si, semi); d.ellipse([x-17, y-17, x+17, y+17], outline=(110,100,90), width=2)

def frame_img(tb, lab):
    im = bg.copy(); d = ImageDraw.Draw(im)
    d.text((660, 40), lab, font=f_sec, fill=(255,230,120), anchor='mm')
    active = None
    vis = [n for n in notes if n[0] < tb + (HIT-HEAD)/PXB + 0.1 and n[0]+n[1] > tb]
    for s, du, p in vis:
        si, fl, semi = FING[p]
        if s - 0.02 <= tb < s + du: active = (p, si, fl, semi)
        y1 = HIT - (s - tb)*PXB; y0 = HIT - (s + du - tb)*PXB
        y1c, y0c = min(y1, HIT), max(y0, HEAD)
        if y1c <= y0c: continue
        x = LX0 + si*LW
        d.rounded_rectangle([x+22, y0c, x+LW-22, y1c], 8, fill=SCOL[si], outline=DARK[si], width=2)
        if y1 > HEAD + 15:
            cy = min(y1c - 15, max(y0c + 15, y1 - 15)); cx = x + 58
            d.ellipse([cx-14, cy-14, cx+14, cy+14], fill=(255,255,255))
            d.text((cx, cy), fl, font=F(22 if len(fl) == 1 else 16), fill=(0,0,0), anchor='mm')
            d.text((cx+22, cy), name(p), font=f_nm, fill=(0,0,0), anchor='lm')
    # string boxes under hit line
    for i in range(4):
        x = LX0 + i*LW; on = active and active[1] == i
        d.rounded_rectangle([x+8, HIT+12, x+LW-8, H-12], 12, fill=SCOL[i] if on else (40,43,55), outline=SCOL[i], width=3)
        d.text((x+LW/2, HIT+36), f'{STR[i]} string', font=F(20), fill=(0,0,0) if on else SCOL[i], anchor='mm')
        if on:
            d.text((x+LW/2, HIT+82), active[2], font=F(44), fill=(0,0,0), anchor='mm')
            d.text((x+LW/2, HIT+128), name(active[0]), font=F(20), fill=(0,0,0), anchor='mm')
        else:
            d.text((x+LW/2, HIT+90), f'open = {name(OPEN[i])}', font=F(17, False), fill=(150,150,160), anchor='mm')
    if active:
        p, si, fl, semi = active
        d.line([SX[si], FBY0-10, SX[si], FBY1], fill=SCOL[si], width=7)
        x, y = spot(si, semi)
        r = 24
        d.ellipse([x-r, y-r, x+r, y+r], fill=SCOL[si], outline=(255,255,255), width=3)
        d.text((x, y), fl, font=F(24 if len(fl) == 1 else 18), fill=(0,0,0), anchor='mm')
        msg = f'{name(p)}: {STR[si]} string, ' + ('open string (0)' if fl == '0' else ('1st finger stretched back (b1)' if fl == 'b1' else f'finger {fl}'))
        d.text(((FBX0+FBX1)/2, 162), msg, font=F(16, False), fill=(230,230,230), anchor='mm')
    return im

def hand_legend(d, x, y):
    lines = [('0', 'open string (no finger)'), ('1', 'index finger'), ('2', 'middle finger'), ('3', 'ring finger'),
             ('4', 'pinky'), ('b1', 'index stretched back a half step')]
    for i, (n, t) in enumerate(lines):
        d.ellipse([x, y+i*46, x+36, y+36+i*46], fill=(255,255,255))
        d.text((x+18, y+18+i*46), n, font=F(20 if len(n) == 1 else 15), fill=(0,0,0), anchor='mm')
        d.text((x+50, y+18+i*46), t, font=F(22, False), fill=(230,230,230), anchor='lm')
def title_img():
    im = Image.new('RGB', (W, H), (14,15,20)); d = ImageDraw.Draw(im)
    d.text((W/2, 90), 'Axel F – cello tutorial', font=F(52), fill=(255,255,255), anchor='mm')
    d.text((W/2, 150), f'Crazy Frog melody · ♩ = {int(BPM)}' + (' · slow practice' if BPM < 100 else '') + ' · all in 1st position', font=F(24, False), fill=(200,200,210), anchor='mm')
    d.text((160, 205), 'Left-hand finger numbers', font=F(26), fill=(255,230,120))
    hand_legend(d, 170, 255)
    d.text((760, 205), 'Strings (low → high)', font=F(26), fill=(255,230,120))
    for i in range(4):
        d.rounded_rectangle([770+i*100, 255, 850+i*100, 345], 10, fill=SCOL[i])
        d.text((810+i*100, 285), STR[i], font=F(34), fill=(0,0,0), anchor='mm')
        d.text((810+i*100, 325), name(OPEN[i]), font=F(18, False), fill=(0,0,0), anchor='mm')
    d.text((760, 380), 'Each falling bar lands on the string\nto play, labeled with finger + note.', font=F(22, False), fill=(200,200,210), spacing=8)
    return im

TITLE = 3.0
FALL = (HIT-HEAD)/PXB * SPB
T0 = TITLE + FALL + 0.3
END = T0 + total_beats*SPB + 2.5
out = f'axelf_cello_{TAG}.mp4'
ff = subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
    '-i', wav, '-map','0:v','-map','1:a','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p',
    '-c:a','aac','-b:a','192k','-af',f'adelay={int(round(T0*1000))}:all=1,apad','-t',f'{END:.3f}','-movflags','+faststart', out], stdin=subprocess.PIPE)
ti = title_img(); ti.save(f'frames_check/cello_{TAG}_title.png'); ti = ti.tobytes()
done = set()
for i in range(int(END*FPS)):
    t = i / FPS
    if t < TITLE: ff.stdin.write(ti); continue
    tb = (t - T0) / SPB
    lab = 'Get ready…' if tb < -1 else ''
    for b0, l in sections:
        if tb >= b0 - 1: lab = l
    im = frame_img(tb, lab)
    for cb in (0.1, 5.1, 37.1, 44.6):
        if cb not in done and tb >= cb: done.add(cb); im.save(f'frames_check/cello_{TAG}_beat{cb:g}.png')
    ff.stdin.write(im.tobytes())
ff.stdin.close(); ff.wait()
print('done', out, 'T0', T0, 'END', END, 'beats', total_beats)

if TAG == 'tutorial':
    L = ['# Axel F – cello fingering', '', 'Everything stays in **1st position** – no shifts needed.',
         'Fingers: 0 = open string, 1 = index, 2 = middle, 3 = ring, 4 = pinky, b1 = 1st finger stretched back a half step (backward extension).',
         'Strings: C (C2), G (G2), D (D3), A (A3). Format below: note (string, finger).', '',
         '## Notes used', '']
    for p in sorted(FING):
        si, fl, _ = FING[p]; L.append(f'- {name(p)} = {STR[si]} string, finger {fl}')
    L += ['', '## Bar by bar', '']
    desc = [('A1','Main bar 1'),('A2','Main bar 2'),('A3','Main bar 3'),('A4','Main bar 4 (keep holding the D3 from bar 3, then)'),
            ('B9','Middle bars 1 & 3'),('B10','Middle bar 2'),('B12','Middle bar 4'),('A3e','Ending bar 3'),('END2','Final note')]
    for k, ds in desc:
        make.seq = [[None, 0]]
        ps = [p for p, d in make.events([getattr(make, k)]) if p is not None]
        L.append(f'- **{ds}:** ' + '  '.join(f'{name(p)} ({STR[FING[p][0]]} string, {FING[p][1]})' for p in ps))
    L += ['', 'Order: main theme ×2, middle part ×2, ending (main bars 1–3, hold D3 a bar, then D4).',
          'Tips: the middle part (G3 F#3 F3 E3 = D4 D3 D2 D1) is a walk down one finger at a time on the D string.',
          'For Bb3 (A b1) slide the 1st finger back a half step from its normal B spot; let it come back for E3/A2 afterwards.']
    open('cello_fingering.md', 'w').write('\n'.join(L) + '\n')
