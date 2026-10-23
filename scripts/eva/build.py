import json, re, subprocess, mido, numpy as np
from score import B, TEMPO, SHORT, UNCERTAIN
NAMES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
def pit(s):
    m = re.fullmatch(r'([A-G])(b|#)?(-?\d)', s); assert m, s
    return 12 * (int(m.group(3)) + 1) + NAMES[m.group(1)] + {'b': -1, '#': 1, None: 0}[m.group(2)]
def voice(txt, shift=0):
    ev = []; t = 0.0; tie = None
    for tok in txt.split():
        if tok.startswith('S'):
            n = 4 if tok.startswith('S4:') else 6; ps = tok.split(':', 1)[1].split(',')
            for p in ps: ev.append([t, 1 / n, [pit(p) + shift]]); t += 1 / n
            continue
        nm, d = tok.split(':'); tied = d.endswith('~'); d = float(d.rstrip('~'))
        if nm != 'r':
            ps = [pit(p) + shift for p in nm.split('+')]
            if tie is not None and sorted(tie[2]) == sorted(ps): tie[1] += d
            else: ev.append([t, d, ps])
            tie = ev[-1] if tied else None
        else: tie = None
        t += d
    return ev, t
notes = []; t0 = 0.0; bar_sec = []; nb = max(B)
for b in range(1, nb + 1):
    spec = B[b]; shift = 0
    if spec[0] == 'DOWN': spec = B[spec[1]]; shift = -12
    bs = 60 / TEMPO[b]; L = SHORT.get(b, 4); bar_sec.append(t0)
    for hand, txt, sh in (('R', spec[0], shift), ('L', spec[1], 0)):
        for v in txt.split(' | '):
            ev, tl = voice(v, sh)
            assert abs(tl - L) < 1e-6, (b, hand, tl, L, v)
            for s, d, ps in ev:
                for p in ps: notes.append([t0 + s * bs, d * bs, p, hand, b, len(ps)])
    t0 += L * bs
