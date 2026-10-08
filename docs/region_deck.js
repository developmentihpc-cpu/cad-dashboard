/* region_deck.js — ODA regional needs-assessment deck (English or Arabic).
 *
 * cover · regional overview (need-index map) · needs at a glance · need ranking ·
 * comparison table · one profile per
 * country · method & sources. Ratings use the shared severity scale (severity.js),
 * identical to the dashboard. Requires deck_kit.js + severity.js (+ i18n_ar.js).
 *
 * opts: region, countries [{ name, iso2, income, flagData, need, needRank, tier, data }],
 *       dateStr, dataNote, PptxGenJS, lang 'en'|'ar', output 'blob' | fileName
 *       (tier = 'hi'|'mid'|'lo' — the country's need tier among ALL tracked countries)
 */
'use strict';

function buildRegionDeck(opts){
  const ar = opts.lang === 'ar';
  const T = (en, a) => ar ? a : en;
  const { C, SEV } = DK;
  const Pptx = opts.PptxGenJS || (typeof PptxGenJS !== 'undefined' ? PptxGenJS : null);
  if (!Pptx) throw new Error('PptxGenJS constructor not provided');
  const regionKey = opts.region || 'Region';
  const REGION = ar && typeof AR_REGION !== 'undefined' ? (AR_REGION[regionKey] || regionKey) : regionKey;
  const cn = c => ar && typeof AR_COUNTRY !== 'undefined' ? (AR_COUNTRY[c] || c) : c;
  const incN = code => ar ? (typeof AR_INCOME !== 'undefined' ? AR_INCOME[code] || '' : '') : ({ LIC:'Low income', LMIC:'Lower-middle income', UMIC:'Upper-middle income' }[code] || '');
  const DATE = opts.dateStr || new Date().toLocaleDateString('en-US', { month:'long', year:'numeric' });
  const F = DK.fmt(ar);
  const HEAD = 'Lora', BODY = 'Montserrat';
  const list = (opts.countries || []).map(c => Object.assign({}, c, { R: DK.reader(c.data || {}) }));
  if (!list.length) throw new Error('No countries supplied for ' + regionKey);

  const IND = [
    { id:'SH.DYN.MORT',    en:'Under-5 mortality',  ar:'وفيات الأطفال دون الخامسة', f:r => F.num(r),    u:['/1k','لكل ألف'],     sector:['Health','الصحة'] },
    { id:'SH.STA.MMRT',    en:'Maternal mortality', ar:'وفيات الأمهات',             f:r => F.num(r),    u:['/100k','لكل 100 ألف'], sector:['Health','الصحة'] },
    { id:'SN.ITK.DEFC.ZS', en:'Undernourishment',   ar:'نقص التغذية',              f:r => F.pct(r, 1), sector:['Food security','الأمن الغذائي'] },
    { id:'SH.H2O.BASW.ZS', en:'Basic drinking water', ar:'مياه الشرب الأساسية',     f:r => F.pct(r),    sector:['WASH','المياه والصرف الصحي'] },
    { id:'SH.STA.BASS.ZS', en:'Basic sanitation',   ar:'الصرف الصحي الأساسي',      f:r => F.pct(r),    sector:['WASH','المياه والصرف الصحي'] },
    { id:'EG.ELC.ACCS.ZS', en:'Electricity access', ar:'الوصول إلى الكهرباء',      f:r => F.pct(r),    sector:['Energy','الطاقة'] },
  ];
  const lbl = ind => T(ind.en, ind.ar);
  const fv = (ind, r) => r ? ind.f(r) + (ind.u ? ' ' + ind.u[ar ? 1 : 0] : '') : '—';
  const rule = id => SEV_RULES[id];
  const tgt = id => rule(id).th[2];
  const curLvl = (c, id) => { const r = c.R(id); return r && !r.stale ? DK.sevLvl(id, r.v) : null; };
  const median = arr => { const a = arr.filter(v => v != null).sort((x, y) => x - y); if (!a.length) return null; const m = Math.floor(a.length / 2); return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2; };
  const gv = (c, id) => { const r = c.R(id); return r ? r.v : null; };

  // aggregates
  const pop = list.reduce((s, c) => s + (gv(c, 'SP.POP.TOTL') || 0), 0);
  const without = id => list.reduce((s, c) => { const p = gv(c, 'SP.POP.TOTL'), v = gv(c, id); return p && v != null ? s + p * (1 - v / 100) : s; }, 0);
  const meds = {}; IND.forEach(i => meds[i.id] = median(list.map(c => gv(c, i.id))));
  const medGdp = median(list.map(c => gv(c, 'NY.GDP.PCAP.PP.CD')));
  const inc = { LIC:0, LMIC:0, UMIC:0 }; list.forEach(c => { if (inc[c.income] != null) inc[c.income]++; });
  const ranked = list.filter(c => c.need != null).sort((a, b) => b.need - a.need);
  const byNeed = list.slice().sort((a, b) => (b.need == null ? -1 : b.need) - (a.need == null ? -1 : a.need));
  const people = v => F.pop({ v });

  // ── deck ──
  const p = new Pptx();
  p.defineLayout({ name:'W', width:13.333, height:7.5 }); p.layout = 'W';
  p.title = REGION + T(' — Regional Assessment', ' — التقييم الإقليمي'); p.author = T('ODA Country Assessment Dashboard', 'لوحة تقييم الدول — مكتب الشؤون التنموية');
  if (ar) p.rtlMode = true;
  let PAGE = 0, TOTAL = 0; const S = [];
  const newSlide = bg => { const sl = DK.slide(p, ar); sl.shape(p.ShapeType.rect, { x:0, y:0, w:13.333, h:7.5, fill:{ color: bg || C.WHITE }, line:{ type:'none' } }); PAGE++; return sl; };
  const eyebrow = (sl, t, x, y, w, col) => sl.text(ar ? t : String(t).toUpperCase(), { x, y, w, h:0.24, fontFace:BODY, fontSize:9, bold:true, color: col || C.GOLD, charSpacing:2.2 });
  const head = (sl, eb, title, stmt) => { eyebrow(sl, eb, 0.5, 0.36, 10);
    sl.text([{ text:title, options:{ bold:true, color:C.INK } }, { text: stmt ? '  —  ' + stmt : '', options:{ color:C.MUTE } }], { x:0.5, y:0.6, w:12.33, h:0.56, fontFace:HEAD, fontSize:18, valign:'middle', fit:'shrink' }); };
  const foot = (sl, src, dark) => {
    const lc = dark ? '3A5068' : C.LINE, tc = dark ? '9FB2C5' : C.FAINT;
    sl.shape(p.ShapeType.line, { x:0.5, y:7.1, w:12.33, h:0, line:{ color:lc, width:0.5 } });
    sl.text(T('Source: ', 'المصدر: ') + src, { x:0.5, y:7.15, w:9.6, h:0.24, fontFace:BODY, fontSize:8, color:tc, valign:'middle' });
    sl.text([{ text:'ODA', options:{ bold:true, color: dark ? C.GOLD_LT : C.NAVY } }, { text:'   ' + DK.pageLabel(PAGE, TOTAL, ar), options:{ color:tc } }],
      { x:10.4, y:7.15, w:2.43, h:0.24, fontFace:BODY, fontSize:8, align:'right', valign:'middle' });
  };
  const SRC_LINE = T('World Bank Open Data · UN IGME · WHO · FAO · WHO/UNICEF JMP · IEA', 'بيانات البنك الدولي · فريق الأمم المتحدة لتقدير وفيات الأطفال · منظمة الصحة العالمية · الفاو · برنامج الرصد المشترك · وكالة الطاقة الدولية');
  const card = (sl, x, y, w, h, value, label, sub, L) => {
    sl.shape(p.ShapeType.rect, { x, y, w, h, fill:{ color:C.CARD }, line:{ type:'none' } });
    sl.shape(p.ShapeType.rect, { x, y, w, h:0.05, fill:{ color: L == null ? C.GOLD : SEV.fill[L] }, line:{ type:'none' } });
    sl.text(String(value), { x:x + 0.16, y:y + 0.14, w:w - 0.3, h:0.5, fontFace:HEAD, fontSize: String(value).length > 9 ? 19 : 24, bold:true, color: L != null && L <= 1 ? SEV.text[L] : C.INK, valign:'middle', fit:'shrink' });
    sl.text(label, { x:x + 0.16, y:y + 0.64, w:w - 0.3, h:0.28, fontFace:BODY, fontSize:8.6, bold:true, color:C.INK, valign:'top', fit:'shrink' });
    if (sub) sl.text(sub, { x:x + 0.16, y:y + h - 0.3, w:w - 0.3, h:0.22, fontFace:BODY, fontSize:7.2, color:C.FAINT, valign:'top' });
  };
  const bullets = (sl, items, x, y, w) => { let yy = y; const per = Math.max(52, Math.round(w * 13));
    items.forEach(t => { const lines = Math.max(1, Math.ceil(String(t).length / per)), hh = 0.2 * lines + 0.1;
      sl.shape(p.ShapeType.ellipse, { x:x + 0.02, y:yy + 0.07, w:0.08, h:0.08, fill:{ color:C.GOLD }, line:{ type:'none' } });
      sl.text(t, { x:x + 0.22, y:yy, w:w - 0.22, h:hh, fontFace:BODY, fontSize:10, color:C.INK, valign:'top', wrap:true }); yy += hh + 0.12; });
    return yy; };

  // ══ 1 · COVER ══
  S.push(() => {
    const sl = newSlide(C.NAVY);
    sl.shape(p.ShapeType.rect, { x:0, y:7.0, w:13.333, h:0.5, fill:{ color:C.INK }, line:{ type:'none' } });
    sl.shape(p.ShapeType.rect, { x:0, y:6.96, w:13.333, h:0.04, fill:{ color:C.GOLD }, line:{ type:'none' } });
    if (opts.logo && opts.logo.data) {
      sl.shape(p.ShapeType.roundRect, { x:0.6, y:0.55, w:2.9, h:0.9, rectRadius:0.08, fill:{ color:C.WHITE }, line:{ type:'none' } });
      const lg = DK.contain(opts.logo.ratio, 0.75, 0.66, 2.6, 0.68);
      sl.image({ data:opts.logo.data, x:lg.x, y:lg.y, w:lg.w, h:lg.h });
    }
    sl.text(T('REGIONAL ASSESSMENT', 'التقييم الإقليمي'), { x:0.6, y:2.25, w:9, h:0.3, fontFace:BODY, fontSize:11, bold:true, color:C.GOLD_LT, charSpacing:3 });
    sl.text(REGION, { x:0.55, y:2.6, w:9.6, h:1.4, fontFace:HEAD, fontSize: REGION.length > 30 ? 36 : 50, bold:true, color:C.WHITE, valign:'top', fit:'shrink' });
    sl.shape(p.ShapeType.rect, { x:0.6, y:4.15, w:1.1, h:0.05, fill:{ color:C.GOLD }, line:{ type:'none' } });
    sl.text(T(`Development needs across ${list.length} countries — health, food security, water and sanitation, and energy — with a profile of every country.`,
              `الاحتياجات التنموية في ${list.length} دولة — الصحة والأمن الغذائي والمياه والصرف الصحي والطاقة — مع ملف تعريفي لكل دولة.`),
      { x:0.6, y:4.4, w:8.6, h:0.8, fontFace:BODY, fontSize:14, color:C.SKY_LT, valign:'top', wrap:true });
    sl.text(list.map(c => cn(c.name)).sort((a, b) => a.localeCompare(b, ar ? 'ar' : 'en')).join('  ·  '), { x:0.6, y:5.35, w:12.1, h:1.4, fontFace:BODY, fontSize:9.5, color:'A9BCCF', valign:'top', wrap:true, fit:'shrink' });
    // big country count, top right
    sl.text(String(list.length), { x:10.3, y:0.5, w:2.4, h:1.1, fontFace:HEAD, fontSize:60, bold:true, color:C.GOLD_LT, align:'right' });
    sl.text(T('countries', 'دولة'), { x:10.3, y:1.55, w:2.4, h:0.3, fontFace:BODY, fontSize:11, color:C.SKY_LT, align:'right' });
    sl.text(DATE, { x:0.6, y:7.05, w:5, h:0.4, fontFace:BODY, fontSize:10, bold:true, color:C.GOLD_LT, valign:'middle' });
    sl.text(T('Office of Development Affairs', 'مكتب الشؤون التنموية'), { x:7.7, y:7.05, w:5.03, h:0.4, fontFace:BODY, fontSize:10, color:C.SKY_LT, align:'right', valign:'middle' });
  });

  // ══ 2 · REGIONAL OVERVIEW — need-index map (country-level data), people, key figures ══
  S.push(() => {
    const sl = newSlide(C.WHITE);
    head(sl, T('Regional overview', 'نظرة عامة على الإقليم'), REGION, T('where needs are greatest, country by country', 'أين يكون الاحتياج أكبر، دولةً بدولة'));
    const M = DK.MAP_SLOTS.region, mx = 0.5, my = 1.35;
    if (opts.mapData) sl.image({ data:opts.mapData, x:mx, y:my, w:M.w, h:M.h });
    else { sl.shape(p.ShapeType.rect, { x:mx, y:my, w:M.w, h:M.h, fill:{ color:C.SKY_PALE }, line:{ type:'none' } });
      sl.text(T('Map unavailable', 'الخريطة غير متاحة'), { x:mx, y:my + M.h / 2 - 0.2, w:M.w, h:0.4, fontFace:BODY, fontSize:11, color:C.FAINT, align:'center' }); }
    // legend under the map: need-index tiers (the map shades each country by its own index)
    const sh = opts.needShades || { hi:'0A6FD1', mid:'2EA0F2', lo:'9ED6FA', none:'C3CDD6' };
    const keys = [[sh.hi, T('Highest-need third', 'الثلث الأعلى احتياجاً')], [sh.mid, T('Middle third', 'الثلث الأوسط')], [sh.lo, T('Lowest third', 'الثلث الأدنى')], [sh.none, T('Not ranked', 'غير مصنّفة')]];
    keys.forEach(([col, t], i) => { const kx = mx + i * 1.85;
      sl.shape(p.ShapeType.rect, { x:kx, y:my + M.h + 0.12, w:0.18, h:0.14, fill:{ color:col }, line:{ type:'none' } });
      sl.text(t, { x:kx + 0.25, y:my + M.h + 0.06, w:1.55, h:0.26, fontFace:BODY, fontSize:7.8, color:C.MUTE, valign:'middle' }); });
    // right column: key figures
    const RX = 8.35, RW = 13.333 - RX - 0.5, ch = 0.98;
    eyebrow(sl, T('The region in numbers', 'الإقليم بالأرقام'), RX, 1.35, RW, C.SKY_DK);
    const cards = [
      [people(pop), T('People in the region', 'سكان الإقليم'), null],
      [people(without('EG.ELC.ACCS.ZS')), T('Without electricity', 'دون كهرباء'), 1],
      [people(without('SH.H2O.BASW.ZS')), T('Without basic drinking water', 'دون مياه شرب أساسية'), 1],
      [people(without('SH.STA.BASS.ZS')), T('Without basic sanitation', 'دون صرف صحي أساسي'), 1],
      [meds['SH.DYN.MORT'] != null ? String(Math.round(meds['SH.DYN.MORT'])) : '—', T('Median under-5 mortality (per 1,000)', 'وسيط وفيات الأطفال دون الخامسة (لكل 1,000)'), meds['SH.DYN.MORT'] != null ? DK.sevLvl('SH.DYN.MORT', meds['SH.DYN.MORT']) : null],
    ];
    cards.forEach(([v, l, L], i) => card(sl, RX, 1.68 + i * (ch + 0.08), RW, ch, v, l, null, L));
    foot(sl, T('ODA need index · World Bank Open Data · Natural Earth (borders) · ', 'مؤشر الاحتياج · بيانات البنك الدولي · Natural Earth (الحدود) · ') + DATE);
  });

  // ══ 3 · NEEDS AT A GLANCE ══
  S.push(() => {
    const sl = newSlide(C.WHITE);
    head(sl, REGION + T(' · regional snapshot', ' · لمحة إقليمية'), T('Needs at a Glance', 'الاحتياجات في لمحة'), T('how widespread each gap is across the region', 'مدى انتشار كل فجوة في الإقليم'));
    eyebrow(sl, T('Key insights', 'أبرز الملاحظات'), 0.5, 1.45, 6.6, C.SKY_DK);
    const top3 = ranked.slice(0, 3).map(c => cn(c.name));
    const u5bad = list.filter(c => (curLvl(c, 'SH.DYN.MORT') ?? 3) <= 1).length;
    const incomeLine = inc.LIC ? T(`${inc.LIC} of ${list.length} countries are low-income; ${inc.LMIC} are lower-middle income.`, `${inc.LIC} من ${list.length} دول منخفضة الدخل، و${inc.LMIC} من الشريحة الدنيا من الدخل المتوسط.`)
      : T(`None of the ${list.length} countries is low-income; ${inc.LMIC} are lower-middle and ${inc.UMIC} upper-middle income.`, `لا توجد دولة منخفضة الدخل بين الدول الـ${list.length}؛ ${inc.LMIC} من الشريحة الدنيا و${inc.UMIC} من الشريحة العليا من الدخل المتوسط.`);
    bullets(sl, [
      top3.length ? T(`Highest need on the ODA index: ${top3.join(', ')}.`, `الأعلى احتياجاً على مؤشر المكتب: ${top3.join('، ')}.`) : T('Not enough data to rank countries by need.', 'البيانات غير كافية لترتيب الدول حسب الاحتياج.'),
      T(`${u5bad} of ${list.length} countries have under-5 mortality above 40 per 1,000 live births (SDG target: 25).`, `${u5bad} من ${list.length} دول تتجاوز فيها وفيات الأطفال دون الخامسة 40 لكل 1,000 مولود حي (الهدف: 25).`),
      meds['SH.DYN.MORT'] != null ? T(`Regional median under-5 mortality is ${Math.round(meds['SH.DYN.MORT'])} per 1,000; median GDP per capita (PPP) is ${medGdp != null ? F.money({ v:medGdp }) : 'not available'}.`,
        `يبلغ الوسيط الإقليمي لوفيات الأطفال دون الخامسة ${Math.round(meds['SH.DYN.MORT'])} لكل 1,000، ووسيط نصيب الفرد من الناتج ${medGdp != null ? F.money({ v:medGdp }) : 'غير متاح'}.`) : null,
      incomeLine,
    ].filter(Boolean), 0.5, 1.8, 6.6);
    const RX = 7.6, RW = 5.23;
    eyebrow(sl, T('Countries rated severe or high concern', 'الدول المصنّفة حرجة أو مقلقة'), RX, 1.45, RW, C.SKY_DK);
    IND.forEach((ind, i) => {
      const have = list.filter(c => curLvl(c, ind.id) != null), bad = have.filter(c => curLvl(c, ind.id) <= 1).length;
      const ry = 1.85 + i * 0.78;
      sl.text(lbl(ind), { x:RX, y:ry, w:RW - 1.2, h:0.26, fontFace:BODY, fontSize:9.4, bold:true, color:C.INK });
      sl.text(T(`${bad} of ${have.length}`, `${bad} من ${have.length}`), { x:RX + RW - 1.2, y:ry, w:1.2, h:0.26, fontFace:BODY, fontSize:9.4, bold:true, color:C.INK, align:'right' });
      sl.shape(p.ShapeType.rect, { x:RX, y:ry + 0.32, w:RW, h:0.24, fill:{ color:C.SKY_PALE }, line:{ type:'none' } });
      if (have.length && bad) sl.shape(p.ShapeType.rect, { x:RX, y:ry + 0.32, w:Math.max(0.05, RW * bad / have.length), h:0.24, fill:{ color:SEV.fill[0] }, line:{ type:'none' } });
    });
    foot(sl, SRC_LINE + ' · ' + DATE);
  });

  // ══ NEED RANKING ══
  const PER_RANK = 18;
  for (let s = 0; s < Math.max(1, Math.ceil(ranked.length / PER_RANK)); s++) {
    const part = ranked.slice(s * PER_RANK, (s + 1) * PER_RANK), pages = Math.ceil(ranked.length / PER_RANK);
    S.push(() => {
      const sl = newSlide(C.WHITE);
      head(sl, REGION + T(' · need ranking', ' · ترتيب الاحتياج') + (pages > 1 ? ` (${s + 1}/${pages})` : ''), T('Where Needs Are Greatest', 'أين يكون الاحتياج أكبر'), T('ODA need index, 0 (lowest) – 100 (highest)', 'مؤشر الاحتياج، من 0 (الأدنى) إلى 100 (الأعلى)'));
      const top = 1.45, rowH = Math.min(0.42, 5.3 / Math.max(part.length, 1)), NW = 3.0, BX = 0.5 + 0.45 + NW + 0.3, BW = 7.6;
      part.forEach((c, i) => { const y = top + i * rowH, rank = s * PER_RANK + i + 1, hi = c.tier === 'hi';
        sl.text(String(rank), { x:0.5, y, w:0.4, h:rowH, fontFace:BODY, fontSize:9.5, bold:true, color:C.FAINT, valign:'middle' });
        sl.text(cn(c.name), { x:0.95, y, w:NW, h:rowH, fontFace:BODY, fontSize:10.5, bold:true, color:C.INK, valign:'middle', fit:'shrink' });
        sl.shape(p.ShapeType.rect, { x:BX, y:y + rowH * 0.22, w:BW, h:rowH * 0.56, fill:{ color:C.SKY_PALE }, line:{ type:'none' } });
        sl.shape(p.ShapeType.rect, { x:BX, y:y + rowH * 0.22, w:Math.max(0.05, BW * c.need / 100), h:rowH * 0.56, fill:{ color: hi ? C.GOLD : C.SKY }, line:{ type:'none' } });
        sl.text(String(Math.round(c.need)), { x:BX + BW + 0.1, y, w:0.6, h:rowH, fontFace:HEAD, fontSize:12, bold:true, color:C.INK, valign:'middle' }); });
      sl.text(T('Gold = among the highest-need third of all countries ODA tracks.', 'الذهبي = ضمن الثلث الأعلى احتياجاً بين جميع الدول التي يتابعها المكتب.'), { x:0.5, y:6.78, w:12.3, h:0.24, fontFace:BODY, fontSize:8, color:C.FAINT });
      foot(sl, T('ODA need index — see Method · ', 'مؤشر الاحتياج — انظر المنهجية · ') + DATE);
    });
  }

  // ══ COMPARISON TABLE ══
  const PER_TBL = 13;
  for (let s = 0; s < Math.ceil(byNeed.length / PER_TBL); s++) {
    const part = byNeed.slice(s * PER_TBL, (s + 1) * PER_TBL), pages = Math.ceil(byNeed.length / PER_TBL);
    S.push(() => {
      const sl = newSlide(C.WHITE);
      head(sl, REGION + T(' · country comparison', ' · مقارنة الدول') + (pages > 1 ? ` (${s + 1}/${pages})` : ''), T('Side by Side', 'جنباً إلى جنب'), T('colour shows severity against SDG / WHO benchmarks', 'يعكس اللون مستوى الحدّة مقارنةً بمعايير أهداف التنمية المستدامة ومنظمة الصحة'));
      const hdr = [T('Country', 'الدولة'), T('Population', 'السكان'), T('GDP/cap PPP', 'نصيب الفرد'), ...IND.map(lbl), T('Need', 'الاحتياج')]
        .map(t => ({ text:t, options:{ bold:true, color:C.WHITE, fill:{ color:C.NAVY }, fontSize:8, align:'center', valign:'middle' } }));
      const rows = [hdr];
      part.forEach(c => {
        const r = [{ text:cn(c.name), options:{ bold:true, color:C.INK, align:'left' } }, { text:F.pop(c.R('SP.POP.TOTL')) }, { text:F.money(c.R('NY.GDP.PCAP.PP.CD')) }];
        IND.forEach(ind => { const rr = c.R(ind.id), L = rr ? DK.sevLvl(ind.id, rr.v) : null;
          r.push({ text: rr ? ind.f(rr) + (rr.stale ? '*' : '') : '—', options:{ fill:{ color: L == null ? C.WHITE : SEV.tint[L] }, color: L == null ? C.FAINT : SEV.text[L], bold: L != null && L <= 1 } }); });
        r.push({ text: c.need == null ? '—' : String(Math.round(c.need)), options:{ bold:true, color: c.tier === 'hi' ? C.GOLD : C.INK } });
        rows.push(r);
      });
      sl.table(rows, { x:0.5, y:1.38, w:12.33, colW:[1.95, 0.98, 1.08, 1.27, 1.27, 1.27, 1.27, 1.27, 1.27, 0.75], fontFace:BODY, fontSize:8.6, color:C.INK, align:'center', valign:'middle', rowH:0.37, border:{ type:'solid', color:C.LINE, pt:0.5 } });
      sl.text(T('Under-5 mortality per 1,000 live births · maternal mortality per 100,000 · access indicators are % of population · * figure older than ' + DK.STALE_YEARS + ' years.',
                'وفيات الأطفال لكل 1,000 مولود حي · وفيات الأمهات لكل 100,000 · مؤشرات الوصول نسبة من السكان · * رقم أقدم من ' + DK.STALE_YEARS + ' سنوات.'), { x:0.5, y:6.78, w:12.3, h:0.24, fontFace:BODY, fontSize:7.6, color:C.FAINT });
      foot(sl, SRC_LINE + ' · ' + DATE);
    });
  }

  // ══ COUNTRY PROFILES ══
  byNeed.forEach(c => S.push(() => {
    const sl = newSlide(C.WHITE);
    eyebrow(sl, REGION + T(' · country profile', ' · ملف الدولة'), 0.5, 0.34, 8);
    let tx = 0.5;
    if (c.flagData) { try { const f = DK.contain(c.flagRatio, 0.5, 0.66, 0.66, 0.46); sl.image({ data:c.flagData, x:f.x, y:f.y, w:f.w, h:f.h }); tx = 1.32; } catch (e) {} }
    sl.text(cn(c.name), { x:tx, y:0.6, w:7.5, h:0.55, fontFace:HEAD, fontSize:24, bold:true, color:C.INK, valign:'middle', fit:'shrink' });
    sl.text([incN(c.income), gv(c, 'SP.POP.TOTL') != null ? T('Population ', 'عدد السكان ') + F.pop(c.R('SP.POP.TOTL')) : null, gv(c, 'NY.GDP.PCAP.PP.CD') != null ? T('GDP/cap ', 'نصيب الفرد ') + F.money(c.R('NY.GDP.PCAP.PP.CD')) : null].filter(Boolean).join(' · '),
      { x:tx, y:1.14, w:8.5, h:0.28, fontFace:BODY, fontSize:10, color:C.MUTE });
    // need badge
    const hi = c.tier === 'hi';
    sl.shape(p.ShapeType.rect, { x:10.33, y:0.5, w:2.5, h:0.92, fill:{ color: hi ? C.GOLD_PALE : C.SKY_PALE }, line:{ type:'none' } });
    sl.text(T('NEED INDEX', 'مؤشر الاحتياج'), { x:10.45, y:0.56, w:2.3, h:0.2, fontFace:BODY, fontSize:7.5, bold:true, color:C.MUTE, charSpacing:1.4 });
    sl.text(c.need == null ? '—' : String(Math.round(c.need)), { x:10.45, y:0.76, w:1.0, h:0.58, fontFace:HEAD, fontSize:26, bold:true, color: hi ? C.GOLD : C.INK, valign:'middle' });
    sl.text(c.needRank ? T(`rank ${c.needRank} of ${ranked.length} in region`, `الترتيب ${c.needRank} من ${ranked.length} في الإقليم`) : T('not ranked', 'غير مصنّفة'), { x:11.3, y:0.8, w:1.5, h:0.5, fontFace:BODY, fontSize:8.6, color:C.MUTE, valign:'middle', fit:'shrink' });
    // left: stat cards 3×2
    const cw = 2.25, ch = 1.15, X0 = 0.5, Y0 = 1.65;
    IND.forEach((ind, i) => { const r = c.R(ind.id), L = r ? DK.sevLvl(ind.id, r.v) : null;
      card(sl, X0 + (i % 3) * (cw + 0.16), Y0 + Math.floor(i / 3) * (ch + 0.16), cw, ch, fv(ind, r), lbl(ind),
        r ? (r.stale ? T(`${r.y} · outdated`, `${r.y} · قديمة`) : (L != null ? DK.sevLabelOf(L, ar) + ' · ' + r.y : String(r.y || ''))) : T('No recent data', 'لا توجد بيانات حديثة'), L); });
    // left bottom: bars vs regional median
    const BY = Y0 + 2 * (ch + 0.16) + 0.15, BW = 3 * cw + 0.32;
    eyebrow(sl, T('Compared with the regional median', 'مقارنةً بالوسيط الإقليمي'), X0, BY, BW, C.SKY_DK);
    IND.forEach((ind, i) => {
      const r = c.R(ind.id), m = meds[ind.id], ry = BY + 0.32 + i * 0.36;
      const max = rule(ind.id).dir < 0 ? 100 : Math.max(r ? r.v : 0, m || 0, tgt(ind.id)) * 1.2;
      sl.text(lbl(ind), { x:X0, y:ry, w:2.2, h:0.28, fontFace:BODY, fontSize:8.2, color:C.INK, valign:'middle', fit:'shrink' });
      const bx = X0 + 2.3, bw = BW - 3.1;
      sl.shape(p.ShapeType.rect, { x:bx, y:ry + 0.07, w:bw, h:0.14, fill:{ color:C.SKY_PALE }, line:{ type:'none' } });
      if (r) { const L = DK.sevLvl(ind.id, r.v); sl.shape(p.ShapeType.rect, { x:bx, y:ry + 0.07, w:Math.max(0.04, bw * Math.min(1, r.v / max)), h:0.14, fill:{ color: L == null ? C.SKY : SEV.fill[L] }, line:{ type:'none' } }); }
      if (m != null) sl.shape(p.ShapeType.rect, { x:bx + bw * Math.min(1, m / max) - 0.012, y:ry + 0.02, w:0.024, h:0.24, fill:{ color:C.NAVY }, line:{ type:'none' } });
      sl.text(r ? ind.f(r) : '—', { x:bx + bw + 0.08, y:ry, w:0.7, h:0.28, fontFace:BODY, fontSize:8.2, bold:true, color:C.INK, valign:'middle' });
    });
    sl.text(T('Bar = country (coloured by severity) · dark tick = regional median', 'الشريط = الدولة (ملوّن حسب الحدّة) · العلامة الداكنة = الوسيط الإقليمي'), { x:X0, y:BY + 0.32 + IND.length * 0.36, w:BW, h:0.2, fontFace:BODY, fontSize:7.2, color:C.FAINT });
    // right: narrative vs region + priority sectors
    const RX = 7.85, RW = 4.98;
    const gaps = IND.map(ind => { const r = c.R(ind.id), m = meds[ind.id]; if (!r || r.stale || m == null) return null;
      const dir = rule(ind.id).dir, worse = dir > 0 ? r.v / Math.max(m, 0.1) : (100 - r.v) / Math.max(1, 100 - m); return { ind, r, m, worse }; }).filter(Boolean).sort((a, b) => b.worse - a.worse);
    eyebrow(sl, T('How it compares', 'موقعها مقارنةً بالإقليم'), RX, 1.65, RW, C.SKY_DK);
    const lines = gaps.slice(0, 3).map(g => { const state = g.worse > 1.05 ? T('worse than', 'أسوأ من') : g.worse < 0.95 ? T('better than', 'أفضل من') : T('close to', 'قريب من');
      return T(`${lbl(g.ind)}: ${fv(g.ind, g.r)} — ${state} the regional median (${fv(g.ind, { v:g.m })}).`, `${lbl(g.ind)}: ${fv(g.ind, g.r)} — ${state} الوسيط الإقليمي (${fv(g.ind, { v:g.m })}).`); });
    const endY = bullets(sl, lines.length ? lines : [T('Not enough current data to compare with the region.', 'لا تتوفر بيانات حديثة كافية للمقارنة بالإقليم.')], RX, 1.98, RW);
    const sectors = []; IND.forEach(ind => { const L = curLvl(c, ind.id); if (L != null && L <= 1) { const nm = T(ind.sector[0], ind.sector[1]); if (!sectors.includes(nm)) sectors.push(nm); } });
    const PY = Math.max(endY + 0.2, 4.6);
    sl.shape(p.ShapeType.rect, { x:RX, y:PY, w:RW, h:1.9, fill:{ color:C.GOLD_PALE }, line:{ type:'none' } });
    sl.shape(p.ShapeType.rect, { x:RX, y:PY, w:0.06, h:1.9, fill:{ color:C.GOLD }, line:{ type:'none' } });
    eyebrow(sl, T('Priority sectors from the data', 'القطاعات ذات الأولوية وفق البيانات'), RX + 0.22, PY + 0.14, RW - 0.4);
    sl.text(sectors.length ? sectors.slice(0, 3).join('  ·  ') : T('No sector is rated severe or high concern', 'لا يوجد قطاع مصنّف حرجاً أو مقلقاً'), { x:RX + 0.22, y:PY + 0.48, w:RW - 0.4, h:0.7, fontFace:HEAD, fontSize: sectors.length ? 17 : 12, bold: !!sectors.length, color:C.INK, valign:'middle', fit:'shrink' });
    sl.text(T('Based on national indicators rated severe or high concern; confirm with a full country assessment.', 'استناداً إلى المؤشرات الوطنية المصنّفة حرجة أو مقلقة؛ يُستحسن التأكيد بتقييم كامل للدولة.'), { x:RX + 0.22, y:PY + 1.25, w:RW - 0.4, h:0.5, fontFace:BODY, fontSize:8, color:C.MUTE, valign:'top', wrap:true });
    foot(sl, SRC_LINE + ' · ' + DATE);
  }));

  // ══ METHOD & SOURCES ══
  S.push(() => {
    const sl = newSlide(C.NAVY);
    sl.text(T('METHOD & SOURCES', 'المنهجية والمصادر'), { x:0.6, y:0.6, w:9, h:0.3, fontFace:BODY, fontSize:10, bold:true, color:C.GOLD_LT, charSpacing:2.6 });
    sl.text(REGION, { x:0.57, y:0.95, w:12, h:0.9, fontFace:HEAD, fontSize:34, bold:true, color:C.WHITE, fit:'shrink' });
    sl.shape(p.ShapeType.rect, { x:0.6, y:1.95, w:0.9, h:0.035, fill:{ color:C.GOLD }, line:{ type:'none' } });
    [[T('ODA need index', 'مؤشر الاحتياج'), T('Combines under-5 and maternal mortality, undernourishment and lack of basic drinking water, sanitation and electricity. Each is scaled 0–100 across all countries the dashboard tracks and averaged; a country needs four of the six to be ranked.',
       'يجمع بين وفيات الأطفال دون الخامسة ووفيات الأمهات ونقص التغذية ونقص مياه الشرب الأساسية والصرف الصحي والكهرباء. يُقاس كل منها من 0 إلى 100 عبر جميع الدول المتابَعة ثم يُحسب المتوسط؛ ويلزم توفر أربعة من ستة مؤشرات للترتيب.')],
     [T('Severity colours', 'ألوان الحدّة'), T('Severe · High concern · Moderate · On track, against SDG / WHO reference points — the same scale as the dashboard. "People without" figures multiply national access rates by population and are estimates.',
       'حرج · مقلق · متوسط · على المسار، وفق مرجعيات أهداف التنمية المستدامة ومنظمة الصحة — وهو مقياس اللوحة نفسه. أعداد السكان المحرومين تقديرية بضرب معدلات الوصول الوطنية في عدد السكان.')],
     [T('Data', 'البيانات'), SRC_LINE + '. ' + (opts.dataNote || '') + T(` Figures older than ${DK.STALE_YEARS} years are marked and excluded from ratings; missing values show as "—".`, ` تُميَّز الأرقام الأقدم من ${DK.STALE_YEARS} سنوات وتُستبعد من التصنيف، وتظهر القيم المفقودة بعلامة «—».`)]]
      .forEach(([h, t], i) => { const y = 2.3 + i * 1.45;
        sl.text(ar ? h : h.toUpperCase(), { x:0.6, y, w:12, h:0.26, fontFace:BODY, fontSize:9.5, bold:true, color:C.GOLD_LT, charSpacing:1.6 });
        sl.text(t, { x:0.6, y:y + 0.32, w:12, h:1.05, fontFace:BODY, fontSize:10.5, color:'E6EEF5', valign:'top', wrap:true }); });
    foot(sl, T('ODA Country Assessment Dashboard · ', 'لوحة تقييم الدول · ') + DATE, true);
  });

  TOTAL = S.length;
  S.forEach(fn => fn());
  if (opts.output === 'blob') return p.write({ outputType:'blob' });
  return p.writeFile({ fileName: opts.fileName || `${regionKey.replace(/[^\w]+/g, '_')}_Regional_Assessment.pptx` });
}

if (typeof window !== 'undefined') window.buildRegionDeck = buildRegionDeck;
if (typeof module !== 'undefined' && module.exports) module.exports = { buildRegionDeck };
