import cairosvg, numpy as np, wave
def n(num,o=0,u=0,d=False,acc=''): return dict(num=num,o=o,u=u,d=d,acc=acc)
D=lambda u=0,d=False:n('6',-1,u,d)
A1=[D(),n('1',0,1,True),D(2),n('0',0,2),D(2),n('2',0,1),D(1),n('5',-1,1)]
A2=[D(),n('3',0,1,True),D(2),n('0',0,2),D(2),n('4',0,1),n('3',0,1),n('1',0,1)]
A3=[D(1),n('3',0,1),n('6',0,1),D(2),n('5',-1,2),n('0',0,2),n('5',-1,2),n('3',-1,1),n('7',-1,1),dict(D(1),tie=True)]
A4=[dict(D(),tiein=True),n('-'),D(),D()]
G=lambda:n('2',0,1); Fs=lambda:n('1',0,1,acc='#'); F=lambda:n('1',0,1); E=lambda u=0:n('7',-1,u)
B9=[G(),Fs(),F(),F(),E(),E()]
B10=[G(),Fs(),F(),F(),E(1),E(1),E()]
B12=[G(),Fs(),F(),F(),D(),D()]
A3e=[dict(t) for t in A3]
END1=[dict(D(),tiein=True),n('-'),n('-'),n('-')]
END2=[n('6',0),n('-'),n('-'),n('-')]
lines=[("Main theme (play twice)",[A1,A2,A3,A4],'rep'),
       ("Middle part (play twice)",[B9,B10,B9,B12],'rep'),
       ("Ending",[A1,A2,A3e],'cont'),("",[END1,END2],'end')]
# ---------- sheet ----------
W=1320; out=[]; A=out.append
H=160+len(lines)*150+130
A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="DejaVu Sans">')
A(f'<rect width="{W}" height="{H}" fill="white"/>')
A(f'<text x="{W/2}" y="55" font-size="34" text-anchor="middle" font-weight="bold">Axel F</text>')
A(f'<text x="{W/2}" y="88" font-size="17" text-anchor="middle">Crazy Frog melody, number notation for cello</text>')
A(f'<text x="60" y="130" font-size="20" font-weight="bold">1 = F     4/4     ♩ = 120</text>')
def wid(t): return 24 if t['u']==2 else (32 if t['u']==1 else 52)
y0=220
for li,(title,bars,kind) in enumerate(lines):
    y=y0+li*150
    A(f'<text x="60" y="{y-55}" font-size="15" fill="#555">{title}</text>')
    x=60
    if kind=='rep': A(f'<text x="{x}" y="{y}" font-size="30" font-weight="bold">‖:</text>'); x+=40
    tie=None
    for bi,bar in enumerate(bars):
        for t in bar:
            w=wid(t)+(14 if t['d'] else 0); cxp=x+w/2
            if t['num']=='-': A(f'<text x="{cxp}" y="{y}" font-size="28" text-anchor="middle">–</text>')
            else:
                A(f'<text x="{cxp}" y="{y}" font-size="28" text-anchor="middle">{t["num"]}</text>')
                if t['acc']: A(f'<text x="{cxp-13}" y="{y-14}" font-size="17" text-anchor="middle">♯</text>')
                if t['d']: A(f'<circle cx="{cxp+14}" cy="{y-9}" r="3"/>')
                if t['o']==-1: A(f'<circle cx="{cxp}" cy="{y+14+t["u"]*6}" r="3"/>')
                if t['o']==1: A(f'<circle cx="{cxp}" cy="{y-30}" r="3"/>')
                if t.get('tie'): tie=cxp
                if t.get('tiein'):
                    sx=tie if tie else x-30
                    A(f'<path d="M {sx} {y-30} Q {(sx+cxp)/2} {y-55} {cxp} {y-30}" stroke="black" fill="none" stroke-width="2"/>')
            for k in range(t['u']):
                A(f'<line x1="{x+3}" y1="{y+6+k*6}" x2="{x+w-3}" y2="{y+6+k*6}" stroke="black" stroke-width="2"/>')
            x+=w
        x+=12
        last=bi==len(bars)-1
        if last and kind=='rep': A(f'<text x="{x-4}" y="{y}" font-size="30" font-weight="bold">:‖</text>')
        elif last and kind=='cont': A(f'<line x1="{x}" y1="{y-26}" x2="{x}" y2="{y+6}" stroke="black" stroke-width="2"/>')
        elif last: A(f'<line x1="{x}" y1="{y-26}" x2="{x}" y2="{y+6}" stroke="black" stroke-width="2"/><line x1="{x+6}" y1="{y-26}" x2="{x+6}" y2="{y+6}" stroke="black" stroke-width="5"/>')
        else: A(f'<line x1="{x}" y1="{y-26}" x2="{x}" y2="{y+6}" stroke="black" stroke-width="2"/>')
        x+=18
    print(title, 'width', x)
