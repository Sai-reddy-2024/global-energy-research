# Global Energy Analysis website

A static website built from the research in `../ENERGY ANALYSIS`. It needs no server: open `index.html` in a browser.

## Pages
- `index.html`: home, with headline numbers, the five key takeaways, section cards and the watch list
- `review.html`: the Global Energy Market Review
- `indicators.html`: charts and tables from the Key Indicators workbook
- `foundations.html` to `finance.html`: the seven section briefs (01 to 07)
- `about.html`: about page. **Fill in the bracketed placeholders (name, bio, contact) before publishing.**

## Updating after new research
The pages are generated from your briefs. After you add new briefs or a new workbook version, run this from the Master Energy folder:

    pip3 install markdown openpyxl
    python3 Website/_build/build_site.py

It picks up the newest dated brief in each section folder, the newest market review and the newest Key Indicators workbook. It only reads `ENERGY ANALYSIS` and never changes it. The MM course material is not used.

## Publishing (optional)
Upload this `Website` folder to GitHub Pages, Netlify (drag and drop) or any static host.
