// Render an episode's video track from its timeline.json.
//   node engine/render.mjs videos/<episode>                  -> <episode>/output/video_only.mp4
//   node engine/render.mjs videos/<episode> --preview 1,5,9  -> PNG stills in <episode>/output/preview/
import { createRequire } from 'node:module';
import { spawn, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const { chromium } = createRequire(import.meta.url)('playwright');
const engine = path.dirname(fileURLToPath(import.meta.url));
const ep = path.resolve(process.argv[2]);
const tl = JSON.parse(fs.readFileSync(path.join(ep, 'timeline.json'), 'utf8'));
const outDir = path.join(ep, 'output');
fs.mkdirSync(outDir, { recursive: true });

const durations = {};
for (const v of tl.voice) {
  const f = path.join(ep, 'audio', 'clean', `${v.file}.wav`);
  durations[v.file] = parseFloat(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).toString());
}

const pi = process.argv.indexOf('--preview');
const preview = pi > -1 ? process.argv[pi + 1].split(',').map(Number) : null;

const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
const page = await browser.newPage({ viewport: { width: tl.width, height: tl.height }, deviceScaleFactor: 1 });
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => { console.error('[pageerror]', e); process.exit(1); });
await page.goto(pathToFileURL(path.join(engine, 'render.html')).href);
console.log('setup:', await page.evaluate(([t, d, u]) => window.setup(t, d, u), [tl, durations, pathToFileURL(ep).href]));

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
  '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(tl.fps), outFile], { stdio: ['pipe', 'inherit', 'inherit'] });
const started = Date.now();
for (let i = 0; i < total; i++) {
  await page.evaluate(t => window.renderFrame(t), i / tl.fps);
  const buf = await page.screenshot({ type: 'jpeg', quality: 93 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (i % 300 === 0) console.log(`${path.basename(ep)} frame ${i}/${total}  ${((Date.now() - started) / 1000).toFixed(0)}s`);
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
console.log('wrote', outFile);