leg=["How to read it: 1=F  2=G  3=A  4=B♭  5=C  6=D  7=E,  0 = rest,  ♯1 = F♯.",
"Dot below = one octave lower, dot above = one octave higher.",
"No line = 1 beat,  one line = ½ beat,  two lines = ¼ beat.  A dot after a number adds half its length.",
"–  holds the note one more beat.  A curve is a tie: keep holding, don't play the note again.",
"On cello: 6̣ = D3 (open D string),  5̣ = C3 (open C string),  3̣ = A2 (open A on the... A string is A3, so this is A2 on the G string),  6 = D4."]
leg[4]="On cello: low-dot 6 = D3 (open D string), low-dot 5 = C3 and low-dot 3 = A2 (G string), 3 = A3 (open A string), 6 = D4."
for i,l in enumerate(leg): A(f'<text x="60" y="{H-120+i*24}" font-size="15">{l}</text>')
A('</svg>')
open('axelf_cello.svg','w').write('\n'.join(out))
cairosvg.svg2png(url='axelf_cello.svg', write_to='axelf_cello.png', scale=1.2)
# ---------- audio ----------
off={'1':0,'2':2,'3':4,'4':5,'5':7,'6':9,'7':11}
def events(bars):
    ev=[]
    for bar in bars:
        for t in bar:
            dur=[1,.5,.25][t['u']]*(1.5 if t['d'] else 1)
            if t['num']=='-' or t.get('tiein'): (ev[-1] if ev else seq[-1])[1]+=dur; continue
            p=None if t['num']=='0' else 53+off[t['num']]+12*t['o']+(1 if t['acc'] else 0)
            ev.append([p,dur])
    return ev
seq=[]
for title,bars,kind in lines:
    e=events(bars); seq+= e+[list(x) for x in e] if kind=='rep' else e
sr=44100; beat=0.5; audio=[]
for p,d in seq:
    T=d*beat; t=np.arange(int(sr*T))/sr
    if p is None: audio.append(np.zeros_like(t)); continue
    f=440*2**((p-69)/12)
    vib=1+0.004*np.sin(2*np.pi*5.5*t)*np.clip(t*4,0,1)
    ph=2*np.pi*f*np.cumsum(vib)/sr
    s=sum((1/k)**1.1*np.sin(k*ph) for k in range(1,12))
    env=np.minimum(1,t/0.03)*np.minimum(1,(T-t)/0.06)*(0.85+0.15*np.exp(-t*6))
    audio.append(s*env)
a=np.concatenate(audio); a=a/np.abs(a).max()*0.8
with wave.open('axelf_cello.wav','wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((a*32767).astype(np.int16).tobytes())
print('seconds',len(a)/sr)
# ---------- MIDI (cello) ----------
import mido
mid=mido.MidiFile(ticks_per_beat=480); tr=mido.MidiTrack(); mid.tracks.append(tr)
tr.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(120)))
tr.append(mido.Message('program_change',program=42,channel=0))
tr.append(mido.Message('control_change',control=91,value=60))
rest=0
for p,d in seq:
    ticks=int(round(d*480))
    if p is None: rest+=ticks; continue
    gap=min(30,ticks//6)
    tr.append(mido.Message('note_on',note=p,velocity=96,time=rest))
    tr.append(mido.Message('note_off',note=p,velocity=0,time=ticks-gap))
    rest=gap
tr.append(mido.Message('note_off',note=0,velocity=0,time=rest+480))
mid.save('axelf_cello.mid')
