import sys, os, subprocess, numpy as np, mido
from PIL import Image, ImageDraw, ImageFont
os.chdir('/workspace/axelf')
import make
BPM = float(sys.argv[1]) if len(sys.argv) > 1 else 120
TAG = sys.argv[2] if len(sys.argv) > 2 else 'tutorial'
SPB = 60.0 / BPM
NM = ['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B']
def name(p): return NM[p % 12] + str(p // 12 - 1)

# ---------------- fingering (right hand, per bar, pitches after +12) ----------------
# fingers listed for every *struck* note in the bar (rests/ties skipped)
RH = {
 'A1': [2,4,2,2,5,2,1],            # D4 F4 D4 D4 G4 D4 C4   (thumb on C4: C1 D2 E3 F4 G5)
 'A2': [1,5,1,1,5,4,2],            # D4 A4 D4 D4 Bb4 A4 F4 (thumb on D4, stretch 5 to Bb)
 'A3': [1,3,5,3,2,2,1,4,3],        # D4 A4 D5 | D4 C4 C4 A3 E4 D4~ (shift: thumb on A3)
 'A4': [3,3],                      # (D4 held) D4 D4
 'B9': [5,4,3,3,2,2],              # G4 F#4 F4 F4 E4 E4  (thumb on D4)
 'B10':[5,4,3,3,2,2,2],            # G4 F#4 F4 F4 E4 E4 E4
 'B12':[5,4,3,3,1,1],              # G4 F#4 F4 F4 D4 D4
 'A3e':[1,3,5,3,2,2,1,4,3],
 'END1':[],
 'END2':[3],                       # D5 (move hand up, middle finger)
}
LH = {50:1, 48:3, 45:5}            # D3=1, C3=3, A2=5
main = ['A1','A2','A3','A4']; midp = ['B9','B10','B9','B12']; endb = ['A1','A2','A3e','END1','END2']

def bars_events(names):
    """events for a block, with per-bar struck-note bookkeeping"""
    make.seq = []
    ev = make.events([getattr(make, n) for n in names])
    # count struck notes per bar to attach fingers in order
    fingers = []; barnames = []
    for n in names:
        fingers += RH[n]; barnames += [n]*len(RH[n])
    struck = [e for e in ev if e[0] is not None]
    assert len(struck) == len(fingers), (names, len(struck), len(fingers))
    out = []; k = 0
    for p, d in ev:
        if p is None: out.append((None, d, 0, ''))
        else: out.append((p + 12, d, fingers[k], barnames[k])); k += 1
    return out

rh = []; lh = []; sections = []
blk = [(50,4),(50,4),(45,2),(48,2),(50,4)]
def add(names, label, bass):
    b0 = sum(d for _, d, _, _ in rh)
    sections.append((b0, label))
    rh.extend(bars_events(names)); 
    if bass: lh.extend(bass)
add(main, 'Main theme – right hand only', [(None,16)])
for i in range(2): add(main, f'Main theme – both hands ({i+1}/2)', blk)
for i in range(2): add(midp, f'Middle part ({i+1}/2)', blk)
add(endb, 'Ending', blk + [(50,4)])

# note list: (start_beat, dur_beats_sounding, pitch, finger, hand)
notes = []
t = 0
for p, d, f, bn in rh:
    if p is not None:
        g = min(40, int(round(d*480))//5) / 480
        notes.append((t, d - g, p, f, 'R'))
    t += d
total_beats = t
t = 0
for p, d in lh:
    if p is not None: notes.append((t, d - 0.03, p, LH[p], 'L'))
    t += d
notes.sort()

# ---------------- MIDI + audio at this tempo ----------------
m = mido.MidiFile(ticks_per_beat=480)
for hand, ch, vel in (('R',0,100),('L',1,70)):
    tr = mido.MidiTrack(); m.tracks.append(tr)
    tr.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))
    tr.append(mido.Message('program_change', program=0, channel=ch))
    msgs = []
    for s, d, p, f, h in notes:
        if h != hand: continue
        msgs.append((int(round(s*480)), 1, p)); msgs.append((int(round((s+d)*480)), 0, p))
    msgs.sort(); last = 0
    for tk, on, p in msgs:
        tr.append(mido.Message('note_on' if on else 'note_off', note=p, velocity=vel if on else 0, time=tk-last, channel=ch)); last = tk
mid = f'axelf_piano_{int(BPM)}bpm.mid'; m.save(mid)
wav = f'piano_{int(BPM)}bpm.wav'
subprocess.run(['fluidsynth','-ni','-q','-g','0.8','-r','44100','-F',wav,'/usr/share/sounds/sf2/FluidR3_GM.sf2',mid], check=True)

