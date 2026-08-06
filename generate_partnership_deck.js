#!/usr/bin/env node
/* generate_partnership_deck.js — the canonical partnership-evaluation deck generator.
 * Data-driven 5-slide ODA leadership deck (16:9 PPTX). Reads an evaluation data model
 * (JSON) and renders the standard format. Empty-inputs guard: if any of
 * {sector, cost, beneficiaries, duration} is missing, merit renders PROVISIONAL and the
 * ask renders as scoping-approval — never "Reject". Rubric/weights are unchanged upstream;
 * this only changes how results are communicated.
 *
 *   node generate_partnership_deck.js [dataModel.json] [out.pptx]
 */
const pptxgen = require("pptxgenjs");
const fs = require("fs");

const dataPath = process.argv[2] || "_sample_ecw.json";
const outPath  = process.argv[3] || "ECW_UAE_Leadership_Deck.pptx";
const D = JSON.parse(fs.readFileSync(dataPath, "utf-8"));

const INK="1D252C", INKD="101820", GOLD="AD833B", BLUE="678CA5", DBLUE="2F586E",
      SKY="CBDCE6", BORDEAUX="79242F", WHITE="FFFFFF", WASH="F4F5F7",
      DIV="E2E2E2", MUTE="5A6670", GREEN="3D6B52", GOLDc="AD833B";
const C={GREEN,DBLUE,BORDEAUX,GOLD,MUTE,INK}; // colour-name lookup for data
const LORA="Lora", MONT="Montserrat";
const W=13.333, H=7.5, M=0.6;

/* ---- empty-inputs guard (the point of the change) ---- */
const p=D.project||{};
const provisional = !(String(p.sector||"").trim() && String(p.cost||"").trim() && String(p.ben||"").trim() && String(p.dur||"").trim());
const meritScore = Math.round((D.scores&&D.scores.merit&&D.scores.merit.score)||0);
const meritDisp = provisional ? (meritScore>0 ? "~"+meritScore : "Provisional") : String(meritScore);
const meritVerdict = provisional ? "Provisional — project undefined"
  : (meritScore>=75?"Strong":meritScore>=55?"Moderate":"Weak");
const ask = provisional ? (D.askScoping||D.askDefined||"") : (D.askDefined||D.askScoping||"");

const pres = new pptxgen();
pres.layout="LAYOUT_WIDE"; pres.author="ODA"; pres.title=(D.partnerShort||D.partner||"Partnership")+" — UAE Partnership Decision";

function rule(s,x,y,w=56/96){ s.addShape(pres.shapes.RECTANGLE,{x,y,w,h:2/96,fill:{color:GOLD},line:{type:"none"}}); }
function header(s,ey,t){ s.background={color:WHITE};
  s.addText(ey.toUpperCase(),{x:M,y:0.4,w:W-2*M,h:0.26,fontFace:MONT,fontSize:10.5,bold:true,color:GOLD,charSpacing:3,margin:0});
  s.addText(t,{x:M,y:0.66,w:W-2*M,h:0.58,fontFace:LORA,fontSize:28,bold:true,color:INK,margin:0});
  rule(s,M,1.36); }
function foot(s,n){ s.addText(D.footers&&D.footers[n]||"",{x:M,y:7.04,w:W-2*M-0.5,h:0.3,fontFace:MONT,fontSize:8,color:MUTE,margin:0});
  s.addText(String(n),{x:W-M-0.3,y:7.04,w:0.3,h:0.3,fontFace:MONT,fontSize:9,color:MUTE,align:"right",margin:0}); }
function chip(s,x,y,w,label,val,verdict,vcolor){
  s.addShape(pres.shapes.RECTANGLE,{x,y,w,h:1.15,fill:{color:WASH},line:{type:"none"}});
  s.addText(label.toUpperCase(),{x:x+0.18,y:y+0.13,w:w-0.36,h:0.22,fontFace:MONT,fontSize:8.5,bold:true,color:MUTE,charSpacing:1.5,margin:0});
  s.addText(String(val),{x:x+0.18,y:y+0.34,w:w-0.36,h:0.5,fontFace:LORA,fontSize:30,bold:true,color:INK,margin:0});
  s.addText(verdict,{x:x+0.18,y:y+0.86,w:w-0.36,h:0.24,fontFace:MONT,fontSize:9.5,bold:true,color:vcolor,margin:0,valign:"top"});
}
const bullets=(arr)=>arr.map((t,i)=>({text:t,options:{bullet:{code:"2022",indent:10},breakLine:i<arr.length-1}}));

