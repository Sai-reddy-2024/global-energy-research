"""EU gas storage model: warm, normal and cold winter cases to 31 March, with live Excel formulas.

Usage:
    python3 20261110_Code_Build_EU_Gas_Storage_Model_Europe_v01.py <ENERGY ANALYSIS folder> <raw folder> [--out FILE] [--start YYYY-MM-DD] [--paths-csv FILE] [--temps FILE]

<raw folder> must hold one GIE AGSI+ storage file (*_GIE_AGSI_Gas_Storage_Europe_Daily.csv) and one ENTSOG flows file
(*_ENTSOG_Physical_Flows_EU_Import_Points_Europe_Daily.csv), as written by the data pull script or the GitHub Actions pull.
Temperatures come from the rolling Open-Meteo history in 01.6_Weather_and_Climate_Data (kept up to date by the pull script).

How the model works (all in formulas, so any blue input can be changed in Excel):
  call on storage  = EU consumption + net exports - EU production, measured in the data as imports + net storage withdrawal
  heating degree days (HDD) = gas-weighted average over 12 EU countries of (18 - mean temperature) on days at or below 15 C
  weather fit      = call = intercept + slope x HDD, fitted on October-April days since 2024 (Calibration sheet)
  normal call      = average of the last two winters by half-month, corrected to normal weather with the fitted slope
  normal weather   = trend of the last 30 winters' HDD (they are getting warmer), by half-month
  warm / cold      = 10th / 90th percentile of those winters around the trend (a 1-in-10 mild or cold winter)
  case call        = (normal call + slope x normal HDD x case HDD change) x (1 - demand response)
  supply           = pipeline and LNG imports by route (last 30 days, or your own level) + LNG case adjustment + Gulf LNG recovery ramp
  withdrawal       = call - supply, capped by what storage can deliver at that fill level; anything above the cap is unmet demand
The script also computes the same model in Python so it can write the case paths to CSV for the weekly note.
Keys: none needed. Sources: GIE AGSI+ (storage), ENTSOG Transparency Platform (flows), Open-Meteo archive (ERA5 temperatures, CC-BY 4.0).
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
PCTL = {"Warm": 0.10, "Cold": 0.90}                              # percentile of past winters' HDD around the trend (1-in-10)
WX = [("DE", "Kassel", 27), ("IT", "Milan", 19), ("FR", "Paris", 12), ("NL", "Utrecht", 8), ("PL", "Warsaw", 6), ("BE", "Brussels", 5),
      ("ES", "Madrid", 4), ("RO", "Bucharest", 4), ("HU", "Budapest", 4), ("AT", "Vienna", 3), ("CZ", "Prague", 3), ("SK", "Bratislava", 2)]
#     weights: approximate share of EU household and services gas use (assumption, rounded); same points as the pull script
HDD_BASE, HDD_THRESH = 18.0, 15.0                                # Eurostat convention: HDD = 18 - T when T <= 15 C, else 0
CLIM_LAST, CLIM_N = 2025, 30                                     # climate base: the 30 winters ending 2025-26
FIT_START = dt.date(2024, 1, 1)                                  # weather fit uses October-April days from here to the model start
FIT_MONTHS = (10, 11, 12, 1, 2, 3, 4)
TEMPS = "01_Market_Foundations_and_Data/01.6_Weather_and_Climate_Data/OpenMeteo_Temperature_EU_Gas_Points_Europe_Daily.csv"
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


def load_temps(path):
    out = {}
    for r in csv.DictReader(open(path)):
        v = [fnum(r.get(c)) for c, _, _ in WX]
        if all(x is not None for x in v): out[r["date"]] = v
    return out


def hdd_series(temps):
    W = sum(w for _, _, w in WX)
    return {d: sum(w * (HDD_BASE - t if t <= HDD_THRESH else 0) for (_, _, w), t in zip(WX, v)) / W for d, v in temps.items()}


def ols(xs, ys):
    mx, my = st.mean(xs), st.mean(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs); a = my - b * mx
    r2 = 1 - sum((y - a - b * x) ** 2 for x, y in zip(xs, ys)) / sum((y - my) ** 2 for y in ys)
    return a, b, r2


def pct_inc(xs, p):  # Excel PERCENTILE.INC
    xs = sorted(xs); k = (len(xs) - 1) * p; f = int(k)
    return xs[f] + (xs[min(f + 1, len(xs) - 1)] - xs[f]) * (k - f)


def weather(hdd, call, full_w, norm_obs, start, s0_day):
    """Python mirror of the Calibration sheet's weather block. Returns the fit, the climate and the weather-normal call."""
    fd = [d for d in sorted(call) if FIT_START.isoformat() <= d <= s0_day and d in hdd and int(d[5:7]) in FIT_MONTHS]
    a, b, r2 = ols([hdd[d] for d in fd], [call[d] for d in fd])
    y0 = start.year if start.month >= 7 else start.year - 1
    years = list(range(CLIM_LAST - CLIM_N + 1, CLIM_LAST + 1))
    def total(y):
        d0, d1 = dt.date(y, start.month, start.day), dt.date(y + 1, END.month, END.day)
        return sum(hdd[(d0 + dt.timedelta(days=i)).isoformat()] for i in range((d1 - d0).days + 1))
    tots = [total(y) for y in years]
    _, slope_t, _ = ols(years, tots); icpt_t = st.mean(tots) - slope_t * st.mean(years)
    trend = icpt_t + slope_t * y0
    res = [t - (icpt_t + slope_t * y) for y, t in zip(years, tots)]
    case_hdd = {"Warm": trend + pct_inc(res, PCTL["Warm"]), "Normal": trend, "Cold": trend + pct_inc(res, PCTL["Cold"])}
    adj = {cs: case_hdd[cs] / trend - 1 for cs in CASES}
    scale = trend / st.mean(tots)
    nhdd, obs_hdd, norm = {}, {}, {}
    for m, h in HALVES:
        k = m * 10 + h
        nhdd[k] = st.mean([v for d, v in hdd.items() if half(dt.date.fromisoformat(d)) == k and years[0] <= int(winter_of(dt.date.fromisoformat(d))[:4]) <= years[-1]]) * scale
        obs_hdd[k] = st.mean([st.mean([v for d, v in hdd.items() if half(dt.date.fromisoformat(d)) == k and winter_of(dt.date.fromisoformat(d)) == w]) for w in full_w])
        norm[k] = norm_obs[k] + b * (nhdd[k] - obs_hdd[k])
    return dict(a=a, b=b, r2=r2, n=len(fd), years=years, tots=tots, trend=trend, case_hdd=case_hdd, adj=adj, scale=scale,
                nhdd=nhdd, obs_hdd=obs_hdd, norm=norm, y0=y0)


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