# ---------------- layout ----------------
W, H, FPS = 1280, 720, 30
LO, HI = 41, 77          # F2 .. F5
whites = [p for p in range(LO, HI+1) if p % 12 not in (1,3,6,8,10)]
WW = W / len(whites)
KY, KH = 545, 175        # keyboard top / height
BH, BW = 105, WW*0.62    # black key height/width
HEAD = 112
PXB = 120                # pixels per beat
def keyx(p):
    if p % 12 in (1,3,6,8,10):
        i = whites.index(p-1); return (i+1)*WW - BW/2, BW, True
    i = whites.index(p); return i*WW, WW, False
F = lambda s, b=True: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if b else ''), s)
f_big, f_num, f_key, f_small, f_sec, f_title = F(26), F(22), F(30), F(15, False), F(24), F(52)
COL = {'R': (60,200,110), 'L': (255,150,40)}
DARK = {'R': (20,110,55), 'L': (170,85,0)}

def draw_hand(d, x, y, hand, s=1.0, lab=True):
    # simple hand: palm + 5 fingers, numbered. hand 'R' thumb on left, 'L' thumb on right
    c = COL[hand]
    d.rounded_rectangle([x, y+38*s, x+92*s, y+86*s], 14*s, fill=c, outline=(255,255,255), width=2)
    lens = [30, 44, 50, 44, 34]  # finger 1..5 lengths (thumb shorter)
    for k in range(5):
        i = k if hand == 'R' else 4-k   # i = left-to-right slot
        fx = x + 3*s + i*18*s
        L = lens[k]*s; top = y+40*s-L
        if k == 0: top += 14*s
        d.rounded_rectangle([fx, top, fx+16*s, y+48*s], 8*s, fill=c, outline=(255,255,255), width=2)
        d.text((fx+8*s, top+12*s), str(k+1), font=F(int(14*s)), fill=(0,0,0), anchor='mm')
    if lab: d.text((x+46*s, y+98*s), 'Right hand' if hand=='R' else 'Left hand', font=f_small, fill=c, anchor='mm')

# static background
bg = Image.new('RGB', (W, H), (24,26,34)); d = ImageDraw.Draw(bg)
d.rectangle([0,0,W,HEAD], fill=(14,15,20))
for i, p in enumerate(whites):          # lane guides at each C and F
    if p % 12 in (0,5): d.line([i*WW, HEAD, i*WW, KY], fill=(40,43,55))
d.text((16, 14), 'Axel F – piano tutorial', font=F(26), fill=(255,255,255))
d.text((16, 50), f'♩ = {int(BPM)}' + ('   (slow practice)' if BPM < 100 else ''), font=F(18, False), fill=(190,190,200))
d.text((16, 78), '1 thumb · 2 index · 3 middle · 4 ring · 5 pinky', font=f_small, fill=(170,170,180))
draw_hand(d, W-235, 2, 'L', 0.95); draw_hand(d, W-120, 2, 'R', 0.95)
d.line([0, KY-1, W, KY-1], fill=(200,40,40), width=3)

def frame_img(tb, sec_label):
    im = bg.copy(); d = ImageDraw.Draw(im)
    d.text((W/2 - 40, 40), sec_label, font=f_sec, fill=(255,230,120), anchor='mm')
    pressed = {}
    # falling bars (black-key bars drawn after white ones)
    vis = [n for n in notes if n[0] < tb + (KY-HEAD)/PXB + 0.1 and n[0]+n[1] > tb]
    for s, du, p, f, h in sorted(vis, key=lambda n: keyx(n[2])[2]):
        x, w, blk = keyx(p)
        if s - 0.02 <= tb < s+du: pressed[p] = (f, h)
        y1 = KY - (s - tb)*PXB; y0 = KY - (s + du - tb)*PXB
        y1c = min(y1, KY); y0c = max(y0, HEAD)
        if y1c <= y0c: continue
        pad = 3 if blk else 5
        d.rounded_rectangle([x+pad, y0c, x+w-pad, y1c], 7, fill=COL[h], outline=DARK[h], width=2)
        cy = min(y1c - 15, max(y0c + 15, y1 - 15))
        if y1 > HEAD + 15:
            cx = x + w/2; r = 13
            d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(255,255,255))
            d.text((cx, cy), str(f), font=f_num, fill=(0,0,0), anchor='mm')
    # keyboard
    for i, p in enumerate(whites):
        x0 = i*WW
        fill = COL[pressed[p][1]] if p in pressed else (250,250,250)
        d.rectangle([x0, KY, x0+WW-1, KY+KH], fill=fill, outline=(60,60,60))
        if p % 12 == 0 or p in pressed:
            d.text((x0+WW/2, KY+KH-14), name(p), font=f_small, fill=(90,90,90) if p not in pressed else (0,0,0), anchor='mm')
        if p in pressed:
            d.text((x0+WW/2, KY+BH+30), str(pressed[p][0]), font=f_key, fill=(0,0,0), anchor='mm')
    for p in range(LO, HI+1):
        x, w, blk = keyx(p)
        if not blk: continue
        fill = COL[pressed[p][1]] if p in pressed else (20,20,20)
        d.rectangle([x, KY, x+w, KY+BH], fill=fill)
        if p in pressed:
            d.text((x+w/2, KY+BH-24), str(pressed[p][0]), font=F(24), fill=(0,0,0), anchor='mm')
            d.text((x+w/2, KY+BH-6), name(p), font=F(11, False), fill=(0,0,0), anchor='mm')
    d.rectangle([0, KY, W, KY+4], fill=(150,30,30))
    return im