/* ===== Slide 1 — THE DECISION ===== */
let s=pres.addSlide();
header(s,"For leadership · "+(D.date||""), (D.partnerShort||D.partner)+" partnership — the decision");
s.addShape(pres.shapes.RECTANGLE,{x:M,y:1.5,w:W-2*M,h:0.92,fill:{color:INKD},line:{type:"none"}});
s.addText([{text:"THE ASK   ",options:{bold:true,color:GOLD,fontSize:11}},{text:ask,options:{color:SKY,fontSize:12}}],
  {x:M+0.28,y:1.52,w:W-2*M-0.56,h:0.84,fontFace:MONT,margin:0,lineSpacingMultiple:1.08,valign:"middle",fit:"shrink"});
const cw=(W-2*M-2*0.3)/3;
chip(s,M,2.62,cw,"Partner soundness",Math.round(D.scores.partner.score),D.scores.partner.verdict,GREEN);
chip(s,M+cw+0.3,2.62,cw,"UAE strategic value",Math.round(D.scores.uae.score),D.scores.uae.verdict,DBLUE);
chip(s,M+2*(cw+0.3),2.62,cw,"Project merit",meritDisp,meritVerdict,provisional?BORDEAUX:GREEN);
const colW=(W-2*M-0.3)/2, fy=4.0, fh=1.78;
s.addShape(pres.shapes.RECTANGLE,{x:M,y:fy,w:colW,h:fh,fill:{color:WASH},line:{color:DIV,width:0.75}});
s.addText("WHY PROCEED",{x:M+0.22,y:fy+0.14,w:colW-0.44,h:0.24,fontFace:MONT,fontSize:11,bold:true,color:GREEN,charSpacing:1.5,margin:0});
s.addText(bullets(D.whyProceed),{x:M+0.22,y:fy+0.44,w:colW-0.44,h:fh-0.55,fontFace:MONT,fontSize:9.4,color:INK,margin:0,paraSpaceAfter:5,lineSpacingMultiple:1.04,valign:"top",fit:"shrink"});
const ax=M+colW+0.3;
s.addShape(pres.shapes.RECTANGLE,{x:ax,y:fy,w:colW,h:fh,fill:{color:WHITE},line:{color:DIV,width:0.75}});
s.addText("WHY HOLD BACK",{x:ax+0.22,y:fy+0.14,w:colW-0.44,h:0.24,fontFace:MONT,fontSize:11,bold:true,color:BORDEAUX,charSpacing:1.5,margin:0});
s.addText(bullets(D.whyHold),{x:ax+0.22,y:fy+0.44,w:colW-0.44,h:fh-0.55,fontFace:MONT,fontSize:9.4,color:INK,margin:0,paraSpaceAfter:5,lineSpacingMultiple:1.04,valign:"top",fit:"shrink"});
s.addShape(pres.shapes.RECTANGLE,{x:M,y:5.95,w:W-2*M,h:0.82,fill:{color:SKY,transparency:78},line:{color:DIV,width:0.75}});
s.addText([{text:"TOP RISK · "+(D.topRisk.level||"")+"   ",options:{bold:true,color:BORDEAUX,fontSize:10}},
  {text:(D.topRisk.risk||"")+"   ",options:{color:INK,fontSize:10}},
  {text:"Mitigation: ",options:{bold:true,color:INK,fontSize:10}},
  {text:(D.topRisk.mitigation||""),options:{color:INK,fontSize:10}}],
  {x:M+0.24,y:6.02,w:W-2*M-0.48,h:0.68,fontFace:MONT,margin:0,lineSpacingMultiple:1.1,valign:"middle",fit:"shrink"});
foot(s,"1");

/* ===== Slide 2 — THE PROJECT ===== */
s=pres.addSlide();
header(s,"The project", provisional?"What it is — and what isn't yet decided":"The defined project");
const pw=(W-2*M-0.3)/2;
s.addShape(pres.shapes.RECTANGLE,{x:M,y:1.55,w:pw,h:2.05,fill:{color:WASH},line:{type:"none"}});
s.addText("DEFINED",{x:M+0.22,y:1.68,w:pw-0.44,h:0.24,fontFace:MONT,fontSize:10.5,bold:true,color:GREEN,charSpacing:1.5,margin:0});
let dy=2.0;
(D.defined||[]).forEach(([k,v])=>{ s.addText(k.toUpperCase(),{x:M+0.22,y:dy,w:2.0,h:0.3,fontFace:MONT,fontSize:8.5,bold:true,color:MUTE,margin:0});
  s.addText(v,{x:M+2.25,y:dy,w:pw-2.45,h:0.34,fontFace:MONT,fontSize:10,color:INK,margin:0,lineSpacingMultiple:1.05}); dy+=0.4; });
