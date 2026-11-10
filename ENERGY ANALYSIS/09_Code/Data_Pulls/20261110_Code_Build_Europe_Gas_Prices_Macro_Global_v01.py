"""Builds sheets from ENTSOG, GIE ALSI, World Bank Pink Sheet and IMF raw files (pulled 10 Nov 2026).
Usage: python3 build_new_sources.py <ENERGY ANALYSIS folder> <YYYYMMDD>"""
import csv, os, sys, glob, json, datetime as dt
from collections import defaultdict
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

HDR = PatternFill("solid", fgColor="1F4E78")
def style(ws, widths, freeze="C2"):
    for c in ws[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = HDR; c.alignment = Alignment(wrap_text=True, vertical="top")
    for i, w in enumerate(widths, 1): ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    ws.freeze_panes = freeze
def note(ws, text): ws.append([]); ws.append([text]); ws.cell(ws.max_row, 1).font = Font(italic=True, color="555555")
def pct(a, b): return round(100 * (a / b - 1), 1) if a is not None and b else None

TWH_PER_BCM = 10.55  # ENTSOG reports kWh at gross calorific value; ~10.55 TWh per bcm
ROUTE = {}
for k in ["ITP-00106", "ITP-00105", "ITP-00081", "ITP-00080", "ITP-00188", "ITP-00126", "ITP-00525", "ITP-00630", "ITP-00045", "ITP-00160"]: ROUTE[k] = "Norway"
for k in ["ITP-00549", "ITP-00041"]: ROUTE[k] = "Russia via TurkStream"
for k in ["ITP-00297", "ITP-00491", "ITP-00247", "ITP-00501", "ITP-00493", "ITP-00024", "ITP-00243", "ITP-00187"]: ROUTE[k] = "Russia, other routes (Nord Stream, Baltics, Finland)"
for k in ["ITP-00087", "ITP-00299", "ITP-00300", "ITP-00438", "ITP-00117", "ITP-00421", "ITP-10006", "ITP-10008"]: ROUTE[k] = "Ukraine border"
for k in ["ITP-00274", "ITP-00046"]: ROUTE[k] = "Azerbaijan and Turkey (TAP, Kipi)"
for k in ["ITP-00093", "ITP-00074", "ITP-00048", "ITP-00082"]: ROUTE[k] = "North Africa (Algeria, Libya)"
EXCLUDE = {"ITP-00085": "Kotlovka (Belarus to Lithuania, mostly Kaliningrad transit)"}
# same physical point reported by several German TSOs: take the max, not the sum
SAME = {"ITP-00105": "DE Emden EPT1", "ITP-00081": "DE Emden EPT1", "ITP-00080": "DE Emden EPT1",
        "ITP-00188": "DE Dornum", "ITP-00126": "DE Dornum", "ITP-00525": "DE Dornum"}
ROUTES = ["Norway", "LNG (all EU terminals)", "North Africa (Algeria, Libya)", "Azerbaijan and Turkey (TAP, Kipi)", "Russia via TurkStream", "Russia, other routes (Nord Stream, Baltics, Finland)", "Ukraine border"]

def entsog(raw):
    f = glob.glob(os.path.join(raw, "*_ENTSOG_Physical_Flows_EU_Import_Points_Europe_Daily.csv"))[0]
    loc = defaultdict(dict)  # (day, location) -> {operator: value}
    meta = {}
    for r in csv.DictReader(open(f)):
        if not r["value"]: continue
        pk = r["point_key"]; pt = r["point_type"] or ""
        route = "LNG (all EU terminals)" if pt.startswith("LNG") else ROUTE.get(pk)
        if not route: continue  # re-entries from Serbia, Switzerland, Moldova are transit, not imports
        locn = SAME.get(pk, pk); meta[locn] = (route, r["point"])
        loc[(r["gas_day"], locn)][r["operator_key"] + pk] = float(r["value"])
    day = defaultdict(lambda: defaultdict(float))
    for (d, l), ops in loc.items():
        v = max(ops.values()) if l in SAME.values() or l.startswith("LNG-") else sum(ops.values())
        day[d][meta[l][0]] += v / 1e9  # TWh/d
    return day

def alsi(raw):
    f = glob.glob(os.path.join(raw, "*_GIE_ALSI_LNG_Terminals_Europe_Daily.csv"))[0]
    D = defaultdict(dict)
    for r in csv.DictReader(open(f)):
        D[r["area"]][r["gas_day"]] = r
    return D

def fnum(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def europe_gas_wb(raw, out):
    day = entsog(raw); A = alsi(raw)
    wb = openpyxl.Workbook(); wb.remove(wb.active)
    days = sorted(day); last = days[-1]
    # monthly bcm by route
    mon = defaultdict(lambda: defaultdict(float)); cnt = defaultdict(set)
    for d in days:
        for k, v in day[d].items(): mon[d[:7]][k] += v / TWH_PER_BCM
        cnt[d[:7]].add(d)
    ws = wb.create_sheet("EU_Imports_by_Route_Monthly")
    ws.append(["Month", "Days"] + [r + " (bcm)" for r in ROUTES] + ["Total imports (bcm)", "LNG share %", "Russia share % (all routes)"])
    for m in sorted(mon):
        vals = [round(mon[m].get(r, 0), 2) for r in ROUTES]; t = sum(vals)
        ws.append([m, len(cnt[m])] + vals + [round(t, 2), round(100 * vals[1] / t, 1) if t else None, round(100 * (vals[4] + vals[5]) / t, 1) if t else None])
    style(ws, [9, 6] + [14] * len(ROUTES) + [12, 9, 11], "B2")
    note(ws, "EU gas imports by entry route, bcm per month (1 bcm = 10.55 TWh GCV). Source: ENTSOG Transparency Platform, physical flows at EU import and LNG entry points. "
             "Where several German TSOs report the same point (Emden EPT1, Dornum) the highest value is used, not the sum. Flows re-entering from Serbia, Switzerland and Moldova are left out as transit. "
             "TurkStream volumes at Strandzha 2 include gas that transits Bulgaria to Serbia and Hungary. Ukraine border = entries from Ukraine into Hungary, Poland, Romania and Slovakia. Latest month is partial.")
    # daily last 60 days
    ws = wb.create_sheet("EU_Imports_Daily_Last_60d")
    ws.append(["Gas day"] + [r + " (mcm/d)" for r in ROUTES] + ["Total (mcm/d)"])
    for d in days[-60:]:
        vals = [round(day[d].get(r, 0) / TWH_PER_BCM * 1000, 1) for r in ROUTES]; ws.append([d] + vals + [round(sum(vals), 1)])
    style(ws, [11] + [14] * len(ROUTES) + [12], "B2")
    note(ws, "Million cubic metres per day. Source: ENTSOG. The last few days are provisional.")
    # same-period comparison: last 30 days vs same 30 days a year earlier and two years earlier
    ws = wb.create_sheet("Route_Comparison")
    ld = dt.date.fromisoformat(last); w = [(ld - dt.timedelta(days=i)).isoformat() for i in range(30)]
    def avg(route, shift):
        xs = [day.get((dt.date.fromisoformat(x) - dt.timedelta(days=365 * shift)).isoformat(), {}).get(route) for x in w]
        xs = [x for x in xs if x is not None]; return sum(xs) / len(xs) / TWH_PER_BCM * 1000 if xs else None
    ws.append(["Route", "Last 30 days (mcm/d)", "Same period 2025", "Same period 2024", "Change vs 2025 %", "Change vs 2024 %"])
    for r in ROUTES + ["Total"]:
        if r == "Total":
            a = [sum(avg(x, s) or 0 for x in ROUTES) for s in (0, 1, 2)]
        else:
            a = [avg(r, s) for s in (0, 1, 2)]
        ws.append([r] + [None if x is None else round(x, 1) for x in a] + [pct(a[0], a[1]), pct(a[0], a[2])])
    style(ws, [44, 14, 14, 14, 12, 12], "B2")
    note(ws, "30 days to %s. Source: ENTSOG." % last)
    # ALSI LNG
    ws = wb.create_sheet("LNG_Terminals_ALSI")
    eu = A.get("EU", {}); ad = sorted(eu)[-1] if eu else None
    ws.append(["Area", "Gas day", "LNG in tanks (GWh)", "Send-out (GWh/d)", "Send-out 30d avg (GWh/d)", "Same 30d a year ago", "y/y %", "Declared total max inventory (GWh)", "Tank fill %"])
    for area in ["EU", "ES", "FR", "IT", "NL", "BE", "DE", "PL", "PT", "GR", "HR", "LT", "FI", "GB"]:
        s = A.get(area, {});
        if not s: continue
        dl = sorted(s)[-1]; r = s[dl]; ldd = dt.date.fromisoformat(dl)
        cur = [fnum(s.get((ldd - dt.timedelta(days=i)).isoformat(), {}).get("send_out_gwh_d")) for i in range(30)]
        prv = [fnum(s.get((ldd - dt.timedelta(days=365 + i)).isoformat(), {}).get("send_out_gwh_d")) for i in range(30)]
        cur = [x for x in cur if x is not None]; prv = [x for x in prv if x is not None]
        c = sum(cur) / len(cur) if cur else None; p = sum(prv) / len(prv) if prv else None
        inv, mx = fnum(r["inventory_gwh"]), fnum(r["dtmi_gwh"])
        ws.append([area, dl, inv, fnum(r["send_out_gwh_d"]), None if c is None else round(c, 1), None if p is None else round(p, 1), pct(c, p), mx, round(100 * inv / mx, 1) if inv and mx else None])
    style(ws, [8, 11, 14, 12, 14, 14, 8, 16, 9], "B2")
    note(ws, "Source: GIE ALSI (Aggregated LNG Storage Inventory). Send-out is regasified LNG sent into the grid. GB is outside the EU.")
    ws = wb.create_sheet("LNG_SendOut_Monthly")
    areas = [a for a in ["EU", "ES", "FR", "IT", "NL", "BE", "DE", "PL", "PT", "GR", "HR", "LT", "FI", "GB"] if a in A]
    months = sorted({d[:7] for d in eu})
    ws.append(["Month"] + [a + " (TWh)" for a in areas])
    for m in months:
        ws.append([m] + [round(sum(fnum(v["send_out_gwh_d"]) or 0 for d, v in A[a].items() if d.startswith(m)) / 1000, 2) for a in areas])
    style(ws, [9] + [9] * len(areas), "B2")
    note(ws, "Monthly LNG send-out, TWh. Source: GIE ALSI. Latest month is partial.")
    wb.save(out); return last

PINK_COLS = ["Crude oil, Brent", "Crude oil, Dubai", "Crude oil, WTI", "Natural gas, US", "Natural gas, Europe", "Liquefied natural gas, Japan", "Coal, Australian", "Coal, South African **",
             "Urea ", "DAP", "Aluminum", "Copper", "Nickel", "Iron ore, cfr spot", "Gold", "Silver", "Platinum"]
IMF_NAMES = {"POILBRE": "Brent", "POILWTI": "WTI", "POILDUB": "Dubai", "PNGASEU": "Natural gas, Europe (TTF)", "PNGASUS": "Natural gas, US (Henry Hub)", "PNGASJP": "LNG, Asia (IMF PNGASJP)",
             "PCOALAU": "Coal, Australia", "PCOALSA": "Coal, South Africa", "PURAN": "Uranium", "PNRG": "IMF energy price index", "PCOPP": "Copper", "PNICK": "Nickel", "PALUM": "Aluminium"}

def prices_sheets(raw, wb):
    f = glob.glob(os.path.join(raw, "*_WorldBank_Pink_Sheet_Commodity_Prices_Global_Monthly.xlsx"))[0]
    src = openpyxl.load_workbook(f, read_only=True, data_only=True)["Monthly Prices"]
    rows = list(src.iter_rows(values_only=True)); upd = rows[3][0]; hdr = rows[4]; units = rows[5]
    ix = [hdr.index(c) for c in PINK_COLS]
    data = [r for r in rows[6:] if r[0] and isinstance(r[0], str) and r[0][:4].isdigit()]
    ws = wb.create_sheet("WB_Pink_Sheet_Monthly")
    ws.append(["Month"] + ["%s %s" % (hdr[i].replace(" **", "").strip(), units[i]) for i in ix])
    for r in data:
        if r[0] >= "2015": ws.append([r[0].replace("M", "-")] + [r[i] if isinstance(r[i], (int, float)) else None for i in ix])
    style(ws, [9] + [12] * len(ix), "B2")
    note(ws, "World Bank Commodity Price Data (the Pink Sheet), nominal US$. %s. Licence CC-BY-4.0." % upd)
    ws = wb.create_sheet("WB_Pink_Sheet_Summary")
    ws.append(["Commodity", "Unit", "Latest month", "Latest", "Month before", "m/m %", "Year before", "y/y %", "2025 average", "2019 average (pre-Covid)"])
    for i in ix:
        s = [(r[0], r[i]) for r in data if isinstance(r[i], (int, float))]
        if not s: continue
        lm, lv = s[-1]; d = dict(s)
        y = str(int(lm[:4]) - 1) + lm[4:]; pm = s[-2][1] if len(s) > 1 else None
        a25 = [v for k, v in s if k.startswith("2025")]; a19 = [v for k, v in s if k.startswith("2019")]
        ws.append([hdr[i].replace(" **", "").strip(), units[i], lm.replace("M", "-"), round(lv, 2), round(pm, 2) if pm else None, pct(lv, pm), round(d[y], 2) if d.get(y) else None, pct(lv, d.get(y)),
                   round(sum(a25) / len(a25), 2) if a25 else None, round(sum(a19) / len(a19), 2) if a19 else None])
    style(ws, [28, 10, 10, 10, 10, 8, 10, 8, 11, 12], "B2")
    note(ws, "Source: World Bank Pink Sheet. %s." % upd)
    # IMF PCPS
    f = glob.glob(os.path.join(raw, "*_IMF_PCPS_Commodity_Prices_Global_Monthly.csv"))[0]
    S = defaultdict(dict)
    for r in csv.DictReader(open(f)): S[r["indicator"]][r["period"].replace("-M", "-")] = float(r["value_usd"])
    ms = sorted({m for s in S.values() for m in s if m >= "2019-01"})
    ws = wb.create_sheet("IMF_Commodity_Prices_Monthly")
    keys = [k for k in IMF_NAMES if k in S]
    ws.append(["Month"] + [IMF_NAMES[k] for k in keys])
    for m in ms: ws.append([m] + [None if S[k].get(m) is None else round(S[k][m], 2) for k in keys])
    style(ws, [9] + [13] * len(keys), "B2")
    note(ws, "IMF Primary Commodity Prices (PCPS), US$ (oil $/bbl, gas and LNG $/MMBtu, coal $/t, uranium $/lb, metals $/t; PNRG is an index, 2016=100). Source: IMF data API, pulled 10 Nov 2026.")

WEO_REGIONS = [("WEOWORLD", "World"), ("ADVEC", "Advanced economies"), ("OEMDC", "Emerging and developing economies"), ("EURO", "Euro area"), ("EU", "European Union"), ("MECA", "Middle East and Central Asia")]
WEO_KEY = [("USA", "United States"), ("CHN", "China"), ("IND", "India"), ("JPN", "Japan"), ("DEU", "Germany"), ("GBR", "United Kingdom"), ("FRA", "France"), ("ITA", "Italy"), ("BRA", "Brazil"),
           ("RUS", "Russia"), ("CAN", "Canada"), ("KOR", "South Korea"), ("MEX", "Mexico"), ("IDN", "Indonesia"), ("TUR", "Turkiye"), ("SAU", "Saudi Arabia"), ("ARE", "United Arab Emirates"),
           ("IRN", "Iran"), ("IRQ", "Iraq"), ("KWT", "Kuwait"), ("QAT", "Qatar"), ("NGA", "Nigeria"), ("ZAF", "South Africa"), ("EGY", "Egypt"), ("AUS", "Australia"), ("NOR", "Norway"),
           ("ARG", "Argentina"), ("VNM", "Vietnam"), ("THA", "Thailand"), ("PAK", "Pakistan")]

def macro_wb(raw, out):
    f = glob.glob(os.path.join(raw, "*_IMF_WEO_Macro_by_Country_Global_Annual.csv"))[0]
    V = defaultdict(lambda: defaultdict(dict))
    for r in csv.DictReader(open(f)):
        try: V[r["indicator"]][r["iso3"]][int(r["year"])] = float(r["value"])
        except ValueError: pass
    wb = openpyxl.Workbook(); wb.remove(wb.active)
    yrs = list(range(2019, 2028))
    for ind, title, unit in [("NGDP_RPCH", "Real_GDP_Growth", "%"), ("PCPIPCH", "CPI_Inflation", "%")]:
        ws = wb.create_sheet(title); ws.append(["Code", "Economy"] + [str(y) for y in yrs])
        for code, nm in WEO_REGIONS + [("", "")] + WEO_KEY:
            if not code: ws.append([]); continue
            ws.append([code, nm] + [None if V[ind][code].get(y) is None else round(V[ind][code][y], 1) for y in yrs])
        style(ws, [10, 34] + [7] * len(yrs))
        note(ws, "%s, %s. Source: IMF World Economic Outlook via the IMF DataMapper API, pulled 10 Nov 2026 (latest WEO vintage). Years from the current year onward are IMF projections." % (title.replace("_", " "), unit))
    ws = wb.create_sheet("GDP_and_Population"); ws.append(["Code", "Economy", "GDP 2025 (US$bn)", "GDP 2026 (US$bn)", "Share of world GDP 2026 %", "Population 2026 (m)", "GDP per head 2026 (US$)"])
    w26 = V["NGDPD"]["WEOWORLD"].get(2026)
    for code, nm in WEO_REGIONS + WEO_KEY:
        g25, g26, p = V["NGDPD"][code].get(2025), V["NGDPD"][code].get(2026), V["LP"][code].get(2026)
        ws.append([code, nm, None if g25 is None else round(g25), None if g26 is None else round(g26), round(100 * g26 / w26, 1) if g26 and w26 else None, None if p is None else round(p, 1), round(g26 * 1000 / p) if g26 and p else None])
    style(ws, [10, 34, 12, 12, 12, 12, 12])
    note(ws, "Nominal GDP in current US$ and population. Source: IMF WEO via DataMapper API.")
    wb.save(out)

def build(root, date):
    raw = os.path.join(root, "01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/Other_Sources/API_%s" % date)
    outs = []
    p = os.path.join(root, "03_Midstream_Logistics_and_Transportation/03.3_Storage_and_Terminals/%s_Analysis_Europe_Gas_Supply_and_LNG_Europe_Daily_v01.xlsx" % date)
    last = europe_gas_wb(raw, p); outs.append(p)
    wb = openpyxl.Workbook(); wb.remove(wb.active); prices_sheets(raw, wb)
    p = os.path.join(root, "07_Financial_Analysis_and_Trading/07.1_Commodity_Pricing/%s_Analysis_Global_Commodity_Prices_WB_IMF_Global_Monthly_v01.xlsx" % date); wb.save(p); outs.append(p)
    p = os.path.join(root, "01_Market_Foundations_and_Data/01.3_Macro_Economic_Indicators/%s_Analysis_Global_Macro_IMF_WEO_Global_Annual_v01.xlsx" % date)
    os.makedirs(os.path.dirname(p), exist_ok=True); macro_wb(raw, p); outs.append(p)
    return outs, last

if __name__ == "__main__":
    o, l = build(sys.argv[1], sys.argv[2]); print("\n".join(o)); print("ENTSOG last day", l)
