"""Build the GLOBAL section workbooks (country and regional level) from raw files written by the data pull:
EIA international annual (all countries), JODI oil monthly, Ember monthly and annual electricity.
Usage: python build_global_workbooks.py <ENERGY ANALYSIS root> YYYYMMDD"""
import csv, os, sys, glob
from collections import defaultdict
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
try:
    import pycountry
    def cname(a2): c = pycountry.countries.get(alpha_2=a2); return c.name if c else a2
except ImportError:
    def cname(a2): return a2
HF, HT = PatternFill("solid", fgColor="1F4E78"), Font(bold=True, color="FFFFFF")
REGIONS = [("WORL", "World"), ("NOAM", "North America"), ("CSAM", "Central & South America"), ("EURO", "Europe"), ("EURA", "Eurasia"),
           ("MIDE", "Middle East"), ("AFRC", "Africa"), ("ASOC", "Asia & Oceania"), ("OECD", "OECD"), ("NOEC", "Non-OECD"), ("OPEC", "OPEC"), ("EU27", "European Union")]
METRICS = [  # key, product, activity, unit, label, unit label
    ("crude_prod", "Crude oil including lease condensate", "Production", "TBPD", "Crude oil production", "kb/d"),
    ("liq_prod", "Total petroleum and other liquids", "Production", "TBPD", "Total liquids production", "kb/d"),
    ("oil_cons", "Petroleum and other liquids", "Consumption", "TBPD", "Oil consumption", "kb/d"),
    ("gas_prod", "Dry natural gas", "Production", "BCM", "Gas production", "bcm"),
    ("gas_cons", "Dry natural gas", "Consumption", "BCM", "Gas consumption", "bcm"),
    ("gas_exp", "Dry natural gas", "Exports", "BCM", "Gas exports (pipeline + LNG)", "bcm"),
    ("gas_imp", "Dry natural gas", "Imports", "BCM", "Gas imports (pipeline + LNG)", "bcm"),
    ("coal_prod", "Coal", "Production", "MT", "Coal production", "Mt"),
    ("coal_cons", "Coal", "Consumption", "MT", "Coal consumption", "Mt"),
    ("coal_exp", "Coal", "Exports", "MT", "Coal exports", "Mt"),
    ("coal_imp", "Coal", "Imports", "MT", "Coal imports", "Mt"),
    ("elec_gen", "Electricity", "Generation", "BKWH", "Electricity generation", "TWh"),
    ("elec_cap", "Electricity", "Capacity", "MK", "Generating capacity", "GW"),
    ("pe_cons", "Primary energy", "Consumption", "QBTU", "Primary energy consumption", "quad Btu"),
    ("pe_prod", "Primary energy", "Production", "QBTU", "Primary energy production", "quad Btu"),
    ("co2", "CO2 emissions", "Emissions", "MMTCD", "Energy CO2 emissions", "Mt CO2"),
]
KEY_COUNTRIES = ["USA", "CHN", "IND", "RUS", "SAU", "JPN", "DEU", "BRA", "CAN", "IRN", "ARE", "QAT", "NOR", "AUS", "IDN", "KOR", "GBR", "NGA", "ZAF", "MEX"]

def style(ws, widths, freeze="C2"):
    for c in ws[1]: c.fill, c.font, c.alignment = HF, HT, Alignment(wrap_text=True, vertical="top")
    for i, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = freeze

def note(ws, text):
    ws.append([]); ws.append([text]); ws.cell(ws.max_row, 1).font = Font(italic=True)

def pct(a, b): return round(100 * (a / b - 1), 1) if a is not None and b else None

def load_eia(root, date):
    f = glob.glob(os.path.join(root, "01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/EIA/API_%s/%s_EIA_API_International_Annual_Global.csv" % (date, date)))[0]
    D = defaultdict(lambda: defaultdict(dict)); names = {}; types = {}
    lk = {(m[1], m[2], m[3]): m[0] for m in METRICS}
    for r in csv.DictReader(open(f)):
        k = lk.get((r["product"], r["activity"], r["unit"]))
        if k:
            v = float(r["value"]); v = v / 1000 if r["unit"] == "MT" else v  # EIA "MT" = thousand tonnes -> Mt
            D[k][r["countryRegionId"]][int(r["year"])] = v; names[r["countryRegionId"]] = r["countryRegion"]; types[r["countryRegionId"]] = r["type"]
    return D, names, types

def latest_year(series_by_area):
    w = series_by_area.get("WORL", {})
    ys = sorted(y for y, v in w.items() if v) if w else sorted({y for s in series_by_area.values() for y in s})
    return ys[-1] if ys else None

