#!/usr/bin/env python3
"""Build the Global Energy Analysis website from the research folder.

Reads the section briefs (Markdown) and the analysis workbooks in "ENERGY ANALYSIS"
and writes static HTML pages into the Website folder. The research files are only
read, never changed. Home page text lives in _build/homepage.md.

Usage (from the Master Energy folder):
    pip3 install markdown openpyxl
    python3 Website/_build/build_site.py

Optional: --src "<path to ENERGY ANALYSIS>"  --out "<path to Website>"

Data rules built in:
- Anything sourced from OilPriceAPI is left out (its trial terms may not allow republishing).
- Ember data is shown with its CC-BY-4.0 attribution.
- Internal sections of the briefs (download status, to-do lists, gaps, file lists) are left out.
"""
import argparse
import datetime
import glob
import html
import json
import os
import re

import markdown
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.dirname(HERE)
MASTER = os.path.dirname(SITE_DIR)

SECTIONS = [
    ("01_Market_Foundations_and_Data", "foundations", "Market Foundations", "Balances, agency views, macro and scenarios"),
    ("02_Upstream_Production_by_Source", "upstream", "Upstream Production", "Producers, costs, companies and minerals"),
    ("03_Midstream_Logistics_and_Transportation", "midstream", "Midstream Logistics", "Hormuz, storage, shipping and trade"),
    ("04_Downstream_Refining_and_End_Use", "downstream", "Downstream and Power", "Refining margins, fuels and electricity"),
    ("05_Regional_Markets_and_Geopolitics", "regions", "Regions and Geopolitics", "OPEC+, the Americas, demand hubs"),
    ("06_Policy_Regulation_and_Carbon", "policy", "Policy and Carbon", "COP31, EU ETS, CBAM and emissions"),
    ("07_Financial_Analysis_and_Trading", "finance", "Prices and Positioning", "Benchmarks, curves, funds and scenarios"),
]
EMBER = 'Source: <a href="https://ember-energy.org/data/yearly-electricity-data/" target="_blank" rel="noopener">Ember Yearly Electricity Data</a>, licensed CC-BY-4.0.'
BANNED = re.compile(r"oil\s*price\s*api", re.I)
INTERNAL_HEADINGS = re.compile(r"^(01\.1 Raw data downloads|What to update next|Gaps to fill|Gaps)\b", re.I)


# ---------------------------------------------------------------- helpers

def files(src, pattern):
    return sorted(glob.glob(os.path.join(src, pattern), recursive=True))


def latest(paths):
    return paths[-1] if paths else None


def esc(s):
    return html.escape("" if s is None else str(s))


def num(v):
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace("~", "").replace(",", "").replace("+", "").replace("(derived)", "").strip())
    except (ValueError, TypeError):
        return None


def sheet_rows(path, sheet):
    if not path:
        return []
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    if sheet not in wb.sheetnames:
        return []
    return [list(r) for r in wb[sheet].iter_rows(values_only=True) if any(c is not None for c in r)]


def table_rows(path, sheet):
    """Header + data rows, dropping trailing note rows (text in first cell only) and banned rows."""
    rows = sheet_rows(path, sheet)
    if not rows:
        return [], [], []
    head, body, notes = rows[0], [], []
    for r in rows[1:]:
        if r == head:
            continue
        if any(BANNED.search(str(c)) for c in r if c is not None):
            continue
        if r[0] is not None and all(c is None for c in r[1:]) and len(str(r[0])) > 40:
            notes.append(str(r[0]))
            continue
        body.append(r)
    return head, body, notes


def date_str(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.strftime("%Y-%m-%d")
    s = str(v)
    if re.fullmatch(r"\d{4}-\d{2}", s):
        return s + "-01"
    if re.fullmatch(r"\d{4}", s):
        return s + "-07-01"
    return s[:10]


def fmt_date(s):
    try:
        d = datetime.date.fromisoformat(date_str(s))
        return d.strftime("%-d %b %Y")
    except ValueError:
        return str(s)


def linkify(text):
    """Turn bare URLs inside a cell into short source links."""
    s = esc(text)
    def rep(m):
        url = m.group(0)
        host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
        return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (url, host)
    return re.sub(r"https?://[^\s;,)]+", rep, s)


# ---------------------------------------------------------------- briefs

def clean_brief(md):
    """Remove banned-source content and internal working notes from a brief."""
    md = re.sub(r"\*\*Live snapshot.*?(?=\n- \*\*Forecast deck)", "", md, flags=re.S)
    out, skip = [], False
    for line in md.splitlines():
        h = re.match(r"^(#{2,3})\s+(.*)", line)
        if h:
            skip = bool(INTERNAL_HEADINGS.match(h.group(2)))
        if skip:
            continue
        if BANNED.search(line):
            continue
        if re.match(r"^\s*-?\s*\*?Inferred:\*? Dubai and Murban", line) or "Dubai and Murban trade above Brent" in line:
            continue
        if re.match(r"^(New data files?|New files in this section|US detail files?|Two new workbooks lead|The US refining and power workbooks stay)", line):
            continue
        if re.match(r"^- `", line):
            continue
        line = re.sub(r"\s*Raw CSVs? (?:is|are) in [\w./ ]+?\.(?=\s|$)", "", line)
        line = re.sub(r"\s*\(tables and report saved in [^)]*\)", "", line)
        line = re.sub(r"New workbook: `[^`]+`\.\s*It ", "The data behind this section ", line)
        line = re.sub(r"This section and the new workbook `[^`]+` now anchor the brief\. The workbook ", "The data behind this section ", line)
        line = re.sub(r";\s*the US weekly and macro workbooks stay in [\d./]+ as detail\.", ".", line)
        line = re.sub(r"\s*\(v\d+: [^)]*\)", "", line)
        line = re.sub(r"\s*\(new lead section\)", "", line)
        if line.startswith("- ") and out and out[-1].strip() and not re.match(r"^\s*(- |\d+\. |\|)", out[-1]):
            out.append("")
        line = re.sub(r"\s*(?:The sheet|Sheets) `[^`]+`(?: and `[^`]+`)? [^.]*\.", "", line)
        line = re.sub(r"\s*Power-sector CO₂ for the last 12 months by region and country is in the 04\.2 global power workbook \(Ember\)\.", "", line)
        line = re.sub(r"\s*The US [\w-]+ workbook stays as detail\.", "", line)
        line = re.sub(r"\s*`[^`]*\.xlsx`", "", line)
        line = re.sub(r"\s*The numbers sit in the Key Indicators workbook \(v02\) in 01\.4\.", "", line)
        out.append(line)
    return "\n".join(out)


def md_to_html(text):
    body = markdown.markdown(text, extensions=["tables", "sane_lists"])
    for folder, slug, _, _ in SECTIONS:
        body = re.sub(r'href="[^"]*%s/[^"]*\.md"' % re.escape(folder), 'href="%s.html"' % slug, body)
    body = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body)
    body = body.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
    return body


