#!/usr/bin/env python3
"""generate_partnership_onepager.py — canonical 1-page executive PDF (A4) for a
partnership evaluation, via the HTML -> Chromium (headless --print-to-pdf) pipeline.

Reads the same evaluation data model as the deck generator. Empty-inputs guard: if any
of {sector, cost, beneficiaries, duration} is missing, merit renders PROVISIONAL ("~N")
and the ASK renders as scoping-approval — never "Reject".

  python generate_partnership_onepager.py [dataModel.json] [out.pdf]
"""
import json, os, sys, subprocess, html

DATA = sys.argv[1] if len(sys.argv) > 1 else "_sample_ecw.json"
OUT  = sys.argv[2] if len(sys.argv) > 2 else "ECW_UAE_Leadership_OnePager.pdf"
D = json.load(open(DATA, encoding="utf-8"))
e = lambda s: html.escape(str(s or ""))

p = D.get("project", {})
prov = not (str(p.get("sector","")).strip() and str(p.get("cost","")).strip()
            and str(p.get("ben","")).strip() and str(p.get("dur","")).strip())
merit = round((D.get("scores",{}).get("merit",{}) or {}).get("score",0))
merit_disp = (("~%d" % merit) if merit > 0 else "Provisional") if prov else str(merit)
merit_verdict = "Provisional — project undefined" if prov else ("Strong" if merit>=75 else "Moderate" if merit>=55 else "Weak")
ask = (D.get("askScoping") if prov else D.get("askDefined")) or D.get("askScoping") or D.get("askDefined") or ""
sc = D.get("scores",{})

def li(items): return "".join("<li>%s</li>" % e(t) for t in items)
def chip(label,val,verdict,vc):
    return ('<div class="chip"><div class="ck">%s</div><div class="cv">%s</div>'
            '<div class="cd" style="color:%s">%s</div></div>' % (e(label.upper()), e(val), vc, e(verdict)))

bands = D.get("bands", [])
band_rows = ""
for b in bands:
    band, unlocks, marginal, influence, rec = (b+[False]*5)[:5]
    band_rows += ('<tr class="%s"><td class="bd">%s%s</td><td>%s</td><td>%s</td></tr>'
        % ("rec" if rec else "",
           e(band), ' <span class="star">★ Recommended</span>' if rec else "",
           e(unlocks), e(influence)))

