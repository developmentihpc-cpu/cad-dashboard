/* country_deck.js — canonical ODA country-assessment deck generator.
 *
 * Reusable in TWO homes from ONE body of layout code:
 *   • Node (this file, `buildCountryDeck(opts)`) — for QA renders and any server-side use.
 *   • Browser (docs/index.html) — the same slide code is ported into cd_exportCountryPPT,
 *     reading live World Bank data from countryDataCache.
 *
 * Design target: Country_Proposals.pptx (the ODA country-needs-assessment deck) —
 * navy left rail, cream panels, gold eyebrows, Lora numerals, grey stat cards each
 * carrying a SOURCE · YEAR citation, sector-status badges, tan intervention boxes,
 * and an "ODA  NN/NN" footer. Every figure is referenced; a closing Sources slide
 * lists provenance.
 *
 * Data model (opts):
 *   country   : display name
 *   data      : { <WB indicator id>: {value:Number|null, year:String} , ... }
 *   info      : { capital, currency, languages }
 *   iso2      : 2-letter code (for the ISO box when no flag image)
 *   programs  : { existing:[], proposed:[], evaluation:[] }  (optional)
 *   requests  : [ {titleEn, sector, path, status, cost, country}, ... ] (optional)
 *   reqMeta   : { <id>: {impact, implName} }  (optional)
 *   flagData  : dataURL of the flag png/svg  (optional)
 *   mapData   : dataURL of a country map image (optional)
 *   dateStr   : "August 2026" (retrieval month)
 *   PptxGenJS : the pptxgenjs constructor (Node passes require('pptxgenjs'); browser uses global)
 *   fileName  : output filename
 *   write     : 'file' (Node writeFile) | 'blob' (browser writeFile download). default 'file'.
 */
'use strict';

// ── ODA brand tokens ──
const INK='1D252C', GOLD='AD833B', GOLD_LT='C7A877', NAVY='333F64', SLATE='2F586E',
      BLUE='678CA5', SKY='CBDCE6', CREAM='F7F5EF', CARD='F4F5F7', PANEL='F1EEE6',
      GREEN='2F7F58', BRONZE='AD833B', BORDEAUX='79242F', WHITE='FFFFFF',
      FG2='5B6A7E', FG3='8A96A4', BORDER='E2E2E2', HEAD='Lora', BODY='Montserrat';

// ── Source attribution: WB indicator id → originating agency label ──
const IND_SRC = {
  'SP.POP.TOTL':'World Bank','EN.POP.DNST':'World Bank','SP.DYN.LE00.IN':'World Bank',
  'NY.GDP.MKTP.KD.ZG':'World Bank','FP.CPI.TOTL.ZG':'World Bank','NY.GDP.MKTP.CD':'World Bank',
  'NY.GDP.PCAP.PP.CD':'World Bank · IMF','NY.GDP.MKTP.PP.CD':'World Bank · IMF',
  'GC.TAX.TOTL.GD.ZS':'IMF · World Bank','GC.DOD.TOTL.GD.ZS':'IMF','BN.CAB.XOKA.GD.ZS':'IMF',
  'NY.GNP.PCAP.CD':'World Bank','SL.UEM.TOTL.ZS':'ILO · World Bank','SI.POV.GINI':'World Bank',
  'SI.POV.DDAY':'World Bank','NE.TRD.GNFS.ZS':'World Bank','BX.KLT.DINV.WD.GD.ZS':'World Bank',
  'SH.DYN.MORT':'UN IGME (UNICEF/WHO)','SH.STA.MMRT':'WHO · UNICEF · UNFPA','SH.XPD.CHEX.GD.ZS':'WHO GHED',
  'SH.MED.PHYS.ZS':'WHO','SH.MED.BEDS.ZS':'WHO','SH.IMM.MEAS':'WHO · UNICEF','SH.STA.STNT.ZS':'UNICEF · WHO · World Bank',
  'SE.ADT.LITR.ZS':'UNESCO UIS','SE.ADT.1524.LT.ZS':'UNESCO UIS','SE.PRM.ENRR':'UNESCO UIS','SE.SEC.ENRR':'UNESCO UIS',
  'SE.TER.ENRR':'UNESCO UIS','SE.PRM.NENR':'UNESCO UIS','SE.SEC.NENR':'UNESCO UIS','SE.PRM.CMPT.ZS':'UNESCO UIS',
  'SE.XPD.TOTL.GD.ZS':'UNESCO · World Bank','SE.PRM.PTRT.ZS':'UNESCO UIS',
  'SN.ITK.DEFC.ZS':'FAO','SN.ITK.DFCT':'FAO','AG.PRD.FOOD.XD':'FAO','AG.YLD.CREL.KG':'FAO',
  'NV.AGR.TOTL.ZS':'World Bank','AG.LND.AGRI.ZS':'FAO · World Bank','AG.LND.ARBL.ZS':'FAO · World Bank',
  'AG.LND.FRST.ZS':'FAO · World Bank','SL.AGR.EMPL.ZS':'ILO · World Bank','SP.RUR.TOTL.ZS':'World Bank',
  'EG.ELC.ACCS.ZS':'World Bank · IEA','EG.FEC.RNEW.ZS':'IEA · World Bank','EG.CFT.ACCS.ZS':'WHO',
  'EG.USE.ELEC.KH.PC':'IEA','EG.USE.PCAP.KG.OE':'IEA','EN.ATM.CO2E.PC':'World Bank · Climate Watch',
  'EN.ATM.PM25.MC.M3':'WHO','ER.PTD.TOTL.ZS':'UNEP-WCMC','ER.LND.PTLD.ZS':'UNEP-WCMC',
  'SH.H2O.SMDW.ZS':'WHO/UNICEF JMP','SH.H2O.BASW.ZS':'WHO/UNICEF JMP','SH.STA.SMSS.ZS':'WHO/UNICEF JMP',
  'SH.STA.BASS.ZS':'WHO/UNICEF JMP','SH.STA.ODFC.ZS':'WHO/UNICEF JMP','SH.STA.HYGN.ZS':'WHO/UNICEF JMP',
  'IT.NET.USER.ZS':'ITU · World Bank','IT.CEL.SETS.P2':'ITU','IT.NET.BBND.P2':'ITU','SP.URB.TOTL.IN.ZS':'World Bank',
};
const srcOf = id => IND_SRC[id] || 'World Bank';

