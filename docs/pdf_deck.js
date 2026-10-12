/* pdf_deck.js — renders the ODA report decks to PDF in the browser.
 *
 * PdfDeck is a stand-in for the PptxGenJS constructor. The deck builders
 * (country_deck.js, region_deck.js) draw through the same calls — addSlide,
 * addText, addShape, addImage, addTable — and PdfDeck records them, paints each
 * slide on a canvas with PowerPoint's layout rules (inch grid, 0.1/0.05 in text
 * insets, single line spacing) and assembles the pages with jsPDF.
 * Arabic text is shaped by the browser; Sakkal Majalla (a Windows font) is
 * replaced by Noto Naskh Arabic, which looks close and loads as a web font.
 *
 * Usage: buildCountryDeck({ ..., PptxGenJS: PdfDeck, output:'blob' }) → PDF Blob.
 */
'use strict';

const PDF_DPI = 180;                                     // canvas pixels per inch (13.33 in → 2400 px wide)
const PDF_FONT = { 'Sakkal Majalla': { family:'Noto Naskh Arabic', scale:0.86 } };
const PDF_JSPDF_URL = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';

let _pdfLib = null;
function pdfLoadJsPDF() {
  if (window.jspdf) return Promise.resolve(window.jspdf);
  if (!_pdfLib) _pdfLib = new Promise((res, rej) => {
    const s = document.createElement('script'); s.src = PDF_JSPDF_URL;
    s.onload = () => window.jspdf ? res(window.jspdf) : rej(new Error('PDF library did not load'));
    s.onerror = () => { _pdfLib = null; rej(new Error('PDF library could not be downloaded')); };
    document.head.appendChild(s);
  });
  return _pdfLib;
}

class PdfDeck {
  constructor() {
    this.ShapeType = { rect:'rect', roundRect:'roundRect', ellipse:'ellipse', line:'line' };
    this.slides = []; this._layouts = {}; this.W = 10; this.H = 5.625; this.title = ''; this.author = '';
  }
  defineLayout(l) { this._layouts[l.name] = l; }
  set layout(name) { const l = this._layouts[name]; if (l) { this.W = l.width; this.H = l.height; } }
  get layout() { return ''; }
  addSlide() {
    const ops = []; this.slides.push(ops);
    return {
      addText: (t, o) => { ops.push({ k:'text', t, o: o || {} }); },
      addShape: (type, o) => { ops.push({ k:'shape', type, o: o || {} }); },
      addImage: o => { ops.push({ k:'image', o: o || {} }); },
      addTable: (rows, o) => { ops.push({ k:'table', rows, o: o || {} }); },
    };
  }
  writeFile(opts) { return this.write().then(b => { const a = document.createElement('a'); a.href = URL.createObjectURL(b);
    a.download = String((opts && opts.fileName) || 'report.pdf').replace(/\.pptx$/i, '.pdf'); a.click(); }); }
  async write() {
    const { jsPDF } = await pdfLoadJsPDF();
    await pdfFontsReady(this.slides);
    const W = this.W, H = this.H;
    const doc = new jsPDF({ orientation:'landscape', unit:'in', format:[W, H], compress:true });
    doc.setProperties({ title: this.title || '', author: this.author || '', creator:'ODA Country Assessment Dashboard' });
    const cv = document.createElement('canvas'); cv.width = Math.round(W * PDF_DPI); cv.height = Math.round(H * PDF_DPI);
    const g = cv.getContext('2d');
    const imgs = await pdfLoadImages(this.slides);
    for (let i = 0; i < this.slides.length; i++) {
      g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#FFFFFF'; g.fillRect(0, 0, cv.width, cv.height);
      g.setTransform(PDF_DPI, 0, 0, PDF_DPI, 0, 0);           // draw in inches
      this.slides[i].forEach(op => pdfDrawOp(g, op, imgs));
      if (i) doc.addPage([W, H], 'landscape');
      doc.addImage(cv.toDataURL('image/jpeg', 0.9), 'JPEG', 0, 0, W, H, undefined, 'FAST');
    }
    return doc.output('blob');
  }
}