def split_title(md):
    lines = md.strip().splitlines()
    if lines and lines[0].startswith("# "):
        return lines[0][2:].strip(), "\n".join(lines[1:])
    return "", md


def brief_versions(src, folder):
    """All editions of a section brief, oldest first: the current one in the section folder, earlier ones in 99_Archive/<section>."""
    paths = files(src, os.path.join(folder, "*_Analysis_*_Global_v*.md")) + files(src, os.path.join("99_Archive", folder, "*_Analysis_*_Global_v*.md"))
    return sorted(paths, key=os.path.basename)


# ---------------------------------------------------------------- chart specs

def series_from(rows, head, col_name, start=None, scale=1.0, reverse=True):
    """[[iso_date, value], ...] for one column of a time-series sheet (newest-first sheets are reversed)."""
    if col_name not in head:
        return []
    i = head.index(col_name)
    pts = []
    for r in rows:
        d, v = r[0], num(r[i]) if i < len(r) else None
        if d is None or v is None:
            continue
        ds = date_str(d)
        if start and ds < start:
            continue
        pts.append([ds, round(v * scale, 3)])
    pts.sort()
    return pts


def chart(cid, title, spec, source, note="", table=None):
    spec = dict(spec, id=cid)
    return {"id": cid, "title": title, "spec": spec, "source": source, "note": note, "table": table}


