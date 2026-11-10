#!/usr/bin/env python3
"""Build the Global Energy Analysis website from the research folder.

Reads the section briefs (Markdown) and the Key Indicators workbook in
"ENERGY ANALYSIS" and writes static HTML pages into the Website folder.
The research files are only read, never changed.

Usage (from the master energy folder):
    pip install markdown openpyxl
    python3 Website/_build/build_site.py

Optional: --src "<path to ENERGY ANALYSIS>"  --out "<path to Website>"
"""
import argparse
import glob
import html
import os
import re

import markdown
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.dirname(HERE)
MASTER = os.path.dirname(SITE_DIR)

SECTIONS = [
    ("01_Market_Foundations_and_Data", "foundations", "Market Foundations", "Supply, demand, stocks, macro and scenarios"),
    ("02_Upstream_Production_by_Source", "upstream", "Upstream Production", "Oil, gas, coal, nuclear, renewables, minerals"),
    ("03_Midstream_Logistics_and_Transportation", "midstream", "Midstream Logistics", "Chokepoints, tankers, pipelines, storage, trade"),
    ("04_Downstream_Refining_and_End_Use", "downstream", "Downstream and End Use", "Refining, power, demand sectors, storage"),
    ("05_Regional_Markets_and_Geopolitics", "regions", "Regions and Geopolitics", "OPEC+, North America, demand hubs, Russia"),
    ("06_Policy_Regulation_and_Carbon", "policy", "Policy and Carbon", "COP31, EU ETS, CBAM, subsidies, emissions"),
    ("07_Financial_Analysis_and_Trading", "finance", "Finance and Trading", "Prices, curves, corporates, scenario models"),
]
REVIEW_GLOB = "08_Outputs/Reports/*Global_Energy_Market_Review*.md"
WORKBOOK_GLOB = "01_Market_Foundations_and_Data/01.4_Supply_Demand_Balances/*Key_Indicators*.xlsx"


def latest(paths):
    """Newest file by the YYYYMMDD prefix and version suffix in its name."""
    return sorted(paths)[-1] if paths else None


def md_to_html(text):
    return markdown.markdown(text, extensions=["tables", "sane_lists"])


def fix_links(body):
    """Point links between briefs at the site's own pages."""
    for folder, slug, _, _ in SECTIONS:
        body = re.sub(r'href="[^"]*%s/[^"]*\.md"' % re.escape(folder), 'href="%s.html"' % slug, body)
    body = body.replace("<code>01_Market_Foundations_and_Data/01.4_Supply_Demand_Balances/", '<code>')
    # External links open in a new tab
    body = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener">', body)
    return body


def split_title(md_text):
    lines = md_text.strip().splitlines()
    title = lines[0].lstrip("# ").strip() if lines and lines[0].startswith("#") else ""
    rest = "\n".join(lines[1:]) if title else md_text
    return title, rest


NAV_ITEMS = [("index", "Home"), ("review", "Market Review"), ("indicators", "Key Indicators")] + \
            [(s[1], s[2]) for s in SECTIONS] + [("about", "About")]


def page(slug, title, body, description=""):
    nav = "\n".join(
        '<a href="%s.html"%s>%s</a>' % (s, ' aria-current="page"' if s == slug else "", html.escape(t))
        for s, t in NAV_ITEMS
    )
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Global Energy Analysis</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="topbar">
  <a class="brand" href="index.html"><span class="mark" aria-hidden="true"></span>Global Energy Analysis</a>
  <button class="menu" aria-expanded="false" aria-controls="nav">Menu</button>
