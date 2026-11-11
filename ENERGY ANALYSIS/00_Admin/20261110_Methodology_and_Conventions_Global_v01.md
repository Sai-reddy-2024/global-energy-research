# Methodology and conventions

Prepared 10 Nov 2026. One page on how numbers in this project are chosen, labelled and checked. It applies to the briefs, the models, the weekly gas note and the website.

## 1. Prices: always say which price
Every price carries its basis. Use these labels, in this order of preference:

| Label | What it is | Typical source here | Use it for |
|---|---|---|---|
| **Settlement (front-month)** | Official daily close of the nearest futures contract | Exchange settlement as reported by the press | "Where the market is today" |
| **Front-month, intraday** | A quote during the day | Press, market wraps | Only when no settlement exists yet; say "about" |
| **Spot** | Physical price for prompt delivery (e.g. EIA Brent spot, Henry Hub spot) | EIA, FRED | History and physical spreads. EIA spot data lag about a week |
| **Monthly average** | Average of daily prices for a calendar month | World Bank Pink Sheet, IMF, EIA | Month-on-month and year-on-year comparisons |
| **Forecast** | An agency or own forecast, for a stated period | EIA STEO, own models | Scenario framing, always with the forecaster and date |

Rules:
- Never put two bases side by side without labels. "Brent $90 (front-month, 10 Nov) vs $125 (October average, World Bank)" is fine; "$90 vs $125" is not.
- Year-on-year price changes compare the same basis on the same date (or the same month).
- The headline price on the website is the front-month settlement, with its date.

## 2. Units
| Market | Default unit | Conversions (00_Admin Reference_Tables) |
|---|---|---|
| Oil | mb/d for flows, mb for stocks, $/bbl | 1 t crude ≈ 7.33 bbl |
| European gas | TWh (GCV) for storage and flows, mcm/d in the weekly note, €/MWh for TTF | 1 bcm = 10.55 TWh |
| LNG | Mt (million tonnes) | 1 Mt ≈ 1.36 bcm ≈ 14.4 TWh ≈ 52 million MMBtu |
| Power | TWh, % of generation | |
| Gas prices across regions | $/MMBtu when comparing TTF, JKM and Henry Hub | 1 MWh = 3.412 MMBtu |

Storage percentages are gas in storage divided by the declared working gas volume (GIE AGSI+).

## 3. Data vintages
- Every figure has an **as-of date** (the date the data refers to) and a **pull date** (when it was downloaded, in the Source Log).
- Raw downloads are never edited; they sit in `01.1_Raw_Data_Downloads/<source>/API_<pull date>/`.
- Monthly agency data (JODI, EIA international) lag one to three months; say which month a number describes ("August, the latest month").
- Model outputs carry their **vintage**: the last day of data they start from (e.g. "storage model, vintage gas day 9 Nov 2026").

## 4. What *inferred* means
- **No label:** published by the cited source, unchanged apart from unit conversion or arithmetic you can repeat from the source file.
- ***Inferred:*** my reading of the data. It is a judgement, not a published fact, and should be possible to check later.
- **Estimate (E):** a number the project produced with a stated method (for example the 2026E LNG balance). The method sits in the workbook.
- **Model:** an output of a formula model under named assumptions. Never presented as a forecast unless it is entered in the call log.
- **Call:** a dated, checkable view in the call log, written and signed off by the author.

## 5. Numbers of record
Any figure used on the website or in more than one document lives once in `01.4_Supply_Demand_Balances/Numbers_of_Record.xlsx`, with its value, unit, basis, as-of date and source. Change it there first. Rows marked *Check* need a second source before publication.

## 6. Models
- Models use live formulas. Inputs are blue on yellow; everything else is calculated.
- Each model has a README sheet (logic, sources, limits) and is rebuilt from raw data by a script in `09_Code/Data_Pulls`.
- Current models: EU gas storage (01.4), global LNG balance (03.4).

## 7. Calls and the scorecard
- A call has a level, a date, a range, the reason, and the source that will settle it (`00_Admin/Call_Log.xlsx`).
- Calls are not edited after they go live. A changed view is a new call that says which one it replaces.
- Every call is graded on its date: *Hit* within the tolerance (3 points for storage), *Partial* inside the stated range, *Miss* outside.

## 8. Licences
- Free to republish with attribution: EIA, FRED, ENTSOG, GIE (AGSI+, ALSI), JODI, World Bank (CC-BY-4.0), IMF, Ember (CC-BY-4.0: always credit "Ember").
- Never republish: OilPriceAPI data, raw IEA, OPEC or Energy Institute downloads, and anything in the private education material.
