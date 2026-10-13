"""宇宙增量游戏 · 主循环背景音乐（代码合成）
风格：慢速、宏大的太空氛围（弦乐垫 + 无词合唱 + 低音长音），
背景点缀 16-bit 方波琶音，低沉缓慢的鼓点。D 小调，75 BPM，16 小节无缝循环。
"""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
import wave, sys

SR = 44100
BPM = 75
BEAT = 60 / BPM
BAR = BEAT * 4
BARS = 16
LOOP = BAR * BARS                 # 51.2 秒
TAIL = 5.0                        # 渲染尾巴，最后折回开头实现无缝循环
N = int((LOOP + TAIL) * SR)
rng = np.random.default_rng(7)

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def lp(x, f, order=2): return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, order=2): return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, order=2): return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)

L = np.zeros(N); R = np.zeros(N)
def add(sig, start, pan=0.0, gain=1.0):
    i = int(start * SR)
    if i >= N: return
    sig = sig[: N - i] * gain
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(sig)] += sig * l; R[i:i + len(sig)] += sig * r

def env_ar(n, a, r):
    """线性起音 a 秒、余弦释放 r 秒（释放从 n 末尾往回算）"""
    e = np.ones(n); na = int(a * SR); nr = int(r * SR)
    e[:na] = np.linspace(0, 1, na)
    e[n - nr:] *= 0.5 * (1 + np.cos(np.linspace(0, np.pi, nr)))
    return e

