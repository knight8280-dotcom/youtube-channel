"""Builds the soundtrack for the plant operators Short.

All music and sound effects are synthesized here (no stock audio), then the
ElevenLabs voice lines are placed on the timeline from timeline.json.
Output: ../audio/mix.wav (48 kHz stereo, not loudness-normalized yet).
"""
import json
import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 48000
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TL = json.loads((HERE / "timeline.json").read_text())
N = int(TL["duration"] * SR)
rng = np.random.default_rng(1234)

voice_bus = np.zeros((N, 2))
music_bus = np.zeros((N, 2))
amb_bus = np.zeros((N, 2))   # beds that duck under dialogue (alarm, rain, hum...)
sfx_bus = np.zeros((N, 2))   # one-shot hits that never duck


# ---------------------------------------------------------------- helpers
def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def place(bus, sig, t0, gain=1.0, pan=0.0):
    """Add mono or stereo signal to a bus at time t0 (seconds)."""
    if sig.ndim == 1:
        left = np.cos((pan + 1) * np.pi / 4)
        right = np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * left * 1.4142, sig * right * 1.4142], axis=1)
    i0 = int(t0 * SR)
    if i0 >= N:
        return
    n = min(len(sig), N - i0)
    bus[i0:i0 + n] += sig[:n] * gain