def build_charts(src):
    W = lambda pat: latest(files(src, pat))
    C = {}
    prices = W("07_Financial_Analysis_and_Trading/**/*Energy_Prices_and_Positioning*.xlsx")
    storage = W("03_Midstream_Logistics_and_Transportation/**/*US_Storage_and_Trade*.xlsx")
    refining = W("04_Downstream_Refining_and_End_Use/**/*Refining_Margins*.xlsx")
    power = W("04_Downstream_Refining_and_End_Use/**/*US_Power_Generation*.xlsx")
    costs = W("02_Upstream_Production_by_Source/**/*Production_Costs_Benchmarks*.xlsx")
    country = W("02_Upstream_Production_by_Source/*Upstream_Production_by_Country*.xlsx")
    crude_m = W("02_Upstream_Production_by_Source/**/*Crude_Production_by_Country*.xlsx")
    keyind = W("01_Market_Foundations_and_Data/01.4_Supply_Demand_Balances/*Key_Indicators*.xlsx")
    co2 = W("06_Policy_Regulation_and_Carbon/**/*CO2_Emissions*.xlsx")

    # --- Prices
    h, rows, _ = table_rows(prices, "Daily")
    if rows:
        C["brent_wti"] = chart("brent_wti", "Brent and WTI spot, daily ($/bbl)", {
            "type": "line", "unit": "$/bbl", "series": [
                {"name": "Brent", "slot": 1, "data": series_from(rows, h, "Brent spot ($/bbl)")},
                {"name": "WTI", "slot": 2, "data": series_from(rows, h, "WTI spot ($/bbl)")}]},
            "Source: EIA spot prices via FRED. Spot data lag futures by about a week.")
        C["henry_hub"] = chart("henry_hub", "Henry Hub gas spot, daily ($/MMBtu)", {
            "type": "line", "unit": "$/MMBtu", "decimals": 2, "series": [
                {"name": "Henry Hub", "slot": 1, "data": series_from(rows, h, "Henry Hub spot ($/MMBtu)")}]},
            "Source: EIA via FRED.")
    h, rows, _ = table_rows(prices, "Weekly_Retail")
    if rows:
        C["retail"] = chart("retail", "US retail fuel prices, weekly ($/gal)", {
            "type": "line", "unit": "$/gal", "decimals": 2, "series": [
                {"name": "Diesel", "slot": 1, "data": series_from(rows, h, "US retail diesel ($/gal)", "2022-01-01")},
                {"name": "Gasoline", "slot": 2, "data": series_from(rows, h, "US retail regular gasoline ($/gal)", "2022-01-01")}]},
            "Source: EIA via FRED.")
    h, rows, _ = table_rows(prices, "Monthly_IMF")
    if rows:
        C["gas_intl"] = chart("gas_intl", "European and Asian gas prices, monthly ($/MMBtu)", {
            "type": "line", "unit": "$/MMBtu", "decimals": 1, "series": [
                {"name": "Japan LNG", "slot": 1, "data": series_from(rows, h, "Japan LNG import price (IMF) ($/MMBtu)", "2021-01-01")},
                {"name": "Europe gas (TTF-linked)", "slot": 2, "data": series_from(rows, h, "Europe natural gas (TTF-linked, IMF) ($/MMBtu)", "2021-01-01")}]},
            "Source: IMF primary commodity prices via FRED (monthly averages, about six weeks' lag).")
    h, rows, _ = table_rows(prices, "COT_Managed_Money")
    if rows:
        def cot(market):
            return sorted([[date_str(r[0]), num(r[6])] for r in rows if r[1] == market and num(r[6]) is not None])
        C["cot"] = chart("cot", "Hedge fund positioning: managed-money net, % of open interest", {
            "type": "line", "unit": "%", "decimals": 1, "zero": True, "series": [
                {"name": "WTI crude", "slot": 1, "data": cot("WTI-PHYSICAL - NEW YORK MERCANTILE EXCHANGE")},
                {"name": "Henry Hub gas", "slot": 2, "data": cot("NAT GAS NYME - NEW YORK MERCANTILE EXCHANGE")}]},
            "Source: CFTC Disaggregated Commitments of Traders, weekly. Above zero means funds are net long.")

    # --- Midstream
    h, rows, _ = table_rows(storage, "EU_Storage_Same_Date")
    if rows:
        def dm(s):
            d, m = s.split("-")
            return "2026-%s-%s" % (m, d)
        def col(name):
            i = h.index(name)
            return [[dm(r[0]), num(r[i])] for r in rows if num(r[i]) is not None]
        band = []
        for r in rows:
            vals = [num(r[h.index("%d %% full" % y)]) for y in (2021, 2022, 2023, 2024)]
            vals = [v for v in vals if v is not None]
            if vals:
                band.append([dm(r[0]), min(vals), max(vals)])
        C["eu_storage"] = chart("eu_storage", "EU gas storage, % full, by date", {
            "type": "line", "unit": "%", "decimals": 1, "xfmt": "month", "yMax": 100, "series": [
                {"name": "2026", "slot": 1, "data": col("2026 % full")},
                {"name": "2025", "slot": 2, "data": col("2025 % full")}],
            "band": {"name": "2021–24 range", "data": band}},
            "Source: GIE AGSI+ (Gas Infrastructure Europe), 1st and 15th of each month.")
    h, rows, _ = table_rows(storage, "Storage_Weekly")
    if rows:
        C["us_distillate"] = chart("us_distillate", "US distillate stocks, weekly (million barrels)", {
            "type": "line", "unit": "mb", "decimals": 1, "series": [
                {"name": "Distillate stocks", "slot": 1, "data": series_from(rows, h, "US distillate stocks (kb)", scale=0.001)}]},
            "Source: EIA Weekly Petroleum Status Report.")
        C["us_crude_stocks"] = chart("us_crude_stocks", "US crude stocks, weekly (million barrels)", {
            "type": "line", "unit": "mb", "decimals": 1, "series": [
                {"name": "Commercial (ex SPR)", "slot": 1, "data": series_from(rows, h, "US commercial crude stocks (ex SPR) (kb)", scale=0.001)},
                {"name": "Strategic reserve (SPR)", "slot": 2, "data": series_from(rows, h, "US SPR stocks (kb)", scale=0.001)}]},
            "Source: EIA Weekly Petroleum Status Report.")

    # --- Downstream
    h, rows, _ = table_rows(refining, "Crack_3-2-1_Monthly")
    if rows:
        C["crack"] = chart("crack", "NY Harbor 3-2-1 crack spread vs WTI, monthly ($/bbl)", {
            "type": "line", "unit": "$/bbl", "decimals": 1, "series": [
                {"name": "3-2-1 crack", "slot": 1, "data": series_from(rows, h, "3-2-1 crack vs WTI ($/bbl)")}]},
            "Source: calculated from EIA spot prices (NYH gasoline and ULSD against WTI Cushing). Latest month is partial.")
    h, rows, _ = table_rows(refining, "Refining_Weekly")
    if rows:
        C["utilisation"] = chart("utilisation", "US refinery utilisation, weekly (%)", {
            "type": "line", "unit": "%", "decimals": 1, "series": [
                {"name": "Utilisation", "slot": 1, "data": series_from(rows, h, "US refinery utilisation (%)", "2023-01-01")}]},
            "Source: EIA Weekly Petroleum Status Report.")
    h, rows, _ = table_rows(power, "Ember_Share_%")
    if rows:
        world = sorted([r for r in rows if r[0] == "World"], key=lambda r: r[1])
        ci, wi, si = h.index("Coal"), h.index("Wind"), h.index("Solar")
        C["world_mix"] = chart("world_mix", "World electricity: coal vs wind and solar, share of generation (%)", {
            "type": "line", "unit": "%", "decimals": 1, "xfmt": "year", "zero": True, "series": [
                {"name": "Coal", "slot": 1, "data": [[date_str(r[1]), r[ci]] for r in world]},
                {"name": "Wind + solar", "slot": 2, "data": [[date_str(r[1]), round(r[wi] + r[si], 1)] for r in world]}]},
            EMBER)
    h, rows, _ = table_rows(power, "Generation_Share_%")
    if rows:
        last = rows[0]
        cats = h[1:]
        C["us_mix"] = chart("us_mix", "US electricity generation by fuel, %s (%% share)" % datetime.date.fromisoformat(date_str(last[0])).strftime("%B %Y"), {
            "type": "bar", "unit": "%", "decimals": 1, "categories": cats,
            "series": [{"name": "Share", "slot": 1, "values": [num(v) for v in last[1:]]}]},
            "Source: EIA Electric Power Monthly.")

    # --- Upstream
    h, rows, _ = table_rows(country, "Oil_2025")
    if rows:
        rows = [r for r in rows if r[0] != "World" and num(r[1]) is not None][:12]
        C["oil_producers"] = chart("oil_producers", "Largest oil producers, 2025 (kb/d, crude + condensate + NGL)", {
            "type": "bar", "unit": "kb/d", "decimals": 0, "categories": [r[0] for r in rows],
            "series": [{"name": "2025", "slot": 1, "values": [num(r[1]) for r in rows]}]},
            "Source: Energy Institute Statistical Review of World Energy 2026. Brazil is derived from its share.")
    h, rows, _ = table_rows(crude_m, "Crude_Production_Monthly")
    if rows:
        C["gulf_crude"] = chart("gulf_crude", "Gulf crude output, monthly (kb/d)", {
            "type": "line", "unit": "kb/d", "decimals": 0, "zero": True, "series": [
                {"name": "Saudi Arabia", "slot": 1, "data": series_from(rows, h, "Saudi Arabia (kb/d)", "2024-01-01")},
                {"name": "UAE", "slot": 2, "data": series_from(rows, h, "UAE (kb/d)", "2024-01-01")},
                {"name": "Iraq", "slot": 3, "data": series_from(rows, h, "Iraq (kb/d)", "2024-01-01")},
                {"name": "Kuwait", "slot": 4, "data": series_from(rows, h, "Kuwait (kb/d)", "2024-01-01")}]},
            "Source: EIA international energy data. EIA's country data lag by about four months.")
    h, rows, _ = table_rows(costs, "Shale_Breakevens_2026")
    if rows:
        rows = [r for r in rows if num(r[1]) is not None]
        C["breakevens"] = chart("breakevens", "US shale breakevens by play, 2026 (WTI $/bbl)", {
            "type": "bar", "unit": "$/bbl", "decimals": 0, "categories": [r[0] for r in rows],
            "series": [{"name": "New well", "slot": 1, "values": [num(r[1]) for r in rows]},
                       {"name": "Existing wells (opex)", "slot": 2, "values": [num(r[2]) for r in rows]}]},
            'Source: <a href="https://www.dallasfed.org/research/surveys/des/2026/2601" target="_blank" rel="noopener">Dallas Fed Energy Survey</a>, Q1 2026.')
    h, rows, _ = table_rows(costs, "LCOE_Lazard_2026")
    if rows:
        rows = [r for r in rows if num(r[1]) is not None]
        C["lcoe"] = chart("lcoe", "Cost of new power, unsubsidised LCOE range ($/MWh)", {
            "type": "range", "unit": "$/MWh", "decimals": 0,
            "rows": [[re.sub(r"\s*\(.*\)", "", r[0]), num(r[1]), num(r[2])] for r in rows]},
            "Source: Lazard LCOE+ 2026 (July 2026).")

    # --- Foundations / regions
    h, rows, _ = table_rows(keyind, "Agency_Comparison")
    if rows:
        rows = [r for r in rows if num(r[1]) is not None and "Nov" not in str(r[0])]
        C["agencies"] = chart("agencies", "How far apart the agencies are: 2026 oil demand vs call on OPEC+ crude (mb/d)", {
            "type": "bar", "unit": "mb/d", "decimals": 1, "categories": [re.sub(r"\s*\(.*\)", "", r[0]) for r in rows],
            "series": [{"name": "2026 world demand", "slot": 1, "values": [num(r[1]) for r in rows]},
                       {"name": "Call on OPEC+ crude, 4Q26", "slot": 2, "values": [num(r[5]) for r in rows]}]},
            "Sources: IEA OMR, OPEC MOMR and EIA STEO (October 2026 editions), compiled by the IEF.")
    h, rows, _ = table_rows(country, "OPECplus_2026")
    if rows:
        rows = [r for r in rows if num(r[1]) is not None and "total" not in str(r[0]).lower() and "OPEC (" not in str(r[0])][:6]
        C["opec_shock"] = chart("opec_shock", "Gulf producers before, during and after the shock (kb/d)", {
            "type": "bar", "unit": "kb/d", "decimals": 0, "categories": [re.sub(r"\s*\(.*\)", "", r[0]) for r in rows],
            "series": [{"name": "Feb 2026", "slot": 1, "values": [num(r[1]) for r in rows]},
                       {"name": "Q2 2026", "slot": 2, "values": [num(r[2]) for r in rows]},
                       {"name": "Sep 2026", "slot": 3, "values": [num(r[3]) for r in rows]}]},
            "Source: OPEC MOMR October 2026, secondary sources.")

    # --- Policy
    h, rows, _ = table_rows(co2, "Power_CO2_Ember")
    if rows:
        world = sorted([r for r in rows if r[0] == "World"], key=lambda r: r[1])
        C["power_co2"] = chart("power_co2", "World power sector: carbon intensity (gCO₂e per kWh)", {
            "type": "line", "unit": "g/kWh", "decimals": 0, "xfmt": "year", "series": [
                {"name": "Carbon intensity", "slot": 1, "data": [[date_str(r[1]), round(r[3], 1)] for r in world]}]},
            EMBER)

    # --- Global, country-level (EIA international, JODI, Ember monthly)
    bal = W("01_Market_Foundations_and_Data/01.4_Supply_Demand_Balances/*Global_Energy_Balance_by_Country*.xlsx")
    gprod = W("02_Upstream_Production_by_Source/*Global_Production_by_Country*.xlsx")
    trade = W("03_Midstream_Logistics_and_Transportation/**/*Global_Energy_Trade_and_Stocks*.xlsx")
    gpow = W("04_Downstream_Refining_and_End_Use/**/*Global_Power_Generation*.xlsx")
    gco2 = W("06_Policy_Regulation_and_Carbon/**/*Global_CO2_by_Country*.xlsx")

    def ranked(path, sheet, n=10):
        head, body, _ = table_rows(path, sheet)
        if not head:
            return None, []
        years = [h for h in head if re.fullmatch(r"\d{4}", str(h))]
        last = years[-1]
        li = head.index(last)
        out = [(r[1], num(r[li])) for r in body if isinstance(r[0], (int, float)) and num(r[li]) is not None]
        return last, out[:n], head, body, years

    def bar_rank(cid, path, sheet, title, unit, source, n=10, dec=0):
        res = ranked(path, sheet, n)
        if not res[1]:
            return
        last, top = res[0], res[1]
        C[cid] = chart(cid, title % last, {"type": "bar", "unit": unit, "decimals": dec,
                       "categories": [t[0] for t in top], "series": [{"name": str(last), "slot": 1, "values": [t[1] for t in top]}]}, source)

    EIA_INTL = "Source: EIA international energy data (annual)."
    h, rows, _ = table_rows(bal, "World_and_Regions")
    if rows:
        regs = [c for c in h[3:] if c not in ("World", "OECD") and c]
        def regrow(metric):
            for r in rows:
                if r[0] == metric:
                    return r
        prod, cons = regrow("Crude oil production"), regrow("Oil consumption")
        tl = regrow("Total liquids production")
        if tl and cons:
            C["regions_oil"] = chart("regions_oil", "Oil supply vs demand by region (kb/d)", {
                "type": "bar", "unit": "kb/d", "decimals": 0, "categories": regs,
                "series": [{"name": "Liquids production, %s" % tl[2], "slot": 1, "values": [num(tl[h.index(c)]) for c in regs]},
                           {"name": "Oil consumption, %s" % cons[2], "slot": 2, "values": [num(cons[h.index(c)]) for c in regs]}]},
                EIA_INTL + " Asia & Oceania burns 37% of the world's oil but produces 9%; the Middle East is the reverse.")
    bar_rank("oil_demand_top", bal, "Oil consumption", "Largest oil consumers, %s (kb/d)", "kb/d", EIA_INTL)
    bar_rank("gas_exporters", trade, "Gas exports (pipeline + LNG)", "Largest gas exporters, pipeline + LNG, %s (bcm)", "bcm", EIA_INTL, dec=1)
    bar_rank("energy_use_top", bal, "Primary energy consumption", "Largest energy consumers, %s (quadrillion Btu)", "quad Btu", EIA_INTL, dec=1)

    res = ranked(gco2, "Energy CO2 emissions", 4)
    if res[1]:
        _, top, head, body, years = res
        names = [t[0] for t in top]
        ser = []
        for i, nm in enumerate(names):
            r = next(b for b in body if b[1] == nm)
            ser.append({"name": nm, "slot": i + 1, "data": [[date_str(y), num(r[head.index(y)])] for y in years if num(r[head.index(y)]) is not None]})
        C["co2_lines"] = chart("co2_lines", "Energy CO₂ emissions, four largest emitters (Mt CO₂)", {
            "type": "line", "unit": "Mt", "decimals": 0, "xfmt": "year", "zero": True, "series": ser}, EIA_INTL)

    def jodi(path, sheet, countries, title, note):
        head, body, notes = table_rows(path, sheet)
        if not head:
            return None
        months = [m for m in head if re.fullmatch(r"\d{4}-\d{2}", str(m))]
        ser = []
        for i, cn in enumerate(countries):
            r = next((b for b in body if b[0] == cn), None)
            if r:
                ser.append({"name": cn.replace("Korea, Republic of", "South Korea"), "slot": i + 1,
                            "data": [[m + "-01", num(r[head.index(m)])] for m in months if num(r[head.index(m)]) is not None]})
        return {"type": "line", "unit": "kb/d", "decimals": 0, "zero": True, "series": ser}
    JODI = 'Source: <a href="https://www.jodidata.org/" target="_blank" rel="noopener">JODI Oil World Database</a>, as reported by national administrations. Russia, Iraq, the UAE and Iran have not reported 2026 data.'
    sp = jodi(gprod, "JODI_Crude_Production_Monthly", ["Saudi Arabia", "Kuwait", "Brazil", "Guyana"], "", "")
    if sp:
        C["jodi_crude"] = chart("jodi_crude", "Crude output: the Gulf vs the Americas, monthly (kb/d)", sp, JODI)
    sp = jodi(trade, "JODI_Crude_Imports_Monthly", ["China", "Korea, Republic of", "Japan", "Germany"], "", "")
    if sp:
        C["jodi_imports"] = chart("jodi_imports", "Crude imports of the largest buyers, monthly (kb/d)", sp, JODI)

    h, rows, _ = table_rows(gpow, "Mix_Last_12m")
    if rows:
        want = ["World", "EU", "China", "United States", "India", "Japan", "Brazil", "Germany", "United Kingdom", "Australia", "Middle East"]
        ws = h.index("Wind+solar share %")
        pick = [(r[0], num(r[ws])) for r in rows if r[0] in want and num(r[ws]) is not None]
        pick.sort(key=lambda x: -x[1])
        C["ws_share"] = chart("ws_share", "Wind and solar share of electricity, last 12 months (%)", {
            "type": "bar", "unit": "%", "decimals": 1, "categories": [p[0] for p in pick],
            "series": [{"name": "Wind + solar", "slot": 1, "values": [p[1] for p in pick]}]},
            'Source: <a href="https://ember-energy.org/data/monthly-electricity-data/" target="_blank" rel="noopener">Ember monthly electricity data</a>, licensed CC-BY-4.0. 12 months to August 2026.')
    return C