def rank_sheet(wb, D, names, types, key, label, unit, top=40, first=2015):
    s = D[key]; y = latest_year(s); world = s.get("WORL", {}).get(y)
    ws = wb.create_sheet(label[:31]); yrs = list(range(first, y + 1))
    ws.append(["Rank", "Country"] + [str(x) for x in yrs] + ["y/y %", "5-yr change %", "Share of world %"])
    cs = sorted([(a, v) for a, v in s.items() if types.get(a) == "Country" and v.get(y)], key=lambda t: -t[1][y])[:top]
    for i, (a, v) in enumerate(cs, 1):
        ws.append([i, names[a]] + [None if v.get(x) is None else round(v[x], 1) for x in yrs] + [pct(v.get(y), v.get(y - 1)), pct(v.get(y), v.get(y - 5)), round(100 * v[y] / world, 1) if world else None])
    ws.append([]); 
    for code, nm in REGIONS:
        v = s.get(code, {})
        if v: ws.append(["", nm] + [None if v.get(x) is None else round(v[x], 1) for x in yrs] + [pct(v.get(y), v.get(y - 1)), pct(v.get(y), v.get(y - 5)), round(100 * v[y] / world, 1) if world and v.get(y) else None])
    style(ws, [6, 26] + [9] * len(yrs) + [8, 10, 10])
    note(ws, "%s, %s. Source: EIA international data (API v2, annual), latest year %s. Regions are EIA definitions." % (label, unit, y))
    return y

def world_summary(wb, D, title="World_and_Regions"):
    ws = wb.create_sheet(title, 0); hdr = ["Metric", "Unit", "Year"] + [nm for _, nm in REGIONS]
    ws.append(hdr)
    for k, _, _, _, label, unit in METRICS:
        s = D[k]; y = latest_year(s)
        if not y: continue
        ws.append([label, unit, y] + [None if s.get(c, {}).get(y) is None else round(s[c][y], 1) for c, _ in REGIONS])
        ws.append([label + " y/y %", "%", y] + [pct(s.get(c, {}).get(y), s.get(c, {}).get(y - 1)) for c, _ in REGIONS])
    style(ws, [36, 9, 6] + [12] * len(REGIONS), "D2")
    note(ws, "EIA international data (API v2). Oil series run to 2025; gas, coal, power, primary energy and CO2 to 2024 (EIA publishes with a lag).")

def country_cards(wb, D, names):
    ws = wb.create_sheet("Key_Countries"); ys = None
    ws.append(["Country"] + [m[4] + " (" + m[5] + ")" for m in METRICS])
    for c in KEY_COUNTRIES:
        row = [names.get(c, c)]
        for k, *_ in METRICS:
            s = D[k].get(c, {}); y = latest_year(D[k]); row.append(None if s.get(y) is None else round(s[y], 1))
        ws.append(row)
    style(ws, [22] + [13] * len(METRICS), "B2")
    note(ws, "Latest EIA year for each metric (oil 2025, others 2024).")

# ---------- JODI ----------
def load_jodi(root, date, kind):
    D = defaultdict(lambda: defaultdict(dict))
    for f in sorted(glob.glob(os.path.join(root, "01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/Other_Sources/API_%s/%s_JODI_Oil_%s_*_Global_Monthly.csv" % (date, date, kind)))):
        for r in csv.DictReader(open(f)):
            try: v = float(r["OBS_VALUE"])
            except (ValueError, TypeError): continue
            D[(r["ENERGY_PRODUCT"], r["FLOW_BREAKDOWN"], r["UNIT_MEASURE"])][r["REF_AREA"]][r["TIME_PERIOD"]] = v
    return D

def jodi_sheet(wb, D, key, title, unit, top=30, months=20):
    s = D.get(key, {}); allm = sorted({m for v in s.values() for m in v})[-months:]
    if not allm: return
    ws = wb.create_sheet(title[:31]); ws.append(["Country", "Code"] + allm + ["Latest", "Latest month", "y/y % (same month)"])
    def lastv(v): ms = sorted(v); return (ms[-1], v[ms[-1]]) if ms else (None, None)
    rows = sorted(((a, v) for a, v in s.items() if len(a) == 2), key=lambda t: -(lastv(t[1])[1] or 0))[:top]
    for a, v in rows:
        lm, lv = lastv(v); py = "%d%s" % (int(lm[:4]) - 1, lm[4:]) if lm else None
        ws.append([cname(a), a] + [None if v.get(m) is None else round(v[m], 1) for m in allm] + [round(lv, 1), lm, pct(lv, v.get(py))])
    style(ws, [24, 6] + [9] * len(allm) + [9, 10, 10])
    note(ws, "%s (%s). Source: JODI Oil World Database, monthly, as reported by national administrations. Countries that have not reported recent months (e.g. Russia, Iraq, UAE, Iran in 2026) are missing or show older data." % (title.replace("_", " "), unit))

