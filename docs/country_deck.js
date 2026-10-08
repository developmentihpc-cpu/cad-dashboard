/* country_deck.js — ODA instant country assessment deck (English or Arabic).
 *
 * 10 slides: cover · country overview (map, key facts, status by sector) · executive summary · six sector slides (health, education,
 * food security & agriculture, WASH, energy & connectivity, economy) · method & sources.
 *
 * Every rating uses the shared severity scale (severity.js) — the same one the
 * dashboard shows. Narrative sentences are generated from each value's severity,
 * so the wording can never contradict the data; missing, impossible (0) and
 * outdated values are kept out of the narrative and flagged on the slide.
 *
 * opts: country, data {id:{value,year}}, info {capital,currency,languages}, iso2,
 *       flagData, mapData (dataURLs), dateStr, PptxGenJS, lang 'en'|'ar',
 *       region, income ('LIC'|'LMIC'|'UMIC'), need {score,rank,of} | null,
 *       output 'blob' | (download) fileName
 * Requires deck_kit.js + severity.js (+ i18n_ar.js for Arabic names).
 */
'use strict';

function buildCountryDeck(opts){
  const ar = opts.lang === 'ar';
  const T = (en, a) => ar ? a : en;
  const { C, SEV } = DK;
  const Pptx = opts.PptxGenJS || (typeof PptxGenJS !== 'undefined' ? PptxGenJS : null);
  if (!Pptx) throw new Error('PptxGenJS constructor not provided');
  const country = opts.country;
  const NAME = ar && typeof AR_COUNTRY !== 'undefined' ? (AR_COUNTRY[country] || country) : country;
  const REGION = ar && typeof AR_REGION !== 'undefined' ? (AR_REGION[opts.region] || opts.region || '') : (opts.region || '');
  const INCOME = opts.income ? (ar ? (typeof AR_INCOME !== 'undefined' ? AR_INCOME[opts.income] : '')
    : ({ LIC:'Low income', LMIC:'Lower-middle income', UMIC:'Upper-middle income' }[opts.income] || '')) : '';
  const DATE = opts.dateStr || new Date().toLocaleDateString('en-US', { month:'long', year:'numeric' });
  const R = DK.reader(opts.data || {});
  const F = DK.fmt(ar);
  const HEAD = 'Lora', BODY = 'Montserrat';
  const SRC = { 'SP.POP.TOTL':'World Bank', 'NY.GDP.PCAP.PP.CD':'World Bank · IMF', 'NY.GDP.MKTP.KD.ZG':'World Bank', 'FP.CPI.TOTL.ZG':'World Bank · IMF',
    'GC.TAX.TOTL.GD.ZS':'IMF · World Bank', 'GC.DOD.TOTL.GD.ZS':'IMF', 'SL.UEM.TOTL.ZS':'ILO', 'SI.POV.DDAY':'World Bank',
    'SH.DYN.MORT':'UN IGME (UNICEF/WHO)', 'SH.STA.MMRT':'WHO · UNICEF · UNFPA', 'SP.DYN.LE00.IN':'World Bank', 'SH.XPD.CHEX.GD.ZS':'WHO GHED',
    'SH.MED.PHYS.ZS':'WHO', 'SH.IMM.MEAS':'WHO · UNICEF', 'SH.STA.STNT.ZS':'UNICEF · WHO · World Bank', 'SN.ITK.DEFC.ZS':'FAO',
    'SE.ADT.LITR.ZS':'UNESCO UIS', 'SE.PRM.CMPT.ZS':'UNESCO UIS', 'SE.SEC.ENRR':'UNESCO UIS', 'SE.XPD.TOTL.GD.ZS':'UNESCO · World Bank', 'SE.PRM.PTRT.ZS':'UNESCO UIS',
    'AG.YLD.CREL.KG':'FAO', 'NV.AGR.TOTL.ZS':'World Bank', 'SH.H2O.BASW.ZS':'WHO/UNICEF JMP', 'SH.H2O.SMDW.ZS':'WHO/UNICEF JMP', 'SH.STA.BASS.ZS':'WHO/UNICEF JMP',
    'SH.STA.SMSS.ZS':'WHO/UNICEF JMP', 'SH.STA.ODFC.ZS':'WHO/UNICEF JMP', 'EG.ELC.ACCS.ZS':'World Bank · IEA', 'EG.CFT.ACCS.ZS':'WHO', 'IT.NET.USER.ZS':'ITU',
    'EG.FEC.RNEW.ZS':'IEA · World Bank' };
  const srcTxt = s => ar && typeof arSource === 'function' ? arSource(s) : s;

  // ── indicator catalogue (labels both languages, how to format) ──
  const I = {
    'SH.DYN.MORT':       { en:'Under-5 mortality', ar:'وفيات الأطفال دون الخامسة', f: r => F.num(r), u:[' per 1,000 births',' لكل 1,000 مولود'] },
    'SH.STA.MMRT':       { en:'Maternal mortality', ar:'وفيات الأمهات', f: r => F.num(r), u:[' per 100,000 births',' لكل 100,000 ولادة'] },
    'SP.DYN.LE00.IN':    { en:'Life expectancy', ar:'متوسط العمر المتوقع', f: r => F.num(r, 1), u:[' years',' سنة'] },
    'SH.XPD.CHEX.GD.ZS': { en:'Health spending (% of GDP)', ar:'الإنفاق الصحي (% من الناتج)', f: r => F.pct(r, 1) },
    'SH.MED.PHYS.ZS':    { en:'Doctors per 1,000 people', ar:'الأطباء لكل 1,000 نسمة', f: r => F.num(r, 2) },
    'SH.IMM.MEAS':       { en:'Measles immunisation', ar:'التحصين ضد الحصبة', f: r => F.pct(r) },
    'SE.ADT.LITR.ZS':    { en:'Adult literacy', ar:'معرفة الكبار بالقراءة والكتابة', f: r => F.pct(r) },
    'SE.PRM.CMPT.ZS':    { en:'Primary completion', ar:'إتمام المرحلة الابتدائية', f: r => F.pct(r) },
    'SE.SEC.ENRR':       { en:'Secondary enrolment (gross)', ar:'الالتحاق بالتعليم الثانوي (إجمالي)', f: r => F.pct(r) },
    'SE.XPD.TOTL.GD.ZS': { en:'Education spending (% of GDP)', ar:'الإنفاق على التعليم (% من الناتج)', f: r => F.pct(r, 1) },
    'SE.PRM.PTRT.ZS':    { en:'Pupils per teacher (primary)', ar:'التلاميذ لكل معلم (ابتدائي)', f: r => F.num(r) },
    'SN.ITK.DEFC.ZS':    { en:'Undernourishment', ar:'نقص التغذية', f: r => F.pct(r, 1) },
    'SH.STA.STNT.ZS':    { en:'Child stunting', ar:'تقزّم الأطفال', f: r => F.pct(r, 1) },
    'AG.YLD.CREL.KG':    { en:'Cereal yield', ar:'إنتاجية الحبوب', f: r => F.num(r), u:[' kg/ha',' كغ/هكتار'] },
    'NV.AGR.TOTL.ZS':    { en:'Agriculture (% of GDP)', ar:'الزراعة (% من الناتج)', f: r => F.pct(r) },
    'SH.H2O.BASW.ZS':    { en:'Basic drinking water', ar:'مياه الشرب الأساسية', f: r => F.pct(r) },
    'SH.H2O.SMDW.ZS':    { en:'Safely managed water', ar:'المياه المُدارة بأمان', f: r => F.pct(r) },
    'SH.STA.BASS.ZS':    { en:'Basic sanitation', ar:'الصرف الصحي الأساسي', f: r => F.pct(r) },
    'SH.STA.SMSS.ZS':    { en:'Safely managed sanitation', ar:'الصرف الصحي المُدار بأمان', f: r => F.pct(r) },
    'SH.STA.ODFC.ZS':    { en:'Open defecation', ar:'التغوط في العراء', f: r => F.pct(r) },
    'EG.ELC.ACCS.ZS':    { en:'Electricity access', ar:'الوصول إلى الكهرباء', f: r => F.pct(r) },
    'EG.CFT.ACCS.ZS':    { en:'Clean cooking access', ar:'الوصول إلى طهي نظيف', f: r => F.pct(r) },
    'IT.NET.USER.ZS':    { en:'Internet users', ar:'مستخدمو الإنترنت', f: r => F.pct(r) },
    'EG.FEC.RNEW.ZS':    { en:'Renewables (% of energy)', ar:'الطاقة المتجددة (% من الاستهلاك)', f: r => F.pct(r) },
    'NY.GDP.MKTP.KD.ZG': { en:'GDP growth', ar:'نمو الناتج المحلي', f: r => F.pct(r, 1) },
    'FP.CPI.TOTL.ZG':    { en:'Inflation', ar:'التضخم', f: r => F.pct(r, 1) },
    'GC.TAX.TOTL.GD.ZS': { en:'Tax revenue (% of GDP)', ar:'الإيرادات الضريبية (% من الناتج)', f: r => F.pct(r, 1) },
    'NY.GDP.PCAP.PP.CD': { en:'GDP per capita (PPP)', ar:'نصيب الفرد من الناتج (تعادل القوة الشرائية)', f: r => F.money(r) },
    'SL.UEM.TOTL.ZS':    { en:'Unemployment', ar:'البطالة', f: r => F.pct(r, 1) },
    'SI.POV.DDAY':       { en:'Extreme poverty (<$2.15/day)', ar:'الفقر المدقع (أقل من 2.15 دولار يومياً)', f: r => F.pct(r, 1) },
    'GC.DOD.TOTL.GD.ZS': { en:'Government debt (% of GDP)', ar:'الدين الحكومي (% من الناتج)', f: r => F.pct(r) },
    'SP.POP.TOTL':       { en:'Population', ar:'عدد السكان', f: r => F.pop(r) },
  };
  const lbl = id => T(I[id].en, I[id].ar);
  const val = id => { const r = R(id); return r ? I[id].f(r) + (I[id].u ? I[id].u[ar ? 1 : 0] : '') : '—'; };
  const valShort = id => { const r = R(id); return r ? I[id].f(r) : '—'; };
  const rule = id => (typeof SEV_RULES !== 'undefined' ? SEV_RULES[id] : null);
  const target = id => { const r = rule(id); return r && !r.peers ? r.th[2] : null; };          // "on track" threshold
  const fmtTarget = id => { const t = target(id); if (t == null) return ''; const r = { v:t };
    return I[id].f(r) + (I[id].u ? I[id].u[ar ? 1 : 0] : ''); };
  // level for narrative: only current (non-stale) values with a benchmark
  const lvl = id => { const r = R(id); return r && !r.stale ? DK.sevLvl(id, r.v) : null; };
  const lvlAny = id => { const r = R(id); return r ? DK.sevLvl(id, r.v) : null; };
  const cite = id => { const r = R(id); const s = srcTxt(SRC[id] || 'World Bank');
    return r ? (r.stale ? s + ' · ' + r.y + T(' · outdated', ' · بيانات قديمة') : s + (r.y ? ' · ' + r.y : '')) : T('No recent data', 'لا توجد بيانات حديثة'); };

  // ── narrative generator: one sentence per indicator, wording follows severity ──
  function sentence(id) {
    const r = R(id); const L = lvl(id); if (!r || L == null) return null;
    const rl = rule(id), tgt = fmtTarget(id), v = val(id), name = lbl(id);
    const ratio = rl.dir > 0 ? r.v / target(id) : null;
    if (rl.dir > 0) {     // higher is worse
      if (L === 0) return T(`${name} is ${v} — ${ratio >= 1.8 ? ratio.toFixed(1) + '× ' : 'far above '}the benchmark of ${tgt}; this is a severe gap.`,
                            `${name} ${v} — ${ratio >= 1.8 ? 'أي ' + ratio.toFixed(1) + ' أضعاف' : 'أعلى بكثير من'} المعيار البالغ ${tgt}؛ وهي فجوة حرجة.`);
      if (L === 1) return T(`${name} at ${v} is well above the benchmark of ${tgt}.`, `${name} عند ${v}، وهو أعلى بوضوح من المعيار البالغ ${tgt}.`);
      if (L === 2) return T(`${name} at ${v} is close to, but still above, the benchmark of ${tgt}.`, `${name} عند ${v}، قريب من المعيار البالغ ${tgt} لكنه لا يزال أعلى منه.`);
      return T(`${name} at ${v} meets the benchmark (${tgt}).`, `${name} عند ${v} ويحقق المعيار (${tgt}).`);
    }
    if (L === 0) return T(`${name} is only ${v}, far below the benchmark of ${tgt}; this is a severe gap.`, `${name} لا يتجاوز ${v}، أي أدنى بكثير من المعيار البالغ ${tgt}؛ وهي فجوة حرجة.`);
    if (L === 1) return T(`${name} at ${v} is well below the benchmark of ${tgt}.`, `${name} عند ${v}، وهو أدنى بوضوح من المعيار البالغ ${tgt}.`);
    if (L === 2) return T(`${name} at ${v} is approaching the benchmark of ${tgt}.`, `${name} عند ${v} ويقترب من المعيار البالغ ${tgt}.`);
    return T(`${name} at ${v} meets the benchmark (${tgt}).`, `${name} عند ${v} ويحقق المعيار (${tgt}).`);
  }
  const staleNote = id => { const r = R(id); return r && r.stale ? T(`${lbl(id)}: the latest figure is from ${r.y}, so it is shown but not used in this assessment.`,
    `${lbl(id)}: أحدث رقم متاح يعود إلى عام ${r.y}، لذا يُعرض دون الاعتماد عليه في هذا التقييم.`) : null; };

  // ── sectors ──
  const SECTORS = [
    { key:'health', en:'Health', ar:'الصحة', short:['Health','الصحة'], stats:['SH.DYN.MORT','SH.STA.MMRT','SP.DYN.LE00.IN','SH.XPD.CHEX.GD.ZS'], bars:['SH.DYN.MORT','SH.STA.MMRT','SP.DYN.LE00.IN','SH.IMM.MEAS','SH.XPD.CHEX.GD.ZS'],
      acts:[ ['SH.DYN.MORT',1,'Scale up community health workers and integrated child-health services.','توسيع نطاق العاملين الصحيين المجتمعيين وخدمات صحة الطفل المتكاملة.'],
             ['SH.STA.MMRT',1,'Expand skilled birth attendance and emergency obstetric care.','توسيع الولادة بإشراف كوادر مؤهلة ورعاية التوليد الطارئة.'],
             ['SH.IMM.MEAS',2,'Close immunisation gaps through outreach and cold-chain investment.','سد فجوات التحصين عبر الوصول الميداني والاستثمار في سلسلة التبريد.'],
             ['SH.XPD.CHEX.GD.ZS',2,'Support higher, more predictable public health financing.','دعم تمويل صحي عام أعلى وأكثر استقراراً.'],
             [null,3,'Strengthen primary-care quality and reach in underserved areas.','تعزيز جودة الرعاية الأولية ووصولها إلى المناطق المحرومة.'] ] },
    { key:'education', en:'Education', ar:'التعليم', short:['Education','التعليم'], stats:['SE.ADT.LITR.ZS','SE.PRM.CMPT.ZS','SE.SEC.ENRR','SE.XPD.TOTL.GD.ZS'], bars:['SE.ADT.LITR.ZS','SE.PRM.CMPT.ZS','SE.SEC.ENRR','SE.PRM.PTRT.ZS','SE.XPD.TOTL.GD.ZS'],
      acts:[ ['SE.PRM.CMPT.ZS',1,'Keep children in primary school to completion (school feeding, fee support).','إبقاء الأطفال في المدرسة حتى إتمام المرحلة الابتدائية (التغذية المدرسية ودعم الرسوم).'],
             ['SE.SEC.ENRR',1,'Expand secondary places and support girls’ transition to secondary school.','زيادة مقاعد التعليم الثانوي ودعم انتقال الفتيات إليه.'],
             ['SE.ADT.LITR.ZS',1,'Fund adult and youth literacy programmes.','تمويل برامج محو الأمية للشباب والكبار.'],
             ['SE.PRM.PTRT.ZS',1,'Recruit and train teachers to bring class sizes down.','توظيف المعلمين وتدريبهم لخفض أعداد الطلاب في الفصول.'],
             [null,3,'Invest in teacher quality and learning assessment.','الاستثمار في جودة المعلمين وتقييم التعلّم.'] ] },
    { key:'food', en:'Food Security & Agriculture', ar:'الأمن الغذائي والزراعة', short:['Food & agriculture','الغذاء والزراعة'], stats:['SN.ITK.DEFC.ZS','SH.STA.STNT.ZS','AG.YLD.CREL.KG','NV.AGR.TOTL.ZS'], bars:['SN.ITK.DEFC.ZS','SH.STA.STNT.ZS','AG.YLD.CREL.KG'],
      acts:[ ['SN.ITK.DEFC.ZS',1,'Scale food assistance and social safety nets for vulnerable households.','توسيع المساعدات الغذائية وشبكات الأمان الاجتماعي للأسر الهشة.'],
             ['SH.STA.STNT.ZS',1,'Fund early-childhood and maternal nutrition programmes.','تمويل برامج تغذية الأمهات والطفولة المبكرة.'],
             ['AG.YLD.CREL.KG',1,'Raise smallholder yields: irrigation, improved seed, extension services.','رفع إنتاجية صغار المزارعين: الري والبذور المحسّنة والإرشاد الزراعي.'],
             [null,3,'Build climate resilience into food systems and storage.','تعزيز قدرة النظم الغذائية والتخزين على الصمود أمام المناخ.'] ] },
    { key:'wash', en:'Water, Sanitation & Hygiene', ar:'المياه والصرف الصحي والنظافة', short:['Water & sanitation','المياه والصرف'], stats:['SH.H2O.BASW.ZS','SH.H2O.SMDW.ZS','SH.STA.BASS.ZS','SH.STA.SMSS.ZS'], bars:['SH.H2O.BASW.ZS','SH.H2O.SMDW.ZS','SH.STA.BASS.ZS','SH.STA.ODFC.ZS'],
      acts:[ ['SH.H2O.BASW.ZS',1,'Extend basic water points and piped supply to unserved communities.','توصيل مياه الشرب الأساسية والشبكات إلى المجتمعات غير المخدومة.'],
             ['SH.STA.BASS.ZS',1,'Fund household and school sanitation; end open defecation.','تمويل الصرف الصحي للمنازل والمدارس وإنهاء التغوط في العراء.'],
             ['SH.H2O.SMDW.ZS',2,'Upgrade water treatment so supply is safely managed.','تحسين معالجة المياه لتصبح مُدارة بأمان.'],
             [null,3,'Climate-proof water sources and utilities.','حماية مصادر المياه ومرافقها من آثار المناخ.'] ] },
    { key:'energy', en:'Energy & Connectivity', ar:'الطاقة والاتصال', short:['Energy & connectivity','الطاقة والاتصال'], stats:['EG.ELC.ACCS.ZS','EG.CFT.ACCS.ZS','IT.NET.USER.ZS','EG.FEC.RNEW.ZS'], bars:['EG.ELC.ACCS.ZS','EG.CFT.ACCS.ZS','IT.NET.USER.ZS'],
      acts:[ ['EG.ELC.ACCS.ZS',1,'Off-grid and mini-grid solar for rural households, clinics and schools.','الطاقة الشمسية خارج الشبكة والشبكات المصغّرة للأرياف والعيادات والمدارس.'],
             ['EG.CFT.ACCS.ZS',1,'Clean-cooking programmes to cut household air pollution.','برامج الطهي النظيف للحد من تلوث الهواء المنزلي.'],
             ['IT.NET.USER.ZS',1,'Expand affordable broadband and digital public services.','توسيع النطاق العريض الميسور والخدمات الحكومية الرقمية.'],
             [null,3,'Improve grid reliability and cut transmission losses.','تحسين موثوقية الشبكة وخفض فواقد النقل.'] ] },
    { key:'economy', en:'Economy', ar:'الاقتصاد', short:['Economy','الاقتصاد'], stats:['NY.GDP.PCAP.PP.CD','NY.GDP.MKTP.KD.ZG','FP.CPI.TOTL.ZG','GC.TAX.TOTL.GD.ZS'], bars:['NY.GDP.MKTP.KD.ZG','FP.CPI.TOTL.ZG','GC.TAX.TOTL.GD.ZS','SL.UEM.TOTL.ZS','SI.POV.DDAY'],
      acts:[ ['GC.TAX.TOTL.GD.ZS',1,'Support domestic revenue mobilisation and public financial management.','دعم تعبئة الإيرادات المحلية وإدارة المالية العامة.'],
             ['FP.CPI.TOTL.ZG',1,'Protect vulnerable households from high inflation (targeted transfers).','حماية الأسر الهشة من التضخم المرتفع (تحويلات موجّهة).'],
             ['SL.UEM.TOTL.ZS',1,'Job creation: SME finance and skills for young people.','خلق فرص العمل: تمويل المنشآت الصغيرة ومهارات الشباب.'],
             ['SI.POV.DDAY',1,'Expand social protection for households in extreme poverty.','توسيع الحماية الاجتماعية للأسر في الفقر المدقع.'],
             [null,3,'Deepen financial inclusion and private investment.','تعميق الشمول المالي والاستثمار الخاص.'] ] },
  ];
  // sector status = worst current level among its benchmarked indicators
  SECTORS.forEach(s => {
    const lv = s.bars.map(lvl).filter(x => x != null);
    s.level = lv.length ? Math.min(...lv) : null;
    s.nSevere = lv.filter(x => x <= 1).length;
    const ranked = s.bars.filter(id => lvl(id) != null).sort((a, b) => lvl(a) - lvl(b));
    s.worst = ranked[0] || null;
    s.name = T(s.en, s.ar);
  });

  // ── deck ──
  const p = new Pptx();
  p.defineLayout({ name:'W', width:13.333, height:7.5 }); p.layout = 'W';
  p.title = NAME + T(' — Country Assessment', ' — تقييم الدولة'); p.author = T('ODA Country Assessment Dashboard', 'لوحة تقييم الدول — مكتب الشؤون التنموية');
  if (ar) p.rtlMode = true;
  let PAGE = 0, TOTAL = 0; const S = [];
  const newSlide = bg => { const sl = DK.slide(p, ar); sl.shape(p.ShapeType.rect, { x:0, y:0, w:13.333, h:7.5, fill:{ color: bg || C.WHITE }, line:{ type:'none' } }); PAGE++; return sl; };
  const eyebrow = (sl, t, x, y, w, col) => sl.text(ar ? t : String(t).toUpperCase(), { x, y, w, h:0.24, fontFace:BODY, fontSize:9, bold:true, color: col || C.GOLD, charSpacing:2.2 });
  const foot = (sl, src, dark) => {
    const lc = dark ? '3A5068' : C.LINE, tc = dark ? '9FB2C5' : C.FAINT;
    sl.shape(p.ShapeType.line, { x:0.5, y:7.1, w:12.33, h:0, line:{ color:lc, width:0.5 } });
    sl.text(T('Source: ', 'المصدر: ') + src, { x:0.5, y:7.15, w:9.6, h:0.24, fontFace:BODY, fontSize:8, color:tc, valign:'middle' });
    sl.text([{ text:'ODA', options:{ bold:true, color: dark ? C.GOLD_LT : C.NAVY } }, { text:'   ' + DK.pageLabel(PAGE, TOTAL, ar), options:{ color:tc } }],
      { x:10.4, y:7.15, w:2.43, h:0.24, fontFace:BODY, fontSize:8, align:'right', valign:'middle' });
  };
  const head = (sl, eb, title, statement) => {
    eyebrow(sl, eb, 0.5, 0.36, 9);
    sl.text([{ text:title, options:{ bold:true, color:C.INK } }, { text: statement ? '  —  ' + statement : '', options:{ color:C.MUTE } }],
      { x:0.5, y:0.6, w:12.33, h:0.56, fontFace:HEAD, fontSize:18, valign:'middle', fit:'shrink' });
  };
  const badge = (sl, L, x, y, w, h) => {
    const lab = L == null ? T('No data', 'لا بيانات') : DK.sevLabelOf(L, ar);
    sl.shape(p.ShapeType.roundRect, { x, y, w, h, rectRadius:0.06, fill:{ color: L == null ? C.LINE : SEV.fill[L] }, line:{ type:'none' } });
    sl.text(ar ? lab : lab.toUpperCase(), { x, y, w, h, fontFace:BODY, fontSize: h < 0.2 ? 6.4 : 7.5, bold:true, color: L == null ? C.MUTE : SEV.onFill[L], align:'center', valign:'middle' });
  };
  // stat card with severity-coloured top bar; outdated values flagged
  const statCard = (sl, id, x, y, w, h, compact) => {
    const r = R(id), L = lvlAny(id), pad = compact ? 0.12 : 0.16;
    sl.shape(p.ShapeType.rect, { x, y, w, h, fill:{ color:C.CARD }, line:{ type:'none' } });
    sl.shape(p.ShapeType.rect, { x, y, w, h:0.05, fill:{ color: L == null ? C.GOLD : SEV.fill[L] }, line:{ type:'none' } });
    sl.text(r ? I[id].f(r) : '—', { x:x + pad, y:y + (compact ? 0.1 : 0.14), w:w - 2 * pad, h: compact ? 0.4 : 0.5, fontFace:HEAD, fontSize: compact ? 19 : 24, bold:true, color: !r ? C.FAINT : (L != null && L <= 1) ? SEV.text[L] : C.INK, valign:'middle' });
    sl.text(lbl(id) + (I[id].u && r ? ' (' + I[id].u[ar ? 1 : 0].trim() + ')' : ''), { x:x + pad, y:y + (compact ? 0.5 : 0.62), w:w - 2 * pad, h:0.3, fontFace:BODY, fontSize: compact ? 7.4 : 8.2, bold:true, color:C.INK, valign:'top' });
    sl.text(cite(id), { x:x + pad, y:y + h - (compact ? 0.21 : 0.25), w:w - 2 * pad, h:0.18, fontFace:BODY, fontSize: compact ? 6.4 : 7, color: r && r.stale ? SEV.text[0] : C.FAINT, valign:'top', bold: !!(r && r.stale) });
  };
  const bullets = (sl, items, x, y, w, col, size) => {
    let yy = y; const per = Math.max(52, Math.round(w * 13));
    items.forEach(t => {
      const lines = Math.max(1, Math.ceil(String(t).length / per)), hh = 0.2 * lines + 0.1;
      sl.shape(p.ShapeType.ellipse, { x: x + 0.02, y: yy + 0.07, w:0.08, h:0.08, fill:{ color: col || C.SKY_DK }, line:{ type:'none' } });
      sl.text(t, { x: x + 0.22, y: yy, w: w - 0.22, h: hh, fontFace:BODY, fontSize: size || 9.6, color:C.INK, valign:'top', wrap:true });
      yy += hh + 0.1;
    });
    return yy;
  };
  // benchmark bars: value bar coloured by severity, benchmark marked with a gold tick
  const benchBars = (sl, ids, x, y, w, h) => {
    const rows = ids.filter(id => R(id) && target(id) != null);
    eyebrow(sl, T('Against benchmarks', 'مقارنةً بالمعايير'), x, y, w, C.SKY_DK);
    if (!rows.length) { sl.text(T('No benchmarked data available.', 'لا تتوفر بيانات مقارنة بالمعايير.'), { x, y:y + 0.5, w, h:0.4, fontFace:BODY, fontSize:10, color:C.FAINT }); return; }
    const rh = Math.min(0.92, (h - 0.4) / rows.length);
    rows.forEach((id, i) => {
      const r = R(id), L = DK.sevLvl(id, r.v), tg = target(id);
      const ry = y + 0.38 + i * rh, bx = x, bw = w, by = ry + 0.3, bh = 0.2;
      const max = /%/.test(I[id].f({ v:1 })) && rule(id).dir < 0 ? 100 : Math.max(r.v, tg) * 1.3;
      sl.text(lbl(id), { x, y:ry, w:w * 0.7, h:0.26, fontFace:BODY, fontSize:9, bold:true, color:C.INK, valign:'bottom' });
      sl.text(val(id) + (r.stale ? T(' (' + r.y + ')', ' (' + r.y + ')') : ''), { x:x + w * 0.5, y:ry, w:w * 0.5, h:0.26, fontFace:BODY, fontSize:9, bold:true, color: L != null && L <= 1 ? SEV.text[L] : C.INK, align:'right', valign:'bottom' });
      sl.shape(p.ShapeType.rect, { x:bx, y:by, w:bw, h:bh, fill:{ color:C.SKY_PALE }, line:{ type:'none' } });
      const fw = Math.max(0.04, Math.min(1, r.v / max) * bw);
      sl.shape(p.ShapeType.rect, { x:bx, y:by, w:fw, h:bh, fill:{ color: L == null ? C.SKY : SEV.fill[L] }, line:{ type:'none' } });
      const tx = bx + Math.min(1, tg / max) * bw;
      sl.shape(p.ShapeType.rect, { x:tx - 0.015, y:by - 0.07, w:0.03, h:bh + 0.14, fill:{ color:C.GOLD }, line:{ type:'none' } });
      const tShort = I[id].f({ v:tg });   // number only — the unit is already in the row label
      const lx = Math.max(bx, Math.min(tx - 0.6, bx + bw - 1.2));
      sl.text(T('Benchmark ', 'المعيار ') + tShort, { x:lx, y:by + bh + 0.02, w:1.2, h:0.2, fontFace:BODY, fontSize:7.2, color:C.GOLD, align:'center' });
    });
  };

  // ══ 1 · COVER ══
  S.push(() => {
    const sl = newSlide(C.NAVY);
    sl.shape(p.ShapeType.rect, { x:0, y:7.0, w:13.333, h:0.5, fill:{ color:C.INK }, line:{ type:'none' } });
    sl.shape(p.ShapeType.rect, { x:0, y:6.96, w:13.333, h:0.04, fill:{ color:C.GOLD }, line:{ type:'none' } });
    if (opts.logo && opts.logo.data) {   // ODA logo on a white chip, proportions preserved
      sl.shape(p.ShapeType.roundRect, { x:0.6, y:0.55, w:2.9, h:0.9, rectRadius:0.08, fill:{ color:C.WHITE }, line:{ type:'none' } });
      const lg = DK.contain(opts.logo.ratio, 0.75, 0.66, 2.6, 0.68);
      sl.image({ data:opts.logo.data, x:lg.x, y:lg.y, w:lg.w, h:lg.h });
    }
    sl.text(T('COUNTRY ASSESSMENT', 'تقييم الدولة'), { x:0.6, y:2.25, w:8, h:0.3, fontFace:BODY, fontSize:11, bold:true, color:C.GOLD_LT, charSpacing:3 });
    sl.text(NAME, { x:0.55, y:2.6, w:8.4, h:1.3, fontFace:HEAD, fontSize: NAME.length > 18 ? 40 : 54, bold:true, color:C.WHITE, valign:'top', fit:'shrink' });
    sl.shape(p.ShapeType.rect, { x:0.6, y:4.05, w:1.1, h:0.05, fill:{ color:C.GOLD }, line:{ type:'none' } });
    sl.text(T('Development needs, sector by sector — an instant assessment built from live World Bank data.', 'الاحتياجات التنموية قطاعاً بقطاع — تقييم فوري مبني على بيانات البنك الدولي المباشرة.'),
      { x:0.6, y:4.3, w:7.8, h:0.8, fontFace:BODY, fontSize:14, color:C.SKY_LT, valign:'top', wrap:true });
    sl.text([REGION, INCOME].filter(Boolean).join('  ·  '), { x:0.6, y:5.25, w:7.8, h:0.35, fontFace:BODY, fontSize:12, bold:true, color:C.WHITE });
    if (opts.flagData) {   // flag at its true proportions (fitted in a 3.2 × 2.2 in area) with a fine white frame
      const f = DK.contain(opts.flagRatio, 9.5, 2.5, 3.2, 2.2);
      sl.shape(p.ShapeType.rect, { x:f.x - 0.07, y:f.y - 0.07, w:f.w + 0.14, h:f.h + 0.14, fill:{ color:C.WHITE }, line:{ type:'none' } });
      sl.image({ data:opts.flagData, x:f.x, y:f.y, w:f.w, h:f.h });
    }
    sl.text(DATE, { x:0.6, y:7.05, w:5, h:0.4, fontFace:BODY, fontSize:10, bold:true, color:C.GOLD_LT, valign:'middle' });
    sl.text(T('Office of Development Affairs', 'مكتب الشؤون التنموية'), { x:7.7, y:7.05, w:5.03, h:0.4, fontFace:BODY, fontSize:10, color:C.SKY_LT, align:'right', valign:'middle' });
  });

  // ══ 2 · COUNTRY OVERVIEW — map, key facts, people, status per sector ══
  S.push(() => {
    const sl = newSlide(C.WHITE);
    head(sl, T('Country overview', 'نظرة عامة على الدولة'), NAME, T('location, key figures and status by sector', 'الموقع والأرقام الرئيسية والوضع حسب القطاع'));
    // map — accurate borders, rendered at exactly this slot's aspect ratio (never stretched)
    const M = DK.MAP_SLOTS.country, mx = 0.5, my = 1.35;
    if (opts.mapData) sl.image({ data:opts.mapData, x:mx, y:my, w:M.w, h:M.h });
    else { sl.shape(p.ShapeType.rect, { x:mx, y:my, w:M.w, h:M.h, fill:{ color:C.SKY_PALE }, line:{ type:'none' } });
      sl.text(T('Map unavailable', 'الخريطة غير متاحة'), { x:mx, y:my + M.h / 2 - 0.2, w:M.w, h:0.4, fontFace:BODY, fontSize:11, color:C.FAINT, align:'center' }); }
    sl.shape(p.ShapeType.rect, { x:mx, y:my + M.h + 0.1, w:0.16, h:0.12, fill:{ color:C.SKY_DK }, line:{ type:'none' } });
    sl.text(NAME + T(' · national borders (Natural Earth)', ' · الحدود الوطنية (Natural Earth)'), { x:mx + 0.24, y:my + M.h + 0.04, w:M.w - 0.3, h:0.24, fontFace:BODY, fontSize:7.6, color:C.FAINT, valign:'middle' });
    // right column
    const RX = 6.85, RW = 13.333 - RX - 0.5;
    const info = ar && typeof AR_INFO !== 'undefined' && AR_INFO[country] ? { capital:AR_INFO[country][0], currency:AR_INFO[country][1], languages:AR_INFO[country][2] } : (opts.info || {});
    const facts = [[T('Region', 'الإقليم'), REGION], [T('Income group', 'فئة الدخل'), INCOME], [T('Capital', 'العاصمة'), info.capital], [T('Currency', 'العملة'), info.currency], [T('Languages', 'اللغات'), info.languages]].filter(f => f[1]);
    eyebrow(sl, T('Key facts', 'معلومات أساسية'), RX, 1.35, RW, C.SKY_DK);
    facts.forEach(([k, v], i) => {
      const fx = RX + (i % 2) * (RW / 2), fy = 1.65 + Math.floor(i / 2) * 0.42;
      sl.text([{ text:k + ':  ', options:{ color:C.MUTE } }, { text:v, options:{ color:C.INK, bold:true } }], { x:fx, y:fy, w:RW / 2 - 0.1, h:0.36, fontFace:BODY, fontSize:9.4, valign:'middle' });
    });
    eyebrow(sl, T('People & living conditions', 'السكان والظروف المعيشية'), RX, 2.95, RW, C.SKY_DK);
    const tiles = ['SP.POP.TOTL', 'NY.GDP.PCAP.PP.CD', 'SH.DYN.MORT', 'SN.ITK.DEFC.ZS', 'SH.H2O.BASW.ZS', 'EG.ELC.ACCS.ZS'];
    const tw = (RW - 0.3) / 3, th = 0.98;
    tiles.forEach((id, i) => statCard(sl, id, RX + (i % 3) * (tw + 0.15), 3.25 + Math.floor(i / 3) * (th + 0.12), tw, th, true));
    // need index + sector status
    const by = 5.5, bh = 1.45;
    sl.shape(p.ShapeType.rect, { x:RX, y:by, w:1.75, h:bh, fill:{ color:C.SKY_PALE }, line:{ type:'none' } });
    sl.text(T('NEED INDEX', 'مؤشر الاحتياج'), { x:RX + 0.15, y:by + 0.12, w:1.5, h:0.22, fontFace:BODY, fontSize:8, bold:true, color:C.GOLD, charSpacing:1.4 });
    if (opts.need) {
      sl.text(String(Math.round(opts.need.score)), { x:RX + 0.15, y:by + 0.36, w:1.5, h:0.6, fontFace:HEAD, fontSize:34, bold:true, color:C.INK, valign:'middle' });
      sl.text(T('of 100 · rank ' + opts.need.rank + '/' + opts.need.of, 'من 100 · الترتيب ' + opts.need.rank + ' من ' + opts.need.of), { x:RX + 0.15, y:by + 1.0, w:1.5, h:0.32, fontFace:BODY, fontSize:8.4, color:C.MUTE });
    } else sl.text(T('Not ranked', 'غير مصنّفة'), { x:RX + 0.15, y:by + 0.5, w:1.5, h:0.4, fontFace:BODY, fontSize:10, color:C.MUTE });
    const sx = RX + 1.95, sw = RW - 1.95;
    sl.text(T('STATUS BY SECTOR', 'الوضع حسب القطاع'), { x:sx, y:by - 0.02, w:sw, h:0.22, fontFace:BODY, fontSize:8, bold:true, color:C.GOLD, charSpacing:1.4 });
    SECTORS.forEach((s, i) => {
      const yy = by + 0.24 + i * 0.205;
      sl.text(T(s.short[0], s.short[1]), { x:sx, y:yy, w:sw - 1.3, h:0.19, fontFace:BODY, fontSize:8.4, color:C.INK, valign:'middle' });
      badge(sl, s.level, sx + sw - 1.2, yy + 0.015, 1.2, 0.165);
    });
    foot(sl, T('World Bank Open Data · Natural Earth (borders) · ', 'بيانات البنك الدولي · Natural Earth (الحدود) · ') + DATE);
  });

  // ══ 3 · EXECUTIVE SUMMARY ══
  S.push(() => {
    const sl = newSlide(C.WHITE);
    head(sl, T('Executive summary', 'الملخص التنفيذي'), NAME, T('where needs are greatest and why', 'أين يكمن الاحتياج الأكبر ولماذا'));
    // overall picture
    const n = opts.need;
    const tierTxt = n ? (n.rank <= n.of / 3 ? T('among the highest', 'ضمن الأعلى') : n.rank <= 2 * n.of / 3 ? T('in the middle', 'في المنتصف') : T('among the lower', 'ضمن الأدنى')) : '';
    const priorities = SECTORS.filter(s => s.level != null && s.level <= 1).sort((a, b) => a.level - b.level || b.nSevere - a.nSevere);
    const overall = [
      n ? T(`${NAME} scores ${Math.round(n.score)}/100 on the ODA need index — rank ${n.rank} of ${n.of}, ${tierTxt} need among the countries ODA tracks.`,
            `تسجّل ${NAME} ${Math.round(n.score)} من 100 على مؤشر الاحتياج — الترتيب ${n.rank} من ${n.of}، أي ${tierTxt} احتياجاً بين الدول التي يتابعها المكتب.`) : null,
      priorities.length === SECTORS.length ? T(`All ${SECTORS.length} sectors are rated severe or high concern — needs are broad-based, not confined to one area.`,
                                               `جميع القطاعات الستة مصنّفة حرجة أو مقلقة — أي أن الاحتياجات واسعة ولا تقتصر على مجال واحد.`)
      : priorities.length ? T(`${priorities.length} of ${SECTORS.length} sectors are rated severe or high concern: ${priorities.map(s => s.en.toLowerCase()).join(', ')}.`,
                             `${priorities.length} من ${SECTORS.length} قطاعات مصنّفة حرجة أو مقلقة: ${priorities.map(s => s.ar).join('، ')}.`)
                        : T('No sector is rated severe or high concern on current data.', 'لا يوجد قطاع مصنّف حرجاً أو مقلقاً وفق البيانات الحالية.'),
    ].filter(Boolean);
    eyebrow(sl, T('Overall picture', 'الصورة العامة'), 0.5, 1.4, 6.2, C.SKY_DK);
    bullets(sl, overall, 0.5, 1.72, 6.2, C.GOLD, 10.5);
    // priority sectors
    eyebrow(sl, T('Priority sectors', 'القطاعات ذات الأولوية'), 0.5, 3.15, 6.2, C.SKY_DK);
    const top3 = (priorities.length ? priorities : SECTORS.filter(s => s.level != null).sort((a, b) => a.level - b.level)).slice(0, 3);
    top3.forEach((s, i) => {
      const y = 3.5 + i * 0.95;
      sl.shape(p.ShapeType.rect, { x:0.5, y, w:6.2, h:0.82, fill:{ color:C.CARD }, line:{ type:'none' } });
      sl.shape(p.ShapeType.rect, { x:0.5, y, w:0.06, h:0.82, fill:{ color: s.level == null ? C.GOLD : SEV.fill[s.level] }, line:{ type:'none' } });
      sl.text(s.name, { x:0.75, y:y + 0.08, w:4.0, h:0.3, fontFace:HEAD, fontSize:13, bold:true, color:C.INK });
      badge(sl, s.level, 5.45, y + 0.12, 1.1, 0.22);
      sl.text(s.worst ? sentence(s.worst) : '', { x:0.75, y:y + 0.38, w:5.8, h:0.4, fontFace:BODY, fontSize:8.6, color:C.MUTE, valign:'top', fit:'shrink' });
    });
    // urgent gaps
    const RX = 7.1, RW = 5.73;
    eyebrow(sl, T('Most urgent gaps', 'أكثر الفجوات إلحاحاً'), RX, 1.4, RW, C.SKY_DK);
    const allIds = [...new Set(SECTORS.flatMap(s => s.bars))];
    const gaps = allIds.filter(id => lvl(id) != null && lvl(id) <= 1).sort((a, b) => lvl(a) - lvl(b)).slice(0, 5);
    if (gaps.length) gaps.forEach((id, i) => {
      const y = 1.72 + i * 0.58, L = lvl(id);
      sl.shape(p.ShapeType.rect, { x:RX, y, w:RW, h:0.5, fill:{ color: SEV.tint[L] }, line:{ type:'none' } });
      sl.text(lbl(id), { x:RX + 0.15, y, w:RW * 0.55, h:0.5, fontFace:BODY, fontSize:9.5, bold:true, color:C.INK, valign:'middle', fit:'shrink' });
      sl.text([{ text: val(id), options:{ bold:true, color:SEV.text[L] } }, { text: T('  ·  benchmark ', '  ·  المعيار ') + I[id].f({ v:target(id) }), options:{ color:C.MUTE } }],
        { x:RX + RW * 0.5, y, w:RW * 0.5 - 0.15, h:0.5, fontFace:BODY, fontSize:9, align:'right', valign:'middle', fit:'shrink' });
    });
    else sl.text(T('No indicator is in the severe or high-concern band.', 'لا يوجد مؤشر في نطاق الحرج أو القلق.'), { x:RX, y:1.75, w:RW, h:0.4, fontFace:BODY, fontSize:10, color:C.MUTE });
    // strengths + data notes
    const strengths = allIds.filter(id => lvl(id) === 3).slice(0, 3);
    let y2 = 1.72 + Math.max(1, gaps.length) * 0.58 + 0.25;
    eyebrow(sl, T('Strengths', 'نقاط القوة'), RX, y2, RW, C.SKY_DK);
    y2 = bullets(sl, strengths.length ? strengths.map(id => T(`${lbl(id)}: ${val(id)} — on track.`, `${lbl(id)}: ${val(id)} — على المسار.`))
      : [T('No indicator is yet on track against its benchmark.', 'لا يوجد مؤشر يحقق معياره حتى الآن.')], RX, y2 + 0.32, RW, SEV.fill[3], 9.2);
    const stale = allIds.filter(id => R(id) && R(id).stale), missing = allIds.filter(id => !R(id));
    if (stale.length || missing.length) {
      eyebrow(sl, T('Data notes', 'ملاحظات البيانات'), RX, y2 + 0.1, RW, C.FAINT);
      const nEn = (n, one, many) => n + ' ' + (n === 1 ? one : many);
      sl.text(T([missing.length ? nEn(missing.length, 'indicator has', 'indicators have') + ' no recent data' : null,
                 stale.length ? nEn(stale.length, 'indicator relies', 'indicators rely') + ` on figures older than ${DK.STALE_YEARS} years and ${stale.length === 1 ? 'is' : 'are'} excluded from ratings` : null].filter(Boolean).join('; ') + '.',
                [missing.length ? `${missing.length} من المؤشرات بلا بيانات حديثة` : null,
                 stale.length ? `${stale.length} من المؤشرات تعتمد على أرقام أقدم من ${DK.STALE_YEARS} سنوات واستُبعدت من التصنيف` : null].filter(Boolean).join('، ') + '.'),
        { x:RX, y:y2 + 0.4, w:RW, h:0.5, fontFace:BODY, fontSize:8.6, color:C.MUTE, valign:'top' });
    }
    foot(sl, T('ODA need index and SDG/WHO benchmarks · World Bank Open Data · ', 'مؤشر الاحتياج ومعايير أهداف التنمية المستدامة · بيانات البنك الدولي · ') + DATE);
  });

  // ══ 4–9 · SECTOR SLIDES ══
  SECTORS.forEach(s => S.push(() => {
    const sl = newSlide(C.WHITE);
    const st = s.level == null ? T('no current benchmarked data', 'لا توجد بيانات حديثة قابلة للمقارنة')
      : s.level === 0 ? T('severe gaps against benchmarks', 'فجوات حرجة مقارنةً بالمعايير')
      : s.level === 1 ? T('high concern on key indicators', 'قلق مرتفع في مؤشرات رئيسية')
      : s.level === 2 ? T('progress made, still short of benchmarks', 'تقدّم ملحوظ لكن دون المعايير')
      : T('key indicators meet their benchmarks', 'المؤشرات الرئيسية تحقق معاييرها');
    head(sl, T('Sector assessment', 'تقييم القطاع'), s.name, st);
    badge(sl, s.level, 11.53, 0.38, 1.3, 0.26);
    // stat cards 2×2
    const LX = 0.5, LW = 7.0, cw = (LW - 0.2) / 2, ch = 1.12;
    s.stats.forEach((id, i) => statCard(sl, id, LX + (i % 2) * (cw + 0.2), 1.38 + Math.floor(i / 2) * (ch + 0.16), cw, ch));
    // insights: worst first, then outdated-data notes
    const ins = s.bars.filter(id => lvl(id) != null).sort((a, b) => lvl(a) - lvl(b)).map(sentence).slice(0, 3);
    const notes = [...new Set(s.stats.concat(s.bars))].map(staleNote).filter(Boolean).slice(0, 1);
    eyebrow(sl, T('Key insights', 'أبرز الملاحظات'), LX, 3.95, LW, C.SKY_DK);
    const insItems = (ins.length ? ins : [T('There is not enough current data to assess this sector against benchmarks.', 'لا تتوفر بيانات حديثة كافية لتقييم هذا القطاع مقارنةً بالمعايير.')]).concat(notes).slice(0, 3);
    const endY = bullets(sl, insItems, LX, 4.25, LW, null, 9.2);
    // interventions: triggered by the indicators that are actually off-track; one per row so nothing overlaps
    const iy = Math.max(endY + 0.06, 5.3), ih = 6.98 - iy, rowH = 0.3;
    const acts = s.acts.filter(([id, maxL]) => id === null ? true : (lvl(id) != null && lvl(id) <= maxL)).map(a => T(a[2], a[3]))
      .slice(0, Math.max(1, Math.min(4, Math.floor((ih - 0.4) / rowH))));
    sl.shape(p.ShapeType.rect, { x:LX, y:iy, w:LW, h:ih, fill:{ color:C.GOLD_PALE }, line:{ type:'none' } });
    sl.shape(p.ShapeType.rect, { x:LX, y:iy, w:0.06, h:ih, fill:{ color:C.GOLD }, line:{ type:'none' } });
    eyebrow(sl, T('Potential interventions', 'تدخلات مقترحة'), LX + 0.22, iy + 0.09, LW - 0.4);
    acts.forEach((t, i) => sl.text([{ text:'▸  ', options:{ color:C.GOLD, bold:true } }, { text:t, options:{ color:C.INK } }],
      { x:LX + 0.22, y:iy + 0.36 + i * rowH, w:LW - 0.4, h:rowH, fontFace:BODY, fontSize:8.8, valign:'middle' }));
    // benchmark chart
    benchBars(sl, s.bars, 7.95, 1.38, 4.88, 5.5);
    const srcs = [...new Set(s.stats.concat(s.bars).map(id => SRC[id]).filter(Boolean).flatMap(x => x.split(' · ')))].slice(0, 5).map(srcTxt).join(' · ');
    foot(sl, srcs + ' · ' + DATE);
  }));

  // ══ 10 · METHOD & SOURCES ══
  S.push(() => {
    const sl = newSlide(C.NAVY);
    sl.text(T('METHOD & SOURCES', 'المنهجية والمصادر'), { x:0.6, y:0.6, w:9, h:0.3, fontFace:BODY, fontSize:10, bold:true, color:C.GOLD_LT, charSpacing:2.6 });
    sl.text(NAME, { x:0.57, y:0.95, w:12, h:0.9, fontFace:HEAD, fontSize:38, bold:true, color:C.WHITE });
    sl.shape(p.ShapeType.rect, { x:0.6, y:1.95, w:0.9, h:0.035, fill:{ color:C.GOLD }, line:{ type:'none' } });
    const blocks = [
      [T('How ratings work', 'آلية التصنيف'), T('Each indicator is rated Severe · High concern · Moderate · On track against SDG, WHO, UNESCO and IMF reference points — the same scale used on the dashboard. A sector takes the rating of its weakest current indicator.',
        'يُصنَّف كل مؤشر (حرج · مقلق · متوسط · على المسار) وفق مرجعيات أهداف التنمية المستدامة ومنظمة الصحة العالمية واليونسكو وصندوق النقد — وهو المقياس نفسه المستخدم في اللوحة. ويأخذ القطاع تصنيف أضعف مؤشراته الحديثة.')],
      [T('Data quality rules', 'قواعد جودة البيانات'), T(`Figures older than ${DK.STALE_YEARS} years are shown with their year but excluded from ratings and narrative. Missing or implausible values (e.g. 0% spending) are shown as "—" rather than estimated.`,
        `تُعرض الأرقام الأقدم من ${DK.STALE_YEARS} سنوات مع سنتها لكنها تُستبعد من التصنيف والسرد. وتُعرض القيم المفقودة أو غير المعقولة (مثل إنفاق 0%) بعلامة «—» دون تقدير.`)],
      [T('ODA need index', 'مؤشر الاحتياج'), T('Combines under-5 and maternal mortality, undernourishment and lack of basic water, sanitation and electricity, each scaled across all tracked countries (0–100).',
        'يجمع بين وفيات الأطفال دون الخامسة ووفيات الأمهات ونقص التغذية ونقص مياه الشرب الأساسية والصرف الصحي والكهرباء، مع قياس كل منها عبر جميع الدول المتابَعة (0–100).')],
      [T('Sources', 'المصادر'), [T('World Bank Open Data', 'بيانات البنك الدولي المفتوحة'), 'IMF', 'WHO', 'UN IGME (UNICEF/WHO)', 'UNESCO UIS', 'FAO', 'WHO/UNICEF JMP', 'ITU', 'IEA', 'ILO'].map(x => ar ? srcTxt(x) : x).join(' · ') +
        T(` — retrieved live on building this report (${DATE}).`, ` — استُرجعت مباشرة عند إعداد هذا التقرير (${DATE}).`)],
    ];
    blocks.forEach(([h, t], i) => {
      const x = 0.6 + (i % 2) * 6.2, y = 2.35 + Math.floor(i / 2) * 2.1;
      sl.text(ar ? h : h.toUpperCase(), { x, y, w:5.8, h:0.26, fontFace:BODY, fontSize:9.5, bold:true, color:C.GOLD_LT, charSpacing:1.6 });
      sl.text(t, { x, y:y + 0.32, w:5.8, h:1.5, fontFace:BODY, fontSize:10.5, color:'E6EEF5', valign:'top', wrap:true });
    });
    foot(sl, T('ODA Country Assessment Dashboard · ', 'لوحة تقييم الدول · ') + DATE, true);
  });

  TOTAL = S.length;
  S.forEach(fn => fn());
  if (opts.output === 'blob') return p.write({ outputType:'blob' });
  return p.writeFile({ fileName: opts.fileName || `${country.replace(/\s+/g, '_')}_Country_Assessment.pptx` });
}

if (typeof window !== 'undefined') window.buildCountryDeck = buildCountryDeck;
if (typeof module !== 'undefined' && module.exports) module.exports = { buildCountryDeck };
