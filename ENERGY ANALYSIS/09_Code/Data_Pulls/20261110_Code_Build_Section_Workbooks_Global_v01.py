"""Build section workbooks from the raw API CSVs written by energy_data_pull.py.
Usage: python build_section_workbooks.py <ENERGY ANALYSIS root> YYYYMMDD"""
import csv, os, sys, glob, datetime as dt
from collections import defaultdict, OrderedDict
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
HF, HT = PatternFill("solid", fgColor="1F4E78"), Font(bold=True, color="FFFFFF")

def load(root, date):
    S = OrderedDict()  # sid -> dict(label,unit,freq,src,group,points)
    for f in glob.glob(os.path.join(root, "01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/*/API_%s/%s_*_API_*.csv" % (date, date))):
        src = os.path.basename(f).split("_")[1]; grp = os.path.basename(f).split("_API_")[1].rsplit("_Global", 1)[0]
        for r in csv.DictReader(open(f)):
            s = S.setdefault(r["series_id"], dict(label=r["label"], unit=r["unit"], freq=r["frequency"], src=src, group=grp, pts={}))
            s["pts"][r["period"]] = float(r["value"])
    for f in glob.glob(os.path.join(root, "01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/Other_Sources/API_%s/%s_GIE_AGSI_*.csv" % (date, date))):
        for r in csv.DictReader(open(f)):
            if r["full"] not in ("", "-"):
                S.setdefault("GIE.%s.full" % r["area_code"], dict(label="%s gas storage, %% full" % r["area"], unit="%", freq="D", src="GIE", group="gie", pts={}))["pts"][r["gasDayStart"]] = float(r["full"])
            if r["area_code"] == "eu" and r["gasInStorage"] not in ("", "-"):
                S.setdefault("GIE.eu.twh", dict(label="EU gas in storage", unit="TWh", freq="D", src="GIE", group="gie", pts={}))["pts"][r["gasDayStart"]] = float(r["gasInStorage"])
    return S

def monthly(pts):
    m = defaultdict(list)
    for p, v in pts.items(): m[p[:7]].append(v)
    return {k: sum(v) / len(v) for k, v in m.items()}

def yoy_ref(period, freq, pts):
    try:
        if freq == "A": k = str(int(period) - 1)
        elif freq == "M": k = "%d-%s" % (int(period[:4]) - 1, period[5:7]) if len(period) == 7 else "%d%s" % (int(period[:4]) - 1, period[4:])
        else:
            d = dt.date.fromisoformat(period[:10]) - dt.timedelta(days=364)
            ks = sorted(k for k in pts if k <= d.isoformat()); k = ks[-1] if ks else None
        return pts.get(k)
    except Exception: return None

def style(ws, widths):
    for c in ws[1]: c.fill, c.font, c.alignment = HF, HT, Alignment(wrap_text=True, vertical="top")
    for i, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "B2"

def latest_sheet(wb, items, S, note):
    ws = wb.create_sheet("Latest", 0)
    ws.append(["Series", "Unit", "Source / id", "Latest period", "Latest value", "Previous period", "Previous value", "Change", "Year earlier", "Change y/y %"])
    for sheet, sids in items:
        for sid in sids:
            s = S[sid]; ks = sorted(s["pts"]); 
            if not ks: continue
            p, v = ks[-1], s["pts"][ks[-1]]; pp = ks[-2] if len(ks) > 1 else None; pv = s["pts"].get(pp)
            y = yoy_ref(p, s["freq"], s["pts"])
            ws.append([s["label"], s["unit"], "%s %s" % (s["src"], sid), p, round(v, 3), pp, None if pv is None else round(pv, 3),
                       None if pv is None else round(v - pv, 3), None if y is None else round(y, 3), None if not y else round(100 * (v / y - 1), 1)])
    style(ws, [38, 14, 34, 13, 13, 13, 13, 11, 13, 12])
    ws.freeze_panes = "A2"
    ws.append([]); ws.append([note]); ws.cell(ws.max_row, 1).font = Font(italic=True)

def wide_sheet(wb, name, sids, S, to_monthly=False, since=None):
    ws = wb.create_sheet(name[:31])
    cols = [(sid, monthly(S[sid]["pts"]) if to_monthly else S[sid]["pts"]) for sid in sids]
    periods = sorted(set(p for _, pts in cols for p in pts if not since or p >= since), reverse=True)
    ws.append(["Period"] + ["%s (%s)" % (S[sid]["label"], S[sid]["unit"]) for sid, _ in cols])
    for p in periods: ws.append([p] + [None if pts.get(p) is None else round(pts[p], 3) for _, pts in cols])
    style(ws, [12] + [16] * len(cols))
    return ws

