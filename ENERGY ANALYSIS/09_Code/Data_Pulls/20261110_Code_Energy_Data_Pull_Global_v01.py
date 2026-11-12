"""Energy Analysis data pull: EIA API v2, FRED, CFTC, GIE AGSI+, Ember and OilPriceAPI (free / trial).

Reads API keys from environment variables EIA_API_KEY, FRED_API_KEY and GIE_API_KEY and OILPRICEAPI_KEY (both optional). Never put keys in this file:
the ENERGY ANALYSIS folder is mirrored to a public GitHub repository.

Usage:  python energy_data_pull.py <ENERGY ANALYSIS root> [YYYYMMDD]
Writes  raw CSVs  -> 01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/{EIA,Other_Sources}/API_<date>/
        section workbooks -> the section folders listed in CATALOG (one workbook per target).
Raw CSVs are written once per pull date and never edited afterwards.
"""
import csv, json, os, sys, time, urllib.request, urllib.parse, datetime as dt
from collections import defaultdict

EIA = os.environ.get("EIA_API_KEY", "").strip()
FRED = os.environ.get("FRED_API_KEY", "").strip()
GIE = "".join(os.environ.get("GIE_API_KEY", "").split())
OPA = "".join(os.environ.get("OILPRICEAPI_KEY", "").split())
START = {"D": "2024-01-01", "W": "2019-01-01", "M": "2015-01", "A": "2000", "Q": "2015-01-01"}

# (workbook key, sheet, label, unit, source, series id, frequency)
INTL = [("SAU","Saudi Arabia"),("RUS","Russia"),("USA","United States"),("CAN","Canada"),("IRQ","Iraq"),("IRN","Iran"),
        ("ARE","UAE"),("KWT","Kuwait"),("CHN","China"),("BRA","Brazil"),("NOR","Norway"),("QAT","Qatar"),("KAZ","Kazakhstan"),
        ("VEN","Venezuela"),("NGA","Nigeria"),("LBY","Libya"),("GUY","Guyana"),("MEX","Mexico"),("DZA","Algeria"),("OMN","Oman")]
CONS = [("USA","United States"),("CHN","China"),("IND","India"),("JPN","Japan"),("RUS","Russia"),("SAU","Saudi Arabia"),
        ("BRA","Brazil"),("KOR","South Korea"),("DEU","Germany"),("CAN","Canada"),("WORL","World")]
CATALOG = []
def add(wb, sheet, label, unit, src, sid, freq): CATALOG.append((wb, sheet, label, unit, src, sid, freq))

# 01.3 Macro (FRED)
for sid, l, u, f in [("GDPC1","US real GDP","bn chained 2017 $","Q"),("CPIAUCSL","US CPI, all items","index 1982-84=100","M"),
    ("CPIENGSL","US CPI, energy","index 1982-84=100","M"),("INDPRO","US industrial production","index 2017=100","M"),
    ("UNRATE","US unemployment rate","%","M"),("FEDFUNDS","Fed funds effective rate","%","M"),("DGS10","US 10-year Treasury yield","%","D"),
    ("T10YIE","US 10-year breakeven inflation","%","D"),("DTWEXBGS","Broad trade-weighted US dollar index","index Jan-2006=100","D")]:
    add("macro","Macro_US",l,u,"FRED",sid,f)
# 01.4 US weekly oil balance (EIA WPSR)
for sid, l, u in [("PET.WCRFPUS2.W","US crude oil field production","kb/d"),("PET.WCESTUS1.W","US commercial crude stocks (ex SPR)","kb"),
    ("PET.WCSSTUS1.W","US SPR stocks","kb"),("PET.W_EPC0_SAX_YCUOK_MBBL.W","Cushing crude stocks","kb"),
    ("PET.WGTSTUS1.W","US total gasoline stocks","kb"),("PET.WDISTUS1.W","US distillate stocks","kb"),
    ("PET.WCRIMUS2.W","US crude imports","kb/d"),("PET.WCREXUS2.W","US crude exports","kb/d"),("PET.WRPEXUS2.W","US product exports","kb/d"),
    ("PET.WRPUPUS2.W","US total product supplied (demand proxy)","kb/d"),("PET.WGFUPUS2.W","US gasoline product supplied","kb/d"),
    ("PET.WDIUPUS2.W","US distillate product supplied","kb/d"),("PET.WPULEUS3.W","US refinery utilisation","%"),
    ("PET.WGIRIUS2.W","US refinery gross inputs","kb/d"),("NG.NW2_EPG0_SWO_R48_BCF.W","US working gas in storage (Lower 48)","bcf")]:
    add("us_weekly","US_Weekly",l,u,"EIA",sid,"W")