SECTION_CHARTS = {
    "foundations": ["regions_oil", "oil_demand_top", "agencies", "energy_use_top"],
    "upstream": ["oil_producers", "jodi_crude", "breakevens", "lcoe"],
    "midstream": ["eu_storage", "jodi_imports", "gas_exporters", "us_crude_stocks"],
    "downstream": ["ws_share", "world_mix", "crack", "retail"],
    "regions": ["regions_oil", "jodi_crude", "opec_shock", "gas_intl"],
    "policy": ["co2_lines", "power_co2", "ws_share", "world_mix"],
    "finance": ["brent_wti", "gas_intl", "henry_hub", "cot", "retail"],
}
HOME_CHARTS = ["brent_wti", "eu_storage", "jodi_crude", "ws_share"]
DATA_GROUPS = [
    ("Global picture", ["regions_oil", "oil_demand_top", "energy_use_top", "gas_exporters", "co2_lines", "ws_share"]),
    ("Prices and positioning", ["brent_wti", "gas_intl", "henry_hub", "retail", "cot"]),
    ("Supply", ["jodi_crude", "opec_shock", "gulf_crude", "oil_producers", "agencies", "breakevens"]),
    ("Trade, storage and logistics", ["jodi_imports", "eu_storage", "us_crude_stocks", "us_distillate"]),
    ("Refining and power", ["crack", "utilisation", "world_mix", "us_mix", "lcoe", "power_co2"]),
]