ms = "".join('<div class="ms"><span class="msn">%d</span><span>%s</span></div>' % (i+1, e(t))
             for i,t in enumerate(D.get("milestones",[])[:5]))

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@600;700&family=Montserrat:wght@400;600;700&display=swap');
@page { size: A4; margin: 0; }
*{box-sizing:border-box;margin:0;padding:0}
html,body{font-family:'Montserrat',-apple-system,Arial,sans-serif;color:#1D252C;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{width:210mm;height:297mm;padding:13mm 13mm 9mm;position:relative}
.eyebrow{font-size:9px;font-weight:700;letter-spacing:2.6px;color:#AD833B;text-transform:uppercase}
h1{font-family:'Lora',Georgia,serif;font-size:23px;font-weight:700;color:#1D252C;margin:3px 0 0}
.rule{width:56px;height:2px;background:#AD833B;margin:7px 0 12px}
.ask{background:#101820;color:#fff;padding:11px 14px;font-size:11px;line-height:1.4}
.ask b{color:#AD833B}.ask .t{color:#CBDCE6}
.chips{display:flex;gap:9px;margin:11px 0}
.chip{flex:1;background:#F4F5F7;padding:9px 11px}
.ck{font-size:7.5px;font-weight:700;letter-spacing:1.3px;color:#5A6670}
.cv{font-family:'Lora',serif;font-size:26px;font-weight:700;color:#1D252C;line-height:1.05;margin:1px 0}
.cd{font-size:8.5px;font-weight:700}
.cols{display:flex;gap:9px;margin-bottom:10px}
.col{flex:1;padding:10px 12px;border:0.75px solid #E2E2E2}
.col.wash{background:#F4F5F7}
.col h3{font-size:9.5px;font-weight:700;letter-spacing:1.2px;margin-bottom:5px}
.col.proceed h3{color:#3D6B52}.col.hold h3{color:#79242F}
.col ul{list-style:none}.col li{font-size:8.6px;line-height:1.32;padding-left:9px;position:relative;margin-bottom:4px}
.col li:before{content:'•';position:absolute;left:0;color:#678CA5}
.risk{background:#EAF1F5;border:0.75px solid #E2E2E2;padding:9px 13px;font-size:9px;line-height:1.4;margin-bottom:10px}
.risk b{color:#79242F}.risk .m{color:#1D252C}
.sec-h{font-size:8.5px;font-weight:700;letter-spacing:1.4px;color:#2F586E;margin:0 0 4px}
table{width:100%;border-collapse:collapse;margin-bottom:10px}
th{text-align:left;font-size:7.5px;font-weight:700;letter-spacing:1px;color:#5A6670;border-bottom:1px solid #1D252C;padding:0 6px 4px}
td{font-size:8.6px;line-height:1.3;padding:6px;vertical-align:top;border-bottom:0.5px solid #E2E2E2}
td.bd{font-family:'Lora',serif;font-size:13px;font-weight:700;white-space:nowrap;width:120px}
tr.rec{background:#F4F5F7}tr.rec td.bd{color:#1D252C}
.star{display:block;font-family:'Montserrat';font-size:7px;font-weight:700;color:#AD833B;letter-spacing:.5px}
.gates{display:flex;gap:6px;margin-bottom:9px}
.ms{flex:1;border:0.75px solid #E2E2E2;padding:7px 8px;font-size:7.4px;line-height:1.25}
.msn{display:block;font-family:'Lora',serif;font-size:14px;font-weight:700;color:#AD833B;margin-bottom:2px}
.foot{position:absolute;left:13mm;right:13mm;bottom:7mm;font-size:7.4px;color:#5A6670;line-height:1.35;border-top:0.5px solid #E2E2E2;padding-top:5px}
.foot b{color:#2F586E}
"""

HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>%s</style></head><body>
<div class="page">
  <div class="eyebrow">FOR LEADERSHIP · %s</div>
  <h1>%s partnership — the decision</h1>
  <div class="rule"></div>
  <div class="ask"><b>THE ASK&nbsp;&nbsp;</b><span class="t">%s</span></div>
  <div class="chips">%s%s%s</div>
  <div class="cols">
    <div class="col proceed wash"><h3>WHY PROCEED</h3><ul>%s</ul></div>
    <div class="col hold"><h3>WHY HOLD BACK</h3><ul>%s</ul></div>
  </div>
  <div class="risk"><b>TOP RISK · %s&nbsp;&nbsp;</b>%s&nbsp;&nbsp;<b class="m">Mitigation:</b> %s</div>
  <div class="sec-h">FUNDING SCENARIOS</div>
  <table><thead><tr><th>BAND</th><th>WHAT IT UNLOCKS</th><th>INFLUENCE</th></tr></thead><tbody>%s</tbody></table>
  <div class="sec-h">PHASING — RELEASE CONDITIONED ON THESE MILESTONES</div>
  <div class="gates">%s</div>
  <div class="foot"><b>Confidence: %s.</b> %s</div>
</div></body></html>""" % (
  CSS, e(D.get("date","")), e(D.get("partnerShort") or D.get("partner")),
  e(ask),
  chip("Partner soundness", round(sc.get("partner",{}).get("score",0)), sc.get("partner",{}).get("verdict",""), "#3D6B52"),
  chip("UAE strategic value", round(sc.get("uae",{}).get("score",0)), sc.get("uae",{}).get("verdict",""), "#2F586E"),
  chip("Project merit", merit_disp, merit_verdict, "#79242F" if prov else "#3D6B52"),
  li(D.get("whyProceed",[])), li(D.get("whyHold",[])),
  e(D.get("topRisk",{}).get("level","")), e(D.get("topRisk",{}).get("risk","")), e(D.get("topRisk",{}).get("mitigation","")),
  band_rows, ms,
  e((D.get("confidence",{}) or {}).get("level","medium")), e((D.get("confidence",{}) or {}).get("note","")),
)

html_path = os.path.abspath("_onepager.html")
open(html_path, "w", encoding="utf-8").write(HTML)

CHROME = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]
exe = next((c for c in CHROME if os.path.exists(c)), None)
if not exe:
    sys.exit("No Chrome/Edge found for HTML->PDF.")
out_abs = os.path.abspath(OUT)
subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                "--print-to-pdf=" + out_abs, "file:///" + html_path.replace("\\", "/")],
               check=True, timeout=90, capture_output=True)
print("ONEPAGER WROTE %s | provisional=%s | merit=%s" % (OUT, prov, merit_disp))
