"""EU gas storage model: warm, normal and cold winter cases to 31 March, with live Excel formulas.

Usage:
    python3 20261110_Code_Build_EU_Gas_Storage_Model_Europe_v01.py <ENERGY ANALYSIS folder> <raw folder> [--out FILE] [--start YYYY-MM-DD] [--paths-csv FILE]

<raw folder> must hold one GIE AGSI+ storage file (*_GIE_AGSI_Gas_Storage_Europe_Daily.csv) and one ENTSOG flows file
(*_ENTSOG_Physical_Flows_EU_Import_Points_Europe_Daily.csv), as written by the data pull script or the GitHub Actions pull.

How the model works (all in formulas, so any blue input can be changed in Excel):
  call on storage  = EU consumption + net exports - EU production, measured in the data as imports + net storage withdrawal
  normal call      = average of the last two winters, by half-month (Calibration sheet)
  case call        = (non-heating call + heating call x (1 + weather adjustment)) x (1 - demand response)
  supply           = pipeline and LNG imports by route (last 30 days, or your own level) + LNG case adjustment + Gulf LNG recovery ramp
  withdrawal       = call - supply, capped by what storage can deliver at that fill level; anything above the cap is unmet demand
The script also computes the same model in Python so it can write the case paths to CSV for the weekly note.
Keys: none needed. Sources: GIE AGSI+ (storage), ENTSOG Transparency Platform (flows).
"""
import argparse, csv, datetime as dt, glob, os, statistics as st
from collections import defaultdict
import openpyxl
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.workbook.defined_name import DefinedName

TWH_PER_BCM = 10.55
ROUTE = {}
for k in ["ITP-00106", "ITP-00105", "ITP-00081", "ITP-00080", "ITP-00188", "ITP-00126", "ITP-00525", "ITP-00630", "ITP-00045", "ITP-00160"]: ROUTE[k] = "Norway"
for k in ["ITP-00549", "ITP-00041"]: ROUTE[k] = "Russia via TurkStream"
for k in ["ITP-00297", "ITP-00491", "ITP-00247", "ITP-00501", "ITP-00493", "ITP-00024", "ITP-00243", "ITP-00187"]: ROUTE[k] = "Russia, other routes"
for k in ["ITP-00087", "ITP-00299", "ITP-00300", "ITP-00438", "ITP-00117", "ITP-00421", "ITP-10006", "ITP-10008"]: ROUTE[k] = "Ukraine border"
for k in ["ITP-00274", "ITP-00046"]: ROUTE[k] = "Azerbaijan (TAP)"
for k in ["ITP-00093", "ITP-00074", "ITP-00048", "ITP-00082"]: ROUTE[k] = "North Africa"
SAME = {"ITP-00105": "Emden", "ITP-00081": "Emden", "ITP-00080": "Emden", "ITP-00188": "Dornum", "ITP-00126": "Dornum", "ITP-00525": "Dornum"}
ROUTES = ["LNG", "Norway", "North Africa", "Azerbaijan (TAP)", "Russia via TurkStream", "Russia, other routes", "Ukraine border"]

# ---------------------------------------------------------------- default assumptions (blue cells in Inputs)
CASES = ["Warm", "Normal", "Cold"]
WEATHER_ADJ = {"Warm": -0.12, "Normal": 0.0, "Cold": 0.12}      # change in heating demand vs normal (whole winter)
LNG_ADJ = {"Warm": 0.15, "Normal": 0.0, "Cold": -0.25}          # TWh/d: a cold winter is usually cold in Asia too
DEMAND_RESP = {"Warm": 0.0, "Normal": 0.0, "Cold": 0.0}         # extra price-driven demand cut, share of call
GULF = {"uplift": 0.50, "start": dt.date(2026, 12, 1), "full": dt.date(2027, 3, 1)}  # extra LNG into the EU as Qatar recovers
MAXW = {"cap": 11.0, "slope": 0.30}                              # deliverability: min(cap, slope x fill %)
END = dt.date(2027, 3, 31)

BLUE = Font(color="0000CC"); BOLD = Font(bold=True); HDR = PatternFill("solid", fgColor="1F4E78"); HFONT = Font(bold=True, color="FFFFFF")
INFILL = PatternFill("solid", fgColor="FFF2CC"); NOTE = Font(italic=True, color="555555"); THIN = Side(style="thin", color="BBBBBB")


