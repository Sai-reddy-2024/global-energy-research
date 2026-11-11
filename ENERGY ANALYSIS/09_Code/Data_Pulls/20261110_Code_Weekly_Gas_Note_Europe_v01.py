"""Weekly European gas and LNG note: one page, three charts, a 'so what' left for the author.

Usage:
    python3 20261110_Code_Weekly_Gas_Note_Europe_v01.py <raw folder> <call paths CSV> <output folder> [--date YYYYMMDD]

Inputs: GIE AGSI+ storage, GIE ALSI LNG send-out and ENTSOG flows (in <raw folder>), and the model case paths written
by the storage model script for the vintage of the live call (<call paths CSV>). Writes YYYYMMDD_Analysis_Weekly_Gas_Note_Europe_Weekly_v01.md
and three PNG charts into <output folder>. The 'So what' section is a placeholder: the call and its reasoning are the author's.
"""
import argparse, csv, datetime as dt, glob, importlib.util, os, statistics as st
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("model", os.path.join(HERE, "20261110_Code_Build_EU_Gas_Storage_Model_Europe_v01.py"))
model = importlib.util.module_from_spec(spec); spec.loader.exec_module(model)
TWH_PER_BCM = model.TWH_PER_BCM
INK, GRID = "#222222", "#DDDDDD"
CASE_COL = {"warm": "#D08C2E", "normal": "#1F4E78", "cold": "#3A8FB7"}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#888888", "axes.grid": True, "grid.color": GRID})


def fnum(x):
    try: return float(x)
    except (TypeError, ValueError): return None


def alsi_eu(raw):
    f = glob.glob(os.path.join(raw, "*_GIE_ALSI_LNG_Terminals_Europe_Daily.csv"))[0]
    out = {}
    for r in csv.DictReader(open(f)):
        if r["area"] == "EU" and fnum(r["send_out_gwh_d"]) is not None: out[r["gas_day"]] = fnum(r["send_out_gwh_d"]) / 1000
    return out


def wavg(series, end, days=7, shift_years=0):
    xs = []
    for i in range(days):
        d = end - dt.timedelta(days=i)
        if shift_years: d = d.replace(year=d.year - shift_years) if not (d.month == 2 and d.day == 29) else d - dt.timedelta(days=1)
        v = series.get(d.isoformat())
        if v is not None: xs.append(v)
    return st.mean(xs) if xs else None