def render_chart(c, wide=False):
    spec = c["spec"]
    # data table for the "Show data" view (last 24 points for long series)
    if spec["type"] == "line":
        names = [s["name"] for s in spec["series"]]
        xs = sorted({p[0] for s in spec["series"] for p in s["data"]})
        lookup = [{p[0]: p[1] for p in s["data"]} for s in spec["series"]]
        shown = xs[-24:]
        head = "<tr><th>Date</th>%s</tr>" % "".join("<th>%s</th>" % esc(n) for n in names)
        body = "".join("<tr><td>%s</td>%s</tr>" % (esc(x), "".join("<td>%s</td>" % esc(l.get(x, "")) for l in lookup)) for x in reversed(shown))
        extra = "<p class=\"note\">Latest %d of %d points shown.</p>" % (len(shown), len(xs)) if len(xs) > len(shown) else ""
    elif spec["type"] == "bar":
        head = "<tr><th></th>%s</tr>" % "".join("<th>%s</th>" % esc(s["name"]) for s in spec["series"])
        body = "".join("<tr><td>%s</td>%s</tr>" % (esc(cat), "".join("<td>%s</td>" % esc(s["values"][i]) for s in spec["series"])) for i, cat in enumerate(spec["categories"]))
        extra = ""
    else:
        head = "<tr><th></th><th>Low</th><th>High</th></tr>"
        body = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(r[0]), esc(r[1]), esc(r[2])) for r in spec["rows"])
        extra = ""
    return """<figure class="chart{w}" id="{id}">
  <figcaption>{t}</figcaption>
  <div class="viz" data-spec='{spec}'></div>
  <p class="note">{src}{note}</p>
  <details><summary>Show data</summary><div class="tablewrap"><table><thead>{head}</thead><tbody>{body}</tbody></table></div>{extra}</details>
</figure>""".format(w=" wide" if wide else "", id=esc(c["id"]), t=esc(c["title"]),
                    spec=html.escape(json.dumps(spec, separators=(",", ":")), quote=True),
                    src=c["source"], note=(" " + c["note"]) if c["note"] else "", head=head, body=body, extra=extra)


# ---------------------------------------------------------------- page shell

TOP_NAV = [("index", "Overview"), ("research", "Research"), ("data", "Data"), ("companies", "Companies"), ("about", "About")]
SECTION_SLUGS = [s[1] for s in SECTIONS]


def page(slug, title, body, description="", hero=""):
    links = []
    for s, t in TOP_NAV:
        if s == "research":
            cur = slug in SECTION_SLUGS or slug == "review" or slug.split("-")[0] in SECTION_SLUGS
            items = "".join('<a href="%s.html"%s><span>%s</span>%s</a>' % (sl, ' aria-current="page"' if sl == slug else "", f[:2], esc(n))
                            for f, sl, n, _ in SECTIONS)
            items += '<a href="review.html"%s><span>Arc</span>October market review</a>' % (' aria-current="page"' if slug == "review" else "")
            links.append('<div class="drop"><button type="button" class="droptoggle%s" aria-expanded="false">Research <span aria-hidden="true">▾</span></button><div class="dropmenu">%s</div></div>' % (" current" if cur else "", items))
        else:
            links.append('<a href="%s.html"%s>%s</a>' % (s, ' aria-current="page"' if s == slug else "", esc(t)))
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Global Energy Analysis</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="assets/style.css">
<script>try{{var t=localStorage.getItem('theme');if(t)document.documentElement.setAttribute('data-theme',t)}}catch(e){{}}</script>
</head>
<body>
<header class="topbar">
  <div class="wrap bar">
    <a class="brand" href="index.html"><span class="mark" aria-hidden="true"></span>Global Energy Analysis</a>
    <nav id="nav" class="topnav">{links}</nav>
    <div class="tools">
      <button class="theme" type="button" aria-label="Switch light or dark theme">◐</button>
      <button class="menu" type="button" aria-expanded="false" aria-controls="nav">Menu</button>
    </div>
  </div>
</header>
{hero}
<main class="wrap">
{body}
</main>
<footer>
  <div class="wrap foot">
    <div><strong>Global Energy Analysis</strong> · by Kolan Sai Kiran Reddy<p>Independent research on global energy markets. Figures are as published by the cited sources; lines marked <em>inferred</em> and the calls on the overview are analytical judgement, not published data. Not investment advice.</p></div>
    <div class="footlinks"><a href="research.html">Research</a><a href="data.html">Data</a><a href="companies.html">Companies</a><a href="about.html#sources">Sources and licences</a></div>
  </div>