def fnum(x):
    try: return float(x)
    except (TypeError, ValueError): return None


def load(raw):
    f = glob.glob(os.path.join(raw, "*_GIE_AGSI_Gas_Storage_Europe_Daily.csv"))[0]
    stor = {}
    for r in csv.DictReader(open(f)):
        if r["area_code"] == "eu" and fnum(r["gasInStorage"]) is not None:
            stor[r["gasDayStart"]] = dict(twh=fnum(r["gasInStorage"]), wgv=fnum(r["workingGasVolume"]), full=fnum(r["full"]),
                                         inj=(fnum(r["injection"]) or 0) / 1000, wd=(fnum(r["withdrawal"]) or 0) / 1000)
    f = glob.glob(os.path.join(raw, "*_ENTSOG_Physical_Flows_EU_Import_Points_Europe_Daily.csv"))[0]
    loc = defaultdict(dict); meta = {}
    for r in csv.DictReader(open(f)):
        if not r["value"]: continue
        pk = r["point_key"]; pt = r["point_type"] or ""
        route = "LNG" if pt.startswith("LNG") else ROUTE.get(pk)
        if not route: continue
        locn = SAME.get(pk, pk); meta[locn] = route
        loc[(r["gas_day"], locn)][r["operator_key"] + pk] = float(r["value"])
    flows = defaultdict(lambda: defaultdict(float))
    for (d, l), ops in loc.items():
        v = max(ops.values()) if l in SAME.values() else sum(ops.values())
        flows[d][meta[l]] += v / 1e9  # kWh/d -> TWh/d
    return stor, flows


def half(d):
    return d.month * 10 + (1 if d.day <= 15 else 2)


