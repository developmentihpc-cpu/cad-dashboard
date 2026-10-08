/* severity.js — ONE severity scale for the whole product (dashboard cards, region
 * popup, country reports and region reports): 0 Severe · 1 High concern · 2 Moderate · 3 On track.
 *
 * Benchmarks follow SDG / WHO / UNESCO / IMF reference points where one exists.
 * dir +1 = higher is worse, -1 = lower is worse; th = [severe, high, moderate] cut-offs.
 * `peers: true` = no standard benchmark — the dashboard compares with the other
 * tracked countries instead (reports skip those).
 */
'use strict';

const SEV_RULES = {
  'SH.DYN.MORT':        { dir: 1, th:[75, 40, 25],        ref:'SDG target 25 per 1,000',           refAr:'هدف التنمية المستدامة 25 لكل 1,000' },
  'SH.STA.MMRT':        { dir: 1, th:[500, 200, 70],      ref:'SDG target 70 per 100,000',         refAr:'هدف التنمية المستدامة 70 لكل 100,000' },
  'SP.DYN.LE00.IN':     { dir:-1, th:[60, 65, 72],        ref:'global average ≈ 73 years',         refAr:'المتوسط العالمي ≈ 73 سنة' },
  'SH.STA.STNT.ZS':     { dir: 1, th:[30, 20, 10],        ref:'WHO prevalence bands',              refAr:'فئات الانتشار لمنظمة الصحة العالمية' },
  'SN.ITK.DEFC.ZS':     { dir: 1, th:[25, 15, 5],         ref:'FAO: below 5% is low',              refAr:'الفاو: أقل من 5% يُعد منخفضاً' },
  'SH.IMM.MEAS':        { dir:-1, th:[70, 85, 95],        ref:'WHO target 95%',                    refAr:'هدف منظمة الصحة العالمية 95%' },
  'SH.XPD.CHEX.GD.ZS':  { dir:-1, th:[3, 4, 5],           ref:'WHO guide 5% of GDP',               refAr:'إرشاد منظمة الصحة العالمية 5% من الناتج' },
  'SH.MED.PHYS.ZS':     { dir:-1, th:[0.2, 0.5, 1],       ref:'WHO workforce thresholds',          refAr:'عتبات القوى العاملة لمنظمة الصحة العالمية' },
  'SE.ADT.LITR.ZS':     { dir:-1, th:[50, 70, 90],        ref:'SDG 4.6 universal literacy',        refAr:'الهدف 4.6 محو الأمية الشامل' },
  'SE.ADT.1524.LT.ZS':  { dir:-1, th:[60, 80, 95],        ref:'SDG 4.6 universal literacy',        refAr:'الهدف 4.6 محو الأمية الشامل' },
  'SE.PRM.CMPT.ZS':     { dir:-1, th:[60, 75, 90],        ref:'SDG 4.1 universal completion',      refAr:'الهدف 4.1 الإتمام الشامل' },
  'SE.SEC.ENRR':        { dir:-1, th:[40, 60, 85],        ref:'SDG 4.1',                           refAr:'الهدف 4.1' },
  'SE.PRM.PTRT.ZS':     { dir: 1, th:[45, 35, 25],        ref:'UNESCO: 40+ pupils per teacher is high', refAr:'اليونسكو: أكثر من 40 تلميذاً لكل معلم مرتفع' },
  'SE.XPD.TOTL.GD.ZS':  { dir:-1, th:[2.5, 3.5, 4],       ref:'UNESCO 4–6% of GDP',                refAr:'اليونسكو 4–6% من الناتج' },
  'EG.ELC.ACCS.ZS':     { dir:-1, th:[40, 70, 95],        ref:'SDG 7.1 universal access',          refAr:'الهدف 7.1 الوصول الشامل' },
  'EG.CFT.ACCS.ZS':     { dir:-1, th:[20, 50, 85],        ref:'SDG 7.1 clean cooking',             refAr:'الهدف 7.1 الطهي النظيف' },
  'SH.H2O.BASW.ZS':     { dir:-1, th:[60, 75, 90],        ref:'SDG 6.1 universal access',          refAr:'الهدف 6.1 الوصول الشامل' },
  'SH.H2O.SMDW.ZS':     { dir:-1, th:[30, 50, 75],        ref:'SDG 6.1 safely managed water',      refAr:'الهدف 6.1 المياه المُدارة بأمان' },
  'SH.STA.BASS.ZS':     { dir:-1, th:[40, 60, 85],        ref:'SDG 6.2 universal sanitation',      refAr:'الهدف 6.2 الصرف الصحي الشامل' },
  'SH.STA.SMSS.ZS':     { dir:-1, th:[20, 40, 65],        ref:'SDG 6.2 safely managed sanitation', refAr:'الهدف 6.2 الصرف الصحي المُدار بأمان' },
  'SH.STA.ODFC.ZS':     { dir: 1, th:[20, 10, 2],         ref:'SDG 6.2 end open defecation',       refAr:'الهدف 6.2 إنهاء التغوط في العراء' },
  'SH.STA.HYGN.ZS':     { dir:-1, th:[30, 50, 75],        ref:'SDG 6.2 basic hygiene',             refAr:'الهدف 6.2 النظافة الأساسية' },
  'SI.POV.DDAY':        { dir: 1, th:[30, 15, 5],         ref:'SDG 1.1 end extreme poverty',       refAr:'الهدف 1.1 القضاء على الفقر المدقع' },
  'SI.POV.GINI':        { dir: 1, th:[45, 40, 35],        ref:'Gini above 40 = high inequality',   refAr:'جيني فوق 40 = تفاوت مرتفع' },
  'FP.CPI.TOTL.ZG':     { dir: 1, th:[20, 10, 5],         ref:'IMF: under 5% is stable',           refAr:'صندوق النقد: أقل من 5% مستقر' },
  'NY.GDP.MKTP.KD.ZG':  { dir:-1, th:[0, 2, 4],           ref:'growth below 2% is weak',           refAr:'النمو دون 2% ضعيف' },
  'SL.UEM.TOTL.ZS':     { dir: 1, th:[15, 10, 6],         ref:'ILO modelled estimates',            refAr:'تقديرات منظمة العمل الدولية' },
  'GC.DOD.TOTL.GD.ZS':  { dir: 1, th:[90, 70, 50],        ref:'IMF debt-risk ranges',              refAr:'نطاقات مخاطر الدين لصندوق النقد' },
  'GC.TAX.TOTL.GD.ZS':  { dir:-1, th:[10, 13, 15],        ref:'IMF: 15% of GDP tipping point',     refAr:'صندوق النقد: عتبة 15% من الناتج' },
  'IT.NET.USER.ZS':     { dir:-1, th:[25, 50, 75],        ref:'ITU connectivity targets',          refAr:'أهداف الاتصال للاتحاد الدولي للاتصالات' },
  'EN.ATM.PM25.MC.M3':  { dir: 1, th:[35, 25, 15],        ref:'WHO interim air-quality targets',   refAr:'أهداف جودة الهواء المرحلية لمنظمة الصحة' },
  'AG.YLD.CREL.KG':     { dir:-1, th:[1500, 2500, 4000],  ref:'world average ≈ 4,000 kg/ha',       refAr:'المتوسط العالمي ≈ 4,000 كغ/هكتار' },
  'NY.GDP.PCAP.PP.CD':  { dir:-1, th:[3000, 7000, 15000], ref:'income bands (PPP)',                refAr:'فئات الدخل (تعادل القوة الشرائية)' },
  // no standard benchmark → compared with the other tracked countries (dashboard only)
  'SH.MED.BEDS.ZS':     { dir:-1, peers:true }, 'SE.TER.ENRR':    { dir:-1, peers:true },
  'IT.NET.BBND.P2':     { dir:-1, peers:true }, 'IT.CEL.SETS.P2': { dir:-1, peers:true },
  'IS.ROD.PAVE.ZS':     { dir:-1, peers:true }, 'ER.PTD.TOTL.ZS': { dir:-1, peers:true },
  'SP.POP.DPND':        { dir: 1, peers:true }, 'SN.ITK.DFCT':    { dir: 1, peers:true },
};
const SEV_LABELS = {
  en: ['Severe', 'High concern', 'Moderate', 'On track'],
  ar: ['حرج', 'مقلق', 'متوسط', 'على المسار'],
};
// hex without '#', for PowerPoint; the dashboard CSS uses the same values
const SEV_COLORS = {
  fill: ['E5484D', 'F5871F', 'F5C518', '1FAF6B'],   // solid (badges, bars)
  tint: ['FFE0E1', 'FFE9D2', 'FFF5CC', 'DDF4E7'],   // cell / card backgrounds
  text: ['C8282E', 'C2620A', '8C6A00', '13804C'],   // values on tints
  onFill: ['FFFFFF', 'FFFFFF', '5C4600', 'FFFFFF'], // text on solid badges
};
// Benchmark level (0–3) for a value, or null when there is no benchmark rule.
function sevLevel(id, v) {
  const r = SEV_RULES[id];
  if (!r || r.peers || v == null || isNaN(v)) return null;
  const [a, b, c] = r.th;
  return r.dir > 0 ? (v > a ? 0 : v > b ? 1 : v > c ? 2 : 3) : (v < a ? 0 : v < b ? 1 : v < c ? 2 : 3);
}

if (typeof window !== 'undefined') Object.assign(window, { SEV_RULES, SEV_LABELS, SEV_COLORS, sevLevel });
if (typeof module !== 'undefined' && module.exports) module.exports = { SEV_RULES, SEV_LABELS, SEV_COLORS, sevLevel };
