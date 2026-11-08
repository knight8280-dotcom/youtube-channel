"""Turn an episode's beat-by-beat script.json into a frame-accurate timeline.json.

Each beat is one shot. Its length comes from the voice lines in it (real WAV
durations), so scripts never need hand-written timestamps.

    python3 engine/build_timeline.py videos/<episode>
"""
import json
import sys
import wave
from pathlib import Path


def wav_dur(p):
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


def main():
    ep = Path(sys.argv[1]).resolve()
    s = json.loads((ep / "script.json").read_text())
    tl = {"fps": 30, "width": 1080, "height": 1920, "shots": [], "chips": [], "voice": [], "texts": [],
          "sfx": [], "amb": [], "music": [], "danger": s.get("danger", [])}
    T = 0.0
    n = 0
    music = "none"

    def seg_music(t0, t1, style):
        m = tl["music"]
        if m and m[-1]["style"] == style and abs(m[-1]["t1"] - t0) < 1e-6:
            m[-1]["t1"] = t1
        else:
            m.append({"t0": t0, "t1": t1, "style": style})

    for b in s["beats"]:
        start = T
        line_times = []
        if "card" in b:
            end = start + b.get("dur", 1.5)
            tl["shots"].append({"t0": start, "t1": end, "card": b["card"], "sub": b.get("sub", ""), "color": b.get("color", "#ff3b30")})
            for i in range(len(b["card"])):
                tl["sfx"].append({"t": start + i * 0.065, "name": "tick", "gain": 0.22})
        else:
            pre, gap, post = b.get("pre", 0.25), b.get("gap", 0.3), b.get("post", 0.55)
            t = start + pre
            for line in b.get("lines", []):
                n += 1
                lid = f"L{n:02d}"
                t += line.get("delay", 0)
                d = wav_dur(ep / "audio" / "clean" / f"{lid}.wav")
                tl["voice"].append({"t": round(t, 3), "file": lid, "who": line["who"], "text": line["text"],
                                    "radio": line.get("filter", "radio" if line["who"] == "board" else None) == "radio" or bool(line.get("radio"))})
                line_times.append((t, t + d))
                t += d + gap
            end = (t - gap + post) if line_times else start + pre
            end = max(end, start + b.get("min", 1.6))
            if "dur" in b:
                end = start + b["dur"]
            img = s.get("frames", {}).get(b["shot"], {}).get("file", b["shot"])
            shot = {"t0": start, "t1": end, "img": img, "zoom": b.get("zoom", [1.0, 1.1]),
                    "cx": b.get("cx", [0.5, 0.5]), "cy": b.get("cy", [0.45, 0.42]), "fx": b.get("fx", [])}
            if b.get("flash"):
                shot["flash"] = True
                tl["sfx"].append({"t": max(0, start - 0.2), "name": "whoosh", "gain": 0.33})
            if "punch" in b:
                shot["punch"] = [start + p for p in b["punch"]]
            tl["shots"].append(shot)

        def at(spec, default_end=None):
            if "at_line" in spec:
                return line_times[spec["at_line"]][0] + spec.get("offset", 0)
            if "after_line" in spec:
                return line_times[spec["after_line"]][1] + spec.get("offset", 0)
            return start + spec.get("at", 0)

        if "chip" in b:
            c = dict(b["chip"])
            prev = tl["chips"][-1] if tl["chips"] else None
            if prev and prev["text"] == c["text"] and abs(prev["t1"] - start) < 1e-6:
                prev["t1"] = end
            else:
                tl["chips"].append({"t0": start, "t1": end, **c})
                tl["sfx"].append({"t": start + 0.12, "name": "pop", "gain": 0.25})
        for tx in b.get("texts", []):
            t0 = at(tx)
            t1 = t0 + tx["dur"] if "dur" in tx else end
            tl["texts"].append({**{k: v for k, v in tx.items() if k not in ("at", "at_line", "after_line", "offset", "dur")}, "t0": t0, "t1": t1})
            if tx.get("style") == "title":
                for i in range(len(tx["lines"])):
                    tl["sfx"].append({"t": t0 + i * 0.2, "name": "pop", "gain": 0.28})
            if tx.get("style") in ("stamp", "banner"):
                tl["sfx"].append({"t": t0, "name": "boom", "gain": 0.35})
            if tx.get("style") in ("note", "phone", "label"):
                tl["sfx"].append({"t": t0, "name": "pop", "gain": 0.3})
        for fx in b.get("sfx", []):
            tl["sfx"].append({**{k: v for k, v in fx.items() if k not in ("at", "at_line", "after_line", "offset")}, "t": at(fx)})
        for a in b.get("amb", []):
            t0 = at(a)
            tl["amb"].append({**{k: v for k, v in a.items() if k not in ("at", "at_line", "after_line", "offset")}, "t": t0, "dur": a.get("dur", end - t0)})
        music = b.get("music", music)
        seg_music(start, end, music)
        T = end

    # call-to-action tail on the last shot
    tail = s.get("end_extra", 1.9)
    final = T + tail
    tl["shots"][-1]["t1"] = final
    tl["chips"] and tl["chips"][-1]["t1"] == T and tl["chips"][-1].update(t1=final)
    for tx in tl["texts"]:
        if abs(tx["t1"] - T) < 1e-6:
            tx["t1"] = final
    if s.get("cta"):
        tl["texts"].append({"style": "cta", "lines": s["cta"], "t0": T - 0.1, "t1": final})
    if tl["music"]:
        tl["music"][-1]["t1"] = final
    tl["duration"] = round(final, 3)
    tl["title"] = s.get("title", ep.name)
    (ep / "timeline.json").write_text(json.dumps(tl, indent=1))
    print(f"{ep.name}: {final:.1f}s, {len(tl['shots'])} shots, {len(tl['voice'])} lines")


if __name__ == "__main__":
    main()
