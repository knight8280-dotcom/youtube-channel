# How the Plant Sees Operators (YouTube Short)

A 66-second vertical (1080×1920) cartoon skit in the glossy 3D-animated "AI video" style. The two
operators from the control-room photo are the stars: the camo-hat guy ("Camo") and the mustache guy
in the blue work shirt ("Stache"). Every department roasts them for "just sitting there"... until
the unit trips at 2:47 AM.

**Final video:** `output/plant-operators-short.mp4`

## Script

| Time | Scene | Line |
|---|---|---|
| 0:00 | Control room, both guys kicked back | On-screen hook: "HOW EVERYONE AT THE PLANT SEES OPERATORS 🙄" |
| 0:03 | 🔧 Maintenance mechanic in the doorway | "Must be nice. Y'all just sit in the AC all day." |
| 0:07 | Stache, hands behind head | "We're monitoring." |
| 0:09 | Camo, on his phone | "Heavily monitoring." |
| 0:11 | 🤓 Nervous engineer | "Um... did you guys follow the procedure?" |
| 0:14 | Camo holding the ancient binder | "The one from 1987? With the coffee stain on step four?" |
| 0:19 | 👔 Plant manager | "So... what exactly do operators do all night?" |
| 0:23 | Both gesture at the plant | *gestures at the entire plant that didn't explode* (crickets) |
| 0:26 | Manager writes it down | "Great. So... nothing. Noted." + sticky note: OPERATOR DUTIES: nothing ✓ |
| 0:29 | ☀️ Day shift walking out | "Everything's running smooth! Should be a quiet night!" |
| 0:33 | Horrified faces | "She said the Q-word." → dun dun DUNNN |
| 0:36 | Black card | 2:47 AM — THAT NIGHT... |
| 0:37 | Red alarm, both launch out of chairs | 📻 "Board to outside! Unit just tripped! Need everybody out here, NOW!" |
| 0:42 | Sprinting through the unit in the rain | "Every. Single. Time!" |
| 0:45 | Fighting a stuck valve | Banner: WHAT OPERATORS ACTUALLY DO |
| 0:48 | Valve, rain easing | 📻 "Pump's back online. Unit's stable. Good work, fellas." |
| 0:52 | Black card | 6:00 AM — THE NEXT MORNING |
| 0:53 | Soaked and wrecked, mechanic strolls in | "Mornin'! Must be nice, just sittin' around all night." |
| 0:57 | Stache, dead-eyed coffee sip | "...yep." (on-screen) |
| 1:00 | Hero shot at dawn | Narrator: "Operators. They don't do anything... until everything." + CTA: tag an operator |

## Suggested YouTube upload text

- **Title:** How the plant sees operators 😂 #plantlife
- **Description:** They say we just sit around all day... until 2:47 AM. Tag an operator who's "just sitting around." 👇
- **Hashtags:** #shorts #plantoperator #operatorlife #refinery #chemicalplant #shiftwork #nightshift #bluecollar

## How it was made

- **Scene art:** 16 frames generated with Figma's AI image tool, from written descriptions of
  the two guys in the photo (outfits, hats, mustache, tattoo sleeve, etc.). Company logos and
  name tags were left out on purpose. Frames are in `frames/`.
- **Voices:** ElevenLabs (`eleven_v4`). Cast: Camo = "Rhett", Stache = "Ronan", maintenance =
  "Rich", engineer = "Timmy", manager = "Marty", day shift = "Mira", radio board operator =
  "Chuck Miller", narrator = "Timber". Raw takes are in `audio/voice/`, trimmed copies in `audio/clean/`.
- **Music and sound effects:** all synthesized in `src/mix_audio.py`, so there's no stock
  audio to clear: comedic pizzicato bed, action drums, "dun dun dunnn" sting, klaxon, rain,
  steam, radio squelch, crickets and birds.
- **Animation:** `src/scene.js` (canvas) handles camera moves, captions with the active word
  highlighted, title cards and the alarm, rain, steam and dust effects. `src/render.mjs`
  captures it frame by frame with Playwright and encodes it with ffmpeg.

## Rebuild

```bash
cd src
./build.sh             # mix audio, render video, mux -> output/plant-operators-short.mp4
node render.mjs --preview 5,24,39   # quick PNG stills at given timestamps -> output/preview/
```

Timing for every shot, voice line and on-screen text is in `src/timeline.json`.

## Known gaps

ElevenLabs stopped generating partway through: the account's free tier was disabled for "unusual
activity". These lines were never voiced and were replaced like this:

- Opening narrator hook → on-screen title text instead
- Stache: "Our best work is when nothing happens, sir." → replaced by the silent gesture gag
- Stache: "...Yep." → on-screen text plus a slurp sound

To add real voices later, drop new WAVs into `audio/clean/`, add them to `voice` in
`src/timeline.json`, and run `./build.sh`.