# 02 / 05 International crude production and consumption (EIA international)
for c, n in INTL: add("intl","Crude_Production_Monthly",n,"kb/d","EIA international",f"INTL.57-1-{c}-TBPD.M","M")
for c, n in CONS: add("intl","Oil_Consumption_Annual",n,"kb/d","EIA international",f"INTL.5-2-{c}-TBPD.A","A")
# 03 Trade (EIA)
for c, n in [("CA","Canada"),("MX","Mexico"),("SA","Saudi Arabia"),("BR","Brazil"),("CO","Colombia"),("NI","Nigeria"),("EC","Ecuador")]:
    add("trade","US_Crude_Imports_by_Origin",n,"kb/d","EIA",f"PET.MCRIMUS{c}2.M","M")
add("trade","US_LNG","US LNG exports","MMcf/month","EIA","NG.N9133US2.M","M")
# 04 Power (EIA electricity)
for fu, n in [("ALL","All fuels"),("NG","Natural gas"),("COW","Coal"),("NUC","Nuclear"),("SUN","Solar (utility)"),("WND","Wind"),("HYC","Hydro (conventional)")]:
    add("power","US_Generation_by_Fuel",n,"GWh","EIA",f"ELEC.GEN.{fu}-US-99.M","M")
for s, n in [("ALL","All sectors"),("RES","Residential"),("COM","Commercial"),("IND","Industrial")]:
    add("power","US_Retail_Power_Price",n,"cents/kWh","EIA",f"ELEC.PRICE.US-{s}.M","M")
add("power","US_Retail_Sales","All sectors","GWh","EIA","ELEC.SALES.US-ALL.M","M")
# 04 Refining spot product prices (for cracks)
for sid, l, u in [("PET.RWTC.D","WTI Cushing spot","$/bbl"),("PET.RBRTE.D","Brent spot","$/bbl"),
    ("PET.EER_EPMRU_PF4_Y35NY_DPG.D","NY Harbor conventional gasoline spot","$/gal"),("PET.EER_EPD2DXL0_PF4_Y35NY_DPG.D","NY Harbor ULSD spot","$/gal"),
    ("PET.EER_EPJK_PF4_RGC_DPG.D","US Gulf Coast jet fuel spot","$/gal")]:
    add("refining","Spot_Prices_Daily",l,u,"EIA",sid,"D")
# 06 Emissions (EIA)
for s, n in [("TT","Total"),("EC","Electric power"),("TC","Transportation"),("IC","Industrial"),("RC","Residential"),("CC","Commercial")]:
    add("emissions","US_CO2_by_Sector",n,"Mt CO2","EIA",f"EMISS.CO2-TOTV-{s}-TO-US.A","A")
# 07 Prices (FRED / World Bank pink sheet via FRED)
for sid, l, u, f in [("DCOILBRENTEU","Brent spot","$/bbl","D"),("DCOILWTICO","WTI spot","$/bbl","D"),("DHHNGSP","Henry Hub spot","$/MMBtu","D"),
    ("PNGASEUUSDM","Europe natural gas (TTF-linked, IMF)","$/MMBtu","M"),("PNGASJPUSDM","Japan LNG import price (IMF)","$/MMBtu","M"),
    ("PCOALAUUSDM","Australian thermal coal (IMF)","$/t","M"),("PCOPPUSDM","Copper (IMF)","$/t","M"),("PURANUSDM","Uranium (IMF)","$/lb","M"),
    ("PNICKUSDM","Nickel (IMF)","$/t","M"),("POILBREUSDM","Brent monthly (IMF)","$/bbl","M"),("GASREGW","US retail regular gasoline","$/gal","W"),
    ("GASDESW","US retail diesel","$/gal","W"),("DJFUELUSGULF","US Gulf jet fuel","$/gal","D")]:
    add("prices","Prices_D" if f=="D" else ("Prices_W" if f=="W" else "Prices_M"),l,u,"FRED",sid,f)