# ---------- Ember monthly ----------
EMB_SRC = ["Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Bioenergy"]
def ember_monthly(root, date):
    f = glob.glob(os.path.join(root, "01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/Other_Sources/API_%s/%s_Ember_Electricity_Generation_Global_Monthly.csv" % (date, date)))
    D = defaultdict(lambda: defaultdict(dict)); E = defaultdict(dict); typ = {}
    for r in csv.DictReader(open(f[0])) if f else []:
        m = r["Date"][:7]; a = r["Area"]; typ[a] = r["Area type"]
        if r["Generation (TWh)"]: D[a][r["Electricity source"]][m] = float(r["Generation (TWh)"])
        if r["Electricity source"] == "Total generation" and r["Emissions (MtCO2e)"]: E[a][m] = float(r["Emissions (MtCO2e)"])
    return D, E, typ

def ember_sheets(wb, D, E, typ, top=30):
    if not D: return None
    months = sorted(D["World"]["Total generation"]); lm = months[-1]
    # areas with data for the latest 12 months
    def tot12(a, end):
        i = months.index(end); win = months[max(0, i - 11):i + 1]; v = D[a].get("Total generation", {})
        return sum(v.get(m, 0) for m in win) if all(m in v for m in win) else None
    # last full month with good country coverage
    cov = [m for m in months if sum(1 for a in D if typ.get(a, "").startswith("Country") and m in D[a].get("Total generation", {})) >= 60]
    end = cov[-1] if cov else lm
    i = months.index(end); win = months[max(0, i - 11):i + 1]; pwin = months[max(0, i - 23):max(0, i - 11)]
    ws = wb.create_sheet("Mix_Last_12m"); ws.append(["Area", "Type", "Generation 12m (TWh)", "y/y %"] + ["%s share %%" % s for s in EMB_SRC] + ["Wind+solar share %", "Wind+solar share change (pts)", "Power CO2 12m (Mt)", "CO2 y/y %"])
    areas = ["World", "EU", "Asia", "Africa", "Latin America and Caribbean", "Middle East", "North America", "Europe", "Oceania"]
    cands = sorted([a for a in D if typ.get(a, "").startswith("Country") and tot12(a, end)], key=lambda a: -tot12(a, end))[:top]
    for a in [x for x in areas if x in D] + cands:
        g = D[a]; t = sum(g.get("Total generation", {}).get(m, 0) for m in win); tp = sum(g.get("Total generation", {}).get(m, 0) for m in pwin)
        sh = lambda s, w, tt: 100 * sum(g.get(s, {}).get(m, 0) for m in w) / tt if tt else None
        ws_now = (sh("Wind", win, t) or 0) + (sh("Solar", win, t) or 0); ws_prev = ((sh("Wind", pwin, tp) or 0) + (sh("Solar", pwin, tp) or 0)) if tp else None
        e = sum(E[a].get(m, 0) for m in win); ep = sum(E[a].get(m, 0) for m in pwin)
        ws.append([a, typ.get(a, ""), round(t, 1), pct(t, tp)] + [None if sh(s, win, t) is None else round(sh(s, win, t), 1) for s in EMB_SRC] + [round(ws_now, 1), None if ws_prev is None else round(ws_now - ws_prev, 1), round(e, 1) if e else None, pct(e, ep) if e and ep else None])
    style(ws, [28, 9, 12, 8] + [10] * len(EMB_SRC) + [11, 12, 12, 9], "B2")
    note(ws, "12 months to %s, against the previous 12 months. Source: Ember monthly electricity data (CC-BY-4.0). Regions are Ember definitions." % end)
    # monthly world + key countries total, coal, gas, wind+solar for last 24 months
    ws = wb.create_sheet("Monthly_Key_Areas"); m24 = months[-24:]
    ws.append(["Area", "Series"] + m24)
    for a in ["World", "China", "United States", "EU", "India", "Japan", "Brazil", "Russia", "Middle East"]:
        if a not in D: continue
        for s in ["Total generation", "Coal", "Gas", "Wind", "Solar", "Nuclear", "Hydro"]:
            v = D[a].get(s, {}); ws.append([a, s] + [None if v.get(m) is None else round(v[m], 1) for m in m24])
    style(ws, [16, 16] + [8] * len(m24))
    note(ws, "TWh per month. Source: Ember monthly electricity data. The most recent months cover fewer countries.")
    return end

