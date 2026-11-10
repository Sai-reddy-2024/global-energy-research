# 04 Downstream Refining and End Use: November 2026 update

Prepared 2026-11-10 (v03: now leads with global and regional data; the US is one market among many). Updates the 17 Oct brief with EIA data pulled through the API on 10 Nov. Background that has not changed is in the v01 brief. *Inferred* marks my own reading.

US detail files (the global workbooks are in the next section):
- `04.1_Refining_and_Processing/20261110_Analysis_Refining_Margins_US_Monthly_v01.xlsx`: weekly runs and demand, daily spot prices, and a monthly 3-2-1 crack.
- `04.2_Power_Generation_and_Grids/20261110_Analysis_US_Power_Generation_US_Monthly_v01.xlsx`: generation by fuel and share, retail prices and sales.


## Global picture (new lead section)

Two new workbooks lead this section:
- `04.1_Refining_and_Processing/20261110_Analysis_Global_Refining_and_Oil_Demand_Global_Monthly_v01.xlsx`: oil consumption for every country (EIA, to 2024) and monthly refinery intake, refinery output and demand for total products, diesel/gasoil, gasoline, jet/kerosene, naphtha and LPG by country (JODI, Jan-25 to Aug-26).
- `04.2_Power_Generation_and_Grids/20261110_Analysis_Global_Power_Generation_Global_Monthly_v01.xlsx`: generation mix for the last 12 months for the world, six regions and the top 30 countries (Ember monthly, to Aug-26), monthly series for key markets, and EIA generation and capacity rankings.

The US refining and power workbooks stay as detail.

### Oil demand by country
**2024 (kb/d, EIA):**
| # | Country | 2024 | y/y | 5-yr | World share |
|---|---|---|---|---|---|
| 1 | United States | 20,464 | +0.9% | -0.4% | 19.8% |
| 2 | China | 16,370 | +2.4% | +17.1% | 15.9% |
| 3 | India | 5,599 | +4.0% | +13.8% | 5.4% |
| 4 | Russia | 3,802 | +2.2% | +2.4% | 3.7% |
| 5 | Saudi Arabia | 3,695 | +1.2% | +4.5% | 3.6% |
| 6 | Brazil | 3,269 | +3.4% | +8.4% | 3.2% |
| 7 | Japan | 3,163 | -4.1% | -15.8% | 3.1% |
| 8 | South Korea | 2,542 | +4.2% | -2.7% | 2.5% |
| 9 | Canada | 2,518 | +2.0% | -0.8% | 2.4% |
| 10 | Germany | 2,040 | -0.7% | -13.4% | 2.0% |

**Latest month, total product demand (kb/d, JODI):**
| Country | Latest (kb/d) | Month | y/y |
|---|---|---|---|
| United States | 21,168 | 2026-08 | +0.7% |
| China | 13,289 | 2026-08 | -20.3% |
| India | 5,612 | 2026-03 | +1.1% |
| Japan | 2,959 | 2026-08 | -3.6% |
| Saudi Arabia | 2,582 | 2026-08 | -7.4% |
| Korea | 2,498 | 2026-08 | -11.3% |
| Germany | 1,609 | 2026-08 | -26.9% |
| Indonesia | 1,548 | 2026-08 | -24.1% |
| Canada | 2,775 | 2026-08 | +11.0% |
| Mexico | 1,551 | 2026-07 | -0.4% |
| France | 1,368 | 2026-08 | -6.3% |
| United Kingdom | 1,352 | 2026-08 | +0.7% |

**Refinery intake, latest month (kb/d, JODI):**
| Country | Latest (kb/d) | Month | y/y |
|---|---|---|---|
| United States | 18,866 | 2026-08 | +7.3% |
| China | 13,247 | 2026-08 | -17.0% |
| Korea | 3,428 | 2026-08 | +1.1% |
| Japan | 2,527 | 2026-08 | -1.1% |
| Saudi Arabia | 2,297 | 2026-08 | -20.8% |
| Germany | 1,573 | 2026-08 | -21.5% |
| Canada | 2,485 | 2026-08 | +0.8% |

- *Inferred:* **the 2026 demand loss is Asian and European, not American.** China's product demand fell 20% y/y in August and its refinery runs 17%; Germany (−27%), Indonesia (−24%) and South Korea (−11%) also fell sharply. US demand was flat (+0.7%) and US runs rose 7% as US refiners exported into the product shortage. That is why the US data looked strong in the v02 brief.
- Germany's JODI figures are often revised heavily; treat the −27% as provisional.
- India's latest JODI month is March 2026, so India is missing from the war-period picture.

