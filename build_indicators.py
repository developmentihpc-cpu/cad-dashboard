#!/usr/bin/env python3
"""
build_indicators.py — bakes World Bank indicator data into a static JSON snapshot.

Why: the dashboard used to fire ~40 live World Bank API calls per country on every
page load. One failed request (network / CORS / rate-limit / sandbox) silently wiped
out the whole panel. This script pulls everything once, up front, into
docs/data/indicators.json, which the dashboard loads instantly. A monthly GitHub
Action re-runs it to keep the snapshot fresh (WB indicators update ~annually).

Single source of truth: the country list (COUNTRY_ISO) and the indicator IDs
(CA_INDICATORS) are parsed directly out of docs/index.html, so this script can never
drift from what the dashboard actually displays.

Efficiency: instead of country x indicator individual calls, it makes ONE request per
indicator against country/all (last 10 years), then keeps the most recent non-null value per
country. ~70 requests total. Government debt comes from the IMF World Economic Outlook
(DataMapper API) and keeps the previous values if the IMF cannot be reached.
It also rebuilds docs/data/sme_jobs.json (jobs by business size) from ILOSTAT labour force surveys.

Output shape (matches the dashboard's countryDataCache exactly):
    {
      "_meta": { "generated": "...", "source": "...", "countries": N, "indicators": M },
      "Ethiopia": { "NY.GDP.MKTP.KD.ZG": {"value": 6.1, "year": "2023"}, ... },
      ...
    }
"""
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
INDEX_HTML = ROOT / "docs" / "index.html"
OUT_PATH = ROOT / "docs" / "data" / "indicators.json"

WB_BASE = "https://api.worldbank.org/v2"
YEARS_BACK = 9     # look back 10 calendar years (survey data such as stunting or poverty is only
                   # collected every few years); the dashboard flags anything older than 8 years
PER_PAGE = 20000   # one page covers ~260 economies x 10 years = ~2,700 rows comfortably
TIMEOUT = 60
RETRIES = 3


def _read_index() -> str:
    if not INDEX_HTML.exists():
        sys.exit(f"ERROR: {INDEX_HTML} not found")
    return INDEX_HTML.read_text(encoding="utf-8")


def parse_country_iso(html: str) -> dict:
    """Extract the COUNTRY_ISO map (display name -> ISO3) from index.html."""
    m = re.search(r"const COUNTRY_ISO\s*=\s*\{(.*?)\n\};", html, re.DOTALL)
    if not m:
        sys.exit("ERROR: could not locate COUNTRY_ISO in index.html")
    block = m.group(1)
    pairs = re.findall(r"'((?:[^'\\]|\\.)*)'\s*:\s*'([A-Z]{3})'", block)
    out = {}
    for name, iso3 in pairs:
        out[name.replace("\\'", "'")] = iso3
    if not out:
        sys.exit("ERROR: parsed 0 countries from COUNTRY_ISO")
    return out


def parse_indicator_ids(html: str) -> list:
    """Extract unique World Bank indicator IDs from CA_INDICATORS in index.html.

    WB ids are uppercase letters / digits / dots (e.g. NY.GDP.MKTP.KD.ZG). The
    OEC special rows use lowercase '__oec_*' ids and are naturally excluded.
    """
    m = re.search(r"const CA_INDICATORS\s*=\s*\{(.*?)\n\};", html, re.DOTALL)
    if not m:
        sys.exit("ERROR: could not locate CA_INDICATORS in index.html")
    block = m.group(1)
    ids = re.findall(r"id\s*:\s*'([A-Z0-9.]+)'", block)
    seen, ordered = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i)
            ordered.append(i)
    if not ordered:
        sys.exit("ERROR: parsed 0 indicator IDs from CA_INDICATORS")
    return ordered


IMF_DEBT_ID = "IMF.GGXWDG_NGDP"   # general government gross debt, % of GDP (IMF World Economic Outlook)
IMF_URL = "https://www.imf.org/external/datamapper/api/v1/GGXWDG_NGDP"
IMF_ALIAS = {"XKX": "UVK"}        # Kosovo's code in IMF data


def fetch_imf_debt(country_isos) -> dict:
    """Return {iso3: {'value', 'year'}} with the latest IMF figure up to last year
    (the WEO also publishes projections, which are skipped). Empty dict on failure."""
    try:
        resp = requests.get(IMF_URL, timeout=TIMEOUT, headers={"User-Agent": "Mozilla/5.0 (CAD dashboard refresh)"})
        resp.raise_for_status()
        series = resp.json()["values"]["GGXWDG_NGDP"]
    except Exception as e:  # noqa: BLE001
        print(f"  ! IMF debt: request failed ({e}) - keeping previous values")
        return {}
    cap = datetime.now(timezone.utc).year - 1
    out = {}
    for iso3 in country_isos:
        ser = series.get(IMF_ALIAS.get(iso3, iso3)) or {}
        years = sorted((int(y) for y, v in ser.items() if v is not None and int(y) <= cap), reverse=True)
        if years:
            out[iso3] = {"value": ser[str(years[0])], "year": str(years[0])}
    return out