</header>
<div class="layout">
<nav id="nav" class="sidenav">
{nav}
</nav>
<main>
{body}
<footer>Independent research. Figures are as published by the cited sources; lines marked <em>inferred</em> are analytical judgement, not published data. Not investment advice.</footer>
</main>
</div>
<script src="assets/site.js"></script>
</body>
</html>
""".format(title=html.escape(title), desc=html.escape(description), nav=nav, body=body)


# ---------- Charts (inline SVG, single series, hover tooltips) ----------

def hbar_chart(title, rows, unit, max_v=None, note=""):
    """rows: list of (label, value, tooltip). Horizontal bars, one series."""
    max_v = max_v or max(v for _, v, _ in rows)
    bar_h, gap, label_w, w = 22, 12, 150, 640
    plot_w = w - label_w - 70
    h = len(rows) * (bar_h + gap) + 10
    parts = []
    for i, (label, v, tip) in enumerate(rows):
        y = 5 + i * (bar_h + gap)
        bw = max(2, plot_w * v / max_v)
        parts.append(
            '<g class="hit" data-tip="{tip}"><rect x="0" y="{y0}" width="{w}" height="{hh}" fill="transparent"/>'
            '<text x="{lx}" y="{ty}" class="lbl" text-anchor="end">{label}</text>'
            '<path d="M{x0},{y} h{bw4} a4,4 0 0 1 4,4 v{bh8} a4,4 0 0 1 -4,4 h-{bw4} z" class="bar"/>'
            '<text x="{vx}" y="{ty}" class="val">{val}</text></g>'.format(
                tip=html.escape(tip), y0=y - gap / 2, w=w, hh=bar_h + gap, lx=label_w - 10, ty=y + bar_h / 2 + 4,
                label=html.escape(label), x0=label_w, y=y, bw4=max(0, bw - 4), bh8=bar_h - 8,
                vx=label_w + bw + 8, val=html.escape(("%g" % v) + unit)))
    svg = '<svg viewBox="0 0 {w} {h}" role="img" aria-label="{t}">{p}</svg>'.format(w=w, h=h, t=html.escape(title), p="".join(parts))
    return '<figure class="chart"><figcaption>{t}</figcaption>{svg}{n}</figure>'.format(
        t=html.escape(title), svg=svg, n='<p class="note">%s</p>' % note if note else "")


def line_chart(title, points, unit, note=""):
    """points: list of (label, value, is_forecast). One series, 2px line, markers."""
    w, h, l, r, t, b = 640, 240, 44, 20, 16, 32
    vals = [v for _, v, _ in points]
    lo, hi = 0, (int(max(vals) / 20) + 1) * 20
    xs = [l + i * (w - l - r) / (len(points) - 1) for i in range(len(points))]
    ys = [t + (h - t - b) * (1 - (v - lo) / (hi - lo)) for v in vals]
    grid = "".join('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" class="grid"/><text x="%d" y="%.1f" class="axis" text-anchor="end">%d</text>'
                   % (l, w - r, t + (h - t - b) * (1 - g / hi), t + (h - t - b) * (1 - g / hi), l - 6, t + (h - t - b) * (1 - g / hi) + 4, g)
                   for g in range(0, hi + 1, 20))
    path = "M" + " L".join("%.1f,%.1f" % p for p in zip(xs, ys))
    marks = "".join(
        '<g class="hit" data-tip="{tip}"><rect x="{rx}" y="{t}" width="40" height="{ph}" fill="transparent"/>'
        '<circle cx="{x}" cy="{y}" r="5" class="dot{f}"/><text x="{x}" y="{ly}" class="axis" text-anchor="middle">{lab}</text></g>'.format(
            tip=html.escape("%s: %g%s%s" % (lab, v, unit, " (forecast)" if fc else "")), rx=x - 20, t=t, ph=h - t - b,
            x="%.1f" % x, y="%.1f" % y, f=" fc" if fc else "", ly=h - 10, lab=html.escape(lab))
        for (lab, v, fc), x, y in zip(points, xs, ys))
    svg = '<svg viewBox="0 0 {w} {h}" role="img" aria-label="{tt}">{g}<path d="{p}" class="line"/>{m}</svg>'.format(
        w=w, h=h, tt=html.escape(title), g=grid, p=path, m=marks)
    return '<figure class="chart"><figcaption>{t}</figcaption>{svg}{n}</figure>'.format(
        t=html.escape(title), svg=svg, n='<p class="note">%s</p>' % note if note else "")


# ---------- Pages ----------

def num(s):
    try:
        return float(str(s).replace("~", "").replace(",", "").replace("+", ""))
    except ValueError:
        return None


def build_indicators(wb_path):
    wb = openpyxl.load_workbook(wb_path, data_only=True)
    sheets = {}
    for ws in wb:
        rows = [r for r in ws.iter_rows(values_only=True) if any(c is not None for c in r)]
        sheets[ws.title] = rows

    def lookup(sheet, ind, period):
        for r in sheets.get(sheet, [])[1:]:
            if r[0] == ind and r[1] == period:
                return num(r[2])
        return None

    charts = []
    shut = [(p, lookup("Oil_Balance", "Gulf crude shut-ins", p)) for p in ["May-26", "Sep-26", "4Q26F", "1Q27F"]]
    if all(v is not None for _, v in shut):
        charts.append(hbar_chart("Gulf crude shut-ins (mb/d)", [(p + (" (peak)" if p == "May-26" else ""), v, "%s: %g mb/d%s" % (p, v, " forecast" if p.endswith("F") else "")) for p, v in shut],
                                 " mb/d", note="Source: EIA STEO Oct-26. Periods ending in F are forecasts."))
    brent = [("Sep-26 avg", 116.89, False)]
    for p in ["4Q26"]:
        v = lookup("Prices", "Brent forecast", p)
        if v: brent.append((p, v, True))
    brent += [("2Q27", 87, True), ("4Q27", 74, True)]
    charts.append(line_chart("Brent: September average and EIA forecast path ($/bbl)", brent, " $/bbl",
                             note="Sep-26 is North Sea Dated average (IEA); later points are EIA STEO Oct-26 forecasts (hollow markers)."))
    charts.append(hbar_chart("Gulf exports in September 2026, as % of pre-war level", [
        ("Crude oil", 75, "Crude: 13.9 mb/d, over 75% of pre-war (IEA)"),
        ("LPG", 45, "LPG: 0.67 vs 1.5 mb/d pre-war (45%)"),
        ("Refined products", 40, "Products: 1.9 vs 4.7 mb/d pre-war (40%)"),
        ("LNG (Qatar + UAE)", 20, "LNG: about 2 vs over 10 bcm/month pre-crisis (about 20%)"),
    ], "%", max_v=100, note="Calculated from IEA OMR Oct-26 and OIES Gas Review #34. Crude is a lower bound (over 75%); LNG is approximate."))

    labels = {"Oil_Balance": "Oil balance", "Prices": "Prices", "Gas_LNG": "Gas and LNG",
              "Power_Transition": "Power and transition", "Macro": "Macro"}
    tables = []
    for name, rows in sheets.items():
        head = "".join("<th>%s</th>" % html.escape(str(c or "")) for c in rows[0])
        body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % html.escape("" if c is None else str(c)) for c in r) for r in rows[1:])
        tables.append('<section id="{id}"><h2>{t}</h2><div class="tablewrap"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div></section>'.format(
            id=name.lower(), t=labels.get(name, name.replace("_", " ")), h=head, b=body))
    toc = " · ".join('<a href="#%s">%s</a>' % (n.lower(), labels.get(n, n)) for n in sheets)
    body = ('<p class="eyebrow">Data</p><h1>Key Indicators</h1><p class="lede">The numbers behind the briefs, from the Key Indicators workbook (%s). '
            'Values are as published; tildes mark approximate figures.</p>' % html.escape(os.path.basename(wb_path)) +
            '<div class="charts">%s</div><p class="toc">Tables: %s</p>%s' % ("".join(charts), toc, "".join(tables)))
    return page("indicators", "Key Indicators", body, "Oil, gas, power, price and macro indicators for October 2026.")


def build_section(src, folder, slug, name):
    path = latest(glob.glob(os.path.join(src, folder, "*_Analysis_*.md")))
    if not path:
        return None, None
    with open(path, encoding="utf-8") as f:
        md = f.read()
    title, rest = split_title(md)
    body = '<p class="eyebrow">Section brief · {f}</p><h1>{t}</h1><article class="prose">{b}</article>'.format(
        f=html.escape(folder[:2]), t=html.escape(title), b=fix_links(md_to_html(rest)))
    return page(slug, name, body, title), title


def build_review(src):
    path = latest(glob.glob(os.path.join(src, REVIEW_GLOB)))
    with open(path, encoding="utf-8") as f:
        md = f.read()
    title, rest = split_title(md)
    rest = re.sub(r"Key numbers are in `[^`]+`\.", "Key numbers are on the [Key Indicators](indicators.html) page.", rest)
    body = '<p class="eyebrow">Monthly review</p><h1>{t}</h1><article class="prose">{b}</article>'.format(
        t=html.escape(title), b=fix_links(md_to_html(rest)))
    return page("review", "Market Review", body, title), md


def build_home(review_md, section_titles):
    def grab(heading):
        m = re.search(r"## %s\n(.*?)(?=\n## |\Z)" % re.escape(heading), review_md, re.S)
        return m.group(1).strip() if m else ""

    five = fix_links(md_to_html(grab("Five things that matter")))
    watch = md_to_html(grab("Watch list (next 30 days)"))
    stats = [("100.7", "mb/d", "Global oil supply 2026, down 5.8 mb/d (IEA)"),
             ("−2.6", "mb/d", "Oil demand change 2026, first fall since 2020"),
             ("71.6%", "", "EU gas storage at end-Q3, going into winter"),
             ("$329", "/MW-day", "PJM capacity price 2026/27, driven by data centres")]
    tiles = "".join('<div class="stat"><div class="num">%s<span>%s</span></div><div class="cap">%s</div></div>' % (html.escape(a), html.escape(b), html.escape(c)) for a, b, c in stats)
    cards = "".join('<a class="card" href="{s}.html"><span class="no">{n}</span><h3>{t}</h3><p>{d}</p></a>'.format(
        s=slug, n=folder[:2], t=html.escape(name), d=html.escape(desc)) for folder, slug, name, desc in SECTIONS if slug in section_titles)
    body = """