bar_sec.append(t0)
# ---- fingering ----
WH = [0, 2, 4, 5, 7, 9, 11]
def widx(p): return (p // 12) * 7 + min(range(7), key=lambda i: abs(WH[i] - p % 12) if WH[i] <= p % 12 else 99)
BLK = (1, 3, 6, 8, 10)
def tcost(p1, f1, p2, f2, hand):
    d = widx(p2) - widx(p1)
    if hand == 'L': d = -d
    fd = f2 - f1; c = 0.0
    if p1 == p2: return 0.0 if f1 == f2 else 1.0
    if f1 == f2: return 6.0
    if d > 0 and fd > 0: c += max(0, d - 2 * fd - (1 if 1 in (f1, f2) else 0)) * 2 + max(0, fd - d) * 1.5
    elif d < 0 and fd < 0: c += max(0, -d - 2 * -fd - (1 if 1 in (f1, f2) else 0)) * 2 + max(0, -fd + d) * 1.5
    elif d > 0 and f2 == 1: c += 2 + max(0, d - 3) * 2          # thumb under
    elif d < 0 and f1 == 1 and f2 in (2, 3, 4): c += 2 + max(0, -d - 3) * 2   # cross over
    else: c += 8 + abs(d)
    if f2 == 1 and p2 % 12 in BLK: c += 3
    if f2 == 5 and p2 % 12 in BLK: c += 1
    if f2 == 4: c += 0.3
    return c
def finger_hand(hn, hand):
    groups = {}
    for n in hn: groups.setdefault(round(n[0], 4), []).append(n)
    keys = sorted(groups); run = []
    def solve(run, prev):
        if not run: return
        INF = 1e9; cost = [[INF] * 6 for _ in run]; bp = [[0] * 6 for _ in run]
        for f in range(1, 6):
            cost[0][f] = tcost(prev[0], prev[1], run[0][2], f, hand) if prev else (0 if f in (1, 2) else 1)
        for i in range(1, len(run)):
            for f in range(1, 6):
                best = min(range(1, 6), key=lambda g: cost[i - 1][g] + tcost(run[i - 1][2], g, run[i][2], f, hand))
                cost[i][f] = cost[i - 1][best] + tcost(run[i - 1][2], best, run[i][2], f, hand); bp[i][f] = best
        f = min(range(1, 6), key=lambda g: cost[-1][g])
        for i in range(len(run) - 1, -1, -1): run[i].append(f); f = bp[i][f]
    prev = None
    for k in keys:
        g = sorted(groups[k], key=lambda n: n[2])
        if len(g) > 1:
            solve(run, prev); run = []
            fs = {2: [1, 5], 3: [1, 3, 5], 4: [1, 2, 3, 5]}.get(len(g), [1, 2, 3, 4, 5])
            if len(g) == 2 and abs(g[1][2] - g[0][2]) <= 4: fs = [1, 3]
            if hand == 'L': fs = fs[::-1] if len(g) != 2 or abs(g[1][2] - g[0][2]) > 4 else [3, 1]
            for n, f in zip(g, fs): n.append(f)
            top = g[-1] if hand == 'R' else g[0]
            prev = (top[2], top[-1])
        else: run.append(g[0])
    solve(run, prev)
for h in 'RL': finger_hand([n for n in notes if n[3] == h], h)
notes.sort(key=lambda n: (n[0], n[2]))
T0 = 3.0
out = [[round(s, 5), round(d, 5), p, str(f), h, b] for s, d, p, h, b, k, f in notes]
D = dict(FPS=30, LO=24, HI=100, KY=410,
         full=dict(notes=out, T0=T0, END=T0 + bar_sec[-1] + 3.0, bar_sec=bar_sec, BARS=list(range(1, nb + 1)), title="Cruel Angel's Thesis"))
json.dump(D, open('eva_notes.json', 'w'))
# ---- MIDI (real time, tempo 60 so 1 beat = 1 s, 960 tpq) ----
m = mido.MidiFile(ticks_per_beat=960); tr = mido.MidiTrack(); m.tracks.append(tr)
tr.append(mido.MetaMessage('set_tempo', tempo=1000000)); tr.append(mido.Message('program_change', program=0))
evs = []
for s, d, p, h, b, k, f in notes:
    v = (96 if k == 1 else 82) if h == 'R' else 70
    if b <= 12: v -= 18
    if b in range(55, 71) or b in (28, 29, 46, 47, 48, 51, 52, 53, 54): v += 10
    v = max(30, min(120, v))
    evs += [(s, 1, p, v), (s + d * 0.95, 0, p, 0)]
evs.sort(key=lambda e: (e[0], e[1])); last = 0
for s, on, p, v in evs:
    tk = int(round(s * 960)); tr.append(mido.Message('note_on' if on else 'note_off', note=p, velocity=v, time=tk - last)); last = tk
m.save('eva_full.mid')
subprocess.run(['fluidsynth', '-ni', '-q', '-g', '0.6', '-r', '44100', '-F', 'eva_raw.wav', '/usr/share/sounds/sf2/FluidR3_GM.sf2', 'eva_full.mid'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'eva_raw.wav', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '44100', 'eva_full.wav'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'eva_full.wav', '-c:a', 'libmp3lame', '-b:a', '192k', 'eva_full.mp3'], check=True)
# fingering text
with open('fingering.md', 'w') as fh:
    fh.write("# Cruel Angel's Thesis - fingering (auto-generated, 1=thumb ... 5=pinky)\n\n")
    for b in range(1, nb + 1):
        r = ' '.join(f"{n[2]}({n[6]})" for n in notes if n[4] == b and n[3] == 'R')
        l = ' '.join(f"{n[2]}({n[6]})" for n in notes if n[4] == b and n[3] == 'L')
        fh.write(f"bar {b}: RH {r}\n        LH {l}\n")
print('notes', len(notes), 'bars', nb, 'music s', round(bar_sec[-1], 2), 'END', D['full']['END'])