def fetch_indicator_all_countries(indicator_id: str) -> dict:
    """Return {iso3: {'value': float, 'year': 'YYYY'}} for one indicator, all countries.

    Keeps the most recent non-null observation per country.
    """
    url = f"{WB_BASE}/country/all/indicator/{indicator_id}"
    this_year = datetime.now(timezone.utc).year
    params = {"format": "json", "date": f"{this_year - YEARS_BACK}:{this_year}", "per_page": PER_PAGE}
    last_err = None
    for attempt in range(1, RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list) or len(data) < 2 or not data[1]:
                return {}
            best: dict = {}
            for row in data[1]:
                iso3 = row.get("countryiso3code")
                val = row.get("value")
                year = row.get("date")
                if not iso3 or val is None or year is None:
                    continue
                cur = best.get(iso3)
                # rows usually arrive newest-first; keep the newest year we see
                if cur is None or year > cur["year"]:
                    best[iso3] = {"value": val, "year": str(year)}
            return best
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.5 * attempt)
    print(f"  ! {indicator_id}: failed after {RETRIES} attempts ({last_err})")
    return {}


SME_PATH = ROOT / "docs" / "data" / "sme_jobs.json"
ILO_SME_URL = ("https://sdmx.ilo.org/rest/data/ILO,DF_EMP_TEMP_SEX_EST_NB/.A..SEX_T."
               "?startPeriod={start}&format=csvfilewithlabels")
SME_MIN_KNOWN = 50   # % of workers whose business size is known; below this the shares would mislead


def build_sme_jobs(country_isos) -> bool:
    """Write docs/data/sme_jobs.json: share of workers by size of the business they work in
    (ILOSTAT labour force surveys, 'Employment by sex and establishment size').

    For each country, the latest year with the aggregate bands (1-4, 5-49, 50+) is used.
    Shares are of workers whose business size is known; countries where it is known for
    fewer than SME_MIN_KNOWN % of workers are left out. ILO bands stop at 50+, so medium
    firms (50-249) are counted with large ones. Returns False (and leaves the previous
    file untouched) if the ILO cannot be reached.
    """
    import csv
    import io

    wanted = set(country_isos)
    start = datetime.now(timezone.utc).year - 14
    try:
        resp = requests.get(ILO_SME_URL.format(start=start), timeout=120,
                            headers={"User-Agent": "Mozilla/5.0 (CAD dashboard refresh)"})
        resp.raise_for_status()
        rows = list(csv.DictReader(io.StringIO(resp.content.decode("utf-8-sig"))))
    except Exception as e:  # noqa: BLE001
        print(f"  ! ILO business size: request failed ({e}) - keeping previous file")
        return False

    data: dict = {}   # iso3 -> year -> band -> persons (thousands)
    for r in rows:
        iso, band, year, val = r.get("REF_AREA"), r.get("EST"), r.get("TIME_PERIOD"), r.get("OBS_VALUE")
        if iso not in wanted or not band or not year or val in (None, ""):
            continue
        try:
            data.setdefault(iso, {}).setdefault(year, {})[band] = float(val)
        except ValueError:
            continue

    def r1(v):
        return round(v * 10) / 10

    out = {}
    for iso, years in data.items():
        usable = [y for y, b in years.items() if "EST_AGGREGATE_S5-49" in b and b.get("EST_AGGREGATE_TOTAL")]
        if not usable:
            continue
        year = max(usable)
        b = years[year]
        total, unknown = b["EST_AGGREGATE_TOTAL"], b.get("EST_AGGREGATE_X", 0.0)
        known = total - unknown
        if known <= 0 or 100 * unknown / total > 100 - SME_MIN_KNOWN:
            continue

        def pc(v):
            return None if v is None else r1(100 * v / known)

        rec = {
            "year": int(year),
            "under50": pc(b.get("EST_AGGREGATE_S1-4", 0.0) + b.get("EST_AGGREGATE_S5-49", 0.0)),
            "s1_4": pc(b.get("EST_AGGREGATE_S1-4")),
            "s5_49": pc(b.get("EST_AGGREGATE_S5-49")),
            "s50plus": pc(b.get("EST_AGGREGATE_SGE50")),
        }
        if "EST_DETAILS_S1" in b and "EST_DETAILS_S2-4" in b:
            rec["s1"], rec["s2_4"] = pc(b["EST_DETAILS_S1"]), pc(b["EST_DETAILS_S2-4"])
        if all(k in b for k in ("EST_DETAILS_S5-9", "EST_DETAILS_S10-19", "EST_DETAILS_S20-49")):
            rec["s5_9"] = pc(b["EST_DETAILS_S5-9"])
            rec["s10_49"] = pc(b["EST_DETAILS_S10-19"] + b["EST_DETAILS_S20-49"])
        rec["coverage"] = round(100 - 100 * unknown / total)
        out[iso] = rec

    if not out:
        print("  ! ILO business size: no usable rows - keeping previous file")
        return False
    payload = {
        "_meta": {
            "generated": datetime.now(timezone.utc).date().isoformat(),
            "source": "ILOSTAT, Employment by sex and establishment size (DF_EMP_TEMP_SEX_EST_NB), from national labour force surveys",
            "url": "https://ilostat.ilo.org/data/",
            "note": ("Shares of employment whose establishment size is known. ILO size bands stop at 50+, so medium-sized "
                     "firms (50–249) are counted with large ones. Countries are included only where firm size is known "
                     f"for at least {SME_MIN_KNOWN}% of all workers (coverage = that share)."),
        },
        **dict(sorted(out.items())),
    }
    SME_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"  business size: {len(out)} countries -> {SME_PATH.name}")
    return True


