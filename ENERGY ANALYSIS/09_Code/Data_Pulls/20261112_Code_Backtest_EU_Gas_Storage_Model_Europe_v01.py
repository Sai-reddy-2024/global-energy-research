"""Backtest the EU gas storage model: rerun it as of a past date each year, using only data known then, and compare with what happened.

Usage:
    python3 20261112_Code_Backtest_EU_Gas_Storage_Model_Europe_v01.py <ENERGY ANALYSIS folder> <raw folder> [<raw folder> ...] [--out FILE] [--csv FILE]
        [--vintage-md 11-09] [--years 2023 2024 2025]

<raw folder>s hold GIE AGSI+ and ENTSOG files (as written by the pull script); several folders are merged, so an older pull
(e.g. 2021-2023) can sit beside the current one. The free ENTSOG API keeps only the last 5 years (from about 12 Nov 2021),
so 2022 is the first testable vintage. It is left out by default (author's choice): winter 2022-23 followed the Russian
supply cut-off and a price-driven demand collapse that no model calibrated on the winters before could see, and it has
only one partial calibration winter. Run --years 2022 2023 2024 2025 to include it. Temperatures: the rolling Open-Meteo history in 01.6.

For each year Y the model is rebuilt exactly as the live model would have been on the vintage date (default 9 Nov):
  - storage at the end of the vintage gas day; imports by route = the 30 days before it
  - normal call = the two winters before Y, weather-corrected; weather fit on October-April days from 1 Jan Y-2
  - climate = the 30 winters ending Y-1, trend value for winter Y; warm/cold = 10th/90th percentile around the trend
  - no Gulf LNG recovery term (that is specific to 2026-27); no demand-cut or LNG adjustments in the 'actual weather' run
It then reports the warm/normal/cold end-March fill, the actual end-March fill (GIE AGSI+), the error, and a run with the
winter's actual heating degree days, which splits the miss into a weather part and a non-weather part (imports, demand).
Sources: GIE AGSI+, ENTSOG, Open-Meteo (ERA5, CC-BY 4.0). Research only; not investment advice.
"""
import argparse, csv, datetime as dt, glob, importlib.util, os, statistics as st
from collections import defaultdict
import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.chart import BarChart, Reference

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("storage", os.path.join(HERE, "20261110_Code_Build_EU_Gas_Storage_Model_Europe_v01.py"))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)


def load_many(raws):
    """Merge storage and flows from several raw folders; later folders win on overlapping days."""
    stor, flows = {}, defaultdict(lambda: defaultdict(float))
    for raw in raws:
        s, f = M.load(raw)
        stor.update(s)
        for d, v in f.items(): flows[d] = v
    return stor, flows