def run_case(case, start, s0, wgv, norm, wx, route30, gulf=GULF):
    rows, s = [], s0
    d = start
    while d <= END:
        k = half(d)
        c = (norm[k] + wx["b"] * wx["nhdd"][k] * wx["adj"][case]) * (1 - DEMAND_RESP[case])
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


def build(root, raw, out, start=None, paths_csv=None, temps=None):
    stor, flows = load(raw)
    temps = load_temps(temps or os.path.join(root, TEMPS)); hdd = hdd_series(temps)
    last = max(d for d in stor if d in flows)
    start = start or (dt.date.fromisoformat(last) + dt.timedelta(days=1))
    s0_day = (start - dt.timedelta(days=1)).isoformat()
    s0, wgv = stor[s0_day]["twh"], stor[s0_day]["wgv"]
    call, full_w, norm_obs, base, summer_years, route30 = calibrate(stor, flows, s0_day)
    wx = weather(hdd, call, full_w, norm_obs, start, s0_day); norm = wx["norm"]

    wb = openpyxl.Workbook(); wb.remove(wb.active)
    rd = wb.create_sheet("README"); inp = wb.create_sheet("Inputs"); summ = wb.create_sheet("Summary")
    mod = wb.create_sheet("Model_Daily"); cal = wb.create_sheet("Calibration"); dat = wb.create_sheet("Data_Daily"); wxs = wb.create_sheet("Weather_Daily")

    # ---- Weather_Daily: temperatures (values, Open-Meteo) and gas-weighted HDD (formula, weights in Inputs)
    wdays = sorted(d for d in temps if d >= "1995-07-01")
    hdr(wxs, 1, ["Date"] + ["%s %s (C)" % (c, city) for c, city, _ in WX] + ["Gas-weighted HDD", "Half-month key", "Winter start year"], [11] + [8] * len(WX) + [9, 7, 8])
    tc0, tc1 = L(2), L(1 + len(WX)); hc = L(2 + len(WX))
    for i, d in enumerate(wdays, 2):
        wxs.append([dt.date.fromisoformat(d)] + temps[d] + ["=SUMPRODUCT((%s%d:%s%d<=HDDThreshold)*(HDDBase-%s%d:%s%d),HDDWeights)/SUM(HDDWeights)" % (tc0, i, tc1, i, tc0, i, tc1, i),
                                                            "=MONTH(A%d)*10+IF(DAY(A%d)<=15,1,2)" % (i, i), "=IF(MONTH(A%d)>=7,YEAR(A%d),YEAR(A%d)-1)" % (i, i, i)])
        wxs.cell(i, 1).number_format = "yyyy-mm-dd"; wxs.cell(i, 2 + len(WX)).number_format = "0.00"
    wxs.freeze_panes = "B2"
    wn = len(wdays) + 1
    WC = {k: "Weather_Daily!$%s$2:$%s$%d" % (c, c, wn) for k, c in [("date", "A"), ("hdd", hc), ("key", L(3 + len(WX))), ("wy", L(4 + len(WX)))]}

    # ---- Data_Daily: one row per gas day since 2024 (values from the raw files)
    days = sorted(d for d in stor if d >= "2021-01-01")
    hdr(dat, 1, ["Gas day", "Storage (TWh)", "Working gas volume (TWh)", "Full %", "Injection (TWh/d)", "Withdrawal (TWh/d)"] + ["%s (TWh/d)" % r for r in ROUTES] +
        ["Total imports (TWh/d)", "Call on imports and storage (TWh/d)", "Half-month key", "Winter", "Month", "Gas-weighted HDD", "Fit: HDD", "Fit: call"],
        [11, 10, 10, 8, 9, 9] + [9] * len(ROUTES) + [10, 12, 8, 9, 7, 9, 8, 8])
    cc, hcol = L(8 + len(ROUTES)), L(12 + len(ROUTES))
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
        fit = "AND(ISNUMBER({c}{i}),ISNUMBER({h}{i}),A{i}>=FitStart,A{i}<StartDate,OR(MONTH(A{i})>=10,MONTH(A{i})<=4))".format(c=cc, h=hcol, i=i)
        row += ['=IFERROR(INDEX(%s,MATCH(A%d,%s,0)),"")' % (WC["hdd"], i, WC["date"]), '=IF(%s,%s%d,"")' % (fit, hcol, i), '=IF(%s,%s%d,"")' % (fit, cc, i)]
        dat.append(row); dat.cell(i, 1).number_format = "yyyy-mm-dd"
    n = len(days) + 1
    dat.freeze_panes = "B2"
    C = {k: "Data_Daily!$%s$2:$%s$%d" % (L(j), L(j), n) for k, j in
         [("date", 1), ("twh", 2), ("full", 4), ("call", 8 + len(ROUTES)), ("key", 9 + len(ROUTES)), ("winter", 10 + len(ROUTES)), ("month", 11 + len(ROUTES)),
          ("hdd", 12 + len(ROUTES)), ("fitx", 13 + len(ROUTES)), ("fity", 14 + len(ROUTES))]}
    for j, r in enumerate(ROUTES):
        C[r] = "Data_Daily!$%s$2:$%s$%d" % (L(7 + j), L(7 + j), n)

    # ---- Calibration: half-month table (rows 2-11), weather fit (13-19), winter HDD climate (21-52), results (54-61)
    hdr(cal, 1, ["Half-month", "Key"] + ["Call %s (TWh/d)" % w for w in full_w] + ["HDD %s (per day)" % w for w in full_w] +
        ["Normal HDD (per day)", "Normal call (TWh/d)", "Heating part of normal call (TWh/d)"], [14, 6, 12, 12, 12, 12, 12, 13, 13])
    for i, (m, h) in enumerate(HALVES, 2):
        k = m * 10 + h
        cal.cell(i, 1, HLABEL[k]); cal.cell(i, 2, k)
        for j, w in enumerate(full_w):
            cal.cell(i, 3 + j, '=AVERAGEIFS(%s,%s,B%d,%s,"%s")' % (C["call"], C["key"], i, C["winter"], w)).number_format = "0.00"
            cal.cell(i, 5 + j, '=AVERAGEIFS(%s,%s,B%d,%s,"%s")' % (C["hdd"], C["key"], i, C["winter"], w)).number_format = "0.00"
        cal.cell(i, 7, "=AVERAGEIFS(%s,%s,B%d,%s,\">=\"&ClimFirst,%s,\"<=\"&ClimLast)*HDDTrendScale" % (WC["hdd"], WC["key"], i, WC["wy"], WC["wy"])).number_format = "0.00"
        cal.cell(i, 8, "=AVERAGE(C%d:D%d)+HeatSlope*(G%d-AVERAGE(E%d:F%d))" % (i, i, i, i, i)).number_format = "0.00"
        cal.cell(i, 9, "=HeatSlope*G%d" % i).number_format = "0.00"
    hdr(cal, 13, ["Weather fit: call = intercept + slope x HDD", "", "Value", "", "", "", "", "", ""])
    fit_rows = [("Days in the fit (October-April, from FitStart to the model start)", "=COUNT(%s)" % C["fitx"], "0", None),
                ("Intercept (TWh/d)", "=INTERCEPT(%s,%s)" % (C["fity"], C["fitx"]), "0.00", "HeatIntercept"),
                ("Slope (TWh/d per HDD)", "=SLOPE(%s,%s)" % (C["fity"], C["fitx"]), "0.000", "HeatSlope"),
                ("R squared", "=RSQ(%s,%s)" % (C["fity"], C["fitx"]), "0.00", None),
                ("Check: summer call, June-August %s (TWh/d)" % " and ".join(summer_years), None, "0.00", "NonHeatingCall"),
                ("Check: summer call minus intercept (should be small)", "=C18-C15", "0.00", None)]
    for i, (lab, fml, fmt, nm) in enumerate(fit_rows, 14):
        cal.cell(i, 1, lab)
        if fml: cal.cell(i, 3, fml).number_format = fmt
        if nm: name(wb, nm, "Calibration!$C$%d" % i)
    yrs = summer_years
    cal.cell(18, 3, "=(AVERAGEIFS(%s,%s,\">=6\",%s,\"<=8\",%s,\">=\"&DATE(%s,1,1),%s,\"<\"&DATE(%s,1,1)))" % (C["call"], C["month"], C["month"], C["date"], yrs[0], C["date"], int(yrs[-1]) + 1)).number_format = "0.00"
    hdr(cal, 21, ["Winter (model window: start day to 31 Mar)", "Start year", "Total HDD", "Trend", "Above trend", "", "", "", ""])
    r0 = 22
    for j in range(CLIM_N):
        i = r0 + j
        cal.cell(i, 2, "=ClimLast-%d" % (CLIM_N - 1 - j))
        cal.cell(i, 1, '=B%d&"-"&RIGHT(B%d+1,2)' % (i, i))
        cal.cell(i, 3, "=SUMIFS(%s,%s,\">=\"&DATE(B%d,MONTH(StartDate),DAY(StartDate)),%s,\"<=\"&DATE(B%d+1,MONTH(EndDate),DAY(EndDate)))" % (WC["hdd"], WC["date"], i, WC["date"], i)).number_format = "0"
        cal.cell(i, 4, "=TREND($C$%d:$C$%d,$B$%d:$B$%d,B%d)" % (r0, r0 + CLIM_N - 1, r0, r0 + CLIM_N - 1, i)).number_format = "0"
        cal.cell(i, 5, "=C%d-D%d" % (i, i)).number_format = "0"
    rl = r0 + CLIM_N - 1; rs = rl + 2
    hdr(cal, rs, ["Weather cases for this winter", "", "HDD", "vs normal", "", "", "", "", ""])
    rows = [("This winter (start year)", "=IF(MONTH(StartDate)>=7,YEAR(StartDate),YEAR(StartDate)-1)", "0", None, "ThisWinter"),
            ("Normal: trend value for this winter", "=TREND($C$%d:$C$%d,$B$%d:$B$%d,ThisWinter)" % (r0, rl, r0, rl), "0", "=0", "HDDNormal"),
            ("Warm: trend + Warm percentile of 'above trend'", "=HDDNormal+PERCENTILE($E$%d:$E$%d,Pctl_Warm)" % (r0, rl), "0", "=C%d/HDDNormal-1", "HDDWarm"),
            ("Cold: trend + Cold percentile of 'above trend'", "=HDDNormal+PERCENTILE($E$%d:$E$%d,Pctl_Cold)" % (r0, rl), "0", "=C%d/HDDNormal-1", "HDDCold"),
            ("Average of the 30 winters", "=AVERAGE($C$%d:$C$%d)" % (r0, rl), "0", "=C%d/HDDNormal-1", None),
            ("Trend scale applied to half-month normals", "=HDDNormal/C%d" % (rs + 5), "0.000", None, "HDDTrendScale"),
            ("Trend change per year (HDD)", "=SLOPE($C$%d:$C$%d,$B$%d:$B$%d)" % (r0, rl, r0, rl), "0.0", None, None)]
    for i, (lab, fml, fmt, vs, nm) in enumerate(rows, rs + 1):
        cal.cell(i, 1, lab); cal.cell(i, 3, fml).number_format = fmt
        if vs: cal.cell(i, 4, vs.replace("%d", str(i)) if "%d" in vs else vs).number_format = "+0.0%;-0.0%;0.0%"
        if nm: name(wb, nm, "Calibration!$C$%d" % i)
    for cs, rr in (("Normal", rs + 2), ("Warm", rs + 3), ("Cold", rs + 4)): name(wb, "Weather_%s" % cs, "Calibration!$D$%d" % rr)
    notes = ["The call on imports and storage = EU consumption + net exports to non-EU neighbours - EU production. It is measured as imports (ENTSOG) + net withdrawal from storage (GIE AGSI+).",
             "HDD: gas-weighted average of 12 EU countries (one city each, weights in Inputs) of (18 - daily mean temperature) on days at or below 15 C. Temperatures: Open-Meteo archive (ERA5), CC-BY 4.0.",
             "Normal call = the average of the last two complete winters (%s) by half-month, moved to normal weather: + slope x (normal HDD - HDD in those winters)." % " and ".join(full_w),
             "Normal weather = the 30-winter trend for this winter (winters are getting milder), spread over half-months in the 30-winter average pattern.",
             "Warm and cold = the 10th and 90th percentile of the 30 winters around the trend: roughly a 1-in-10 mild or cold winter.",
             "Limitations: the fit rests on two winters of flow data (ENTSOG pull starts 2024); one city per country; it ignores wind and the lag between temperature and demand."]
    for i, t in enumerate(notes, rs + 10): cal.cell(i, 1, t).font = NOTE

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
    inp.cell(r + 1, 1, "Weather: percentile of past winters (HDD)")
    for j, cs in enumerate(CASES):
        if cs == "Normal": inp.cell(r + 1, 3, "trend")
        else:
            c = inp.cell(r + 1, 2 + j, PCTL[cs]); c.font = BLUE; c.fill = INFILL; c.number_format = "0%"; name(wb, "Pctl_%s" % cs, "Inputs!$%s$%d" % (L(2 + j), r + 1))
    inp.cell(r + 1, 6, "10% and 90% = a 1-in-10 mild or cold winter, measured around the 30-winter trend (Calibration).").font = NOTE
    inp.cell(r + 2, 1, "Heating degree days vs normal (result)")
    for j, cs in enumerate(CASES): inp.cell(r + 2, 2 + j, "=Weather_%s" % cs).number_format = "+0.0%;-0.0%;0.0%"
    inp.cell(r + 2, 6, "Formula. Scales the weather-driven part of the call (slope x normal HDD).").font = NOTE
    for i, (lab, d, nm, fmt, note) in enumerate([
            ("Extra demand cut from high prices (share of call)", DEMAND_RESP, "DemandCut", "0.0%", "0 means demand behaves as in the last two winters. Each 1% is about 1.6 TWh over the winter per TWh/d of call."),
            ("LNG send-out adjustment (TWh/d)", LNG_ADJ, "LNGAdj", "0.00", "Judgement: a cold Europe usually means a cold Northeast Asia bidding for the same cargoes.")], r + 3):
        inp.cell(i, 1, lab)
        for j, cs in enumerate(CASES):
            c = inp.cell(i, 2 + j, d[cs]); c.font = BLUE; c.fill = INFILL; c.number_format = fmt
            name(wb, "%s_%s" % (nm, cs), "Inputs!$%s$%d" % (L(2 + j), i))
        inp.cell(i, 6, note).font = NOTE
    r = 16
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
    r += 6
    hdr(inp, r, ["Weather", "Value", "", "", "", "Note"])
    put(r + 1, "Last winter of the 30-winter climate base (start year)", CLIM_LAST, "ClimLast", "0", "2025 = winter 2025-26. The base is the 30 winters ending there.")
    inp.cell(r + 2, 1, "First winter of the climate base"); inp.cell(r + 2, 2, "=ClimLast-%d" % (CLIM_N - 1)); name(wb, "ClimFirst", "Inputs!$B$%d" % (r + 2))
    put(r + 3, "Weather fit starts", FIT_START, "FitStart", "yyyy-mm-dd", "October-April days from here to the model start (ENTSOG flows start 2024-01-01).")
    put(r + 4, "HDD base temperature (C)", HDD_BASE, "HDDBase", "0.0", "Eurostat convention.")
    put(r + 5, "HDD threshold (C): no heating above", HDD_THRESH, "HDDThreshold", "0.0", "Eurostat convention.")
    r += 7
    inp.cell(r, 1, "Weights by country (share of EU household and services gas use)").font = BOLD
    for j, (c, city, w) in enumerate(WX):
        inp.column_dimensions[L(2 + j)].width = max(inp.column_dimensions[L(2 + j)].width or 0, 9)
        inp.cell(r + 1, 2 + j, c).font = BOLD; inp.cell(r + 2, 2 + j, city)
        x = inp.cell(r + 3, 2 + j, w); x.font = BLUE; x.fill = INFILL
    inp.cell(r + 1, 1, "Country"); inp.cell(r + 2, 1, "Temperature point"); inp.cell(r + 3, 1, "Weight (approximate %, assumption)")
    name(wb, "HDDWeights", "Inputs!$B$%d:$%s$%d" % (r + 3, L(1 + len(WX)), r + 3))
    inp.cell(r + 4, 1, "Rounded shares of EU household and services gas use (Eurostat energy balances, approximate). Only relative sizes matter.").font = NOTE

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
        mod.cell(i, 3, "=INDEX(Calibration!$H$2:$H$11,MATCH(B%d,Calibration!$B$2:$B$11,0))" % i).number_format = "0.00"
        mod.cell(i, 4, "=IF(A%d<GulfStart,0,MIN(1,(A%d-GulfStart)/MAX(1,GulfFull-GulfStart)))" % (i, i)).number_format = "0.00"
        for k, cs in enumerate(CASES):
            c0 = 5 + 8 * k; col = {s: L(c0 + j) for j, s in enumerate(sub)}
            prev = "StartTWh" if i == 2 else "%s%d" % (col["Storage TWh"], i - 1)
            f = {
                "Call": "=(C{i}+INDEX(Calibration!$I$2:$I$11,MATCH(B{i},Calibration!$B$2:$B$11,0))*Weather_{cs})*(1-DemandCut_{cs})",
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
            "Warm and cold change only the weather (a 1-in-10 mild or cold winter by heating degree days) and the LNG Europe can attract; imports by route and the Gulf recovery are the same in all three.",
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
            "Normal call = average of the last two full winters by half-month, corrected to normal weather with the fitted demand-temperature slope (Calibration).",
            "Weather cases: 1-in-10 mild or cold winters by gas-weighted heating degree days, around the 30-winter trend (Open-Meteo temperatures, Weather_Daily).",
            "Actual full % fills in automatically as new data is pulled; 'Actual minus Normal' shows how far reality is running from the normal case.",
            "",
            "Units: TWh (gross calorific value) as reported by GIE; 1 bcm = 10.55 TWh. Storage % = gas in storage / working gas volume.",
            "Sources: GIE AGSI+ (agsi.gie.eu), ENTSOG Transparency Platform (transparency.entsog.eu) and Open-Meteo (open-meteo.com, ERA5, CC-BY 4.0), all free. Not investment advice."], 1):
        rd.cell(i, 1, t).font = Font(bold=True, size=13) if i == 1 else Font()
    wb.calculation.fullCalcOnLoad = True
    wb.save(out)

    # ---- Python mirror for the paths CSV
    paths = {cs: run_case(cs, start, s0, wgv, norm, wx, route30) for cs in CASES}
    if paths_csv:
        with open(paths_csv, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["vintage", "gas_day"] + ["%s_full_pct" % cs.lower() for cs in CASES] + ["%s_unmet_twh" % cs.lower() for cs in CASES])
            for i in range(len(paths["Normal"])):
                w.writerow([s0_day, paths["Normal"][i]["date"].isoformat()] + [round(paths[cs][i]["pct"], 2) for cs in CASES] + [round(paths[cs][i]["unmet"], 3) for cs in CASES])
    return dict(last=s0_day, s0=s0, wgv=wgv, norm=norm, base=base, route30=route30, full_w=full_w, paths=paths, wx=wx)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("root"); ap.add_argument("raw")
    ap.add_argument("--out"); ap.add_argument("--start"); ap.add_argument("--paths-csv"); ap.add_argument("--temps")
    a = ap.parse_args()
    start = dt.date.fromisoformat(a.start) if a.start else None
    out = a.out or os.path.join(a.root, "01_Market_Foundations_and_Data/01.4_Supply_Demand_Balances",
                                "%s_Model_EU_Gas_Storage_Winter_Cases_Europe_Daily_v01.xlsx" % dt.date.today().strftime("%Y%m%d"))
    r = build(a.root, a.raw, out, start, a.paths_csv, a.temps)
    print("start storage %.1f TWh (%.1f%%) on %s" % (r["s0"], 100 * r["s0"] / r["wgv"], r["last"]))
    print("normal call by half-month:", {HLABEL[k]: round(v, 2) for k, v in r["norm"].items()}, "summer call", round(r["base"], 2))
    w = r["wx"]; print("weather fit: call = %.2f + %.3f x HDD (R2 %.2f, %d days); HDD normal %.0f, warm %.0f (%+.1f%%), cold %.0f (%+.1f%%)" % (
        w["a"], w["b"], w["r2"], w["n"], w["trend"], w["case_hdd"]["Warm"], 100 * w["adj"]["Warm"], w["case_hdd"]["Cold"], 100 * w["adj"]["Cold"]))
    print("imports last 30d:", {k: round(v, 2) for k, v in r["route30"].items()}, "total", round(sum(r["route30"].values()), 2))
    for cs, p in r["paths"].items():
        e = p[-1]; print("%-6s 31 Mar %.1f%%  min %.1f%%  unmet %.1f TWh" % (cs, e["pct"], min(x["pct"] for x in p), sum(x["unmet"] for x in p)))
    print("wrote", out)