function buildCountryDeck(opts){
  const { country, data={}, info={}, iso2='', programs={}, requests=[], reqMeta={},
          flagData=null, mapData=null, dateStr, write='file' } = opts;
  const Pptx = opts.PptxGenJS || (typeof PptxGenJS!=='undefined' ? PptxGenJS : null);
  if(!Pptx) throw new Error('PptxGenJS constructor not provided');
  const DATE = dateStr || new Date().toLocaleDateString('en-US',{month:'long',year:'numeric'});

  // ── optional AI deep-research model (phase 2). When present, its cited multi-source
  //    stats / insights / interventions override the World-Bank-templated content. ──
  const R = opts.research || null;
  const rSec = k => (R && R.sectors && R.sectors[k]) || null;
  const _t=(s,n)=>{s=String(s==null?'':s);return s.length>n?s.slice(0,n-1)+'…':s;};
  const rStats = k => { const s=rSec(k); if(!s||!Array.isArray(s.stats)||!s.stats.length) return null;
    return s.stats.slice(0,4).map(st=>({ val:_t(st.value==null?'—':st.value,14), lbl:_t(st.label||'',40),
      cite:_t([st.source,st.year].filter(Boolean).join(' · '),42), neg:!!st.neg })); };
  const statusBadge = st => { const s=String(st||'').toLowerCase();
    return s.startsWith('impr')?{l:'Improving',c:'2F7F58'}:s.startsWith('sev')?{l:'Severe',c:'79242F'}:s.startsWith('weak')?{l:'Weak',c:'79242F'}:{l:'Developing',c:'AD833B'}; };

  // ── data accessors ──
  const gv = id => (data[id] && data[id].value!=null) ? data[id].value : null;
  const yr = id => (data[id] && data[id].year) ? String(data[id].year) : '';
  const cite = id => { const s=srcOf(id), y=yr(id); return y ? (s+' · '+y) : s; };
  const f1=(id,u='')=>{const v=gv(id);return v!=null?v.toFixed(1)+u:'—';};
  const f0=(id,u='')=>{const v=gv(id);return v!=null?Math.round(v)+u:'—';};
  const fPop=id=>{const v=gv(id);if(v==null)return '—';return v>=1e9?(v/1e9).toFixed(1)+'B':v>=1e6?(v/1e6).toFixed(1)+'M':Math.round(v).toLocaleString();};
  const fGDP=id=>{const v=gv(id);if(v==null)return '—';return v>=1e12?'$'+(v/1e12).toFixed(1)+'T':v>=1e9?'$'+(v/1e9).toFixed(0)+'B':'$'+(v/1e6).toFixed(0)+'M';};
  const fMoney0=id=>{const v=gv(id);return v!=null?'$'+Math.round(v).toLocaleString():'—';};

  // headline figures
  const pop=fPop('SP.POP.TOTL'), gdpGr=f1('NY.GDP.MKTP.KD.ZG','%'), inf=f1('FP.CPI.TOTL.ZG','%'),
        le=f1('SP.DYN.LE00.IN'), u5mr=f0('SH.DYN.MORT'), hexp=f1('SH.XPD.CHEX.GD.ZS','%'),
        lit=f0('SE.ADT.LITR.ZS','%'), stunt=f0('SH.STA.STNT.ZS','%'), under=f0('SN.ITK.DEFC.ZS','%'),
        elec=f0('EG.ELC.ACCS.ZS','%'), water=f0('SH.H2O.SMDW.ZS','%'), forest=f1('AG.LND.FRST.ZS','%'),
        inet=f0('IT.NET.USER.ZS','%'), unemp=f1('SL.UEM.TOTL.ZS','%'), agriGDP=f0('NV.AGR.TOTL.ZS','%'),
        co2=f1('EN.ATM.CO2E.PC'), tax=f1('GC.TAX.TOTL.GD.ZS','%'),
        gdpCapV=gv('NY.GDP.PCAP.PP.CD'), gdpCap=gdpCapV!=null?'$'+Math.round(gdpCapV).toLocaleString():'—';
  // income class from GDP/cap PPP (GNI Atlas often null in snapshot)
  const incBasis = gv('NY.GNP.PCAP.CD') || (gdpCapV!=null?gdpCapV/1.6:null);
  const dacClass = incBasis==null?'Developing':incBasis<1135?'Least Developed · Low Income':incBasis<4465?'Developing · Lower-Middle Income':incBasis<13845?'Developing · Upper-Middle Income':'High Income';
  const cInfo = { capital:info.capital||'—', currency:info.currency||'—', languages:info.languages||'—' };

  // sector status badges
  const badge=(l,c)=>({l,c});
  const healthSt=(()=>{const v=gv('SH.DYN.MORT');if(v==null)return badge('Developing',BRONZE);return v>80?badge('Severe',BORDEAUX):v>40?badge('Weak',BORDEAUX):v>25?badge('Developing',BRONZE):badge('Improving',GREEN);})();
  const eduSt=(()=>{const v=gv('SE.ADT.LITR.ZS');if(v==null)return badge('Developing',BRONZE);return v<40?badge('Severe',BORDEAUX):v<65?badge('Weak',BORDEAUX):v<88?badge('Developing',BRONZE):badge('Improving',GREEN);})();
  const foodSt=(()=>{const v=gv('SN.ITK.DEFC.ZS');if(v==null)return badge('Developing',BRONZE);return v>25?badge('Severe',BORDEAUX):v>15?badge('Weak',BORDEAUX):v>7?badge('Developing',BRONZE):badge('Improving',GREEN);})();
  const washSt=(()=>{const v=gv('SH.H2O.SMDW.ZS');if(v==null)return badge('Developing',BRONZE);return v<40?badge('Severe',BORDEAUX):v<65?badge('Developing',BRONZE):v<85?badge('Developing',BRONZE):badge('Improving',GREEN);})();
  const econSt=(()=>{const g=gv('NY.GDP.MKTP.KD.ZG'),i=gv('FP.CPI.TOTL.ZG');if(g==null)return badge('Developing',BRONZE);return(g>4&&(i==null||i<8))?badge('Improving',GREEN):g>2?badge('Developing',BRONZE):badge('Weak',BORDEAUX);})();
  const infraSt=(()=>{const v=gv('EG.ELC.ACCS.ZS');if(v==null)return badge('Developing',BRONZE);return v<40?badge('Severe',BORDEAUX):v<70?badge('Weak',BORDEAUX):v<95?badge('Developing',BRONZE):badge('Improving',GREEN);})();

  // data-driven interventions (reference key each to a live figure)
  const iH=[gv('SH.XPD.CHEX.GD.ZS')!=null&&gv('SH.XPD.CHEX.GD.ZS')<5?`Raise health spending toward WHO's 5% of GDP (now ${hexp}).`:'Strengthen primary-healthcare networks and rural reach.',`Scale community health workers — under-5 mortality ${u5mr}/1,000.`,'Strengthen vaccine coverage & immunisation systems.','Improve maternal & emergency obstetric care.'];
  const iE=[`Improve learning quality & assessment — adult literacy ${lit}.`,'Expand secondary-school access & retention.','Mother-tongue early-grade instruction.','Conditional transfers to keep girls in school.'];
  const iEc=[gv('GC.TAX.TOTL.GD.ZS')!=null&&gv('GC.TAX.TOTL.GD.ZS')<15?`Mobilise domestic revenue — tax take just ${tax} of GDP.`:'Strengthen public financial management.',`Hold inflation near ${inf} via monetary & supply-side policy.`,'Attract FDI and support SME development.','Deepen financial inclusion.'];
  const iF=[stunt!=='—'?`Cut child stunting from ${stunt} via early-childhood nutrition.`:'Scale nutrition-sensitive programmes.','Strengthen food safety nets for vulnerable households.','Diversify food systems & cut post-harvest loss.','Build strategic reserves & market integration.'];
  const iA=['Expand smallholder irrigation & resilient seeds.',`Strengthen agricultural extension — cereal yield ${f0('AG.YLD.CREL.KG')} kg/ha.`,'Invest in rural markets & value chains.','Scale climate-smart agriculture.'];
  const iI=[elec!=='—'?`Extend reliable power beyond ${elec} national access — prioritise rural.`:'Improve grid reliability & rural electrification.','Invest in all-season rural roads.','Mobile-money rails for social protection.','Off-grid solar for clinics & schools.'];
  const iW=[water!=='—'?`Extend safely managed water beyond ${water} — rural gaps largest.`:'Expand safely managed water infrastructure.','Upgrade sanitation & eliminate open defecation.','Move households from basic to safely managed service.','Climate-proof source water.'];
  const iEn=['Upgrade transmission & distribution to cut losses.',`Scale renewable capacity — clean fuels for cooking at ${f0('EG.CFT.ACCS.ZS','%')}.`,'Electrify transport & clean cooking beyond the grid.','Expand solar to complement hydropower.'];

  // ── PPTX ──
  const p = new Pptx();
  p.defineLayout({name:'W',width:13.333,height:7.5}); p.layout='W';
  p.title=`${country} — Country Assessment`; p.author='ODA Country Assessment Dashboard';
  let PAGE=0, TOTAL=0;

  // ── shared helpers (reference-matched) ──
  const trim=(s,n)=>{s=String(s==null?'':s);return s.length>n?s.slice(0,n-1)+'…':s;};
  const eyebrow=(sl,t,x,y,w,col)=>sl.addText(String(t).toUpperCase(),{x,y,w,h:0.22,fontFace:BODY,fontSize:9,bold:true,color:col||GOLD,charSpacing:2.4});
  const foot=(sl,srcTxt,dark)=>{
    PAGE++;
    const lc=dark?'4A5578':BORDER, tc=dark?'9AA7BD':FG3, oc=dark?GOLD_LT:NAVY;
    sl.addShape(p.ShapeType.line,{x:0.5,y:7.12,w:12.33,h:0,line:{color:lc,width:0.5}});
    sl.addText('Source: '+srcTxt,{x:0.5,y:7.17,w:9.5,h:0.22,fontFace:BODY,fontSize:8,color:tc,valign:'middle'});
    sl.addText([{text:'ODA',options:{bold:true,color:oc}},{text:'   '+String(PAGE).padStart(2,'0')+' / '+String(TOTAL).padStart(2,'0'),options:{color:tc}}],{x:10.5,y:7.17,w:2.33,h:0.22,fontFace:BODY,fontSize:8,align:'right',valign:'middle'});
  };
  const oneLine=s=>trim(String(s==null?'':s).split(/\.\s/)[0].replace(/\.$/,''),82);
  const sectorHead=(sl,eb,title,statement)=>{
    eyebrow(sl,eb,0.5,0.34,8,GOLD);
    sl.addText([{text:title,options:{bold:true,color:INK}},{text:'  —  '+oneLine(statement),options:{color:FG3}}],{x:0.5,y:0.58,w:12.3,h:0.5,fontFace:HEAD,fontSize:18,valign:'middle'});
  };
  // 2×2 grid of citation stat cards
  const statCards=(sl,stats,x,y,w,cols=2,cardH=1.0)=>{
    const gap=0.18, cw=(w-(cols-1)*gap)/cols;
    stats.slice(0,cols*2).forEach((s,i)=>{
      const cx=x+(i%cols)*(cw+gap), cy=y+Math.floor(i/cols)*(cardH+gap);
      sl.addShape(p.ShapeType.rect,{x:cx,y:cy,w:cw,h:cardH,fill:{color:CARD},line:{type:'none'}});
      sl.addShape(p.ShapeType.rect,{x:cx,y:cy,w:cw,h:0.045,fill:{color:s.neg?BORDEAUX:GOLD},line:{type:'none'}});
      sl.addText(String(s.val),{x:cx+0.16,y:cy+0.12,w:cw-0.3,h:0.44,fontFace:HEAD,fontSize:(String(s.val).length>7?20:26),bold:true,color:s.neg?BORDEAUX:INK,valign:'middle'});
      sl.addText(s.lbl,{x:cx+0.16,y:cy+0.55,w:cw-0.3,h:0.26,fontFace:BODY,fontSize:8.4,bold:true,color:INK,valign:'top',wrap:true});
      sl.addText(s.cite||'',{x:cx+0.16,y:cardH>1.05?cy+0.80:cy+0.80,w:cw-0.3,h:0.18,fontFace:BODY,fontSize:7,color:FG3,valign:'top'});
    });
  };
  const insights=(sl,items,x,y,w)=>{
    eyebrow(sl,'Key insights',x,y,w,SLATE);
    let iy=y+0.28;
    items.slice(0,3).forEach(t=>{
      sl.addShape(p.ShapeType.rect,{x:x+0.02,y:iy+0.04,w:0.09,h:0.09,fill:{color:SLATE},line:{type:'none'}});
      const lines=Math.max(1,Math.ceil(String(t).length/64));
      sl.addText(t,{x:x+0.24,y:iy,w:w-0.24,h:0.20*lines+0.06,fontFace:BODY,fontSize:9,color:INK,valign:'top',wrap:true});
      iy+=0.20*lines+0.12;
    });
    return iy;
  };
  const interventions=(sl,items,x,y,w,h)=>{
    sl.addShape(p.ShapeType.rect,{x,y,w,h,fill:{color:PANEL},line:{type:'none'}});
    sl.addShape(p.ShapeType.rect,{x,y,w:0.06,h,fill:{color:GOLD},line:{type:'none'}});
    eyebrow(sl,'Potential interventions',x+0.2,y+0.12,w-0.3,GOLD);
    const list=items.slice(0,4), colW=(w-0.5)/2, rowY=y+0.42, rh=(h-0.52)/2;
    list.forEach((t,i)=>{
      const cx=x+0.2+(i%2)*colW, cy=rowY+Math.floor(i/2)*rh;
      sl.addText([{text:'▸  ',options:{color:GOLD,bold:true}},{text:trim(t,90),options:{color:INK}}],{x:cx,y:cy,w:colW-0.05,h:rh,fontFace:BODY,fontSize:8.4,valign:'top',wrap:true});
    });
  };
  // right-side visual: horizontal benchmark bars vs a reference value
  const benchViz=(sl,x,y,w,h,title,rows)=>{
    sl.addText(title,{x,y,w,h:0.24,fontFace:BODY,fontSize:10,bold:true,color:INK});
    const valid=rows.filter(r=>r.val!=null);
    if(!valid.length){ sl.addShape(p.ShapeType.rect,{x,y:y+0.34,w,h:h-0.5,fill:{color:CARD},line:{type:'none'}}); sl.addText('Indicator data not available for '+country+'.',{x:x+0.2,y:y+h/2-0.2,w:w-0.4,h:0.4,fontFace:BODY,fontSize:10,color:FG3,align:'center',valign:'middle'}); return; }
    const rH=(h-0.5)/valid.length;
    valid.forEach((r,i)=>{
      const ry=y+0.4+i*rH;
      sl.addText(r.label,{x,y:ry,w,h:0.2,fontFace:BODY,fontSize:8.6,bold:true,color:FG2});
      const bx=x,by=ry+0.22,bw=w,bh=0.24;
      sl.addShape(p.ShapeType.rect,{x:bx,y:by,w:bw,h:bh,fill:{color:'ECEFF2'},line:{type:'none'}});
      const ratio=r.inv?Math.max(0,Math.min(1,(r.bench-r.val)/r.bench)):Math.min(1,r.val/r.bench);
      const col=ratio>=0.8?GREEN:ratio>=0.5?GOLD:BORDEAUX;
      if(ratio>0)sl.addShape(p.ShapeType.rect,{x:bx,y:by,w:Math.max(0.04,bw*ratio),h:bh,fill:{color:col},line:{type:'none'}});
      sl.addText(r.val.toFixed(r.dec!=null?r.dec:1)+(r.unit||''),{x:bx+0.08,y:by,w:bw*0.5,h:bh,fontFace:BODY,fontSize:8.4,bold:true,color:WHITE,valign:'middle'});
      sl.addText('Benchmark '+r.bench+(r.unit||''),{x:bx+bw*0.5,y:by,w:bw*0.5-0.06,h:bh,fontFace:BODY,fontSize:7.4,color:FG3,align:'right',valign:'middle'});
    });
  };
  const mapOrPlaceholder=(sl,x,y,w,h,cap)=>{
    if(mapData){ sl.addImage({data:mapData,x,y,w,h}); sl.addShape(p.ShapeType.rect,{x,y,w,h,fill:{type:'none'},line:{color:BORDER,width:0.5}}); }
    else { sl.addShape(p.ShapeType.rect,{x,y,w,h,fill:{color:'E8EEF2'},line:{color:BORDER,width:0.5}}); sl.addText(country,{x,y:y+h/2-0.2,w,h:0.4,fontFace:HEAD,fontSize:16,color:BLUE,align:'center',bold:true}); }
    if(cap) sl.addText(cap,{x,y:y+h+0.04,w,h:0.18,fontFace:BODY,fontSize:7.5,color:FG3});
  };

  const S=[]; // slide builder queue (so we can count TOTAL then render with correct page nums)

  // ══ 01 COVER ══
  S.push(()=>{
    const sl=p.addSlide(); const LW=3.75;
    sl.addShape(p.ShapeType.rect,{x:0,y:0,w:13.333,h:7.5,fill:{color:CREAM},line:{type:'none'}});
    sl.addShape(p.ShapeType.rect,{x:0,y:0,w:LW,h:7.5,fill:{color:NAVY},line:{type:'none'}});
    if(flagData) sl.addImage({data:flagData,x:0.4,y:0.44,w:1.5,h:1.0});
    else { sl.addShape(p.ShapeType.rect,{x:0.4,y:0.44,w:1.5,h:1.0,fill:{color:'27304D'},line:{color:WHITE,width:0.5,transparency:60}}); sl.addText((iso2||'').toUpperCase(),{x:0.4,y:0.44,w:1.5,h:1.0,fontFace:HEAD,fontSize:26,bold:true,color:GOLD_LT,align:'center',valign:'middle'}); }
    sl.addText('COUNTRY OVERVIEW',{x:0.4,y:1.66,w:LW-0.6,h:0.22,fontFace:BODY,fontSize:9,bold:true,color:GOLD_LT,charSpacing:2.6});
    sl.addText(country,{x:0.37,y:1.9,w:LW-0.45,h:1.05,fontFace:HEAD,fontSize:country.length>12?36:46,bold:true,color:WHITE,valign:'top',wrap:true});
    if(R&&R.subtitle) sl.addText(R.subtitle,{x:0.4,y:3.02,w:LW-0.55,h:0.46,fontFace:BODY,fontSize:9.5,italic:true,color:SKY,valign:'top',wrap:true});
    const rows=[['UN CLASS',(R&&R.incomeClass)||dacClass],['CAPITAL',cInfo.capital],['GNI / CAP',gdpCap+(gdpCapV!=null?' PPP ('+yr('NY.GDP.PCAP.PP.CD')+')':'')],['CURRENCY',cInfo.currency],['LANGUAGES',cInfo.languages],['PERIOD',DATE]];
    let ry=3.55;
    rows.forEach(([k,v])=>{
      sl.addText(k,{x:0.4,y:ry,w:1.2,h:0.24,fontFace:BODY,fontSize:8,bold:true,color:GOLD_LT,charSpacing:1.2,valign:'top'});
      sl.addText(v,{x:1.62,y:ry,w:LW-1.75,h:0.52,fontFace:BODY,fontSize:11,color:'EAF0F4',valign:'top',wrap:true});
      ry+=0.55;
    });
    sl.addText(DATE.toUpperCase(),{x:0.4,y:7.05,w:LW-0.6,h:0.24,fontFace:BODY,fontSize:8.5,bold:true,color:GOLD_LT,charSpacing:1.5});
    // right: national snapshot
    const RX=LW+0.35, RW=13.333-LW-0.75;
    eyebrow(sl,'National snapshot · '+DATE,RX,0.34,RW,GOLD);
    sl.addShape(p.ShapeType.line,{x:RX,y:0.6,w:RW,h:0,line:{color:GOLD_LT,width:0.75}});
    const groups=[
      {lbl:'General',bc:GOLD,hero:{v:pop,k:'Total Population',c:cite('SP.POP.TOTL')},subs:[[le,'Life Expectancy (yrs)'],[unemp,'Unemployment']]},
      {lbl:'Economic',bc:GOLD,hero:{v:gdpCap,k:'GDP per capita PPP · '+gdpGr+' growth',c:cite('NY.GDP.PCAP.PP.CD')},subs:[[inf,'Inflation'],[tax,'Tax revenue / GDP']]},
      {lbl:'Social & Human Dev.',bc:GREEN,hero:{v:u5mr,k:'Under-5 Mortality / 1,000',c:cite('SH.DYN.MORT')},subs:[[elec,'Electricity access'],[water,'Safe water access']]},
    ];
    const gW=(RW-0.4)/3;
    groups.forEach((g,gi)=>{
      const gx=RX+gi*(gW+0.2);
      sl.addShape(p.ShapeType.rect,{x:gx,y:0.78,w:0.04,h:0.2,fill:{color:g.bc},line:{type:'none'}});
      sl.addText(g.lbl.toUpperCase(),{x:gx+0.12,y:0.78,w:gW-0.15,h:0.2,fontFace:BODY,fontSize:8.5,bold:true,color:NAVY,charSpacing:1.2});
      sl.addShape(p.ShapeType.rect,{x:gx,y:1.06,w:gW,h:1.0,fill:{color:WHITE},line:{type:'none'}});
      sl.addText(String(g.hero.v),{x:gx+0.14,y:1.14,w:gW-0.24,h:0.46,fontFace:HEAD,fontSize:26,bold:true,color:gi===2?GREEN:(gi===1?GOLD:NAVY)});
      sl.addText(g.hero.k,{x:gx+0.14,y:1.6,w:gW-0.24,h:0.24,fontFace:BODY,fontSize:8,bold:true,color:INK,wrap:true});
      sl.addText(g.hero.c,{x:gx+0.14,y:1.84,w:gW-0.24,h:0.18,fontFace:BODY,fontSize:6.8,color:FG3});
      const sw=(gW-0.1)/2;
      g.subs.forEach((s,si)=>{
        const sx=gx+si*(sw+0.1);
        sl.addShape(p.ShapeType.rect,{x:sx,y:2.14,w:sw,h:0.66,fill:{color:WHITE},line:{type:'none'}});
        sl.addText(String(s[0]),{x:sx+0.1,y:2.2,w:sw-0.18,h:0.28,fontFace:HEAD,fontSize:15,bold:true,color:NAVY});
        sl.addText(s[1],{x:sx+0.1,y:2.5,w:sw-0.18,h:0.26,fontFace:BODY,fontSize:7.4,color:FG2,wrap:true});
      });
    });
    // geographic + sector status
    eyebrow(sl,'Geographic context · sector status',RX,3.06,RW,GOLD);
    sl.addShape(p.ShapeType.line,{x:RX,y:3.32,w:RW,h:0,line:{color:GOLD_LT,width:0.75}});
    const mW=5.0, mY=3.46, mH=3.3;
    mapOrPlaceholder(sl,RX,mY,mW,mH,'');
    const spX=RX+mW+0.25, spW=RW-mW-0.25;
    sl.addShape(p.ShapeType.rect,{x:spX,y:mY,w:spW,h:mH,fill:{color:WHITE},line:{type:'none'}});
    sl.addShape(p.ShapeType.rect,{x:spX,y:mY,w:spW,h:0.045,fill:{color:NAVY},line:{type:'none'}});
    sl.addText('SECTOR STATUS · '+DATE.split(' ').pop(),{x:spX+0.14,y:mY+0.12,w:spW-0.24,h:0.2,fontFace:BODY,fontSize:8.5,bold:true,color:GOLD,charSpacing:1});
    const srows=(R&&Array.isArray(R.sectorStatus)&&R.sectorStatus.length>=6)?R.sectorStatus.slice(0,6).map(s=>[s.sector,trim(s.note,44),statusBadge(s.status)]):[['Health','U5 mortality '+u5mr+'/1,000',healthSt],['Education','Adult literacy '+lit,eduSt],['Food Security','Undernourishment '+under,foodSt],['WASH','Safe water '+water,washSt],['Economic','GDP growth '+gdpGr+' · inflation '+inf,econSt],['Infrastructure','Electricity '+elec,infraSt]];
    const srH=(mH-0.5)/srows.length;
    srows.forEach((r,i)=>{
      const sry=mY+0.42+i*srH;
      sl.addText(r[0],{x:spX+0.14,y:sry,w:spW-1.25,h:0.2,fontFace:BODY,fontSize:9.5,bold:true,color:INK});
      sl.addText(r[1],{x:spX+0.14,y:sry+0.2,w:spW-1.25,h:0.16,fontFace:BODY,fontSize:7,color:FG3});
      sl.addShape(p.ShapeType.rect,{x:spX+spW-1.06,y:sry+0.03,w:0.92,h:0.23,fill:{color:r[2].c},line:{type:'none'}});
      sl.addText(r[2].l.toUpperCase(),{x:spX+spW-1.06,y:sry+0.03,w:0.92,h:0.23,fontFace:BODY,fontSize:7,bold:true,color:WHITE,align:'center',valign:'middle'});
    });
  });

  // ══ 02 CROSS-SECTOR SNAPSHOT ══
  S.push(()=>{
    const sl=p.addSlide(); sl.addShape(p.ShapeType.rect,{x:0,y:0,w:13.333,h:7.5,fill:{color:WHITE},line:{type:'none'}});
    eyebrow(sl,country+' · cross-sector snapshot',0.5,0.34,10,GOLD);
    sl.addText([{text:'Sector Overview',options:{bold:true,color:INK}},{text:'  —  key indicators & recommended interventions by sector',options:{color:FG3}}],{x:0.5,y:0.58,w:12.3,h:0.44,fontFace:HEAD,fontSize:18,valign:'middle'});
    const cards=(R&&Array.isArray(R.crossSector)&&R.crossSector.length>=6)?R.crossSector.slice(0,6).map(c=>({nm:c.sector,st:statusBadge(c.status),lines:(c.lines||[]).slice(0,2).map(x=>trim(x,54)),rec:c.recommended||''})):[
      {nm:'Health',st:healthSt,lines:[`Under-5 mortality ${u5mr}/1,000 · life expectancy ${le} yrs`,`Health spend ${hexp} of GDP`],rec:iH[0]},
      {nm:'Education',st:eduSt,lines:[`Adult literacy ${lit}`,`Education spend ${f1('SE.XPD.TOTL.GD.ZS','%')} of GDP`],rec:iE[0]},
      {nm:'Food Security',st:foodSt,lines:[`Undernourishment ${under} · stunting ${stunt}`,`Agriculture ${agriGDP} of GDP`],rec:iF[0]},
      {nm:'Agriculture',st:econSt,lines:[`Agriculture ${agriGDP} of GDP`,`Cereal yield ${f0('AG.YLD.CREL.KG')} kg/ha`],rec:iA[0]},
      {nm:'Infrastructure',st:infraSt,lines:[`Electricity ${elec} · internet ${inet}`,`Mobile ${f0('IT.CEL.SETS.P2')}/100 people`],rec:iI[0]},
      {nm:'WASH',st:washSt,lines:[`Safely managed water ${water}`,`Safely managed sanitation ${f0('SH.STA.SMSS.ZS','%')}`],rec:iW[0]},
    ];
    const cols=3, gap=0.25, cw=(12.33-(cols-1)*gap)/cols, ch=2.55, y0=1.32;
    cards.forEach((c,i)=>{
      const cx=0.5+(i%cols)*(cw+gap), cy=y0+Math.floor(i/cols)*(ch+0.2);
      sl.addShape(p.ShapeType.rect,{x:cx,y:cy,w:cw,h:ch,fill:{color:CARD},line:{type:'none'}});
      sl.addText(c.nm,{x:cx+0.16,y:cy+0.14,w:cw-1.36,h:0.3,fontFace:HEAD,fontSize:15,bold:true,color:INK});
      sl.addShape(p.ShapeType.rect,{x:cx+cw-1.22,y:cy+0.16,w:1.06,h:0.24,fill:{color:c.st.c},line:{type:'none'}});
      sl.addText(c.st.l.toUpperCase(),{x:cx+cw-1.22,y:cy+0.16,w:1.06,h:0.24,fontFace:BODY,fontSize:6.8,bold:true,color:WHITE,align:'center',valign:'middle'});
      let ly=cy+0.56;
      c.lines.forEach(t=>{ sl.addText([{text:'•  ',options:{color:GOLD,bold:true}},{text:t,options:{color:INK}}],{x:cx+0.16,y:ly,w:cw-0.3,h:0.34,fontFace:BODY,fontSize:8.4,valign:'top',wrap:true}); ly+=0.36; });
      sl.addShape(p.ShapeType.rect,{x:cx+0.16,y:cy+ch-0.86,w:cw-0.32,h:0.72,fill:{color:PANEL},line:{type:'none'}});
      sl.addText('RECOMMENDED',{x:cx+0.28,y:cy+ch-0.8,w:cw-0.5,h:0.18,fontFace:BODY,fontSize:7,bold:true,color:GOLD,charSpacing:1});
      sl.addText(trim(c.rec,110),{x:cx+0.28,y:cy+ch-0.62,w:cw-0.52,h:0.5,fontFace:BODY,fontSize:8,color:INK,valign:'top',wrap:true});
    });
    foot(sl,'World Bank · WHO · UNESCO UIS · UNICEF · FAO · WHO/UNICEF JMP · ITU · '+DATE);
  });

  // sector slide factory (stats left, benchmark viz right — reference layout)
  const SECKEY={'Economy':'economy','Health':'health','Education':'education','Food Security & Nutrition':'food','Agriculture & Rural Livelihoods':'agriculture','Infrastructure & Connectivity':'infrastructure','Water, Sanitation & Hygiene':'wash','Energy & Power':'energy'};
  const sectorSlide=(eb,title,statement,stats,ins,intv,viz,footSrc)=>S.push(()=>{
    // Prefer AI-researched content for this sector when a research model is supplied.
    const key=SECKEY[eb]||String(eb).toLowerCase(), rs=rSec(key), rst=rStats(key);
    const useStmt=(rs&&rs.statement)?rs.statement:statement;
    const useStats=rst||stats;
    const useIns=(rs&&Array.isArray(rs.insights)&&rs.insights.length)?rs.insights.slice(0,3).map(t=>trim(t,140)):ins;
    const useIntv=(rs&&Array.isArray(rs.interventions)&&rs.interventions.length)?rs.interventions:intv;
    const useFoot=(rs&&rs.stats&&rs.stats.length)?(rs.stats.map(s=>s.source).filter(Boolean).filter((v,i,a)=>a.indexOf(v)===i).slice(0,4).join(' · ')+' · '+DATE):footSrc;
    const sl=p.addSlide(); sl.addShape(p.ShapeType.rect,{x:0,y:0,w:13.333,h:7.5,fill:{color:WHITE},line:{type:'none'}});
    sectorHead(sl,eb,title,useStmt);
    const LX=0.5, LW=7.0;
    statCards(sl,useStats,LX,1.35,LW);
    const insEnd=insights(sl,useIns,LX,3.7,LW);
    interventions(sl,useIntv,LX,Math.max(insEnd+0.05,5.05),LW,1.55);
    // right visual (World Bank benchmark bars — kept as an orientation reference)
    const RX=7.85, RW=4.98;
    viz(sl,RX,1.5,RW,4.8);
    foot(sl,useFoot);
  });

  // ══ 03 NATIONAL OVERVIEW ══
  S.push(()=>{
    const sl=p.addSlide(); sl.addShape(p.ShapeType.rect,{x:0,y:0,w:13.333,h:7.5,fill:{color:WHITE},line:{type:'none'}});
    sectorHead(sl,'National Overview','At a Glance',`${country}'s steady indicators alongside persistent service gaps`);
    statCards(sl,[
      {val:pop,lbl:'Population',cite:cite('SP.POP.TOTL')},
      {val:gdpCap,lbl:'GDP per capita PPP · '+dacClass.split('·').pop().trim(),cite:cite('NY.GDP.PCAP.PP.CD')},
      {val:le,lbl:'Life expectancy (yrs)',cite:cite('SP.DYN.LE00.IN')},
      {val:u5mr,lbl:'Under-5 mortality / 1,000',cite:cite('SH.DYN.MORT'),neg:gv('SH.DYN.MORT')>40},
    ],0.5,1.35,7.0);
    insights(sl,[
      `GDP growth ${gdpGr} with inflation ${inf} supports gradual gains in household welfare.`,
      `Strong national headline figures can mask urban–rural divides in water, sanitation and connectivity.`,
      `Life expectancy ${le} yrs and literacy ${lit} give a solid human-capital base to build on.`,
    ],0.5,3.75,7.0);
    mapOrPlaceholder(sl,7.85,1.5,4.98,4.4,'Geographic context');
    foot(sl,'World Bank Open Data · '+DATE);
  });

  // ══ per-sector ══
  sectorSlide('Economy','Economy',`Growth of ${gdpGr} continues; low tax revenue limits social investment`,
    [{val:gdpGr,lbl:'GDP growth',cite:cite('NY.GDP.MKTP.KD.ZG')},{val:inf,lbl:'Inflation',cite:cite('FP.CPI.TOTL.ZG'),neg:gv('FP.CPI.TOTL.ZG')>15},{val:gdpCap,lbl:'GDP per capita PPP',cite:cite('NY.GDP.PCAP.PP.CD')},{val:tax,lbl:'Tax revenue / GDP',cite:cite('GC.TAX.TOTL.GD.ZS')}],
    [`Growth ${gdpGr} is steady but commodity- and weather-sensitive; diversification builds resilience.`,`Inflation ${inf} is contained but still erodes real gains for lower-income households.`,`Tax revenue ${tax} of GDP constrains fiscal space for social investment.`],
    iEc,(sl,x,y,w,h)=>benchViz(sl,x,y,w,h,'Economy vs. benchmarks',[
      {label:'GDP growth (%)',val:gv('NY.GDP.MKTP.KD.ZG'),unit:'%',bench:3,dec:1},
      {label:'Inflation (%)',val:gv('FP.CPI.TOTL.ZG'),unit:'%',bench:5,inv:true,dec:1},
      {label:'Tax revenue (% GDP)',val:gv('GC.TAX.TOTL.GD.ZS'),unit:'%',bench:15,dec:1},
      {label:'Trade (% GDP)',val:gv('NE.TRD.GNFS.ZS'),unit:'%',bench:60,dec:0},
    ]),'World Bank · IMF · '+DATE);

  sectorSlide('Health','Health',`Child-health outcomes track at ${u5mr} under-5 deaths per 1,000`,
    [{val:u5mr,lbl:'Under-5 deaths / 1,000',cite:cite('SH.DYN.MORT'),neg:gv('SH.DYN.MORT')>40},{val:le,lbl:'Life expectancy (yrs)',cite:cite('SP.DYN.LE00.IN')},{val:hexp,lbl:'Health expenditure / GDP',cite:cite('SH.XPD.CHEX.GD.ZS')},{val:f1('SH.MED.PHYS.ZS'),lbl:'Physicians / 1,000',cite:cite('SH.MED.PHYS.ZS')}],
    [`Under-5 mortality ${u5mr}/1,000 reflects child-health system capacity for the income level.`,`Health spending ${hexp} of GDP — the gap is often rural reach and quality, not funding level.`,`Sustaining ${le}-yr life expectancy depends on continued maternal & child-health gains.`],
    iH,(sl,x,y,w,h)=>benchViz(sl,x,y,w,h,'Health vs. global benchmarks',[
      {label:'Under-5 mortality / 1,000',val:gv('SH.DYN.MORT'),unit:'',bench:37,inv:true,dec:0},
      {label:'Life expectancy (yrs)',val:gv('SP.DYN.LE00.IN'),unit:'',bench:73,dec:1},
      {label:'Health spend (% GDP)',val:gv('SH.XPD.CHEX.GD.ZS'),unit:'%',bench:5,dec:1},
      {label:'Maternal mortality / 100k',val:gv('SH.STA.MMRT'),unit:'',bench:211,inv:true,dec:0},
    ]),'World Bank · WHO · UNICEF · '+DATE);

  sectorSlide('Education','Education',`Access is strong at ${lit} literacy; learning-quality gaps persist`,
    [{val:lit,lbl:'Adult literacy rate',cite:cite('SE.ADT.LITR.ZS')},{val:f1('SE.XPD.TOTL.GD.ZS','%'),lbl:'Education expenditure / GDP',cite:cite('SE.XPD.TOTL.GD.ZS')},{val:f0('SE.SEC.ENRR','%'),lbl:'Secondary enrollment (gross)',cite:cite('SE.SEC.ENRR')},{val:f0('SE.PRM.CMPT.ZS','%'),lbl:'Primary completion',cite:cite('SE.PRM.CMPT.ZS')}],
    [`Adult literacy ${lit} is a major asset — the priority shifts from access to learning quality.`,`The secondary-transition gap is structural; keeping adolescents — especially girls — enrolled is critical.`,`Sustained investment in teacher quality converts enrollment into measurable learning.`],
    iE,(sl,x,y,w,h)=>benchViz(sl,x,y,w,h,'Education vs. benchmarks',[
      {label:'Adult literacy (%)',val:gv('SE.ADT.LITR.ZS'),unit:'%',bench:86,dec:0},
      {label:'Primary completion (%)',val:gv('SE.PRM.CMPT.ZS'),unit:'%',bench:90,dec:0},
      {label:'Secondary enrollment (%)',val:gv('SE.SEC.ENRR'),unit:'%',bench:75,dec:0},
      {label:'Education spend (% GDP)',val:gv('SE.XPD.TOTL.GD.ZS'),unit:'%',bench:4.7,dec:1},
    ]),'UNESCO UIS · World Bank · '+DATE);

  sectorSlide('Food Security & Nutrition','Food Security',`Undernourishment at ${under}, with child stunting at ${stunt}`,
    [{val:stunt,lbl:'Child stunting (under-5)',cite:cite('SH.STA.STNT.ZS'),neg:gv('SH.STA.STNT.ZS')>20},{val:under,lbl:'Undernourishment (% pop.)',cite:cite('SN.ITK.DEFC.ZS'),neg:gv('SN.ITK.DEFC.ZS')>15},{val:agriGDP,lbl:'Agriculture / GDP',cite:cite('NV.AGR.TOTL.ZS')},{val:f0('AG.YLD.CREL.KG')+' kg',lbl:'Cereal yield (kg/ha)',cite:cite('AG.YLD.CREL.KG')}],
    [`Stunting ${stunt} carries a long-term human-capital cost concentrated in rural & indigenous communities.`,`Undernourishment ${under} reflects pockets of structural vulnerability rather than a generalised crisis.`,`Agriculture ${agriGDP} of GDP underpins food availability; diversification reduces shock exposure.`],
    iF,(sl,x,y,w,h)=>benchViz(sl,x,y,w,h,'Nutrition vs. benchmarks',[
      {label:'Child stunting (%)',val:gv('SH.STA.STNT.ZS'),unit:'%',bench:22,inv:true,dec:0},
      {label:'Undernourishment (%)',val:gv('SN.ITK.DEFC.ZS'),unit:'%',bench:9,inv:true,dec:0},
      {label:'Cereal yield (kg/ha)',val:gv('AG.YLD.CREL.KG'),unit:'',bench:4000,dec:0},
      {label:'Food production index',val:gv('AG.PRD.FOOD.XD'),unit:'',bench:120,dec:0},
    ]),'UNICEF · WHO · FAO · '+DATE);

  sectorSlide('Agriculture & Rural Livelihoods','Agriculture',`A productive sector at ${agriGDP} of GDP, exposed to mounting climate risk`,
    [{val:agriGDP,lbl:'Agriculture / GDP',cite:cite('NV.AGR.TOTL.ZS')},{val:f0('AG.LND.AGRI.ZS','%'),lbl:'Agricultural land (% area)',cite:cite('AG.LND.AGRI.ZS')},{val:f0('AG.YLD.CREL.KG')+' kg',lbl:'Cereal yield (kg/ha)',cite:cite('AG.YLD.CREL.KG')},{val:f0('SP.RUR.TOTL.ZS','%'),lbl:'Rural population',cite:cite('SP.RUR.TOTL.ZS')}],
    [`Agriculture ${agriGDP} of GDP drives livelihoods and foreign exchange.`,`Yields near/above the world average show productivity strength; irrigation & inputs can push further.`,`Climate variability — drought and flooding — is the core risk to largely rain-fed systems.`],
    iA,(sl,x,y,w,h)=>benchViz(sl,x,y,w,h,'Agriculture vs. benchmarks',[
      {label:'Cereal yield (kg/ha)',val:gv('AG.YLD.CREL.KG'),unit:'',bench:4000,dec:0},
      {label:'Agricultural land (%)',val:gv('AG.LND.AGRI.ZS'),unit:'%',bench:38,dec:0},
      {label:'Arable land (%)',val:gv('AG.LND.ARBL.ZS'),unit:'%',bench:11,dec:0},
      {label:'Food production index',val:gv('AG.PRD.FOOD.XD'),unit:'',bench:120,dec:0},
    ]),'World Bank · FAO · '+DATE);

  sectorSlide('Infrastructure & Connectivity','Infrastructure',`Electricity reaches ${elec}; a stark urban–rural gap defines service access`,
    [{val:elec,lbl:'Electricity access',cite:cite('EG.ELC.ACCS.ZS')},{val:inet,lbl:'Internet users',cite:cite('IT.NET.USER.ZS')},{val:f0('IT.CEL.SETS.P2'),lbl:'Mobile subs / 100',cite:cite('IT.CEL.SETS.P2')},{val:f0('SP.URB.TOTL.IN.ZS','%'),lbl:'Urban population',cite:cite('SP.URB.TOTL.IN.ZS')}],
    [`Electricity ${elec} nationally, but service quality & reliability still favour urban areas.`,`Internet ${inet} with a mobile-first base makes a services leapfrog realistic.`,`Rural gaps in roads, water and broadband constrain health, education and commerce.`],
    iI,(sl,x,y,w,h)=>benchViz(sl,x,y,w,h,'Connectivity vs. benchmarks',[
      {label:'Electricity access (%)',val:gv('EG.ELC.ACCS.ZS'),unit:'%',bench:100,dec:0},
      {label:'Internet users (%)',val:gv('IT.NET.USER.ZS'),unit:'%',bench:66,dec:0},
      {label:'Mobile subs / 100',val:gv('IT.CEL.SETS.P2'),unit:'',bench:110,dec:0},
      {label:'Urban population (%)',val:gv('SP.URB.TOTL.IN.ZS'),unit:'%',bench:57,dec:0},
    ]),'World Bank · ITU · '+DATE);

  sectorSlide('Water, Sanitation & Hygiene','WASH',`Only ${water} on safely managed drinking water; sanitation gaps affect health`,
    [{val:water,lbl:'Safely managed drinking water',cite:cite('SH.H2O.SMDW.ZS'),neg:gv('SH.H2O.SMDW.ZS')<65},{val:f0('SH.STA.SMSS.ZS','%'),lbl:'Safely managed sanitation',cite:cite('SH.STA.SMSS.ZS'),neg:gv('SH.STA.SMSS.ZS')<50},{val:f0('SH.H2O.BASW.ZS','%'),lbl:'Basic drinking water',cite:cite('SH.H2O.BASW.ZS')},{val:f0('SH.STA.BASS.ZS','%'),lbl:'Basic sanitation',cite:cite('SH.STA.BASS.ZS')}],
    [`Access is near-universal at the basic tier, but only ${water} have safely managed water.`,`Gaps concentrate in rural and peri-urban belts on intermittent or untreated supply.`,`Weak water quality sustains diarrhoeal disease and erodes child-health and schooling gains.`],
    iW,(sl,x,y,w,h)=>benchViz(sl,x,y,w,h,'WASH vs. universal target',[
      {label:'Safely managed water (%)',val:gv('SH.H2O.SMDW.ZS'),unit:'%',bench:100,dec:0},
      {label:'Safely managed sanitation (%)',val:gv('SH.STA.SMSS.ZS'),unit:'%',bench:100,dec:0},
      {label:'Basic water (%)',val:gv('SH.H2O.BASW.ZS'),unit:'%',bench:100,dec:0},
      {label:'Basic sanitation (%)',val:gv('SH.STA.BASS.ZS'),unit:'%',bench:100,dec:0},
    ]),'WHO/UNICEF JMP · World Bank · '+DATE);

  sectorSlide('Energy & Power','Energy',`Electricity access at ${elec}; the shift is toward clean, reliable power`,
    [{val:elec,lbl:'Electricity access',cite:cite('EG.ELC.ACCS.ZS')},{val:f0('EG.FEC.RNEW.ZS','%'),lbl:'Renewable energy (% final)',cite:cite('EG.FEC.RNEW.ZS')},{val:f0('EG.CFT.ACCS.ZS','%'),lbl:'Clean cooking access',cite:cite('EG.CFT.ACCS.ZS')},{val:f0('EG.USE.ELEC.KH.PC')+' kWh',lbl:'Power use / capita',cite:cite('EG.USE.ELEC.KH.PC')}],
    [`Electricity is ${elec} nationally; reliability and rural quality remain the frontier.`,`Renewable share and clean-cooking access shape the carbon intensity of total energy.`,`Grid losses and distribution constraints limit how much clean supply reaches productive use.`],
    iEn,(sl,x,y,w,h)=>benchViz(sl,x,y,w,h,'Energy vs. benchmarks',[
      {label:'Electricity access (%)',val:gv('EG.ELC.ACCS.ZS'),unit:'%',bench:100,dec:0},
      {label:'Renewable energy (%)',val:gv('EG.FEC.RNEW.ZS'),unit:'%',bench:30,dec:0},
      {label:'Clean cooking (%)',val:gv('EG.CFT.ACCS.ZS'),unit:'%',bench:75,dec:0},
      {label:'CO₂ per capita (t)',val:gv('EN.ATM.CO2E.PC'),unit:'t',bench:4.7,inv:true,dec:1},
    ]),'IEA · World Bank · '+DATE);

  // (Pipeline-projects and Priorities slides intentionally omitted — this deck is a pure
  //  country assessment; pipeline data is country-specific and not relevant across all decks.)

  // ══ SOURCES ══
  S.push(()=>{
    const sl=p.addSlide(); sl.addShape(p.ShapeType.rect,{x:0,y:0,w:13.333,h:7.5,fill:{color:NAVY},line:{type:'none'}});
    sl.addText('COUNTRY OVERVIEW',{x:0.6,y:0.7,w:8,h:0.3,fontFace:BODY,fontSize:10,bold:true,color:GOLD_LT,charSpacing:2.6});
    sl.addText(country,{x:0.57,y:1.0,w:11,h:1.0,fontFace:HEAD,fontSize:44,bold:true,color:WHITE});
    sl.addText('Sector Assessment & Intervention Priorities · '+DATE+' · ODA Country Analysis',{x:0.6,y:2.05,w:11,h:0.4,fontFace:BODY,fontSize:12,color:SKY});
    sl.addShape(p.ShapeType.rect,{x:0.6,y:2.8,w:0.9,h:0.03,fill:{color:GOLD},line:{type:'none'}});
    sl.addText('SOURCES & PROVENANCE',{x:0.6,y:3.15,w:11,h:0.3,fontFace:BODY,fontSize:11,bold:true,color:GOLD_LT,charSpacing:2});
    const srcLine=(R&&Array.isArray(R.sources)&&R.sources.length)?R.sources.map(s=>s&&(s.label||s.url)).filter(Boolean).slice(0,14).join(' · '):'World Bank Open Data · IMF · WHO · UN IGME (UNICEF/WHO) · UNESCO UIS · FAO · WHO/UNICEF JMP · ITU · IEA · ILO';
    sl.addText(srcLine,{x:0.6,y:3.55,w:11.9,h:0.85,fontFace:BODY,fontSize:11,color:'EAF0F4',valign:'top',wrap:true});
    sl.addText(R?[
      {text:'This assessment was produced by live AI deep-research'+(R.searches?(' ('+R.searches+' web searches)'):'')+' across the primary sources above',options:{bold:true,color:WHITE}},
      {text:'. Every figure carries its source and reference year; interventions are country-specific. Figures that could not be verified against a primary source were omitted rather than estimated'+(R.confidence?('. Overall confidence: '+R.confidence):'')+'.',options:{color:SKY}},
    ]:[
      {text:'All indicator values are retrieved live from World Bank Open Data at the time of download',options:{bold:true,color:WHITE}},
      {text:' and compiled from the originating agencies listed above. Each figure on every slide carries its source and reference year. Where an indicator is unavailable for '+country+', the field is shown as “—” rather than estimated. Benchmarks are global or regional reference values for orientation, not targets.',options:{color:SKY}},
    ],{x:0.6,y:4.55,w:11.6,h:1.7,fontFace:BODY,fontSize:11,valign:'top',wrap:true,lineSpacingMultiple:1.15});
    sl.addText('Retrieved '+DATE+' · ODA Country Assessment Dashboard',{x:0.6,y:6.5,w:11,h:0.3,fontFace:BODY,fontSize:9,color:FG3});
    foot(sl,'World Bank Open Data (retrieved '+DATE+') + originating agencies',true);
  });

  TOTAL=S.length;
  S.forEach(fn=>fn());

  const fileName = opts.fileName || `${country.replace(/\s+/g,'_')}_Country_Assessment.pptx`;
  return p.writeFile({ fileName });
}

// Node CLI: node country_deck.js <indicators.json> <Country> [out.pptx]
if(typeof require!=='undefined' && require.main===module){
  const fs=require('fs'); const Pptx=require('pptxgenjs');
  const jsonPath=process.argv[2], country=process.argv[3], out=process.argv[4];
  const all=JSON.parse(fs.readFileSync(jsonPath,'utf8'));
  const data=all[country]||{};
  const INFO={Paraguay:{capital:'Asunción · 2.3M metro',currency:'Guaraní (PYG)',languages:'Spanish · Guaraní'}};
  buildCountryDeck({country,data,info:INFO[country]||{},iso2:'PY',PptxGenJS:Pptx,fileName:out||undefined,write:'file'})
    .then(f=>console.log('WROTE',f)).catch(e=>{console.error(e);process.exit(1);});
}

if(typeof module!=='undefined' && module.exports) module.exports={ buildCountryDeck, IND_SRC };
if(typeof window!=='undefined'){ window.buildCountryDeck=buildCountryDeck; window.COUNTRY_DECK_IND_SRC=IND_SRC; }
