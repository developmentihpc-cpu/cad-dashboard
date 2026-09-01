#!/usr/bin/env python3
"""build_country_report.py — produce the EXACT ODA country-proposal deck for a country
by filling the bundled 23-slide template (country_report/assets/country_proposal_template.pptx).

This automates the country-needs-assessment skill's method: start from the template stub
(Zimbabwe text = the format + length budget), have Claude research the target country live
and rewrite every country-specific slot in place, then fill_template.py builds the deck.

    python build_country_report.py Paraguay --iso2 PY --only 1        # cover only (validation)
    python build_country_report.py Paraguay --iso2 PY                 # full deck

Key from .env (ANTHROPIC_API_KEY). Web search on by default.
"""
import argparse, json, os, re, sys, subprocess, urllib.request, io, unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent
CR   = BASE / "country_report"
TEMPLATE = CR / "assets" / "country_proposal_template.pptx"
SCRIPTS  = CR / "scripts"
MODEL = os.environ.get("SCORING_MODEL", "claude-opus-4-5")
os.environ.setdefault("PYTHONUTF8", "1")

# ── .env ──
def load_env():
    env = {}
    f = BASE / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("ANTHROPIC_API_KEY",):
        if k not in env and k in os.environ:
            env[k] = os.environ[k]
    return env
ENV = load_env()

def client():
    import anthropic
    key = ENV.get("ANTHROPIC_API_KEY")
    if not key or key.startswith("sk-ant-xxx"):
        sys.exit("No ANTHROPIC_API_KEY in .env")
    return anthropic.Anthropic(api_key=key)

# ── stub ──
def make_stub():
    out = subprocess.run([sys.executable, str(SCRIPTS / "extract_slots.py"), str(TEMPLATE), "--stub"],
                         capture_output=True, text=True, encoding="utf-8",
                         env={**os.environ, "PYTHONUTF8": "1"})
    if out.returncode != 0:
        sys.exit("extract_slots failed:\n" + out.stderr)
    return json.loads(out.stdout)

def group_by_slide(text):
    groups = {}
    for k in text:
        si = int(k[1:].split("_")[0])
        groups.setdefault(si, {})[k] = text[k]
    return groups

# slide groups fed to the model together (kept small enough for accurate rewriting)
CHUNKS = [
    ("Cover & national snapshot", [1]),
    ("Cross-sector snapshot", [2]),
    ("Key actors, shock geography & national strategy", [3, 4, 5]),
    ("Section dividers", [6, 16, 17, 22]),
    ("At a glance", [7]),
    ("Sector deep-dives A", [8, 9, 10, 11]),
    ("Sector deep-dives B", [12, 13, 14, 15]),
    ("Programme menu & detail cards", [18, 19, 20, 21]),
    ("GPS matrix", [23]),
]

SYSTEM = """You are the Country Needs Assessment researcher for the UAE Office of Development Affairs (ODA).
You are filling a FIXED 23-slide PowerPoint template for a target country. You will be given a JSON
object of slot-id -> current value (the template's Zimbabwe text). REWRITE every value for the TARGET
COUNTRY, editing in place.

ABSOLUTE RULES
- Return STRICT JSON only: the SAME keys, with rewritten values. No new keys, no removed keys, no prose.
- A value that is a LIST must stay a list of the SAME length (one string per run). A string stays a string.
- LENGTH: each rewritten value must be <= the character length of the value you are replacing (the box does
  not grow). Match the register: compressed, declarative, a number or mechanism per line. British spelling.
- STATIC LABELS STAY: section kickers, column headers, words like "KEY INSIGHTS", "POTENTIAL INTERVENTIONS",
  "STATUS", "CAPITAL", "RECOMMENDED", "ODA", arrow glyphs "▸", and page numbers like "   NN / 23" must be
  returned UNCHANGED. Only rewrite the country-specific content (names, numbers, findings, sources, insights).
- EVERY figure must be real and sourced from THIS session's web search — never a remembered or invented number.
  Carry the source + year into the note/caption/sources slots exactly as the template does (e.g. "WB 2024",
  "UN IGME 2024"). If a figure cannot be verified, keep the metric label but use a conservative sourced value
  or "ND". Titles state the finding, not the topic.
- Do NOT mention Zimbabwe, Harare, ZiG, ZimStat, or any Zimbabwe-specific entity anywhere in the output.
"""

def _run(cl, messages, tools, system=SYSTEM):
    searches = 0; last = None
    for _ in range(6):
        last = cl.messages.create(model=MODEL, max_tokens=8000, system=system,
                                  messages=messages, tools=tools) if tools else \
               cl.messages.create(model=MODEL, max_tokens=8000, system=system, messages=messages)
        searches += sum(1 for b in last.content if getattr(b, "type", "") == "server_tool_use")
        if getattr(last, "stop_reason", None) == "pause_turn":
            messages.append({"role": "assistant", "content": last.content}); continue
        break
    return last, searches