HALVES = [(11, 1), (11, 2), (12, 1), (12, 2), (1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (3, 2)]
HLABEL = {m * 10 + h: "%s %s" % (["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][m - 1], "1-15" if h == 1 else "16-end") for m, h in HALVES}


def winter_of(d):
    return "%d-%02d" % (d.year, (d.year + 1) % 100) if d.month >= 7 else "%d-%02d" % (d.year - 1, d.year % 100)


# ---------------------------------------------------------------- Python mirror of the Excel model

def calibrate(stor, flows, last):
    days = sorted(d for d in flows if d in stor and d <= last)
    call = {d: sum(flows[d].values()) + stor[d]["wd"] - stor[d]["inj"] for d in days}
    ld = dt.date.fromisoformat(last)
    winters = sorted({winter_of(dt.date.fromisoformat(d)) for d in days if dt.date.fromisoformat(d).month in (11, 12, 1, 2, 3)})
    full_w = [w for w in winters if dt.date(int(w[:4]) + 1, 3, 31).isoformat() <= last][-2:]
    norm = {}
    for m, h in HALVES:
        k = m * 10 + h
        vals = [st.mean([call[d] for d in days if half(dt.date.fromisoformat(d)) == k and winter_of(dt.date.fromisoformat(d)) == w]) for w in full_w]
        norm[k] = st.mean(vals)
    summer_years = sorted({d[:4] for d in days if d[5:7] in ("06", "07", "08") and d[:4] < last[:4] or (d[:4] == last[:4] and d[5:7] in ("06", "07", "08"))})[-2:]
    base = st.mean([call[d] for d in days if d[5:7] in ("06", "07", "08") and d[:4] in summer_years])
    l30 = [(ld - dt.timedelta(days=i)).isoformat() for i in range(30)]
    route30 = {r: st.mean([flows[d].get(r, 0) for d in l30 if d in flows]) for r in ROUTES}
    return call, full_w, norm, base, summer_years, route30


def run_case(case, start, s0, wgv, norm, base, route30, gulf=GULF):
    rows, s = [], s0
    d = start
    while d <= END:
        n = norm[half(d)]
        c = (base + (n - base) * (1 + WEATHER_ADJ[case])) * (1 - DEMAND_RESP[case])
        ramp = 0 if d < gulf["start"] else min(1, (d - gulf["start"]).days / max(1, (gulf["full"] - gulf["start"]).days))
        sup = sum(route30.values()) + LNG_ADJ[case] + gulf["uplift"] * ramp
        req = c - sup
        maxw = min(MAXW["cap"], MAXW["slope"] * 100 * s / wgv)
        w = min(req, maxw) if req > 0 else max(req, s - wgv)
        unmet = max(0, req - maxw)
        s = s - w
        rows.append(dict(date=d, call=c, supply=sup, req=req, maxw=maxw, wd=w, unmet=unmet, twh=s, pct=100 * s / wgv))
        d += dt.timedelta(days=1)
    return rows


# ---------------------------------------------------------------- workbook

def hdr(ws, row, values, widths=None):
    for i, v in enumerate(values, 1):
        c = ws.cell(row, i, v); c.font = HFONT; c.fill = HDR; c.alignment = Alignment(wrap_text=True, vertical="top")
    if widths:
        for i, w in enumerate(widths, 1): ws.column_dimensions[L(i)].width = w


def name(wb, nm, ref):
    wb.defined_names[nm] = DefinedName(nm, attr_text=ref)


def build(root, raw, out, start=None, paths_csv=None):
    stor, flows = load(raw)
    last = max(d for d in stor if d in flows)
    start = start or (dt.date.fromisoformat(last) + dt.timedelta(days=1))
    s0_day = (start - dt.timedelta(days=1)).isoformat()
    s0, wgv = stor[s0_day]["twh"], stor[s0_day]["wgv"]
    call, full_w, norm, base, summer_years, route30 = calibrate(stor, flows, s0_day)

    wb = openpyxl.Workbook(); wb.remove(wb.active)
    rd = wb.create_sheet("README"); inp = wb.create_sheet("Inputs"); summ = wb.create_sheet("Summary")
    mod = wb.create_sheet("Model_Daily"); cal = wb.create_sheet("Calibration"); dat = wb.create_sheet("Data_Daily")

    # ---- Data_Daily: one row per gas day since 2024 (values from the raw files)
    days = sorted(d for d in stor if d >= "2021-01-01")
    hdr(dat, 1, ["Gas day", "Storage (TWh)", "Working gas volume (TWh)", "Full %", "Injection (TWh/d)", "Withdrawal (TWh/d)"] + ["%s (TWh/d)" % r for r in ROUTES] +
        ["Total imports (TWh/d)", "Call on imports and storage (TWh/d)", "Half-month key", "Winter", "Month"], [11, 10, 10, 8, 9, 9] + [9] * len(ROUTES) + [10, 12, 8, 9, 7])
    for i, d in enumerate(days, 2):
        x = stor[d]; dd = dt.date.fromisoformat(d)
        row = [dd, x["twh"], x["wgv"], x["full"], round(x["inj"], 4), round(x["wd"], 4)]
        if d in flows:
            row += [round(flows[d].get(r, 0), 4) for r in ROUTES]
            fc, lc = L(7), L(6 + len(ROUTES))
            row += ["=SUM(%s%d:%s%d)" % (fc, i, lc, i), "=%s%d+F%d-E%d" % (L(7 + len(ROUTES)), i, i, i)]
        else:
            row += [None] * (len(ROUTES) + 2)
        row += ["=MONTH(A%d)*10+IF(DAY(A%d)<=15,1,2)" % (i, i), '=IF(MONTH(A%d)>=7,YEAR(A%d)&"-"&RIGHT(YEAR(A%d)+1,2),YEAR(A%d)-1&"-"&RIGHT(YEAR(A%d),2))' % (i, i, i, i, i), "=MONTH(A%d)" % i]
        dat.append(row); dat.cell(i, 1).number_format = "yyyy-mm-dd"
    n = len(days) + 1
    dat.freeze_panes = "B2"
    C = {k: "Data_Daily!$%s$2:$%s$%d" % (L(j), L(j), n) for k, j in
         [("date", 1), ("twh", 2), ("full", 4), ("call", 8 + len(ROUTES)), ("key", 9 + len(ROUTES)), ("winter", 10 + len(ROUTES)), ("month", 11 + len(ROUTES))]}
    for j, r in enumerate(ROUTES):
        C[r] = "Data_Daily!$%s$2:$%s$%d" % (L(7 + j), L(7 + j), n)

    # ---- Calibration
    hdr(cal, 1, ["Half-month", "Key"] + ["Winter %s (TWh/d)" % w for w in full_w] + ["Normal call (TWh/d)", "Non-heating call (TWh/d)", "Heating call (TWh/d)"], [14, 6, 14, 14, 13, 13, 13])
    for i, (m, h) in enumerate(HALVES, 2):
        k = m * 10 + h
        cal.cell(i, 1, HLABEL[k]); cal.cell(i, 2, k)
        for j, w in enumerate(full_w):
            cal.cell(i, 3 + j, '=AVERAGEIFS(%s,%s,B%d,%s,"%s")' % (C["call"], C["key"], i, C["winter"], w)).number_format = "0.00"
        cal.cell(i, 5, "=AVERAGE(C%d:D%d)" % (i, i)).number_format = "0.00"
        cal.cell(i, 6, "=NonHeatingCall").number_format = "0.00"
        cal.cell(i, 7, "=E%d-F%d" % (i, i)).number_format = "0.00"
    cal.cell(13, 1, "Non-heating call: June to August average of %s" % " and ".join(summer_years)).font = BOLD
    yrs = summer_years
    cal.cell(13, 5, "=(AVERAGEIFS(%s,%s,\">=6\",%s,\"<=8\",%s,\">=\"&DATE(%s,1,1),%s,\"<\"&DATE(%s,1,1)))" % (C["call"], C["month"], C["month"], C["date"], yrs[0], C["date"], int(yrs[-1]) + 1)).number_format = "0.00"
    name(wb, "NonHeatingCall", "Calibration!$E$13")
    notes = ["The call on imports and storage = EU consumption + net exports to non-EU neighbours - EU production. It is measured as imports (ENTSOG) + net withdrawal from storage (GIE AGSI+).",
             "Normal call = the average of the last two complete winters (%s), by half-month. Winter 2025-26 included a cold January." % " and ".join(full_w),
             "Heating call = normal call - non-heating call. The weather cases scale only the heating part.",
             "Limitations: two winters is a short base, and no weather data is used yet (weather APIs are blocked in this build environment; the GitHub Actions pull adds heating degree days)."]
    for i, t in enumerate(notes, 15): cal.cell(i, 1, t).font = NOTE

    # ---- Inputs
    inp.column_dimensions["A"].width = 46
    for c in "BCDE": inp.column_dimensions[c].width = 14
    inp.column_dimensions["F"].width = 70
    inp["A1"] = "Inputs: blue cells on yellow are assumptions you can change. Everything else is a formula."; inp["A1"].font = BOLD
    r = 3
    hdr(inp, r, ["Starting point", "Value", "", "", "", "Note"])
    def put(row, label, val, nm=None, fmt=None, note="", blue=True):
        inp.cell(row, 1, label); c = inp.cell(row, 2, val)
        if blue: c.font = BLUE; c.fill = INFILL
        if fmt: c.number_format = fmt
        if nm: name(wb, nm, "Inputs!$B$%d" % row)
        inp.cell(row, 6, note).font = NOTE
    put(4, "Model start (first projected gas day)", start, "StartDate", "yyyy-mm-dd", "Day after the latest storage data.")
    put(5, "Storage at start (TWh)", "=INDEX(%s,MATCH(StartDate-1,%s,0))" % (C["twh"], C["date"]), "StartTWh", "0.0", "GIE AGSI+, EU, end of the gas day before the start.", blue=False)
    put(6, "Working gas volume (TWh)", wgv, "WGV", "0.0", "GIE AGSI+ declared working gas volume.")
    put(7, "Start fill %", "=StartTWh/WGV", None, "0.0%", "", blue=False)
    put(8, "Model end", END, "EndDate", "yyyy-mm-dd", "")
    r = 10
    hdr(inp, r, ["Weather and demand", "Warm", "Normal", "Cold", "", "Note"])
    for i, (lab, d, nm, fmt, note) in enumerate([
            ("Heating demand vs normal", WEATHER_ADJ, "Weather", "0%", "Applied to the heating part of the call only. +/-12% is roughly a 1-in-10 mild or cold winter for EU heating degree days (assumption)."),
            ("Extra demand cut from high prices (share of call)", DEMAND_RESP, "DemandCut", "0.0%", "0 means demand behaves as in the last two winters. Each 1% is about 1.6 TWh over the winter per TWh/d of call."),
            ("LNG send-out adjustment (TWh/d)", LNG_ADJ, "LNGAdj", "0.00", "Judgement: a cold Europe usually means a cold Northeast Asia bidding for the same cargoes.")], r + 1):
        inp.cell(i, 1, lab)
        for j, cs in enumerate(CASES):
            c = inp.cell(i, 2 + j, d[cs]); c.font = BLUE; c.fill = INFILL; c.number_format = fmt
            name(wb, "%s_%s" % (nm, cs), "Inputs!$%s$%d" % (L(2 + j), i))
        inp.cell(i, 6, note).font = NOTE
    r = 15
    hdr(inp, r, ["Imports by route (TWh/d)", "Last 30 days", "Assumed to 31 Mar", "mcm/d", "", "Note"])
    for i, rt in enumerate(ROUTES, r + 1):
        inp.cell(i, 1, rt)
        inp.cell(i, 2, "=AVERAGEIFS(%s,%s,\">=\"&(StartDate-30),%s,\"<\"&StartDate)" % (C[rt], C["date"], C["date"])).number_format = "0.00"
        c = inp.cell(i, 3, "=B%d" % i); c.font = BLUE; c.fill = INFILL; c.number_format = "0.00"
        inp.cell(i, 4, "=C%d/%s*1000" % (i, TWH_PER_BCM)).number_format = "0"
    tot = r + 1 + len(ROUTES)
    inp.cell(tot, 1, "Total imports").font = BOLD
    for col in "BCD": inp["%s%d" % (col, tot)] = "=SUM(%s%d:%s%d)" % (col, r + 1, col, tot - 1); inp["%s%d" % (col, tot)].number_format = "0.00" if col != "D" else "0"
    name(wb, "BaseImports", "Inputs!$C$%d" % tot)
    inp.cell(r + 1, 6, "Overwrite column C to test an outage or a change in flows, e.g. Norway maintenance.").font = NOTE
    r = tot + 2
    hdr(inp, r, ["Gulf LNG recovery", "Value", "", "", "", "Note"])
    put(r + 1, "Extra LNG into the EU at full recovery (TWh/d)", GULF["uplift"], "GulfUplift", "0.00", "0.50 TWh/d (about 47 mcm/d) restores EU LNG send-out to last year's level for the same weeks.")
    put(r + 2, "Recovery starts reaching EU terminals", GULF["start"], "GulfStart", "yyyy-mm-dd", "Qatari loadings were reported at about half of pre-war levels on 10 Nov (Bloomberg). Allow ~3 weeks of voyage.")
    put(r + 3, "Full recovery reached", GULF["full"], "GulfFull", "yyyy-mm-dd", "Linear ramp between the two dates. Damaged trains stay out (see the LNG balance).")
    r += 5
    hdr(inp, r, ["Storage deliverability", "Value", "", "", "", "Note"])
    put(r + 1, "Maximum EU withdrawal (TWh/d)", MAXW["cap"], "MaxWCap", "0.0", "Highest daily withdrawals observed since 2021 were about 10.4-10.9 TWh/d at 40-70% full (GIE AGSI+).")
    put(r + 2, "Withdrawal capacity per point of fill (TWh/d per %)", MAXW["slope"], "MaxWSlope", "0.00", "Capacity falls as storage empties: about 9 TWh/d at 30% full, 6 at 20%, 3 at 10%. Fitted to observed peaks.")
    r += 4
    hdr(inp, r, ["Reference levels", "Value", "", "", "", "Note"])
    put(r + 1, "EU storage on 31 Mar 2026", "=INDEX(%s,MATCH(DATE(2026,3,31),%s,0))/100" % (C["full"], C["date"]), "Ref2026", "0.0%", "Last winter's end point (GIE AGSI+).", blue=False)
    put(r + 2, "Comfortable end-winter level", 0.30, "RefComfort", "0%", "Market rule of thumb; below it, refilling to 90% needs record summer injections.")
    put(r + 3, "Refill target for 2027 (any day 1 Oct-1 Dec)", 0.90, "RefillTarget", "0%", "EU Gas Storage Regulation as amended in 2025; member states may deviate by up to 10 points in difficult conditions.")
    put(r + 4, "Refill season (days, 1 Apr-1 Nov)", 214, "RefillDays", "0", "")

    # ---- Model_Daily
    heads = ["Gas day", "Half-month key", "Normal call (TWh/d)", "Gulf LNG ramp (0-1)"]
    sub = ["Call", "Supply", "Needed from storage", "Max withdrawal", "Withdrawal", "Unmet demand", "Storage TWh", "Full %"]
    for cs in CASES: heads += ["%s: %s" % (cs, s) for s in sub]
    hist = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
    heads += ["Actual full % (data)", "Actual minus Normal (points)"] + ["Same date %s %%" % h for h in hist]
    hdr(mod, 1, heads, [11, 7, 9, 8] + [9] * (8 * 3) + [9, 9] + [8] * 5)
    nd = (END - start).days + 1
    for i in range(2, nd + 2):
        mod.cell(i, 1, "=StartDate" if i == 2 else "=A%d+1" % (i - 1)).number_format = "yyyy-mm-dd"
        mod.cell(i, 2, "=MONTH(A%d)*10+IF(DAY(A%d)<=15,1,2)" % (i, i))
        mod.cell(i, 3, "=INDEX(Calibration!$E$2:$E$11,MATCH(B%d,Calibration!$B$2:$B$11,0))" % i).number_format = "0.00"
        mod.cell(i, 4, "=IF(A%d<GulfStart,0,MIN(1,(A%d-GulfStart)/MAX(1,GulfFull-GulfStart)))" % (i, i)).number_format = "0.00"
        for k, cs in enumerate(CASES):
            c0 = 5 + 8 * k; col = {s: L(c0 + j) for j, s in enumerate(sub)}
            prev = "StartTWh" if i == 2 else "%s%d" % (col["Storage TWh"], i - 1)
            f = {
                "Call": "=(NonHeatingCall+(C{i}-NonHeatingCall)*(1+Weather_{cs}))*(1-DemandCut_{cs})",
                "Supply": "=BaseImports+LNGAdj_{cs}+GulfUplift*D{i}",
                "Needed from storage": "={c}{i}-{s}{i}",
                "Max withdrawal": "=MIN(MaxWCap,MaxWSlope*100*{prev}/WGV)",
                "Withdrawal": "=IF({n}{i}>0,MIN({n}{i},{m}{i}),MAX({n}{i},{prev}-WGV))",
                "Unmet demand": "=MAX(0,{n}{i}-{m}{i})",
                "Storage TWh": "={prev}-{w}{i}",
                "Full %": "={t}{i}/WGV",
            }
            for j, s in enumerate(sub):
                cell = mod.cell(i, c0 + j, f[s].format(i=i, cs=cs, c=col["Call"], s=col["Supply"], n=col["Needed from storage"], m=col["Max withdrawal"],
                                                       w=col["Withdrawal"], t=col["Storage TWh"], prev=prev))
                cell.number_format = "0.0%" if s == "Full %" else ("0.0" if s == "Storage TWh" else "0.00")
        a = 5 + 24
        mod.cell(i, a, "=IFERROR(INDEX(%s,MATCH(A%d,%s,0))/100,\"\")" % (C["full"], i, C["date"])).number_format = "0.0%"
        mod.cell(i, a + 1, "=IF(%s%d=\"\",\"\",(%s%d-%s%d)*100)" % (L(a), i, L(a), i, L(5 + 8 + 7), i)).number_format = "0.0"
        for h in range(5):
            back = 5 - h
            mod.cell(i, a + 2 + h, "=IFERROR(INDEX(%s,MATCH(EDATE(A%d,-%d),%s,0))/100,\"\")" % (C["full"], i, 12 * back, C["date"])).number_format = "0.0%"
    mod.freeze_panes = "B2"
    last_row = nd + 1
    pct_cols = {cs: L(5 + 8 * k + 7) for k, cs in enumerate(CASES)}
    unmet_cols = {cs: L(5 + 8 * k + 5) for k, cs in enumerate(CASES)}

    # ---- Summary
    summ.column_dimensions["A"].width = 44
    for c in "BCD": summ.column_dimensions[c].width = 13
    summ["A1"] = "EU gas storage to 31 March: three winter cases"; summ["A1"].font = Font(bold=True, size=13)
    summ["A2"] = "=\"Start: \"&TEXT(StartTWh,\"0\")&\" TWh (\"&TEXT(StartTWh/WGV,\"0.0%\")&\") at the end of gas day \"&TEXT(StartDate-1,\"d mmm yyyy\")&\". Sources: GIE AGSI+, ENTSOG.\""
    hdr(summ, 4, ["Result", "Warm", "Normal", "Cold"])
    rng = lambda c: "Model_Daily!$%s$2:$%s$%d" % (c, c, last_row)
    dates = rng("A")
    lines = [
        ("Storage full % on 31 Dec 2026", lambda cs: "=INDEX(%s,MATCH(DATE(2026,12,31),%s,0))" % (rng(pct_cols[cs]), dates), "0.0%"),
        ("Storage full % on 31 Jan 2027", lambda cs: "=INDEX(%s,MATCH(DATE(2027,1,31),%s,0))" % (rng(pct_cols[cs]), dates), "0.0%"),
        ("Storage full % on 28 Feb 2027", lambda cs: "=INDEX(%s,MATCH(DATE(2027,2,28),%s,0))" % (rng(pct_cols[cs]), dates), "0.0%"),
        ("Storage full % on 31 Mar 2027", lambda cs: "=INDEX(%s,MATCH(EndDate,%s,0))" % (rng(pct_cols[cs]), dates), "0.0%"),
        ("Storage TWh on 31 Mar 2027", lambda cs: "=%s*WGV" % ("%s8" % "BCD"[CASES.index(cs)]), "0"),
        ("Lowest fill % in the winter", lambda cs: "=MIN(%s)" % rng(pct_cols[cs]), "0.0%"),
        ("First day below 30% full", lambda cs: "=IFERROR(INDEX(%s,MATCH(TRUE,INDEX(%s<0.3,0),0)),\"not reached\")" % (dates, rng(pct_cols[cs])), "d mmm yyyy"),
        ("First day below 20% full", lambda cs: "=IFERROR(INDEX(%s,MATCH(TRUE,INDEX(%s<0.2,0),0)),\"not reached\")" % (dates, rng(pct_cols[cs])), "d mmm yyyy"),
        ("Unmet demand: storage cannot deliver (TWh)", lambda cs: "=SUM(%s)" % rng(unmet_cols[cs]), "0.0"),
        ("Unmet demand as bcm", lambda cs: "=%s13/%s" % ("BCD"[CASES.index(cs)], TWH_PER_BCM), "0.0"),
        ("End-March vs last year (points)", lambda cs: "=(%s8-Ref2026)*100" % "BCD"[CASES.index(cs)], "0.0"),
        ("Summer injection needed to reach the refill target (TWh/d)", lambda cs: "=(RefillTarget-%s8)*WGV/RefillDays" % "BCD"[CASES.index(cs)], "0.00"),
    ]
    for i, (lab, fn, fmt) in enumerate(lines, 5):
        summ.cell(i, 1, lab)
        for j, cs in enumerate(CASES):
            summ.cell(i, 2 + j, fn(cs)).number_format = fmt
    summ.cell(18, 1, "For comparison: average summer injection Apr-Oct 2026 (TWh/d)")
    summ.cell(18, 3, "=AVERAGEIFS(Data_Daily!$E$2:$E$%d,%s,\">=\"&DATE(2026,4,1),%s,\"<\"&DATE(2026,11,1))-AVERAGEIFS(Data_Daily!$F$2:$F$%d,%s,\">=\"&DATE(2026,4,1),%s,\"<\"&DATE(2026,11,1))" % (n, C["date"], C["date"], n, C["date"], C["date"])).number_format = "0.00"
    summ.cell(20, 1, "Reading the cases").font = BOLD
    for i, t in enumerate([
            "Warm and cold change only the weather (heating demand +/-12%) and the LNG Europe can attract; imports by route and the Gulf recovery are the same in all three.",
            "'Unmet demand' is gas the system needs but storage cannot physically deliver at that fill level. In practice prices rise until industry and power cut that much demand or more LNG arrives.",
            "This is a model, not a forecast. The published call is the one in the call log, with the date it was made."], 21):
        summ.cell(i, 1, t).font = NOTE

    ch = LineChart(); ch.title = "EU gas storage, % full: model cases vs past winters"; ch.y_axis.title = "% full"; ch.height = 10; ch.width = 24
    ch.y_axis.number_format = "0%"
    for c in [pct_cols[cs] for cs in CASES] + [L(29)] + [L(31 + h) for h in range(5)]:
        idx = openpyxl.utils.column_index_from_string(c)
        ch.add_data(Reference(mod, min_col=idx, min_row=1, max_row=last_row), titles_from_data=True)
    ch.set_categories(Reference(mod, min_col=1, min_row=2, max_row=last_row))
    ch.x_axis.number_format = "d mmm"; ch.x_axis.majorTimeUnit = "months"
    summ.add_chart(ch, "F4")

    # ---- README
    rd.column_dimensions["A"].width = 120
    for i, t in enumerate([
            "EU gas storage model: warm, normal and cold winter cases to 31 March 2027",
            "Built %s from GIE AGSI+ storage (to gas day %s) and ENTSOG physical flows. Script: 09_Code/Data_Pulls/20261110_Code_Build_EU_Gas_Storage_Model_Europe_v01.py" % (dt.date.today().isoformat(), s0_day),
            "",
            "How to use: change the blue cells in Inputs. Summary and the chart update. Model_Daily holds the day-by-day path for each case.",
            "Logic: storage(t) = storage(t-1) - withdrawal(t); withdrawal = call on storage - imports, capped by deliverability at that fill level.",
            "Call on storage = consumption + net exports - EU production, measured as imports + net withdrawal (Calibration and Data_Daily).",
            "Normal call = average of the last two full winters by half-month. Weather cases scale the heating part (call above the summer level).",
            "Actual full % fills in automatically as new data is pulled; 'Actual minus Normal' shows how far reality is running from the normal case.",
            "",
            "Units: TWh (gross calorific value) as reported by GIE; 1 bcm = 10.55 TWh. Storage % = gas in storage / working gas volume.",
            "Sources: GIE AGSI+ (agsi.gie.eu) and ENTSOG Transparency Platform (transparency.entsog.eu), both free. Not investment advice."], 1):
        rd.cell(i, 1, t).font = Font(bold=True, size=13) if i == 1 else Font()
    wb.calculation.fullCalcOnLoad = True
    wb.save(out)

    # ---- Python mirror for the paths CSV
    paths = {cs: run_case(cs, start, s0, wgv, norm, base, route30) for cs in CASES}
    if paths_csv:
        with open(paths_csv, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["vintage", "gas_day"] + ["%s_full_pct" % cs.lower() for cs in CASES] + ["%s_unmet_twh" % cs.lower() for cs in CASES])
            for i in range(len(paths["Normal"])):
                w.writerow([s0_day, paths["Normal"][i]["date"].isoformat()] + [round(paths[cs][i]["pct"], 2) for cs in CASES] + [round(paths[cs][i]["unmet"], 3) for cs in CASES])
    return dict(last=s0_day, s0=s0, wgv=wgv, norm=norm, base=base, route30=route30, full_w=full_w, paths=paths)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("root"); ap.add_argument("raw")
    ap.add_argument("--out"); ap.add_argument("--start"); ap.add_argument("--paths-csv")
    a = ap.parse_args()
    start = dt.date.fromisoformat(a.start) if a.start else None
    out = a.out or os.path.join(a.root, "01_Market_Foundations_and_Data/01.4_Supply_Demand_Balances",
                                "%s_Model_EU_Gas_Storage_Winter_Cases_Europe_Daily_v01.xlsx" % dt.date.today().strftime("%Y%m%d"))
    r = build(a.root, a.raw, out, start, a.paths_csv)
    print("start storage %.1f TWh (%.1f%%) on %s" % (r["s0"], 100 * r["s0"] / r["wgv"], r["last"]))
    print("normal call by half-month:", {HLABEL[k]: round(v, 2) for k, v in r["norm"].items()}, "non-heating", round(r["base"], 2))
    print("imports last 30d:", {k: round(v, 2) for k, v in r["route30"].items()}, "total", round(sum(r["route30"].values()), 2))
    for cs, p in r["paths"].items():
        e = p[-1]; print("%-6s 31 Mar %.1f%%  min %.1f%%  unmet %.1f TWh" % (cs, e["pct"], min(x["pct"] for x in p), sum(x["unmet"] for x in p)))
    print("wrote", out)
