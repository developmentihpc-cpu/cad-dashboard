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

  return { W, C, SEV, sevLvl, sevLabelOf, reader, slide, fmt, pageLabel, STALE_YEARS };
})();

if (typeof window !== 'undefined') window.DK = DK;
if (typeof module !== 'undefined' && module.exports) module.exports = DK;
