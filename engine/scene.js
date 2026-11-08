// Shared frame renderer for the plant-operators Shorts series.
// render.mjs calls window.setup(timeline, voiceDurations, episodeUrl) once, then
// window.renderFrame(t) per frame and screenshots the 1080x1920 canvas.

const W = 1080, H = 1920;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');
const EMOJI = '"Noto Color Emoji"';

let TL = null, DUR = {}, IMGS = {}, GRAIN = [], CAPTION_GROUPS = [];

// ---------- helpers ----------
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, p) => a + (b - a) * p;
const easeInOut = p => -(Math.cos(Math.PI * p) - 1) / 2;
const easeOut = p => 1 - Math.pow(1 - p, 3);
const easeOutBack = p => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); };
function rng(seed) {
  return function () {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
function particles(n, seed) { const r = rng(seed), out = []; for (let i = 0; i < n; i++) out.push({ a: r(), b: r(), c: r(), d: r() }); return out; }
const RAIN = particles(280, 7), DUST = particles(70, 11), STEAM = particles(16, 23), SNOW = particles(220, 31), SPARKS = particles(60, 41), HEAT = particles(40, 53);

function loadImage(src) { return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error('missing image ' + src)); im.src = src; }); }

function makeGrain() {
  const out = [], r = rng(99);
  for (let k = 0; k < 4; k++) {
    const g = document.createElement('canvas'); g.width = 540; g.height = 960;
    const gc = g.getContext('2d'), id = gc.createImageData(540, 960);
    for (let i = 0; i < id.data.length; i += 4) { const v = Math.floor(r() * 255); id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 22; }
    gc.putImageData(id, 0, 0); out.push(g);
  }
  return out;
}

