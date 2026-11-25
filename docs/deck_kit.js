/* deck_kit.js — shared building blocks for the ODA report decks (country_deck.js,
 * region_deck.js): palette, fonts, the shared severity scale, value hygiene
 * (missing / impossible / outdated values) and right-to-left mirroring for Arabic.
 *
 * Arabic decks are built on the same 13.333 × 7.5 in grid as English ones; every
 * shape, image, text box and table is mirrored horizontally (x → W − x − w),
 * text is right-aligned with rtlMode, and the font switches to Sakkal Majalla
 * (+2 pt, per the ODA brand guide).
 */
'use strict';

const DK = (() => {
  const W = 13.333;
  // White / sky / gold — matches the dashboard
  const C = {
    INK:'0F2A40', NAVY:'14324A', SKY:'3E9BD6', SKY_DK:'1B6FA8', SKY_LT:'DCEDF9', SKY_PALE:'F3F8FC',
    GOLD:'B08A3E', GOLD_LT:'D9BF86', GOLD_PALE:'F5EEDF', WHITE:'FFFFFF', MUTE:'5D7186', FAINT:'8DA0B3',
    LINE:'E4ECF3', CARD:'F6F9FC', HAIR:'C9D6E2',
  };
  const SEV = (typeof SEV_COLORS !== 'undefined') ? SEV_COLORS
    : { fill:['E5484D','F5871F','F5C518','1FAF6B'], tint:['FFE0E1','FFE9D2','FFF5CC','DDF4E7'], text:['C8282E','C2620A','8C6A00','13804C'], onFill:['FFFFFF','FFFFFF','5C4600','FFFFFF'] };
  const sevLvl = (id, v) => (typeof sevLevel === 'function') ? sevLevel(id, v) : null;
  const sevLabelOf = (lvl, ar) => (typeof SEV_LABELS !== 'undefined' ? SEV_LABELS[ar ? 'ar' : 'en'] : ['Severe','High concern','Moderate','On track'])[lvl];

  // Values that cannot genuinely be zero (a 0 here is a reporting gap, not a fact)
  const NONZERO = new Set(['SE.XPD.TOTL.GD.ZS','SH.XPD.CHEX.GD.ZS','SH.MED.PHYS.ZS','SH.MED.BEDS.ZS','SE.ADT.LITR.ZS',
    'SE.ADT.1524.LT.ZS','SE.PRM.CMPT.ZS','SE.SEC.ENRR','SE.PRM.ENRR','SP.DYN.LE00.IN','GC.TAX.TOTL.GD.ZS','AG.YLD.CREL.KG',
    'EG.ELC.ACCS.ZS','SH.H2O.BASW.ZS','SH.STA.BASS.ZS','IT.NET.USER.ZS','SP.POP.TOTL','NY.GDP.PCAP.PP.CD']);
  const STALE_YEARS = 8;   // older than this is flagged as outdated and kept out of the narrative
  // Below these a reported value is not credible (e.g. 0.04% of GDP on education) → treated as missing
  const PLAUSIBLE_MIN = { 'SE.XPD.TOTL.GD.ZS':0.5, 'SH.XPD.CHEX.GD.ZS':0.5, 'GC.TAX.TOTL.GD.ZS':0.5, 'SH.MED.PHYS.ZS':0.005, 'SP.DYN.LE00.IN':30 };

  // Clean accessor over a {id:{value,year}} map → { v, y, stale } or null
  function reader(data) {
    const now = new Date().getFullYear();
    return id => {
      const d = data && data[id];
      if (!d || d.value == null || isNaN(d.value)) return null;
      if (NONZERO.has(id) && Number(d.value) <= 0) return null;
      if (PLAUSIBLE_MIN[id] != null && Number(d.value) < PLAUSIBLE_MIN[id]) return null;
      const y = d.year ? Number(String(d.year).slice(0, 4)) : null;
      return { v: Number(d.value), y, stale: !!(y && now - y > STALE_YEARS) };
    };
  }

  // Right-to-left slide wrapper: mirrors geometry, right-aligns text, Arabic font.
  function slide(p, ar) {
    const sl = p.addSlide();
    const AR_FONT = 'Sakkal Majalla';
    const fontFix = o => {
      if (!ar) return o;
      o.fontFace = AR_FONT; if (o.fontSize) o.fontSize = o.fontSize + 2; delete o.charSpacing;
      o.rtlMode = true; o.lang = 'ar-SA'; return o;
    };
    const mx = o => (ar && o && o.x != null && o.w != null) ? Object.assign({}, o, { x: W - o.x - o.w }) : Object.assign({}, o);
    const flip = a => !ar ? a : a === 'right' ? 'left' : a === 'center' ? 'center' : 'right';
    const runs = t => Array.isArray(t) ? t.map(r => ({ text: r.text, options: fontFix(Object.assign({}, r.options || {})) })) : t;
    return {
      raw: sl,
      shape(type, o) { return sl.addShape(type, mx(o)); },
      image(o) { return sl.addImage(mx(o)); },
      text(t, o) { const q = fontFix(mx(o)); q.align = flip(q.align || 'left'); return sl.addText(runs(t), q); },
      table(rows, o) {
        if (ar) rows = rows.map(r => r.slice().reverse().map(c => { const cell = typeof c === 'object' ? c : { text: String(c) };
          const opt = fontFix(Object.assign({}, cell.options || {})); opt.align = flip(opt.align || o.align || 'left'); return { text: cell.text, options: opt }; }));
        const q = Object.assign({}, mx(o), ar ? { colW: (o.colW || []).slice().reverse(), fontFace: AR_FONT, fontSize: (o.fontSize || 9) + 1.5 } : {});
        return sl.addTable(rows, q);
      },
    };
  }

  // Formatting (Western digits in both languages; Arabic unit words)
  function fmt(ar) {
    const big = (v, money) => {
      const pre = money ? '$' : '';
      if (v >= 1e12) return pre + (v / 1e12).toFixed(1) + (ar ? ' ترليون' : 'T');
      if (v >= 1e9)  return pre + (v / 1e9).toFixed(v >= 1e10 ? 0 : 1) + (ar ? ' مليار' : 'B');
      if (v >= 1e6)  return pre + (v / 1e6).toFixed(1) + (ar ? ' مليون' : 'M');
      return pre + Math.round(v).toLocaleString('en-US');
    };
    return {
      pct: (r, d = 0) => r ? r.v.toFixed(d) + '%' : '—',
      num: (r, d = 0) => r ? (d ? r.v.toFixed(d) : Math.round(r.v).toLocaleString('en-US')) : '—',
      pop: r => r ? big(r.v) : '—',
      money: r => r ? (ar ? Math.round(r.v).toLocaleString('en-US') + ' دولار' : '$' + Math.round(r.v).toLocaleString('en-US')) : '—',
      bigMoney: r => r ? big(r.v, true) : '—',
    };
  }

  // "03 / 09" in English; "3 من 9" in Arabic (a slash pair would display reversed right-to-left)
  const pageLabel = (page, total, ar) => ar ? page + ' من ' + total : String(page).padStart(2, '0') + ' / ' + String(total).padStart(2, '0');

  // Map slots (inches). The dashboard renders each map image at exactly this aspect ratio,
  // and the decks place it at exactly this size — so maps are never stretched.
  // line icons (Lucide, ISC licence) — SVG bodies on a 24×24 grid; rasterised to PNG by the dashboard (repIcons)
  const ICONS = {
    briefcase: '<path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect width="20" height="14" x="2" y="6" rx="2"/>',
    droplet: '<path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    zap: '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    sprout: '<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/>',
    graduation: '<path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/>',
    heartPulse: '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="M3.22 12H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27"/>',
    building: '<rect width="16" height="20" x="4" y="2" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/>',
    ship: '<path d="M2 21c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1 .6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M19.38 20A11.6 11.6 0 0 0 21 14l-9-4-9 4c0 2.9.94 5.34 2.81 7.76"/><path d="M19 13V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v6"/><path d="M12 10v4"/><path d="M12 2v3"/>',
    landmark: '<line x1="3" x2="21" y1="22" y2="22"/><line x1="6" x2="6" y1="18" y2="11"/><line x1="10" x2="10" y1="18" y2="11"/><line x1="14" x2="14" y1="18" y2="11"/><line x1="18" x2="18" y1="18" y2="11"/><polygon points="12 2 20 7 4 7"/>',
  };
  const MAP_SLOTS = { country: { w:6.0, h:4.3 }, region: { w:7.55, h:5.35 }, sub: { w:7.3, h:5.08 }, focus: { w:4.6, h:5.3 }, atlas: { w:3.2, h:4.35 } };
  // Fit an image of the given width/height ratio inside a box, centred, without distortion
  const contain = (ratio, x, y, w, h) => {
    const r = ratio || w / h; let iw = w, ih = w / r;
    if (ih > h) { ih = h; iw = h * r; }
    return { x: x + (w - iw) / 2, y: y + (h - ih) / 2, w: iw, h: ih };
  };

  return { W, C, SEV, sevLvl, sevLabelOf, reader, slide, fmt, pageLabel, STALE_YEARS, MAP_SLOTS, ICONS, contain };
})();

if (typeof window !== 'undefined') window.DK = DK;
if (typeof module !== 'undefined' && module.exports) module.exports = DK;