# ---------------- 和弦进行：Dm – B♭ – F – C，每个两小节 ----------------
CHORDS = [
    dict(root=38, pad=[50, 57, 62, 65], choir=[62, 65, 69]),   # Dm
    dict(root=34, pad=[46, 53, 58, 62], choir=[62, 65, 70]),   # B♭
    dict(root=41, pad=[53, 57, 60, 65], choir=[60, 65, 69]),   # F
    dict(root=36, pad=[48, 55, 60, 64], choir=[60, 64, 67]),   # C
]
SEQ = [CHORDS[(b // 2) % 4] for b in range(BARS)]
SEGS = [(i * 2 * BAR, CHORDS[i % 4]) for i in range(BARS // 2)]   # (开始时间, 和弦)
SEG_LEN = 2 * BAR

# ---------------- 弦乐 / 合成器长音垫 ----------------
def saw(f, n, det=0.0):
    t = np.arange(n) / SR
    ph = (f * (1 + det) * t + rng.random()) % 1.0
    return 2 * ph - 1

for start, ch in SEGS:
    n = int((SEG_LEN + 1.6) * SR)
    e = env_ar(n, 1.6, 1.8)
    for k, m in enumerate(ch['pad']):
        f = hz(m)
        s = sum(saw(f, n, d) for d in (-0.004, 0.0, 0.0045)) / 3
        s = lp(s, 1400 + 300 * k)
        # 缓慢的音量起伏，像弦乐的弓
        t = np.arange(n) / SR
        s *= (0.85 + 0.15 * np.sin(2 * np.pi * 0.17 * t + k))
        add(s * e, start, pan=(-0.5, 0.5, -0.25, 0.3)[k], gain=0.075)

# ---------------- 无词合唱 "ah"：加法合成 + 共振峰 ----------------
FORM = [(800, 80, 1.0), (1150, 90, 0.5), (2900, 120, 0.12)]
def choir_voice(f0, n, seed):
    r = np.random.default_rng(seed)
    t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * (4.8 + r.random()) * t + r.random() * 6)
    drift = 1 + 0.002 * np.sin(2 * np.pi * 0.3 * t + r.random() * 6)
    phase = 2 * np.pi * np.cumsum(f0 * vib * drift) / SR
    out = np.zeros(n)
    for h in range(1, 30):
        fh = h * f0
        if fh > 5000: break
        amp = sum(g * np.exp(-0.5 * ((fh - fc) / bw) ** 2) for fc, bw, g in FORM) + 0.02 / h
        out += amp * np.sin(h * phase + r.random() * 6)
    return out

for idx, (start, ch) in enumerate(SEGS):
    swell = 0.55 if idx < 4 else 1.0          # 后半段合唱更饱满
    n = int((SEG_LEN + 1.6) * SR)
    e = env_ar(n, 2.2, 2.0)
    for k, m in enumerate(ch['choir']):
        v = sum(choir_voice(hz(m), n, idx * 31 + k * 7 + j) for j in range(3)) / 3
        add(v * e, start, pan=(-0.6, 0.0, 0.6)[k], gain=0.05 * swell)

# ---------------- 低音长音 ----------------
for start, ch in SEGS:
    n = int((SEG_LEN + 1.0) * SR)
    t = np.arange(n) / SR
    f = hz(ch['root'])
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.25 * lp(saw(f, n), 300)
    add(s * env_ar(n, 0.4, 1.0), start, gain=0.16)

# ---------------- 16-bit 方波琶音（带回声，降位深） ----------------
def square(f, n, duty=0.25):
    ph = (f * np.arange(n) / SR) % 1.0
    return np.where(ph < duty, 1.0, -1.0)

ARP = [0, 1, 2, 1, 2, 3, 2, 1]                      # 和弦音索引
step = BEAT / 2                                     # 八分音符
arp = np.zeros(N)
for b in range(BARS):
    ch = SEQ[b]
    tones = sorted(ch['pad'])[1:] + [ch['pad'][1] + 12]
    tones = [m + 12 for m in tones]
    vol = 0.35 if b < 8 else 0.7                    # 前半段很轻，后半段浮出来
    for s_i in range(8):
        m = tones[ARP[s_i] % len(tones)]
        n = int(0.32 * SR)
        e = np.exp(-np.arange(n) / SR / 0.09)
        note = square(hz(m), n) * e * vol
        i = int((b * BAR + s_i * step) * SR)
        arp[i:i + n] += note[: N - i]
arp = np.round(arp * 24) / 24                       # 降位深，芯片味
arp = lp(arp, 4200)
echo = np.zeros(N); d = int(BEAT * 0.75 * SR)       # 附点八分回声
for k in range(1, 5):
    echo[d * k:] += arp[: N - d * k] * (0.42 ** k)
add(arp, 0, pan=-0.35, gain=0.035)
add(echo, 0, pan=0.45, gain=0.03)

# ---------------- 鼓：低沉的太鼓 / 通鼓 + 轻踢鼓，后半段加轻沙锤 ----------------
def taiko(f0=110, f1=48, dur=0.9, bright=0.25):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.06)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.28)
    skin = lp(rng.standard_normal(n), 900) * np.exp(-t / 0.03) * bright
    return body + skin

def shaker():
    n = int(0.12 * SR); t = np.arange(n) / SR
    s = hp(rng.standard_normal(n), 6000) * np.exp(-t / 0.025)
    return np.round(s * 10) / 10                    # 粗糙的 bit 感

for b in range(BARS):
    t0 = b * BAR
    add(taiko(), t0, gain=0.55)                                   # 第 1 拍 重
    add(taiko(95, 45, 0.7, 0.15), t0 + 2 * BEAT, gain=0.38)       # 第 3 拍
    add(taiko(130, 70, 0.4, 0.3), t0 + 1.5 * BEAT, pan=0.3, gain=0.16)   # 第 2 拍反拍 轻
    if b % 2 == 1:                                                # 每两小节末尾一个小滚奏
        add(taiko(150, 80, 0.35, 0.3), t0 + 3.5 * BEAT, pan=-0.3, gain=0.2)
        add(taiko(170, 90, 0.35, 0.3), t0 + 3.75 * BEAT, pan=-0.3, gain=0.24)
    if b >= 8:
        for e8 in range(8):
            add(shaker(), t0 + e8 * BEAT / 2, pan=0.5, gain=0.035 if e8 % 2 else 0.02)

# ---------------- 混响：指数衰减噪声卷积 ----------------
def ir(seed, secs=3.8):
    r = np.random.default_rng(seed); n = int(secs * SR); t = np.arange(n) / SR
    x = r.standard_normal(n) * np.exp(-t / 1.1)
    return lp(x, 5000) / np.sqrt(np.sum(x ** 2))

wetL = fftconvolve(L, ir(1))[:N]; wetR = fftconvolve(R, ir(2))[:N]
L = L * 0.75 + wetL * 0.55; R = R * 0.75 + wetR * 0.55
L = hp(L, 30); R = hp(R, 30)

# ---------------- 无缝循环：把尾巴折回开头 ----------------
n_loop = int(LOOP * SR)
for ch in (L, R):
    ch[: N - n_loop] += ch[n_loop:]
L = L[:n_loop]; R = R[:n_loop]

out = np.stack([L, R], axis=1)
out = np.tanh(out / np.max(np.abs(out)) * 1.2) / np.tanh(1.2) * 0.89
pcm = (out * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('done', round(LOOP, 1), 's')