// Estimated per-word timing from each line's real duration, grouped into 1-3 word captions.
function buildCaptions() {
  const groups = [];
  for (const v of TL.voice) {
    const dur = DUR[v.file] || 2;
    const words = v.text.split(/\s+/);
    const weights = words.map(w => w.replace(/[^A-Za-z0-9']/g, '').length + 1.5 + (/[.!?]$/.test(w) ? 3 : 0) + (/\.\.\.$/.test(w) ? 4 : 0) + (/,$/.test(w) ? 1.5 : 0));
    const total = weights.reduce((a, b) => a + b, 0);
    let acc = 0;
    const timed = words.map((w, i) => { const s = v.t + (acc / total) * dur; acc += weights[i]; return { w, s }; });
    const lineGroups = [];
    let cur = [];
    const flush = () => { if (cur.length) { lineGroups.push({ words: cur, radio: !!v.radio }); cur = []; } };
    for (const tw of timed) {
      const chars = cur.reduce((a, x) => a + x.w.length + 1, 0) + tw.w.length;
      if (cur.length >= 3 || (cur.length && chars > 17)) flush();
      cur.push(tw);
      if (/[.!?]$/.test(tw.w)) flush();
    }
    flush();
    lineGroups.forEach((g, i) => { g.t0 = g.words[0].s; g.t1 = i < lineGroups.length - 1 ? lineGroups[i + 1].words[0].s : v.t + dur + 0.35; });
    groups.push(...lineGroups);
  }
  return groups;
}

window.setup = async function (timeline, durations, epUrl) {
  TL = timeline; DUR = durations;
  const names = [...new Set(TL.shots.filter(s => s.img).map(s => s.img))];
  for (const n of names) IMGS[n] = await loadImage(`${epUrl}/frames/${n}`);
  for (const f of ['900 100px Mont', '800 100px Mont', '400 100px Bangers', `100px ${EMOJI}`]) await document.fonts.load(f);
  GRAIN = makeGrain();
  CAPTION_GROUPS = buildCaptions();
  return { images: names.length, groups: CAPTION_GROUPS.length };
};

// ---------- drawing primitives ----------
function drawCover(img, zoom, cx, cy, ox, oy) {
  const base = Math.max(W / img.width, H / img.height);
  const s = base * zoom, dw = img.width * s, dh = img.height * s;
  let x = clamp(W / 2 - cx * dw, W - dw, 0), y = clamp(H / 2 - cy * dh, H - dh, 0);
  ctx.drawImage(img, x + ox, y + oy, dw, dh);
}
function strokeText(text, x, y, font, fill, stroke, lw, align = 'center') {
  ctx.font = font; ctx.textAlign = align; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round'; ctx.miterLimit = 2;
  if (lw > 0) { ctx.lineWidth = lw; ctx.strokeStyle = stroke; ctx.strokeText(text, x, y); }
  ctx.fillStyle = fill; ctx.fillText(text, x, y);
}
function fitFont(text, weight, maxSize, maxWidth, family = 'Mont') {
  let size = maxSize;
  ctx.font = `${weight} ${size}px ${family}, ${EMOJI}`;
  while (ctx.measureText(text).width > maxWidth && size > 20) { size -= 2; ctx.font = `${weight} ${size}px ${family}, ${EMOJI}`; }
  return size;
}
function roundRect(x, y, w, h, r) {
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}
function vignette(strength) {
  const g = ctx.createRadialGradient(W / 2, H * 0.48, H * 0.28, W / 2, H * 0.5, H * 0.78);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${strength})`);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}

// ---------- effects ----------
function fxRain(t, n, alpha) {
  ctx.save(); ctx.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const p = RAIN[i], speed = 2300 + p.b * 900, len = 40 + p.c * 70;
    const y = ((p.a * (H + 300) + t * speed) % (H + 300)) - 150;
    const x = ((p.d * (W + 400) + y * 0.16) % (W + 400)) - 200;
    ctx.strokeStyle = `rgba(210,225,255,${alpha * (0.5 + p.c * 0.5)})`; ctx.lineWidth = 1.5 + p.b * 2;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + len * 0.16, y + len); ctx.stroke();
  }
  ctx.restore();
}
function fxSnow(t) {
  ctx.save(); ctx.fillStyle = 'rgba(255,255,255,0.85)';
  for (const p of SNOW) {
    const speed = 90 + p.b * 160, r = 2 + p.c * 6;
    const y = ((p.a * (H + 100) + t * speed) % (H + 100)) - 50;
    const x = (p.d * W + Math.sin(t * (0.8 + p.c) + p.a * 10) * 40 + W) % W;
    ctx.globalAlpha = 0.4 + p.c * 0.6; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}
function fxDust(t) {
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  for (const p of DUST) {
    const x = (p.a * W + Math.sin(t * 0.6 + p.c * 9) * 50) % W, y = ((p.b * H - t * (15 + p.d * 30)) % H + H) % H;
    const r = 2 + p.c * 5;
    const g = ctx.createRadialGradient(x, y, 0, x, y, r * 3);
    g.addColorStop(0, `rgba(255,235,190,${0.25 + p.d * 0.45})`); g.addColorStop(1, 'rgba(255,235,190,0)');
    ctx.fillStyle = g; ctx.fillRect(x - r * 3, y - r * 3, r * 6, r * 6);
  }
  ctx.restore();
}
function fxSteam(t) {
  ctx.save();
  for (const p of STEAM) {
    const life = 2.4, ph = ((t + p.a * life) % life) / life;
    const x = 980 - ph * (250 + p.b * 200) + Math.sin(t * 2 + p.c * 6) * 30, y = 420 - ph * (380 + p.d * 200);
    const r = 80 + ph * 260, a = 0.22 * Math.sin(Math.PI * ph);
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, `rgba(255,255,255,${a})`); g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }
  ctx.restore();
}
function fxHeat(t) {
  ctx.save();
  ctx.fillStyle = 'rgba(255,120,0,0.10)'; ctx.fillRect(0, 0, W, H);
  ctx.globalCompositeOperation = 'screen';
  for (const p of HEAT) {
    const life = 3, ph = ((t + p.a * life) % life) / life;
    const x = p.b * W + Math.sin(t * 3 + p.c * 8) * 25, y = H - ph * (H * 0.9);
    const r = 60 + p.d * 90, a = 0.10 * Math.sin(Math.PI * ph);
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, `rgba(255,190,90,${a})`); g.addColorStop(1, 'rgba(255,150,0,0)');
    ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }
  ctx.restore();
}
function fxSparks(t) {
  ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.lineCap = 'round';
  for (const p of SPARKS) {
    const life = 0.9, ph = ((t + p.a * life) % life) / life;
    const ox = W * (0.3 + p.d * 0.4), oy = H * 0.55;
    const ang = -Math.PI / 2 + (p.b - 0.5) * 2.4, sp = 500 + p.c * 900;
    const x = ox + Math.cos(ang) * sp * ph * life, y = oy + Math.sin(ang) * sp * ph * life + 900 * (ph * life) ** 2;
    ctx.strokeStyle = `rgba(255,${180 + p.c * 60},80,${1 - ph})`; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - Math.cos(ang) * 18, y - Math.sin(ang) * 18); ctx.stroke();
  }
  ctx.restore();
}
function fxAlarm(t) {
  const pulse = Math.pow((Math.sin(2 * Math.PI * 1.6 * t) + 1) / 2, 2);
  ctx.save();
  ctx.fillStyle = `rgba(255,0,20,${0.08 + 0.22 * pulse})`; ctx.fillRect(0, 0, W, H);
  const g = ctx.createRadialGradient(560, 150, 10, 560, 150, 700);
  g.addColorStop(0, `rgba(255,60,40,${0.55 * pulse})`); g.addColorStop(1, 'rgba(255,0,0,0)');
  ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}
function fxGlow(t) {
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  const a = 0.22 + 0.1 * Math.sin(t * 1.3);
  const g = ctx.createRadialGradient(W * 0.55, H * 0.33, 20, W * 0.55, H * 0.33, 900);
  g.addColorStop(0, `rgba(255,190,90,${a})`); g.addColorStop(1, 'rgba(255,120,0,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
}
function fxFlicker(t) {
  const f = (Math.sin(t * 53) + Math.sin(t * 31.7) + Math.sin(t * 7.3)) / 3;
  if (f > 0.35) { ctx.fillStyle = `rgba(0,0,0,${(f - 0.35) * 0.9})`; ctx.fillRect(0, 0, W, H); }
}

// ---------- text layers ----------
function drawChips(t) {
  for (const c of TL.chips) {
    if (t < c.t0 || t >= c.t1) continue;
    const p = clamp((t - c.t0) / 0.3, 0, 1), s = easeOutBack(p);
    const font = `900 60px Mont, ${EMOJI}`;
    ctx.save(); ctx.translate(540, 250); ctx.scale(s, s); ctx.rotate(-0.02);
    ctx.font = font;
    const w = ctx.measureText(c.text).width + 90, h = 110;
    ctx.shadowColor = 'rgba(0,0,0,0.5)'; ctx.shadowBlur = 24; ctx.shadowOffsetY = 8;
    roundRect(-w / 2, -h / 2, w, h, 55); ctx.fillStyle = c.bg || '#ff8a00'; ctx.fill();
    ctx.shadowColor = 'transparent'; ctx.lineWidth = 6; ctx.strokeStyle = '#111'; ctx.stroke();
    strokeText(c.text, 0, 4, font, c.fg || '#111', '', 0);
    ctx.restore();
    if (c.tag && p >= 1) {
      ctx.save(); ctx.globalAlpha = clamp((t - c.t0 - 0.3) / 0.3, 0, 1);
      strokeText(c.tag, 540, 160, '800 38px Mont', '#fff', 'rgba(0,0,0,0.85)', 8);
      ctx.restore();
    }
  }
}

function drawCaptions(t) {
  const g = CAPTION_GROUPS.find(g => t >= g.t0 && t < g.t1);
  if (!g) return;
  const y = 1330, gp = clamp((t - g.t0) / 0.1, 0, 1), gs = 0.86 + 0.14 * easeOutBack(gp);
  const size = fitFont(g.words.map(w => w.w).join(' '), 900, 96, 940);
  ctx.save(); ctx.translate(540, y); ctx.scale(gs, gs);
  ctx.font = `900 ${size}px Mont`;
  const space = ctx.measureText(' ').width, widths = g.words.map(w => ctx.measureText(w.w).width);
  let x = -(widths.reduce((a, b) => a + b, 0) + space * (g.words.length - 1)) / 2;
  g.words.forEach((w, i) => {
    const active = t >= w.s && (i === g.words.length - 1 || t < g.words[i + 1].s);
    const danger = (TL.danger || []).includes(w.w);
    const fill = active ? (danger ? '#ff3b30' : '#ffe135') : '#ffffff';
    const pop = active ? 1 + 0.12 * (1 - clamp((t - w.s) / 0.12, 0, 1)) : 1;
    ctx.save(); ctx.translate(x + widths[i] / 2, 0); ctx.scale(pop, pop);
    ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 18; ctx.shadowOffsetY = 6;
    strokeText(w.w, 0, 0, `900 ${size}px Mont`, fill, '#000', Math.round(size * 0.17));
    ctx.shadowColor = 'transparent';
    strokeText(w.w, 0, 0, `900 ${size}px Mont`, fill, '#000', 0);
    ctx.restore();
    x += widths[i] + space;
  });
  ctx.restore();
  if (g.radio) {
    ctx.save(); ctx.globalAlpha = 0.7 + 0.3 * Math.sin(t * 20);
    strokeText('📻 RADIO', 540, y - 115, `900 44px Mont, ${EMOJI}`, '#ffe135', '#000', 9);
    ctx.restore();
  }
}

function drawNote(tx, local) {
  const p = clamp(local / 0.28, 0, 1), s = easeOutBack(p) * (tx.scale || 0.85);
  ctx.save(); ctx.translate(tx.x || 560, tx.y || 900); ctx.rotate(tx.rot ?? -0.07); ctx.scale(s, s);
  ctx.shadowColor = 'rgba(0,0,0,0.45)'; ctx.shadowBlur = 30; ctx.shadowOffsetY = 14;
  ctx.fillStyle = tx.paper || '#ffe873'; ctx.fillRect(-320, -240, 640, 480);
  ctx.shadowColor = 'transparent';
  ctx.fillStyle = 'rgba(0,0,0,0.06)'; ctx.fillRect(-320, -240, 640, 64);
  strokeText(tx.header || '', 0, -170, '900 44px Mont', '#2b2b2b', '', 0);
  ctx.strokeStyle = 'rgba(40,80,200,0.3)'; ctx.lineWidth = 3;
  for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.moveTo(-280, -100 + i * 85); ctx.lineTo(280, -100 + i * 85); ctx.stroke(); }
  const body = tx.lines || [];
  const wp = clamp((local - 0.2) / 0.5, 0, 1);
  ctx.save(); ctx.beginPath(); ctx.rect(-300, -140, 600 * wp, 400); ctx.clip();
  body.forEach((ln, i) => {
    const size = Math.min(tx.size || 110, fitFont(ln, 400, tx.size || 110, 560, 'Bangers'));
    strokeText(ln, 0, -40 + i * (size + 10) - (body.length - 1) * (size + 10) / 2 + 40, `400 ${size}px Bangers`, tx.ink || '#d0122f', '', 0);
  });
  ctx.restore();
  ctx.restore();
}

function drawStamp(tx, local) {
  const p = clamp(local / 0.16, 0, 1), s = lerp(2.2, 1, easeOut(p));
  ctx.save(); ctx.translate(tx.x || 540, tx.y || 900); ctx.rotate(tx.rot ?? -0.18); ctx.scale(s, s); ctx.globalAlpha = p;
  const lines = tx.lines, size = tx.size || 96;
  ctx.font = `900 ${size}px Mont`;
  const w = Math.max(...lines.map(l => ctx.measureText(l).width)) + 80, h = lines.length * (size + 14) + 50;
  ctx.strokeStyle = tx.color || '#e01b24'; ctx.lineWidth = 14; roundRect(-w / 2, -h / 2, w, h, 18); ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,0.12)'; ctx.fill();
  lines.forEach((l, i) => strokeText(l, 0, -((lines.length - 1) * (size + 14)) / 2 + i * (size + 14) + 4, `900 ${size}px Mont`, tx.color || '#e01b24', 'rgba(255,255,255,0.9)', 6));
  ctx.restore();
}

function drawPhone(tx, local) {
  const p = clamp(local / 0.3, 0, 1), s = easeOutBack(p);
  const buzz = Math.sin(local * 60) * 6 * (Math.floor(local * 2) % 2 === 0 ? 1 : 0);
  ctx.save(); ctx.translate(540 + buzz, tx.y || 640); ctx.scale(s, s);
  ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 40;
  roundRect(-300, -170, 600, 340, 50); ctx.fillStyle = 'rgba(20,20,24,0.92)'; ctx.fill();
  ctx.shadowColor = 'transparent';
  for (let k = 0; k < 2; k++) {
    const ph = ((local * 1.2 + k * 0.5) % 1);
    ctx.strokeStyle = `rgba(80,220,120,${1 - ph})`; ctx.lineWidth = 6;
    ctx.beginPath(); ctx.arc(-190, 0, 60 + ph * 50, 0, Math.PI * 2); ctx.stroke();
  }
  ctx.font = `90px ${EMOJI}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('📞', -190, 6);
  strokeText(tx.name || 'PLANT', 60, -40, '900 76px Mont', '#fff', '', 0, 'center');
  strokeText(tx.sub || 'incoming call...', 60, 50, '800 44px Mont', '#9fe8b0', '', 0, 'center');
  ctx.restore();
}

function drawTexts(t) {
  for (const tx of TL.texts) {
    if (t < tx.t0 || t >= tx.t1) continue;
    const local = t - tx.t0;
    const st = tx.style;
    if (st === 'title') {
      const y0 = tx.y || 330;
      tx.lines.forEach((ln, i) => {
        const p = clamp((local - i * 0.2) / 0.28, 0, 1);
        if (p <= 0) return;
        const s = easeOutBack(p), size = fitFont(ln, 900, 118, 960);
        ctx.save(); ctx.translate(540, y0 + i * 150); ctx.rotate(-0.035); ctx.scale(s, s);
        ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 24; ctx.shadowOffsetY = 8;
        strokeText(ln, 0, 0, `900 ${size}px Mont`, i === tx.lines.length - 1 ? '#ffe135' : '#fff', '#000', 20);
        ctx.restore();
      });
      const ep = clamp((local - 0.2 * tx.lines.length - 0.2) / 0.3, 0, 1);
      if (tx.emoji && ep > 0) {
        ctx.save(); ctx.translate(540, y0 + tx.lines.length * 150 + 20); ctx.scale(easeOutBack(ep), easeOutBack(ep)); ctx.rotate(Math.sin(local * 6) * 0.08);
        ctx.font = `130px ${EMOJI}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(tx.emoji, 0, 0); ctx.restore();
      }
    } else if (st === 'action') {
      ctx.save(); ctx.globalAlpha = clamp(local / 0.25, 0, 1);
      const lh = 84, h = tx.lines.length * lh + 60, w = 900, y0 = (tx.y || 1260) - h / 2;
      roundRect(540 - w / 2, y0, w, h, 30); ctx.fillStyle = 'rgba(0,0,0,0.62)'; ctx.fill();
      tx.lines.forEach((ln, i) => { const size = fitFont(ln, 800, 66, 840); strokeText(ln, 540, y0 + 30 + lh / 2 + i * lh, `800 ${size}px Mont`, '#fff', '', 0); });
      ctx.restore();
    } else if (st === 'banner') {
      const p = clamp(local / 0.18, 0, 1), s = lerp(1.9, 1, easeOut(p));
      const shake = local < 0.4 ? (1 - local / 0.4) * 14 : 0;
      ctx.save(); ctx.translate(540 + Math.sin(local * 90) * shake, (tx.y || 330) + Math.cos(local * 70) * shake); ctx.rotate(-0.05); ctx.scale(s, s);
      ctx.globalAlpha = p;
      const bw = 1300, bh = 110 + tx.lines.length * 100;
      ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 30; ctx.fillStyle = tx.bg || '#ffd400'; ctx.fillRect(-bw / 2, -bh / 2, bw, bh);
      ctx.shadowColor = 'transparent';
      ctx.save(); ctx.beginPath(); ctx.rect(-bw / 2, -bh / 2, bw, 34); ctx.rect(-bw / 2, bh / 2 - 34, bw, 34); ctx.clip();
      ctx.fillStyle = '#111';
      for (let x = -bw / 2 - 100; x < bw / 2 + 100; x += 60) { ctx.beginPath(); ctx.moveTo(x, -bh / 2); ctx.lineTo(x + 30, -bh / 2); ctx.lineTo(x + 30 + bh, bh / 2); ctx.lineTo(x + bh, bh / 2); ctx.closePath(); ctx.fill(); }
      ctx.restore();
      tx.lines.forEach((ln, i) => { const size = fitFont(ln, 900, 100, 980); strokeText(ln, 0, -((tx.lines.length - 1) * 104) / 2 + i * 104 + 4, `900 ${size}px Mont`, tx.fg || '#111', '', 0); });
      ctx.restore();
    } else if (st === 'caption_static') {
      const s = 0.86 + 0.14 * easeOutBack(clamp(local / 0.12, 0, 1));
      ctx.save(); ctx.translate(540, tx.y || 1330); ctx.scale(s, s);
      tx.lines.forEach((ln, i) => { const size = fitFont(ln, 900, 110, 960); strokeText(ln, 0, i * 120, `900 ${size}px Mont`, tx.color || '#ffe135', '#000', 18); });
      ctx.restore();
    } else if (st === 'label') {
      const p = clamp(local / 0.25, 0, 1), s = easeOutBack(p);
      ctx.save(); ctx.translate(540, tx.y || 260); ctx.scale(s, s);
      tx.lines.forEach((ln, i) => {
        const size = fitFont(ln, 900, tx.size || 92, 960);
        ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 20;
        strokeText(ln, 0, i * (size + 16), `900 ${size}px Mont, ${EMOJI}`, tx.color || '#fff', '#000', 16);
      });
      ctx.restore();
    } else if (st === 'note') {
      drawNote(tx, local);
    } else if (st === 'stamp') {
      drawStamp(tx, local);
    } else if (st === 'phone') {
      drawPhone(tx, local);
    } else if (st === 'cta') {
      ctx.save(); ctx.globalAlpha = clamp(local / 0.25, 0, 1);
      tx.lines.forEach((ln, i) => { const size = fitFont(ln, 900, 64, 960); strokeText(ln, 540, 1500 + i * 82, `900 ${size}px Mont`, i === tx.lines.length - 1 ? '#ffe135' : '#fff', '#000', 13); });
      ctx.font = `96px ${EMOJI}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText('👇', 540, 1500 + tx.lines.length * 82 + 60 - Math.abs(Math.sin(local * 7)) * 26);
      ctx.restore();
    }
  }
}

function drawCard(shot, local) {
  ctx.fillStyle = '#050505'; ctx.fillRect(0, 0, W, H);
  const txt = shot.card, color = shot.color || '#ff3b30';
  const n = Math.floor(clamp(local / 0.45, 0, 1) * txt.length + 0.0001);
  let shown = txt.slice(0, n);
  if (n >= txt.length && /\d:\d/.test(txt) && Math.floor(local * 3) % 2 === 1) shown = shown.replace(':', ' ');
  const size = fitFont(txt, 900, 230, 980);
  ctx.save(); ctx.shadowColor = color; ctx.shadowBlur = 50;
  strokeText(shown, 540, 900, `900 ${size}px Mont, ${EMOJI}`, color, '', 0);
  ctx.restore();
  if (shot.sub) {
    ctx.save(); ctx.globalAlpha = clamp((local - 0.5) / 0.3, 0, 1);
    strokeText(shot.sub, 540, 1100, `800 ${fitFont(shot.sub, 800, 64, 960)}px Mont`, '#ffffff', '', 0);
    ctx.restore();
  }
}

// ---------- main ----------
window.renderFrame = function (t) {
  const shot = TL.shots.find(s => t >= s.t0 && t < s.t1) || TL.shots[TL.shots.length - 1];
  const local = t - shot.t0, p = clamp(local / (shot.t1 - shot.t0), 0, 1), fx = shot.fx || [];
  ctx.save();
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  if (shot.card) {
    drawCard(shot, local);
  } else {
    let zoom = lerp(shot.zoom[0], shot.zoom[1], easeInOut(p));
    for (const hit of shot.punch || []) zoom += 0.12 * easeOut(clamp((t - hit) / 0.1, 0, 1));
    zoom *= 1 + 0.04 * (1 - easeOut(clamp(local / 0.25, 0, 1)));  // snap-in on every cut
    let ox = 0, oy = 0;
    if (fx.includes('shake')) { const a = 12; ox = a * (Math.sin(t * 41) + 0.5 * Math.sin(t * 23.7)); oy = a * (Math.cos(t * 37) + 0.5 * Math.sin(t * 29.3)); zoom *= 1.03; }
    if (fx.includes('shake_small')) { const a = 6; ox = a * Math.sin(t * 31); oy = a * Math.cos(t * 27); zoom *= 1.015; }
    ctx.filter = 'contrast(1.05) saturate(1.08)';
    drawCover(IMGS[shot.img], zoom, lerp(shot.cx[0], shot.cx[1], easeInOut(p)), lerp(shot.cy[0], shot.cy[1], easeInOut(p)), ox, oy);
    ctx.filter = 'none';
    if (fx.includes('heat')) fxHeat(t);
    if (fx.includes('dust')) fxDust(t);
    if (fx.includes('steam')) fxSteam(t);
    if (fx.includes('snow')) fxSnow(t);
    if (fx.includes('rain')) fxRain(t, 280, 0.45);
    if (fx.includes('rain_light')) fxRain(t, 120, 0.3);
    if (fx.includes('sparks')) fxSparks(t);
    if (fx.includes('alarm')) fxAlarm(t);
    if (fx.includes('glow')) fxGlow(t);
    if (fx.includes('flicker')) fxFlicker(t);
    if (fx.includes('darken')) { ctx.fillStyle = `rgba(0,0,0,${0.12 + 0.18 * p})`; ctx.fillRect(0, 0, W, H); vignette(0.5 + 0.3 * p); }
    vignette(0.42);
  }
  ctx.globalCompositeOperation = 'overlay';
  ctx.drawImage(GRAIN[Math.floor(t * 30) % GRAIN.length], 0, 0, W, H);
  ctx.globalCompositeOperation = 'source-over';
  drawChips(t);
  drawTexts(t);
  drawCaptions(t);
  if (shot.flash && local < 0.18) { ctx.fillStyle = `rgba(255,255,255,${0.85 * (1 - local / 0.18)})`; ctx.fillRect(0, 0, W, H); }
  if (t > TL.duration - 0.4) { ctx.fillStyle = `rgba(0,0,0,${clamp((t - (TL.duration - 0.4)) / 0.4, 0, 1)})`; ctx.fillRect(0, 0, W, H); }
  ctx.restore();
  return true;
};