def main(raw, paths_csv, outdir, date):
    os.makedirs(outdir, exist_ok=True)
    stor, flows = model.load(raw); lng = alsi_eu(raw)
    last = max(d for d in stor if d in flows); ld = dt.date.fromisoformat(last)
    paths = list(csv.DictReader(open(paths_csv))); vintage = paths[0]["vintage"]
    P = {r["gas_day"]: r for r in paths}
    pct = stor[last]["full"]; twh = stor[last]["twh"]
    wk = (ld - dt.timedelta(days=7)).isoformat()
    yago = ld.replace(year=ld.year - 1).isoformat()
    model_today = P.get(last)
    # imports by route: last 7 days vs same week last year, mcm/d
    routes = {r: (wavg({d: flows[d].get(r, 0) for d in flows}, ld), wavg({d: flows[d].get(r, 0) for d in flows}, ld, shift_years=1)) for r in model.ROUTES}
    tot_now = sum(v[0] for v in routes.values()); tot_ly = sum(v[1] or 0 for v in routes.values())
    lng7, lng7ly = routes["LNG"]   # headline: ENTSOG LNG entry flows, the series the storage model uses (ALSI only in chart 3)
    nw7 = st.mean([stor[(ld - dt.timedelta(days=i)).isoformat()]["wd"] - stor[(ld - dt.timedelta(days=i)).isoformat()]["inj"] for i in range(7)])
    end = paths[-1]

    # ---- chart 1: storage vs model and past winters
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    w0 = dt.date(ld.year if ld.month >= 7 else ld.year - 1, 10, 1)
    for k, yrs in enumerate([2, 1]):
        a = dt.date(w0.year - yrs, 10, 1); b = dt.date(w0.year - yrs + 1, 3, 31)
        xs = [d for d in sorted(stor) if a.isoformat() <= d <= b.isoformat()]
        ax.plot([dt.date.fromisoformat(d).replace(year=dt.date.fromisoformat(d).year + yrs) for d in xs], [stor[d]["full"] for d in xs],
                color="#BBBBBB" if yrs == 2 else "#888888", lw=1.2, label="Winter %d-%02d" % (w0.year - yrs, (w0.year - yrs + 1) % 100))
    xs = [d for d in sorted(stor) if d >= w0.isoformat()]
    ax.plot([dt.date.fromisoformat(d) for d in xs], [stor[d]["full"] for d in xs], color=INK, lw=2.2, label="Actual %d-%02d" % (w0.year, (w0.year + 1) % 100))
    for cs in ("warm", "normal", "cold"):
        ax.plot([dt.date.fromisoformat(r["gas_day"]) for r in paths], [float(r[cs + "_full_pct"]) for r in paths], color=CASE_COL[cs], lw=1.6, ls="--", label="Model: %s" % cs)
    ax.axhline(30, color="#C0392B", lw=0.8, ls=":"); ax.text(dt.date(w0.year, 10, 3), 31, "30%", color="#C0392B", fontsize=8)
    ax.set_ylim(0, 100); ax.set_ylabel("% full"); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.set_title("EU gas storage vs model cases (vintage %s)" % vintage, loc="left", fontsize=10, color=INK)
    ax.legend(fontsize=7, ncol=3, frameon=False, loc="lower left")
    fig.text(0.01, 0.01, "Source: GIE AGSI+; model: storage model (01.4)", fontsize=7, color="#666666"); fig.tight_layout(rect=(0, 0.03, 1, 1))
    c1 = "%s_Chart_EU_Storage_vs_Model.png" % date; fig.savefig(os.path.join(outdir, c1), dpi=150); plt.close(fig)

    # ---- chart 2: imports by route, this week vs same week last year
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    names = [r for r in model.ROUTES if (routes[r][0] or 0) > 0.01 or (routes[r][1] or 0) > 0.01]
    y = range(len(names))
    ax.barh([i + 0.2 for i in y], [(routes[r][1] or 0) / TWH_PER_BCM * 1000 for r in names], height=0.4, color="#BBBBBB", label="Same week last year")
    ax.barh([i - 0.2 for i in y], [routes[r][0] / TWH_PER_BCM * 1000 for r in names], height=0.4, color="#1F4E78", label="Last 7 days")
    ax.set_yticks(list(y)); ax.set_yticklabels(names); ax.invert_yaxis(); ax.set_xlabel("mcm/d")
    ax.set_title("EU gas imports by route, 7 days to %s" % ld.strftime("%-d %b"), loc="left", fontsize=10, color=INK); ax.legend(fontsize=7, frameon=False)
    fig.text(0.01, 0.01, "Source: ENTSOG Transparency Platform, physical flows", fontsize=7, color="#666666"); fig.tight_layout(rect=(0, 0.03, 1, 1))
    c2 = "%s_Chart_EU_Imports_by_Route.png" % date; fig.savefig(os.path.join(outdir, c2), dpi=150); plt.close(fig)

    # ---- chart 3: LNG send-out, 7-day average, this year vs last
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    for yrs, col, lab in ((1, "#BBBBBB", "A year earlier"), (0, "#1F4E78", "This year")):
        xs, ys = [], []
        for i in range(120, -1, -1):
            d = ld - dt.timedelta(days=i); v = wavg(lng, d, shift_years=yrs)
            if v is not None: xs.append(d); ys.append(v / TWH_PER_BCM * 1000)
        ax.plot(xs, ys, color=col, lw=1.8, label=lab)
    ax.set_ylabel("mcm/d (7-day avg)"); ax.xaxis.set_major_formatter(mdates.DateFormatter("%-d %b"))
    ax.set_title("EU LNG send-out, terminal data (GIE ALSI)", loc="left", fontsize=10, color=INK); ax.legend(fontsize=7, frameon=False)
    fig.text(0.01, 0.01, "Source: GIE ALSI", fontsize=7, color="#666666"); fig.tight_layout(rect=(0, 0.03, 1, 1))
    c3 = "%s_Chart_EU_LNG_SendOut.png" % date; fig.savefig(os.path.join(outdir, c3), dpi=150); plt.close(fig)

    # ---- note
    gap = pct - float(model_today["normal_full_pct"]) if model_today else None
    pub = dt.datetime.strptime(date, "%Y%m%d").date()
    rows = "\n".join("| %s | %.0f | %s | %s |" % (r, routes[r][0] / TWH_PER_BCM * 1000, "%.0f" % (routes[r][1] / TWH_PER_BCM * 1000) if routes[r][1] is not None else "n/a",
                                                ("%+.0f%%" % (100 * (routes[r][0] / routes[r][1] - 1))) if routes[r][1] else "n/a") for r in names)
    md = f"""# European gas weekly: {pub.strftime('%-d %B %Y')}

*Data to gas day {ld.strftime('%-d %b %Y')}. Storage model vintage {vintage}. Draft until the author signs off the "So what".*

## The numbers
- **EU storage:** {pct:.1f}% full ({twh:.0f} TWh), against {stor[yago]['full']:.1f}% a year earlier and {stor[wk]['full']:.1f}% a week ago. Net withdrawals averaged {nw7:.2f} TWh/d over the last 7 days.
- **Against the model:** {"the normal case had %.1f%% for this date, so storage is running %+.1f points against it." % (float(model_today['normal_full_pct']), gap) if model_today else "the model path starts after this date."} The cases end March at {float(end['warm_full_pct']):.0f}% (warm), {float(end['normal_full_pct']):.0f}% (normal) and {float(end['cold_full_pct']):.0f}% (cold).
- **Imports:** {tot_now / TWH_PER_BCM * 1000:.0f} mcm/d over the last 7 days, {100 * (tot_now / tot_ly - 1):+.0f}% on the same week last year.
- **LNG:** {lng7 / TWH_PER_BCM * 1000:.0f} mcm/d into the EU grid (ENTSOG LNG entry points, 7-day average), {100 * (lng7 / lng7ly - 1):+.0f}% y/y. Terminal send-out reported by GIE ALSI is in the chart below and can differ by a few percent.

![EU storage vs model]({c1})

| Route | Last 7 days (mcm/d) | Same week last year | Change |
|---|---|---|---|
{rows}

![EU imports by route]({c2})

![EU LNG send-out]({c3})

## So what
*To be written by the author: what changed this week, whether the base-case call still holds, and what would change it.*

## Prices and positioning
- TTF and JKM daily prices are not in the free data set; quote the latest settlement with its source and date, and use the Numbers of Record sheet for any figure that also appears on the website.
- CFTC covers Henry Hub only. TTF positioning (ICE Commitments of Traders) has to be downloaded by hand each week.

*Sources: GIE AGSI+ and ALSI, ENTSOG Transparency Platform. 1 bcm = 10.55 TWh. Research for information only; not investment advice.*
"""
    out = os.path.join(outdir, "%s_Analysis_Weekly_Gas_Note_Europe_Weekly_v01.md" % date)
    open(out, "w").write(md)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("raw"); ap.add_argument("paths_csv"); ap.add_argument("outdir"); ap.add_argument("--date")
    a = ap.parse_args()
    print("wrote", main(a.raw, a.paths_csv, a.outdir, a.date or dt.date.today().strftime("%Y%m%d")))
