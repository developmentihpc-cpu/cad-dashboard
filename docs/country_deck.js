/* country_deck.js — ODA instant country assessment deck (English or Arabic).
 *
 * 12 slides: cover · country overview (map with neighbours, flag, leaders and terms, political situation
 * with colour key, need index, status by sector) · executive summary (priority sectors and their most
 * urgent gaps) · eight sector slides (water, energy, agriculture & food security, education, health,
 * economic empowerment, business enablement, trade) · method & sources. Governance appears only in the
 * overview slide's political-situation box.
 * A sector gets an extra "where the need is" map slide only when a recent DHS survey measured, region by
 * region, one of that sector's two most critical issues (opts.subnational, built in index.html); that
 * issue then leads the sector slide so the map continues its story.
 *
 * Every rating uses the shared severity scale (severity.js) — the same one the dashboard shows.
 * Sector slides: stat cards carry their benchmark and gap; key insights explain the "so what" — the
 * linked factors that are also off track in this country's data (WHY / DP) and what the gap means;
 * interventions add a development-investment angle where the data makes it relevant (inv).
 * Indicators without data are left off the slides; outdated values are shown with their year but
 * kept out of ratings and narrative.
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
    'SE.ADT.LITR.ZS':'UNESCO UIS', 'SE.PRM.CMPT.ZS':'UNESCO UIS', 'SE.SEC.ENRR':'UNESCO UIS', 'SE.XPD.TOTL.GD.ZS':'UNESCO · World Bank', 'SE.PRM.ENRL.TC.ZS':'UNESCO UIS',
    'AG.YLD.CREL.KG':'FAO', 'NV.AGR.TOTL.ZS':'World Bank', 'SH.H2O.BASW.ZS':'WHO/UNICEF JMP', 'SH.H2O.SMDW.ZS':'WHO/UNICEF JMP', 'SH.STA.BASS.ZS':'WHO/UNICEF JMP',
    'SH.STA.SMSS.ZS':'WHO/UNICEF JMP', 'SH.STA.ODFC.ZS':'WHO/UNICEF JMP', 'EG.ELC.ACCS.ZS':'World Bank · IEA', 'EG.CFT.ACCS.ZS':'WHO', 'IT.NET.USER.ZS':'ITU',
    'EG.FEC.RNEW.ZS':'IEA · World Bank', 'GOV_WGI_PV.SC':'World Bank WGI', 'GOV_WGI_VA.SC':'World Bank WGI', 'GOV_WGI_GE.SC':'World Bank WGI',
    'GOV_WGI_RL.SC':'World Bank WGI', 'GOV_WGI_CC.SC':'World Bank WGI',
    'SL.UEM.1524.ZS':'ILO', 'SL.TLF.CACT.FE.ZS':'ILO', 'SL.EMP.VULN.ZS':'ILO', 'FX.OWN.TOTL.ZS':'World Bank Global Findex', 'SI.POV.GINI':'World Bank',
    'SN.ITK.MSFI.ZS':'FAO', 'FS.AST.PRVT.GD.ZS':'IMF · World Bank', 'BX.KLT.DINV.WD.GD.ZS':'IMF · World Bank', 'FR.INR.LEND':'IMF',
    'IC.FRM.BKWC.ZS':'World Bank Enterprise Surveys', 'IC.ELC.OUTG.ZS':'World Bank Enterprise Surveys', 'IC.BUS.NDNS.ZS':'World Bank', 'LP.LPI.OVRL.XQ':'World Bank LPI',
    'NE.EXP.GNFS.ZS':'World Bank', 'TM.TAX.MRCH.WM.AR.ZS':'World Bank WITS', 'BN.CAB.XOKA.GD.ZS':'IMF', 'TX.VAL.MANF.ZS.UN':'UN Comtrade · World Bank' };
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
    'SE.PRM.ENRL.TC.ZS':    { en:'Pupils per teacher (primary)', ar:'التلاميذ لكل معلم (ابتدائي)', f: r => F.num(r) },
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
    'SI.POV.DDAY':       { en:'Extreme poverty (<$3.00/day)', ar:'الفقر المدقع (أقل من 3.00 دولار يومياً)', f: r => F.pct(r, 1) },
    'GC.DOD.TOTL.GD.ZS': { en:'Government debt (% of GDP)', ar:'الدين الحكومي (% من الناتج)', f: r => F.pct(r) },
    'SP.POP.TOTL':       { en:'Population', ar:'عدد السكان', f: r => F.pop(r) },
    'GOV_WGI_PV.SC':     { en:'Political stability (0–100)', ar:'الاستقرار السياسي (0–100)', f: r => F.num(r) },
    'GOV_WGI_VA.SC':     { en:'Voice & accountability (0–100)', ar:'المشاركة والمساءلة (0–100)', f: r => F.num(r) },
    'GOV_WGI_GE.SC':     { en:'Government effectiveness (0–100)', ar:'فعالية الحكومة (0–100)', f: r => F.num(r) },
    'GOV_WGI_RL.SC':     { en:'Rule of law (0–100)', ar:'سيادة القانون (0–100)', f: r => F.num(r) },
    'GOV_WGI_CC.SC':     { en:'Control of corruption (0–100)', ar:'مكافحة الفساد (0–100)', f: r => F.num(r) },
    // Economic empowerment · Business enablement · Trade
    'SL.UEM.1524.ZS':    { en:'Youth unemployment (15–24)', ar:'بطالة الشباب (15–24)', f: r => F.pct(r, 1) },
    'SL.TLF.CACT.FE.ZS': { en:'Women in the labour force', ar:'مشاركة المرأة في القوى العاملة', f: r => F.pct(r) },
    'SL.EMP.VULN.ZS':    { en:'Vulnerable employment', ar:'العمالة الهشة', f: r => F.pct(r) },
    'FX.OWN.TOTL.ZS':    { en:'Adults with an account', ar:'البالغون الذين لديهم حساب', f: r => F.pct(r) },
    'SI.POV.GINI':       { en:'Inequality (Gini index)', ar:'عدم المساواة (مؤشر جيني)', f: r => F.num(r, 1) },
    'SN.ITK.MSFI.ZS':    { en:'Moderate or severe food insecurity', ar:'انعدام الأمن الغذائي المتوسط أو الشديد', f: r => F.pct(r) },
    'FS.AST.PRVT.GD.ZS': { en:'Private-sector credit (% of GDP)', ar:'الائتمان للقطاع الخاص (% من الناتج)', f: r => F.pct(r) },
    'BX.KLT.DINV.WD.GD.ZS': { en:'Foreign direct investment (% of GDP)', ar:'الاستثمار الأجنبي المباشر (% من الناتج)', f: r => F.pct(r, 1) },
    'FR.INR.LEND':       { en:'Lending interest rate', ar:'سعر الفائدة على القروض', f: r => F.pct(r, 1) },
    'IC.FRM.BKWC.ZS':    { en:'Firms using bank credit', ar:'الشركات التي تستخدم الائتمان المصرفي', f: r => F.pct(r) },
    'IC.ELC.OUTG.ZS':    { en:'Firms hit by power outages', ar:'الشركات المتأثرة بانقطاع الكهرباء', f: r => F.pct(r) },
    'IC.BUS.NDNS.ZS':    { en:'New businesses per 1,000 adults', ar:'الشركات الجديدة لكل 1,000 بالغ', f: r => F.num(r, 2) },
    'LP.LPI.OVRL.XQ':    { en:'Logistics performance (1–5)', ar:'الأداء اللوجستي (1–5)', f: r => F.num(r, 2) },
    'NE.EXP.GNFS.ZS':    { en:'Exports (% of GDP)', ar:'الصادرات (% من الناتج)', f: r => F.pct(r) },
    'TM.TAX.MRCH.WM.AR.ZS': { en:'Average import tariff', ar:'متوسط التعريفة الجمركية', f: r => F.pct(r, 1) },
    'BN.CAB.XOKA.GD.ZS': { en:'Current account balance (% of GDP)', ar:'رصيد الحساب الجاري (% من الناتج)', f: r => F.pct(r, 1) },
    'TX.VAL.MANF.ZS.UN': { en:'Manufactured goods (% of exports)', ar:'السلع المصنّعة (% من الصادرات)', f: r => F.pct(r) },
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

  const isPts = id => (/%$/.test(I[id].f({ v:1 })) && !/\.GD\.ZS$/.test(id)) || /^GOV_WGI/.test(id) || id === 'BN.CAB.XOKA.GD.ZS';   // shares of people and 0–100 scores: gap in points; % of GDP: relative gap
  // gap against the benchmark — short for stat cards ("3.9× higher"), long for insights ("3.9× the benchmark")
  function gap(id, long) {
    const r = R(id), t = target(id), L = lvl(id);
    if (!r || t == null || L == null) return '';
    if (L === 3) return long ? T('meets the benchmark', 'يحقق المعيار') : T('met', 'محقق');
    const dir = rule(id).dir, tail = long ? T(' the benchmark', ' من المعيار') : '';
    if (isPts(id)) { const d = Math.round(Math.abs(r.v - t)); return d < 1 ? '' :
      dir < 0 ? T(`${d} pts below`, `أقل بـ${d} نقطة`) + tail : T(`${d} pts above`, `أعلى بـ${d} نقطة`) + tail; }
    if (dir > 0) { const k = r.v / t; return k >= 1.15 ? (long ? T(`${k.toFixed(1)}× the benchmark`, `${k.toFixed(1)} أضعاف المعيار`) : T(`${k.toFixed(1)}× higher`, `${k.toFixed(1)} أضعاف`))
      : T('above', 'أعلى') + tail; }
    const b = Math.round((1 - r.v / t) * 100); return b < 1 ? '' : T(`${b}% below`, `أقل بنسبة ${b}%`) + tail;
  }
  // people affected, from a national rate × population (only where the rate applies to the whole population)
  const POP = R('SP.POP.TOTL');
  const PEOPLE = { 'SH.H2O.BASW.ZS':-1, 'SH.STA.BASS.ZS':-1, 'EG.ELC.ACCS.ZS':-1, 'EG.CFT.ACCS.ZS':-1, 'SN.ITK.DEFC.ZS':1, 'SI.POV.DDAY':1 };
  const people = id => { const r = R(id); if (!r || r.stale || !POP || PEOPLE[id] == null) return null;
    const n = POP.v * (PEOPLE[id] > 0 ? r.v / 100 : 1 - r.v / 100); return n >= 1e5 ? F.pop({ v:n }) : null; };
  const off = (id, maxL) => lvl(id) != null && lvl(id) <= maxL;                        // indicator is off track
  const atLeast = (id, min) => { const r = R(id); return !!(r && !r.stale && r.v >= min); };

  // ── "so what" analysis: for each problem indicator, the related indicators that are also off track in this
  //    country's data (linked factors) and what the gap means in practice. Linked factors are only named when
  //    the data shows them, so the explanation always fits this country.
  const DP = {   // how a linked factor is described (v = value with unit, n = people affected)
    'SH.MED.PHYS.ZS':    v => T(`only ${v} doctors per 1,000 people`, `${v} طبيب فقط لكل 1,000 نسمة`),
    'SH.IMM.MEAS':       v => T(`measles immunisation at ${v}`, `تحصين ضد الحصبة بنسبة ${v}`),
    'SH.XPD.CHEX.GD.ZS': v => T(`health spending of ${v} of GDP`, `إنفاق صحي لا يتجاوز ${v} من الناتج`),
    'SH.H2O.BASW.ZS':    (v, n) => n ? T(`${n} people without basic drinking water`, `${n} شخص بلا مياه شرب أساسية`) : T(`basic water access at ${v}`, `وصول إلى مياه الشرب الأساسية بنسبة ${v}`),
    'SH.STA.BASS.ZS':    (v, n) => n ? T(`${n} people without basic sanitation`, `${n} شخص بلا صرف صحي أساسي`) : T(`basic sanitation at ${v}`, `صرف صحي أساسي بنسبة ${v}`),
    'SH.STA.ODFC.ZS':    v => T(`${v} of people practising open defecation`, `${v} من السكان يمارسون التغوط في العراء`),
    'SH.STA.STNT.ZS':    v => T(`${v} of children stunted`, `${v} من الأطفال يعانون التقزّم`),
    'SN.ITK.DEFC.ZS':    (v, n) => n ? T(`${n} people undernourished`, `${n} شخص يعانون نقص التغذية`) : T(`undernourishment at ${v}`, `نقص تغذية بنسبة ${v}`),
    'SI.POV.DDAY':       (v, n) => n ? T(`${n} people in extreme poverty`, `${n} شخص في فقر مدقع`) : T(`extreme poverty at ${v}`, `فقر مدقع بنسبة ${v}`),
    'FP.CPI.TOTL.ZG':    v => T(`inflation of ${v}`, `تضخم بنسبة ${v}`),
    'AG.YLD.CREL.KG':    v => T(`cereal yields of ${v}`, `إنتاجية حبوب لا تتجاوز ${v}`),
    'NV.AGR.TOTL.ZS':    v => T(`agriculture making up ${v} of GDP`, `زراعة تشكّل ${v} من الناتج`),
    'SE.PRM.ENRL.TC.ZS': v => T(`${v} pupils per teacher`, `${v} تلميذاً لكل معلم`),
    'SE.XPD.TOTL.GD.ZS': v => T(`education spending of ${v} of GDP`, `إنفاق على التعليم لا يتجاوز ${v} من الناتج`),
    'SE.PRM.CMPT.ZS':    v => T(`primary completion at ${v}`, `إتمام المرحلة الابتدائية بنسبة ${v}`),
    'GC.TAX.TOTL.GD.ZS': v => T(`tax revenue of ${v} of GDP`, `إيرادات ضريبية لا تتجاوز ${v} من الناتج`),
    'EG.ELC.ACCS.ZS':    (v, n) => n ? T(`${n} people without electricity`, `${n} شخص بلا كهرباء`) : T(`electricity access at ${v}`, `وصول إلى الكهرباء بنسبة ${v}`),
    'SH.DYN.MORT':       v => T(`under-5 mortality of ${v}`, `وفيات أطفال دون الخامسة تبلغ ${v}`),
    'SH.STA.MMRT':       v => T(`maternal mortality of ${v}`, `وفيات أمهات تبلغ ${v}`),
    'SL.UEM.TOTL.ZS':    v => T(`unemployment at ${v}`, `بطالة بنسبة ${v}`),
    'GOV_WGI_PV.SC':     v => T(`a political-stability score of ${v}/100`, `درجة استقرار سياسي ${v} من 100`),
    'GOV_WGI_GE.SC':     v => T(`a government-effectiveness score of ${v}/100`, `درجة فعالية حكومية ${v} من 100`),
    'GOV_WGI_RL.SC':     v => T(`a rule-of-law score of ${v}/100`, `درجة سيادة القانون ${v} من 100`),
    'SE.SEC.ENRR':       v => T(`secondary enrolment of ${v}`, `التحاق بالتعليم الثانوي بنسبة ${v}`),
    'SE.ADT.LITR.ZS':    v => T(`adult literacy of ${v}`, `معرفة الكبار بالقراءة والكتابة بنسبة ${v}`),
    'NY.GDP.MKTP.KD.ZG': v => T(`GDP growth of ${v}`, `نمو اقتصادي بنسبة ${v}`),
    'SL.TLF.CACT.FE.ZS': v => T(`only ${v} of women in the labour force`, `${v} فقط من النساء في القوى العاملة`),
    'SL.AGR.EMPL.ZS':    v => T(`${v} of jobs in farming`, `${v} من الوظائف في الزراعة`),
    'FS.AST.PRVT.GD.ZS': v => T(`private-sector credit of only ${v} of GDP`, `ائتمان للقطاع الخاص لا يتجاوز ${v} من الناتج`),
    'FR.INR.LEND':       v => T(`lending rates of ${v}`, `أسعار فائدة على القروض تبلغ ${v}`),
    'IC.FRM.BKWC.ZS':    v => T(`only ${v} of firms using bank credit`, `${v} فقط من الشركات تستخدم الائتمان المصرفي`),
    'IC.ELC.OUTG.ZS':    v => T(`${v} of firms hit by power outages`, `${v} من الشركات تعاني انقطاع الكهرباء`),
    'LP.LPI.OVRL.XQ':    v => T(`a logistics score of ${v}/5`, `درجة أداء لوجستي ${v} من 5`),
  };
  const WHY = {
    'SH.DYN.MORT': { d:['SH.MED.PHYS.ZS','SH.IMM.MEAS','SH.H2O.BASW.ZS','SH.STA.STNT.ZS','SH.STA.BASS.ZS','SH.XPD.CHEX.GD.ZS'],
      so:['Most of these deaths come from preventable causes (pneumonia, diarrhoea, malaria, malnutrition), so primary care, immunisation and clean water would save the most lives.',
          'معظم هذه الوفيات ناجم عن أسباب يمكن الوقاية منها (الالتهاب الرئوي والإسهال والملاريا وسوء التغذية)، لذا فإن الرعاية الأولية والتحصين والمياه النظيفة هي الأكثر إنقاذاً للأرواح.'] },
    'SH.STA.MMRT': { d:['SH.MED.PHYS.ZS','SH.XPD.CHEX.GD.ZS','SI.POV.DDAY'],
      so:['Most maternal deaths happen around childbirth; without skilled birth attendants and emergency obstetric care within reach, treatable complications become fatal.',
          'تقع معظم وفيات الأمهات حول الولادة؛ ومن دون قابلات مؤهلات ورعاية توليد طارئة في المتناول، تتحول مضاعفات قابلة للعلاج إلى وفيات.'] },
    'SP.DYN.LE00.IN': { d:['SH.DYN.MORT','SH.STA.MMRT','SH.H2O.BASW.ZS'],
      so:['Short lives here reflect deaths in childhood and childbirth more than old-age disease; the same gaps in basic care and clean water drive both.',
          'يعكس قِصر الأعمار هنا وفيات الطفولة والولادة أكثر من أمراض الشيخوخة، وتقف وراءهما الفجوات نفسها في الرعاية الأساسية والمياه النظيفة.'] },
    'SH.IMM.MEAS': { d:['SH.MED.PHYS.ZS','SH.XPD.CHEX.GD.ZS','EG.ELC.ACCS.ZS'],
      so:['Low coverage leaves children exposed to outbreaks; it usually means remote communities are missed by outreach and vaccines are not kept cold reliably.',
          'تترك التغطية المنخفضة الأطفال عرضة لتفشي الأمراض، وتعني عادةً أن المجتمعات النائية لا تصلها الخدمات وأن اللقاحات لا تُحفظ مبرّدة بشكل موثوق.'] },
    'SH.XPD.CHEX.GD.ZS': { d:['GC.TAX.TOTL.GD.ZS'],
      so:['With little public money for health, families pay out of pocket; the poorest delay or skip care, and one illness can push a household into poverty.',
          'مع ضآلة التمويل العام للصحة تدفع الأسر التكاليف من جيبها، فيؤجل الأفقر العلاج أو يتخلّون عنه، وقد يدفع مرض واحد أسرة إلى الفقر.'] },
    'SH.MED.PHYS.ZS': { d:['SH.XPD.CHEX.GD.ZS'],
      so:['With so few doctors, care is concentrated in cities; rural communities depend on under-staffed clinics and community health workers.',
          'مع قلة الأطباء تتركز الرعاية في المدن، وتعتمد المجتمعات الريفية على عيادات تنقصها الكوادر وعلى العاملين الصحيين المجتمعيين.'] },
    'SE.ADT.LITR.ZS': { d:['SE.PRM.CMPT.ZS','SI.POV.DDAY'],
      so:['Adults who cannot read are shut out of better jobs and of written health, farming and financial information, which slows every other programme.',
          'يُحرم الكبار غير الملمّين بالقراءة من الوظائف الأفضل ومن المعلومات المكتوبة عن الصحة والزراعة والمال، مما يبطئ كل البرامج الأخرى.'] },
    'SE.PRM.CMPT.ZS': { d:['SE.PRM.ENRL.TC.ZS','SE.XPD.TOTL.GD.ZS','SI.POV.DDAY','SH.STA.STNT.ZS'],
      so:['Many children leave school before gaining basic skills; costs, distance to school and the need for children to work are the usual reasons.',
          'يغادر كثير من الأطفال المدرسة قبل اكتساب المهارات الأساسية، والأسباب المعتادة هي التكاليف وبُعد المدرسة وحاجة الأسر إلى عمل أطفالها.'] },
    'SE.SEC.ENRR': { d:['SE.PRM.CMPT.ZS','SI.POV.DDAY','SE.XPD.TOTL.GD.ZS'],
      so:['Too few secondary places, plus pressure to work or marry early, end schooling for many teenagers, girls most of all.',
          'قلة مقاعد التعليم الثانوي وضغوط العمل أو الزواج المبكر تُنهي تعليم كثير من المراهقين، والفتيات أكثر من غيرهن.'] },
    'SE.PRM.ENRL.TC.ZS': { d:['SE.XPD.TOTL.GD.ZS'],
      so:['Overcrowded classes leave little teaching time per child, so learning stays low even where enrolment looks good.',
          'تقلّص الفصول المكتظة وقت التعليم لكل طفل، فيبقى التعلّم ضعيفاً حتى حيث تبدو معدلات الالتحاق جيدة.'] },
    'SE.XPD.TOTL.GD.ZS': { d:['GC.TAX.TOTL.GD.ZS'],
      so:['Under-funding shows up as teacher shortages, missing materials and schools without water or power.',
          'يظهر نقص التمويل في نقص المعلمين والمواد التعليمية ومدارس بلا مياه أو كهرباء.'] },
    'SN.ITK.DEFC.ZS': { d:['AG.YLD.CREL.KG','SI.POV.DDAY','FP.CPI.TOTL.ZG'],
      so:['Hunger here is about both production and purchasing power: households can neither grow nor buy enough food.',
          'يرتبط الجوع هنا بالإنتاج والقدرة الشرائية معاً، فالأسر لا تستطيع زراعة ما يكفي من الغذاء ولا شراءه.'] },
    'SH.STA.STNT.ZS': { d:['SN.ITK.DEFC.ZS','SH.H2O.BASW.ZS','SH.STA.BASS.ZS'],
      so:['Stunting is largely irreversible after age two and lowers lifelong learning and earnings; it comes from poor diets combined with repeated infections from unsafe water and sanitation.',
          'لا يمكن تدارك التقزّم غالباً بعد سن الثانية، وهو يضعف التعلّم والدخل مدى الحياة؛ وينتج عن سوء التغذية مع تكرار العدوى بسبب المياه والصرف الصحي غير الآمنين.'] },
    'AG.YLD.CREL.KG': { d:['NV.AGR.TOTL.ZS','SN.ITK.DEFC.ZS','EG.ELC.ACCS.ZS'],
      so:['Low yields point to little irrigation, improved seed or mechanisation; with so many livelihoods in farming, productivity is the main lever for both food and income.',
          'تشير الإنتاجية المنخفضة إلى ضعف الري والبذور المحسّنة والميكنة؛ ومع اعتماد كثير من سبل العيش على الزراعة، تبقى الإنتاجية الرافعة الأهم للغذاء والدخل معاً.'] },
    'SH.H2O.BASW.ZS': { d:['EG.ELC.ACCS.ZS','SI.POV.DDAY','SH.DYN.MORT'],
      so:['Women and girls spend hours fetching water instead of working or studying, and unsafe sources spread diarrhoeal disease, a leading killer of young children.',
          'تقضي النساء والفتيات ساعات في جلب المياه بدلاً من العمل أو الدراسة، والمصادر غير الآمنة تنشر أمراض الإسهال، وهي من أبرز أسباب وفاة الأطفال الصغار.'] },
    'SH.H2O.SMDW.ZS': { d:['SH.H2O.BASW.ZS'],
      so:['Even where a water point exists, the water is often contaminated or not available when it is needed.',
          'حتى حيث توجد نقطة مياه، تكون المياه في الغالب ملوثة أو غير متاحة عند الحاجة.'] },
    'SH.STA.BASS.ZS': { d:['SH.STA.ODFC.ZS','SH.STA.STNT.ZS'],
      so:['Poor sanitation spreads diarrhoea and parasites, which feed child stunting, and keeps girls out of school where there are no toilets.',
          'يؤدي ضعف الصرف الصحي إلى انتشار الإسهال والطفيليات مما يغذّي تقزّم الأطفال، ويُبعد الفتيات عن المدارس التي تفتقر إلى دورات المياه.'] },
    'SH.STA.SMSS.ZS': { d:['SH.STA.BASS.ZS'],
      so:['Most waste is not safely treated, so it ends up contaminating water sources, especially in fast-growing towns.',
          'لا تُعالج معظم المخلفات بأمان، فينتهي بها الأمر إلى تلويث مصادر المياه، لا سيما في المدن سريعة النمو.'] },
    'SH.STA.ODFC.ZS': { d:['SH.STA.BASS.ZS'],
      so:['Open defecation contaminates water and soil for whole communities, not just the households involved.',
          'يلوّث التغوط في العراء المياه والتربة للمجتمع بأكمله، لا للأسر المعنية فحسب.'] },
    'EG.ELC.ACCS.ZS': { d:['SI.POV.DDAY','SH.IMM.MEAS'],
      so:['Without power, clinics cannot keep vaccines cold, schools cannot run after dark and farms and firms cannot process or add value; this gap holds back every other sector.',
          'من دون كهرباء لا تستطيع العيادات حفظ اللقاحات مبرّدة، ولا المدارس العمل بعد الغروب، ولا المزارع والشركات تصنيع منتجاتها؛ فهذه الفجوة تعيق كل القطاعات الأخرى.'] },
    'EG.CFT.ACCS.ZS': { d:['EG.ELC.ACCS.ZS'],
      so:['Most households cook on wood or charcoal; the smoke is a leading cause of death for women and young children, and the demand for fuel drives deforestation.',
          'تطهو معظم الأسر بالحطب أو الفحم، ودخانهما من أبرز أسباب وفاة النساء والأطفال الصغار، كما يدفع الطلب على الوقود إلى إزالة الغابات.'] },
    'IT.NET.USER.ZS': { d:['EG.ELC.ACCS.ZS'],
      so:['Low connectivity shuts people out of mobile money, digital public services, online learning and market prices.',
          'يحرم ضعف الاتصال الناس من الأموال عبر الهاتف والخدمات الحكومية الرقمية والتعلّم عن بُعد ومعرفة أسعار السوق.'] },
    'NY.GDP.MKTP.KD.ZG': { d:['FP.CPI.TOTL.ZG','GOV_WGI_PV.SC'],
      so:['Weak growth means incomes per person barely rise as the population grows, leaving little room to fund services.',
          'يعني النمو الضعيف أن دخل الفرد بالكاد يرتفع مع نمو السكان، مما يترك هامشاً ضئيلاً لتمويل الخدمات.'] },
    'FP.CPI.TOTL.ZG': { d:[],
      so:['High inflation erodes household purchasing power and the real value of aid budgets, so cash support needs regular adjustment.',
          'يُضعف التضخم المرتفع القدرة الشرائية للأسر والقيمة الحقيقية لميزانيات المساعدات، لذا يحتاج الدعم النقدي إلى تعديل منتظم.'] },
    'GC.TAX.TOTL.GD.ZS': { d:['GOV_WGI_GE.SC'],
      so:['The state raises too little revenue to fund health, schools and infrastructure on its own, so services depend on external financing.',
          'لا تجمع الدولة إيرادات كافية لتمويل الصحة والمدارس والبنية التحتية بمفردها، فتبقى الخدمات معتمدة على التمويل الخارجي.'] },
    'SL.UEM.TOTL.ZS': { d:['NY.GDP.MKTP.KD.ZG'],
      so:['Joblessness, especially among young people, fuels migration and instability.',
          'تغذّي البطالة، ولا سيما بين الشباب، الهجرة وعدم الاستقرار.'] },
    'SI.POV.DDAY': { d:['SL.UEM.TOTL.ZS','FP.CPI.TOTL.ZG'],
      so:['These households cannot absorb shocks such as a failed harvest or a price spike; social protection and jobs come first.',
          'لا تستطيع هذه الأسر تحمّل الصدمات مثل فشل المحصول أو ارتفاع الأسعار، لذا تأتي الحماية الاجتماعية وفرص العمل أولاً.'] },
    'GOV_WGI_PV.SC': { d:['GOV_WGI_GE.SC'],
      so:['Instability raises the risk of programme disruption; delivery needs flexible, conflict-sensitive design and trusted local partners.',
          'يرفع عدم الاستقرار خطر تعطّل البرامج، لذا يحتاج التنفيذ إلى تصميم مرن يراعي النزاع وإلى شركاء محليين موثوقين.'] },
    'GOV_WGI_VA.SC': { d:[],
      so:['Limited civic space makes community feedback and independent monitoring more important for every programme.',
          'يجعل ضيق الفضاء المدني ملاحظات المجتمعات والرقابة المستقلة أكثر أهمية لكل برنامج.'] },
    'GOV_WGI_GE.SC': { d:['GC.TAX.TOTL.GD.ZS'],
      so:['Weak public delivery capacity means funding should come with technical assistance and close monitoring.',
          'يعني ضعف قدرة الجهات العامة على التنفيذ أن التمويل يجب أن يقترن بالمساعدة الفنية والمتابعة الدقيقة.'] },
    'GOV_WGI_RL.SC': { d:[],
      so:['Weak contract enforcement and land rights deter private investment and complicate partnerships.',
          'يُضعف تراجع إنفاذ العقود وحقوق الأراضي الاستثمار الخاص ويعقّد الشراكات.'] },
    'GOV_WGI_CC.SC': { d:[],
      so:['High corruption risk calls for ring-fenced funds, third-party monitoring and payment on results.',
          'يستدعي ارتفاع خطر الفساد تمويلاً مخصصاً ورقابة من طرف ثالث ودفعات مرتبطة بالنتائج.'] },
    // Economic empowerment
    'SL.UEM.1524.ZS': { d:['SE.SEC.ENRR','NY.GDP.MKTP.KD.ZG'],
      so:['Young people are the fastest-growing part of the labour force; without work or skills they are the group most likely to migrate or be drawn into instability.',
          'الشباب هم الشريحة الأسرع نمواً في القوى العاملة؛ ومن دون عمل أو مهارات يكونون الأكثر عرضة للهجرة أو الانجرار إلى عدم الاستقرار.'] },
    'SL.TLF.CACT.FE.ZS': { d:['SE.ADT.LITR.ZS','FX.OWN.TOTL.ZS'],
      so:['Getting more women into paid work raises household income and increases spending on children’s health and schooling.',
          'إن إدخال مزيد من النساء إلى العمل المأجور يرفع دخل الأسرة ويزيد الإنفاق على صحة الأطفال وتعليمهم.'] },
    'SL.EMP.VULN.ZS': { d:['SI.POV.DDAY','SL.AGR.EMPL.ZS'],
      so:['Most people earn a living without a contract or social protection, so one illness or bad harvest can push a family into poverty.',
          'يكسب معظم الناس رزقهم دون عقد أو حماية اجتماعية، لذا قد يدفع مرض واحد أو موسم حصاد سيئ الأسرة إلى الفقر.'] },
    'FX.OWN.TOTL.ZS': { d:['SL.TLF.CACT.FE.ZS','SI.POV.DDAY'],
      so:['Without an account, people cannot save safely, borrow, or receive wages and transfers digitally — a basic building block for cash and livelihoods programmes.',
          'من دون حساب لا يستطيع الناس الادخار بأمان أو الاقتراض أو تلقي الأجور والتحويلات رقمياً، وهو أساس لبرامج الدعم النقدي وسبل العيش.'] },
    'SI.POV.GINI': { d:['SI.POV.DDAY'],
      so:['The gains from growth are shared unevenly, so programmes need explicit targeting to reach the poorest households.',
          'تتوزع ثمار النمو بشكل غير متكافئ، لذا تحتاج البرامج إلى استهداف صريح للوصول إلى الأسر الأفقر.'] },
    // Business enablement
    'FS.AST.PRVT.GD.ZS': { d:['FR.INR.LEND','IC.FRM.BKWC.ZS'],
      so:['Businesses have little access to bank finance, so they cannot invest, grow or hire; small firms are hit hardest.',
          'تحظى الأعمال بقدر ضئيل من التمويل المصرفي، فلا تستطيع الاستثمار أو النمو أو التوظيف، والشركات الصغيرة هي الأكثر تضرراً.'] },
    'BX.KLT.DINV.WD.GD.ZS': { d:['LP.LPI.OVRL.XQ','IC.ELC.OUTG.ZS','GOV_WGI_RL.SC'],
      so:['Little foreign investment arrives, which limits new jobs, technology and access to export markets.',
          'يصل قدر ضئيل من الاستثمار الأجنبي، مما يحدّ من فرص العمل الجديدة والتقنية والوصول إلى أسواق التصدير.'] },
    'FR.INR.LEND': { d:['FP.CPI.TOTL.ZG'],
      so:['Credit is expensive, so only short-term, high-margin activity gets financed and productive investment is held back.',
          'الائتمان مكلف، فلا يُموَّل إلا النشاط قصير الأجل مرتفع الهامش، ويتعطل الاستثمار المنتج.'] },
    'IC.FRM.BKWC.ZS': { d:['FS.AST.PRVT.GD.ZS','FR.INR.LEND'],
      so:['Most firms rely on their own cash to operate, which caps how fast they can grow.',
          'تعتمد معظم الشركات على أموالها الخاصة لتسيير أعمالها، مما يحدّ من سرعة نموها.'] },
    'IC.ELC.OUTG.ZS': { d:['EG.ELC.ACCS.ZS'],
      so:['Frequent outages force firms to run generators or stop production, raising costs and deterring investment.',
          'تجبر الانقطاعات المتكررة الشركات على تشغيل المولدات أو وقف الإنتاج، مما يرفع التكاليف ويُنفّر الاستثمار.'] },
    'LP.LPI.OVRL.XQ': { d:[],
      so:['Slow, costly customs and transport raise the price of every import and export and keep firms out of regional supply chains.',
          'تؤدي الإجراءات الجمركية والنقل البطيئة والمكلفة إلى رفع سعر كل واردات وصادرات، وتُبقي الشركات خارج سلاسل الإمداد الإقليمية.'] },
    // Trade
    'TM.TAX.MRCH.WM.AR.ZS': { d:['LP.LPI.OVRL.XQ'],
      so:['High tariffs raise the cost of imported inputs and everyday goods and limit integration into regional markets.',
          'ترفع التعريفات المرتفعة كلفة المدخلات المستوردة والسلع اليومية وتحدّ من الاندماج في الأسواق الإقليمية.'] },
    'BN.CAB.XOKA.GD.ZS': { d:['FP.CPI.TOTL.ZG'],
      so:['The country spends far more abroad than it earns, which strains foreign-exchange reserves and the currency and makes imports such as food and fuel dearer.',
          'ينفق البلد في الخارج أكثر بكثير مما يكسب، مما يضغط على احتياطيات النقد الأجنبي والعملة ويرفع كلفة الواردات مثل الغذاء والوقود.'] },
  };
  const andList = xs => xs.length < 2 ? xs.join('') : xs.slice(0, -1).join(T(', ', '، ')) + T(' and ', ' و') + xs[xs.length - 1];
  // one insight: heading (indicator + gap) and body (linked factors in the data + what it means)
  function insight(id, mapNote) {
    const w = WHY[id]; if (!w || lvl(id) == null) return null;
    const drivers = w.d.filter(d => d !== id && DP[d] && (off(d, 1) || (d === 'NV.AGR.TOTL.ZS' && atLeast(d, 15)))).slice(0, 3)
      .map(d => DP[d](val(d), people(d)));
    const g = gap(id, true);
    const body = (drivers.length ? T('Linked factors: ', 'عوامل مرتبطة: ') + andList(drivers) + T('. ', '. ') : '') + T(w.so[0], w.so[1])
      + (mapNote ? T(' The next slide shows which regions are worst affected.', ' وتُظهر الشريحة التالية المناطق الأكثر تضرراً.') : '');
    return { id, L: lvl(id), head: lbl(id) + (g ? '  ·  ' + g : ''), body };
  }
  // ODA need index — explained wherever the score is shown
  const NEED_NOTE = T('* ODA need index: a 0–100 score combining under-5 and maternal mortality, undernourishment and the share of people without basic water, sanitation and electricity, each scaled across the countries ODA tracks. Higher means greater need.',
    '* مؤشر الاحتياج لدى المكتب: درجة من 0 إلى 100 تجمع وفيات الأطفال دون الخامسة ووفيات الأمهات ونقص التغذية ونسبة السكان المحرومين من مياه الشرب الأساسية والصرف الصحي والكهرباء، مع قياس كل منها عبر الدول التي يتابعها المكتب. الأعلى يعني احتياجاً أكبر.');

  // ── sectors ── acts: [indicator that triggers it, worst level it applies to, English, Arabic] (null = always)
  //               inv:  development-investment angles, only where the data makes them relevant
  const SECTORS = [
    { key:'wash', en:'Water', ar:'المياه', short:['Water','المياه'], stats:['SH.H2O.BASW.ZS','SH.H2O.SMDW.ZS','SH.STA.BASS.ZS','SH.STA.SMSS.ZS'], bars:['SH.H2O.BASW.ZS','SH.H2O.SMDW.ZS','SH.STA.BASS.ZS','SH.STA.SMSS.ZS','SH.STA.ODFC.ZS'],
      acts:[ ['SH.H2O.BASW.ZS',1,'Extend basic water points and piped supply to unserved communities.','توصيل مياه الشرب الأساسية والشبكات إلى المجتمعات غير المخدومة.'],
             ['SH.STA.BASS.ZS',1,'Fund household and school sanitation; end open defecation.','تمويل الصرف الصحي للمنازل والمدارس وإنهاء التغوط في العراء.'],
             ['SH.H2O.SMDW.ZS',2,'Upgrade water treatment so supply is safely managed.','تحسين معالجة المياه لتصبح مُدارة بأمان.'],
             [null,3,'Climate-proof water sources and utilities.','حماية مصادر المياه ومرافقها من آثار المناخ.'] ],
      inv:[ [() => off('SH.H2O.BASW.ZS', 1) || off('SH.H2O.SMDW.ZS', 1), 'Results-based concessions or PPPs for water utilities, desalination or treatment plants and water-kiosk operators, using blended finance.',
             'امتيازات قائمة على النتائج أو شراكات بين القطاعين لمرافق المياه ومحطات التحلية أو المعالجة ومشغّلي أكشاك المياه، بتمويل مختلط.'] ] },
    { key:'energy', en:'Energy', ar:'الطاقة', short:['Energy','الطاقة'], stats:['EG.ELC.ACCS.ZS','EG.CFT.ACCS.ZS','EG.FEC.RNEW.ZS'], bars:['EG.ELC.ACCS.ZS','EG.CFT.ACCS.ZS'],
      acts:[ ['EG.ELC.ACCS.ZS',1,'Off-grid and mini-grid solar for rural households, clinics and schools.','الطاقة الشمسية خارج الشبكة والشبكات المصغّرة للأرياف والعيادات والمدارس.'],
             ['EG.CFT.ACCS.ZS',1,'Clean-cooking programmes to cut household air pollution.','برامج الطهي النظيف للحد من تلوث الهواء المنزلي.'],
             [null,3,'Improve grid reliability and cut transmission losses.','تحسين موثوقية الشبكة وخفض فواقد النقل.'] ],
      inv:[ [() => off('EG.ELC.ACCS.ZS', 1), 'Blended finance for solar power producers, mini-grid concessions and pay-as-you-go solar companies.',
             'تمويل مختلط لمنتجي الطاقة الشمسية وامتيازات الشبكات المصغّرة وشركات الطاقة الشمسية بنظام الدفع حسب الاستخدام.'] ] },
    { key:'food', en:'Agriculture & Food Security', ar:'الزراعة والأمن الغذائي', short:['Agriculture & food security','الزراعة والأمن الغذائي'], stats:['SN.ITK.DEFC.ZS','SH.STA.STNT.ZS','AG.YLD.CREL.KG','NV.AGR.TOTL.ZS'], bars:['SN.ITK.DEFC.ZS','SH.STA.STNT.ZS','AG.YLD.CREL.KG','SN.ITK.MSFI.ZS'],
      acts:[ ['SN.ITK.DEFC.ZS',1,'Scale food assistance and social safety nets for vulnerable households.','توسيع المساعدات الغذائية وشبكات الأمان الاجتماعي للأسر الهشة.'],
             ['SH.STA.STNT.ZS',1,'Fund early-childhood and maternal nutrition programmes.','تمويل برامج تغذية الأمهات والطفولة المبكرة.'],
             ['AG.YLD.CREL.KG',1,'Raise smallholder yields: irrigation, improved seed, extension services.','رفع إنتاجية صغار المزارعين: الري والبذور المحسّنة والإرشاد الزراعي.'],
             [null,3,'Build climate resilience into food systems and storage.','تعزيز قدرة النظم الغذائية والتخزين على الصمود أمام المناخ.'] ],
      inv:[ [() => off('AG.YLD.CREL.KG', 2) || atLeast('NV.AGR.TOTL.ZS', 15), 'Offtake agreements with buyers, including UAE food importers, that guarantee smallholders a market, backed by input finance and aggregation hubs.',
             'اتفاقيات شراء مسبق للمحاصيل مع مشترين، منهم مستوردو الغذاء في الإمارات، تضمن لصغار المزارعين سوقاً لإنتاجهم، مدعومة بتمويل المدخلات ومراكز التجميع.'],
            [() => off('SN.ITK.DEFC.ZS', 1) || off('AG.YLD.CREL.KG', 1), 'Invest in storage, cold chain and agro-processing to cut post-harvest losses and keep more value in the country.',
             'الاستثمار في التخزين وسلاسل التبريد والتصنيع الزراعي لخفض فاقد ما بعد الحصاد والإبقاء على قيمة أكبر داخل البلد.'] ] },
    { key:'education', en:'Education', ar:'التعليم', short:['Education','التعليم'], stats:['SE.ADT.LITR.ZS','SE.PRM.CMPT.ZS','SE.SEC.ENRR','SE.XPD.TOTL.GD.ZS'], bars:['SE.ADT.LITR.ZS','SE.PRM.CMPT.ZS','SE.SEC.ENRR','SE.PRM.ENRL.TC.ZS','SE.XPD.TOTL.GD.ZS'],
      acts:[ ['SE.PRM.CMPT.ZS',1,'Keep children in primary school to completion (school feeding, fee support).','إبقاء الأطفال في المدرسة حتى إتمام المرحلة الابتدائية (التغذية المدرسية ودعم الرسوم).'],
             ['SE.SEC.ENRR',1,'Expand secondary places and support girls’ transition to secondary school.','زيادة مقاعد التعليم الثانوي ودعم انتقال الفتيات إليه.'],
             ['SE.ADT.LITR.ZS',1,'Fund adult and youth literacy programmes.','تمويل برامج محو الأمية للشباب والكبار.'],
             ['SE.PRM.ENRL.TC.ZS',1,'Recruit and train teachers to bring class sizes down.','توظيف المعلمين وتدريبهم لخفض أعداد الطلاب في الفصول.'],
             [null,3,'Invest in teacher quality and learning assessment.','الاستثمار في جودة المعلمين وتقييم التعلّم.'] ],
      inv:[ [() => off('SE.SEC.ENRR', 1) && off('SL.UEM.TOTL.ZS', 2), 'Technical and vocational training co-designed and co-funded with employers in growth sectors, so skills lead to jobs.',
             'تدريب تقني ومهني يُصمَّم ويُموَّل بالشراكة مع أصحاب العمل في القطاعات الواعدة، لتقود المهارات إلى وظائف.'] ] },
    { key:'health', en:'Health', ar:'الصحة', short:['Health','الصحة'], stats:['SH.DYN.MORT','SH.STA.MMRT','SP.DYN.LE00.IN','SH.XPD.CHEX.GD.ZS'], bars:['SH.DYN.MORT','SH.STA.MMRT','SP.DYN.LE00.IN','SH.IMM.MEAS','SH.XPD.CHEX.GD.ZS','SH.MED.PHYS.ZS'],
      acts:[ ['SH.DYN.MORT',1,'Scale up community health workers and integrated child-health services.','توسيع نطاق العاملين الصحيين المجتمعيين وخدمات صحة الطفل المتكاملة.'],
             ['SH.STA.MMRT',1,'Expand skilled birth attendance and emergency obstetric care.','توسيع الولادة بإشراف كوادر مؤهلة ورعاية التوليد الطارئة.'],
             ['SH.IMM.MEAS',2,'Close immunisation gaps through outreach and cold-chain investment.','سد فجوات التحصين عبر الوصول الميداني والاستثمار في سلسلة التبريد.'],
             ['SH.XPD.CHEX.GD.ZS',2,'Support higher, more predictable public health financing.','دعم تمويل صحي عام أعلى وأكثر استقراراً.'],
             [null,3,'Strengthen primary-care quality and reach in underserved areas.','تعزيز جودة الرعاية الأولية ووصولها إلى المناطق المحرومة.'] ],
      inv:[ [() => off('SH.MED.PHYS.ZS', 1) || off('SH.DYN.MORT', 0), 'Co-invest with private operators in diagnostic centres and district hospitals (PPP), and in local production of essential medicines and medical supplies.',
             'الاستثمار المشترك مع مشغّلين من القطاع الخاص في مراكز التشخيص والمستشفيات الإقليمية (شراكة بين القطاعين)، وفي التصنيع المحلي للأدوية والمستلزمات الطبية الأساسية.'] ] },
    { key:'econ', en:'Economic Empowerment', ar:'التمكين الاقتصادي', short:['Economic empowerment','التمكين الاقتصادي'],
      stats:['SI.POV.DDAY','SL.UEM.TOTL.ZS','SL.TLF.CACT.FE.ZS','FX.OWN.TOTL.ZS'], bars:['SI.POV.DDAY','SL.UEM.TOTL.ZS','SL.UEM.1524.ZS','SL.TLF.CACT.FE.ZS','SL.EMP.VULN.ZS','FX.OWN.TOTL.ZS','SI.POV.GINI'],
      acts:[ ['SI.POV.DDAY',1,'Expand social protection and cash transfers for households in extreme poverty.','توسيع الحماية الاجتماعية والتحويلات النقدية للأسر في الفقر المدقع.'],
             ['SL.UEM.1524.ZS',1,'Youth employment: vocational skills, apprenticeships and job-matching services.','تشغيل الشباب: المهارات المهنية والتدريب المهني وخدمات المواءمة مع الوظائف.'],
             ['SL.TLF.CACT.FE.ZS',1,'Women’s economic empowerment: childcare, skills and finance for women entrepreneurs.','التمكين الاقتصادي للمرأة: رعاية الأطفال والمهارات والتمويل لرائدات الأعمال.'],
             ['FX.OWN.TOTL.ZS',1,'Widen financial inclusion through mobile money and agent banking.','توسيع الشمول المالي عبر الأموال عبر الهاتف والخدمات المصرفية عبر الوكلاء.'],
             ['SL.EMP.VULN.ZS',1,'Help informal workers formalise: registration, savings and social insurance.','مساعدة العاملين في القطاع غير الرسمي على الانتقال إلى الاقتصاد الرسمي: التسجيل والادخار والتأمين الاجتماعي.'],
             [null,3,'Link households to savings groups, skills and decent jobs.','ربط الأسر بمجموعات الادخار والمهارات وفرص العمل اللائق.'] ],
      inv:[ [() => off('FX.OWN.TOTL.ZS', 1) || off('SL.TLF.CACT.FE.ZS', 1), 'Invest in microfinance institutions and digital lenders that serve women and low-income households.',
             'الاستثمار في مؤسسات التمويل الأصغر والمقرضين الرقميين الذين يخدمون النساء والأسر منخفضة الدخل.'],
            [() => off('SL.UEM.1524.ZS', 1) || off('SL.UEM.TOTL.ZS', 1), 'Co-invest with employers in skills-to-jobs programmes in labour-intensive sectors such as agro-processing, construction and tourism.',
             'الاستثمار المشترك مع أصحاب العمل في برامج تربط المهارات بالوظائف في القطاعات كثيفة العمالة مثل التصنيع الزراعي والبناء والسياحة.'] ] },
    { key:'business', en:'Business Enablement', ar:'تمكين الأعمال', short:['Business enablement','تمكين الأعمال'],
      stats:['FS.AST.PRVT.GD.ZS','BX.KLT.DINV.WD.GD.ZS','FR.INR.LEND','LP.LPI.OVRL.XQ'], bars:['FS.AST.PRVT.GD.ZS','BX.KLT.DINV.WD.GD.ZS','FR.INR.LEND','IC.FRM.BKWC.ZS','IC.ELC.OUTG.ZS','LP.LPI.OVRL.XQ','IC.BUS.NDNS.ZS'],
      acts:[ ['FS.AST.PRVT.GD.ZS',1,'Partial credit guarantees and credit bureaus to widen bank lending to small businesses.','ضمانات ائتمان جزئية ومكاتب استعلام ائتماني لتوسيع الإقراض المصرفي للأعمال الصغيرة.'],
             ['FR.INR.LEND',1,'Support financial-sector reforms that bring down the cost of credit.','دعم إصلاحات القطاع المالي التي تخفض كلفة الائتمان.'],
             ['IC.ELC.OUTG.ZS',1,'Reliable power for industrial zones and small-business clusters.','كهرباء موثوقة للمناطق الصناعية وتجمعات الأعمال الصغيرة.'],
             ['LP.LPI.OVRL.XQ',1,'Customs modernisation and a single window for trade paperwork.','تحديث الجمارك ونافذة موحدة لإجراءات التجارة.'],
             ['BX.KLT.DINV.WD.GD.ZS',1,'Investment-climate reform: a one-stop shop for investors and clear licensing rules.','إصلاح مناخ الاستثمار: مركز خدمة شامل للمستثمرين وقواعد ترخيص واضحة.'],
             [null,3,'Simplify business registration, licensing and tax filing.','تبسيط تسجيل الأعمال والترخيص والإقرارات الضريبية.'] ],
      inv:[ [() => off('FS.AST.PRVT.GD.ZS', 1) || off('IC.FRM.BKWC.ZS', 1) || off('FR.INR.LEND', 1), 'Credit lines and partial guarantees through local banks to unlock lending to small and medium-sized businesses.',
             'خطوط ائتمان وضمانات جزئية عبر البنوك المحلية لفتح الإقراض أمام المنشآت الصغيرة والمتوسطة.'],
            [() => off('BX.KLT.DINV.WD.GD.ZS', 2) || off('LP.LPI.OVRL.XQ', 2), 'Co-invest with private developers in special economic zones, industrial parks and logistics hubs.',
             'الاستثمار المشترك مع المطورين من القطاع الخاص في المناطق الاقتصادية الخاصة والمجمعات الصناعية والمراكز اللوجستية.'] ] },
    { key:'trade', en:'Trade', ar:'التجارة', short:['Trade','التجارة'],
      stats:['NE.EXP.GNFS.ZS','BN.CAB.XOKA.GD.ZS','TM.TAX.MRCH.WM.AR.ZS','TX.VAL.MANF.ZS.UN'], bars:['BN.CAB.XOKA.GD.ZS','TM.TAX.MRCH.WM.AR.ZS'],
      acts:[ ['TM.TAX.MRCH.WM.AR.ZS',1,'Support tariff reform and regional trade agreements that open neighbouring markets.','دعم إصلاح التعريفات واتفاقيات التجارة الإقليمية التي تفتح أسواق الجوار.'],
             ['BN.CAB.XOKA.GD.ZS',1,'Export promotion and diversification to narrow the trade gap.','تشجيع الصادرات وتنويعها لتضييق الفجوة التجارية.'],
             [null,3,'Help exporters meet international standards and certification to reach new markets.','مساعدة المصدّرين على استيفاء المعايير والشهادات الدولية للوصول إلى أسواق جديدة.'] ],
      inv:[ [() => off('BN.CAB.XOKA.GD.ZS', 2) || (R('TX.VAL.MANF.ZS.UN') && !R('TX.VAL.MANF.ZS.UN').stale && R('TX.VAL.MANF.ZS.UN').v < 30), 'Co-invest in export-oriented processing (agro-processing, light manufacturing) and in port, storage and logistics capacity, including with UAE trade and logistics partners.',
             'الاستثمار المشترك في التصنيع الموجّه للتصدير (التصنيع الزراعي والصناعات الخفيفة) وفي قدرات الموانئ والتخزين والخدمات اللوجستية، بما في ذلك مع شركاء التجارة والخدمات اللوجستية في الإمارات.'] ] },
  ];
  // "where the need is" maps: the DHS survey indicator ↔ the national indicator it measures
  const SUB_LINK = { CM_ECMR_C_U5M:'SH.DYN.MORT', CH_VACC_C_BAS:'SH.IMM.MEAS', ED_LITR_W_LIT:'SE.ADT.LITR.ZS', CN_NUTS_C_HA2:'SH.STA.STNT.ZS', WS_SRCE_H_IMP:'SH.H2O.BASW.ZS', WS_TLET_H_IMP:'SH.STA.BASS.ZS' };
  const SUBN = opts.subnational || {};
  // sector status = worst current level among its benchmarked indicators
  SECTORS.forEach(s => {
    s.ids = [...new Set(s.stats.concat(s.bars))];
    const lv = s.ids.map(lvl).filter(x => x != null);
    s.level = lv.length ? Math.min(...lv) : null;
    s.nSevere = lv.filter(x => x <= 1).length;
    s.ranked = s.ids.filter(id => lvl(id) != null).sort((a, b) => lvl(a) - lvl(b));   // worst first
    s.worst = s.ranked[0] || null;
    s.name = T(s.en, s.ar);
    // a regional map slide only when it shows one of the sector's two most critical issues (severe or high concern)
    const e = SUBN[s.key], link = e && SUB_LINK[e.id];
    s.mapId = e && e.mapData && e.regions && link && off(link, 1) && s.ranked.slice(0, 2).includes(link) ? link : null;
    // the issue the map shows leads the sector slide, so the map builds on what the reader has just seen
    if (s.mapId) s.ranked = [s.mapId].concat(s.ranked.filter(id => id !== s.mapId));
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
  // rough text height (inches) for wrapped body text, so stacked blocks never overlap
  const textH = (t, w, size) => { const per = Math.max(20, Math.floor(w * (ar ? 15.5 : 14) * 9 / size)); return Math.max(1, Math.ceil(String(t).length / per)) * size * 0.0185 + 0.06; };
  // stat card: value (+unit), label, benchmark line with the gap, source. Severity-coloured top bar; outdated values flagged.
  // Only called for indicators that have data — cards without data are left out of the slide.
  const statCard = (sl, id, x, y, w, h, compact) => {
    const r = R(id), L = lvlAny(id), pad = compact ? 0.12 : 0.16, unit = I[id].u ? I[id].u[ar ? 1 : 0] : '';
    sl.shape(p.ShapeType.rect, { x, y, w, h, fill:{ color:C.CARD }, line:{ type:'none' } });
    sl.shape(p.ShapeType.rect, { x, y, w, h:0.05, fill:{ color: L == null ? C.GOLD : SEV.fill[L] }, line:{ type:'none' } });
    sl.text([{ text:I[id].f(r), options:{ fontFace:HEAD, fontSize: compact ? 19 : 22, bold:true, color: (L != null && L <= 1) ? SEV.text[L] : C.INK } },
             { text: unit, options:{ fontFace:BODY, fontSize: compact ? 7.4 : 8, color:C.MUTE } }],
      { x:x + pad, y:y + 0.1, w:w - 2 * pad, h:0.46, valign:'middle', fit:'shrink' });
    sl.text(lbl(id), { x:x + pad, y:y + 0.56, w:w - 2 * pad, h:0.26, fontFace:BODY, fontSize: compact ? 7.6 : 8.4, bold:true, color:C.INK, valign:'top', fit:'shrink' });
    const t = target(id);
    if (t != null) {
      const g = gap(id);
      sl.shape(p.ShapeType.rect, { x:x + pad, y:y + 0.91, w:0.16, h:0.025, fill:{ color:C.GOLD }, line:{ type:'none' } });
      sl.text([{ text:T('Benchmark ', 'المعيار ') + I[id].f({ v:t }), options:{ color:C.GOLD, bold:true } },
               { text: g ? '  ·  ' + g : '', options:{ color: L != null && L <= 1 ? SEV.text[L] : C.MUTE, bold: L != null && L <= 1 } }],
        { x:x + pad + 0.22, y:y + 0.8, w:w - 2 * pad - 0.22, h:0.24, fontFace:BODY, fontSize: compact ? 7 : 7.6, valign:'middle', fit:'shrink' });
    }
    sl.text(cite(id), { x:x + pad, y:y + h - 0.25, w:w - 2 * pad, h:0.22, fontFace:BODY, fontSize: compact ? 6.2 : 6.8, color: r && r.stale ? SEV.text[0] : C.FAINT, valign:'top', bold: !!(r && r.stale) });
  };
  const bullets = (sl, items, x, y, w, col, size) => {
    let yy = y;
    items.forEach(t => {
      const hh = textH(t, w - 0.22, size || 9.6);
      sl.shape(p.ShapeType.ellipse, { x: x + 0.02, y: yy + 0.07, w:0.08, h:0.08, fill:{ color: col || C.SKY_DK }, line:{ type:'none' } });
      sl.text(t, { x: x + 0.22, y: yy, w: w - 0.22, h: hh, fontFace:BODY, fontSize: size || 9.6, color:C.INK, valign:'top', wrap:true });
      yy += hh + 0.08;
    });
    return yy;
  };
  // title above a map: what it shows, with an optional muted note (e.g. the survey) on the right
  const mapTitle = (sl, title, note, x, w) => {
    sl.text(title, { x, y:1.32, w: note ? w * 0.68 : w, h:0.3, fontFace:HEAD, fontSize:12, bold:true, color:C.INK, valign:'middle', fit:'shrink' });
    if (note) sl.text(note, { x:x + w * 0.68, y:1.32, w:w * 0.32, h:0.3, fontFace:BODY, fontSize:7.6, color:C.MUTE, align:'right', valign:'middle' });
  };
  const needNote = (sl, x, y, w) => sl.text(NEED_NOTE, { x, y, w, h:0.36, fontFace:BODY, fontSize:7, color:C.MUTE, valign:'top', wrap:true });

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

  // ══ 2 · COUNTRY OVERVIEW — map + flag, capital, population, leaders, political situation, status by sector ══
  S.push(() => {
    const sl = newSlide(C.WHITE);
    head(sl, T('Country overview', 'نظرة عامة على الدولة'), NAME, T('location, leadership, political situation and status by sector', 'الموقع والقيادة والوضع السياسي والوضع حسب القطاع'));
    // map — accurate borders and neighbouring countries named, rendered at exactly this slot's aspect ratio (never stretched); flag in the corner
    const M = DK.MAP_SLOTS.country, mx = 0.5, my = 1.68;
    mapTitle(sl, T(`${NAME} and neighbouring countries`, `${NAME} والدول المجاورة`), '', mx, M.w);
    if (opts.mapData) sl.image({ data:opts.mapData, x:mx, y:my, w:M.w, h:M.h });
    else { sl.shape(p.ShapeType.rect, { x:mx, y:my, w:M.w, h:M.h, fill:{ color:C.SKY_PALE }, line:{ type:'none' } });
      sl.text(T('Map unavailable', 'الخريطة غير متاحة'), { x:mx, y:my + M.h / 2 - 0.2, w:M.w, h:0.4, fontFace:BODY, fontSize:11, color:C.FAINT, align:'center' }); }
    if (opts.flagData) { const f = DK.contain(opts.flagRatio, mx + 0.2, my + 0.2, 1.1, 0.75);
      sl.shape(p.ShapeType.rect, { x:f.x - 0.04, y:f.y - 0.04, w:f.w + 0.08, h:f.h + 0.08, fill:{ color:C.WHITE }, line:{ color:C.LINE, width:0.5 } });
      sl.image({ data:opts.flagData, x:f.x, y:f.y, w:f.w, h:f.h }); }
    sl.text(T('National borders: Natural Earth', 'الحدود الوطنية: Natural Earth'), { x:mx, y:my + M.h + 0.03, w:M.w, h:0.22, fontFace:BODY, fontSize:7.4, color:C.FAINT, valign:'middle' });
    if (opts.need) needNote(sl, mx, my + M.h + 0.27, M.w);
    // right column
    const RX = 6.85, RW = 13.333 - RX - 0.5, pol = opts.politics;
    const info = ar && typeof AR_INFO !== 'undefined' && AR_INFO[country] ? { capital:AR_INFO[country][0] } : (opts.info || {});
    const nm = list => (list || []).slice(0, 2).map(x => T(x.en, x.ar)).join(T(' & ', ' و'));
    // term in office as years, e.g. "2019–present" or "2021–2026" when Wikidata records a scheduled end
    // term in office as years: start of tenure – end of the current term (researched table, else Wikidata), e.g. "2018–2028 (5-year term)"
    const term = (from, to, tm) => {
      const y0 = (tm && tm.since) || (from ? String(from).slice(0, 4) : ''); if (!y0) return '';
      const end = (tm && tm.end) || (to ? String(to).slice(0, 4) : '');
      return T('In office ', 'في المنصب ') + y0 + '–' + (end || T('present', 'الآن')) + (tm && tm.years ? '  ·  ' + T(`${tm.years}-year term`, `ولاية مدتها ${tm.years} سنوات`) : '');
    };
    const hasHos = !!(pol && pol.hos && pol.hos.length), hasHog = !!(pol && pol.hog && pol.hog.length);
    const sameLeader = hasHos && hasHog && nm(pol.hog) === nm(pol.hos);
    const offTxt = o => o && o.length ? T(o[0].en, o[0].ar) : '';
    const sub = (o, from, to, tm) => [offTxt(o), term(from, to, tm)];   // two lines: office title, then term
    const pop = R('SP.POP.TOTL');
    const facts = [
      info.capital ? [T('Capital', 'العاصمة'), info.capital] : null,
      pop ? [T('Population', 'عدد السكان'), F.pop(pop) + ' (' + pop.y + ')'] : null,
      hasHos ? [T('Head of state', 'رئيس الدولة'), nm(pol.hos), sub(pol.office, pol.hosSince, pol.hosUntil, pol.hosTerm)] : null,
      hasHog ? [T('Head of government', 'رئيس الحكومة'), sameLeader ? T('Same as head of state', 'رئيس الدولة نفسه') : nm(pol.hog), sameLeader ? '' : sub(pol.hogOffice, pol.hogSince, pol.hogUntil, pol.hogTerm)] : null,
      pol && pol.gov && pol.gov.length ? [T('System of government', 'نظام الحكم'), pol.gov.slice(0, 2).map(x => { const t = T(x.en, x.ar); return t.charAt(0).toUpperCase() + t.slice(1); }).join(' · ')] : REGION ? [T('Region', 'الإقليم'), REGION] : null,
      INCOME ? [T('Income group', 'فئة الدخل'), INCOME] : null,
    ].filter(Boolean);   // facts we have no information on are left out
    eyebrow(sl, T('Key facts', 'معلومات أساسية'), RX, 1.35, RW, C.SKY_DK);
    // rows are as tall as their content: the leaders row carries office and term lines
    const rowTop = [1.64]; for (let r = 0; r * 2 < facts.length; r++) rowTop.push(rowTop[r] + (facts.slice(r * 2, r * 2 + 2).some(f => f[2] && (f[2][0] || f[2][1])) ? 0.8 : 0.54));
    facts.forEach(([k, v, s2], i) => {
      const fx = RX + (i % 2) * (RW / 2 + 0.05), fy = rowTop[Math.floor(i / 2)], fw = RW / 2 - 0.1;
      sl.text(k, { x:fx, y:fy, w:fw, h:0.2, fontFace:BODY, fontSize:7.6, bold:true, color:C.FAINT, charSpacing:1 });
      sl.text(v, { x:fx, y:fy + 0.17, w:fw, h:0.27, fontFace:BODY, fontSize:10.2, bold:true, color:C.INK, valign:'top' });
      if (s2 && s2[0]) sl.text(s2[0], { x:fx, y:fy + 0.39, w:fw, h:0.22, fontFace:BODY, fontSize:7.4, color:C.MUTE, valign:'top' });
      if (s2 && s2[1]) sl.text(s2[1], { x:fx, y:fy + (s2[0] ? 0.56 : 0.39), w:fw, h:0.22, fontFace:BODY, fontSize:7.6, bold:true, color:C.SKY_DK, valign:'top' });
    });
    // political situation — WGI governance scores, coloured on the shared severity scale, with a colour key
    const W5 = [['GOV_WGI_PV.SC', 'Political stability', 'الاستقرار السياسي'], ['GOV_WGI_VA.SC', 'Voice & accountability', 'المشاركة والمساءلة'],
                ['GOV_WGI_GE.SC', 'Government effectiveness', 'فعالية الحكومة'], ['GOV_WGI_RL.SC', 'Rule of law', 'سيادة القانون'], ['GOV_WGI_CC.SC', 'Control of corruption', 'مكافحة الفساد']]
      .filter(([id]) => R(id));
    const py = 3.64, ph = 1.68;
    sl.shape(p.ShapeType.rect, { x:RX, y:py, w:RW, h:ph, fill:{ color:C.SKY_PALE }, line:{ type:'none' } });
    sl.text(T('POLITICAL SITUATION', 'الوضع السياسي'), { x:RX + 0.18, y:py + 0.08, w:RW * 0.5, h:0.22, fontFace:BODY, fontSize:8, bold:true, color:C.GOLD, charSpacing:1.4 });
    sl.text(T('governance scores, 0–100 (higher is better)', 'مؤشرات الحوكمة، 0–100 (الأعلى أفضل)'), { x:RX + RW * 0.45, y:py + 0.08, w:RW * 0.55 - 0.18, h:0.22, fontFace:BODY, fontSize:7.4, color:C.MUTE, align:'right' });
    const rowH = W5.length ? Math.min(0.24, 1.1 / W5.length) : 0.22;
    W5.forEach(([id, en, a], i) => {
      const r = R(id), L = DK.sevLvl(id, r.v), ry = py + 0.34 + i * rowH, lw = 2.3, bx = RX + 0.18 + lw, bw = RW - lw - 0.95;
      sl.text(T(en, a), { x:RX + 0.18, y:ry, w:lw, h:0.2, fontFace:BODY, fontSize:8.6, color:C.INK, valign:'middle' });
      sl.shape(p.ShapeType.rect, { x:bx, y:ry + 0.06, w:bw, h:0.09, fill:{ color:C.WHITE }, line:{ type:'none' } });
      sl.shape(p.ShapeType.rect, { x:bx, y:ry + 0.06, w:Math.max(0.04, bw * Math.min(1, r.v / 100)), h:0.09, fill:{ color: L == null ? C.SKY : SEV.fill[L] }, line:{ type:'none' } });
      sl.text(String(Math.round(r.v)) + (r.stale ? ' (' + r.y + ')' : ''), { x:bx + bw + 0.08, y:ry, w:0.7, h:0.2, fontFace:BODY, fontSize:9, bold:true, color: L != null && L <= 1 ? SEV.text[L] : C.INK, valign:'middle' });
    });
    if (!W5.length) sl.text(T('Governance scores could not be retrieved when this report was built.', 'تعذّر استرجاع مؤشرات الحوكمة عند إعداد هذا التقرير.'),
      { x:RX + 0.18, y:py + 0.45, w:RW - 0.36, h:0.4, fontFace:BODY, fontSize:9, color:C.MUTE, valign:'top' });
    // colour key: the severity bands for a 0–100 governance score
    const th = (rule('GOV_WGI_PV.SC') || { th:[25, 40, 60] }).th;
    const bands = [T(`< ${th[0]}`, `أقل من ${th[0]}`), `${th[0]}–${th[1]}`, `${th[1]}–${th[2]}`, T(`${th[2]}+`, `${th[2]} فأكثر`)];
    const ky = py + ph - 0.3, kw = (RW - 0.36) / 4;
    bands.forEach((b, L) => {
      const kx = RX + 0.18 + L * kw;
      sl.shape(p.ShapeType.rect, { x:kx, y:ky + 0.07, w:0.14, h:0.1, fill:{ color:SEV.fill[L] }, line:{ type:'none' } });
      sl.text([{ text:DK.sevLabelOf(L, ar), options:{ bold:true, color:C.INK } }, { text:'  ' + b, options:{ color:C.MUTE } }],
        { x:kx + 0.18, y:ky, w:kw - 0.2, h:0.24, fontFace:BODY, fontSize:6.8, valign:'middle', fit:'shrink' });
    });
    // need index + status by sector
    const by = 5.36, bh = 1.62;
    sl.shape(p.ShapeType.rect, { x:RX, y:by, w:1.6, h:bh, fill:{ color:C.GOLD_PALE }, line:{ type:'none' } });
    sl.text(T('NEED INDEX' + (opts.need ? '*' : ''), 'مؤشر الاحتياج' + (opts.need ? '*' : '')), { x:RX + 0.14, y:by + 0.12, w:1.4, h:0.22, fontFace:BODY, fontSize:7.8, bold:true, color:C.GOLD, charSpacing:1.4 });
    if (opts.need) {
      sl.text(String(Math.round(opts.need.score)), { x:RX + 0.14, y:by + 0.38, w:1.4, h:0.62, fontFace:HEAD, fontSize:32, bold:true, color:C.INK, valign:'middle' });
      sl.text(T('of 100 · Rank ' + opts.need.rank + '/' + opts.need.of, 'من 100 · الترتيب ' + opts.need.rank + ' من ' + opts.need.of), { x:RX + 0.14, y:by + 1.06, w:1.4, h:0.4, fontFace:BODY, fontSize:8, color:C.MUTE, valign:'top' });
    } else sl.text(T('Not ranked', 'غير مصنّفة'), { x:RX + 0.14, y:by + 0.5, w:1.4, h:0.4, fontFace:BODY, fontSize:10, color:C.MUTE });
    const sx = RX + 1.78, sw = RW - 1.78, shown = SECTORS.filter(s => s.level != null);
    sl.text(T('STATUS BY SECTOR', 'الوضع حسب القطاع'), { x:sx, y:by - 0.02, w:sw, h:0.2, fontFace:BODY, fontSize:7.8, bold:true, color:C.GOLD, charSpacing:1.4 });
    shown.forEach((s, i) => {
      const yy = by + 0.21 + i * Math.min(0.205, 1.42 / Math.max(1, shown.length));   // up to eight sectors fit
      sl.text(T(s.short[0], s.short[1]), { x:sx, y:yy, w:sw - 1.3, h:0.19, fontFace:BODY, fontSize:8.2, color:C.INK, valign:'middle' });
      badge(sl, s.level, sx + sw - 1.2, yy + 0.015, 1.2, 0.15);
    });
    foot(sl, T('World Bank Open Data & WGI · Wikidata (leaders) · Natural Earth (borders) · ', 'بيانات البنك الدولي ومؤشرات الحوكمة · ويكي بيانات (القادة) · Natural Earth (الحدود) · ') + DATE);
  });

  // ══ 3 · EXECUTIVE SUMMARY — overall picture, then each priority sector with its most urgent gaps ══
  S.push(() => {
    const sl = newSlide(C.WHITE);
    head(sl, T('Executive summary', 'الملخص التنفيذي'), NAME, T('priority sectors and their most urgent gaps', 'القطاعات ذات الأولوية وأكثر فجواتها إلحاحاً'));
    const n = opts.need;
    const tierTxt = n ? (n.rank <= n.of / 3 ? T('among the highest', 'ضمن الأعلى') : n.rank <= 2 * n.of / 3 ? T('in the middle', 'في المنتصف') : T('among the lower', 'ضمن الأدنى')) : '';
    const rated = SECTORS.filter(s => s.level != null);
    const priorities = rated.filter(s => s.level <= 1).sort((a, b) => a.level - b.level || b.nSevere - a.nSevere);
    const overall = [
      n ? T(`${NAME} scores ${Math.round(n.score)}/100 on the ODA need index* — rank ${n.rank} of ${n.of}, ${tierTxt} need among the countries ODA tracks.`,
            `تسجّل ${NAME} ${Math.round(n.score)} من 100 على مؤشر الاحتياج* — الترتيب ${n.rank} من ${n.of}، أي ${tierTxt} احتياجاً بين الدول التي يتابعها المكتب.`) : null,
      priorities.length && priorities.length === rated.length ? T(`All ${rated.length} sectors are rated severe or high concern — needs are broad-based, not confined to one area.`,
                                                  `جميع القطاعات (${rated.length}) مصنّفة حرجة أو مقلقة — أي أن الاحتياجات واسعة ولا تقتصر على مجال واحد.`)
      : priorities.length ? T(`${priorities.length} of ${rated.length} sectors are rated severe or high concern: ${priorities.map(s => s.en.toLowerCase()).join(', ')}.`,
                             `${priorities.length} من ${rated.length} قطاعات مصنّفة حرجة أو مقلقة: ${priorities.map(s => s.ar).join('، ')}.`)
                        : T('No sector is rated severe or high concern on current data; the sectors below are furthest from their benchmarks.', 'لا يوجد قطاع مصنّف حرجاً أو مقلقاً وفق البيانات الحالية؛ والقطاعات أدناه هي الأبعد عن معاييرها.'),
    ].filter(Boolean);
    eyebrow(sl, T('Overall picture', 'الصورة العامة'), 0.5, 1.36, 12.33, C.SKY_DK);
    const oy = bullets(sl, overall, 0.5, 1.66, 12.33, C.GOLD, 10.5);
    // priority sectors as columns; under each, its most urgent gaps and what they mean
    const top = (priorities.length ? priorities : rated.filter(s => s.level <= 2).sort((a, b) => a.level - b.level)).slice(0, 4);
    const cy = Math.max(oy + 0.12, 2.5);
    eyebrow(sl, T('Priority sectors and most urgent gaps', 'القطاعات ذات الأولوية وأكثر الفجوات إلحاحاً'), 0.5, cy, 12.33, C.SKY_DK);
    if (!top.length) sl.text(T('Key indicators in every sector meet their benchmarks on current data.', 'المؤشرات الرئيسية في جميع القطاعات تحقق معاييرها وفق البيانات الحالية.'),
      { x:0.5, y:cy + 0.4, w:12.33, h:0.4, fontFace:BODY, fontSize:10.5, color:C.MUTE });
    const gapCol = 0.2, cw = top.length ? (12.33 - gapCol * (top.length - 1)) / top.length : 0, ctop = cy + 0.32, ch = (n ? 6.56 : 6.98) - ctop;
    top.forEach((s, i) => {
      const x = 0.5 + i * (cw + gapCol), pad = 0.16, iw = cw - 2 * pad;
      sl.shape(p.ShapeType.rect, { x, y:ctop, w:cw, h:ch, fill:{ color:C.CARD }, line:{ type:'none' } });
      sl.shape(p.ShapeType.rect, { x, y:ctop, w:cw, h:0.06, fill:{ color:SEV.fill[s.level] }, line:{ type:'none' } });
      sl.text(s.name, { x:x + pad, y:ctop + 0.14, w:iw, h:0.34, fontFace:HEAD, fontSize: top.length > 3 ? 12 : 13.5, bold:true, color:C.INK, valign:'top', fit:'shrink' });
      badge(sl, s.level, x + pad, ctop + 0.52, 1.15, 0.2);
      const gaps = s.ranked.filter(id => lvl(id) <= Math.max(1, s.level)).slice(0, 3);
      let gy = ctop + 0.88;
      gaps.forEach(id => {
        const L = lvl(id), ppl = people(id);
        sl.shape(p.ShapeType.rect, { x:x + pad, y:gy, w:0.05, h:0.56, fill:{ color:SEV.fill[L] }, line:{ type:'none' } });
        sl.text(lbl(id), { x:x + pad + 0.14, y:gy - 0.02, w:iw - 0.14, h:0.25, fontFace:BODY, fontSize:9, bold:true, color:C.INK, valign:'top', fit:'shrink' });
        sl.text([{ text:val(id), options:{ bold:true, color:SEV.text[L] } }, { text: target(id) != null ? T('  ·  benchmark ', '  ·  المعيار ') + I[id].f({ v:target(id) }) : '', options:{ color:C.MUTE } }],
          { x:x + pad + 0.14, y:gy + 0.19, w:iw - 0.14, h:0.24, fontFace:BODY, fontSize:8.4, valign:'top', fit:'shrink' });
        if (ppl) sl.text(T(`≈ ${ppl} people affected`, `≈ ${ppl} شخص متأثر`), { x:x + pad + 0.14, y:gy + 0.38, w:iw - 0.14, h:0.22, fontFace:BODY, fontSize:7.8, color:C.MUTE, valign:'top' });
        gy += 0.68;
      });
      // what it means — the "so what" behind the most urgent gap
      const w = WHY[gaps[0]];
      if (w) {
        const so = T(w.so[0], w.so[1]), sy = Math.max(gy + 0.04, ctop + 0.88 + 3 * 0.68 + 0.04);
        sl.shape(p.ShapeType.line, { x:x + pad, y:sy, w:iw, h:0, line:{ color:C.HAIR, width:0.5 } });
        sl.text(T('WHY IT MATTERS', 'لماذا يهم ذلك'), { x:x + pad, y:sy + 0.06, w:iw, h:0.2, fontFace:BODY, fontSize:7.2, bold:true, color:C.GOLD, charSpacing:1.2 });
        sl.text(so, { x:x + pad, y:sy + 0.27, w:iw, h:ctop + ch - sy - 0.33, fontFace:BODY, fontSize: top.length > 3 ? 8 : 8.6, color:C.INK, valign:'top', wrap:true, fit:'shrink' });
      }
    });
    if (n) needNote(sl, 0.5, 6.66, 12.33);
    foot(sl, T('ODA need index and SDG/WHO benchmarks · World Bank Open Data · ', 'مؤشر الاحتياج ومعايير أهداف التنمية المستدامة · بيانات البنك الدولي · ') + DATE);
  });

  // ══ "Where the need is" — sub-national map after a sector slide. Only when an official DHS survey measured the
  //    indicator region by region AND it is one of the sector's most critical issues (s.mapId), so the map
  //    builds on the story of the sector slide rather than introducing a new one ══
  const SURVEY_AR = { DHS:'المسح الديموغرافي والصحي', MIS:'مسح مؤشرات الملاريا', AIS:'مسح مؤشرات الإيدز' };
  function subSlide(s) {
    if (!s.mapId) return;
    const e = SUBN[s.key], M0 = s.mapId;
    S.push(() => {
      const sl = newSlide(C.WHITE);
      const fv = v => v == null ? '—' : e.pct ? F.pct({ v }, 1) : F.num({ v });
      const svy = T(country + ' ' + e.type + ' ' + e.year, (SURVEY_AR[e.type] || e.type) + ' ' + e.year);
      const ind = T(e.en, e.ar);
      const bad = v => e.worse === 'high' ? v : -v;                       // larger = greater need
      const ranked = e.regions.filter(r => r.v != null).sort((a, b) => bad(b.v) - bad(a.v));
      const worst = ranked[0], best = ranked[ranked.length - 1];
      head(sl, T('Where the need is', 'أين تتركز الاحتياجات'), s.name, T(`${e.en.toLowerCase()} is worst in ${worst.name}`, `${e.ar}: الأسوأ في ${worst.name}`));
      // map — rendered at the slot's exact aspect ratio
      const M = DK.MAP_SLOTS.sub, mx = 0.5, my = 1.68;
      mapTitle(sl, T(e.en.charAt(0).toUpperCase() + e.en.slice(1) + ' by area', e.ar + ' حسب المنطقة'), svy, mx, M.w);
      sl.image({ data:e.mapData, x:mx, y:my, w:M.w, h:M.h });
      sl.text(T('Each area is shaded by its measured survey value; grey = no estimate. Boundaries: DHS Spatial Data Repository.',
                'تُلوَّن كل منطقة وفق القيمة المقيسة في المسح؛ الرمادي = لا يوجد تقدير. الحدود: مستودع البيانات المكانية لبرنامج DHS.'),
        { x:mx, y:my + M.h + 0.04, w:M.w, h:0.24, fontFace:BODY, fontSize:7.6, color:C.FAINT, valign:'middle' });
      // right column: the national problem from the sector slide → where it is concentrated → where to act first
      const RX = 8.15, RW = 13.333 - RX - 0.5, L0 = lvl(M0);
      sl.shape(p.ShapeType.rect, { x:RX, y:1.35, w:RW, h:1.0, fill:{ color: SEV.tint[L0] }, line:{ type:'none' } });
      sl.shape(p.ShapeType.rect, { x:RX, y:1.35, w:0.06, h:1.0, fill:{ color: SEV.fill[L0] }, line:{ type:'none' } });
      sl.text(T('NATIONALLY', 'على المستوى الوطني'), { x:RX + 0.2, y:1.42, w:RW - 0.3, h:0.2, fontFace:BODY, fontSize:7.6, bold:true, color:SEV.text[L0], charSpacing:1.2 });
      sl.text([{ text:val(M0), options:{ bold:true, color:SEV.text[L0] } }, { text:'  ' + lbl(M0) + (gap(M0, true) ? ' · ' + gap(M0, true) : ''), options:{ color:C.INK } }],
        { x:RX + 0.2, y:1.62, w:RW - 0.3, h:0.42, fontFace:BODY, fontSize:9.4, valign:'top', wrap:true, fit:'shrink' });
      sl.text((e.national != null ? T('Survey national average ', 'المتوسط الوطني في المسح ') + fv(e.national) + ' · ' : '') + svy,
        { x:RX + 0.2, y:2.06, w:RW - 0.3, h:0.2, fontFace:BODY, fontSize:7.4, color:C.MUTE, valign:'middle' });
      const g2 = worst && best && Math.min(worst.v, best.v) > 0 ? Math.max(worst.v, best.v) / Math.min(worst.v, best.v) : null;
      const above = e.national != null ? ranked.filter(r => bad(r.v) > bad(e.national)).length : null;
      const act = s.acts.find(a => a[0] === M0);
      const story = T(`It ranges from ${fv(best.v)} in ${best.name} to ${fv(worst.v)} in ${worst.name}` + (g2 && g2 >= 1.3 ? `, a ${g2.toFixed(1)}× gap` : '') + '.'
                + (above != null ? ` ${above} of ${ranked.length} regions are worse than the national average.` : '')
                + (act && ranked.length > 2 ? ` ${worst.name} and ${ranked[1].name} are where to start: ${act[2].charAt(0).toLowerCase() + act[2].slice(1)}` : ''),
                `يتراوح بين ${fv(best.v)} في ${best.name} و${fv(worst.v)} في ${worst.name}` + (g2 && g2 >= 1.3 ? `، أي فجوة بمقدار ${g2.toFixed(1)} أضعاف` : '') + '.'
                + (above != null ? ` ${above} من ${ranked.length} مناطق أسوأ من المتوسط الوطني.` : '')
                + (act && ranked.length > 2 ? ` وتُعد ${worst.name} و${ranked[1].name} نقطة البداية: ${act[3]}` : ''));
      sl.text(story, { x:RX, y:2.46, w:RW, h:0.92, fontFace:BODY, fontSize:9, color:C.INK, valign:'top', wrap:true, fit:'shrink' });
      // legend — five equal value bands, colour darkens with need
      eyebrow(sl, T('Legend', 'دليل الألوان'), RX, 3.42, RW, C.SKY_DK);
      const lw = RW / 5;
      e.cols.forEach((col, i) => {
        sl.shape(p.ShapeType.rect, { x:RX + i * lw, y:3.7, w:lw - 0.03, h:0.16, fill:{ color:col }, line:{ type:'none' } });
        sl.text(fv(e.breaks[i]).replace(/\.0(%?)$/, '$1') + '–' + fv(e.breaks[i + 1]).replace(/\.0(%?)$/, '$1'), { x:RX + i * lw, y:3.87, w:lw, h:0.2, fontFace:BODY, fontSize:6.8, color:C.MUTE, align:'center' });
      });
      // highest / lowest need regions, bars on the same scale
      const max = e.pct ? 100 : Math.max(...ranked.map(r => r.v)) * 1.1;
      const list = (title, items, y) => {
        eyebrow(sl, title, RX, y, RW, C.GOLD);
        items.forEach((r, i) => {
          const ry = y + 0.28 + i * 0.27, nw = 1.75, bx = RX + nw + 0.05, bw = RW - nw - 0.75;
          const col = e.cols[Math.min(4, Math.floor((r.v - e.breaks[0]) / ((e.breaks[5] - e.breaks[0]) / 5 || 1)))];
          sl.text(r.name, { x:RX, y:ry, w:nw, h:0.22, fontFace:BODY, fontSize:8.4, color:C.INK, valign:'middle', fit:'shrink' });
          sl.shape(p.ShapeType.rect, { x:bx, y:ry + 0.06, w:bw, h:0.1, fill:{ color:C.SKY_PALE }, line:{ type:'none' } });
          sl.shape(p.ShapeType.rect, { x:bx, y:ry + 0.06, w:Math.max(0.04, bw * Math.min(1, r.v / max)), h:0.1, fill:{ color:col }, line:{ type:'none' } });
          sl.text(fv(r.v), { x:bx + bw + 0.05, y:ry, w:0.65, h:0.22, fontFace:BODY, fontSize:8.6, bold:true, color:C.INK, valign:'middle', align:'right' });
        });
        return y + 0.28 + items.length * 0.27;
      };
      const nTop = Math.min(5, Math.ceil(ranked.length / 2)), nBot = Math.min(2, ranked.length - nTop);
      const y2 = list(T('Greatest need', 'الاحتياج الأكبر'), ranked.slice(0, nTop), 4.2);
      if (nBot > 0) list(T('Least need', 'الاحتياج الأقل'), ranked.slice(-nBot).reverse(), y2 + 0.12);
      foot(sl, T('The DHS Program (ICF, USAID) · ', 'برنامج المسوح الديموغرافية والصحية (DHS) · ') + svy + ' · ' + DATE);
    });
  }

  // ══ 4–10 · SECTOR SLIDES (incl. governance & stability) ══
  SECTORS.forEach(s => { S.push(() => {
    const sl = newSlide(C.WHITE);
    const st = s.level == null ? T('not enough current data to rate this sector', 'لا تتوفر بيانات حديثة كافية لتصنيف هذا القطاع')
      : s.level === 0 ? T('severe gaps against benchmarks', 'فجوات حرجة مقارنةً بالمعايير')
      : s.level === 1 ? T('high concern on key indicators', 'قلق مرتفع في مؤشرات رئيسية')
      : s.level === 2 ? T('progress made, still short of benchmarks', 'تقدّم ملحوظ لكن دون المعايير')
      : T('key indicators meet their benchmarks', 'المؤشرات الرئيسية تحقق معاييرها');
    head(sl, T('Sector assessment', 'تقييم القطاع'), s.name, st);
    if (s.level != null) badge(sl, s.level, 11.53, 0.38, 1.3, 0.26);
    // stat cards — only indicators with data, the most critical first; benchmark shown inside each card
    const LX = 0.5, LW = 7.0;
    const cards = [...new Set(s.ranked.filter(id => s.stats.includes(id) || lvl(id) <= 1).concat(s.stats))].filter(id => R(id)).slice(0, 6);
    const cols = cards.length > 4 ? 3 : 2, rows = Math.ceil(cards.length / cols), cw = (LW - 0.18 * (cols - 1)) / cols, ch = 1.32;
    cards.forEach((id, i) => statCard(sl, id, LX + (i % cols) * (cw + 0.18), 1.38 + Math.floor(i / cols) * (ch + 0.14), cw, ch, cols === 3));
    const cardsEnd = cards.length ? 1.38 + rows * (ch + 0.14) - 0.14 : 1.38;
    // interventions: triggered by the indicators that are actually off track, plus development-investment angles where relevant
    const iy = cardsEnd + 0.2, room = 6.98 - iy;
    // one list: aid interventions triggered by off-track indicators, then development-investment options where the data makes them relevant
    let acts = s.acts.filter(([id, maxL]) => id === null ? false : off(id, maxL)).map(a => T(a[2], a[3]));
    if (acts.length < 3) acts = acts.concat(s.acts.filter(a => a[0] === null).map(a => T(a[2], a[3])));   // round out a short list with the sector-wide action
    const inv = (s.inv || []).filter(([cond]) => cond()).map(a => T(a[1], a[2])).slice(0, 2);
    const items = [], itemH = t => Math.max(0.29, textH(t, LW - 0.62, 8.8) + 0.04);
    let need = 0.5;
    acts.slice(0, 4).concat(inv).forEach(t => { if (need + itemH(t) <= room) { items.push(t); need += itemH(t); } });
    const ih = Math.min(room, need);   // box sized to its content
    sl.shape(p.ShapeType.rect, { x:LX, y:iy, w:LW, h:ih, fill:{ color:C.GOLD_PALE }, line:{ type:'none' } });
    sl.shape(p.ShapeType.rect, { x:LX, y:iy, w:0.06, h:ih, fill:{ color:C.GOLD }, line:{ type:'none' } });
    eyebrow(sl, T('Potential interventions', 'تدخلات مقترحة'), LX + 0.22, iy + 0.1, LW - 0.4);
    let ay = iy + 0.38;
    items.forEach(t => { const h = itemH(t);
      sl.text([{ text:'▸  ', options:{ color:C.GOLD, bold:true } }, { text:t, options:{ color:C.INK } }],
        { x:LX + 0.22, y:ay, w:LW - 0.4, h, fontFace:BODY, fontSize:8.8, valign:'middle', wrap:true }); ay += h; });
    // where several indicators have no recent figures, say which (instead of empty cards) so the reader knows the picture is partial
    const missing = s.ids.filter(id => !R(id));
    if (missing.length >= 2 && iy + ih + 0.75 < 6.98) {
      const my2 = iy + ih + 0.22;
      sl.text(T('LIMITED DATA', 'بيانات محدودة'), { x:LX, y:my2, w:LW, h:0.22, fontFace:BODY, fontSize:7.8, bold:true, color:C.FAINT, charSpacing:1.4 });
      sl.text(T(`No recent figures for ${andList(missing.map(id => { const t = lbl(id).replace(/ \(.*\)$/, ''); return /^[A-Z]{2}/.test(t) ? t : t.charAt(0).toLowerCase() + t.slice(1); }))}. A field assessment would confirm the picture before programming.`,
                `لا تتوفر أرقام حديثة عن ${andList(missing.map(id => lbl(id)))}. ويُستحسن إجراء تقييم ميداني لتأكيد الصورة قبل البرمجة.`),
        { x:LX, y:my2 + 0.24, w:LW, h:0.5, fontFace:BODY, fontSize:8.8, color:C.MUTE, valign:'top', wrap:true });
    }
    // key insights: what the gaps mean and what sits behind them, most critical first
    const RX = 7.85, RW = 13.333 - RX - 0.5;
    eyebrow(sl, T('Key insights', 'أبرز الملاحظات'), RX, 1.38, RW, C.SKY_DK);
    let ins = s.ranked.filter(id => lvl(id) <= 2).map(id => insight(id, id === s.mapId)).filter(Boolean).slice(0, 3);
    // Trade: what the export base looks like (manufactured vs food share) — a structural point, not a benchmark rating
    if (s.key === 'trade') {
      const m = R('TX.VAL.MANF.ZS.UN'), fd = R('TX.VAL.FOOD.ZS.UN'), tp = opts.trade && opts.trade.exports;
      const narrow = (m && !m.stale && m.v < 30) || (fd && !fd.stale && fd.v >= 40);
      if (narrow) {
        const mk = tp && tp.top.length ? T(' Main markets: ', ' أبرز الأسواق: ') + andList(tp.top.slice(0, 3).map(x => x.name)) + '.' : '';
        ins = ins.concat([{ L: 2, head: T('Narrow export base', 'قاعدة صادرات ضيقة'),
          body: T(`Manufactured goods are ${m ? Math.round(m.v) + '%' : 'a small share'} of exports${fd ? ` and food ${Math.round(fd.v)}%` : ''}, so earnings depend on a few primary products and swing with world prices and the weather.`,
                  `تشكّل السلع المصنّعة ${m ? Math.round(m.v) + '%' : 'نسبة صغيرة'} من الصادرات${fd ? ` والأغذية ${Math.round(fd.v)}%` : ''}، لذا تعتمد الإيرادات على عدد قليل من المنتجات الأولية وتتقلب مع الأسعار العالمية والطقس.`) + mk }]).slice(0, 3);
      }
    }
    let y = 1.7;
    if (!ins.length) {
      const msg = s.level === 3 ? T('Key indicators meet their benchmarks. The priority is to protect these gains and reach the communities still left behind.',
                                    'تحقق المؤشرات الرئيسية معاييرها. والأولوية هي الحفاظ على هذه المكاسب والوصول إلى المجتمعات التي لا تزال متأخرة.')
                                : T('There is not enough current data to analyse this sector. A field assessment is needed before programming here.',
                                    'لا تتوفر بيانات حديثة كافية لتحليل هذا القطاع، ويلزم إجراء تقييم ميداني قبل البرمجة فيه.');
      sl.text(msg, { x:RX, y, w:RW, h:0.8, fontFace:BODY, fontSize:9.6, color:C.INK, valign:'top', wrap:true });
    }
    ins.forEach(it => {
      const bh = textH(it.body, RW - 0.2, 9.6), hh = 0.34, total = hh + bh;
      if (y + total > 6.98) return;
      sl.shape(p.ShapeType.rect, { x:RX, y, w:0.05, h:total, fill:{ color:SEV.fill[it.L] }, line:{ type:'none' } });
      sl.text(it.head, { x:RX + 0.18, y, w:RW - 0.2, h:hh, fontFace:HEAD, fontSize:12, bold:true, color:C.INK, valign:'top', fit:'shrink' });
      sl.text(it.body, { x:RX + 0.18, y:y + hh, w:RW - 0.2, h:bh, fontFace:BODY, fontSize:9.6, color:C.INK, valign:'top', wrap:true });
      y += total + 0.2;
    });
    // Trade: main trading partners (World Bank WITS / UN Comtrade), under the insights
    if (s.key === 'trade' && opts.trade && (opts.trade.exports || opts.trade.imports) && y + 1.75 <= 6.98) {
      const cols = [[T('Top export markets', 'أبرز أسواق التصدير'), opts.trade.exports], [T('Top import sources', 'أبرز مصادر الاستيراد'), opts.trade.imports]].filter(c => c[1]);
      const cw2 = (RW - 0.2 * (cols.length - 1)) / cols.length;
      cols.forEach(([title, side], ci) => {
        const cx = RX + ci * (cw2 + 0.2);
        eyebrow(sl, title, cx, y, cw2, C.SKY_DK);
        sl.text(T('Share of goods trade, ', 'الحصة من تجارة السلع، ') + side.year, { x:cx, y:y + 0.22, w:cw2, h:0.18, fontFace:BODY, fontSize:7, color:C.FAINT });
        side.top.forEach((pt, i) => {
          const ry = y + 0.44 + i * 0.25, nw = cw2 * 0.5, bx = cx + nw, bw = cw2 - nw - 0.5;
          sl.text(pt.name, { x:cx, y:ry, w:nw - 0.05, h:0.22, fontFace:BODY, fontSize:8.4, color:C.INK, valign:'middle', fit:'shrink' });
          sl.shape(p.ShapeType.rect, { x:bx, y:ry + 0.07, w:bw, h:0.09, fill:{ color:C.SKY_PALE }, line:{ type:'none' } });
          sl.shape(p.ShapeType.rect, { x:bx, y:ry + 0.07, w:Math.max(0.03, bw * Math.min(1, pt.share / 50)), h:0.09, fill:{ color:C.SKY }, line:{ type:'none' } });
          sl.text(pt.share.toFixed(1) + '%', { x:bx + bw + 0.04, y:ry, w:0.46, h:0.22, fontFace:BODY, fontSize:8.4, bold:true, color:C.INK, valign:'middle', align:'right' });
        });
      });
    }
    const srcs = [...new Set(s.ids.map(id => SRC[id]).filter(Boolean).flatMap(x => x.split(' · ')))].slice(0, 5).map(srcTxt).join(' · ');
    foot(sl, srcs + ' · ' + DATE);
  }); subSlide(s); });

  // ══ 11 · METHOD & SOURCES ══
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
      [T('ODA need index', 'مؤشر الاحتياج'), T('A 0–100 score (higher = greater need). Combines under-5 and maternal mortality, undernourishment and lack of basic water, sanitation and electricity, each scaled across all tracked countries (0–100).',
        'درجة من 0 إلى 100 (الأعلى = احتياج أكبر). تجمع بين وفيات الأطفال دون الخامسة ووفيات الأمهات ونقص التغذية ونقص مياه الشرب الأساسية والصرف الصحي والكهرباء، مع قياس كل منها عبر جميع الدول المتابَعة (0–100).')],
      [T('Sources', 'المصادر'), [T('World Bank Open Data', 'بيانات البنك الدولي المفتوحة'), T('World Bank Worldwide Governance Indicators', 'مؤشرات الحوكمة العالمية'), 'IMF', 'WHO', 'UN IGME (UNICEF/WHO)', 'UNESCO UIS', 'FAO', 'WHO/UNICEF JMP', 'ITU', 'IEA', 'ILO', T('Wikidata (heads of state and government)', 'ويكي بيانات (رؤساء الدول والحكومات)'), T('The DHS Program (regional maps)', 'برنامج المسوح الديموغرافية والصحية DHS (الخرائط حسب المنطقة)'), T('ILO', 'منظمة العمل الدولية'), T('World Bank Global Findex, Enterprise Surveys and Logistics Performance Index', 'مؤشر الشمول المالي ومسوح المؤسسات ومؤشر الأداء اللوجستي للبنك الدولي'), T('World Bank WITS', 'نظام WITS للبنك الدولي')].map(x => ar ? srcTxt(x) : x).join(' · ') +
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