def ember_rows(root, date):
    f = glob.glob(os.path.join(root, "01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/Other_Sources/API_%s/%s_Ember_*.csv" % (date, date)))
    return list(csv.DictReader(open(f[0]))) if f else []

EMBER_AREAS = ["World", "China", "United States", "EU", "India", "Japan", "Brazil", "Russia", "Middle East", "Africa"]
EMBER_SRC = ["Coal", "Gas", "Other fossil", "Nuclear", "Hydro", "Wind", "Solar", "Bioenergy", "Other renewables"]

def ember_sheets(wb, rows, metric, title, since="2015"):
    ws = wb.create_sheet(title[:31]); ws.append(["Area", "Year"] + EMBER_SRC + ["Total"])
    idx = defaultdict(dict)
    for r in rows:
        if r["Area"] in EMBER_AREAS and r["Year"] >= since and r[metric] not in ("",):
            idx[(r["Area"], r["Year"])][r["Electricity source"]] = float(r[metric])
    for a in EMBER_AREAS:
        for y in sorted({k[1] for k in idx if k[0] == a}, reverse=True):
            d = idx[(a, y)]; ws.append([a, int(y)] + [round(d.get(src, 0), 1) for src in EMBER_SRC] + [round(d.get("Total generation", sum(d.get(x, 0) for x in EMBER_SRC)), 1)])
    style(ws, [26, 8] + [11] * (len(EMBER_SRC) + 1))

