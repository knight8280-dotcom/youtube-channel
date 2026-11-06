// Frame renderer for "How the plant sees operators" (vertical Short).
// The driver (render.mjs) calls window.setup(timeline, voiceDurations) once,
// then window.renderFrame(t) for every frame and screenshots the canvas.

const W = 1080, H = 1920;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');

let TL = null;
let DUR = {};
const IMGS = {};
let GRAIN = [];
let CAPTION_GROUPS = [];

const CHIPS = [
  { t0: 2.80,  t1: 10.80, text: '🔧 MAINTENANCE', bg: '#ff8a00', fg: '#111' },
  { t0: 10.80, t1: 18.90, text: '🤓 ENGINEERING', bg: '#2f80ff', fg: '#fff' },
  { t0: 18.90, t1: 29.40, text: '👔 MANAGEMENT',  bg: '#8e44ff', fg: '#fff' },
  { t0: 29.40, t1: 32.80, text: '☀️ DAY SHIFT',    bg: '#ffd400', fg: '#111' },
];

// ---------- helpers ----------
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, p) => a + (b - a) * p;
const easeInOut = p => -(Math.cos(Math.PI * p) - 1) / 2;
const easeOut = p => 1 - Math.pow(1 - p, 3);
const easeOutBack = p => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); };
function rng(seed) { // mulberry32
  return function () {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
function particles(n, seed) {
  const r = rng(seed), out = [];
  for (let i = 0; i < n; i++) out.push({ a: r(), b: r(), c: r(), d: r() });
  return out;
}
const RAIN = particles(280, 7);
const DUST = particles(70, 11);
const STEAM = particles(16, 23);

function loadImage(src) {
  return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = src; });
}

function makeGrain() {
  const out = [];
  const r = rng(99);
  for (let k = 0; k < 4; k++) {
    const g = document.createElement('canvas'); g.width = 540; g.height = 960;
    const gc = g.getContext('2d');
    const id = gc.createImageData(540, 960);
    for (let i = 0; i < id.data.length; i += 4) {
      const v = Math.floor(r() * 255);
      id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 22;
    }
    gc.putImageData(id, 0, 0);
    out.push(g);
  }
  return out;
}