</footer>
<script src="assets/site.js"></script>
</body>
</html>
""".format(title=esc(title), desc=esc(description), links="".join(links), body=body, hero=hero)


# ---------------------------------------------------------------- pages

def stat_tiles(src):
    W = lambda pat: latest(files(src, pat))
    tiles = []
    def from_latest(path, series, label, unit, scale=1.0, dec=1, pre=""):
        h, rows, _ = table_rows(path, "Latest")
        for r in rows:
            if r[0] == series and num(r[4]) is not None:
                v = num(r[4]) * scale
                yy = num(r[9])
                chg = ("%+.0f%% y/y" % yy) if yy is not None else ""
                tiles.append((pre + ("{:,.%df}" % dec).format(v), unit, label, "%s · %s" % (fmt_date(r[3]), chg) if chg else fmt_date(r[3]), yy))
                return
    prices = W("07_Financial_Analysis_and_Trading/**/*Energy_Prices_and_Positioning*.xlsx")
    storage = W("03_Midstream_Logistics_and_Transportation/**/*US_Storage_and_Trade*.xlsx")
    refining = W("04_Downstream_Refining_and_End_Use/**/*Refining_Margins*.xlsx")
    from_latest(prices, "Brent spot", "Brent spot", "/bbl", dec=2, pre="$")
    from_latest(prices, "Europe natural gas (TTF-linked, IMF)", "European gas (TTF-linked)", "/MMBtu", dec=2, pre="$")
    from_latest(prices, "Japan LNG import price (IMF)", "Japan LNG import price", "/MMBtu", dec=2, pre="$")
    from_latest(storage, "EU gas storage, % full", "EU gas storage", "% full", dec=1)
    gprod = W("02_Upstream_Production_by_Source/*Global_Production_by_Country*.xlsx")
    h, rows, _ = table_rows(gprod, "JODI_Crude_Production_Monthly")
    for r in rows:
        if r[0] == "Saudi Arabia" and "Latest" in h:
            v, m, yy = num(r[h.index("Latest")]), r[h.index("Latest month")], num(r[h.index("y/y % (same month)")])
            tiles.append(("{:,.0f}".format(v), "kb/d", "Saudi crude output", "%s · %+.0f%% y/y" % (fmt_date(m)[2:] if fmt_date(m)[0].isdigit() else m, yy), yy))
    gpow = W("04_Downstream_Refining_and_End_Use/**/*Global_Power_Generation*.xlsx")
    h, rows, _ = table_rows(gpow, "Mix_Last_12m")
    for r in rows:
        if r[0] == "World":
            ch = num(r[h.index("Wind+solar share change (pts)")])
            tiles.append(("%.1f" % num(r[h.index("Wind+solar share %")]), "%", "World wind + solar share", "12 months to Aug 2026" + (" · %+.1f pts" % ch if ch is not None else ""), None))
    return "".join('<div class="stat"><div class="cap">{l}</div><div class="num">{v}<span>{u}</span></div><div class="sub">{s}</div></div>'.format(
        l=esc(l), v=esc(v), u=esc(u), s=esc(s)) for v, u, l, s, _ in tiles)


def parse_home(path):
    with open(path, encoding="utf-8") as f:
        text = re.sub(r"<!--.*?-->", "", f.read(), flags=re.S)
    head, *blocks = re.split(r"^## ", text, flags=re.M)
    meta = dict(re.findall(r"^(\w+):\s*(.+)$", head, flags=re.M))
    calls, watch = [], ""
    for b in blocks:
        kind, _, rest = b.partition("\n")
        if kind.strip() == "call":
            m = dict(re.findall(r"^(title|link):\s*(.+)$", rest, flags=re.M))
            body = re.sub(r"^(title|link):.*$\n?", "", rest, flags=re.M).strip()
            calls.append((m.get("title", ""), m.get("link", "#"), body))
        elif kind.strip() == "watch":
            watch = rest.strip()
    return meta, calls, watch


def scenarios_table(src):
    for p in reversed(brief_versions(src, "07_Financial_Analysis_and_Trading")):
        with open(p, encoding="utf-8") as f:
            m = re.search(r"(\| Assumption \| Reopening.*?)(\n\n|\Z)", f.read(), re.S)
        if m:
            return md_to_html(m.group(1))
    return ""


def research_items(src):
    """(date, section label, slug, title, excerpt) for the latest brief in each section."""
    items = []
    for folder, slug, name, _ in SECTIONS:
        v = brief_versions(src, folder)
        if not v:
            continue
        with open(v[-1], encoding="utf-8") as f:
            title, rest = split_title(clean_brief(f.read()))
        exc = ""
        m = re.search(r"## Big picture\s*\n+(.+?)\n", rest)
        if m:
            exc = m.group(1)
        else:
            for line in rest.splitlines():
                if line.startswith("- **") and not BANNED.search(line):
                    exc = line
                    break
        exc = re.sub(r"\*\*|\*|`|^- ", "", exc)
        exc = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", exc)
        if len(exc) > 230:
            exc = exc[:230].rsplit(" ", 1)[0] + "…"
        b = os.path.basename(v[-1])
        items.append(("%s-%s-%s" % (b[:4], b[4:6], b[6:8]), "%s · %s" % (folder[:2], name), slug, re.sub(r"^\d+\s+", "", title.split(":")[0]), exc))
    return items


def research_list(items):
    return '<ol class="insights">%s</ol>' % "".join(
        '<li><a href="{s}.html"><span class="meta">{sec} <time>{d}</time></span><h3>{t}</h3><p>{e}</p><span class="arrow">Read the brief →</span></a></li>'.format(
            s=slug, sec=esc(sec), d=esc(fmt_date(d)), t=esc(t), e=esc(e)) for d, sec, slug, t, e in items)


def build_home(src, charts, meta, calls, watch):
    call_html = "".join(
        '<article class="call"><span class="no">{n:02d}</span><h3>{t}</h3><div>{b}</div><a class="more" href="{l}">See the evidence →</a></article>'.format(
            n=i + 1, t=esc(t), b=md_to_html(b), l=esc(l)) for i, (t, l, b) in enumerate(calls))
    featured = "".join(render_chart(charts[c]) for c in HOME_CHARTS if c in charts)
    hero = """<section class="hero"><div class="wrap">
  <p class="eyebrow">{ed} · The view · Kolan Sai Kiran Reddy</p>
  <h1>{h}</h1>
  <p class="lede">{lede}</p>
  <p class="cta"><a href="#calls">Read the five calls →</a><a href="data.html">Explore the data →</a></p>
  <div class="stats">{tiles}</div>
</div></section>""".format(ed=esc(meta.get("edition", "")), h=esc(meta.get("headline", "")), lede=esc(meta.get("lede", "")), tiles=stat_tiles(src))
    body = """