def build(root, date):
    S = load(root, date)
    by = lambda grp, cond=lambda s: True: [k for k, s in S.items() if s["group"] == grp and cond(s)]
    lab = lambda grp, words: [k for k in by(grp) if any(w in S[k]["label"] for w in words)]
    raw = "01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/{EIA,Other_Sources}/API_%s" % date
    note = "Built %s from free APIs (EIA API v2, FRED, CFTC). Raw CSVs: %s. Rebuild with 09_Code/Data_Pulls." % (date, raw)
    out = []
    def save(rel, wb):
        p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); wb.save(p); out.append(rel)
    def nwb(): wb = openpyxl.Workbook(); wb.remove(wb.active); return wb
    # 01.3 Macro
    wb = nwb(); m = by("macro"); latest_sheet(wb, [("", m)], S, note)
    wide_sheet(wb, "Monthly_and_Quarterly", [k for k in m if S[k]["freq"] in "MQ"], S)
    wide_sheet(wb, "Daily_to_Monthly_avg", [k for k in m if S[k]["freq"] == "D"], S, to_monthly=True)
    save("01_Market_Foundations_and_Data/01.3_Macro_Economic_Indicators/%s_Analysis_Macro_Indicators_US_Monthly_v01.xlsx" % date, wb)
    # 01.4 US weekly balance
    wb = nwb(); w = by("us_weekly"); latest_sheet(wb, [("", w)], S, note)
    wide_sheet(wb, "Weekly", w, S, since="2021")
    save("01_Market_Foundations_and_Data/01.4_Supply_Demand_Balances/%s_Analysis_US_Weekly_Oil_Gas_Balance_US_Weekly_v01.xlsx" % date, wb)
    # 02.1 / 05 International production and consumption
    wb = nwb(); prod = lab("intl", []) or [k for k in by("intl") if ".M" in k]; prod = [k for k in by("intl") if k.endswith(".M")]; cons = [k for k in by("intl") if k.endswith(".A")]
    latest_sheet(wb, [("", prod + cons)], S, note + " EIA international data lag 4-6 months; Russia/Kazakhstan monthly not published by EIA (shown as missing).")
    wide_sheet(wb, "Crude_Production_Monthly", prod, S, since="2019")
    wide_sheet(wb, "Oil_Consumption_Annual", cons, S)
    save("02_Upstream_Production_by_Source/02.1_Fossil_Fuels/Crude_Oil/%s_Analysis_Crude_Production_by_Country_Global_Monthly_v01.xlsx" % date, wb)
    # 03 Midstream: storage + trade
    wb = nwb(); stor = lab("us_weekly", ["stocks", "SPR", "working gas"]); flows = lab("us_weekly", ["imports", "exports"]); tr = by("trade")
    gie = by("gie")
    latest_sheet(wb, [("", stor + flows + tr + gie)], S, note + (" EU storage: GIE AGSI+." if gie else ""))
    wide_sheet(wb, "Storage_Weekly", stor, S, since="2021"); wide_sheet(wb, "Trade_Weekly", flows, S, since="2021")
    wide_sheet(wb, "Imports_by_Origin_and_LNG", tr, S, since="2019")
    if gie:
        wide_sheet(wb, "EU_Gas_Storage_Daily", gie, S, since="2025")
        eu = S["GIE.eu.full"]["pts"]; yrs = sorted({p[:4] for p in eu})
        ws = wb.create_sheet("EU_Storage_Same_Date"); ws.append(["Date (day-month)"] + ["%s %% full" % y for y in yrs])
        for mm in range(1, 13):
            for dd in (1, 15):
                ws.append(["%02d-%02d" % (dd, mm)] + [eu.get("%s-%02d-%02d" % (y, mm, dd)) for y in yrs])
        style(ws, [16] + [10] * len(yrs))
    save("03_Midstream_Logistics_and_Transportation/03.3_Storage_and_Terminals/%s_Analysis_US_Storage_and_Trade_US_Weekly_v01.xlsx" % date, wb)
    # 04.1 Refining: utilisation, product supplied, spot cracks
    wb = nwb(); ref_w = lab("us_weekly", ["refinery", "product supplied"]); sp = by("refining")
    latest_sheet(wb, [("", ref_w + sp)], S, note + " Crack = (2 x gasoline + 1 x ULSD)/3 x 42 - WTI, monthly averages of daily EIA spot prices.")
    wide_sheet(wb, "Refining_Weekly", ref_w, S, since="2021")
    ws = wb.create_sheet("Crack_3-2-1_Monthly"); ws.append(["Month", "WTI ($/bbl)", "NYH gasoline ($/bbl)", "NYH ULSD ($/bbl)", "3-2-1 crack vs WTI ($/bbl)", "Brent ($/bbl)", "ULSD minus Brent ($/bbl)"])
    g = lambda w: next(k for k in sp if w in S[k]["label"])
    wti, gas, ulsd, brent = (monthly(S[g(x)]["pts"]) for x in ("WTI", "gasoline", "ULSD", "Brent"))
    for mth in sorted(set(wti) & set(gas) & set(ulsd), reverse=True):
        if mth < "2019": continue
        gb, ub = gas[mth] * 42, ulsd[mth] * 42
        ws.append([mth, round(wti[mth], 2), round(gb, 2), round(ub, 2), round((2 * gb + ub) / 3 - wti[mth], 2), round(brent.get(mth, 0), 2) or None, round(ub - brent[mth], 2) if mth in brent else None])
    style(ws, [10, 12, 14, 14, 16, 12, 16])
    wide_sheet(wb, "Spot_Daily", sp, S, since="2025")
    save("04_Downstream_Refining_and_End_Use/04.1_Refining_and_Processing/%s_Analysis_Refining_Margins_US_Monthly_v01.xlsx" % date, wb)
    # 04.2 Power
    wb = nwb(); pw = by("power"); latest_sheet(wb, [("", pw)], S, note)
    gen = [k for k in pw if "GEN" in k]; wide_sheet(wb, "Generation_by_Fuel", gen, S, since="2019")
    ws = wb.create_sheet("Generation_Share_%"); allk = next(k for k in gen if "ALL" in k); ws.append(["Month"] + [S[k]["label"] for k in gen if k != allk])
    for mth in sorted(S[allk]["pts"], reverse=True):
        if mth < "2019": continue
        ws.append([mth] + [round(100 * S[k]["pts"].get(mth, 0) / S[allk]["pts"][mth], 1) for k in gen if k != allk])
    style(ws, [10] + [14] * (len(gen) - 1))
    wide_sheet(wb, "Retail_Price_and_Sales", [k for k in pw if "GEN" not in k], S, since="2019")
    er = ember_rows(root, date)
    if er:
        ember_sheets(wb, er, "Generation (TWh)", "Ember_Generation_TWh")
        ember_sheets(wb, er, "Share of generation (%)", "Ember_Share_%")
    save("04_Downstream_Refining_and_End_Use/04.2_Power_Generation_and_Grids/%s_Analysis_US_Power_Generation_US_Monthly_v01.xlsx" % date, wb)
    # 06.4 Emissions
    wb = nwb(); em = by("emissions"); latest_sheet(wb, [("", em)], S, note + " EIA state-level CO2 series end in 2022; use EIA MER/STEO or Ember for later years.")
    wide_sheet(wb, "US_CO2_by_Sector_Annual", em, S)
    er = ember_rows(root, date)
    if er:
        ws = wb.create_sheet("Power_CO2_Ember"); ws.append(["Area", "Year", "Power-sector emissions (MtCO2e)", "Emissions intensity (gCO2e/kWh)"])
        for r in er:
            if r["Area"] in EMBER_AREAS and r["Electricity source"] == "Total generation" and r["Year"] >= "2010":
                ws.append([r["Area"], int(r["Year"]), float(r["Emissions (MtCO2e)"] or 0) or None, float(r["Emissions intensity (gCO2e/kWh)"] or 0) or None])
        style(ws, [26, 8, 18, 18])
    save("06_Policy_Regulation_and_Carbon/06.4_Emissions_Data/%s_Analysis_US_CO2_Emissions_US_Annual_v01.xlsx" % date, wb)
    # 07.1 Prices + COT
    wb = nwb(); pr = by("prices"); latest_sheet(wb, [("", pr)], S, note + " Monthly IMF commodity prices via FRED lag about 6 weeks.")
    wide_sheet(wb, "Daily", [k for k in pr if S[k]["freq"] == "D"], S, since="2025")
    wide_sheet(wb, "Daily_to_Monthly_avg", [k for k in pr if S[k]["freq"] == "D"], S, to_monthly=True)
    wide_sheet(wb, "Weekly_Retail", [k for k in pr if S[k]["freq"] == "W"], S, since="2021")
    wide_sheet(wb, "Monthly_IMF", [k for k in pr if S[k]["freq"] == "M"], S, since="2019")
    of = glob.glob(os.path.join(root, "01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/Other_Sources/API_%s/*OilPriceAPI*.csv" % date))
    if of:
        ws = wb.create_sheet("Live_Snapshot_OilPriceAPI", 1)
        ws.append(["Group", "Code", "Price", "Currency", "Unit", "Type", "Observed at (UTC)", "Data status", "24h change %"])
        for r in csv.DictReader(open(of[0])):
            if r["price"]: ws.append([r["group"], r["code"], float(r["price"]), r["currency"], r["unit"], r["type"], r["observed_at"][:16].replace("T", " "), r["data_status"], float(r["change_24h_pct"]) if r["change_24h_pct"] else None])
        style(ws, [20, 32, 10, 9, 14, 12, 18, 11, 11]); ws.freeze_panes = "A2"
        ws.append([]); ws.append(["OilPriceAPI latest prices pulled %s (trial plan). Status 'stale', 'delayed' or 'degraded' is the provider's own flag; check before use." % date]); ws.cell(ws.max_row, 1).font = Font(italic=True)
    f = glob.glob(os.path.join(root, "01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/Other_Sources/API_%s/*CFTC*.csv" % date))[0]
    ws = wb.create_sheet("COT_Managed_Money"); ws.append(["Report date", "Market", "Open interest", "Managed money long", "Managed money short", "Managed money net", "Net as % of OI", "Producer/merchant net", "Swap dealer net"])
    rows = sorted(csv.DictReader(open(f)), key=lambda r: (r["report_date_as_yyyy_mm_dd"], r["cftc_code"]), reverse=True)
    i = lambda r, k: int(float(r[k] or 0))
    for r in rows:
        oi = i(r, "open_interest_all"); mm = i(r, "m_money_positions_long_all") - i(r, "m_money_positions_short_all")
        ws.append([r["report_date_as_yyyy_mm_dd"][:10], r["market_and_exchange_names"], oi, i(r, "m_money_positions_long_all"), i(r, "m_money_positions_short_all"), mm,
                   round(100 * mm / oi, 1) if oi else None, i(r, "prod_merc_positions_long") - i(r, "prod_merc_positions_short"), i(r, "swap_positions_long_all") - i(r, "swap__positions_short_all")])
    style(ws, [12, 44, 12, 14, 14, 14, 10, 14, 14])
    save("07_Financial_Analysis_and_Trading/07.1_Commodity_Pricing/%s_Analysis_Energy_Prices_and_Positioning_Global_Daily_v01.xlsx" % date, wb)
    return out

if __name__ == "__main__":
    for o in build(sys.argv[1], sys.argv[2]): print(o)