def build(root, date):
    out = []
    def save(rel, wb):
        p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); wb.save(p); out.append(rel)
    def nwb(): wb = openpyxl.Workbook(); wb.remove(wb.active); return wb
    D, names, types = load_eia(root, date)
    M = {m[0]: m for m in METRICS}
    # 01.4 master: world + regions + every metric ranked
    wb = nwb(); world_summary(wb, D)
    for k, *_ in METRICS: rank_sheet(wb, D, names, types, k, M[k][4], M[k][5])
    save("01_Market_Foundations_and_Data/01.4_Supply_Demand_Balances/%s_Analysis_Global_Energy_Balance_by_Country_Global_Annual_v01.xlsx" % date, wb)
    # 02 production
    JP = load_jodi(root, date, "Primary"); JS = load_jodi(root, date, "Secondary")
    wb = nwb()
    for k in ["crude_prod", "liq_prod", "gas_prod", "coal_prod", "elec_gen", "pe_prod"]: rank_sheet(wb, D, names, types, k, M[k][4], M[k][5])
    jodi_sheet(wb, JP, ("CRUDEOIL", "INDPROD", "KBD"), "JODI_Crude_Production_Monthly", "kb/d")
    save("02_Upstream_Production_by_Source/%s_Analysis_Global_Production_by_Country_Global_Annual_v01.xlsx" % date, wb)
    # 03 trade and stocks
    wb = nwb()
    for k in ["gas_exp", "gas_imp", "coal_exp", "coal_imp"]: rank_sheet(wb, D, names, types, k, M[k][4], M[k][5])
    jodi_sheet(wb, JP, ("TOTCRUDE", "TOTEXPSB", "KBD"), "JODI_Crude_Exports_Monthly", "kb/d")
    jodi_sheet(wb, JP, ("TOTCRUDE", "TOTIMPSB", "KBD"), "JODI_Crude_Imports_Monthly", "kb/d")
    jodi_sheet(wb, JP, ("TOTCRUDE", "CLOSTLV", "KBBL"), "JODI_Crude_Stocks_Monthly", "kb")
    jodi_sheet(wb, JS, ("TOTPRODS", "TOTEXPSB", "KBD"), "JODI_Product_Exports_Monthly", "kb/d")
    jodi_sheet(wb, JS, ("TOTPRODS", "CLOSTLV", "KBBL"), "JODI_Product_Stocks_Monthly", "kb")
    save("03_Midstream_Logistics_and_Transportation/03.4_Trade_Flows_and_Sanctions/%s_Analysis_Global_Energy_Trade_and_Stocks_Global_Monthly_v01.xlsx" % date, wb)
    # 04.1 refining and product demand
    wb = nwb()
    rank_sheet(wb, D, names, types, "oil_cons", M["oil_cons"][4], M["oil_cons"][5])
    jodi_sheet(wb, JP, ("TOTCRUDE", "REFINOBS", "KBD"), "JODI_Refinery_Intake_Monthly", "kb/d")
    for p, t in [("TOTPRODS", "Total_Products"), ("GASDIES", "Gasoil_Diesel"), ("GASOLINE", "Gasoline"), ("JETKERO", "Jet_Kerosene"), ("NAPHTHA", "Naphtha"), ("LPG", "LPG")]:
        jodi_sheet(wb, JS, (p, "TOTDEMO", "KBD"), "JODI_Demand_" + t, "kb/d")
    jodi_sheet(wb, JS, ("TOTPRODS", "REFGROUT", "KBD"), "JODI_Refinery_Output_Monthly", "kb/d")
    save("04_Downstream_Refining_and_End_Use/04.1_Refining_and_Processing/%s_Analysis_Global_Refining_and_Oil_Demand_Global_Monthly_v01.xlsx" % date, wb)
    # 04.2 global power (Ember monthly) + EIA generation/capacity
    ED, EE, typ = ember_monthly(root, date); wb = nwb(); end = ember_sheets(wb, ED, EE, typ)
    for k in ["elec_gen", "elec_cap"]: rank_sheet(wb, D, names, types, k, M[k][4], M[k][5])
    save("04_Downstream_Refining_and_End_Use/04.2_Power_Generation_and_Grids/%s_Analysis_Global_Power_Generation_Global_Monthly_v01.xlsx" % date, wb)
    # 05 regional
    wb = nwb(); world_summary(wb, D, "Regions"); country_cards(wb, D, names)
    for k in ["pe_cons", "oil_cons", "gas_cons", "coal_cons"]: rank_sheet(wb, D, names, types, k, M[k][4], M[k][5])
    save("05_Regional_Markets_and_Geopolitics/%s_Analysis_Regional_Energy_Profiles_Global_Annual_v01.xlsx" % date, wb)
    # 06.4 global CO2
    wb = nwb(); rank_sheet(wb, D, names, types, "co2", M["co2"][4], M["co2"][5], top=50, first=2010)
    save("06_Policy_Regulation_and_Carbon/06.4_Emissions_Data/%s_Analysis_Global_CO2_by_Country_Global_Annual_v01.xlsx" % date, wb)
    return out, end

if __name__ == "__main__":
    o, e = build(sys.argv[1], sys.argv[2]); print("\n".join(o)); print("ember window end", e)