if(provisional){
  s.addShape(pres.shapes.RECTANGLE,{x:M+pw+0.3,y:1.55,w:pw,h:2.05,fill:{color:WHITE},line:{color:BORDEAUX,width:1}});
  s.addText("NOT YET DEFINED — LEADERSHIP MUST SUPPLY",{x:M+pw+0.52,y:1.68,w:pw-0.44,h:0.24,fontFace:MONT,fontSize:10.5,bold:true,color:BORDEAUX,charSpacing:1,margin:0});
  s.addText(bullets(D.mustSupply),{x:M+pw+0.52,y:2.02,w:pw-0.7,h:1.5,fontFace:MONT,fontSize:10.5,color:INK,margin:0,paraSpaceAfter:5,lineSpacingMultiple:1.05});
  s.addShape(pres.shapes.RECTANGLE,{x:M,y:3.85,w:W-2*M,h:0.62,fill:{color:INKD},line:{type:"none"}});
  s.addText([{text:"PROVISIONAL MERIT  ",options:{bold:true,color:GOLD,fontSize:10.5}},
    {text:"Indicative only"+(meritScore>0?(" ("+meritDisp+"/100)"):"")+". Four core inputs are undefined, so this is a direction-of-travel signal, not a scored project. ",options:{color:WHITE,fontSize:10.5}},
    {text:"This is a go/no-go on developing a proposal — not yet on the contribution itself.",options:{italic:true,color:SKY,fontSize:10.5}}],
    {x:M+0.26,y:3.91,w:W-2*M-0.52,h:0.5,fontFace:MONT,margin:0,lineSpacingMultiple:1.08,valign:"middle"});
} else {
  s.addShape(pres.shapes.RECTANGLE,{x:M+pw+0.3,y:1.55,w:pw,h:2.05,fill:{color:WASH},line:{type:"none"}});
  s.addText("SCOPE & OUTCOMES",{x:M+pw+0.52,y:1.68,w:pw-0.44,h:0.24,fontFace:MONT,fontSize:10.5,bold:true,color:GREEN,charSpacing:1.5,margin:0});
  const sc=[["Sector",p.sector],["Cost",p.cost],["Beneficiaries",p.ben],["Duration",p.dur]]; let sy=2.0;
  sc.forEach(([k,v])=>{ s.addText(k.toUpperCase(),{x:M+pw+0.52,y:sy,w:2.0,h:0.3,fontFace:MONT,fontSize:8.5,bold:true,color:MUTE,margin:0});
    s.addText(String(v||"—"),{x:M+pw+2.55,y:sy,w:pw-2.25,h:0.34,fontFace:MONT,fontSize:10,color:INK,margin:0}); sy+=0.4; });
  s.addShape(pres.shapes.RECTANGLE,{x:M,y:3.85,w:W-2*M,h:0.62,fill:{color:INKD},line:{type:"none"}});
  s.addText([{text:"PROJECT MERIT  ",options:{bold:true,color:GOLD,fontSize:10.5}},
    {text:meritScore+"/100 — assessed against the full ODA criteria with the inputs supplied.",options:{color:WHITE,fontSize:10.5}}],
    {x:M+0.26,y:3.91,w:W-2*M-0.52,h:0.5,fontFace:MONT,margin:0,valign:"middle"});
}
s.addText((provisional?"DIMENSION BREAKDOWN — PROVISIONAL, PENDING DEFINITION":"DIMENSION BREAKDOWN"),{x:M,y:4.66,w:9,h:0.24,fontFace:MONT,fontSize:9,bold:true,color:DBLUE,charSpacing:1.5,margin:0});
const dcw=(W-2*M-3*0.25)/4;
(D.dims||[]).forEach(([k,v],i)=>{ const x=M+(i%4)*(dcw+0.25), y=5.0+Math.floor(i/4)*0.72;
  s.addShape(pres.shapes.RECTANGLE,{x,y,w:dcw,h:0.6,fill:{color:WASH},line:{type:"none"}});
  s.addText(k,{x:x+0.16,y:y+0.1,w:dcw-0.7,h:0.4,fontFace:MONT,fontSize:9,color:INK,margin:0,valign:"middle"});
  s.addText(v,{x:x+dcw-0.72,y:y+0.1,w:0.62,h:0.4,fontFace:LORA,fontSize:12,bold:true,color:DBLUE,align:"right",margin:0,valign:"middle"}); });
foot(s,"2");

