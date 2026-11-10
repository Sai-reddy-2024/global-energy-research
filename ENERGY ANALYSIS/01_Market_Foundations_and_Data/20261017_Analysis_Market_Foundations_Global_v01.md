# 01 Market Foundations and Data: October 2026 brief

Prepared 2026-10-17 from the latest public releases (IEA OMR Oct-26, EIA STEO Oct-26, OPEC MOMR Oct-26, IMF WEO Oct-26, OIES Gas Review Oct-26). Figures are as published; anything marked *inferred* is my own reading.

## Big picture

2026 is a supply-shock year. The US–Israel war on Iran began on 28 Feb 2026 and the Strait of Hormuz has been closed or restricted for more than seven months. Gulf oil, product and LNG exports collapsed in Q2 and are only partly back. The result is the largest oil supply loss on record, a demand contraction (the first since 2020), record freight and diesel prices, and a global LNG deficit heading into winter.

## 01.1 Raw data downloads: what to pull first

| Release | Latest | Why it matters now | Save to |
|---|---|---|---|
| IEA Oil Market Report | 14 Oct 2026 | Supply/demand, Hormuz flow estimates, stocks | 01.1/IEA |
| EIA STEO | 6 Oct 2026 | Brent path, shut-in assumptions, US gas/power | 01.1/EIA |
| OPEC MOMR | 12 Oct 2026 | Secondary-source output; demand cut to +0.4 mb/d | 01.1/OPEC |
| OIES Quarterly Gas Review #34 | Oct 2026 | LNG supply loss, EU storage | 01.1/Other_Sources |
| IMF WEO | Oct 2026 | Macro and oil price assumptions | 01.3 |
| IEA Electricity Mid-Year Update | Jul 2026 | Power demand, coal/gas switching | 04.2 |
| IEA World Energy Outlook 2026 | Due Oct/Nov 2026 | Long-term scenarios (watch for release) | 01.5 |

None of these files are downloaded yet; links are in the Source Log.

## 01.2 Energy flows (Sankey notes)

The flow picture to chart this year is Gulf exports and their bypass routes, not the usual primary-to-final-use Sankey:
- Gulf crude exports in September: **13.9 mb/d**, over 75% of pre-war. Of that, **10.9 mb/d** went via Hormuz and **5.6 mb/d** via bypass pipelines (IEA OMR Oct-26; the two overlap, so treat them as separate measures).
- Middle East product exports: **1.9 mb/d** vs 4.7 mb/d pre-war. LPG exports: **0.67 mb/d** vs 1.5 mb/d pre-war.
- Qatar/UAE LNG: just over **2 bcm/month** vs more than 10 bcm/month pre-crisis (OIES).
- Suggested chart: pre-war vs Sep-26 Sankey of Gulf crude, products and LNG to Asia, Europe and others. Build it from the IEA OMR tables once downloaded.

## 01.3 Macro indicators (IMF WEO Oct-26)

| | 2025 | 2026 | 2027 |
|---|---|---|---|
| World GDP growth | 3.5% | 3.1% | 3.4% |
| United States | – | 2.3% | 2.3% |
| Euro area | 1.2% | 1.1% | 1.2% |
| China | 5.0% | 4.5% | 4.0% |
| India (calendar year) | – | 7.4% | 7.0% |
| World headline inflation | 4.1% | 4.7% | 4.1% |
| IMF oil price assumption ($/bbl) | 67.74 | 95.74 | 87.39 |

The IMF says AI investment is offsetting the oil shock, but that "buffers are becoming increasingly limited". Energy is pushing up inflation in the US (3.6% in 2026), the euro area (3.1%) and India (5.0%).

## 01.4 Supply/demand balances

| Agency (Oct-26) | 2026 demand | 2026 supply | 2027 view |
|---|---|---|---|
| IEA | 102.4 mb/d, **−2.6 mb/d y/y** | 100.7 mb/d, **−5.8 mb/d** | Demand +~2 mb/d, still 0.62 mb/d below 2025; supply +7.7 mb/d |
| OPEC | Growth cut to **+0.4 mb/d** (from +1.4) | – | Some lost 2026 demand expected to return in 2027 |
| EIA | – | Gulf shut-ins 4.8 mb/d in Sep, 4.5 in 4Q26, ~2.7 in 1Q27 | Stocks rebuild through 2027 |

- **Inventories:** global observed stocks are **509 mb below end-February**. September draw was 10 mb (on-land −113 mb, oil on water +103 mb). China accounted for 78% of the non-OECD crude draw. EIA estimates draws of 1.9 mb/d in 3Q26 and 0.7 mb/d in 4Q26.
- **Distillates are the tightest part of the barrel.** OECD gasoil stocks were 565 mb in July, the lowest since Nov-23. US East Coast distillate stocks were 32% below the 5-year average in September (EIA).
- **The agencies disagree.** The IEA sees demand falling sharply, while OPEC still shows growth. The roughly 3 mb/d gap is the main forecasting risk to track monthly.

## 01.5 Scenarios and outlooks

- Short-term: EIA puts Brent at $105 in 4Q26, $87 in 2Q27 and $74 in 4Q27, with most Gulf output back by end-2Q27. This "normalisation" case depends on Hormuz reopening.
- *Inferred:* use three cases for 07.3 models:
  1. **Reopening:** Hormuz normalises by 2Q27 and Brent falls to the mid-$70s (EIA path).
  2. **Prolonged restriction:** flows stay near Sep-26 levels through 2027 and Brent holds at $95–110.
  3. **Escalation:** bypass pipelines are hit again and Brent goes above $130 (the 15 Sep spike reached $131).
- The IEA WEO-2026 (STEPS/APS/NZE) is due shortly. Log it when published.

## 01.6 Weather and climate

- EIA expects winter 2026–27 to be about **3% warmer** than the 10-winter average for the US.
- OIES flags a possible "Super El Niño" winter, which could save Europe about **12 bcm (−5%)** of gas demand. This is the main upside risk for the European gas balance.
- US gas storage should be **3,850 bcf** at end-October, about 2% above the 5-year average. The US enters winter well supplied while Europe does not.

## Sources
- [IEA Oil Market Report, Oct 2026](https://www.iea.org/reports/oil-market-report-october-2026)
- [EIA STEO, Oct 2026](https://www.eia.gov/outlooks/steo/pdf/steo_text.pdf)
- [OPEC demand cut, Nairametrics, 12 Oct 2026](https://nairametrics.com/2026/10/12/opec-slashes-2026-oil-demand-forecast-by-over-70-to-400000-bpd/)
- [IMF WEO Oct 2026, SteelOrbis summary](https://www.steelorbis.com/steel-news/latest-news/imf-forecasts-global-economic-growth-to-slow-to-31-percent-in-2026-amid-energy-price-pressures-1483524.htm)
- [OIES Quarterly Gas Review #34](https://www.oxfordenergy.org/wpcms/wp-content/uploads/2026/10/OIES-Quarterly-Gas-Review-Issue-34.pdf)
- [2026–2028 world oil market chronology (Wikipedia)](https://en.wikipedia.org/wiki/2026%E2%80%932028_world_oil_market_chronology)
