"""Synthesize music + sound effects and mix them with an episode's voice lines.

    python3 engine/mix_audio.py videos/<episode>     -> <episode>/audio/mix.wav

Everything except the dialogue is generated here, so there is no stock audio to license.
Music styles (timeline "music" segments): comedy, fast, action, tense, chill, dreamy, none.
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
EP = Path(sys.argv[1]).resolve()
TL = json.loads((EP / "timeline.json").read_text())
N = int(TL["duration"] * SR) + SR // 2
rng = np.random.default_rng(1234)

voice_bus, music_bus, amb_bus, sfx_bus = (np.zeros((N, 2)) for _ in range(4))


# ---------------------------------------------------------------- helpers
def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def place(bus, sig, t0, gain=1.0, pan=0.0):
    if sig.ndim == 1:
        sig = np.stack([sig * np.cos((pan + 1) * np.pi / 4) * 1.4142, sig * np.sin((pan + 1) * np.pi / 4) * 1.4142], axis=1)
    i0 = int(max(t0, 0) * SR)
    if i0 >= N:
        return
    n = min(len(sig), N - i0)
    bus[i0:i0 + n] += sig[:n] * gain


def band(x, lo=None, hi=None, order=4):
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
    e = np.concatenate([np.linspace(0, 1, a_n, endpoint=False), np.linspace(1, s, d_n, endpoint=False), np.full(s_n, s), np.linspace(s, 0, r_n)])
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


def noise(dur):
    return rng.standard_normal(int(dur * SR))


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
    return (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) + 0.12 * np.sin(6 * np.pi * freq * t)) * np.exp(-decay * t) * (1 - np.exp(-t * 500))


def marimba(freq, dur=0.4):
    t = tvec(dur)
    return (np.sin(2 * np.pi * freq * t) * np.exp(-9 * t) + 0.3 * np.sin(2 * np.pi * 4 * freq * t) * np.exp(-30 * t)) * (1 - np.exp(-t * 800))


def rhodes(freq, dur=1.2):
    t = tvec(dur)
    return (np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * 2 * freq * t) * np.exp(-6 * t)) * np.exp(-2.2 * t) * (1 - np.exp(-t * 300)) * (1 + 0.06 * np.sin(2 * np.pi * 5 * t))


def kick(dur=0.35, f0=120, f1=45):
    t = tvec(dur)
    f = f1 + (f0 - f1) * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) + band(rng.standard_normal(len(t)), 2000, 8000) * np.exp(-t * 200) * 0.2


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
    return norm(band(out, 60, cutoff, order=2), 1.0) * env_adsr(n, attack, 0.3, 0.85, release)


def brass(freq, dur, cutoff=1400, vibrato=0.0):
    n = int(dur * SR)
    t = tvec(dur)
    if vibrato:
        ph = 2 * np.pi * np.cumsum(freq * (1 + vibrato * np.sin(2 * np.pi * 5.5 * t))) / SR
        tone = sum(np.sin(k * ph) / k for k in range(1, int(3000 / freq)))
    else:
        tone = saw(freq, dur) + 0.6 * saw(freq * 1.003, dur) + 0.5 * saw(freq / 2, dur)
    return norm(band(tone[:n], 50, cutoff, 2), 1.0) * env_adsr(n, 0.03, 0.15, 0.75, 0.25)


# ---------------------------------------------------------------- sound effects (one-shots unless noted)
def whoosh(dur=0.45):
    n = int(dur * SR)
    return norm(band(noise(dur), 300, 5000, 2) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2.5, 1.0)


def pop():
    t = tvec(0.09)
    return np.sin(2 * np.pi * np.cumsum(300 + 700 * np.exp(-t * 60)) / SR) * np.exp(-t * 45)


def boom(dur=1.3):
    t = tvec(dur)
    s = np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(42 + 60 * np.exp(-t * 8)) / SR)) * np.exp(-t * 2.8)
    return s + band(rng.standard_normal(len(t)), 80, 1500) * np.exp(-t * 40) * 0.5


def tick():
    n = int(0.03 * SR)
    return band(rng.standard_normal(n), 2500, 9000) * np.exp(-np.arange(n) / SR * 300)


def ding():
    t = tvec(1.2)
    return (np.sin(2 * np.pi * 1320 * t) + 0.4 * np.sin(2 * np.pi * 2640 * t)) * np.exp(-t * 4)


def clang():
    t = tvec(1.4)
    return norm(sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in ((410, 3), (1083, 4), (1716, 5), (2560, 7), (3390, 9))), 1.0)


def bang():
    return norm(boom(1.0) + np.pad(band(noise(0.25), 400, 9000) * np.exp(-tvec(0.25) * 18), (0, int(0.75 * SR))), 1.0)


def squelch(start=True):
    if start:
        t = tvec(0.09)
        nz = band(noise(0.12), 800, 4000) * 0.5
        return np.concatenate([np.sin(2 * np.pi * 1250 * t) * 0.6, nz * np.exp(-np.arange(len(nz)) / SR * 25)])
    nz = band(noise(0.22), 600, 5000)
    return nz * np.exp(-np.arange(len(nz)) / SR * 12) * 0.7


def slurp(dur=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    g = 0.55 + 0.45 * np.sin(2 * np.pi * (14 + 6 * np.sin(2 * np.pi * 1.3 * t)) * t)
    return norm(band(noise(dur), 700, 2600) * g * env_adsr(n, 0.15, 0.2, 0.8, 0.25), 1.0)


def riser(dur=1.0):
    n = int(dur * SR)
    return norm(band(noise(dur), 3000, 14000), 1.0) * np.linspace(0, 1, n) ** 3


def sting():
    """'dun dun DUNNN' dramatic reveal (about 2 s)."""
    out = np.zeros(int(2.4 * SR))
    for off, f, d in ((0.0, 110.0, 0.26), (0.30, 110.0, 0.26), (0.60, 87.31, 1.3)):
        s = brass(f, d) * 0.7 + brass(f * 2, d) * 0.3 + np.pad(boom(0.9), (0, max(0, int(d * SR) - int(0.9 * SR))))[:int(d * SR)] * 0.5
        i = int(off * SR)
        out[i:i + len(s)] += s
    return norm(out, 1.0)


def sad_trombone():
    out = np.zeros(int(3.0 * SR))
    for i, (f, d, v) in enumerate(((233.08, 0.42, 0), (220.0, 0.42, 0), (207.65, 0.42, 0), (196.0, 1.4, 0.03))):
        s = brass(f, d, cutoff=1100, vibrato=v)
        j = int(i * 0.45 * SR)
        out[j:j + len(s)] += s
    return norm(out, 1.0)


def record_scratch():
    t = tvec(0.45)
    f = 1800 * np.exp(-t * 6) + 200
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * band(rng.standard_normal(len(t)), 300, 6000) * np.exp(-t * 5)
    return norm(s, 1.0)


def phone_ring(dur=3.0):
    t = tvec(dur)
    on = ((t % 3.0) < 0.4) | (((t % 3.0) > 0.6) & ((t % 3.0) < 1.0))
    ring = (np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 480 * t)) * on
    buzz = np.sign(np.sin(2 * np.pi * 150 * t)) * 0.25 * on
    return norm(band(ring + buzz, 200, 4000), 1.0)


def bubble():
    t = tvec(0.25)
    return np.sin(2 * np.pi * np.cumsum(500 + 900 * t / 0.25) / SR) * np.exp(-t * 14)


# ---- ambience beds (have a duration, duck under dialogue)
def a_crickets(dur):
    t = tvec(dur)
    out = np.zeros_like(t)
    for f, period, off in ((4700, 0.62, 0.0), (5200, 0.81, 0.27)):
        out += np.sin(2 * np.pi * f * t) * (((t + off) % period) < 0.16) * (np.sin(2 * np.pi * 32 * t) > 0) * 0.5
    return band(out, 3000, 8000) * env_adsr(len(t), 0.3, 0.1, 1.0, 0.4)


def a_klaxon(dur):
    t = tvec(dur)
    freq = np.where((t % 0.625) < 0.3125, 720.0, 960.0)
    ph = 2 * np.pi * np.cumsum(freq) / SR
    return np.tanh(1.8 * sum(np.sin(k * ph) / k for k in (1, 3, 5, 7))) * (0.75 + 0.25 * np.sin(2 * np.pi * 1.6 * t)) * env_adsr(len(t), 0.02, 0.05, 1.0, 0.3)


def a_beeps(dur):
    t = tvec(dur)
    return np.sin(2 * np.pi * 2200 * t) * (((t % 0.5) < 0.08)) * 0.6 * env_adsr(len(t), 0.01, 0.05, 1.0, 0.1)


def a_rain(dur):
    n = int(dur * SR)
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    r = band(np.fft.irfft(X / np.sqrt(np.maximum(f, 20) / 20), n), 250, 9000)
    drops = np.zeros(n)
    for i in rng.integers(0, max(n - 400, 1), int(dur * 90)):
        drops[i:i + 300] += rng.uniform(0.2, 1.0) * np.exp(-np.arange(300) / 40) * rng.choice([-1, 1])
    return norm(norm(r) + band(drops, 1500, 9000) * 0.6) * env_adsr(n, 0.3, 0.1, 1.0, 0.6)


def a_hiss(dur):
    n = int(dur * SR)
    return norm(band(noise(dur), 2500, 12000)) * env_adsr(n, 0.04, 0.4, 0.6, 0.6)


def a_sizzle(dur):
    n = int(dur * SR)
    crackle = np.zeros(n)
    for i in rng.integers(0, max(n - 200, 1), int(dur * 400)):
        crackle[i:i + 60] += rng.uniform(-1, 1) * np.exp(-np.arange(60) / 10)
    return norm(band(noise(dur), 3000, 12000) * 0.4 + band(crackle, 2000, 10000)) * env_adsr(n, 0.1, 0.1, 1.0, 0.3)


def a_wind(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return norm(band(noise(dur), 150, 1200, 2) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.25 * t + 1.3 * np.sin(2 * np.pi * 0.11 * t)))) * env_adsr(n, 0.5, 0.1, 1.0, 0.6)


def a_birds(dur):
    t = tvec(dur)
    out = np.zeros_like(t)
    for _ in range(int(dur * 4)):
        length = rng.uniform(0.06, 0.14)
        tt = tvec(length)
        f0, f1 = rng.uniform(2800, 4200), rng.uniform(4200, 6500)
        if rng.random() < 0.5:
            f0, f1 = f1, f0
        chirp = np.sin(2 * np.pi * np.cumsum(f0 + (f1 - f0) * tt / length) / SR) * np.sin(np.pi * tt / length) ** 2
        i = int(rng.uniform(0, max(dur - 0.3, 0.01)) * SR)
        out[i:i + len(chirp)] += chirp[: len(out) - i] * rng.uniform(0.3, 1.0)
    return out


def a_snore(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    cyc = (t % 3.2) / 3.2
    e = np.where(cyc < 0.45, np.sin(np.pi * cyc / 0.45), 0) ** 2
    return norm(band(noise(dur), 80, 600, 2) * (1 + 0.8 * np.sin(2 * np.pi * 28 * t)) * e)


def a_room(dur):
    n = int(dur * SR)
    return norm(band(noise(dur), 40, 260, 2)) * 0.6 + np.sin(2 * np.pi * 60 * np.arange(n) / SR) * 0.15


def a_crowd(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    voices = sum(band(noise(dur), 250 + 80 * k, 1600 + 150 * k, 2) * (0.6 + 0.4 * np.sin(2 * np.pi * (0.7 + 0.3 * k) * t + k)) for k in range(4))
    return norm(voices) * env_adsr(n, 0.4, 0.1, 1.0, 0.5)


SFX = {"whoosh": whoosh, "pop": pop, "boom": boom, "tick": tick, "ding": ding, "clang": clang, "bang": bang,
       "slurp": slurp, "riser": riser, "sting": sting, "sad_trombone": sad_trombone, "record_scratch": record_scratch,
       "phone_ring": phone_ring, "bubble": bubble}
AMB = {"crickets": a_crickets, "klaxon": a_klaxon, "beeps": a_beeps, "rain": a_rain, "hiss": a_hiss, "sizzle": a_sizzle,
       "wind": a_wind, "birds": a_birds, "snore": a_snore, "room": a_room, "crowd": a_crowd}


# ---------------------------------------------------------------- music
def music_segment(style, t0, t1):
    dur = t1 - t0
    buf = np.zeros((int((dur + 1.5) * SR), 2))

    def put(sig, t, g, pan=0.0):
        if t < dur:
            place_local(buf, sig, t, g, pan)

    if style in ("comedy", "fast"):
        bpm = 112 if style == "comedy" else 150
        beat = 60 / bpm
        chords = [(130.81, (523.25, 659.25, 783.99)), (110.0, (440.0, 523.25, 659.25)), (87.31, (349.23, 440.0, 523.25)), (98.0, (392.0, 493.88, 587.33))]
        k, t = 0, 0.0
        while t < dur:
            root, tones = chords[(k // 8) % 4]
            e = k % 8
            if e in (0, 4):
                put(pluck(root, 0.6, 5) * 0.9, t, 1.0)
                put(kick(0.25, 100, 50) * 0.5, t, 1.0)
            if e in (2, 6):
                put(pluck(root * 1.5, 0.4, 7) * 0.5, t, 1.0)
                put(snare() * 0.25, t, 1.0)
            if e % 2 == 1:
                put(marimba(tones[(k // 2) % 3], 0.35) * 0.55, t, 1.0, 0.3 if e in (1, 5) else -0.3)
            put(hat() * (0.12 if style == "comedy" else 0.2), t, 1.0, 0.2)
            k += 1
            t += beat / 2
    elif style == "action":
        beat = 60 / 140
        roots = [73.42, 58.27, 65.41, 73.42]
        s, t = 0, 0.0
        while t < dur:
            bar, pos = (s // 16) % 4, s % 16
            root = roots[bar]
            note = saw(root * (2 if pos in (3, 7, 11, 14) else 1), beat / 4 * 0.95, 1800)
            note *= np.exp(-np.arange(len(note)) / SR * 14) * (1.0 if pos % 4 == 0 else 0.65)
            put(note * 0.5, t, 1.0)
            if pos % 4 == 0:
                put(kick() * 0.9, t, 1.0)
            if pos in (4, 12):
                put(snare() * 0.6, t, 1.0)
            if pos in (10, 14, 15) and bar % 2 == 1:
                put(tom(0.35, 170 if pos == 10 else 130) * 0.6, t, 1.0, -0.4 if pos == 14 else 0.4)
            if pos % 2 == 0:
                put(hat() * 0.18, t, 1.0, 0.3)
            if pos == 0:
                put(pad([root * 4, root * 4 * 1.189, root * 4 * 1.498], beat * 0.9, attack=0.01, release=0.15, cutoff=3000) * 0.35, t, 1.0)
            s += 1
            t += beat / 4
    elif style == "tense":
        put(pad([73.42, 110.0, 146.83], dur + 0.8, attack=0.8, release=0.8, cutoff=900) * 0.6, 0, 1.0)
        t = 0.0
        while t < dur:
            put(tick() * 1.2, t, 0.8)
            put(kick(0.3, 70, 40) * 0.5, t + 0.5, 1.0)
            put(kick(0.3, 70, 40) * 0.35, t + 0.68, 1.0)
            t += 1.0
    elif style == "chill":
        beat = 60 / 80
        chords = [(174.61, 220.0, 261.63, 329.63), (164.81, 196.0, 246.94, 293.66), (146.83, 174.61, 220.0, 261.63), (130.81, 164.81, 196.0, 246.94)]
        k, t = 0, 0.0
        while t < dur:
            ch = chords[(k // 4) % 4]
            if k % 4 == 0:
                for i, f in enumerate(ch):
                    put(rhodes(f, beat * 4) * 0.35, t + i * 0.025, 1.0, (i - 1.5) * 0.2)
                put(pluck(ch[0] / 2, 1.0, 3) * 0.7, t, 1.0)
            put(kick(0.3, 90, 45) * 0.45 if k % 2 == 0 else snare() * 0.18, t, 1.0)
            put(hat() * 0.08, t + beat / 2, 1.0, 0.3)
            k += 1
            t += beat
    elif style == "dreamy":
        put(pad([261.63, 329.63, 392.0, 493.88], dur + 1.0, attack=1.0, release=1.2, cutoff=1800) * 0.6, 0, 1.0)
        t = 0.0
        for i, f in enumerate([1046.5, 1318.5, 1568.0, 1975.5, 1568.0, 1318.5] * 6):
            if t >= dur:
                break
            put(marimba(f, 0.6) * 0.25, t, 1.0, (i % 3 - 1) * 0.4)
            t += 0.42
    # fade the segment's edges so style changes never click
    n = int(dur * SR)
    fade = int(0.04 * SR)
    buf[:fade] *= np.linspace(0, 1, fade)[:, None]
    tail = buf[n:n + int(0.35 * SR)]
    tail *= np.linspace(1, 0, len(tail))[:, None]
    buf[n + int(0.35 * SR):] = 0
    return buf


def place_local(buf, sig, t0, gain, pan):
    if sig.ndim == 1:
        sig = np.stack([sig * np.cos((pan + 1) * np.pi / 4) * 1.4142, sig * np.sin((pan + 1) * np.pi / 4) * 1.4142], axis=1)
    i0 = int(t0 * SR)
    n = min(len(sig), len(buf) - i0)
    if n > 0:
        buf[i0:i0 + n] += sig[:n] * gain


MUSIC_GAIN = {"comedy": 0.30, "fast": 0.30, "action": 0.26, "tense": 0.30, "chill": 0.30, "dreamy": 0.26}

# ---------------------------------------------------------------- build
for seg in TL["music"]:
    if seg["style"] != "none":
        place(music_bus, music_segment(seg["style"], seg["t0"], seg["t1"]), seg["t0"], MUSIC_GAIN[seg["style"]] * seg.get("gain", 1.0))

for v in TL["voice"]:
    sig = read_wav(EP / "audio" / "clean" / f"{v['file']}.wav")
    if v.get("radio"):
        place(sfx_bus, squelch(True), v["t"] - 0.22, 0.35)
        place(sfx_bus, squelch(False), v["t"] + len(sig) / SR + 0.02, 0.3)
        sig = sig + band(rng.standard_normal(len(sig)), 1000, 5000) * 0.015
    rms = np.sqrt(np.mean(sig ** 2))
    place(voice_bus, np.tanh(sig * (0.11 / max(rms, 1e-4)) * 1.2) / 1.2, v["t"], 1.0)

for fx in TL["sfx"]:
    name = fx["name"]
    sig = SFX[name]() if name in SFX else AMB[name](fx.get("dur", 2.0))
    place(sfx_bus, sig, fx["t"], fx.get("gain", 0.3), fx.get("pan", 0.0))
for a in TL["amb"]:
    place(amb_bus, AMB[a["name"]](max(a["dur"], 0.3)), a["t"], a.get("gain", 0.15), a.get("pan", 0.0))

# duck music and ambience under dialogue
venv = np.abs(voice_bus).max(axis=1)
hop = SR // 100
env = venv[: len(venv) // hop * hop].reshape(-1, hop).max(axis=1)
env = np.lib.stride_tricks.sliding_window_view(np.pad(env, (12, 12)), 25).max(axis=1)
env = np.convolve(env, np.ones(15) / 15, mode="same")
act = np.interp(np.arange(N), np.arange(len(env)) * hop, np.clip(env / 0.08, 0, 1))
mix = voice_bus + music_bus * (1 - 0.6 * act)[:, None] + amb_bus * (1 - 0.75 * act)[:, None] + sfx_bus
mix = mix[: int(TL["duration"] * SR)]
peak = np.max(np.abs(mix))
mix = np.tanh(mix / peak * 1.1) / np.tanh(1.1) * 0.95

with wave.open(str(EP / "audio" / "mix.wav"), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())

bed = music_bus * (1 - 0.6 * act)[:, None] + amb_bus * (1 - 0.75 * act)[:, None] + sfx_bus
db = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
worst = min(((db(voice_bus[int(v["t"] * SR):int(v["t"] * SR) + 4000 + len(read_wav(EP / "audio" / "clean" / f"{v['file']}.wav"))]) -
              db(bed[int(v["t"] * SR):int(v["t"] * SR) + 4000 + len(read_wav(EP / "audio" / "clean" / f"{v['file']}.wav"))]), v["file"]) for v in TL["voice"]), default=(99, "-"))
print(f"{EP.name}: mix {TL['duration']:.1f}s, worst dialogue-over-bed gap {worst[0]:.1f} dB ({worst[1]})")