COT = [("067651","WTI crude (NYMEX)"),("023651","Henry Hub natural gas (NYMEX)"),("111659","RBOB gasoline (NYMEX)"),("022651","NY Harbor ULSD (NYMEX)")]

def get(url, headers=None, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=headers or {"User-Agent": "energy-research-script"})
            with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode())
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(2 ** (i + 1))

def eia(sid, freq):
    out, off = [], 0
    while True:
        q = urllib.parse.urlencode({"api_key": EIA, "start": START[freq], "length": 5000, "offset": off})
        r = get(f"https://api.eia.gov/v2/seriesid/{sid}?{q}")["response"]
        rows = r.get("data") or []
        for x in rows:
            v = next((x[k] for k in ("value", "generation", "price", "sales") if k in x and x[k] not in (None, "")), None)
            try: out.append((str(x["period"]), float(v)))
            except (TypeError, ValueError): pass  # EIA uses '--' / 'NA' for missing
        off += len(rows)
        if not rows or off >= int(r.get("total") or 0): break
    return sorted(set(out))

def fred(sid, freq):
    q = urllib.parse.urlencode({"series_id": sid, "api_key": FRED, "file_type": "json", "observation_start": START[freq] if freq != "A" else "2000-01-01"})
    if freq == "M" or freq == "Q": q = q.replace(urllib.parse.quote(START[freq]), START[freq] + ("-01" if len(START[freq]) == 7 else ""))
    obs = get(f"https://api.stlouisfed.org/fred/series/observations?{q}")["observations"]
    return [(o["date"], float(o["value"])) for o in obs if o["value"] not in (".", "")]

def cot(code):
    q = urllib.parse.urlencode({"cftc_contract_market_code": code, "$where": "report_date_as_yyyy_mm_dd >= '2022-01-01'",
                                "$order": "report_date_as_yyyy_mm_dd", "$limit": 5000})
    return get(f"https://publicreporting.cftc.gov/resource/72hh-3qpy.json?{q}")

GIE_AREAS = [("eu", "EU"), ("DE", "Germany"), ("FR", "France"), ("IT", "Italy"), ("NL", "Netherlands"), ("AT", "Austria"), ("ES", "Spain"), ("PL", "Poland")]
GIE_FIELDS = ["gasDayStart", "gasInStorage", "workingGasVolume", "full", "trend", "injection", "withdrawal", "netWithdrawal", "consumptionFull", "status"]

