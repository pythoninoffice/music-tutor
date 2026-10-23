# usage: python toon_video.py <tag> <hand_dir> <wav> <out.mp4> [workers]
import sys, os, json, shutil, subprocess, multiprocessing as mp
tag, hd, wav, out = sys.argv[1:5]; NW = int(sys.argv[5]) if len(sys.argv) > 5 else max(2, os.cpu_count() - 2)
os.environ['TOON_TAG'] = tag
import numpy as np
import toon_compose as TC
TR = json.load(open(os.path.join(hd, 'track.json'))); N = TR['N']; WK = 0.0235
def job(f):
    kw = TR['kw'][f]; m = dict(W=TR['W'], H=TR['H'], KYtop=TR['KYtop'], cx=TR['cx'][f], scale=TR['W'] / (kw * WK),
                               t=f / TC.D['FPS'] - TR['T0'], frac=f / (N - 1))
    return TC.compose(m, None, None, handp=os.path.join(hd, f'hand_{f:05d}.png')).tobytes()
if __name__ == '__main__':
    TC.set_tag(tag); T0 = TC.S['T0']; END = TC.S['END']; FPS = TC.D['FPS']
    FF = shutil.which('ffmpeg') or r'C:\Program Files\ffmpeg\bin\ffmpeg.exe'
    p = subprocess.Popen([FF, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f"{TR['W']}x{TR['H']}", '-r', str(FPS), '-i', '-',
        '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '22', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k', '-af', f'adelay={int(round(T0 * 1000))}:all=1,apad', '-t', f'{N / FPS:.3f}', '-movflags', '+faststart', out],
        stdin=subprocess.PIPE)
    with mp.Pool(NW) as pool:
        for i, b in enumerate(pool.imap(job, range(N), chunksize=4)):
            p.stdin.write(b)
            if i % 300 == 0: print('frame', i, '/', N, flush=True)
    p.stdin.close(); p.wait(); print('DONE', out, p.returncode)