def _extract_json(text):
    """Return the first balanced top-level JSON object (ignores prose/extra blocks around it)."""
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in model reply")
    depth = 0; instr = False; esc = False
    for i in range(start, len(text)):
        c = text[i]
        if esc:
            esc = False; continue
        if c == "\\":
            esc = True; continue
        if c == '"':
            instr = not instr; continue
        if instr:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("unbalanced JSON in model reply")

def edit_chunk(cl, country, iso2, indicators, label, slots):
    inds = "\n".join("%s = %s (%s)" % (k, v.get("value"), v.get("year", ""))
                     for k, v in list(indicators.items())[:70])
    user = ("TARGET COUNTRY: %s  (ISO2 %s)\n"
            "Template section: %s\n\n"
            "World Bank baseline indicators (id = value (year)) — verify/enrich with primary sources:\n%s\n\n"
            "Rewrite EVERY value in the JSON below for %s, editing in place. Research the latest primary-source "
            "figures (World Bank, IMF, WHO, UNICEF/UN IGME, UNESCO UIS, FAO, WHO/UNICEF JMP, ITU, IEA, OCHA, "
            "national statistics office) and cite each. Return the SAME JSON keys with rewritten values only.\n\n"
            "JSON to rewrite:\n%s"
            % (country, iso2, label, inds, country, json.dumps(slots, ensure_ascii=False)))
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}]
    msg, n = _run(cl, [{"role": "user", "content": user}], tools)
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    edited = _extract_json(text)
    # keep only known keys; preserve run-count; fall back to stub value on any mismatch
    out = {}
    for k, orig in slots.items():
        v = edited.get(k, orig)
        if isinstance(orig, list):
            if isinstance(v, list) and len(v) == len(orig):
                pass  # matches the template's run count — keep as list
            elif isinstance(v, list) and v:
                v = " ".join(str(x) for x in v)  # wrong run count → collapse (fill_template fills run 0)
            elif isinstance(v, str) and v.strip():
                pass  # a plain string fills run 0 and blanks the rest
            else:
                v = orig
        else:
            if isinstance(v, list):
                v = v[0] if v else orig
            v = str(v)
        out[k] = v
    return out, n

MAP_SLOTS = ["cover_map", "crisis_map", "map_s7", "map_s8", "map_s9", "map_s10",
             "map_s11", "map_s12", "map_s13", "map_s14", "map_s15"]
BAND_COLOR = {"SEVERE": "9B120B", "RED": "9B120B", "CRITICAL": "9B120B",
              "AMBER": "AD833B", "DEVELOPING": "AD833B", "MODERATE": "AD833B",
              "GREEN": "1F8A5B", "STABLE": "1F8A5B", "IMPROVING": "1F8A5B", "STRONG": "1F8A5B"}

GPS_RECTS = [15, 23, 31, 39, 47, 55, 63, 71, 79, 87, 95]  # slide 23 chip rects; GPS value at rect+1
ZW = re.compile(r"zimbabw|harar|zanu|mnangagw|\bzig\b|campfire|hwange|kariba|zimstat|zimsec|"
                r"bulawayo|masvingo|matabele|manicaland|mashonaland|zambezi|lowveld|\bndebele\b|"
                r"\bshona\b|gukurahundi|chitepo|nkomo", re.I)

def _asstr(v):
    return v if isinstance(v, str) else " ".join(str(x) for x in v) if isinstance(v, list) else str(v)

def gps_chip_fills(edited):
    """Recolour the 11 GPS-matrix chips to their band from the GPS value the model wrote."""
    fills = {}
    for R in GPS_RECTS:
        raw = re.sub(r"[^0-9]", "", _asstr(edited.get("s23_%d" % (R + 1), "")))
        if not raw:
            continue
        g = int(raw)
        fills["s23_%d" % R] = "9B120B" if g >= 15 else "AD833B" if g >= 8 else "1F8A5B"
    return fills

def cover_chip_fills(edited):
    """Recolour the 6 cover sector-status chips to match the band word the model wrote
    (chip band text at s1_74/78/82/86/90/94; the coloured rect is one shape before)."""
    fills = {}
    for tslot in ("s1_74", "s1_78", "s1_82", "s1_86", "s1_90", "s1_94"):
        v = edited.get(tslot)
        if isinstance(v, list):
            v = v[0] if v else ""
        col = BAND_COLOR.get(str(v).strip().upper())
        if col:
            fills["s1_%d" % (int(tslot.split("_")[1]) - 1)] = col
    return fills