/* ===== Slide 3 — PARTNER OVERVIEW ===== */
s=pres.addSlide();
header(s,"The partner",(D.partner)+" — sound vehicle ("+Math.round(D.scores.partner.score)+"/100)");
s.addText(D.partnerSummary||"",{x:M,y:1.5,w:W-2*M,h:0.5,fontFace:MONT,fontSize:11.5,italic:true,color:DBLUE,margin:0,lineSpacingMultiple:1.12});
const scw=(W-2*M-0.3)/2, sch=1.34;
(D.partnerSubs||[]).forEach(([t,v,cn,d],i)=>{ const x=M+(i%2)*(scw+0.3), y=2.15+Math.floor(i/2)*(sch+0.25); const c=C[cn]||DBLUE;
  s.addShape(pres.shapes.RECTANGLE,{x,y,w:scw,h:sch,fill:{color:WASH},line:{type:"none"}});
  s.addText(String(v),{x:x+0.2,y:y+0.18,w:1.0,h:0.7,fontFace:LORA,fontSize:30,bold:true,color:c,margin:0,valign:"middle"});
  s.addText(t,{x:x+1.25,y:y+0.16,w:scw-1.45,h:0.28,fontFace:MONT,fontSize:12,bold:true,color:INK,margin:0});
  s.addText(d,{x:x+1.25,y:y+0.46,w:scw-1.45,h:0.8,fontFace:MONT,fontSize:9.5,color:MUTE,margin:0,lineSpacingMultiple:1.08,fit:"shrink"}); });
s.addText("RISK PROFILE",{x:M,y:5.4,w:9,h:0.24,fontFace:MONT,fontSize:9,bold:true,color:DBLUE,charSpacing:1.5,margin:0});
const rcw=(W-2*M-3*0.22)/4;
(D.partnerRisks||[]).forEach(([lvl,cn,d],i)=>{ const x=M+i*(rcw+0.22), y=5.7; const c=C[cn]||MUTE;
  s.addShape(pres.shapes.RECTANGLE,{x,y,w:rcw,h:0.95,fill:{color:WHITE},line:{color:DIV,width:0.75}});
  s.addText(lvl,{x:x+0.16,y:y+0.12,w:rcw-0.32,h:0.24,fontFace:MONT,fontSize:10,bold:true,color:c,charSpacing:1,margin:0});
  s.addText(d,{x:x+0.16,y:y+0.36,w:rcw-0.32,h:0.52,fontFace:MONT,fontSize:8.8,color:INK,margin:0,lineSpacingMultiple:1.05}); });
foot(s,"3");

/* ===== Slide 4 — FUNDING SCENARIOS & MILESTONES ===== */
s=pres.addSlide();
header(s,"Funding scenarios","What each level buys — and the milestone gates");
const bx=[M,2.5,7.2,9.7], by0=1.62;
[["BAND",bx[0],1.8],["WHAT IT UNLOCKS",bx[1],4.5],["MARGINAL VALUE",bx[2],2.3],["INFLUENCE",bx[3],W-M-bx[3]]].forEach(([h,x,w])=>
  s.addText(h,{x,y:by0,w,h:0.22,fontFace:MONT,fontSize:9,bold:true,color:MUTE,charSpacing:1.5,margin:0}));
s.addShape(pres.shapes.LINE,{x:M,y:by0+0.28,w:W-2*M,h:0,line:{color:INK,width:1}});
let yb=2.02;
(D.bands||[]).forEach(([b,u,m,inf,rec])=>{ const rh=1.18;
  if(rec){ s.addShape(pres.shapes.RECTANGLE,{x:M-0.05,y:yb-0.06,w:W-2*M+0.1,h:rh,fill:{color:WASH},line:{type:"none"}});
    s.addText("★ RECOMMENDED",{x:W-M-1.7,y:yb-0.02,w:1.7,h:0.2,fontFace:MONT,fontSize:7.5,bold:true,color:GOLD,align:"right",charSpacing:1,margin:0}); }
  s.addText(b,{x:bx[0],y:yb+0.04,w:1.8,h:0.4,fontFace:LORA,fontSize:16,bold:true,color:rec?INK:MUTE,margin:0});
  s.addText(u,{x:bx[1],y:yb+0.02,w:4.5,h:1.05,fontFace:MONT,fontSize:9,color:INK,margin:0,lineSpacingMultiple:1.05,fit:"shrink"});
  s.addText(m,{x:bx[2],y:yb+0.02,w:2.3,h:1.05,fontFace:MONT,fontSize:9,color:MUTE,margin:0,lineSpacingMultiple:1.05,fit:"shrink"});
  s.addText(inf,{x:bx[3],y:yb+0.02,w:W-M-bx[3],h:1.05,fontFace:MONT,fontSize:9,color:INK,margin:0,lineSpacingMultiple:1.05,fit:"shrink"}); yb+=rh+0.06; });
