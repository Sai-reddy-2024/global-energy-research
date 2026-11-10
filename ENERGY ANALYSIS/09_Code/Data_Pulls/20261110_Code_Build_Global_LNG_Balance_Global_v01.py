"""Global LNG balance, annual 2024-2027 and quarterly 2026-2027, with live Excel formulas.

Usage:
    python3 20261110_Code_Build_Global_LNG_Balance_Global_v01.py <raw folder> --out FILE

<raw folder> must hold the GIE ALSI file (*_GIE_ALSI_LNG_Terminals_Europe_Daily.csv); EU send-out from it sets Europe's 2026 imports.
The question the balance answers: Qatar and the UAE lost most of their exports after Hormuz closed (28 Feb 2026),
so who gave up the missing cargoes? Supply is built bottom-up by exporter; named importers come from published estimates;
'Other importers' is the residual, so it shows how much the price-sensitive buyers (South and Southeast Asia, Middle East, Latin America) gave up.
Figures for 2025 are IGU World LNG Report 2026 (Rystad data). 2026-2027 are assumptions (blue cells), each with a source or a stated judgement.
"""
import argparse, csv, glob, os, datetime as dt
from collections import defaultdict
import openpyxl
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter as L

BLUE = Font(color="0000CC"); BOLD = Font(bold=True); HDR = PatternFill("solid", fgColor="1F4E78"); HFONT = Font(bold=True, color="FFFFFF")
INFILL = PatternFill("solid", fgColor="FFF2CC"); NOTE = Font(italic=True, color="555555")
TWH_PER_MT = 14.4   # 1 Mt LNG ~ 1.36 bcm ~ 14.4 TWh (GCV, 10.55 TWh/bcm); Reference_Tables

# exporter: (2025 actual Mt, 2026E, 2027E, note). None = formula from the Qatar_Monthly sheet.
EXPORTERS = [
    ("United States", 110.74, 129.0, 142.0, "2025 IGU. 2026: Plaquemines at full rate, Corpus Christi Stage 3 trains and Golden Pass train 1 (first cargo Apr 2026). 2027: Golden Pass trains 2-3. Judgement."),
    ("Qatar", 81.51, None, None, "From Qatar_Monthly: pre-war rate x undamaged capacity x utilisation by month."),
    ("Australia", 80.32, 79.0, 78.0, "2025 IGU. Gradual decline of older fields (judgement)."),
    ("Russia", 30.52, 31.0, 31.0, "2025 IGU. Sanctions cap growth (judgement)."),
    ("Malaysia", 28.80, 29.0, 29.0, "2025 IGU."),
    ("Canada", 2.10, 9.0, 13.0, "2025 IGU (LNG Canada first cargo Jun 2025, 14 Mtpa). Ramp-up (judgement)."),
    ("Mexico", 0.0, 1.5, 3.0, "Energia Costa Azul start-up (judgement)."),
    ("UAE", 5.60, None, None, "2025 approximate (Das Island, ~5.6 Mt; Claude estimate, to verify). Same Hormuz utilisation as Qatar."),
]
IMPORTERS = [
    ("Europe (incl. UK and Turkey)", 126.45, None, 130.0, "2025: IGU 126.2-126.7 Mt (average used). 2026: scaled by EU send-out (GIE ALSI). 2027: judgement, a low end-March refill keeps Europe bidding."),
    ("China", 69.77, 61.5, 74.0, "2025 IGU. 2026: ICIS 61 Mt, Kpler 62 Mt (Nov 2026). 2027: recovery as prices ease (judgement)."),
    ("Japan", 67.37, 62.5, 65.0, "2025 IGU. 2026: ICIS 62 Mt, Kpler 63 Mt (Nov 2026)."),
    ("South Korea", 48.67, 47.0, 49.0, "2025 IGU. 2026: no published estimate found; -3% assumed (judgement)."),
    ("India", 24.60, 22.0, 28.0, "2025 IGU. 2026: Sept imports -11% y/y (Kpler), -10% assumed for the year."),
]
TOTAL_2025 = 436.98
# Qatar export utilisation of undamaged capacity, by month (share). Calibrated so that Qatar + UAE lost ~36 Mt to mid-Sep 2026 (Shell, via The National).
UTIL = {"2026-01": 1, "2026-02": 1, "2026-03": 0.2, "2026-04": 0.08, "2026-05": 0.08, "2026-06": 0.08, "2026-07": 0.08, "2026-08": 0.01,
        "2026-09": 0.10, "2026-10": 0.30, "2026-11": 0.60, "2026-12": 0.70}