def fetch_geojson(iso3, dest):
    """ADM1 boundaries from geoBoundaries (gbOpen) by ISO3, cached to dest."""
    if dest.exists() and dest.stat().st_size > 1000:
        return str(dest)
    meta = json.loads(urllib.request.urlopen(
        "https://www.geoboundaries.org/api/current/gbOpen/%s/ADM1/" % iso3.upper(), timeout=25).read())
    m = meta[0] if isinstance(meta, list) else meta
    data = urllib.request.urlopen(m["gjDownloadURL"], timeout=60).read()
    dest.write_bytes(data)
    return str(dest)

# map slot -> content slot carrying its caption/theme (slide 7 + the 8 sector deep-dives)
THEME_CAP = {"map_s7": "s7_50", "map_s8": "s8_29", "map_s9": "s9_29", "map_s10": "s10_29",
             "map_s11": "s11_29", "map_s12": "s12_29", "map_s13": "s13_29",
             "map_s14": "s14_29", "map_s15": "s15_29"}
CHORO_PAL = ["6E4A1E", "AD833B", "E7D7B4"]  # high -> medium -> low (dark gold -> light)
MAPS_SYSTEM = ("You are a subnational data analyst. For a country's ADM1 regions, classify each into "
               "HIGH / MEDIUM density bands for a given indicator using known geographic patterns "
               "(indicative estimates — the deck labels them 'est.'). Return STRICT JSON only, using the "
               "exact region names supplied.")

def _norm(s):
    return "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c)).lower().strip()

def region_names(geojson_path, name_key="shapeName"):
    g = json.load(open(geojson_path, encoding="utf-8"))
    return [f["properties"].get(name_key) for f in g["features"] if f["properties"].get(name_key)]

def choropleth_maps(cl, country, geojson_path, themes):
    """Ask the model to band each ADM1 region (high/medium; rest = low) per map theme, then build
    vector_maps choropleth specs. Region names are matched diacritic-insensitively to the geojson."""
    regions = region_names(geojson_path)
    rnorm = {_norm(r): r for r in regions}
    theme_list = "\n".join("- %s: %s" % (k, v) for k, v in themes.items())
    user = ("COUNTRY: %s\nADM1 regions (use these EXACT names as keys): %s\n\n"
            "For EACH map below, list the regions in the HIGH band and the MEDIUM band for that indicator "
            "(every other region is treated as LOW). Base it on known subnational patterns (indicative). "
            "Give a 3-item legend describing the high, medium and low bands (each <= 44 characters).\n\n"
            "MAPS:\n%s\n\n"
            'Return STRICT JSON only: {"map_key": {"high":[regions], "medium":[regions], '
            '"legend":[high_label, medium_label, low_label]}, ...}. Include every map key. Region names verbatim.'
            % (country, ", ".join(regions), theme_list))
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 6}]
    msg, n = _run(cl, [{"role": "user", "content": user}], tools, system=MAPS_SYSTEM)
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    data = _extract_json(text)
    vm = {}
    for mk, spec in data.items():
        if mk not in ("crisis_map",) + tuple(MAP_SLOTS):
            continue
        classes = {}
        for r in (spec.get("high") or []):
            m = rnorm.get(_norm(r))
            if m:
                classes[m] = 0
        for r in (spec.get("medium") or []):
            m = rnorm.get(_norm(r))
            if m and m not in classes:
                classes[m] = 1
        leg = spec.get("legend")
        vm[mk] = {"geojson": geojson_path, "classes": classes, "palette": CHORO_PAL,
                  "legend": leg if isinstance(leg, list) and len(leg) == 3 else None}
    return vm, n

