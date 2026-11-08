"""Voice every dialogue line of an episode with Kokoro (local, free TTS).

    python3 engine/tts.py videos/<episode>            # generate missing/changed lines
    python3 engine/tts.py videos/<episode> --check    # also transcribe each line to verify it

Lines are written to <episode>/audio/clean/Lnn.wav (48 kHz mono, silence-trimmed,
pitch-shifted per character, radio/phone filtered where the cast or line says so).
A line that already has a WAV whose recorded text matches is skipped, so hand-made
or ElevenLabs takes dropped into audio/clean/ with a matching manifest entry are kept.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ENGINE = Path(__file__).resolve().parent
MODEL = Path.home() / ".cache" / "kokoro"


def episode_lines(script):
    n = 0
    for beat in script["beats"]:
        for line in beat.get("lines", []):
            n += 1
            yield f"L{n:02d}", line


def ffmpeg_filter(char, line):
    f = []
    pitch = line.get("pitch", char.get("pitch", 1.0))
    if abs(pitch - 1.0) > 1e-3:
        f.append(f"asetrate={int(24000 * pitch)},aresample=24000,atempo={1 / pitch:.5f}")
    f.append("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,areverse,"
             "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse")
    kind = line.get("filter", char.get("filter"))
    if kind == "radio":
        f.append("highpass=f=380,lowpass=f=3000,volume=2.5,asoftclip=type=tanh,volume=0.7")
    elif kind == "phone":
        f.append("highpass=f=450,lowpass=f=3400,volume=2.0,asoftclip=type=tanh,volume=0.8")
    f.append("aresample=48000")
    return ",".join(f)


def main():
    ep = Path(sys.argv[1]).resolve()
    check = "--check" in sys.argv
    script = json.loads((ep / "script.json").read_text())
    cast = json.loads((ENGINE / "cast.json").read_text())
    out = ep / "audio" / "clean"
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    kokoro = None
    for lid, line in episode_lines(script):
        char = cast[line["who"]]
        say = line.get("say", line["text"])
        key = hashlib.sha1(json.dumps([say, char, line.get("pitch"), line.get("speed"), line.get("filter")]).encode()).hexdigest()[:12]
        wav = out / f"{lid}.wav"
        if wav.exists() and manifest.get(lid, {}).get("key") in (key, "manual"):
            continue
        if kokoro is None:
            from kokoro_onnx import Kokoro
            kokoro = Kokoro(str(MODEL / "model.onnx"), str(MODEL / "voices.npz"))
        samples, sr = kokoro.create(say, voice=char["voice"], speed=line.get("speed", char.get("speed", 1.0)), lang="en-us")
        raw = out / f"{lid}_raw.wav"
        sf.write(raw, samples, sr)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", ffmpeg_filter(char, line), "-ac", "1", str(wav)], check=True)
        raw.unlink()
        manifest[lid] = {"key": key, "who": line["who"], "text": line["text"]}
        print(f"{lid} {line['who']:7s} {sf.info(wav).duration:5.2f}s  {line['text']}")
    manifest_path.write_text(json.dumps(manifest, indent=1))

    if check:
        from faster_whisper import WhisperModel
        model = WhisperModel("tiny.en", device="cpu", compute_type="int8", download_root=str(Path.home() / ".cache" / "whisper"))
        norm = lambda s: " ".join("".join(c.lower() if c.isalnum() or c == " " else " " for c in s).split())
        for lid, line in episode_lines(script):
            pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out / f"{lid}.wav"), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                                 check=True, capture_output=True).stdout
            segs, _ = model.transcribe(np.frombuffer(pcm, dtype=np.float32))
            heard = " ".join(s.text for s in segs).strip()
            want, got = set(norm(line.get("say", line["text"])).split()), set(norm(heard).split())
            score = len(want & got) / max(len(want), 1)
            flag = "OK " if score >= 0.6 else "?? "
            print(f"{flag}{lid} {score:4.0%}  heard: {heard}")


if __name__ == "__main__":
    main()
