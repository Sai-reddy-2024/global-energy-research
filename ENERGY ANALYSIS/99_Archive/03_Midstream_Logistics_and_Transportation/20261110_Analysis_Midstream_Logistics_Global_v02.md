# 03 Midstream Logistics and Transportation: November 2026 update

Prepared 2026-11-10. Updates the 17 Oct brief with EIA weekly data (week to 30 Oct), EU storage data and news to 10 Nov. Background that has not changed is in the v01 brief. *Inferred* marks my own reading.

New data file: `03.3_Storage_and_Terminals/20261110_Analysis_US_Storage_and_Trade_US_Weekly_v01.xlsx` (EIA API: weekly stocks and trade since 2021, monthly crude imports by origin and LNG exports since 2019; GIE AGSI+: daily EU gas storage for the EU and seven countries since 2021, with a same-date comparison by year).

## 03.1 Maritime shipping and chokepoints
- **Hormuz:** a tanker was hit by a mine on 6 Nov, and US–Iran–mediator talks open in Abu Dhabi on 10–11 Nov. Brent futures fell about 16% in the week to 9 Nov on hopes of an interim deal (TradingNEWS).
- An agreed shipping lane near Oman for Iraqi exports is reported to be part of the US understanding with Iraq (TradingNEWS).
- *Inferred:* freight and war-risk insurance will lag any deal by weeks. Mines take time to clear, so tanker rates should fall more slowly than flat price.

## 03.3 Storage and terminals
| Stock (week to 30 Oct) | Level | vs a year ago |
|---|---|---|
| US commercial crude | 409.8 mb | −2.7% |
| US SPR | 282.2 mb | −31% (after the IEA-coordinated release) |
| Cushing | 27.3 mb | +19% |
| US gasoline | 209.0 mb | +1.4% |
| US distillate | 99.3 mb | −11% |
| US working gas | 3,801 bcf | −2.7% |

- **EU gas storage (GIE AGSI+, gas day 9 Nov):** 72.0% full, or 815 TWh, against 82.4% a year earlier. On 1 Nov it was 74.6%, the lowest for that date since at least 2021 (2021: 77.1%; 2022–24: 95–99%; 2025: 82.8%). Withdrawals have started early (IntelliNews).
- **By country (9 Nov):** Germany 58.5% (74.7% a year earlier), Netherlands 63.1%, Austria 64.0%, France 80.2%, Spain 80.6%, Italy 88.6%, Poland 97.1%.
- On 1 April 2026, after last winter, EU storage was 27.9%, below every year since 2021 apart from 2022 (26.5%). That means the system went into this winter from a weak base.
- The IEA's worst case (Gulf LNG back only from end-1Q27, cold winter) leaves EU stocks at 7% by end-March; its best case is 33% (via BNP Paribas).
- *Inferred:* US distillate stocks are the tightest product inventory in the US system, consistent with record diesel cracks (see 04).

## 03.4 Trade flows and sanctions
- **US crude exports** fell to 3.7 mb/d in the week to 30 Oct (−16% y/y). Weekly data are noisy, but high US refinery runs (94.5%) are keeping more crude at home.
- **US crude imports by origin (Aug-26):** Canada 3.83 mb/d (+3% y/y), Mexico 0.26 (−37%), Saudi Arabia 0.21 (−25%), Brazil 0.28, Colombia 0.17, Nigeria 0.04 (−77%).
- **US LNG exports** were 515 bcf in August (about 16.6 bcf/d), up 14% y/y. EIA forecasts 19 bcf/d in 2027.
- Russia and Iran sanctions: no change since October. Check CREA's October report when it is published.

## Gaps
- Tanker rates (Baltic Exchange) are paid data. Free proxies are listed tanker equities and press reports.

## Sources
- EIA API v2 (Weekly Petroleum Status Report, natural gas storage, petroleum imports by origin, LNG exports), pulled 10 Nov 2026. Raw CSVs are in 01.1/EIA/API_20261110.
- [GIE AGSI+](https://agsi.gie.eu/) EU gas storage, pulled 10 Nov 2026. Raw CSV is in 01.1/Other_Sources/API_20261110.
- [Morgan Downey commodity news, 10 Nov 2026](https://commoditynews.morgandowney.com/news/2026-11-10) · [IntelliNews on EU withdrawals](https://www.intellinews.com/europe-s-gas-withdrawals-hit-date-records-as-gazprom-s-deliveries-to-turkey-nearly-quadruple-482841/) · [BNP Paribas, 9 Nov 2026](https://economic-research.bnpparibas.com/html/en-US/2026-exposed-risks-European-market-11/9/2026,53921)
- [TradingNEWS, 9 Nov 2026](https://www.tradingnews.com/news/brent-93-usd-extends-16-perent-weekly-collapse-as-iran-deal-heads-to-trump)