<section id="calls"><div class="sechead"><h2>Five calls</h2><p class="muted">Where I think the 2026 shock goes next. Each call links to the evidence.</p></div><div class="calls">{calls}</div></section>
<section><div class="sechead"><h2>The evidence</h2><a class="textlink" href="data.html">All charts and data →</a></div><div class="charts two">{featured}</div></section>
<section class="split">
  <div><div class="sechead"><h2>Three cases for 2027</h2></div><p class="muted">The scenario frame used across the research. The EIA's November outlook sits at the low end of the reopening case.</p><div class="prose">{scen}</div></div>
  <div class="watchbox"><h2>Watch list</h2><div class="prose watch">{watch}</div></div>
</section>
<section><div class="sechead"><h2>Latest research</h2><a class="textlink" href="research.html">All research →</a></div>{research}</section>
""".format(calls=call_html, featured=featured, scen=scenarios_table(src), watch=md_to_html(watch), research=research_list(research_items(src)))
    return page("index", "Overview", body, meta.get("headline", ""), hero=hero)


def build_research_index(src):
    body = """<header class="pagehead"><p class="eyebrow">Research</p><h1>Energy market research</h1>
<p class="lede">Seven briefs follow the energy value chain, from market foundations to prices and positioning. Each is updated monthly; earlier editions stay in the archive.</p></header>
{lst}
<section><h2>Archive</h2><ul class="plain"><li><a href="review.html">Global Energy Market Review, October 2026 →</a></li>{old}</ul></section>""".format(
        lst=research_list(research_items(src)),
        old="".join('<li><a href="%s-%s.html">%s →</a></li>' % (slug, os.path.basename(p)[:8], esc(split_title(open(p, encoding="utf-8").read())[0]))
                    for folder, slug, _, _ in SECTIONS for p in brief_versions(src, folder)[:-1]))
    return page("research", "Research", body, "Monthly energy market research briefs.")


def build_section(src, folder, slug, name, charts):
    versions = brief_versions(src, folder)
    if not versions:
        return {}
    out = {}
    with open(versions[-1], encoding="utf-8") as f:
        title, rest = split_title(clean_brief(f.read()))
    older = ""
    for p in versions[:-1]:
        with open(p, encoding="utf-8") as f:
            t, r = split_title(clean_brief(f.read()))
        arch = "%s-%s" % (slug, os.path.basename(p)[:8])
        older += '<li><a href="%s.html">%s</a></li>' % (arch, esc(t))
        out[arch] = page(slug, t, '<p class="eyebrow">Archive · Section {n}</p><h1>{t}</h1><p class="muted">An earlier edition. The <a href="{s}.html">latest brief</a> supersedes it.</p><article class="prose">{b}</article>'.format(
            n=folder[:2], t=esc(t), s=slug, b=md_to_html(r)), t)
    chart_html = "".join(render_chart(charts[c]) for c in SECTION_CHARTS.get(slug, []) if c in charts)
    body = """<header class="pagehead"><p class="eyebrow">Section {n} · {name}</p><h1>{t}</h1><p class="muted">Published {d}</p></header>
{charts}
<article class="prose">{b}</article>
{older}""".format(n=folder[:2], name=esc(name), t=esc(title),
                  charts='<div class="charts two">%s</div>' % chart_html if chart_html else "",
                  b=md_to_html(rest),
                  older='<aside class="older"><h2>Earlier editions</h2><ul>%s</ul></aside>' % older if older else "",
                  d=esc(fmt_date("%s-%s-%s" % (os.path.basename(versions[-1])[:4], os.path.basename(versions[-1])[4:6], os.path.basename(versions[-1])[6:8]))))
    out[slug] = page(slug, name, body, title)
    return out


def build_data(src, charts):
    groups = ""
    for gname, ids in DATA_GROUPS:
        inner = "".join(render_chart(charts[c]) for c in ids if c in charts)
        if inner:
            groups += '<section id="%s"><h2>%s</h2><div class="charts two">%s</div></section>' % (re.sub(r"\W+", "-", gname.lower()), esc(gname), inner)
    keyind = latest(files(src, "01_Market_Foundations_and_Data/01.4_Supply_Demand_Balances/*Key_Indicators*.xlsx"))
    tables = ""
    labels = {"Oil_Balance": "Oil balance", "Prices": "Prices", "Gas_LNG": "Gas and LNG", "Power_Transition": "Power and transition",
              "Macro": "Macro", "Agency_Comparison": "Agency comparison"}
    if keyind:
        wb = openpyxl.load_workbook(keyind, data_only=True, read_only=True)
        for sh in wb.sheetnames:
            head, body, notes = table_rows(keyind, sh)
            if not head:
                continue
            thead = "".join("<th>%s</th>" % esc(c) for c in head if c is not None)
            tb = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % linkify("" if c is None else c) for c in r[:len([x for x in head if x is not None])]) for r in body)
            tables += '<details class="tbl"><summary>{t} <span class="muted">({n} rows)</span></summary><div class="tablewrap"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>{notes}</details>'.format(
                t=esc(labels.get(sh, sh.replace("_", " "))), n=len(body), h=thead, b=tb,
                notes="".join('<p class="note">%s</p>' % esc(n) for n in notes))
    toc = " · ".join('<a href="#%s">%s</a>' % (re.sub(r"\W+", "-", g.lower()), esc(g)) for g, _ in DATA_GROUPS)
    body = """<header class="pagehead"><p class="eyebrow">Data</p><h1>Charts and key indicators</h1>