// ── helpers ──
const pdfCol = c => c ? (String(c).startsWith('#') ? c : '#' + c) : null;
function pdfFace(face) { const m = PDF_FONT[face]; return m ? m : { family: face || 'Montserrat', scale: 1 }; }
function pdfFontStr(o, sizePt) {
  const f = pdfFace(o.fontFace), px = (sizePt || 12) * f.scale / 72 * PDF_DPI;   // pixels
  return { css: `${o.bold ? 700 : 400} ${px}px "${f.family}", "IBM Plex Sans Arabic", "Inter", sans-serif`, px };
}
async function pdfFontsReady(slides) {
  const want = new Set();
  slides.forEach(ops => ops.forEach(op => {
    const add = o => { if (!o) return; const f = pdfFace(o.fontFace).family; want.add('400 20px "' + f + '"'); want.add('700 20px "' + f + '"'); };
    add(op.o); if (Array.isArray(op.t)) op.t.forEach(r => add(Object.assign({}, op.o, r.options)));
    if (op.rows) op.rows.forEach(r => r.forEach(c => add(Object.assign({}, op.o, c && c.options))));
  }));
  try { await Promise.all([...want].map(f => document.fonts.load(f, 'Aa ع'))); } catch (e) {}
}
async function pdfLoadImages(slides) {
  const map = new Map();
  slides.forEach(ops => ops.forEach(op => { if (op.k === 'image') { const src = op.o.data || op.o.path; if (src && !map.has(src)) map.set(src, null); } }));
  await Promise.all([...map.keys()].map(src => new Promise(res => {
    const im = new Image(); im.crossOrigin = 'anonymous';
    im.onload = () => { map.set(src, im); res(); }; im.onerror = () => res(); im.src = src;
  })));
  return map;
}

function pdfDrawOp(g, op, imgs) {
  const o = op.o;
  if (op.k === 'shape') return pdfShape(g, op.type, o);
  if (op.k === 'image') { const im = imgs.get(o.data || o.path); if (im) g.drawImage(im, o.x, o.y, o.w, o.h); return; }
  if (op.k === 'text') return pdfText(g, op.t, o);
  if (op.k === 'table') return pdfTable(g, op.rows, o);
}
function pdfShape(g, type, o) {
  const { x = 0, y = 0, w = 0, h = 0 } = o;
  const fill = o.fill && o.fill.color ? pdfCol(o.fill.color) : null;
  const ln = o.line && o.line.type !== 'none' && o.line.color ? { col: pdfCol(o.line.color), w: (o.line.width || o.line.pt || 0.75) / 72 } : null;
  g.beginPath();
  if (type === 'line') { g.moveTo(x, y); g.lineTo(x + w, y + h); if (ln) { g.strokeStyle = ln.col; g.lineWidth = ln.w; g.stroke(); } return; }
  if (type === 'ellipse') g.ellipse(x + w / 2, y + h / 2, w / 2, h / 2, 0, 0, Math.PI * 2);
  else if (type === 'roundRect') { const r = Math.min(o.rectRadius || 0.1, w / 2, h / 2); g.roundRect ? g.roundRect(x, y, w, h, r) : g.rect(x, y, w, h); }
  else g.rect(x, y, w, h);
  if (fill) { g.fillStyle = fill; g.fill(); }
  if (ln) { g.strokeStyle = ln.col; g.lineWidth = ln.w; g.stroke(); }
}

