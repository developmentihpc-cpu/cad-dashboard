/* region_deck.js — ODA regional needs-assessment deck (browser, pptxgenjs).
 *
 * One deck for a whole region: cover · regional snapshot · need ranking ·
 * comparison table · one profile slide per country · methodology & sources.
 * Same brand tokens as country_deck.js. Every figure carries source · year.
 *
 * opts:
 *   region    : display name (e.g. "Sub-Saharan Africa")
 *   countries : [{ name, iso2, income, flagData, need, needRank, data:{<WB id>:{value,year}} }]
 *               need = 0–100 need index (null if too little data); needRank = 1 = highest need
 *   dateStr   : "October 2026"
 *   dataNote  : sentence describing data freshness (live vs snapshot)
 *   PptxGenJS : constructor
 *   output    : 'blob' → resolve with a Blob; otherwise download as fileName
 */
'use strict';

function buildRegionDeck(opts){
  const INK='1D252C', GOLD='AD833B', GOLD_LT='C7A877', NAVY='333F64', SLATE='2F586E',
        SKY='CBDCE6', CREAM='F7F5EF', CARD='F4F5F7', PANEL='F1EEE6', GREEN='2F7F58',
        BORDEAUX='79242F', WHITE='FFFFFF', FG2='5B6A7E', FG3='8A96A4', BORDER='E2E2E2',
        SKYBAR='3E9BD6', HEAD='Lora', BODY='Montserrat';
  const SRC = (typeof window!=='undefined' && window.COUNTRY_DECK_IND_SRC) || {};
  const srcOf = id => SRC[id] || 'World Bank';

  const Pptx = opts.PptxGenJS || (typeof PptxGenJS!=='undefined' ? PptxGenJS : null);
  if(!Pptx) throw new Error('PptxGenJS constructor not provided');
  const region = opts.region || 'Region';
  const DATE = opts.dateStr || new Date().toLocaleDateString('en-US',{month:'long',year:'numeric'});
  const C = (opts.countries||[]).slice();
  if(!C.length) throw new Error('No countries supplied for '+region);

  // ── data helpers ──
  const gv = (c,id) => (c.data && c.data[id] && c.data[id].value!=null) ? c.data[id].value : null;
  const yr = (c,id) => (c.data && c.data[id] && c.data[id].year) ? String(c.data[id].year) : '';
  const cite = (c,id) => { const y=yr(c,id); return srcOf(id)+(y?' · '+y:''); };
  const fPop = v => v==null?'—':v>=1e9?(v/1e9).toFixed(2)+'B':v>=1e6?(v/1e6).toFixed(1)+'M':Math.round(v).toLocaleString();
  const fMil = v => v==null?'—':v>=1e9?(v/1e9).toFixed(1)+' billion':(v/1e6).toFixed(v>=1e8?0:1)+' million';
  const fN = (v,d=0,u='') => v==null?'—':(d?v.toFixed(d):Math.round(v).toLocaleString())+u;
  const median = arr => { const a=arr.filter(v=>v!=null).sort((x,y)=>x-y); if(!a.length) return null; const m=Math.floor(a.length/2); return a.length%2?a[m]:(a[m-1]+a[m])/2; };
  const trim=(s,n)=>{s=String(s==null?'':s);return s.length>n?s.slice(0,n-1)+'…':s;};

  // indicators shown per country; dir:+1 = higher is worse, -1 = lower is worse
  const IND = [
    { id:'SH.DYN.MORT',     lbl:'Under-5 mortality', unit:' /1k', d:0, dir:1,  sector:'Health',        th:[80,40,25] },
    { id:'SH.STA.MMRT',     lbl:'Maternal mortality', unit:' /100k', d:0, dir:1, sector:'Health',      th:[500,200,70] },
    { id:'SN.ITK.DEFC.ZS',  lbl:'Undernourishment',  unit:'%', d:1, dir:1,  sector:'Food security',    th:[25,15,7] },
    { id:'SH.H2O.BASW.ZS',  lbl:'Basic drinking water', unit:'%', d:0, dir:-1, sector:'WASH',           th:[60,75,90] },
    { id:'SH.STA.BASS.ZS',  lbl:'Basic sanitation',  unit:'%', d:0, dir:-1, sector:'WASH',             th:[40,60,85] },
    { id:'EG.ELC.ACCS.ZS',  lbl:'Electricity access', unit:'%', d:0, dir:-1, sector:'Energy',          th:[40,70,95] },
  ];
  const sev = (ind,v) => { if(v==null) return 3; const [a,b,c]=ind.th;
    return ind.dir>0 ? (v>a?0:v>b?1:v>c?2:3) : (v<a?0:v<b?1:v<c?2:3); };          // 0 severe … 3 good
  const SEV_FILL = ['F2D9DC','F6E6D0','F4F5F7','E3F0E8'], SEV_TXT=[BORDEAUX,'8A5A12',INK,GREEN];

  // ── regional aggregates ──
  const totPop = C.reduce((s,c)=>s+(gv(c,'SP.POP.TOTL')||0),0);
  const without = id => C.reduce((s,c)=>{ const p=gv(c,'SP.POP.TOTL'), v=gv(c,id); return (p&&v!=null)?s+p*(1-v/100):s; },0);
  const noElec=without('EG.ELC.ACCS.ZS'), noWater=without('SH.H2O.BASW.ZS'), noSan=without('SH.STA.BASS.ZS');
  const medU5 = median(C.map(c=>gv(c,'SH.DYN.MORT')));
  const medGdp = median(C.map(c=>gv(c,'NY.GDP.PCAP.PP.CD')));
  const lic = C.filter(c=>c.income==='LIC').length;
  const ranked = C.filter(c=>c.need!=null).sort((a,b)=>b.need-a.need);
  const u5Over40 = C.filter(c=>(gv(c,'SH.DYN.MORT')||0)>40).length;
  const meds = {}; IND.forEach(i=>meds[i.id]=median(C.map(c=>gv(c,i.id))));

  // ── deck ──
  const p = new Pptx();
  p.defineLayout({name:'W',width:13.333,height:7.5}); p.layout='W';
  p.title = `${region} — Regional Needs Assessment`; p.author='ODA Country Assessment Dashboard';
  let PAGE=0, TOTAL=0;
  const S=[];
  const eyebrow=(sl,t,x,y,w,col)=>sl.addText(String(t).toUpperCase(),{x,y,w,h:0.22,fontFace:BODY,fontSize:9,bold:true,color:col||GOLD,charSpacing:2.4});
  const head=(sl,eb,title,stmt)=>{ eyebrow(sl,eb,0.5,0.34,10,GOLD);
    sl.addText([{text:title,options:{bold:true,color:INK}},{text:stmt?'  —  '+stmt:'',options:{color:FG3}}],{x:0.5,y:0.58,w:12.3,h:0.5,fontFace:HEAD,fontSize:18,valign:'middle'}); };
  const foot=(sl,srcTxt,dark)=>{ PAGE++;
    const lc=dark?'4A5578':BORDER, tc=dark?'9AA7BD':FG3, oc=dark?GOLD_LT:NAVY;
    sl.addShape(p.ShapeType.line,{x:0.5,y:7.12,w:12.33,h:0,line:{color:lc,width:0.5}});
    sl.addText('Source: '+srcTxt,{x:0.5,y:7.17,w:9.5,h:0.22,fontFace:BODY,fontSize:8,color:tc,valign:'middle'});
    sl.addText([{text:'ODA',options:{bold:true,color:oc}},{text:'   '+String(PAGE).padStart(2,'0')+' / '+String(TOTAL).padStart(2,'0'),options:{color:tc}}],{x:10.5,y:7.17,w:2.33,h:0.22,fontFace:BODY,fontSize:8,align:'right',valign:'middle'}); };
  const card=(sl,x,y,w,h,val,lbl,sub,neg)=>{
    sl.addShape(p.ShapeType.rect,{x,y,w,h,fill:{color:CARD},line:{type:'none'}});
    sl.addShape(p.ShapeType.rect,{x,y,w,h:0.045,fill:{color:neg?BORDEAUX:GOLD},line:{type:'none'}});
    sl.addText(String(val),{x:x+0.16,y:y+0.12,w:w-0.3,h:0.46,fontFace:HEAD,fontSize:String(val).length>9?18:24,bold:true,color:neg?BORDEAUX:INK,valign:'middle'});
    sl.addText(lbl,{x:x+0.16,y:y+0.58,w:w-0.3,h:0.26,fontFace:BODY,fontSize:8.6,bold:true,color:INK,valign:'top',wrap:true});
    if(sub) sl.addText(sub,{x:x+0.16,y:y+h-0.27,w:w-0.3,h:0.2,fontFace:BODY,fontSize:7,color:FG3,valign:'top'}); };
  const bullets=(sl,items,x,y,w,col)=>{ let iy=y;
    items.forEach(t=>{ const lines=Math.max(1,Math.ceil(String(t).length/Math.max(40,w*11)));
      sl.addShape(p.ShapeType.rect,{x:x+0.02,y:iy+0.05,w:0.09,h:0.09,fill:{color:col||SLATE},line:{type:'none'}});
      sl.addText(t,{x:x+0.24,y:iy,w:w-0.24,h:0.21*lines+0.06,fontFace:BODY,fontSize:9.5,color:INK,valign:'top',wrap:true});
      iy+=0.21*lines+0.14; }); return iy; };

  // ══ COVER ══
  S.push(()=>{
    const sl=p.addSlide();
    sl.addShape(p.ShapeType.rect,{x:0,y:0,w:13.333,h:7.5,fill:{color:CREAM},line:{type:'none'}});
    sl.addShape(p.ShapeType.rect,{x:0,y:0,w:4.1,h:7.5,fill:{color:NAVY},line:{type:'none'}});
    sl.addText('REGIONAL ASSESSMENT',{x:0.45,y:0.7,w:3.4,h:0.3,fontFace:BODY,fontSize:9,bold:true,color:GOLD_LT,charSpacing:2.6});
    sl.addText(String(C.length),{x:0.45,y:1.4,w:3.4,h:0.9,fontFace:HEAD,fontSize:54,bold:true,color:WHITE});
    sl.addText('countries assessed',{x:0.45,y:2.25,w:3.4,h:0.3,fontFace:BODY,fontSize:11,color:SKY});
    [['Population',fPop(totPop)],['Low-income countries',String(lic)],['Median under-5 mortality',medU5!=null?Math.round(medU5)+' /1,000':'—'],['Median GDP / capita (PPP)',medGdp!=null?'$'+Math.round(medGdp).toLocaleString():'—']]
      .forEach(([l,v],i)=>{ const y=3.1+i*0.85;
        sl.addShape(p.ShapeType.line,{x:0.45,y:y-0.1,w:3.2,h:0,line:{color:'4A5578',width:0.5}});
        sl.addText(l.toUpperCase(),{x:0.45,y,w:3.2,h:0.22,fontFace:BODY,fontSize:7.5,bold:true,color:GOLD_LT,charSpacing:1.6});
        sl.addText(v,{x:0.45,y:y+0.22,w:3.2,h:0.4,fontFace:HEAD,fontSize:18,bold:true,color:WHITE}); });
    eyebrow(sl,'ODA · Regional needs assessment',4.7,1.2,8,GOLD);
    sl.addText(region,{x:4.65,y:1.55,w:8.2,h:1.6,fontFace:HEAD,fontSize:region.length>28?34:44,bold:true,color:INK,valign:'top',wrap:true});
    sl.addShape(p.ShapeType.rect,{x:4.7,y:3.3,w:0.9,h:0.04,fill:{color:GOLD},line:{type:'none'}});
    sl.addText('Development needs across '+C.length+' countries — health, food security, water & sanitation and energy — with a country-by-country profile.',{x:4.7,y:3.55,w:7.9,h:0.9,fontFace:BODY,fontSize:13,color:FG2,valign:'top',wrap:true});
    sl.addText(trim(C.map(c=>c.name).sort().join(' · '),520),{x:4.7,y:4.75,w:7.9,h:1.5,fontFace:BODY,fontSize:9,color:FG3,valign:'top',wrap:true});
    sl.addText(DATE+' · ODA Country Assessment Dashboard',{x:4.7,y:6.6,w:7.9,h:0.3,fontFace:BODY,fontSize:9,color:FG3});
    PAGE++;
  });

  // ══ REGIONAL SNAPSHOT ══
  S.push(()=>{
    const sl=p.addSlide(); sl.addShape(p.ShapeType.rect,{x:0,y:0,w:13.333,h:7.5,fill:{color:WHITE},line:{type:'none'}});
    head(sl,region+' · regional snapshot','At a Glance','the scale of unmet basic needs across the region');
    const cw=2.9, gap=0.2, y=1.45;
    card(sl,0.5,y,cw,1.25,fPop(totPop),'People in the region','World Bank · latest year');
    card(sl,0.5+(cw+gap),y,cw,1.25,fMil(noElec),'Without electricity','Estimated from national access rates',true);
    card(sl,0.5+2*(cw+gap),y,cw,1.25,fMil(noWater),'Without basic drinking water','Estimated from national access rates',true);
    card(sl,0.5+3*(cw+gap),y,cw,1.25,fMil(noSan),'Without basic sanitation','Estimated from national access rates',true);
    eyebrow(sl,'Key insights',0.5,3.05,6,SLATE);
    const top3 = ranked.slice(0,3).map(c=>c.name);
    const ins = [
      top3.length?`Highest need on the ODA need index: ${top3.join('; ')}${/\.$/.test(top3[top3.length-1])?'':'.'}`:'Not enough data to rank countries by need.',
      `${u5Over40} of ${C.length} countries have under-5 mortality above 40 per 1,000 live births (SDG target: 25).`,
      medU5!=null?`The regional median under-5 mortality is ${Math.round(medU5)} per 1,000; the median GDP per capita (PPP) is ${medGdp!=null?'$'+Math.round(medGdp).toLocaleString():'not available'}.`:'Under-5 mortality data is limited for this region.',
      `${lic} of ${C.length} countries are classified low-income by the World Bank.`,
    ];
    bullets(sl,ins,0.5,3.38,7.2);
    // right: sector severity count
    const RX=8.2, RW=4.6; eyebrow(sl,'Countries in severe or weak position',RX,3.05,RW,SLATE);
    IND.forEach((ind,i)=>{
      const vals=C.map(c=>sev(ind,gv(c,ind.id)));
      const bad=vals.filter(s=>s<=1).length, have=C.filter(c=>gv(c,ind.id)!=null).length;
      const ry=3.42+i*0.55;
      sl.addText(ind.lbl,{x:RX,y:ry,w:RW,h:0.2,fontFace:BODY,fontSize:8.6,bold:true,color:FG2});
      sl.addShape(p.ShapeType.rect,{x:RX,y:ry+0.22,w:RW,h:0.22,fill:{color:'ECEFF2'},line:{type:'none'}});
      if(have&&bad) sl.addShape(p.ShapeType.rect,{x:RX,y:ry+0.22,w:Math.max(0.05,RW*bad/C.length),h:0.22,fill:{color:BORDEAUX},line:{type:'none'}});
      sl.addText(`${bad} of ${have}`,{x:RX+RW-1.2,y:ry+0.22,w:1.14,h:0.22,fontFace:BODY,fontSize:8,bold:true,color:INK,align:'right',valign:'middle'});
    });
    foot(sl,'World Bank Open Data, WHO/UNICEF JMP, FAO, UN IGME · '+DATE);
  });

  // ══ NEED RANKING (bars, up to 18 per slide) ══
  const PER_RANK=18;
  for(let s=0;s<Math.max(1,Math.ceil(ranked.length/PER_RANK));s++){
    const part=ranked.slice(s*PER_RANK,(s+1)*PER_RANK);
    S.push(()=>{
      const sl=p.addSlide(); sl.addShape(p.ShapeType.rect,{x:0,y:0,w:13.333,h:7.5,fill:{color:WHITE},line:{type:'none'}});
      head(sl,region+' · need ranking'+(ranked.length>PER_RANK?` (${s+1}/${Math.ceil(ranked.length/PER_RANK)})`:''),'Where Needs Are Greatest','ODA need index, 0 (lowest) – 100 (highest)');
      if(!part.length){ sl.addText('Not enough indicator data to rank these countries.',{x:0.5,y:3,w:12.3,h:0.5,fontFace:BODY,fontSize:12,color:FG3,align:'center'}); }
      const top=1.4, rowH=Math.min(0.31,5.4/Math.max(part.length,1)), LX=0.5, NW=2.6, BX=LX+NW+0.5, BW=8.3;
      part.forEach((c,i)=>{ const y=top+i*rowH, rank=s*PER_RANK+i+1;
        sl.addText(String(rank),{x:LX,y,w:0.4,h:rowH,fontFace:BODY,fontSize:9,bold:true,color:FG3,valign:'middle'});
        sl.addText(c.name,{x:LX+0.4,y,w:NW,h:rowH,fontFace:BODY,fontSize:9.5,bold:true,color:INK,valign:'middle'});
        sl.addShape(p.ShapeType.rect,{x:BX,y:y+rowH*0.18,w:BW,h:rowH*0.64,fill:{color:'EEF4F8'},line:{type:'none'}});
        sl.addShape(p.ShapeType.rect,{x:BX,y:y+rowH*0.18,w:Math.max(0.05,BW*c.need/100),h:rowH*0.64,fill:{color:rank<=5?GOLD:SKYBAR},line:{type:'none'}});
        sl.addText(String(Math.round(c.need)),{x:BX+BW+0.08,y,w:0.6,h:rowH,fontFace:BODY,fontSize:9,bold:true,color:INK,valign:'middle'});
      });
      foot(sl,'ODA need index from World Bank / WHO / UNICEF / FAO indicators — see Methodology · '+DATE);
    });
  }

  // ══ COMPARISON TABLE (14 rows per slide) ══
  const PER_TBL=14, byName=C.slice().sort((a,b)=>(b.need==null?-1:b.need)-(a.need==null?-1:a.need));
  for(let s=0;s<Math.ceil(byName.length/PER_TBL);s++){
    const part=byName.slice(s*PER_TBL,(s+1)*PER_TBL);
    S.push(()=>{
      const sl=p.addSlide(); sl.addShape(p.ShapeType.rect,{x:0,y:0,w:13.333,h:7.5,fill:{color:WHITE},line:{type:'none'}});
      head(sl,region+' · country comparison'+(byName.length>PER_TBL?` (${s+1}/${Math.ceil(byName.length/PER_TBL)})`:''),'Side by Side','colour shows severity against SDG-linked thresholds');
      const hdr=['Country','Population','GDP/cap PPP',...IND.map(i=>i.lbl),'Need'].map(t=>({text:t,options:{bold:true,color:WHITE,fill:{color:NAVY},fontSize:8,align:'center',valign:'middle'}}));
      const rows=[hdr];
      part.forEach(c=>{
        const r=[{text:c.name,options:{bold:true,color:INK,align:'left'}},
                 {text:fPop(gv(c,'SP.POP.TOTL'))},
                 {text:gv(c,'NY.GDP.PCAP.PP.CD')!=null?'$'+Math.round(gv(c,'NY.GDP.PCAP.PP.CD')).toLocaleString():'—'}];
        IND.forEach(ind=>{ const v=gv(c,ind.id), sv=sev(ind,v);
          r.push({text:v==null?'—':fN(v,ind.d,ind.unit.trim()==='%'?'%':''),options:{fill:{color:v==null?WHITE:SEV_FILL[sv]},color:v==null?FG3:SEV_TXT[sv],bold:sv<=1}}); });
        r.push({text:c.need==null?'—':String(Math.round(c.need)),options:{bold:true,color:c.needRank&&c.needRank<=5?'8A5A12':INK}});
        rows.push(r);
      });
      sl.addTable(rows,{x:0.5,y:1.35,w:12.33,colW:[2.0,1.05,1.15,1.25,1.25,1.25,1.25,1.25,1.25,0.63],fontFace:BODY,fontSize:8.4,color:INK,align:'center',valign:'middle',rowH:0.36,border:{type:'solid',color:'E2E2E2',pt:0.5}});
      sl.addText('Under-5 mortality per 1,000 live births · maternal mortality per 100,000 live births · access indicators are % of population.',{x:0.5,y:6.78,w:12.3,h:0.24,fontFace:BODY,fontSize:7.5,color:FG3});
      foot(sl,'World Bank Open Data · UN IGME · WHO · FAO · WHO/UNICEF JMP · IEA · '+DATE);
    });
  }

  // ══ COUNTRY PROFILES (one slide each, ordered by need) ══
  byName.forEach(c=>{
    S.push(()=>{
      const sl=p.addSlide(); sl.addShape(p.ShapeType.rect,{x:0,y:0,w:13.333,h:7.5,fill:{color:WHITE},line:{type:'none'}});
      eyebrow(sl,region+' · country profile',0.5,0.34,8,GOLD);
      let tx=0.5;
      if(c.flagData){ try{ sl.addImage({data:c.flagData,x:0.5,y:0.66,w:0.6,h:0.4}); tx=1.25; }catch(e){} }
      sl.addText(c.name,{x:tx,y:0.58,w:8,h:0.55,fontFace:HEAD,fontSize:24,bold:true,color:INK,valign:'middle'});
      const tag=[c.income?({LIC:'Low income',LMIC:'Lower-middle income',UMIC:'Upper-middle income'}[c.income]||c.income):null,
                 gv(c,'SP.POP.TOTL')!=null?'Population '+fPop(gv(c,'SP.POP.TOTL')):null].filter(Boolean).join(' · ');
      sl.addText(tag,{x:tx,y:1.1,w:8,h:0.26,fontFace:BODY,fontSize:10,color:FG2});
      // need badge
      sl.addShape(p.ShapeType.rect,{x:10.33,y:0.5,w:2.5,h:0.9,fill:{color:c.needRank&&c.needRank<=5?'F6EED9':'EEF4F8'},line:{type:'none'}});
      sl.addText('NEED INDEX',{x:10.45,y:0.56,w:2.3,h:0.2,fontFace:BODY,fontSize:7.5,bold:true,color:FG2,charSpacing:1.6});
      sl.addText(c.need==null?'—':String(Math.round(c.need)),{x:10.45,y:0.76,w:1.0,h:0.55,fontFace:HEAD,fontSize:26,bold:true,color:INK,valign:'middle'});
      sl.addText(c.needRank?`rank ${c.needRank} of ${ranked.length}`:'not ranked',{x:11.35,y:0.86,w:1.4,h:0.35,fontFace:BODY,fontSize:9,color:FG2,valign:'middle'});
      // stat cards 3×2
      const cw=2.25, ch=1.12, gx=0.16, gy=0.16, X0=0.5, Y0=1.6;
      IND.forEach((ind,i)=>{ const v=gv(c,ind.id), sv=sev(ind,v);
        card(sl,X0+(i%3)*(cw+gx),Y0+Math.floor(i/3)*(ch+gy),cw,ch,v==null?'—':fN(v,ind.d,ind.unit),ind.lbl,v==null?'No recent data':cite(c,ind.id),v!=null&&sv<=1); });
      // insights vs regional median
      const gaps=IND.map(ind=>{ const v=gv(c,ind.id), m=meds[ind.id]; if(v==null||m==null) return null;
          const worse = ind.dir>0 ? v/(m||1) : (100-v)/Math.max(1,100-m);
          return { ind, v, m, worse }; }).filter(Boolean).sort((a,b)=>b.worse-a.worse);
      const RX=7.85, RW=4.98;
      eyebrow(sl,'Compared with the regional median',RX,1.6,RW,SLATE);
      const lines=gaps.slice(0,3).map(g=>{ const better=g.worse<0.95, same=g.worse>=0.95&&g.worse<=1.05;
        const val=fN(g.v,g.ind.d,g.ind.unit), med=fN(g.m,g.ind.d,g.ind.unit);
        return `${g.ind.lbl}: ${val} — ${same?'close to':better?'better than':'worse than'} the regional median (${med}).`; });
      const endY = bullets(sl,lines.length?lines:['Not enough data to compare with the region.'],RX,1.92,RW);
      // priority sectors
      const sectors=[]; gaps.filter(g=>g.worse>1.05||sev(g.ind,g.v)<=1).forEach(g=>{ if(!sectors.includes(g.ind.sector)) sectors.push(g.ind.sector); });
      const PY=Math.max(endY+0.15,4.3);
      sl.addShape(p.ShapeType.rect,{x:RX,y:PY,w:RW,h:1.35,fill:{color:PANEL},line:{type:'none'}});
      sl.addShape(p.ShapeType.rect,{x:RX,y:PY,w:0.06,h:1.35,fill:{color:GOLD},line:{type:'none'}});
      eyebrow(sl,'Priority sectors from the data',RX+0.2,PY+0.12,RW-0.3,GOLD);
      sl.addText(sectors.length?sectors.slice(0,3).join('  ·  '):'No sector stands out against the region',{x:RX+0.2,y:PY+0.45,w:RW-0.35,h:0.5,fontFace:HEAD,fontSize:sectors.length?16:11,bold:!!sectors.length,color:INK,valign:'middle'});
      sl.addText('Indicative — based on national indicators only; confirm with a full country assessment.',{x:RX+0.2,y:PY+0.95,w:RW-0.35,h:0.3,fontFace:BODY,fontSize:7.5,color:FG3,valign:'top'});
      foot(sl,IND.map(i=>srcOf(i.id)).filter((v,i,a)=>a.indexOf(v)===i).slice(0,4).join(' · ')+' · '+DATE);
    });
  });

  // ══ METHODOLOGY & SOURCES ══
  S.push(()=>{
    const sl=p.addSlide(); sl.addShape(p.ShapeType.rect,{x:0,y:0,w:13.333,h:7.5,fill:{color:NAVY},line:{type:'none'}});
    sl.addText('REGIONAL ASSESSMENT',{x:0.6,y:0.7,w:8,h:0.3,fontFace:BODY,fontSize:10,bold:true,color:GOLD_LT,charSpacing:2.6});
    sl.addText(region,{x:0.57,y:1.0,w:12,h:0.9,fontFace:HEAD,fontSize:36,bold:true,color:WHITE});
    sl.addShape(p.ShapeType.rect,{x:0.6,y:2.0,w:0.9,h:0.03,fill:{color:GOLD},line:{type:'none'}});
    sl.addText('METHODOLOGY',{x:0.6,y:2.3,w:11,h:0.3,fontFace:BODY,fontSize:11,bold:true,color:GOLD_LT,charSpacing:2});
    sl.addText('The ODA need index combines six indicators: under-5 mortality, maternal mortality, undernourishment, and the share of people without basic drinking water, basic sanitation and electricity. Each is scaled 0–100 across all countries tracked by the dashboard and averaged (a country needs at least four of the six to be ranked). "People without access" figures multiply national access rates by population and are estimates. Severity colours use SDG-linked thresholds.',{x:0.6,y:2.65,w:12,h:1.4,fontFace:BODY,fontSize:10.5,color:'EAF0F4',valign:'top',wrap:true});
    sl.addText('SOURCES & DATA',{x:0.6,y:4.25,w:11,h:0.3,fontFace:BODY,fontSize:11,bold:true,color:GOLD_LT,charSpacing:2});
    sl.addText('World Bank Open Data · UN IGME (UNICEF/WHO) · WHO · FAO · WHO/UNICEF JMP · IEA. '+(opts.dataNote||'')+' Each figure on the profile slides carries its source and reference year; missing values are shown as "—" rather than estimated.',{x:0.6,y:4.6,w:12,h:1.2,fontFace:BODY,fontSize:10.5,color:'EAF0F4',valign:'top',wrap:true});
    sl.addText('Retrieved '+DATE+' · ODA Country Assessment Dashboard',{x:0.6,y:6.5,w:11,h:0.3,fontFace:BODY,fontSize:9,color:FG3});
    foot(sl,'World Bank Open Data (retrieved '+DATE+') + originating agencies',true);
  });

  TOTAL=S.length;
  S.forEach(fn=>fn());
  if (opts.output === 'blob') return p.write({ outputType:'blob' });
  return p.writeFile({ fileName: opts.fileName || `${region.replace(/[^\w]+/g,'_')}_Regional_Assessment.pptx` });
}

if(typeof window!=='undefined'){ window.buildRegionDeck=buildRegionDeck; }
if(typeof module!=='undefined' && module.exports) module.exports={ buildRegionDeck };