<p class="lede">The numbers behind the calls, rebuilt from public data (EIA, FRED, CFTC, GIE, Ember and others) on {d}. Hover a chart for values, or open “Show data” for the table.</p></header>
<p class="toc">{toc} · <a href="#indicators">Key indicators</a></p>
{groups}
<section id="indicators"><h2>Key indicators</h2><p class="muted">From the Key Indicators workbook: agency reports, prices and balances as published.</p>{tables}</section>""".format(
        d=esc(fmt_date(os.path.basename(keyind)[:8][:4] + "-" + os.path.basename(keyind)[4:6] + "-" + os.path.basename(keyind)[6:8])) if keyind else "",
        toc=toc, groups=groups, tables=tables)
    return page("data", "Data", body, "Energy market charts and key indicators.")


def build_companies(src):
    path = latest(files(src, "02_Upstream_Production_by_Source/*Upstream_Companies*.xlsx"))
    if not path:
        return None
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    labels = {"Oil_Gas_Majors": "Oil and gas majors", "NOCs_and_Gulf": "National oil companies and the Gulf", "Gas_Producers": "Gas producers",
              "Coal": "Coal", "Nuclear_Uranium": "Nuclear and uranium", "Renewables_Power": "Renewables and power",
              "Solar_Wind_Manufacturers": "Solar and wind manufacturers", "Critical_Minerals": "Critical minerals",
              "KPI_Definitions": "How to read the KPIs"}
    caps, sections, toc = [], "", []
    for sh in wb.sheetnames:
        if sh == "README":
            continue
        head, body, notes = table_rows(path, sh)
        if not head:
            continue
        ncols = len([c for c in head if c is not None])
        if "Market cap (US$bn)" in head:
            ci = head.index("Market cap (US$bn)")
            for r in body:
                v = num(r[ci])
                if v:
                    caps.append((r[0], v))
        sid = sh.lower()
        toc.append('<a href="#%s">%s</a>' % (sid, esc(labels.get(sh, sh))))
        thead = "".join("<th>%s</th>" % esc(c) for c in head[:ncols])
        tb = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % linkify("" if c is None else c) for c in r[:ncols]) for r in body)
        sections += '<section id="{id}"><h2>{t}</h2><div class="tablewrap"><table class="dense"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>{n}</section>'.format(
            id=sid, t=esc(labels.get(sh, sh)), h=thead, b=tb, n="".join('<p class="note">%s</p>' % esc(x) for x in notes))
    seen, top = set(), []
    for n, v in sorted(caps, key=lambda x: -x[1]):
        if n not in seen:
            seen.add(n)
            top.append((n, v))
    top = top[:15]
    cap_chart = ""
    if top:
        cap_chart = render_chart(chart("mcap", "Largest listed energy and mining companies by market value (US$bn, 9–10 Nov 2026)", {
            "type": "bar", "unit": "US$bn", "decimals": 0, "categories": [t[0] for t in top],
            "series": [{"name": "Market cap", "slot": 1, "values": [t[1] for t in top]}]},
            "Source: companiesmarketcap.com list pages, 9–10 Nov 2026. Some figures cover a group or one listing only; see the tables."), wide=True)
    body = """<header class="pagehead"><p class="eyebrow">Companies</p><h1>Who produces the world's energy</h1>
<p class="lede">About 80 companies across oil and gas, national oil companies, coal, nuclear, renewables, manufacturing and critical minerals: 2025 output, reserves, 2026 updates and market value, each with its source.</p></header>
<div class="charts">{cap}</div>
<p class="toc">{toc}</p>
{sections}""".format(cap=cap_chart, toc=" · ".join(toc), sections=sections)
    return page("companies", "Companies", body, "Energy company reference: output, reserves and market value.")


def build_review(src):
    path = latest(files(src, "08_Outputs/Reports/*Global_Energy_Market_Review*.md"))
    if not path:
        return None
    with open(path, encoding="utf-8") as f:
        title, rest = split_title(clean_brief(f.read()))
    rest = re.sub(r"Key numbers are in `[^`]+`\.", "Key numbers are on the [Data](data.html) page.", rest)
    body = '<p class="eyebrow">Archive · Monthly review</p><h1>{t}</h1><p class="muted">Published {d}. The <a href="index.html">overview</a> and the section briefs carry the November update.</p><article class="prose">{b}</article>'.format(
        t=esc(title), d=esc(fmt_date("%s-%s-%s" % (os.path.basename(path)[:4], os.path.basename(path)[4:6], os.path.basename(path)[6:8]))), b=md_to_html(rest))
    return page("review", "October review", body, title)


def build_about():
    body = """<header class="pagehead"><p class="eyebrow">About</p><h1>About this research</h1></header>
<article class="prose">
<p><strong>Kolan Sai Kiran Reddy</strong></p>
<p>This site is my monthly view of global energy markets, with the research and data behind it. The briefs follow the value chain: market foundations, upstream production, midstream logistics, downstream refining and power, regional markets and geopolitics, policy and carbon, and prices and positioning.</p>
<p><em>[Add your email or LinkedIn here.]</em></p>
<h2>Method</h2>
<ul>
<li>Figures come from public releases and data services, listed below and cited in each brief.</li>
<li>Lines marked <em>inferred</em>, and the five calls on the overview, are my own analytical judgement, not published data.</li>
<li>Prices are snapshots. Check them against exchange data before relying on them. Nothing here is investment advice.</li>
</ul>
<h2 id="sources">Data sources and licences</h2>
<ul>
<li><strong>US Energy Information Administration (EIA):</strong> weekly petroleum and gas storage data, spot prices, Electric Power Monthly, international production and the Short-Term Energy Outlook. EIA data are public domain.</li>
<li><strong>FRED, Federal Reserve Bank of St. Louis:</strong> retail fuel prices, IMF primary commodity prices and US macro series.</li>
<li><strong>CFTC:</strong> Disaggregated Commitments of Traders reports.</li>
<li><strong>GIE AGSI+ (Gas Infrastructure Europe):</strong> EU gas storage. Data from <a href="https://agsi.gie.eu/" target="_blank" rel="noopener">agsi.gie.eu</a>.</li>
<li><strong>Ember:</strong> electricity generation and power-sector emissions from <a href="https://ember-energy.org/data/yearly-electricity-data/" target="_blank" rel="noopener">Ember Yearly Electricity Data</a>, used under the <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">CC-BY-4.0 licence</a>.</li>
<li><strong>Energy Institute:</strong> Statistical Review of World Energy 2026 (2025 country data).</li>
<li><strong>Federal Reserve Bank of Dallas:</strong> Dallas Fed Energy Survey (shale breakevens).</li>
<li><strong>Lazard:</strong> LCOE+ 2026.</li>
<li><strong>Agency reports:</strong> IEA Oil Market Report, OPEC Monthly Oil Market Report, IMF World Economic Outlook, OIES Quarterly Gas Review, USGS Mineral Commodity Summaries.</li>
<li><strong>Company data:</strong> annual reports, results releases and filings, with market values from companiesmarketcap.com. Every row in the company tables names its source.</li>
</ul>
</article>"""
    return page("about", "About and sources", body, "About this energy research, its method and data sources.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(MASTER, "ENERGY ANALYSIS"))
    ap.add_argument("--out", default=SITE_DIR)
    a = ap.parse_args()
    charts = build_charts(a.src)
    meta, calls, watch = parse_home(os.path.join(HERE, "homepage.md"))
    out = {"index": build_home(a.src, charts, meta, calls, watch), "data": build_data(a.src, charts), "about": build_about(), "research": build_research_index(a.src)}
    for folder, slug, name, _ in SECTIONS:
        out.update(build_section(a.src, folder, slug, name, charts))
    for slug, fn in (("companies", build_companies), ("review", build_review)):
        p = fn(a.src)
        if p:
            out[slug] = p
    for old in ("indicators",):  # pages from the first version that no longer exist
        p = os.path.join(a.out, old + ".html")
        if os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                f.write('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=data.html"><a href="data.html">Moved to Data</a>')
    for slug, text in out.items():
        if BANNED.search(text):
            raise SystemExit("Refusing to write %s: it contains OilPriceAPI content" % slug)
        with open(os.path.join(a.out, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(text)
    print("Wrote %d pages and %d charts to %s" % (len(out), len(charts), a.out))


if __name__ == "__main__":
    main()