// Text box: rich runs, word wrap, alignment, vertical anchor, shrink-to-fit, letter spacing, RTL.
function pdfText(g, t, o, inset) {
  const runs0 = (Array.isArray(t) ? t : [{ text: t, options: {} }]).map(r => ({ text: String(r.text == null ? '' : r.text), o: Object.assign({}, o, r.options || {}) }));
  const ins = inset || { l:0.1, r:0.1, t:0.05, b:0.05 };
  const D = PDF_DPI, bx = (o.x + ins.l) * D, by = (o.y + ins.t) * D, bw = Math.max(1, (o.w - ins.l - ins.r) * D), bh = Math.max(1, (o.h - ins.t - ins.b) * D);
  if (o.fill && o.fill.color) { g.fillStyle = pdfCol(o.fill.color); g.fillRect(o.x, o.y, o.w, o.h); }
  g.save(); g.beginPath(); g.rect(o.x - 0.5, o.y - 0.5, o.w + 1, o.h + 1); g.clip(); g.setTransform(1, 0, 0, 1, 0, 0);   // text is laid out in pixels
  const rtl = !!o.rtlMode;
  let scale = 1, lines;
  for (let tries = 0; tries < 12; tries++) {
    lines = pdfLayout(g, runs0, bw, scale, o.wrap !== false);
    const total = lines.reduce((s, l) => s + l.h, 0);
    if (o.fit !== 'shrink' || total <= bh * 1.02) break;
    scale *= 0.92;
  }
  const total = lines.reduce((s, l) => s + l.h, 0);
  const va = o.valign || 'top';
  let yy = va === 'middle' ? by + (bh - total) / 2 : va === 'bottom' ? by + bh - total : by;
  const al = o.align || 'left';

  lines.forEach(l => {
    const base = yy + l.h * 0.5;
    let cx = al === 'center' ? bx + (bw - l.w) / 2 : al === 'right' ? bx + bw - l.w : bx;
    const segs = rtl ? l.segs.slice().reverse() : l.segs;        // right-to-left: first run sits at the right
    segs.forEach(s => {
      g.font = s.font; g.fillStyle = pdfCol(s.o.color) || '#000000';
      g.direction = rtl ? 'rtl' : 'ltr'; g.textAlign = 'left'; g.textBaseline = 'middle';
      try { g.letterSpacing = s.ls + 'px'; } catch (e) {}
      if (rtl) { g.textAlign = 'right'; g.fillText(s.text, cx + s.w, base); } else g.fillText(s.text, cx, base);
      cx += s.w;
    });
    yy += l.h;
  });
  try { g.letterSpacing = '0px'; } catch (e) {}
  g.restore();
}
function pdfLayout(g, runs, maxW, scale, wrap) {
  const lines = []; let cur = { segs: [], w: 0, h: 0 };
  const push = () => { if (!cur.h) cur.h = 0.2 * scale * PDF_DPI; lines.push(cur); cur = { segs: [], w: 0, h: 0 }; };
  runs.forEach(r => {
    const size = (r.o.fontSize || 12) * scale, f = pdfFontStr(r.o, size), ls = (r.o.charSpacing || 0) / 72 * PDF_DPI;
    const lh = f.px * 1.2;
    const measure = s => { g.font = f.css; try { g.letterSpacing = ls + 'px'; } catch (e) {} return g.measureText(s).width; };
    String(r.text).split('\n').forEach((para, pi) => {
      if (pi > 0) push();
      const toks = para.match(/\S+\s*|\s+/g) || [''];
      toks.forEach(tok => {
        const w = measure(tok);
        if (wrap && cur.w + w > maxW && cur.w > 0) {                    // wrap before this word
          const last = cur.segs[cur.segs.length - 1];
          if (last) { const trimmed = last.text.replace(/\s+$/, ''); if (trimmed !== last.text) { cur.w -= last.w - measure(trimmed); last.w = measure(trimmed); last.text = trimmed; } }
          push(); if (!tok.trim()) return;
        }
        const last = cur.segs[cur.segs.length - 1];
        if (last && last.font === f.css && last.o === r.o) { last.text += tok; last.w += w; }
        else cur.segs.push({ text: tok, w, font: f.css, o: r.o, ls });
        cur.w += w; cur.h = Math.max(cur.h, lh);
      });
    });
  });
  if (cur.segs.length || !lines.length) push();
  return lines;
}
function pdfTable(g, rows, o) {
  const colW = o.colW || rows[0].map(() => o.w / rows[0].length), rh = o.rowH || 0.3;
  const border = o.border && o.border.type !== 'none' ? { col: pdfCol(o.border.color || 'CCCCCC'), w: (o.border.pt || 0.5) / 72 } : null;
  let y = o.y;
  rows.forEach(row => {
    let x = o.x;
    row.forEach((cell, ci) => {
      const c = typeof cell === 'object' && cell ? cell : { text: String(cell) };
      const co = Object.assign({}, o, c.options || {}, { x, y, w: colW[ci], h: rh, fit: 'shrink' });
      delete co.border; delete co.colW; delete co.rowH;
      if (co.fill && co.fill.color) { g.fillStyle = pdfCol(co.fill.color); g.fillRect(x, y, colW[ci], rh); }
      delete co.fill;
      pdfText(g, c.text, co, { l:0.05, r:0.05, t:0.03, b:0.03 });
      if (border) { g.strokeStyle = border.col; g.lineWidth = border.w; g.strokeRect(x, y, colW[ci], rh); }
      x += colW[ci];
    });
    y += rh;
  });
}

if (typeof window !== 'undefined') window.PdfDeck = PdfDeck;