def gie_pull(raw_dir, date, start="2021-01-01"):
    """EU gas storage from GIE AGSI+ (free key). Writes one raw CSV; returns rows written."""
    end = dt.date.today().isoformat(); n = 0
    with open(os.path.join(raw_dir, f"{date}_GIE_AGSI_Gas_Storage_Europe_Daily.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["area_code", "area"] + GIE_FIELDS)
        for code, name in GIE_AREAS:
            page, last = 1, 1
            while page <= last:
                q = (f"type=eu" if code == "eu" else f"country={code}") + f"&from={start}&to={end}&size=300&page={page}"
                r = get(f"https://agsi.gie.eu/api?{q}", headers={"x-key": GIE, "User-Agent": "energy-research-script"})
                last = int(r.get("last_page") or 1)
                for x in r.get("data", []): w.writerow([code, name] + [x.get(k, "") for k in GIE_FIELDS]); n += 1
                page += 1
    return n

# OilPriceAPI latest-price snapshot (key OILPRICEAPI_KEY; trial = 10,000 requests). (section, code)
OPA_CODES = [("Crude", c) for c in ["BRENT_CRUDE_USD", "BRENT_SPOT_USD", "WTI_USD", "WTI_SPOT_USD", "DUBAI_CRUDE_USD", "MURBAN_CRUDE_USD", "URALS_CRUDE_USD", "WCS_CRUDE_USD"]] + \
    [("Products", c) for c in ["GASOLINE_RBOB_USD", "HEATING_OIL_USD", "GASOIL_USD", "JET_FUEL_A4A_USD", "PROPANE_MONT_BELVIEU_USD", "ETHANOL_USD", "VLSFO_SGSIN_USD", "VLSFO_NLRTM_USD", "DIESEL_RETAIL_USD"]] + \
    [("Gas and LNG", c) for c in ["NATURAL_GAS_USD", "NATURAL_GAS_HENRY_HUB_SPOT_USD", "NATURAL_GAS_WAHA", "NATURAL_GAS_AECO_CAD", "DUTCH_TTF_EUR", "NATURAL_GAS_THE_EUR", "NATURAL_GAS_GBP", "JKM_LNG_USD", "LNG_NW_EUROPE_EUR"]] + \
    [("Power", c) for c in ["POWER_PJM_WEST_USD", "POWER_HOUSTON_USD", "POWER_SP15_USD", "POWER_MISO_ILLINOIS_USD", "SPARK_SPREAD_MID_ATLANTIC_USD", "SPARK_SPREAD_HOUSTON_USD"]] + \
    [("Coal, carbon, metals", c) for c in ["NEWCASTLE_COAL_USD", "COAL_USD", "EU_CARBON_EUR", "UK_CARBON_GBP", "COPPER_USD", "NICKEL_USD", "ALUMINUM_USD", "UREA_USD"]] + \
    [("Drilling and storage", c) for c in ["US_RIG_COUNT", "CANADA_RIG_COUNT", "INTERNATIONAL_RIG_COUNT", "US_FRAC_SPREAD_COUNT", "PERMIAN_DUC_WELLS", "CUSHING_STORAGE", "EU_GAS_STORAGE_FULL_PCT"]] + \
    [("Positioning", c) for c in ["CFTC_COT_BRENT_SPEC_NET", "CFTC_COT_WTI_SPEC_NET"]]

def opa_pull(raw_dir, date):
    n = 0
    with open(os.path.join(raw_dir, f"{date}_OilPriceAPI_Latest_Prices_Global_Daily.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["group", "code", "price", "currency", "unit", "type", "observed_at", "source_date", "data_status", "change_24h_pct", "error"])
        for grp, code in OPA_CODES:
            try:
                d = get(f"https://api.oilpriceapi.com/v1/prices/latest?by_code={code}", headers={"Authorization": f"Token {OPA}", "User-Agent": "energy-research-script"})["data"]
                ch = ((d.get("changes") or {}).get("24h") or {}).get("percent", "")
                w.writerow([grp, code, d.get("price"), d.get("currency"), d.get("unit"), d.get("type"), d.get("observed_at") or d.get("as_of") or d.get("created_at"),
                            d.get("source_date", ""), d.get("data_status", (d.get("freshness") or {}).get("status", "")), ch, ""]); n += 1
            except Exception as e:
                w.writerow([grp, code, "", "", "", "", "", "", "", "", str(e)[:80]])
    return n

def ember_pull(raw_dir, date):
    url = "https://files.ember-energy.org/public-downloads/generation/outputs/release_generation_yearly_global.csv"
    req = urllib.request.Request(url, headers={"User-Agent": "energy-research-script"})
    with urllib.request.urlopen(req, timeout=120) as r, open(os.path.join(raw_dir, f"{date}_Ember_Electricity_Generation_Global_Annual.csv"), "wb") as f:
        f.write(r.read())

# Global, every country: EIA international annual. (productId, unit) -> all activities, all countries/regions
EIA_INTL_BULK = [(57, "TBPD"), (53, "TBPD"), (5, "TBPD"), (26, "BCM"), (7, "MT"), (2, "BKWH"), (2, "MK"), (44, "QBTU"), (4008, "MMTCD")]

def eia_intl_bulk(raw_dir, date, start="2010"):
    n = 0
    with open(os.path.join(raw_dir, f"{date}_EIA_API_International_Annual_Global.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["productId", "product", "activityId", "activity", "unit", "countryRegionId", "countryRegion", "type", "year", "value"])
        for pid, unit in EIA_INTL_BULK:
            off = 0
            while True:
                q = f"api_key={EIA}&frequency=annual&data[]=value&facets[productId][]={pid}&facets[unit][]={unit}&start={start}&length=5000&offset={off}"
                r = get("https://api.eia.gov/v2/international/data/?" + q.replace("[", "%5B").replace("]", "%5D"))["response"]
                rows = r.get("data") or []
                for x in rows:
                    try: v = float(x["value"])
                    except (TypeError, ValueError): continue
                    w.writerow([pid, x["productName"], x["activityId"], x["activityName"], unit, x["countryRegionId"], x["countryRegionName"], x["countryRegionTypeName"], x["period"], v]); n += 1
                off += len(rows)
                if not rows or off >= int(r.get("total") or 0): break
    return n

JODI = {"oil_primary": "https://www.jodidata.org/_resources/files/downloads/oil-data/annual-csv/primary/{f}.csv",
        "oil_secondary": "https://www.jodidata.org/_resources/files/downloads/oil-data/annual-csv/secondary/{f}.csv"}

def jodi_pull(raw_dir, date, years=(2025, 2026)):
    for kind, url in JODI.items():
        for y in years:
            fname = f"{kind.split('_')[1]}year{y}" if y == dt.date.today().year else str(y)
            req = urllib.request.Request(url.format(f=fname), headers={"User-Agent": "energy-research-script"})
            with urllib.request.urlopen(req, timeout=300) as r, open(os.path.join(raw_dir, f"{date}_JODI_{kind.title().replace('_', '_')}_{y}_Global_Monthly.csv"), "wb") as f:
                f.write(r.read())

def ember_monthly_pull(raw_dir, date):
    url = "https://files.ember-energy.org/public-downloads/generation/outputs/release_generation_monthly_global.csv"
    req = urllib.request.Request(url, headers={"User-Agent": "energy-research-script"})
    with urllib.request.urlopen(req, timeout=300) as r, open(os.path.join(raw_dir, f"{date}_Ember_Electricity_Generation_Global_Monthly.csv"), "wb") as f:
        f.write(r.read())

# ---- Added 10 Nov 2026: ENTSOG, GIE ALSI, World Bank Pink Sheet, IMF ----
ENTSOG = "https://transparency.entsog.eu/api/v1/operationaldata"

def entsog_pull(raw_dir, date, start="2024-01-01", probe_day=None):
    """Daily physical flows at every EU import point (pipeline from non-EU) and every EU LNG entry point. No key."""
    import urllib.parse
    end = dt.date.today() - dt.timedelta(days=1)
    probe = probe_day or (end - dt.timedelta(days=7)).isoformat()
    day = get(ENTSOG + "?" + urllib.parse.urlencode({"from": probe, "to": probe, "indicator": "Physical Flow", "periodType": "day", "limit": -1}))["operationaldata"]
    sel = {}
    for r in day:
        pt = r.get("pointType") or ""
        if r["directionKey"] != "entry" or r["operatorKey"][:2] in ("UA", "UK"): continue
        if pt.startswith("Cross-Border Transmission IP between EU and Non-EU") or pt == "LNG Entry point":
            sel[r["operatorKey"] + r["pointKey"] + "entry"] = pt
    keys = list(sel); n = 0
    halves = []; a = dt.date.fromisoformat(start)
    while a <= end:
        b = min(dt.date(a.year, 6, 30) if a.month <= 6 else dt.date(a.year, 12, 31), end); halves.append((a, b)); a = b + dt.timedelta(days=1)
    with open(os.path.join(raw_dir, f"{date}_ENTSOG_Physical_Flows_EU_Import_Points_Europe_Daily.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["gas_day", "operator_key", "operator", "point_key", "point", "direction", "point_type", "unit", "value", "flow_status"])
        for a, b in halves:
            for i in range(0, len(keys), 40):
                q = urllib.parse.urlencode({"pointDirection": ",".join(keys[i:i + 40]), "from": a.isoformat(), "to": b.isoformat(), "indicator": "Physical Flow", "periodType": "day", "timezone": "CET", "limit": -1})
                for r in get(ENTSOG + "?" + q).get("operationaldata", []):
                    w.writerow([r["periodFrom"][:10], r["operatorKey"], r["operatorLabel"], r["pointKey"], r["pointLabel"], r["directionKey"], r.get("pointType") or sel.get(r["operatorKey"] + r["pointKey"] + "entry"), r["unit"], r["value"], r.get("flowStatus")]); n += 1
    return n

ALSI_AREAS = ["eu", "be", "de", "es", "fr", "gr", "hr", "it", "lt", "nl", "pl", "pt", "fi", "gb"]
def alsi_pull(raw_dir, date, start="2021-01-01"):
    """LNG terminal inventory and send-out from GIE ALSI (same key as AGSI+)."""
    end = dt.date.today().isoformat(); n = 0
    with open(os.path.join(raw_dir, f"{date}_GIE_ALSI_LNG_Terminals_Europe_Daily.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["gas_day", "area", "name", "inventory_lng_1000m3", "inventory_gwh", "send_out_gwh_d", "dtmi_lng_1000m3", "dtmi_gwh", "dtrs_gwh_d", "status"])
        for c in ALSI_AREAS:
            page, last = 1, 1
            while page <= last:
                q = ("type=eu" if c == "eu" else f"country={c}") + f"&from={start}&to={end}&size=300&page={page}"
                r = get(f"https://alsi.gie.eu/api?{q}", headers={"x-key": GIE, "User-Agent": "energy-research-script"})
                last = int(r.get("last_page") or 1)
                for x in r.get("data", []):
                    inv, dt_ = x.get("inventory") or {}, x.get("dtmi") or {}
                    w.writerow([x.get("gasDayStart"), c.upper(), x.get("name"), inv.get("lng"), inv.get("gwh"), x.get("sendOut"), dt_.get("lng"), dt_.get("gwh"), x.get("dtrs"), x.get("status")]); n += 1
                page += 1
    return n

# Gas-heating weather points for the EU: one city per country, weighted by approximate share of EU household and
# services gas use (assumption, editable in the storage model's Inputs sheet). Open-Meteo archive (ERA5), CC-BY 4.0, no key.
WX_POINTS = [("DE", "Kassel", 51.31, 9.48, 27), ("IT", "Milan", 45.46, 9.19, 19), ("FR", "Paris", 48.86, 2.35, 12), ("NL", "Utrecht", 52.09, 5.12, 8),
             ("PL", "Warsaw", 52.23, 21.01, 6), ("BE", "Brussels", 50.85, 4.35, 5), ("ES", "Madrid", 40.42, -3.70, 4), ("RO", "Bucharest", 44.43, 26.10, 4),
             ("HU", "Budapest", 47.50, 19.04, 4), ("AT", "Vienna", 48.21, 16.37, 3), ("CZ", "Prague", 50.08, 14.44, 3), ("SK", "Bratislava", 48.15, 17.11, 2)]
WX_START = "1990-07-01"

def openmeteo_pull(raw_dir, date, hist_csv):
    """Daily mean 2 m temperature (deg C) at the WX_POINTS from the Open-Meteo archive API.
    Keeps a rolling history file (hist_csv, one column per country). Only the last 60 days before its end are pulled again,
    because recent ERA5 days are revised; with no history file the whole record from WX_START is pulled.
    The pulled slice is also written to raw_dir unchanged."""
    hist = {}
    if os.path.exists(hist_csv):
        for r in csv.DictReader(open(hist_csv)): hist[r["date"]] = r
    start = WX_START if not hist else (dt.date.fromisoformat(max(hist)) - dt.timedelta(days=60)).isoformat()
    end = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    q = urllib.parse.urlencode(dict(latitude=",".join(str(p[2]) for p in WX_POINTS), longitude=",".join(str(p[3]) for p in WX_POINTS),
                                    start_date=start, end_date=end, daily="temperature_2m_mean", timezone="Europe/Berlin"))
    r = get("https://archive-api.open-meteo.com/v1/archive?" + q)
    r = r if isinstance(r, list) else [r]
    cols = [p[0] for p in WX_POINTS]
    new = {}
    for j, x in enumerate(r):
        for t, v in zip(x["daily"]["time"], x["daily"]["temperature_2m_mean"]):
            new.setdefault(t, {"date": t})[cols[j]] = "" if v is None else v
    with open(os.path.join(raw_dir, f"{date}_OpenMeteo_Temperature_EU_Gas_Points_Europe_Daily.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, ["date"] + cols); w.writeheader(); [w.writerow(new[t]) for t in sorted(new)]
    for t, row in new.items():
        if all(row.get(c, "") != "" for c in cols): hist[t] = row     # keep the old value until all points have the day
    os.makedirs(os.path.dirname(hist_csv), exist_ok=True)
    with open(hist_csv, "w", newline="") as f:
        w = csv.DictWriter(f, ["date"] + cols, extrasaction="ignore"); w.writeheader(); [w.writerow(hist[t]) for t in sorted(hist)]
    return len(new)

PINK_PAGE = "https://www.worldbank.org/en/research/commodity-markets"
def pink_pull(raw_dir, date):
    """World Bank Pink Sheet monthly prices workbook (CC-BY-4.0). Finds the current link on the commodity markets page."""
    import re
    req = urllib.request.Request(PINK_PAGE, headers={"User-Agent": "energy-research-script"})
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
    url = re.findall(r'https://thedocs\.worldbank\.org[^"]*CMO-Historical-Data-Monthly\.xlsx', html)[0]
    req = urllib.request.Request(url, headers={"User-Agent": "energy-research-script"})
    out = os.path.join(raw_dir, f"{date}_WorldBank_Pink_Sheet_Commodity_Prices_Global_Monthly.xlsx")
    open(out, "wb").write(urllib.request.urlopen(req, timeout=120).read())
    return url

IMF_DM = ["NGDP_RPCH", "PCPIPCH", "NGDPD", "LP"]   # real GDP growth %, CPI inflation %, GDP US$bn, population m (WEO)
IMF_PCPS = ["POILBRE", "POILWTI", "POILDUB", "PNGASEU", "PNGASUS", "PNGASJP", "PCOALAU", "PCOALSA", "PURAN", "PNRG", "PCOPP", "PNICK", "PALUM"]
def imf_pull(raw_dir, date):
    """IMF WEO country macro (DataMapper API) and IMF primary commodity prices (PCPS, SDMX 3.0). No key."""
    n = 0
    with open(os.path.join(raw_dir, f"{date}_IMF_WEO_Macro_by_Country_Global_Annual.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["indicator", "iso3", "year", "value"])
        for ind in IMF_DM:
            # The DataMapper API refuses urllib's request profile, so use the system curl (a standard API client).
            import subprocess
            vals = json.loads(subprocess.run(["curl", "-s", "-m", "60", f"https://www.imf.org/external/datamapper/api/v1/{ind}"], capture_output=True, check=True).stdout)["values"][ind]
            for iso, ys in vals.items():
                for y, v in ys.items(): w.writerow([ind, iso, y, v]); n += 1
    u = ("https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.RES/PCPS/+/G001." + "+".join(IMF_PCPS) +
         ".USD.M?dimensionAtObservation=TIME_PERIOD&attributes=dsd&measures=all")
    d = get(u, headers={"Accept": "application/json", "User-Agent": "energy-research-script"})["data"]
    dims = d["structures"][0]["dimensions"]; tv = [x["value"] for x in dims["observation"][0]["values"]]
    ind_ix = [x["id"] for x in dims["series"]].index("INDICATOR"); inds = [x["id"] for x in dims["series"][ind_ix]["values"]]
    with open(os.path.join(raw_dir, f"{date}_IMF_PCPS_Commodity_Prices_Global_Monthly.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["indicator", "period", "value_usd"])
        for k, s in d["dataSets"][0]["series"].items():
            ind = inds[int(k.split(":")[ind_ix])]
            for t, o in sorted(s["observations"].items(), key=lambda x: int(x[0])):
                if o[0] not in (None, ""): w.writerow([ind, tv[int(t)], o[0]]); n += 1
    return n
# ICE Futures Europe COT (Brent, gasoil, TTF) sits behind bot protection for scripts, so it is not pulled. CFTC covers NYMEX contracts.

def main(root, date):
    raw_eia = os.path.join(root, "01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/EIA", f"API_{date}")
    raw_oth = os.path.join(root, "01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/Other_Sources", f"API_{date}")
    os.makedirs(raw_eia, exist_ok=True); os.makedirs(raw_oth, exist_ok=True)
    data, meta, fails = {}, [], []
    for wb, sheet, label, unit, src, sid, freq in CATALOG:
        try:
            s = eia(sid, freq) if src.startswith("EIA") else fred(sid, freq)
            if not s: raise ValueError("no data")
            data[sid] = s; meta.append((wb, sheet, label, unit, src, sid, freq))
        except Exception as e:
            fails.append((sid, label, str(e)[:120]))
    groups = defaultdict(list)
    for m in meta: groups[(m[4].split()[0], m[0])].append(m)
    for (src, wb), ms in groups.items():
        d = raw_eia if src == "EIA" else raw_oth
        with open(os.path.join(d, f"{date}_{src}_API_{wb}_Global.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["series_id", "label", "unit", "frequency", "period", "value"])
            for m in ms:
                for p, v in data[m[5]]: w.writerow([m[5], m[2], m[3], m[6], p, v])
    cots = {}
    for code, name in COT:
        try:
            rows = cot(code); cots[code] = (name, rows)
        except Exception as e:
            fails.append((code, name, str(e)[:120]))
    if cots:
        keys = ["report_date_as_yyyy_mm_dd", "market_and_exchange_names", "open_interest_all", "prod_merc_positions_long", "prod_merc_positions_short",
                "swap_positions_long_all", "swap__positions_short_all", "m_money_positions_long_all", "m_money_positions_short_all",
                "other_rept_positions_long", "other_rept_positions_short", "nonrept_positions_long_all", "nonrept_positions_short_all"]
        with open(os.path.join(raw_oth, f"{date}_CFTC_COT_Disaggregated_Energy_US_Weekly.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["cftc_code"] + keys)
            for code, (name, rows) in cots.items():
                for r in rows: w.writerow([code] + [r.get(k, "") for k in keys])
    if GIE:
        try: gie_rows = gie_pull(raw_oth, date)
        except Exception as e: fails.append(("GIE", "EU gas storage", str(e)[:120]))
    if OPA:
        try: opa_pull(raw_oth, date)
        except Exception as e: fails.append(("OPA", "OilPriceAPI", str(e)[:120]))
    for fn, d, label in ((eia_intl_bulk, raw_eia, "EIA international bulk"), (jodi_pull, raw_oth, "JODI"), (ember_monthly_pull, raw_oth, "Ember monthly"), (entsog_pull, raw_oth, "ENTSOG EU import flows"), (pink_pull, raw_oth, "World Bank Pink Sheet"), (imf_pull, raw_oth, "IMF WEO and PCPS")) + (((alsi_pull, raw_oth, "GIE ALSI LNG terminals"),) if GIE else ()):
        try: fn(d, date)
        except Exception as e: fails.append((label, label, str(e)[:120]))
    try: ember_pull(raw_oth, date)
    except Exception as e: fails.append(("EMBER", "Ember yearly generation", str(e)[:120]))
    json.dump({"meta": meta, "fails": fails, "cot": {k: v[0] for k, v in cots.items()}}, open(os.path.join(raw_oth, f"{date}_pull_manifest.json"), "w"), indent=1)
    return data, meta, fails, cots

if __name__ == "__main__":
    if not EIA or not FRED: sys.exit("Set EIA_API_KEY and FRED_API_KEY in the environment.")
    root = sys.argv[1]; date = sys.argv[2] if len(sys.argv) > 2 else dt.date.today().strftime("%Y%m%d")
    data, meta, fails, cots = main(root, date)
    print(f"series ok: {len(meta)}; COT markets: {len(cots)}; failed: {len(fails)}")
    for f in fails: print("FAILED", f)