// Split each voice line into words with estimated timings, then into caption groups.
function buildCaptions() {
  const groups = [];
  for (const v of TL.voice) {
    const dur = DUR[v.file] || 2;
    const words = v.text.split(/\s+/);
    const weights = words.map(w => w.replace(/[^A-Za-z0-9']/g, '').length + 1.5 + (/[.!?]$/.test(w) ? 3 : 0) + (/\.\.\.$/.test(w) ? 4 : 0) + (/,$/.test(w) ? 1.5 : 0));
    const total = weights.reduce((a, b) => a + b, 0);
    let acc = 0;
    const timed = words.map((w, i) => { const s = v.t + (acc / total) * dur; acc += weights[i]; return { w, s, e: v.t + (acc / total) * dur }; });
    let cur = [];
    const flush = () => { if (cur.length) { groups.push({ words: cur, radio: !!v.radio }); cur = []; } };
    for (const tw of timed) {
      const chars = cur.reduce((a, x) => a + x.w.length + 1, 0) + tw.w.length;
      if (cur.length >= 3 || (cur.length && chars > 17)) flush();
      cur.push(tw);
      if (/[.!?]$/.test(tw.w)) flush();
    }
    flush();
    // set display window for groups of this line
    const lineGroups = groups.filter(g => g.t0 === undefined);
    lineGroups.forEach((g, i) => {
      g.t0 = g.words[0].s;
      g.t1 = i < lineGroups.length - 1 ? lineGroups[i + 1].words[0].s : v.t + dur + 0.35;
    });
  }
  return groups;
}

window.setup = async function (timeline, durations) {
  TL = timeline; DUR = durations;
  const names = [...new Set(TL.shots.filter(s => s.img).map(s => s.img))];
  for (const n of names) IMGS[n] = await loadImage(`../frames/${n}.png`);
  await document.fonts.load('900 100px Mont');
  await document.fonts.load('800 100px Mont');
  await document.fonts.load('400 100px Bangers');
  await document.fonts.load('100px "Noto Color Emoji"');
  GRAIN = makeGrain();
  CAPTION_GROUPS = buildCaptions();
  return { images: names.length, groups: CAPTION_GROUPS.length };
};

// ---------- drawing primitives ----------
function drawCover(img, zoom, cx, cy, ox, oy) {
  const base = Math.max(W / img.width, H / img.height);
  const s = base * zoom, dw = img.width * s, dh = img.height * s;
  let x = W / 2 - cx * dw, y = H / 2 - cy * dh;
  x = clamp(x, W - dw, 0); y = clamp(y, H - dh, 0);
  ctx.drawImage(img, x + ox, y + oy, dw, dh);
}

function strokeText(text, x, y, font, fill, stroke, lw, align = 'center') {
  ctx.font = font; ctx.textAlign = align; ctx.textBaseline = 'middle';
  ctx.lineJoin = 'round'; ctx.miterLimit = 2;
  if (lw > 0) { ctx.lineWidth = lw; ctx.strokeStyle = stroke; ctx.strokeText(text, x, y); }
  ctx.fillStyle = fill; ctx.fillText(text, x, y);
}

function fitFont(text, weight, maxSize, maxWidth, family = 'Mont') {
  let size = maxSize;
  ctx.font = `${weight} ${size}px ${family}, "Noto Color Emoji"`;
  while (ctx.measureText(text).width > maxWidth && size > 20) { size -= 2; ctx.font = `${weight} ${size}px ${family}, "Noto Color Emoji"`; }
  return size;
}

function roundRect(x, y, w, h, r) {
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}

// ---------- effects ----------
function fxRain(t, n, alpha) {
  ctx.save(); ctx.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const p = RAIN[i];
    const speed = 2300 + p.b * 900, len = 40 + p.c * 70;
    const y = ((p.a * (H + 300) + t * speed) % (H + 300)) - 150;
    const x = ((p.d * (W + 400) + y * 0.16) % (W + 400)) - 200;
    ctx.strokeStyle = `rgba(210,225,255,${alpha * (0.5 + p.c * 0.5)})`;
    ctx.lineWidth = 1.5 + p.b * 2;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + len * 0.16, y + len); ctx.stroke();
  }
  ctx.restore();
}
function fxDust(t) {
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  for (const p of DUST) {
    const x = (p.a * W + Math.sin(t * 0.6 + p.c * 9) * 50) % W;
    const y = ((p.b * H - t * (15 + p.d * 30)) % H + H) % H;
    const r = 2 + p.c * 5;
    ctx.fillStyle = `rgba(255,235,190,${0.18 + p.d * 0.4})`;
    ctx.shadowColor = 'rgba(255,230,180,0.9)'; ctx.shadowBlur = 12;
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}
function fxSteam(t) {
  ctx.save();
  for (const p of STEAM) {
    const life = 2.4, ph = ((t + p.a * life) % life) / life;
    const x = 980 - ph * (250 + p.b * 200) + Math.sin(t * 2 + p.c * 6) * 30;
    const y = 420 - ph * (380 + p.d * 200);
    const r = 80 + ph * 260;
    const a = 0.22 * Math.sin(Math.PI * ph);
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, `rgba(255,255,255,${a})`); g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }
  ctx.restore();
}
function fxAlarm(t) {
  const pulse = Math.pow((Math.sin(2 * Math.PI * 1.6 * t) + 1) / 2, 2);
  ctx.save();
  ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = `rgba(255,0,20,${0.08 + 0.22 * pulse})`; ctx.fillRect(0, 0, W, H);
  const g = ctx.createRadialGradient(560, 150, 10, 560, 150, 700);
  g.addColorStop(0, `rgba(255,60,40,${0.55 * pulse})`); g.addColorStop(1, 'rgba(255,0,0,0)');
  ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}
function vignette(strength) {
  const g = ctx.createRadialGradient(W / 2, H * 0.48, H * 0.28, W / 2, H * 0.5, H * 0.78);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${strength})`);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
function fxGlow(t) {
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  const a = 0.22 + 0.1 * Math.sin(t * 1.3);
  const g = ctx.createRadialGradient(W * 0.55, H * 0.33, 20, W * 0.55, H * 0.33, 900);
  g.addColorStop(0, `rgba(255,190,90,${a})`); g.addColorStop(1, 'rgba(255,120,0,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
}
function fxNotepad(local) {
  const appear = 2.05;
  if (local < appear) return;
  const p = clamp((local - appear) / 0.28, 0, 1);
  const s = easeOutBack(p);
  ctx.save();
  ctx.translate(560, 1010); ctx.rotate(-0.08); ctx.scale(s * 0.85, s * 0.85);
  ctx.shadowColor = 'rgba(0,0,0,0.45)'; ctx.shadowBlur = 30; ctx.shadowOffsetY = 14;
  ctx.fillStyle = '#ffe873'; ctx.fillRect(-300, -230, 600, 460);
  ctx.shadowColor = 'transparent';
  ctx.fillStyle = 'rgba(0,0,0,0.06)'; ctx.fillRect(-300, -230, 600, 60);
  strokeText('OPERATOR DUTIES:', 0, -150, '900 46px Mont', '#2b2b2b', '', 0);
  ctx.strokeStyle = 'rgba(40,80,200,0.35)'; ctx.lineWidth = 3;
  for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.moveTo(-260, -90 + i * 80); ctx.lineTo(260, -90 + i * 80); ctx.stroke(); }
  // "nothing" scribbled in, then a check mark
  const wp = clamp((local - appear - 0.2) / 0.45, 0, 1);
  ctx.save();
  ctx.beginPath(); ctx.rect(-260, -120, 520 * wp, 200); ctx.clip();
  strokeText('nothing', -10, -10, '400 150px Bangers', '#d0122f', '', 0);
  ctx.restore();
  const cp = clamp((local - appear - 0.75) / 0.25, 0, 1);
  if (cp > 0) {
    ctx.strokeStyle = '#d0122f'; ctx.lineWidth = 16; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath(); ctx.moveTo(-120, 130);
    if (cp < 0.4) { const q = cp / 0.4; ctx.lineTo(-120 + 60 * q, 130 + 50 * q); }
    else { ctx.lineTo(-60, 180); const q = (cp - 0.4) / 0.6; ctx.lineTo(-60 + 200 * q, 180 - 150 * q); }
    ctx.stroke();
  }
  ctx.restore();
}

// ---------- text layers ----------
function drawChip(t) {
  for (const c of CHIPS) {
    if (t < c.t0 || t >= c.t1) continue;
    const p = clamp((t - c.t0) / 0.3, 0, 1);
    const s = easeOutBack(p);
    ctx.save(); ctx.translate(540, 250); ctx.scale(s, s); ctx.rotate(-0.02);
    ctx.font = '900 60px Mont, "Noto Color Emoji"';
    const tw = ctx.measureText(c.text).width;
    const w = tw + 90, h = 110;
    ctx.shadowColor = 'rgba(0,0,0,0.5)'; ctx.shadowBlur = 24; ctx.shadowOffsetY = 8;
    roundRect(-w / 2, -h / 2, w, h, 55); ctx.fillStyle = c.bg; ctx.fill();
    ctx.shadowColor = 'transparent';
    ctx.lineWidth = 6; ctx.strokeStyle = '#111'; ctx.stroke();
    strokeText(c.text, 0, 4, '900 60px Mont, "Noto Color Emoji"', c.fg, '', 0);
    ctx.restore();
    // small "how they see us" tag above the chip
    if (p >= 1) {
      ctx.save(); ctx.globalAlpha = clamp((t - c.t0 - 0.3) / 0.3, 0, 1);
      strokeText('HOW THEY SEE US', 540, 160, '800 38px Mont', '#fff', 'rgba(0,0,0,0.85)', 8);
      ctx.restore();
    }
  }
}

function drawCaptions(t) {
  const g = CAPTION_GROUPS.find(g => t >= g.t0 && t < g.t1);
  if (!g) return;
  const y = 1330;
  const gp = clamp((t - g.t0) / 0.1, 0, 1);
  const gs = 0.86 + 0.14 * easeOutBack(gp);
  const text = g.words.map(w => w.w).join(' ');
  const size = fitFont(text, 900, 96, 940);
  ctx.save();
  ctx.translate(540, y); ctx.scale(gs, gs);
  ctx.font = `900 ${size}px Mont`;
  const space = ctx.measureText(' ').width;
  const widths = g.words.map(w => ctx.measureText(w.w).width);
  const total = widths.reduce((a, b) => a + b, 0) + space * (g.words.length - 1);
  let x = -total / 2;
  g.words.forEach((w, i) => {
    const active = t >= w.s && (i === g.words.length - 1 || t < g.words[i + 1].s);
    const spoken = t >= w.s;
    const danger = TL.danger.includes(w.w);
    let fill = '#ffffff';
    if (active) fill = danger ? '#ff3b30' : '#ffe135';
    else if (!spoken) fill = 'rgba(255,255,255,0.92)';
    const pop = active ? 1 + 0.12 * (1 - clamp((t - w.s) / 0.12, 0, 1)) : 1;
    ctx.save();
    ctx.translate(x + widths[i] / 2, 0); ctx.scale(pop, pop);
    ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 18; ctx.shadowOffsetY = 6;
    strokeText(w.w, 0, 0, `900 ${size}px Mont`, fill, '#000', Math.round(size * 0.17));
    ctx.shadowColor = 'transparent';
    strokeText(w.w, 0, 0, `900 ${size}px Mont`, fill, '#000', 0);
    ctx.restore();
    x += widths[i] + space;
  });
  ctx.restore();
  if (g.radio) {
    const a = 0.7 + 0.3 * Math.sin(t * 20);
    ctx.save(); ctx.globalAlpha = a;
    strokeText('📻 RADIO', 540, y - 115, '900 44px Mont, "Noto Color Emoji"', '#ffe135', '#000', 9);
    ctx.restore();
  }
}

function drawTexts(t) {
  for (const tx of TL.texts) {
    if (t < tx.t0 || t >= tx.t1) continue;
    const local = t - tx.t0;
    if (tx.style === 'title') {
      tx.lines.forEach((ln, i) => {
        const p = clamp((local - i * 0.2) / 0.28, 0, 1);
        if (p <= 0) return;
        const s = easeOutBack(p);
        const size = fitFont(ln, 900, 118, 960);
        ctx.save(); ctx.translate(540, 330 + i * 150); ctx.rotate(-0.035); ctx.scale(s, s);
        ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 24; ctx.shadowOffsetY = 8;
        strokeText(ln, 0, 0, `900 ${size}px Mont`, i === tx.lines.length - 1 ? '#ffe135' : '#fff', '#000', 20);
        ctx.restore();
      });
      const ep = clamp((local - 0.85) / 0.3, 0, 1);
      if (ep > 0) {
        ctx.save(); ctx.translate(540, 330 + tx.lines.length * 150 + 20); ctx.scale(easeOutBack(ep), easeOutBack(ep));
        ctx.rotate(Math.sin(local * 6) * 0.08);
        ctx.font = '130px "Noto Color Emoji"'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText('🙄', 0, 0); ctx.restore();
      }
    } else if (tx.style === 'action') {
      const p = clamp(local / 0.25, 0, 1);
      ctx.save(); ctx.globalAlpha = p;
      const lh = 84, h = tx.lines.length * lh + 60, w = 900, y0 = 1260 - h / 2;
      roundRect(540 - w / 2, y0, w, h, 30); ctx.fillStyle = 'rgba(0,0,0,0.62)'; ctx.fill();
      tx.lines.forEach((ln, i) => strokeText(ln, 540, y0 + 30 + lh / 2 + i * lh, '800 66px Mont', '#fff', '', 0));
      ctx.restore();
    } else if (tx.style === 'banner') {
      const p = clamp(local / 0.18, 0, 1);
      const s = lerp(1.9, 1, easeOut(p));
      const shake = local < 0.4 ? (1 - local / 0.4) * 14 : 0;
      ctx.save(); ctx.translate(540 + Math.sin(local * 90) * shake, 330 + Math.cos(local * 70) * shake); ctx.rotate(-0.05); ctx.scale(s, s);
      ctx.globalAlpha = p;
      const bw = 1300, bh = 300;
      ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 30;
      ctx.fillStyle = '#ffd400'; ctx.fillRect(-bw / 2, -bh / 2, bw, bh);
      ctx.shadowColor = 'transparent';
      // hazard stripes along top and bottom edges
      ctx.save(); ctx.beginPath(); ctx.rect(-bw / 2, -bh / 2, bw, 34); ctx.rect(-bw / 2, bh / 2 - 34, bw, 34); ctx.clip();
      ctx.fillStyle = '#111';
      for (let x = -bw / 2 - 100; x < bw / 2 + 100; x += 60) { ctx.beginPath(); ctx.moveTo(x, -bh / 2); ctx.lineTo(x + 30, -bh / 2); ctx.lineTo(x + 30 + bh, bh / 2); ctx.lineTo(x + bh, bh / 2); ctx.closePath(); ctx.fill(); }
      ctx.restore();
      tx.lines.forEach((ln, i) => strokeText(ln, 0, -50 + i * 108, '900 100px Mont', '#111', '', 0));
      ctx.restore();
    } else if (tx.style === 'caption_static') {
      const p = clamp(local / 0.12, 0, 1);
      const s = 0.86 + 0.14 * easeOutBack(p);
      ctx.save(); ctx.translate(540, 1330); ctx.scale(s, s);
      strokeText(tx.lines[0], 0, 0, '900 110px Mont', '#ffe135', '#000', 18);
      ctx.restore();
    } else if (tx.style === 'cta') {
      const p = clamp(local / 0.25, 0, 1);
      ctx.save(); ctx.globalAlpha = p;
      tx.lines.forEach((ln, i) => {
        const size = fitFont(ln, 900, 64, 960);
        strokeText(ln, 540, 1500 + i * 82, `900 ${size}px Mont`, i === 1 ? '#ffe135' : '#fff', '#000', 13);
      });
      ctx.font = '96px "Noto Color Emoji"'; ctx.textAlign = 'center';
      ctx.fillText('👇', 540, 1690 + Math.abs(Math.sin(local * 7)) * -26);
      ctx.restore();
    }
  }
}

function drawCard(shot, local) {
  ctx.fillStyle = '#050505'; ctx.fillRect(0, 0, W, H);
  const color = shot.cardColor || '#ff3b30';
  const txt = shot.card;
  const n = Math.floor(clamp(local / 0.45, 0, 1) * txt.length + 0.0001);
  let shown = txt.slice(0, n);
  if (n >= txt.length && Math.floor(local * 3) % 2 === 1) shown = shown.replace(':', ' ');
  ctx.save();
  ctx.shadowColor = color; ctx.shadowBlur = 50;
  strokeText(shown, 540, 900, '900 230px Mont', color, '', 0);
  ctx.restore();
  const sub = txt.startsWith('2') ? 'THAT NIGHT...' : 'THE NEXT MORNING';
  ctx.save(); ctx.globalAlpha = clamp((local - 0.5) / 0.3, 0, 1);
  strokeText(sub, 540, 1100, '800 64px Mont', '#ffffff', '', 0);
  ctx.restore();
}

// ---------- main ----------
window.renderFrame = function (t) {
  const shot = TL.shots.find(s => t >= s.t0 && t < s.t1) || TL.shots[TL.shots.length - 1];
  const local = t - shot.t0, len = shot.t1 - shot.t0;
  const p = clamp(local / len, 0, 1);
  const fx = shot.fx || [];
  ctx.save();
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);

  if (shot.card) {
    drawCard(shot, local);
  } else {
    const img = IMGS[shot.img];
    let zoom = lerp(shot.zoom[0], shot.zoom[1], easeInOut(p));
    if (fx.includes('punch')) { // slow creep during the whisper, then stepped zooms on the "dun dun dunnn" hits
      const hits = [2.15, 2.45, 2.75];
      let z = 1.0 + 0.06 * easeInOut(clamp(local / 2.1, 0, 1));
      hits.forEach(s0 => { z += 0.12 * easeOut(clamp((local - s0) / 0.1, 0, 1)); });
      zoom = z;
    }
    zoom *= 1 + 0.04 * (1 - easeOut(clamp(local / 0.25, 0, 1))); // snap-in on every cut
    let ox = 0, oy = 0;
    if (fx.includes('shake')) { const a = 12; ox = a * (Math.sin(t * 41) + 0.5 * Math.sin(t * 23.7)); oy = a * (Math.cos(t * 37) + 0.5 * Math.sin(t * 29.3)); zoom *= 1.03; }
    if (fx.includes('shake_small')) { const a = 6; ox = a * Math.sin(t * 31); oy = a * Math.cos(t * 27); zoom *= 1.015; }
    ctx.filter = 'contrast(1.05) saturate(1.08)';
    drawCover(img, zoom, lerp(shot.cx[0], shot.cx[1], easeInOut(p)), lerp(shot.cy[0], shot.cy[1], easeInOut(p)), ox, oy);
    ctx.filter = 'none';

    if (fx.includes('dust')) fxDust(t);
    if (fx.includes('steam')) fxSteam(t);
    if (fx.includes('rain')) fxRain(t, 280, 0.45);
    if (fx.includes('rain_light')) fxRain(t, 120, 0.3);
    if (fx.includes('alarm')) fxAlarm(t);
    if (fx.includes('glow')) fxGlow(t);
    if (fx.includes('darken')) { ctx.fillStyle = `rgba(0,0,0,${0.12 + 0.18 * p})`; ctx.fillRect(0, 0, W, H); vignette(0.5 + 0.3 * p); }
    vignette(0.42);
    if (fx.includes('notepad')) fxNotepad(local);
  }

  // film grain
  ctx.globalCompositeOperation = 'overlay';
  ctx.drawImage(GRAIN[Math.floor(t * 30) % GRAIN.length], 0, 0, W, H);
  ctx.globalCompositeOperation = 'source-over';

  drawChip(t);
  drawTexts(t);
  drawCaptions(t);

  if (shot.flash && local < 0.18) { ctx.fillStyle = `rgba(255,255,255,${0.85 * (1 - local / 0.18)})`; ctx.fillRect(0, 0, W, H); }
  // fade out at the very end
  if (t > TL.duration - 0.4) { ctx.fillStyle = `rgba(0,0,0,${clamp((t - (TL.duration - 0.4)) / 0.4, 0, 1)})`; ctx.fillRect(0, 0, W, H); }
  ctx.restore();
  return true;
};
