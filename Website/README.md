# Global Energy Analysis website

A static website built from the research in `../ENERGY ANALYSIS`. Open `index.html` in a browser; it needs no server.

## Pages
- `index.html`: the overview, set out like a pitch book. It has the headline view, live stat tiles, five calls, featured charts, the 2027 scenarios, a watch list and the latest research.
- `research.html`: list of the seven section briefs, plus the archive
- `foundations.html` to `finance.html`: the latest brief for each section with its charts. Earlier editions are kept as `<section>-YYYYMMDD.html`.
- `data.html`: all 19 charts (hover for values, "Show data" for tables) and the Key Indicators tables
- `companies.html`: the upstream company reference tables and a market-value chart
- `review.html`: the October market review (archive)
- `about.html`: about, method, and data sources and licences. **Fill in the bracketed placeholders (name, bio, contact).**

## Editing the overview
The headline, the five calls and the watch list are in `_build/homepage.md`. Edit that file, then rebuild.

## Rebuilding after new research
From the Master Energy folder:

    pip3 install markdown openpyxl
    python3 Website/_build/build_site.py

The build picks up the newest dated brief in each section and the newest version of each workbook. It only reads `ENERGY ANALYSIS`, never changes it, and does not use the MM course material.

## Data rules built into the build
- Nothing sourced from OilPriceAPI is published (its trial terms may not allow it). The build refuses to write a page that mentions it.
- Ember charts carry the CC-BY-4.0 attribution.
- Internal parts of the briefs (download status, to-do lists, gaps, file names) are left out.
