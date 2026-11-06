// Renders the Short's video track.
//   node render.mjs                 -> ../output/video_only.mp4
//   node render.mjs --preview 1,15  -> PNG stills at those timestamps in ../output/preview/
import { createRequire } from 'node:module';
import { spawn, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Use the pre-installed Playwright (resolved like CommonJS so NODE_PATH / global installs work).
const { chromium } = createRequire(import.meta.url)('playwright');

const here = path.dirname(fileURLToPath(import.meta.url));
const tl = JSON.parse(fs.readFileSync(path.join(here, 'timeline.json'), 'utf8'));
const outDir = path.join(here, '..', 'output');
fs.mkdirSync(outDir, { recursive: true });

const durations = {};
for (const v of tl.voice) {
  const f = path.join(here, '..', 'audio', 'clean', `${v.file}.wav`);
  durations[v.file] = parseFloat(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).toString());
}

const previewArg = process.argv.indexOf('--preview');
const preview = previewArg > -1 ? process.argv[previewArg + 1].split(',').map(Number) : null;

const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
const page = await browser.newPage({ viewport: { width: tl.width, height: tl.height }, deviceScaleFactor: 1 });
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => { console.error('[pageerror]', e); process.exit(1); });
await page.goto('file://' + path.join(here, 'render.html'));
console.log('setup:', await page.evaluate(([t, d]) => window.setup(t, d), [tl, durations]));

if (preview) {
  const pdir = path.join(outDir, 'preview');
  fs.mkdirSync(pdir, { recursive: true });
  for (const t of preview) {
    await page.evaluate(t => window.renderFrame(t), t);
    await page.screenshot({ path: path.join(pdir, `t${String(t).replace('.', '_')}.png`) });
  }
  await browser.close();
  process.exit(0);
}

const total = Math.round(tl.duration * tl.fps);
const outFile = path.join(outDir, 'video_only.mp4');
const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(tl.fps), '-c:v', 'mjpeg', '-i', '-',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(tl.fps), outFile], { stdio: ['pipe', 'inherit', 'inherit'] });
const started = Date.now();
for (let i = 0; i < total; i++) {
  await page.evaluate(t => window.renderFrame(t), i / tl.fps);
  const buf = await page.screenshot({ type: 'jpeg', quality: 93 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (i % 150 === 0) console.log(`frame ${i}/${total}  ${((Date.now() - started) / 1000).toFixed(0)}s`);
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
console.log('wrote', outFile);
