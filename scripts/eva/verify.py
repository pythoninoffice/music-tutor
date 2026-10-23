import sys, subprocess, numpy as np
def load(p):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', '8000', '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(r, np.float32)
v, w = load(sys.argv[1]), load(sys.argv[2]); T0 = float(sys.argv[3])
pad = np.concatenate([np.zeros(int(T0 * 8000), np.float32), w])
n = min(len(v), len(pad)); a, b = v[:n], pad[:n]
F = np.fft.rfft(a, 2 * n) * np.conj(np.fft.rfft(b, 2 * n)); c = np.fft.irfft(F)
lag = int(np.argmax(c)); lag = lag - 2 * n if lag > n else lag
print(f'offset {lag / 8:.2f} ms (+ = video audio late)')
