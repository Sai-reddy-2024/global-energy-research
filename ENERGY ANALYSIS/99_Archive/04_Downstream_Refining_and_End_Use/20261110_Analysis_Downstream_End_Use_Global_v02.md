# 04 Downstream Refining and End Use: November 2026 update

Prepared 2026-11-10. Updates the 17 Oct brief with EIA data pulled through the API on 10 Nov. Background that has not changed is in the v01 brief. *Inferred* marks my own reading.

New data files:
- `04.1_Refining_and_Processing/20261110_Analysis_Refining_Margins_US_Monthly_v01.xlsx`: weekly runs and demand, daily spot prices, and a monthly 3-2-1 crack.
- `04.2_Power_Generation_and_Grids/20261110_Analysis_US_Power_Generation_US_Monthly_v01.xlsx`: generation by fuel and share, retail prices and sales.

## 04.1 Refining and processing
- **US refiners are running hard:** utilisation was 94.5% in the week to 30 Oct, against 86% a year earlier. Gross inputs were 17.1 mb/d (+9% y/y).
- **NY Harbor 3-2-1 crack (NY Harbor gasoline and ULSD against WTI Cushing, monthly average):**

| Month | WTI | NYH gasoline | NYH ULSD | 3-2-1 crack |
|---|---|---|---|---|
| Aug-26 | $83.9 | $135.0 | $178.6 | $65.6 |
| Sep-26 | $97.1 | $144.2 | $208.1 | $68.4 |
| Oct-26 | $102.1 | $127.5 | $207.9 | $52.2 |
| Nov-26 (to 3 Nov) | $99.9 | $112.9 | $199.5 | $41.9 |

- Cracks are easing from September's records but are still several times normal levels (*inferred*: a typical pre-war crack was $20–30). Diesel is the tight product: NYH ULSD is about $92/bbl above Brent, and US distillate demand is up 20% y/y while stocks are 11% lower.
- US retail diesel was $6.13/gal on 9 Nov (+60% y/y), and gasoline $4.00 (+31%) (EIA via FRED).

## 04.2 Power generation and grids
- **US generation, Aug-26:** 449 TWh (+6.8% y/y). Gas 46.7% share, coal 15.8%, nuclear 15.7%, utility solar 8.6%, wind 7.4%, hydro 4.1%.
- Solar (+20% y/y) and wind (+20%) supplied most of the growth. Gas rose 8% even at higher fuel prices, because demand grew faster than renewables could cover.
- **World, 2025 (Ember):** generation rose 2.8% to 31,925 TWh. Coal fell to 33.2% and gas to 21.7%. Solar (8.8%) overtook wind (8.5%) and matched nuclear (8.8%). Solar output grew 30% in a year (2,161 to 2,807 TWh).
- **Mix by market, 2025 (Ember):** China coal 54.8%, wind and solar 21.9%; India coal 70.9%; US gas 40.0%, nuclear 17.4%; EU nuclear 23.3%, wind and solar 30.2%; Middle East gas 68.7%. Sheets `Ember_Generation_TWh` and `Ember_Share_%` cover ten regions since 2015.
- US retail electricity averaged 14.9 c/kWh in August (+5.1% y/y). Industrial prices rose most (+7.3%). Retail sales were up 4.6% y/y, which is consistent with data-centre load.

## 04.3 Demand sectors
- **US oil demand proxy** (total product supplied) was 22.0 mb/d in the week to 30 Oct (+8% y/y). One-week figures are volatile; check the four-week average before relying on it.
- No new global sector data since October. Next updates: IEA WEO-2026 (due ~18–23 Nov) and the IEA November OMR.

## 04.4 Energy storage
- No change since October. Battery storage capacity reached 302 GW in 2025 (+66%, EI), as noted in the 01 brief.

## Sources
- EIA API v2 (Weekly Petroleum Status Report, spot prices, Electric Power Monthly), pulled 10 Nov 2026. Raw CSVs are in 01.1/EIA/API_20261110.
- FRED (EIA retail gasoline and diesel), pulled 10 Nov 2026.
- [Ember yearly electricity data](https://ember-energy.org/data/yearly-electricity-data/) (CC-BY-4.0), downloaded 10 Nov 2026. Raw CSV is in 01.1/Other_Sources/API_20261110.