<section class="hero">
  <p class="eyebrow">October 2026 edition</p>
  <h1>Global energy markets, across the value chain</h1>
  <p class="lede">Independent research on the 2026 supply shock: from upstream production and Gulf chokepoints to refining, power, policy and prices.</p>
  <p><a class="btn" href="review.html">Read the market review</a> <a class="btn ghost" href="indicators.html">See the key indicators</a></p>
</section>
<div class="stats">{tiles}</div>
<section><h2>Five things that matter</h2><div class="prose">{five}</div></section>
<section><h2>Section briefs</h2><div class="cards">{cards}</div></section>
<section><h2>Watch list</h2><div class="prose">{watch}</div></section>
""".format(tiles=tiles, five=five, cards=cards, watch=watch)
    return page("index", "Home", body, "Independent research on global energy markets across the value chain.")


def build_about():
    body = """<p class="eyebrow">About</p><h1>About this research</h1>
<article class="prose">
<p><strong>[Your name]</strong> · <em>[One line about you, e.g. energy market analyst focused on oil, gas and power.]</em></p>
<p>This site publishes my monthly analysis of global energy markets. It follows the value chain: market foundations and data, upstream production, midstream logistics, downstream refining and end use, regional markets and geopolitics, policy and carbon, and financial analysis and trading.</p>
<h2>Method</h2>
<ul>
<li>Figures come from public releases (IEA, EIA, OPEC, IMF, OIES, Ember and others) and press coverage of them. Each brief lists its sources.</li>
<li>Lines marked <em>inferred</em> are my own analytical judgement, not published data.</li>
<li>Prices are indicative snapshots. Check them against exchange data before relying on them.</li>
</ul>
<h2>Contact</h2>
<p><em>[Add your email or LinkedIn here.]</em></p>
</article>"""
    return page("about", "About", body, "About this energy research.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(MASTER, "ENERGY ANALYSIS"))
    ap.add_argument("--out", default=SITE_DIR)
    a = ap.parse_args()
    out = {}
    titles = {}
    for folder, slug, name, _ in SECTIONS:
        html_text, title = build_section(a.src, folder, slug, name)
        if html_text:
            out[slug] = html_text
            titles[slug] = title
    out["review"], review_md = build_review(a.src)
    out["index"] = build_home(review_md, titles)
    out["about"] = build_about()
    wb = latest(glob.glob(os.path.join(a.src, WORKBOOK_GLOB)))
    if wb:
        out["indicators"] = build_indicators(wb)
    for slug, text in out.items():
        with open(os.path.join(a.out, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(text)
    print("Wrote %d pages to %s" % (len(out), a.out))


if __name__ == "__main__":
    main()
