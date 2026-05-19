"""
generate_ethiopia_ppt.py
========================
Thin driver — builds the Ethiopia context dict matching design/Country_Overview_extracted.html
and calls the canonical builder.

The 13-slide structure, palette, layouts, and helper blocks live in
`country_ppt_builder.py` (the single source of truth).
"""
from country_ppt_builder import (
    build, BLUE, GOLD, NAVY, DEEP_GREEN, DEEP_RED, NEG, SEMI_NEG, BLUE_PALE
)

OUT = "Ethiopia_brief.pptx"


def build_context():
    return {
        "country":  "Ethiopia",
        "iso2":     "et",
        "lat":      9.145,
        "lng":      40.4897,
        "subtitle": "Federal Democratic Republic of Ethiopia · Horn of Africa · 130M people",

        # ─── Map: choropleth heatmap of admin-1 regions ───
        # Categories map to severity colors: escalating > re-escalating > high
        # > stable > improving. Region names must match Natural Earth's admin-1
        # spelling (see skill output if you change them).
        # Note: Sidama (carved out of SNNPR in 2020) and South West Ethiopia
        # (2021) aren't in Natural Earth 1:50m yet — they roll into SNNPR.
        "map": {"type": "choropleth"},
        "subnational_indicators": {
            "Tigray":                                    "re-escalating", # post-Pretoria fragile peace
            "Amhara":                                    "escalating",    # Fano insurgency
            "Oromiya":                                   "high",          # OLA conflict pockets
            "Afar":                                      "high",          # drought + displacement
            "Somali":                                    "high",          # drought-driven need
            "Addis Ababa":                               "stable",        # capital, calmer
            "Southern Nations, Nationalities and Peoples":"stable",       # SNNPR (incl. Sidama post-2020)
            "Gambela Peoples":                           "stable",
            "Benshangul-Gumaz":                          "stable",
            "Harari People":                             "improving",
            "Dire Dawa":                                 "improving",
        },

        "snapshot": {
            "capital":   "Addis Ababa · 5.2M",
            "currency":  "Ethiopian Birr (ETB)",
            "languages": "Amharic · Oromo · Tigrinya · Somali",
            "dac_class": "LEAST DEVELOPED · LOW INCOME",
            "gni_cap":   "$1,020 (2024)",
        },

        # ─── 3-column hero snapshot (slide 1 top) ───
        "hero_snapshot": [
            {
                "section":     "General",
                "hero_value":  "$1.1B",
                "hero_label":  "UAE contribution · aid & deposits 2018–24",
                "hero_source": "UAE MoFA · 2024",
                "sub_cells": [
                    {"value":"0.50",  "label":"HDI · rank 175", "source":"UNDP · 2024"},
                    {"value":"~250K", "label":"Diaspora in UAE","source":"IOM · MoLSA"},
                ],
            },
            {
                "section":     "Economic",
                "hero_value":  "$163B",
                "hero_label":  "GDP · 7.3% growth FY24",
                "hero_source": "IMF · AfDB",
                "sub_cells": [
                    {"value":"B+",          "label":"Investment potential", "source":"AfDB Outlook"},
                    {"value":"Agri · Mfg",  "label":"Top sectors",           "source":"World Bank"},
                ],
            },
            {
                "section":     "Political & Humanitarian",
                "hero_value":  "21.4M",
                "hero_label":  "Humanitarian need · HRP ~40% funded",
                "hero_source": "OCHA · 2024",
                "sub_cells": [
                    {"value":"4.5M+",  "label":"IDPs · 900K refugees",  "source":"IOM DTM · UNHCR"},
                    {"value":"Active", "label":"Conflict · Amhara/Oromia","source":"ACLED · ICG"},
                ],
            },
        ],

        "kpi_pair": [
            {"label":"Population", "value":"130M",    "sublabel":"2nd in Africa  ·  UN DESA 2024"},
            {"label":"Land Area",  "value":"1.1M km²","sublabel":"12th in Africa  ·  landlocked"},
        ],

        # ─── 7-row sector status table (cover) ───
        "sector_status": [
            {"name":"Health",         "status":"severe",     "summary":"High maternal/child mortality · low UHC"},
            {"name":"Education",      "status":"weak",       "summary":"18M+ out of school · conflict disruption"},
            {"name":"Food Security",  "status":"severe",     "summary":"15.8M food-insecure · Tigray/Amhara"},
            {"name":"WASH",           "status":"weak",       "summary":"~50% rural access to safe water"},
            {"name":"Economic",       "status":"improving",  "summary":"7.3% growth · macro reforms underway"},
            {"name":"Governance",     "status":"weak",       "summary":"Federal tensions · regional conflicts"},
            {"name":"Infrastructure", "status":"developing", "summary":"GERD · road/rail expansion"},
        ],

        "cover_footer":
            "Sources: UN DESA · IMF · World Bank · AfDB · UNDP · OCHA · IOM DTM · UAE MoFA · UNICEF · WHO",

        # ─── Sector slides ───
        "sectors": {
            # SLIDE 2 — At a Glance
            "at_a_glance": {
                "statement": "130M people drive Africa's fastest-growing economy amid deep fragility",
                "chart_title": "Regional Population Distribution",
                "stats": [
                    {"val":"130M", "label":"Population — 2nd most populous African nation, growing 2.5%/yr"},
                    {"val":"12",   "label":"Regions & 2 city administrations — highlands, lowlands, pastoral"},
                    {"val":"7.3%", "label":"GDP growth FY2023/24 — outpacing SSA average of 3.6%"},
                    {"val":"4.5M+","label":"Internally displaced persons — among Africa's largest crises", "neg":True},
                ],
                "insights": [
                    "Strong economic growth co-exists with high inflation (26.6%) and acute debt distress; gains unevenly distributed.",
                    "Conflict in Tigray, Amhara and Oromia plus drought in Somali and Afar are the dominant drivers of humanitarian need.",
                    "Regional disparities in health, education and infrastructure are structural — region-targeted programming required.",
                ],
                "interventions": [
                    "Multi-region targeted programming",
                    "Conflict-sensitive design across Amhara/Oromia/Tigray",
                    "Pair humanitarian + development financing",
                ],
                "sources": "Sources: UN DESA · Govt of Ethiopia · AfDB Economic Outlook · IOM DTM Ethiopia",
            },

            # SLIDE 3 — Economy
            "economy": {
                "statement": "7.3% growth masks 26.6% inflation and acute debt distress",
                "chart": {
                    "title": "GDP Growth vs. Inflation — FY20 to FY24",
                    "x_labels": ["FY20","FY21","FY22","FY23","FY24"],
                    "bar_values": [6.1, 6.3, 6.4, 6.6, 7.3],
                    "line_values": [14, 16, 24, 28, 26.6],
                    "y_max": 40,
                    "bar_label":  "GDP growth (%)",
                    "line_label": "CPI inflation (%)",
                },
                "stats": [
                    {"val":"7.3%", "label":"GDP growth FY2023/24 — driven by industry & agriculture"},
                    {"val":"26.6%","label":"Headline inflation FY24; food inflation 28.1%", "neg":True},
                    {"val":"$28B", "label":"External debt stock; defaulted on $33M Eurobond Dec 2023"},
                    {"val":"7.3%", "label":"Tax revenue / GDP — among the lowest globally"},
                ],
                "insights": [
                    "High risk of debt distress; March 2025 Agreement in Principle with Official Creditor Committee on ~$8.4B under G20 Common Framework.",
                    "Inflation hits net food buyers — including 8.5M poor urban households — hardest, deepening poverty despite headline growth.",
                    "A revenue base of just 7.3% of GDP caps fiscal space for social investment; PFM reform is foundational.",
                ],
                "interventions": [
                    "Finalize Common Framework debt treatment",
                    "Domestic revenue mobilization reform",
                    "Anti-inflation input subsidies",
                    "PFM strengthening & expenditure controls",
                ],
                "sources": "Sources: AfDB · National Bank of Ethiopia · IMF Article IV 2024 · World Bank",
            },

            # SLIDE 4 — Health
            "health": {
                "statement": "51-per-1,000 child mortality reflects stark regional inequity",
                "chart_title": "Full Immunization Coverage by Region (% under-5)",
                "stats": [
                    {"val":"51",   "label":"Under-5 deaths per 1,000 live births — ~3× global average of 18", "neg":True},
                    {"val":"44%",  "label":"Full immunization coverage, against 90% national target"},
                    {"val":"2.5%", "label":"Government health spending / GDP, vs. WHO-recommended 5%"},
                    {"val":"42K",  "label":"Health Extension Workers deployed — flagship community model"},
                ],
                "insights": [
                    "U5 mortality has fallen from 200+ in 1990 to ~51 today — but pneumonia, diarrhea and malaria remain leading killers.",
                    "Children in Addis Ababa are 7× more likely to be fully vaccinated than children in Afar — the largest regional gap.",
                    "Out-of-pocket spending drives household impoverishment; community-based health insurance remains under-scaled.",
                ],
                "interventions": [
                    "Expand HEW networks in Afar & Somali",
                    "Scale community health insurance",
                    "Strengthen vaccine cold-chain logistics",
                    "Increase health budget toward 5% of GDP",
                ],
                "sources": "Sources: UN IGME · WHO/UNICEF JRF · WHO GHED · Ethiopia MoH",
            },

            # SLIDE 5 — Education
            "education": {
                "statement": "90% of 10-year-olds cannot read — a learning crisis, not an enrollment one",
                "chart": {
                    "title": "Enrollment by Level & Gender (Net %)",
                    "x_labels": ["Primary", "Lower-Sec.", "Upper-Sec.", "Tertiary"],
                    "series_a": [95, 38, 22, 11],
                    "series_b": [88, 32, 17, 8],
                    "a_label":  "Boys",
                    "b_label":  "Girls",
                    "y_max": 100,
                },
                "stats": [
                    {"val":"90%", "label":"10-year-olds who cannot read with comprehension", "neg":True},
                    {"val":"95%", "label":"Primary net enrollment — near-universal access achieved"},
                    {"val":"32%", "label":"Girls' lower-secondary enrollment — sharp Gr 9 cliff", "neg":True},
                    {"val":"4.5%","label":"Education spend / GDP — below GPE benchmark of 6%"},
                ],
                "insights": [
                    "Enrollment success contrasts with foundational-learning crisis — 90% of 10-year-olds cannot read with comprehension.",
                    "Mother-tongue instruction (Gr 1–4) implemented across regional languages — but quality varies sharply.",
                    "Conflict closures in Amhara and Oromia put an estimated 3M children out of school in 2023–24.",
                ],
                "interventions": [
                    "Structured pedagogy at scale (TaRL)",
                    "Conditional transfers for girls' secondary",
                    "School-feeding in food-insecure woredas",
                    "TVET tied to industrial-park demand",
                ],
                "sources": "Sources: UNESCO UIS · GPE · Ethiopia MoE · World Bank GEPD",
            },

            # SLIDE 6 — Nutrition Cascade
            "nutrition": {
                "statement": "From the 130M population, 8M+ face acute food insecurity",
                "chart_title": "Population Cascade — From Risk to Acute Need",
                "funnel": [
                    {"pct":"130M", "percent_text":"100%",
                     "label":"Total population",
                     "stage":"National baseline",
                     "sublabel":"UN DESA, 2024",
                     "width_ratio":1.00, "color":NAVY},
                    {"pct":"36M",  "percent_text":"28%",
                     "label":"At food-security risk",
                     "stage":"Rain-fed-ag dependent",
                     "sublabel":"USDA / FEWS NET, 2024",
                     "width_ratio":0.88, "color":BLUE},
                    {"pct":"27M",  "percent_text":"21%",
                     "label":"IPC Phase 2+ · Stressed",
                     "stage":"Programmatic support needed",
                     "sublabel":"IPC/CH Analysis, 2024",
                     "width_ratio":0.74, "color":GOLD},
                    {"pct":"8.4M", "percent_text":"6.5%",
                     "label":"IPC Phase 3+ · Crisis",
                     "stage":"Acute food insecurity",
                     "sublabel":"IPC/CH Analysis, 2024",
                     "width_ratio":0.58, "color":SEMI_NEG},
                    {"pct":"2.0M", "percent_text":"1.5%",
                     "label":"P4 · Emergency",
                     "stage":"Severe food gaps",
                     "sublabel":"IPC/CH Analysis, 2024",
                     "width_ratio":0.42, "color":NEG},
                ],
                "stats": [
                    {"val":"37%", "label":"Stunting under-5 — highest absolute counts in SSA", "neg":True},
                    {"val":"36%", "label":"Agriculture share of GDP; 73% of labor force employed"},
                    {"val":"+51%","label":"Cereal import surge, H2 2024 vs prior year", "neg":True},
                ],
                "insights": [
                    "The cascade narrows from baseline risk to acute need — each phase reflects vulnerability that compounds with the next shock.",
                    "Somali, Oromia, and South Ethiopia account for the majority of IPC Phase 3+ caseloads.",
                    "Stunting at 37% is a long-term human capital loss — Ethiopia has among the highest absolute counts in SSA.",
                ],
                "interventions": [
                    "Scale smallholder irrigation",
                    "Drought-resilient seed varieties",
                    "Nutrition-sensitive ag extension",
                    "Strategic grain reserves & market integration",
                ],
                "sources": "Sources: UNICEF/WHO Joint Estimates · CSA Ethiopia · FAO GIEWS",
            },

            # SLIDE 7 — Agriculture
            "agriculture": {
                "statement": "73% of Ethiopians depend on rain-fed farming vulnerable to climate shocks",
                "chart_title": "Stunting Prevalence Among Children Under 5 by Region (%)",
                "stats": [
                    {"val":"73%",  "label":"Labor force in agriculture — overwhelmingly subsistence-based"},
                    {"val":"78%",  "label":"Farmers reliant on rain-fed agriculture; only 5% land irrigated", "neg":True},
                    {"val":"$1.4B","label":"Coffee export earnings — single largest commodity export"},
                    {"val":"126B", "label":"Birr in agricultural input subsidies in 2024"},
                ],
                "insights": [
                    "Cereal imports surged +51% in H2 2024 vs prior year, stressing FX reserves and reflecting domestic shortfalls.",
                    "Pastoralist regions (Somali, Afar) face compounding drought-conflict-displacement cycles that erode coping capacity.",
                    "Coffee remains a strategic FX anchor but is increasingly exposed to climate volatility and global price swings.",
                ],
                "interventions": [
                    "Smallholder irrigation expansion",
                    "Drought-tolerant seed adoption",
                    "Pastoralist livelihood programming",
                    "Climate-smart extension services",
                ],
                "sources": "Sources: CSA Labour Force Survey · Ethiopia MoA · ECTA · NBE Annual Report",
            },

            # SLIDE 8 — Infrastructure
            "infrastructure": {
                "statement": "Urban Ethiopia has electricity; rural Ethiopia largely does not",
                "chart_title": "Service Access — Urban vs. Rural Comparison",
                "compare_rows": [
                    {"label":"Electricity",         "urban":95, "rural":15},
                    {"label":"Safe water",          "urban":85, "rural":50},
                    {"label":"Improved sanitation", "urban":35, "rural":12},
                    {"label":"Internet access",     "urban":45, "rural":8},
                    {"label":"Mobile money",        "urban":62, "rural":18},
                ],
                "stats": [
                    {"val":"55%",  "label":"National electricity access — improved from 27% in 2010"},
                    {"val":"~15%", "label":"Rural electrification, despite GERD & regional power exports", "neg":True},
                    {"val":"31%",  "label":"Rural roads passable year-round; seasonal flooding isolates"},
                ],
                "insights": [
                    "Urban-rural gap is the defining infrastructure story — rural access lags urban by 4–10× across services.",
                    "Mobile money (Telebirr, CBE Birr) is growing fast — a leapfrog opportunity for last-mile inclusion and G2P transfers.",
                    "Rural facility electrification limits vaccine cold-chain, diagnostics and digital learning — infrastructure constrains every other sector.",
                ],
                "interventions": [
                    "Off-grid solar for clinics & schools",
                    "Climate-resilient feeder roads",
                    "Mobile money rails for cash transfers",
                    "Last-mile grid extension",
                ],
                "sources": "Sources: World Bank · Ethiopia Electric Utility · Ethiopian Roads Authority · ITU",
            },

            # SLIDE 9 — Climate
            "climate": {
                "statement": "Ethiopia ranks in the top 15% most climate-vulnerable countries globally",
                "chart": {
                    "title": "Forest Cover Decline & Climate Risk — 2000 to 2024",
                    "x_labels": ["2000","2005","2010","2015","2020","2024"],
                    "series": [
                        {"label":"Forest cover (% land area)",
                         "values":[40, 35, 28, 22, 17, 15], "color": DEEP_GREEN},
                        {"label":"ND-GAIN climate risk index",
                         "values":[20, 25, 33, 45, 58, 68], "color": NEG, "dashed":True},
                    ],
                    "y_max": 100,
                },
                "stats": [
                    {"val":"14.9%", "label":"Forest cover — down from estimated 35–40% a century ago", "neg":True},
                    {"val":"+1.5°C","label":"Projected warming by 2050 — up to +3°C in highland regions"},
                    {"val":"25B",   "label":"Tree seedlings planted via the Green Legacy Initiative"},
                    {"val":"$8B+",  "label":"National Adaptation Plan finance gap — severely underfunded", "neg":True},
                ],
                "insights": [
                    "Ethiopia ranks in the top 15% most climate-vulnerable countries globally on ND-GAIN, driven by drought exposure and adaptive-capacity gaps.",
                    "More frequent El Niño events and prolonged Horn of Africa droughts are directly driving food insecurity cycles.",
                    "The Green Legacy Initiative has planted 25B+ seedlings — domestic commitment exists; complementary policy enforcement is the gap.",
                ],
                "interventions": [
                    "Mobilize GCF/GEF for NAP financing",
                    "Integrate DRR into regional plans",
                    "Enforce community forestry rules",
                    "Climate-smart agriculture at scale",
                ],
                "sources": "Sources: World Bank · IPCC AR6 Africa · Govt of Ethiopia · Ethiopia NAP · ND-GAIN",
            },

            # SLIDE 10 — Humanitarian
            "humanitarian": {
                "statement": "4.5M+ IDPs make Ethiopia one of Africa's largest displacement crises",
                "chart_title": "IDP Concentration by Region of Origin",
                "stats": [
                    {"val":"4.5M+", "label":"Internally displaced persons; conflict, drought & flood drivers", "neg":True},
                    {"val":"~900K", "label":"Refugees hosted from South Sudan, Eritrea & Somalia"},
                    {"val":"21.4M", "label":"People in humanitarian need — 2024 HRP planning figure"},
                ],
                "insights": [
                    "Three drivers overlap: conflict (Tigray, Amhara, Oromia), drought (Somali, Afar), and floods — generating compounding caseloads.",
                    "The Pretoria Peace Agreement (Nov 2022) brought relative stability to Tigray, enabling partial returns; Amhara/Oromia conflicts continue to displace.",
                    "Humanitarian access remains constrained in active conflict zones, limiting needs assessment and last-mile delivery.",
                ],
                "interventions": [
                    "Multi-year flexible HRP funding",
                    "Durable solutions for Tigray returnees",
                    "Access advocacy in Amhara & Oromia",
                    "Link IDP returns with livelihoods",
                ],
                "sources": "Sources: IOM DTM Round 36 · UNHCR · OCHA Ethiopia HRP",
            },
        },

        # ─── SLIDE 11 — Big-stat (Funding Gap) ───
        "bigstat": {
            "crumb":        "11 · FUNDING GAP · 2024 HUMANITARIAN RESPONSE PLAN",
            "hero_value":   "~40%",
            "hero_label":   "OF $2.4B HRP FUNDED IN 2024",
            "statement":    "$1.4B unfunded means food, shelter and health support are out of reach for millions of Ethiopians in acute need.",
            "quote":        "“The 2024 Ethiopia Humanitarian Response Plan is among the most underfunded major appeals globally, despite needs intensifying.”",
            "quote_source": "— OCHA Ethiopia, 2024",
            "strip": [
                {"value":"$2.4B", "label":"Required (2024)"},
                {"value":"$960M", "label":"Funded"},
                {"value":"21.4M", "label":"People in need"},
            ],
        },

        # ─── SLIDE 12 — 8-card Priorities ───
        "priorities_block": {
            "crumb":     "12 · STRATEGIC RECOMMENDATIONS",
            "topic":     "Priorities",
            "statement": "Eight cross-sector interventions, sequenced by urgency",
            "cards": [
                {"num":"01 · Economy",        "title":"Finalize Common Framework debt deal",
                 "desc":"Conclude bilateral creditor negotiations; sequence with revenue mobilization reform and PFM strengthening to rebuild fiscal space.",
                 "priority":"high"},
                {"num":"02 · Health",         "title":"Scale CHWs in Afar & Somali",
                 "desc":"Close the 7× immunization gap with pastoralist-adapted outreach; expand community health insurance beyond Amhara pilot scale.",
                 "priority":"high"},
                {"num":"03 · Education",      "title":"Structured pedagogy at scale",
                 "desc":"Move from enrollment to learning. Mother-tongue early-grade instruction; conditional transfers for girls' secondary retention.",
                 "priority":"high"},
                {"num":"04 · Food Security",  "title":"Smallholder irrigation 5%→15%",
                 "desc":"Triple irrigated cropland over a decade. Drought-resilient seed adoption. Nutrition integration in agricultural extension.",
                 "priority":"high"},
                {"num":"05 · Humanitarian",   "title":"Multi-year flexible HRP funding",
                 "desc":"Close the $1.4B 2024 funding gap. Durable solutions for Tigray returnees; access advocacy in Amhara & Oromia.",
                 "priority":"high"},
                {"num":"06 · Infrastructure", "title":"Off-grid solar for clinics & schools",
                 "desc":"Climate-proof rural feeder roads. Mobile money infrastructure as the rail for social protection cash transfers.",
                 "priority":"medium"},
                {"num":"07 · Climate",        "title":"GCF/GEF finance for NAP",
                 "desc":"Mobilize external climate finance against the $8B NAP gap. Enforce community forestry rules; scale climate-smart ag.",
                 "priority":"medium"},
                {"num":"08 · Cross-cutting",  "title":"Strengthen national data systems",
                 "desc":"HMIS, EMIS and humanitarian M&E capacity. Without reliable disaggregated data, region-targeted programming is impossible.",
                 "priority":"foundational", "dark":True},
            ],
            "footer": "Priority levels reflect urgency × systemic impact, not preference. High-priority items address acute distress; medium-priority items address structural constraints; the foundational item enables all others.",
        },

        # ─── SLIDE 13 — Closing ───
        "closing": {
            "subtitle": "Country Overview · Sector Assessment & Intervention Priorities",
            "meta": ["May 2026", "Country Analysis Team"],
            "sources":
                "Sources: World Bank · AfDB · IMF · OCHA · WHO · UNICEF · UNESCO UIS · UNHCR · IOM DTM    "
                "IPC/CH · ND-GAIN · National Bank of Ethiopia · CSA Ethiopia · MoH · MoE · MoA",
        },
    }


if __name__ == "__main__":
    ctx = build_context()
    build(ctx, OUT)
    print(f"OK -> {OUT}")