for m in range(1, 13): UTIL["2027-%02d" % m] = 0.8 if m <= 3 else (0.9 if m <= 6 else 0.95)


def hdr(ws, row, vals, widths=None):
    for i, v in enumerate(vals, 1):
        c = ws.cell(row, i, v); c.font = HFONT; c.fill = HDR; c.alignment = Alignment(wrap_text=True, vertical="top")
    if widths:
        for i, w in enumerate(widths, 1): ws.column_dimensions[L(i)].width = w


def blue(c, fmt="0.0"):
    c.font = BLUE; c.fill = INFILL; c.number_format = fmt


def alsi_monthly(raw):
    f = glob.glob(os.path.join(raw, "*_GIE_ALSI_LNG_Terminals_Europe_Daily.csv"))[0]
    m = defaultdict(float); last = ""
    for r in csv.DictReader(open(f)):
        if r["area"] != "EU": continue
        try: v = float(r["send_out_gwh_d"])
        except (TypeError, ValueError): continue
        m[r["gas_day"][:7]] += v / 1000; last = max(last, r["gas_day"])
    return m, last


def build(raw, out):
    send, last = alsi_monthly(raw)
    wb = openpyxl.Workbook(); wb.remove(wb.active)
    rd, ann, qtr, qm, eu = (wb.create_sheet(n) for n in ["README", "Annual_Balance", "Quarterly_Balance", "Qatar_Monthly", "EU_LNG_SendOut"])

    # ---- EU send-out (data)
    hdr(eu, 1, ["Month", "EU LNG send-out (TWh)", "Days with data", "Note"], [9, 14, 9, 60])
    months = sorted(k for k in send if k >= "2024-01")
    for i, mth in enumerate(months, 2):
        eu.cell(i, 1, mth); eu.cell(i, 2, round(send[mth], 1))
        eu.cell(i, 3, (dt.date.fromisoformat(last).day if mth == last[:7] else None))
    eu.cell(2, 4, "Source: GIE ALSI, EU total send-out (regasified LNG into the grid). Latest month is partial to %s." % last).font = NOTE
    ne = len(months) + 1
    SM = "EU_LNG_SendOut!$A$2:$A$%d" % ne; SV = "EU_LNG_SendOut!$B$2:$B$%d" % ne

    # ---- Qatar monthly
    hdr(qm, 1, ["Month", "Pre-war export rate (Mt/month)", "Share of capacity undamaged", "Utilisation (blue)", "Qatar exports (Mt)", "UAE exports (Mt)", "Quarter"], [9, 12, 12, 11, 11, 11, 9])
    qm["I1"] = "Inputs"; qm["I1"].font = BOLD
    qm["I2"] = "Pre-war Qatari exports (Mt/month)"; qm["J2"] = 6.51; blue(qm["J2"], "0.00")
    qm["K2"] = "Kpler average for the three months to end-Feb 2026 (via Reuters, 16 Sep 2026)"
    qm["I3"] = "Damaged capacity (Mtpa)"; qm["J3"] = 12.8; blue(qm["J3"])
    qm["K3"] = "Two of 14 trains hit at Ras Laffan on 18 Mar 2026; 3-5 years to repair (The National, 14 Sep 2026)"
    qm["I4"] = "Qatar nameplate (Mtpa)"; qm["J4"] = 77; blue(qm["J4"], "0")
    qm["I5"] = "UAE pre-war exports (Mt/yr)"; qm["J5"] = 5.6; blue(qm["J5"])
    qm["I6"] = "Damage effective from"; qm["J6"] = dt.date(2026, 4, 1); blue(qm["J6"], "yyyy-mm-dd")
    for c in ("K2", "K3"): qm[c].font = NOTE
    qm.column_dimensions["I"].width = 30
    for i, (mth, u) in enumerate(sorted(UTIL.items()), 2):
        y, mo = int(mth[:4]), int(mth[5:])
        qm.cell(i, 1, dt.date(y, mo, 1)).number_format = "mmm yyyy"
        qm.cell(i, 2, "=$J$2")
        qm.cell(i, 3, "=IF(A%d>=$J$6,1-$J$3/$J$4,1)" % i).number_format = "0.0%"
        blue(qm.cell(i, 4, u), "0%")
        qm.cell(i, 5, "=B%d*C%d*D%d" % (i, i, i)).number_format = "0.00"
        qm.cell(i, 6, "=$J$5/12*D%d" % i).number_format = "0.00"
        qm.cell(i, 7, '=YEAR(A%d)&"Q"&ROUNDUP(MONTH(A%d)/3,0)' % (i, i))
    nq = len(UTIL) + 1
    qm.cell(nq + 2, 1, "Utilisation: Mar 2026 = force majeure from 3 Mar; Aug = one cargo left Hormuz (Kpler); Nov = loadings reported at about half of pre-war (Bloomberg headline, 10 Nov). "
                       "Apr-Jul set so Qatar + UAE losses to mid-Sep total about 36 Mt (Shell, The National 14 Sep). 2027 = gradual normalisation if the Hormuz talks hold (judgement).").font = NOTE
    QY = lambda col, y: "SUMIFS(Qatar_Monthly!$%s$2:$%s$%d,Qatar_Monthly!$A$2:$A$%d,\">=\"&DATE(%d,1,1),Qatar_Monthly!$A$2:$A$%d,\"<\"&DATE(%d,1,1))" % (col, col, nq, nq, y, nq, y + 1)

    # ---- Annual balance
    ann.column_dimensions["A"].width = 34
    for c in "BCDEFG": ann.column_dimensions[c].width = 11
    ann.column_dimensions["H"].width = 90
    ann["A1"] = "Global LNG balance (million tonnes)"; ann["A1"].font = Font(bold=True, size=13)
    hdr(ann, 3, ["Supply by exporter", "2025", "2026E", "2027E", "2026 vs 2025", "2027 vs 2026", "", "Source or assumption"])
    r = 4
    for nm, a25, a26, a27, note in EXPORTERS:
        ann.cell(r, 1, nm); ann.cell(r, 2, a25).number_format = "0.0"
        if a26 is None:
            col = "E" if nm == "Qatar" else "F"
            ann.cell(r, 3, "=" + QY(col, 2026)).number_format = "0.0"; ann.cell(r, 4, "=" + QY(col, 2027)).number_format = "0.0"
        else:
            blue(ann.cell(r, 3, a26)); blue(ann.cell(r, 4, a27))
        ann.cell(r, 5, "=C%d-B%d" % (r, r)).number_format = "+0.0;-0.0;0.0"; ann.cell(r, 6, "=D%d-C%d" % (r, r)).number_format = "+0.0;-0.0;0.0"
        ann.cell(r, 8, note).font = NOTE; r += 1
    ann.cell(r, 1, "Rest of world")
    ann.cell(r, 2, "=%s-SUM(B4:B%d)" % (TOTAL_2025, r - 1)).number_format = "0.0"
    ann.cell(r, 3, "=B%d+1.5" % r).number_format = "0.0"; ann.cell(r, 4, "=C%d+3" % r).number_format = "0.0"
    for c in (3, 4): ann.cell(r, c).font = BLUE; ann.cell(r, c).fill = INFILL
    ann.cell(r, 5, "=C%d-B%d" % (r, r)).number_format = "+0.0;-0.0;0.0"; ann.cell(r, 6, "=D%d-C%d" % (r, r)).number_format = "+0.0;-0.0;0.0"
    ann.cell(r, 8, "2025 = IGU world total (436.98 Mt) minus the countries above. Nigeria, Indonesia, Algeria, Oman, PNG, Trinidad and others. Growth from Mauritania/Senegal and Congo (judgement).").font = NOTE
    sup_end = r; r += 1
    ann.cell(r, 1, "World supply").font = BOLD
    for c in "BCDEF": ann["%s%d" % (c, r)] = "=SUM(%s4:%s%d)" % (c, c, sup_end); ann["%s%d" % (c, r)].number_format = "0.0"; ann["%s%d" % (c, r)].font = BOLD
    SUP = r; r += 2
    hdr(ann, r, ["Imports by buyer", "2025", "2026E", "2027E", "2026 vs 2025", "2027 vs 2026", "Share of 2026 loss", "Source or assumption"]); r += 1
    d0 = r
    for nm, a25, a26, a27, note in IMPORTERS:
        ann.cell(r, 1, nm); ann.cell(r, 2, a25).number_format = "0.0"
        if a26 is None:
            ann.cell(r, 3, "=B%d*EU_2026_vs_2025" % r).number_format = "0.0"
        else:
            blue(ann.cell(r, 3, a26))
        blue(ann.cell(r, 4, a27))
        ann.cell(r, 5, "=C%d-B%d" % (r, r)).number_format = "+0.0;-0.0;0.0"; ann.cell(r, 6, "=D%d-C%d" % (r, r)).number_format = "+0.0;-0.0;0.0"
        ann.cell(r, 7, "=E%d/$E$%d" % (r, SUP)).number_format = "0%"
        ann.cell(r, 8, note).font = NOTE; r += 1
    ann.cell(r, 1, "Other importers (residual)").font = BOLD
    for c in "BCD": ann["%s%d" % (c, r)] = "=%s%d-SUM(%s%d:%s%d)" % (c, SUP, c, d0, c, r - 1); ann["%s%d" % (c, r)].number_format = "0.0"
    ann.cell(r, 5, "=C%d-B%d" % (r, r)).number_format = "+0.0;-0.0;0.0"; ann.cell(r, 6, "=D%d-C%d" % (r, r)).number_format = "+0.0;-0.0;0.0"
    ann.cell(r, 7, "=E%d/$E$%d" % (r, SUP)).number_format = "0%"
    ann.cell(r, 8, "Supply minus the named buyers: Taiwan, Pakistan, Bangladesh, Thailand and other South/Southeast Asia, the Middle East and Latin America. The price-sensitive buyers that lose cargoes first.").font = NOTE
    OTH = r; r += 1
    ann.cell(r, 1, "World imports").font = BOLD
    for c in "BCD": ann["%s%d" % (c, r)] = "=SUM(%s%d:%s%d)" % (c, d0, c, OTH); ann["%s%d" % (c, r)].number_format = "0.0"
    r += 2
    ann.cell(r, 1, "Europe 2026 scaling").font = BOLD; r += 1
    ann.cell(r, 1, "EU send-out Jan-Oct 2025 (TWh)"); ann.cell(r, 2, "=SUMIFS(%s,%s,\">=2025-01\",%s,\"<=2025-10\")" % (SV, SM, SM)).number_format = "0"; a = r; r += 1
    ann.cell(r, 1, "EU send-out Jan-Oct 2026 (TWh)"); ann.cell(r, 2, "=SUMIFS(%s,%s,\">=2026-01\",%s,\"<=2026-10\")" % (SV, SM, SM)).number_format = "0"; b = r; r += 1
    ann.cell(r, 1, "EU send-out Nov-Dec 2025 (TWh)"); ann.cell(r, 2, "=SUMIFS(%s,%s,\">=2025-11\",%s,\"<=2025-12\")" % (SV, SM, SM)).number_format = "0"; c_ = r; r += 1
    ann.cell(r, 1, "Assumed Nov-Dec 2026 send-out (TWh/d)"); blue(ann.cell(r, 2, 3.9), "0.00"); ann.cell(r, 8, "Nov 2026 to date runs at about 3.8-4.0 TWh/d (ALSI). Rises if Qatari cargoes return.").font = NOTE; dd = r; r += 1
    ann.cell(r, 1, "Europe 2026 vs 2025"); ann.cell(r, 2, "=(B%d+B%d*61)/(B%d+B%d)" % (b, dd, a, c_)).number_format = "0.0%"
    wb.defined_names["EU_2026_vs_2025"] = openpyxl.workbook.defined_name.DefinedName("EU_2026_vs_2025", attr_text="Annual_Balance!$B$%d" % r)
    r += 2
    ann.cell(r, 1, "What the balance says").font = BOLD; r += 1
    ann.cell(r, 1, '="Supply falls "&TEXT(-E%d,"0")&" Mt in 2026, of which Qatar and the UAE lose "&TEXT(-(E5+E11),"0")&" Mt and new North American supply adds "&TEXT(E4+E9+E10,"0")&" Mt."' % (SUP,)); r += 1
    ann.cell(r, 1, '="Europe gives up "&TEXT(-E%d,"0.0")&" Mt ("&TEXT(G%d,"0%%")&" of the loss); China, Japan, Korea and India give up "&TEXT(-SUM(E%d:E%d),"0.0")&" Mt; other buyers "&TEXT(-E%d,"0.0")&" Mt."' % (d0, d0, d0 + 1, d0 + 4, OTH)); r += 1
    ann.cell(r, 1, "Europe is paying up to keep its LNG; Asia's price-sensitive buyers and China's switch to coal and pipeline gas absorb most of the missing cargoes (inferred).").font = NOTE

    ch = BarChart(); ch.type = "bar"; ch.title = "Change in LNG imports, 2026 vs 2025 (Mt)"; ch.height = 8; ch.width = 16
    ch.add_data(Reference(ann, min_col=5, min_row=d0, max_row=OTH), titles_from_data=False)
    ch.set_categories(Reference(ann, min_col=1, min_row=d0, max_row=OTH)); ch.legend = None
    ann.add_chart(ch, "J3")

    # ---- Quarterly balance
    qtr.column_dimensions["A"].width = 34
    quarters = ["%dQ%d" % (y, q) for y in (2026, 2027) for q in (1, 2, 3, 4)]
    hdr(qtr, 1, ["Million tonnes"] + quarters + ["Note"])
    for i in range(2, 10): qtr.column_dimensions[L(i)].width = 9
    qtr.column_dimensions["J"].width = 80
    QQ = lambda col, q: "SUMIFS(Qatar_Monthly!$%s$2:$%s$%d,Qatar_Monthly!$G$2:$G$%d,\"%s\")" % (col, col, nq, nq, q)
    rows = [("Qatar", lambda q, y: "=" + QQ("E", q)), ("UAE", lambda q, y: "=" + QQ("F", q))]
    yr_col = {2026: "C", 2027: "D"}
    others = [(e[0], i) for i, e in enumerate(EXPORTERS, 4) if e[0] not in ("Qatar", "UAE")] + [("Rest of world", sup_end)]
    rows += [(nm, (lambda rr: lambda q, y: "=Annual_Balance!%s%d/4" % (yr_col[y], rr))(rr)) for nm, rr in others]
    r = 2
    for nm, f in rows:
        qtr.cell(r, 1, nm)
        for j, q in enumerate(quarters, 2): qtr.cell(r, j, f(q, int(q[:4]))).number_format = "0.0"
        r += 1
    qtr.cell(2, 10, "Qatar and UAE by month (Qatar_Monthly); other exporters spread evenly through the year (simplification).").font = NOTE
    qtr.cell(r, 1, "World supply").font = BOLD
    for j in range(2, 10): qtr.cell(r, j, "=SUM(%s2:%s%d)" % (L(j), L(j), r - 1)).number_format = "0.0"
    QS = r; r += 2
    qtr.cell(r, 1, "Europe imports")
    shares = {}
    for j, q in enumerate(quarters, 2):
        y, qn = int(q[:4]), int(q[-1])
        m1, m3 = "%d-%02d" % (y, 3 * qn - 2), "%d-%02d" % (y, 3 * qn)
        if y == 2026 and qn <= 3:
            f = "=SUMIFS(%s,%s,\">=%s\",%s,\"<=%s\")/SUMIFS(%s,%s,\">=2025-01\",%s,\"<=2025-12\")*Annual_Balance!$B$%d" % (SV, SM, m1, SM, m3, SV, SM, SM, d0)
        elif y == 2026:
            f = "=Annual_Balance!$C$%d-SUM(B%d:D%d)" % (d0, r, r)
        else:
            p1, p3 = "2025-%02d" % (3 * qn - 2), "2025-%02d" % (3 * qn)
            f = "=SUMIFS(%s,%s,\">=%s\",%s,\"<=%s\")/SUMIFS(%s,%s,\">=2025-01\",%s,\"<=2025-12\")*Annual_Balance!$D$%d" % (SV, SM, p1, SM, p3, SV, SM, SM, d0)
        qtr.cell(r, j, f).number_format = "0.0"
    qtr.cell(r, 10, "2026Q1-Q3 from EU send-out (ALSI) scaled to Europe's 2025 total; 2026Q4 = annual estimate minus Q1-Q3; 2027 uses 2025 seasonality.").font = NOTE
    QE = r; r += 1
    qtr.cell(r, 1, "Asia and all other buyers (residual)")
    for j in range(2, 10): qtr.cell(r, j, "=%s%d-%s%d" % (L(j), QS, L(j), QE)).number_format = "0.0"
    r += 1
    qtr.cell(r, 1, "Same quarter of 2025, Asia and other (approx.)")
    for j, q in enumerate(quarters[:4], 2):
        qn = int(q[-1]); p1, p3 = "2025-%02d" % (3 * qn - 2), "2025-%02d" % (3 * qn)
        qtr.cell(r, j, "=Annual_Balance!$B$%d/4-SUMIFS(%s,%s,\">=%s\",%s,\"<=%s\")/SUMIFS(%s,%s,\">=2025-01\",%s,\"<=2025-12\")*Annual_Balance!$B$%d" % (SUP, SV, SM, p1, SM, p3, SV, SM, SM, d0)).number_format = "0.0"
    qtr.cell(r, 10, "2025 world supply spread evenly, minus Europe by quarter. Approximate.").font = NOTE

    # ---- README
    rd.column_dimensions["A"].width = 120
    for i, t in enumerate([
            "Global LNG balance: where did the missing Qatari cargoes come from?",
            "Built %s. Script: 09_Code/Data_Pulls/20261110_Code_Build_Global_LNG_Balance_Global_v01.py. EU send-out data to %s." % (dt.date.today().isoformat(), last),
            "",
            "Annual_Balance: supply by exporter and imports by buyer, 2025 actual, 2026-2027 estimates. Change blue cells; totals, shares and the summary sentences update.",
            "Quarterly_Balance: the same by quarter, 2026-2027. Qatar_Monthly: the Hormuz path for Qatar and the UAE (utilisation by month is the main lever).",
            "Other importers are a residual: world supply minus the named buyers. Stock changes at sea and in tanks are ignored (a simplification).",
            "",
            "Sources: IGU World LNG Report 2026 (2025 trade, via TASS 7 Jul 2026 and nCa 8 Jul 2026); Kpler and ICIS estimates via Reuters (Clyde Russell, 16 Sep and 22 Oct 2026) and energynewsbeat (1 Nov 2026);",
            "The National (14 and 28 Sep 2026) on Qatar damage and force majeure; GIE ALSI (EU send-out). Units: million tonnes LNG; 1 Mt ~ 1.36 bcm ~ 14.4 TWh.",
            "Estimates for 2026-2027 are judgement unless a source is named. Not investment advice."], 1):
        rd.cell(i, 1, t).font = Font(bold=True, size=13) if i == 1 else Font()
    wb.calculation.fullCalcOnLoad = True
    wb.active = 1
    wb.save(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("raw"); ap.add_argument("--out", required=True)
    a = ap.parse_args(); build(a.raw, a.out); print("wrote", a.out)