s.addText("PHASING — RELEASE CONDITIONED ON THESE MILESTONES",{x:M,y:5.62,w:11,h:0.24,fontFace:MONT,fontSize:9.5,bold:true,color:DBLUE,charSpacing:1.5,margin:0});
const mw=(W-2*M-4*0.2)/5;
(D.milestones||[]).slice(0,5).forEach((t,i)=>{ const x=M+i*(mw+0.2), y=5.92;
  s.addShape(pres.shapes.RECTANGLE,{x,y,w:mw,h:0.92,fill:{color:WHITE},line:{color:DIV,width:0.75}});
  s.addText(String(i+1),{x:x+0.14,y:y+0.1,w:0.4,h:0.3,fontFace:LORA,fontSize:15,bold:true,color:GOLD,margin:0});
  s.addText(t,{x:x+0.14,y:y+0.4,w:mw-0.28,h:0.48,fontFace:MONT,fontSize:7.6,color:INK,margin:0,lineSpacingMultiple:1.02}); });
foot(s,"4");

/* ===== Slide 5 — STRATEGIC CONTEXT ===== */
s=pres.addSlide();
header(s,"Strategic context","Why act now — the positional case");
s.addText(D.strategicLead||"",{x:M,y:1.5,w:W-2*M,h:0.62,fontFace:MONT,fontSize:12.5,color:INK,margin:0,lineSpacingMultiple:1.13,fit:"shrink"});
s.addText("UAE PRECEDENTS IN EDUCATION FINANCING",{x:M,y:2.3,w:9,h:0.24,fontFace:MONT,fontSize:9,bold:true,color:DBLUE,charSpacing:1.5,margin:0});
const prw=(W-2*M-2*0.3)/3;
(D.precedents||[]).slice(0,3).forEach(([n,d],i)=>{ const x=M+i*(prw+0.3), y=2.62;
  s.addShape(pres.shapes.RECTANGLE,{x,y,w:prw,h:1.2,fill:{color:WASH},line:{type:"none"}});
  s.addText(n,{x:x+0.2,y:y+0.16,w:prw-0.4,h:0.45,fontFace:LORA,fontSize:22,bold:true,color:INK,margin:0});
  s.addText(d,{x:x+0.2,y:y+0.62,w:prw-0.4,h:0.5,fontFace:MONT,fontSize:9,color:MUTE,margin:0,lineSpacingMultiple:1.08}); });
s.addText("THE POSITIONAL SEQUENCE",{x:M,y:4.1,w:9,h:0.24,fontFace:MONT,fontSize:9,bold:true,color:DBLUE,charSpacing:1.5,margin:0});
const sqw=(W-2*M-2*0.3)/3;
(D.sequence||[]).slice(0,3).forEach(([tag,t,d],i)=>{ const x=M+i*(sqw+0.3), y=4.42;
  s.addShape(pres.shapes.RECTANGLE,{x,y,w:sqw,h:1.5,fill:{color:i===0?INKD:WHITE},line:i===0?{type:"none"}:{color:DIV,width:0.75}});
  s.addText(tag,{x:x+0.2,y:y+0.16,w:sqw-0.4,h:0.24,fontFace:MONT,fontSize:9,bold:true,color:GOLD,charSpacing:2,margin:0});
  s.addText(t,{x:x+0.2,y:y+0.44,w:sqw-0.4,h:0.3,fontFace:MONT,fontSize:12,bold:true,color:i===0?WHITE:INK,margin:0});
  s.addText(d,{x:x+0.2,y:y+0.78,w:sqw-0.4,h:0.66,fontFace:MONT,fontSize:9,color:i===0?SKY:MUTE,margin:0,lineSpacingMultiple:1.08}); });
s.addShape(pres.shapes.RECTANGLE,{x:M,y:6.18,w:W-2*M,h:0.6,fill:{color:SKY,transparency:80},line:{color:DIV,width:0.75}});
s.addText([{text:"Confidence: "+((D.confidence&&D.confidence.level)||"medium")+".  ",options:{bold:true,color:DBLUE,fontSize:9.5}},
  {text:(D.confidence&&D.confidence.note)||"",options:{color:INK,fontSize:9.5}}],
  {x:M+0.24,y:6.25,w:W-2*M-0.48,h:0.48,fontFace:MONT,margin:0,lineSpacingMultiple:1.08,valign:"middle"});
foot(s,"5");

pres.writeFile({fileName:outPath}).then(()=>console.log("DECK WROTE "+outPath+"  | provisional="+provisional+" | merit="+meritDisp));