def fetch_flag(iso2, dest):
    try:
        url = "https://flagcdn.com/w320/%s.png" % iso2.lower()
        data = urllib.request.urlopen(url, timeout=15).read()
        # Pad to the slot's AR 2.000 with TRANSPARENCY (not white), so the navy panel shows
        # through the sides and only the flag is visible — no white bars, no distortion.
        from PIL import Image
        im = Image.open(io.BytesIO(data)).convert("RGBA")
        ar = 2.0
        w, h = im.size
        if abs(w / h - ar) > 0.01:
            if w / h < ar:  # too tall -> pad width (transparent left/right)
                nw = int(round(h * ar)); canvas = Image.new("RGBA", (nw, h), (0, 0, 0, 0))
                canvas.paste(im, ((nw - w) // 2, 0), im)
            else:            # too wide -> pad height (transparent top/bottom)
                nh = int(round(w / ar)); canvas = Image.new("RGBA", (w, nh), (0, 0, 0, 0))
                canvas.paste(im, (0, (nh - h) // 2), im)
            im = canvas
        im.save(dest)  # PNG keeps the alpha channel
        return str(dest)
    except Exception as e:
        print("  flag fetch failed:", e); return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("country")
    ap.add_argument("--iso2", default="")
    ap.add_argument("--iso3", default="")
    ap.add_argument("--out", default=None)
    ap.add_argument("--only", type=int, default=None, help="only this slide number (validation)")
    ap.add_argument("--indicators", default=str(BASE / "docs" / "data" / "indicators.json"))
    args = ap.parse_args()

    stub = make_stub()
    text = stub["text"]
    print("stub: %d slots" % len(text))

    allind = json.loads(Path(args.indicators).read_text(encoding="utf-8"))
    inds = {k: v for k, v in (allind.get(args.country, {}) or {}).items()
            if isinstance(v, dict) and v.get("value") is not None}
    print("indicators for %s: %d" % (args.country, len(inds)))

    cl = client()
    groups = group_by_slide(text)
    edited = dict(text)
    total_searches = 0
    for label, slides in CHUNKS:
        if args.only and args.only not in slides:
            continue
        subset = {k: v for si in slides for k, v in groups.get(si, {}).items()}
        if not subset:
            continue
        print("→ %s (%d slots)…" % (label, len(subset)), flush=True)
        out, n = edit_chunk(cl, args.country, args.iso2 or "", inds, label, subset)
        edited.update(out); total_searches += n
        print("   done (%d searches)" % n)

    # residual-Zimbabwe re-ask: any slot left as Zimbabwe-specific text (usually a multi-run
    # slot whose run count did not match) gets one targeted rewrite pass.
    if not args.only:
        leftover = {k: v for k, v in edited.items() if ZW.search(_asstr(v))}
        if leftover:
            print("→ residual-Zimbabwe re-ask (%d slots)…" % len(leftover), flush=True)
            out, n = edit_chunk(cl, args.country, args.iso2 or "", inds,
                                "Fix residual Zimbabwe-specific content — rewrite fully for the target country", leftover)
            edited.update(out); total_searches += n
            print("   done (%d searches)" % n)

    content = {"template": str(TEMPLATE), "text": edited, "images": {}}
    build = BASE / "_report_build"; build.mkdir(exist_ok=True)
    # chip colours: cover sector-status + GPS-matrix bands, from the values the model wrote
    fills = {}
    if not args.only or args.only == 1:
        fills.update(cover_chip_fills(edited))
    if not args.only or args.only == 23:
        fills.update(gps_chip_fills(edited))
    if fills:
        content["shape_fills"] = fills
    # flag
    if args.iso2:
        fp = fetch_flag(args.iso2, build / ("flag_%s.png" % args.iso2))
        if fp:
            content["images"]["flag"] = fp
    # maps — ADM1 choropleths (density bands per map theme) for the data maps; flat gold locator
    # for cover_map. geoBoundaries ADM1 boundaries; per-region classification via the model.
    if args.iso3:
        try:
            gj = fetch_geojson(args.iso3, build / ("%s_adm1.geojson" % args.iso3.upper()))
            vm = {"cover_map": {"geojson": gj, "classes": {}, "palette": ["AD833B"]}}
            themes = {mk: _asstr(edited.get(cap, "")).strip() for mk, cap in THEME_CAP.items()
                      if _asstr(edited.get(cap, "")).strip()}
            themes["crisis_map"] = "Climate and disaster shock exposure by region"
            try:
                choro, cn = choropleth_maps(cl, args.country, gj, themes)
                total_searches += cn
                vm.update(choro)
                print("  maps: %d ADM1 choropleths + cover locator (%d searches)" % (len(choro), cn))
            except Exception as e:  # noqa: BLE001
                print("  choropleth classification failed, using flat locators:", e)
                vm.update({slot: {"geojson": gj, "classes": {}, "palette": ["AD833B"]} for slot in MAP_SLOTS})
            content["vector_maps"] = vm
        except Exception as e:  # noqa: BLE001
            print("  maps skipped (geojson fetch failed):", e)

    slug = re.sub(r"[^a-z0-9]+", "_", args.country.lower()).strip("_")
    cjson = BASE / ("_content_%s.json" % slug)
    cjson.write_text(json.dumps(content, ensure_ascii=False, indent=1), encoding="utf-8")
    out = args.out or str(BASE / "_report_build" / ("%s_Country_Proposal.pptx" % args.country.replace(" ", "_")))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, str(SCRIPTS / "fill_template.py"), str(cjson),
                        "-o", out, "-t", str(TEMPLATE)],
                       capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, "PYTHONUTF8": "1"})
    print(r.stdout); print(r.stderr, file=sys.stderr)
    if r.returncode != 0:
        sys.exit("fill_template failed")
    print("WROTE", out, "| total web searches:", total_searches)

if __name__ == "__main__":
    main()