def band(x, lo=None, hi=None, order=4):
    """Zero-phase FFT band filter with smooth (Butterworth-shaped) skirts."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if lo:
        g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    if hi:
        g *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
    return np.fft.irfft(X * g, len(x))


def env_adsr(n, a=0.005, d=0.1, s=0.7, r=0.1):
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r * SR)
    s_n = max(n - a_n - d_n - r_n, 0)
    e = np.concatenate([np.linspace(0, 1, a_n, endpoint=False), np.linspace(1, s, d_n, endpoint=False),
                        np.full(s_n, s), np.linspace(s, 0, r_n)])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def saw(freq, dur, harmonics_to=3000):
    t = tvec(dur)
    out = np.zeros_like(t)
    k = 1
    while k * freq < harmonics_to:
        out += np.sin(2 * np.pi * k * freq * t) / k
        k += 1
    return out * 0.6


def norm(x, peak=1.0):
    m = np.max(np.abs(x))
    return x if m == 0 else x / m * peak


def read_wav(path):
    with wave.open(str(path)) as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
        if w.getnchannels() == 2:
            data = data.reshape(-1, 2).mean(axis=1)
        assert w.getframerate() == SR, path
    return data


# ---------------------------------------------------------------- instruments
def pluck(freq, dur=0.5, decay=6.0):
    t = tvec(dur)
    tone = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) + 0.12 * np.sin(6 * np.pi * freq * t)
    return tone * np.exp(-decay * t) * (1 - np.exp(-t * 500))


def marimba(freq, dur=0.4):
    t = tvec(dur)
    return (np.sin(2 * np.pi * freq * t) * np.exp(-9 * t) + 0.3 * np.sin(2 * np.pi * 4 * freq * t) * np.exp(-30 * t)) * (1 - np.exp(-t * 800))


def kick(dur=0.35, f0=120, f1=45):
    t = tvec(dur)
    f = f1 + (f0 - f1) * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) + band(rng.standard_normal(len(t)), 2000, 8000) * np.exp(-t * 200) * 0.2


def snare(dur=0.18):
    t = tvec(dur)
    return band(rng.standard_normal(len(t)), 900, 7000) * np.exp(-t * 28) * 0.7 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 35) * 0.4


def hat(dur=0.05):
    t = tvec(dur)
    return band(rng.standard_normal(len(t)), 7000, None) * np.exp(-t * 90)


def tom(dur=0.4, f0=150, f1=80):
    t = tvec(dur)
    f = f1 + (f0 - f1) * np.exp(-t * 12)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)


def pad(freqs, dur, attack=0.6, release=1.0, cutoff=2200):
    n = int(dur * SR)
    out = np.zeros(n)
    for f in freqs:
        for det in (-0.004, 0.0, 0.004):
            out += saw(f * (1 + det), dur, harmonics_to=4000)[:n]
    out = band(out, 60, cutoff, order=2)
    return norm(out, 1.0) * env_adsr(n, attack, 0.3, 0.85, release)


def brass(freq, dur, cutoff=1400):
    n = int(dur * SR)
    tone = saw(freq, dur) + 0.6 * saw(freq * 1.003, dur) + 0.5 * saw(freq / 2, dur)
    return norm(band(tone[:n], 50, cutoff, 2), 1.0) * env_adsr(n, 0.03, 0.15, 0.75, 0.25)


# ---------------------------------------------------------------- sound effects
def whoosh(dur=0.45):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    nz = band(rng.standard_normal(n), 300, 5000, 2)
    e = np.sin(np.pi * t) ** 2.5
    return norm(nz * e, 1.0)


def pop():
    t = tvec(0.09)
    f = 300 + 700 * np.exp(-t * 60)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 45)


def boom(dur=1.3):
    t = tvec(dur)
    f = 42 + 60 * np.exp(-t * 8)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    s = np.tanh(2.5 * s) * np.exp(-t * 2.8)
    return s + band(rng.standard_normal(len(t)), 80, 1500) * np.exp(-t * 40) * 0.5


def crickets(dur):
    t = tvec(dur)
    out = np.zeros_like(t)
    for f, period, off in ((4700, 0.62, 0.0), (5200, 0.81, 0.27)):
        gate = (((t + off) % period) < 0.16).astype(float)
        am = (np.sin(2 * np.pi * 32 * t) > 0).astype(float)
        out += np.sin(2 * np.pi * f * t) * gate * am * 0.5
    return band(out, 3000, 8000) * env_adsr(len(t), 0.3, 0.1, 1.0, 0.4)


def klaxon(dur):
    t = tvec(dur)
    period = 0.625
    freq = np.where((t % period) < period / 2, 720.0, 960.0)
    ph = 2 * np.pi * np.cumsum(freq) / SR
    sq = sum(np.sin(k * ph) / k for k in (1, 3, 5, 7))
    am = 0.75 + 0.25 * np.sin(2 * np.pi * 1.6 * t)
    return np.tanh(1.8 * sq) * am * env_adsr(len(t), 0.02, 0.05, 1.0, 0.3)


def rain(dur):
    n = int(dur * SR)
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    X /= np.sqrt(np.maximum(f, 20) / 20)  # pinkish
    r = np.fft.irfft(X, n)
    r = band(r, 250, 9000)
    drops = np.zeros(n)
    idx = rng.integers(0, n - 400, int(dur * 90))
    for i in idx:
        drops[i:i + 300] += rng.uniform(0.2, 1.0) * np.exp(-np.arange(300) / 40) * rng.choice([-1, 1])
    r = norm(r, 1.0) + band(drops, 1500, 9000) * 0.6
    return norm(r, 1.0)


def hiss(dur):
    n = int(dur * SR)
    return norm(band(rng.standard_normal(n), 2500, 12000), 1.0) * env_adsr(n, 0.04, 0.4, 0.55, 0.9)


def squelch(start=True):
    if start:
        t = tvec(0.09)
        beep = np.sin(2 * np.pi * 1250 * t) * 0.6
        nz = band(rng.standard_normal(int(0.12 * SR)), 800, 4000) * 0.5
        return np.concatenate([beep, nz * np.exp(-np.arange(len(nz)) / SR * 25)])
    nz = band(rng.standard_normal(int(0.22 * SR)), 600, 5000)
    return nz * np.exp(-np.arange(len(nz)) / SR * 12) * 0.7


def tick():
    n = int(0.03 * SR)
    return band(rng.standard_normal(n), 2500, 9000) * np.exp(-np.arange(n) / SR * 300)


def birds(dur):
    t = tvec(dur)
    out = np.zeros_like(t)
    for _ in range(int(dur * 4)):
        start = rng.uniform(0, dur - 0.3)
        length = rng.uniform(0.06, 0.14)
        tt = tvec(length)
        f0, f1 = rng.uniform(2800, 4200), rng.uniform(4200, 6500)
        if rng.random() < 0.5:
            f0, f1 = f1, f0
        f = f0 + (f1 - f0) * tt / length
        chirp = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / length) ** 2
        i = int(start * SR)
        out[i:i + len(chirp)] += chirp * rng.uniform(0.3, 1.0)
    return out


def slurp(dur=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    nz = band(rng.standard_normal(n), 700, 2600)
    gurgle = 0.55 + 0.45 * np.sin(2 * np.pi * (14 + 6 * np.sin(2 * np.pi * 1.3 * t)) * t)
    return norm(nz * gurgle * env_adsr(n, 0.15, 0.2, 0.8, 0.25), 1.0)


def riser(dur):
    n = int(dur * SR)
    return norm(band(rng.standard_normal(n), 3000, 14000), 1.0) * np.linspace(0, 1, n) ** 3


def room_tone(dur):
    n = int(dur * SR)
    return norm(band(rng.standard_normal(n), 40, 260, 2), 1.0) * 0.6 + np.sin(2 * np.pi * 60 * np.arange(n) / SR) * 0.15


# ---------------------------------------------------------------- music
def comedic_bed(t0, t1, gain):
    """Bouncy pizzicato/marimba loop, 112 BPM, C-Am-F-G."""
    beat = 60 / 112
    chords = [(130.81, (523.25, 659.25, 783.99)), (110.0, (440.0, 523.25, 659.25)),
              (87.31, (349.23, 440.0, 523.25)), (98.0, (392.0, 493.88, 587.33))]
    k = 0
    t = t0
    while t < t1 - 0.05:
        bar = (k // 8) % 4
        root, tones = chords[bar]
        e = k % 8
        if e in (0, 4):
            place(music_bus, pluck(root, 0.6, 5) * 0.9, t, gain)
            place(music_bus, kick(0.25, 100, 50) * 0.5, t, gain)
        if e in (2, 6):
            place(music_bus, pluck(root * 1.5, 0.4, 7) * 0.5, t, gain)
            place(music_bus, snare() * 0.25, t, gain)
        if e % 2 == 1:
            place(music_bus, marimba(tones[(k // 2) % 3], 0.35) * 0.55, t, gain, pan=0.3 if e in (1, 5) else -0.3)
        place(music_bus, hat() * 0.12, t, gain, pan=0.2)
        k += 1
        t += beat / 2


def action_bed(t0, t1, gain):
    """Driving 140 BPM D-minor ostinato with kicks and toms."""
    beat = 60 / 140
    roots = [73.42, 58.27, 65.41, 73.42]  # D2 Bb1 C2 D2
    s = 0
    t = t0
    while t < t1 - 0.05:
        bar = (s // 16) % 4
        root = roots[bar]
        pos = s % 16
        n_len = beat / 4
        note = saw(root * (2 if pos in (3, 7, 11, 14) else 1), n_len * 0.95, 1800)
        note *= np.exp(-np.arange(len(note)) / SR * 14) * (1.0 if pos % 4 == 0 else 0.65)
        place(music_bus, note * 0.5, t, gain)
        if pos % 4 == 0:
            place(music_bus, kick() * 0.9, t, gain)
        if pos in (4, 12):
            place(music_bus, snare() * 0.6, t, gain)
        if pos in (10, 14, 15) and bar % 2 == 1:
            place(music_bus, tom(0.35, 170 if pos == 10 else 130) * 0.6, t, gain, pan=-0.4 if pos == 14 else 0.4)
        if pos % 2 == 0:
            place(music_bus, hat() * 0.18, t, gain, pan=0.3)
        if pos == 0:
            stab = pad([root * 4, root * 4 * 1.189, root * 4 * 1.498], beat * 0.9, attack=0.01, release=0.15, cutoff=3000)
            place(music_bus, stab * 0.35, t, gain)
        s += 1
        t += beat / 4


# ---------------------------------------------------------------- build timeline
# Voices
for v in TL["voice"]:
    path = ROOT / "audio" / "clean" / f"{v['file']}.wav"
    sig = read_wav(path)
    if v.get("radio"):
        tmp = ROOT / "audio" / "clean" / f"{v['file']}_radio.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-af",
                        "highpass=f=380,lowpass=f=3000,volume=2.5,asoftclip=type=tanh,volume=0.7", str(tmp)], check=True)
        sig = read_wav(tmp)
        place(sfx_bus, squelch(True), v["t"] - 0.22, 0.35)
        place(sfx_bus, squelch(False), v["t"] + len(sig) / SR + 0.02, 0.3)
        sig = sig + band(rng.standard_normal(len(sig)), 1000, 5000) * 0.015  # radio static bed
    rms = np.sqrt(np.mean(sig ** 2))
    sig = np.tanh(sig * (0.11 / max(rms, 1e-4)) * 1.2) / 1.2  # level-match lines, soft-limit peaks
    place(voice_bus, sig, v["t"], 1.0)

# Music
comedic_bed(0.0, 22.70, 0.30)
comedic_bed(25.70, 32.80, 0.30)
action_bed(37.20, 47.60, 0.26)
place(music_bus, pad([146.83, 185.0, 220.0, 293.66], 4.6, attack=0.5, release=2.0), 47.60, 0.18)   # D major "unit stable"
place(music_bus, pad([146.83, 185.0, 220.0, 293.66, 369.99], 6.4, attack=0.15, release=1.6, cutoff=3200), 59.80, 0.24)  # finale
place(music_bus, brass(146.83, 1.6) * 0.5 + brass(220.0, 1.6) * 0.4 + brass(293.66, 1.6) * 0.35, 59.80, 0.28)
for k, tt in enumerate((59.80, 61.30, 62.80, 64.30)):
    place(music_bus, kick(0.6, 90, 40) * 0.9, tt, 0.35)
    place(music_bus, tom(0.8, 110, 60) * 0.7, tt + 0.01, 0.3)

# Sound effects
place(sfx_bus, whoosh(0.5), 0.0, 0.35, pan=-0.3)
for i in range(3):
    place(sfx_bus, pop(), 0.12 + i * 0.2, 0.28)
place(sfx_bus, pop(), 0.97, 0.3)
for tt in (2.80, 10.80, 18.90, 29.40, 44.60, 59.80):  # flash cuts
    place(sfx_bus, whoosh(0.4), tt - 0.2, 0.35, pan=0.3)
for tt in (2.85, 10.85, 18.95, 29.45):  # department chip pops
    place(sfx_bus, pop(), tt + 0.12, 0.25)
place(amb_bus, crickets(3.0), 22.70, 0.16)
place(sfx_bus, pop(), 27.75, 0.3)  # sticky note pops in
# "dun dun dunnn" right after the Q-word whisper (zoom punches in scene.js hit at the same times)
for off, freq, dur in ((0.0, 110.0, 0.26), (0.30, 110.0, 0.26), (0.60, 87.31, 1.3)):
    place(sfx_bus, brass(freq, dur) * 0.7 + brass(freq * 2, dur) * 0.3, 34.95 + off, 0.5)
    place(sfx_bus, boom(0.9) * 0.8, 34.95 + off, 0.35)
# 2:47 AM card: typewriter clicks then clock ticks
for i in range(7):
    place(sfx_bus, tick(), 35.80 + i * 0.065, 0.22)
for tt in (36.30, 36.80):
    place(sfx_bus, tick() * 1.5, tt, 0.4)
place(sfx_bus, boom(1.2), 37.20, 0.4)
place(amb_bus, klaxon(4.4), 37.20, 0.12)
r = rain(10.6)
r[:int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))
fade = np.ones(len(r))
fade[int(5.9 * SR):] = np.linspace(1, 0.35, len(r) - int(5.9 * SR))
fade[-int(0.6 * SR):] *= np.linspace(1, 0, int(0.6 * SR))
place(amb_bus, r * fade, 41.50, 0.22)
place(amb_bus, hiss(2.8), 44.60, 0.20, pan=0.4)
place(sfx_bus, boom(1.0), 44.60, 0.4)
place(sfx_bus, whoosh(0.4), 51.80, 0.25)
for i in range(7):
    place(sfx_bus, tick(), 52.00 + i * 0.065, 0.3)
place(amb_bus, birds(3.0), 52.20, 0.06, pan=0.4)
place(sfx_bus, slurp(1.0), 57.45, 0.16)
place(sfx_bus, riser(0.9), 58.90, 0.15)
place(sfx_bus, boom(1.4), 59.80, 0.4)
# control room hum under indoor scenes
place(amb_bus, room_tone(35.8), 0.0, 0.02)
place(amb_bus, room_tone(6.6), 53.2, 0.02)

# ---------------------------------------------------------------- duck music under dialogue and mix
venv = np.abs(voice_bus).max(axis=1)
hop = SR // 100
env = venv[: len(venv) // hop * hop].reshape(-1, hop).max(axis=1)
env = np.lib.stride_tricks.sliding_window_view(np.pad(env, (12, 12)), 25).max(axis=1)  # hold +/-120 ms
env = np.convolve(env, np.ones(15) / 15, mode="same")  # smooth the gain changes
act = np.interp(np.arange(N), np.arange(len(env)) * hop, np.clip(env / 0.08, 0, 1))
duck = 1 - 0.6 * act          # music: about -8 dB under dialogue
duck_amb = 1 - 0.75 * act     # alarm / rain / steam: about -12 dB under dialogue
mix = voice_bus + music_bus * duck[:, None] + amb_bus * duck_amb[:, None] + sfx_bus
peak = np.max(np.abs(mix))
mix = np.tanh(mix / peak * 1.1) / np.tanh(1.1) * 0.95

out = ROOT / "audio" / "mix.wav"
with wave.open(str(out), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("wrote", out, f"{N / SR:.1f}s", "pre-limit peak", round(float(peak), 3))

# ---------------------------------------------------------------- level report (dialogue vs. bed)
if __name__ == "__main__":
    bed = music_bus * duck[:, None] + amb_bus * duck_amb[:, None] + sfx_bus
    def db(x):
        return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
    for v in TL["voice"]:
        d = len(read_wav(ROOT / "audio" / "clean" / f"{v['file']}.wav")) / SR
        a, b = int(v["t"] * SR), int((v["t"] + d) * SR)
        print(f"{v['file']:11s} voice {db(voice_bus[a:b]):6.1f} dB   bed {db(bed[a:b]):6.1f} dB   gap {db(voice_bus[a:b]) - db(bed[a:b]):5.1f}")
