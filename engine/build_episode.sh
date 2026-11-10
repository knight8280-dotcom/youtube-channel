#!/usr/bin/env bash
# Build one episode end to end:  engine/build_episode.sh videos/<episode>
#   voices (Kokoro) -> timeline -> music/SFX mix -> rendered frames -> final MP4
set -euo pipefail
ENGINE=$(cd "$(dirname "$0")" && pwd)
EP=$(cd "$1" && pwd)
NAME=$(basename "$EP")
[ -d "$ENGINE/node_modules/@fontsource" ] || (cd "$ENGINE" && npm install --silent)
python3 "$ENGINE/tts.py" "$EP"
python3 "$ENGINE/build_timeline.py" "$EP"
python3 "$ENGINE/mix_audio.py" "$EP"
node "$ENGINE/render.mjs" "$EP"
ffmpeg -y -v error -i "$EP/output/video_only.mp4" -i "$EP/audio/mix.wav" -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 21 -maxrate 9M -bufsize 18M -pix_fmt yuv420p -profile:v high \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart \
  "$EP/output/$NAME.mp4"
rm -f "$EP/output/video_only.mp4"
echo "done: $EP/output/$NAME.mp4 ($(du -h "$EP/output/$NAME.mp4" | cut -f1))"