def backtest_year(Y, md, stor, flows, hdd, calib_winters=2):
    vint = dt.date(Y, *md); s0_day = vint.isoformat(); start = vint + dt.timedelta(days=1)
    M.END = dt.date(Y + 1, 3, 31); M.FIT_START = dt.date(Y - 2, 1, 1); M.CLIM_LAST = Y - 1
    call, full_w, norm_obs, base, summer_years, route30 = M.calibrate(stor, flows, s0_day)
    if calib_winters == 1:   # variant: normal call from the last winter only
        full_w = full_w[-1:]
        norm_obs = {m * 10 + h: st.mean([call[d] for d in call if M.half(dt.date.fromisoformat(d)) == m * 10 + h and M.winter_of(dt.date.fromisoformat(d)) == full_w[0]]) for m, h in M.HALVES}
    wx = M.weather(hdd, call, full_w, norm_obs, start, s0_day)
    s0, wgv = stor[s0_day]["twh"], stor[s0_day]["wgv"]
    nogulf = dict(M.GULF, uplift=0.0)
    out = {cs: M.run_case(cs, start, s0, wgv, wx["norm"], wx, route30, nogulf)[-1]["pct"] for cs in M.CASES}
    # actual weather and actual outcome
    d0, d1 = start, M.END
    days = [(d0 + dt.timedelta(days=i)).isoformat() for i in range((d1 - d0).days + 1)]
    hdd_act = sum(hdd[d] for d in days)
    # the model's winter HDD runs from the vintage month/day: use the same window for the comparison
    hdd_norm_win = wx["trend"] * sum(hdd[d] for d in days) / max(1e-9, sum(hdd[d] for d in days))  # = trend (same window)
    wx_act = dict(wx); wx_act["adj"] = dict(wx["adj"], Actual=hdd_act / wx["trend"] - 1)
    M.LNG_ADJ.setdefault("Actual", 0.0); M.DEMAND_RESP.setdefault("Actual", 0.0)
    act_w = M.run_case("Actual", start, s0, wgv, wx["norm"], wx_act, route30, nogulf)[-1]["pct"]
    end_day = M.END.isoformat()
    actual = stor[end_day]["full"] if end_day in stor else None
    imp_assumed = sum(route30.values())
    imp_actual = st.mean([sum(flows[d].values()) for d in days if d in flows])
    call_act = st.mean([call[d] for d in days if d in call]) if all(d in call for d in days) else None
    return dict(year=Y, winter="%d-%02d" % (Y, (Y + 1) % 100), vintage=s0_day, start_pct=100 * s0 / wgv,
                calib=" and ".join(full_w), fit_slope=wx["b"], fit_r2=wx["r2"],
                warm=out["Warm"], normal=out["Normal"], cold=out["Cold"], actual=actual,
                err=None if actual is None else out["Normal"] - actual,
                inside=None if actual is None else (out["Cold"] - 1e-9 <= actual <= out["Warm"] + 1e-9),
                hdd_normal=wx["trend"], hdd_actual=hdd_act, hdd_dev=100 * (hdd_act / wx["trend"] - 1),
                actual_weather=act_w, err_weather_known=None if actual is None else act_w - actual,
                imp_assumed=imp_assumed, imp_actual=imp_actual)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("root"); ap.add_argument("raws", nargs="+")
    ap.add_argument("--out"); ap.add_argument("--csv"); ap.add_argument("--vintage-md", default="11-09"); ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    a = ap.parse_args()
    md = tuple(int(x) for x in a.vintage_md.split("-"))
    stor, flows = load_many(a.raws)
    hdd = M.hdd_series(M.load_temps(os.path.join(a.root, M.TEMPS)))
    rows = [backtest_year(Y, md, stor, flows, hdd) for Y in a.years]
    for r, r1 in zip(rows, [backtest_year(Y, md, stor, flows, hdd, calib_winters=1) for Y in a.years]):
        r["normal_1w"] = r1["normal"]; r["actual_weather_1w"] = r1["actual_weather"]
    done = [r for r in rows if r["actual"] is not None]
    mae = st.mean(abs(r["err"]) for r in done); bias = st.mean(r["err"] for r in done)
    mae_w = st.mean(abs(r["err_weather_known"]) for r in done)
    for r in rows:
        print("%s  start %.1f  model W/N/C %.1f / %.1f / %.1f  actual %.1f  error %+.1f  inside %s  HDD %+.0f%%  with actual weather %.1f (%+.1f)  imports %.2f vs %.2f" % (
            r["winter"], r["start_pct"], r["warm"], r["normal"], r["cold"], r["actual"], r["err"], r["inside"], r["hdd_dev"], r["actual_weather"], r["err_weather_known"], r["imp_assumed"], r["imp_actual"]))
    print("mean absolute error %.1f points, bias %+.1f, with actual weather %.1f; inside range %d of %d" % (mae, bias, mae_w, sum(r["inside"] for r in done), len(done)))

    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.DictWriter(f, list(rows[0])); w.writeheader(); [w.writerow({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}) for r in rows]
    if a.out:
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Backtest"
        HDR = PatternFill("solid", fgColor="1F4E78"); HF = Font(bold=True, color="FFFFFF"); NOTE = Font(italic=True, color="555555")
        ws["A1"] = "EU gas storage model backtest: projection made on %s each year vs actual end-March storage" % dt.date(2000, *md).strftime("%-d %B"); ws["A1"].font = Font(bold=True, size=13)
        heads = [("Winter", "winter", None), ("Vintage (end of gas day)", "vintage", None), ("Storage at vintage %", "start_pct", "0.0"),
                 ("Model warm %", "warm", "0.0"), ("Model normal %", "normal", "0.0"), ("Model cold %", "cold", "0.0"), ("Actual 31 Mar %", "actual", "0.0"),
                 ("Error, normal minus actual (points)", None, "+0.0;-0.0;0.0"), ("Actual inside warm-cold range", None, None),
                 ("Winter HDD vs normal %", "hdd_dev", "+0.0;-0.0;0.0"), ("Model with actual weather %", "actual_weather", "0.0"), ("Error with actual weather (points)", None, "+0.0;-0.0;0.0"),
                 ("Imports assumed (TWh/d)", "imp_assumed", "0.00"), ("Imports actual, vintage to 31 Mar (TWh/d)", "imp_actual", "0.00"), ("Calibration winters", "calib", None),
                 ("Variant, last winter only: normal %", "normal_1w", "0.0"), ("Variant error (points)", None, "+0.0;-0.0;0.0")]
        for j, (h, _, _) in enumerate(heads, 1):
            c = ws.cell(3, j, h); c.fill = HDR; c.font = HF
            ws.column_dimensions[openpyxl.utils.get_column_letter(j)].width = 14 if j > 1 else 10
        ws.column_dimensions["O"].width = 22
        for i, r in enumerate(rows, 4):
            for j, (h, k, fmt) in enumerate(heads, 1):
                if k: v = r[k]
                elif j == 8: v = "=E%d-G%d" % (i, i)
                elif j == 9: v = '=IF(AND(G%d>=F%d,G%d<=D%d),"yes","no")' % (i, i, i, i)
                elif j == 12: v = "=K%d-G%d" % (i, i)
                elif j == 17: v = "=P%d-G%d" % (i, i)
                c = ws.cell(i, j, v)
                if fmt: c.number_format = fmt
        e = 3 + len(rows); s = e + 2
        for i, (lab, fml, fmt) in enumerate([
                ("Mean absolute error, normal case (points)", "=SUMPRODUCT(ABS(H4:H%d))/COUNT(H4:H%d)" % (e, e), "0.0"),
                ("Average error, normal case (points; + = model too high)", "=AVERAGE(H4:H%d)" % e, "+0.0;-0.0;0.0"),
                ("Mean absolute error with actual weather (points)", "=SUMPRODUCT(ABS(L4:L%d))/COUNT(L4:L%d)" % (e, e), "0.0"),
                ("Winters inside the warm-cold range", '=COUNTIF(I4:I%d,"yes")&" of "&COUNTA(I4:I%d)' % (e, e), None),
                ("Winters within the 3-point call tolerance", '=SUMPRODUCT(--(ABS(H4:H%d)<=3))&" of "&COUNT(H4:H%d)' % (e, e), None),
                ("Variant, last winter only: mean absolute error (points)", "=SUMPRODUCT(ABS(Q4:Q%d))/COUNT(Q4:Q%d)" % (e, e), "0.0")], s):
            ws.cell(i, 1, lab).font = Font(bold=True); c = ws.cell(i, 5, fml)
            if fmt: c.number_format = fmt
        notes = ["Each row reruns today's model as it would have run on that date, with only data available then: storage and the last 30 days of imports (GIE AGSI+, ENTSOG),",
                 "the two previous winters for the normal call, a weather fit from 1 January two years earlier, and the 30 winters before for normal, warm and cold weather (Open-Meteo).",
                 "No Gulf LNG recovery term is used (it is specific to 2026-27). 'With actual weather' reruns the normal case with the winter's real heating degree days:",
                 "what is left is the non-weather miss (imports that changed after the vintage, demand behaving differently from the two calibration winters).",
                 "Winters covered: 2023-24 to 2025-26. Winter 2022-23 is left out (author's choice): it followed the Russian supply cut-off and a price-driven demand collapse,",
                 "and ENTSOG's free API (5 years, from 12 Nov 2021) gives it only one partial calibration winter. Winter 2021-22 cannot be tested for the same reason.",
                 "'Variant, last winter only' calibrates the normal call on the single most recent winter instead of the last two.",
                 "Model figures are values from the backtest script (09_Code/Data_Pulls/20261112_Code_Backtest_EU_Gas_Storage_Model_Europe_v01.py); the error and summary cells are formulas."]
        for i, t in enumerate(notes, s + 7): ws.cell(i, 1, t).font = NOTE
        ch = BarChart(); ch.type = "col"; ch.title = "End-March storage: model normal case vs actual"; ch.y_axis.title = "% full"; ch.height = 8; ch.width = 18
        for col in (5, 7): ch.add_data(Reference(ws, min_col=col, min_row=3, max_row=e), titles_from_data=True)
        ch.set_categories(Reference(ws, min_col=1, min_row=4, max_row=e)); ws.add_chart(ch, "A%d" % (s + 14))
        ws.freeze_panes = "B4"
        wb.calculation.fullCalcOnLoad = True; wb.save(a.out)
    return rows


if __name__ == "__main__":
    main()
