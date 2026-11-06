#!/usr/bin/env bash
# Rebuilds the Short from the frames, voice lines and timeline:
#   1. synthesize music/SFX and mix the voices  -> ../audio/mix.wav
#   2. render the animated video track          -> ../output/video_only.mp4
#   3. mux + loudness-normalize for YouTube     -> ../output/plant-operators-short.mp4
set -euo pipefail
cd "$(dirname "$0")"
[ -d node_modules/@fontsource ] || npm install --silent
python3 mix_audio.py
node render.mjs
ffmpeg -y -v error -i ../output/video_only.mp4 -i ../audio/mix.wav -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart \
  ../output/plant-operators-short.mp4
echo "done: ../output/plant-operators-short.mp4"