### Power generation mix, 12 months to Aug-26 (Ember)
| Area | 12m generation (TWh) | y/y | Coal | Gas | Nuclear | Hydro | Wind + solar | W+S change (pts) |
|---|---|---|---|---|---|---|---|---|
| World | 31,643 | +3.1% | 32.6% | 21.1% | 8.7% | 14.1% | 18.7% | +1.6 |
| Asia | 16,681 | +3.9% | 51.3% | 9.5% | 5.0% | 12.1% | 19.0% | +1.7 |
| North America | 5,248 | +3.1% | 13.5% | 37.3% | 16.6% | 11.6% | 18.8% | +1.5 |
| Europe | 4,956 | +1.6% | 12.7% | 22.9% | 19.3% | 16.3% | 22.9% | +2.1 |
| EU | 2,684 | +2.9% | 9.1% | 16.8% | 22.8% | 10.9% | 33.2% | +2.3 |
| Latin America & Caribbean | 1,868 | +2.3% | 3.8% | 24.1% | 2.0% | 41.1% | 19.0% | +1.1 |
| China | 10,654 | +4.3% | 54.1% | 3.1% | 4.6% | 12.9% | 23.0% | +1.6 |
| United States | 4,609 | +3.2% | 15.1% | 40.0% | 17.2% | 5.5% | 20.2% | +1.7 |
| India | 1,972 | +6.1% | 67.6% | 1.2% | 3.0% | 8.5% | 18.8% | +3.5 |
| Russia | 1,150 | −0.2% | 17.0% | 44.0% | 19.3% | 18.1% | 0.6% | 0.0 |
| Japan | 914 | −2.2% | 28.9% | 29.5% | 10.1% | 7.1% | 11.9% | +0.4 |
| Brazil | 763 | +0.8% | 1.4% | 7.7% | 2.0% | 52.8% | 28.6% | +1.6 |
| Germany | 502 | +5.6% | 18.9% | 16.2% | 0.0% | 3.1% | 48.2% | +3.7 |
| United Kingdom | 283 | +3.5% | 0.0% | 30.4% | 11.4% | 2.0% | 40.8% | +5.5 |
| Australia | 244 | +1.2% | 48.3% | 6.2% | 0.0% | 5.8% | 39.5% | +3.5 |

- World generation grew 3.1%. Wind and solar reached 18.7% of the global mix, up 1.6 points in a year, and solar alone (9.8%) is now above wind (8.9%) and nuclear (8.7%).
- Coal still supplies a third of world power and over half of Asia's. India (67.6% coal) is growing fastest (+6.1%) and adding wind and solar fastest (+3.5 points).
- Gas-heavy systems are the ones exposed to the LNG shock: Japan (29.5% gas), the UK (30.4%), Italy (47.9%), Taiwan (51.1%) and Bangladesh (47.1%).
- The Middle East and Africa are missing from the monthly regional table because too few of their countries report monthly; use the annual EIA ranking for them.

## 04.1 Refining and processing (US detail)
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

## 04.3 Demand sectors (US detail)
- **US oil demand proxy** (total product supplied) was 22.0 mb/d in the week to 30 Oct (+8% y/y). One-week figures are volatile; check the four-week average before relying on it.
- No new global sector data since October. Next updates: IEA WEO-2026 (due ~18–23 Nov) and the IEA November OMR.

## 04.4 Energy storage
- No change since October. Battery storage capacity reached 302 GW in 2025 (+66%, EI), as noted in the 01 brief.

## Sources
- EIA API v2 (Weekly Petroleum Status Report, spot prices, Electric Power Monthly), pulled 10 Nov 2026. Raw CSVs are in 01.1/EIA/API_20261110.
- FRED (EIA retail gasoline and diesel), pulled 10 Nov 2026.
- [Ember yearly electricity data](https://ember-energy.org/data/yearly-electricity-data/) (CC-BY-4.0), downloaded 10 Nov 2026. Raw CSV is in 01.1/Other_Sources/API_20261110.
- EIA international data (API v2, annual, all countries and regions), JODI Oil World Database (monthly, free with attribution) and Ember monthly electricity data (CC-BY-4.0), pulled 10 Nov 2026. Raw files are in 01.1.
