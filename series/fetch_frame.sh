#!/usr/bin/env bash
# usage: series/fetch_frame.sh <episode-dir-name> <frame-letter> <figma-asset-url>
# Downloads a generated frame and stores it as a high-quality JPEG in videos/<episode>/frames/<letter>.jpg
set -euo pipefail
cd "$(dirname "$0")/.."
out="videos/$1/frames/$(echo "$2" | tr 'A-Z' 'a-z').jpg"
tmp=$(mktemp --suffix .png)
curl -sSfL -o "$tmp" "$3"
python3 -c "import sys; from PIL import Image; Image.open(sys.argv[1]).convert('RGB').save(sys.argv[2], quality=92)" "$tmp" "$out"
rm -f "$tmp"
echo "saved $out"
