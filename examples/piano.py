import make, mido
seq=[]
def ev(bars):
    global seq
    make.seq=seq
    e=make.events(bars); seq+=e; return e
main=[make.A1,make.A2,make.A3,make.A4]; mid_=[make.B9,make.B10,make.B9,make.B12]
endb=[make.A1,make.A2,make.A3e,make.END1,make.END2]
blk=[(50,4),(50,4),(45,2),(48,2),(50,4)]  # D3, D3, A2+C3, D3 per 4 bars
bass=[]
ev(main); bass.append((None,16))
for _ in range(2): ev(main); bass+= [(50,4),(50,4),(45,2),(48,2),(50,4)]
for _ in range(2): ev(mid_); bass+= [(50,4),(50,4),(45,2),(48,2),(50,4)]
ev(endb); bass+= [(50,4),(50,4),(45,2),(48,2),(50,4),(50,4)]
m=mido.MidiFile(ticks_per_beat=480)
def track(notes,shift,vel,ch,legato):
    t=mido.MidiTrack(); m.tracks.append(t)
    t.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(120)))
    t.append(mido.Message('program_change',program=0,channel=ch))
    rest=0
    for p,d in notes:
        k=int(round(d*480))
        if p is None: rest+=k; continue
        g=0 if legato else min(40,k//5)
        t.append(mido.Message('note_on',note=p+shift,velocity=vel,time=rest,channel=ch))
        t.append(mido.Message('note_off',note=p+shift,velocity=0,time=k-g,channel=ch)); rest=g
track(seq,12,100,0,False)
track(bass,0,70,1,True)
m.save('axelf_piano.mid')
print(sum(d for _,d in seq), sum(d for _,d in bass))