def fetch_regions(country_iso: dict) -> dict:
    """Return {region_name: [display names present]} from WB country metadata.

    One request to /country gives each economy's World Bank region; aggregates
    (region == 'Aggregates') are skipped. Matched back to our display names via ISO3.
    """
    iso3_to_name = {iso: name for name, iso in country_iso.items()}
    try:
        resp = requests.get(f"{WB_BASE}/country",
                            params={"format": "json", "per_page": 400}, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:  # noqa: BLE001
        print(f"  ! regions: failed ({e})")
        return {}
    rows = data[1] if isinstance(data, list) and len(data) > 1 and data[1] else []
    groups: dict = {}
    for row in rows:
        iso3 = row.get("id")
        region = ((row.get("region") or {}).get("value") or "").strip()
        if not iso3 or not region or region.lower() == "aggregates":
            continue
        name = iso3_to_name.get(iso3)
        if name is not None:
            groups.setdefault(region, []).append(name)
    return {r: sorted(set(groups[r])) for r in sorted(groups)}


def main() -> None:
    html = _read_index()
    country_iso = parse_country_iso(html)
    indicator_ids = parse_indicator_ids(html)
    iso3_to_name = {iso: name for name, iso in country_iso.items()}

    print(f"Countries: {len(country_iso)} | Indicators: {len(indicator_ids)}")
    print(f"Fetching from {WB_BASE} (one request per indicator)...")

    previous = {}   # last snapshot: fallback when a source cannot be reached this run
    if OUT_PATH.exists():
        try:
            previous = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            previous = {}

    out: dict = {name: {} for name in country_iso}
    filled = 0
    for n, ind in enumerate(indicator_ids, 1):
        by_iso = fetch_indicator_all_countries(ind)
        hits = 0
        for iso3, rec in by_iso.items():
            name = iso3_to_name.get(iso3)
            if name is not None:
                out[name][ind] = rec
                hits += 1
                filled += 1
        if not by_iso:   # request failed: keep the previous snapshot's values rather than blanking the indicator
            for name in country_iso:
                rec = (previous.get(name) or {}).get(ind)
                if rec:
                    out[name][ind] = rec
                    hits += 1
                    filled += 1
            print(f"  [{n:>2}/{len(indicator_ids)}] {ind:<22} {hits} countries (kept from previous snapshot)")
            continue
        print(f"  [{n:>2}/{len(indicator_ids)}] {ind:<22} {hits} countries")

    print("Fetching IMF government debt...")
    imf = fetch_imf_debt(country_iso.values())
    for name, iso3 in country_iso.items():
        rec = imf.get(iso3) or (previous.get(name) or {}).get(IMF_DEBT_ID)   # keep last good value if the IMF is unreachable
        if rec:
            out[name][IMF_DEBT_ID] = rec
            filled += 1
    print(f"  IMF debt: {len(imf)} fetched, {sum(1 for n in out if IMF_DEBT_ID in out[n])} countries in snapshot")

    print("Fetching World Bank regions...")
    regions = fetch_regions(country_iso)
    print(f"  regions: {len(regions)} ({sum(len(v) for v in regions.values())} memberships)")

    out = {name: vals for name, vals in out.items()}
    payload = {
        "_meta": {
            "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": "World Bank Open Data API (api.worldbank.org)",
            "countries": len(country_iso),
            "indicators": len(indicator_ids),
            "datapoints": filled,
        },
        "_regions": regions,
        **out,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"\nWrote {OUT_PATH} ({size_kb:.0f} KB, {filled} datapoints)")

    print("Fetching ILO jobs by business size...")
    build_sme_jobs(country_iso.values())


if __name__ == "__main__":
    main()