def title_img():
    im = Image.new('RGB', (W, H), (14,15,20)); d = ImageDraw.Draw(im)
    d.text((W/2, 140), 'Axel F – piano tutorial', font=f_title, fill=(255,255,255), anchor='mm')
    d.text((W/2, 205), f'Crazy Frog melody · ♩ = {int(BPM)}' + (' · slow practice' if BPM < 100 else ''), font=F(26, False), fill=(200,200,210), anchor='mm')
    d.text((W/2, 265), 'Finger numbers:  1 = thumb   2 = index   3 = middle   4 = ring   5 = pinky', font=F(26), fill=(255,230,120), anchor='mm')
    draw_hand(d, W/2-330, 320, 'L', 2.4, False); draw_hand(d, W/2+110, 320, 'R', 2.4, False)
    d.text((W/2-220, 600), 'LEFT hand = orange', font=F(26), fill=COL['L'], anchor='mm')
    d.text((W/2+220, 600), 'RIGHT hand = green', font=F(26), fill=COL['R'], anchor='mm')
    d.text((W/2, 660), 'The number on each falling bar tells you which finger to use.', font=F(22, False), fill=(200,200,210), anchor='mm')
    return im

TITLE = 3.0
FALL = (KY-HEAD)/PXB * SPB
T0 = TITLE + FALL + 0.3          # time (s) when beat 0 hits the keyboard
END = T0 + total_beats*SPB + 2.5
nfr = int(END*FPS)
out = f'axelf_piano_{TAG}.mp4'
ff = subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
    '-i', wav,
    '-map','0:v','-map','1:a','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p',
    '-c:a','aac','-b:a','192k','-af',f'adelay={int(round(T0*1000))}:all=1,apad','-t',f'{END:.3f}','-movflags','+faststart', out], stdin=subprocess.PIPE)
ti = title_img().tobytes()
checks = {}
for i in range(nfr):
    t = i / FPS
    if t < TITLE: buf = ti
    else:
        tb = (t - T0) / SPB
        lab = ''
        for b0, l in sections:
            if tb >= b0 - 1: lab = l
        if tb < -1: lab = 'Get ready…'
        im = frame_img(tb, lab); buf = im.tobytes()
        for cb in (0.1, 18.1, 56.1, 84.6):
            if abs(tb - cb) < 0.5/FPS/SPB*1.0001 and cb not in checks:
                checks[cb] = 1; im.save(f'frames_check/{TAG}_beat{cb:g}.png')
    ff.stdin.write(buf)
ff.stdin.close(); ff.wait()
print('done', out, 'T0', T0, 'END', END, 'beats', total_beats)
# fingering text
if TAG == 'tutorial':
    L = ['# Axel F – piano fingering', '', '1 = thumb, 2 = index, 3 = middle, 4 = ring, 5 = pinky. Key: F major / D minor.', '',
         '## Left hand (bass)', '', '- D3 = **1** (thumb), C3 = **3** (middle), A2 = **5** (pinky). Keep the hand resting over A2–D3.',
         '- Pattern for each 4 bars (from the 2nd time through the main theme): D3 (whole) | D3 (whole) | A2 (half) C3 (half) | D3 (whole)', '',
         '## Right hand (melody)', '']
    desc = {'A1':'Main bar 1 – thumb on C4','A2':'Main bar 2 – thumb on D4, stretch pinky to Bb','A3':'Main bar 3 – jump up, then move thumb to A3',
            'A4':'Main bar 4 (keep holding the D4 from bar 3 for 2 beats, then)','B9':'Middle bars 1 & 3 – thumb on D4, chromatic walk down 5-4-3','B10':'Middle bar 2','B12':'Middle bar 4',
            'A3e':'Ending bar 3 (same as main bar 3)','END2':'Final note'}
    for k in ['A1','A2','A3','A4','B9','B10','B12','A3e','END2']:
        make.seq = [[None,0]]
        ev = make.events([getattr(make, k)])
        ps = [name(p+12) for p, d in ev if p is not None]
        if k == 'A4': ps = ps[-2:] if len(ps) > 2 else ps
        pair = '  '.join(f'{a}({b})' for a, b in zip(ps, RH[k]))
        L.append(f'- **{desc[k]}:** {pair}')
    L += ['', 'Order: main theme ×3 (1st time right hand alone, then with left hand), middle part ×2, ending (main bars 1–3, hold D4, then D5).',
          'Tip: repeated notes (F4 F4, E4 E4, D4 D4) use the same finger – just lift and replay.']
    open('fingering.md','w').write('\n'.join(L) + '\n')
