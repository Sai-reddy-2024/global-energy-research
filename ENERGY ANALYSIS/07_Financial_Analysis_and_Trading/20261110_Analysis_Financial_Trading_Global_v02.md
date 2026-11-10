# 07 Financial Analysis and Trading: November 2026 update

Prepared 2026-11-10. Updates the 17 Oct brief with prices and futures positioning pulled through free APIs (EIA, FRED, CFTC). Background that has not changed is in the v01 brief. Verify prices against exchange data before trading or modelling. *Inferred* marks my own reading.

New data file: `07.1_Commodity_Pricing/20261110_Analysis_Energy_Prices_and_Positioning_Global_Daily_v01.xlsx` (daily, weekly and monthly prices plus CFTC managed-money positions since 2022).

## 07.1 Commodity pricing
| Benchmark | Latest | vs a year ago | Source |
|---|---|---|---|
| Brent spot | $107.03 (3 Nov) | +65% | EIA |
| Brent futures | ~$90–93 (9–10 Nov) | | Saxo / TradingNEWS |
| WTI spot | $99.64 (3 Nov) | +62% | EIA |
| Henry Hub spot | $2.63/MMBtu (3 Nov) | −21% | EIA |
| TTF | ~€82/MWh, ~$27/MMBtu (10 Nov) | +164% | Morgan Downey |
| JKM | ~$31/MMBtu (10 Nov) | +182% | Morgan Downey |
| EU ETS Dec-26 | €86.66 (7 Nov) | | AlanChand / energate |
| NYH ULSD | $4.82/gal, $203/bbl (3 Nov) | +94% | EIA |
| US retail diesel | $6.13/gal (9 Nov) | +60% | EIA via FRED |
| Australian thermal coal | $154/t (Sep avg) | +37% | IMF via FRED |
| Copper | $14,473/t (Sep avg) | +45% | IMF via FRED |
| Uranium | $72.5/lb (Sep avg, spot) | +15% | IMF via FRED |

- EIA spot data lag about a week, which is why Brent spot ($107 on 3 Nov) sits well above futures after the 9–10 Nov sell-off.

- **Forecast deck (EIA Nov STEO):** Brent $109 in 4Q26, $95 in 1Q27 and $77 in 4Q27. Annual averages are $97 for 2026 and $86 for 2027. Henry Hub is $3.37 in 2026 and $2.88 in 2027.

## Futures positioning (CFTC, 3 Nov)
| Market | Managed money net | Net as % of open interest | A year earlier |
|---|---|---|---|
| WTI (NYMEX) | +21.7k | +1.1% | +7.7k |
| Henry Hub gas | −225k | −13.4% | −44k |
| RBOB gasoline | +87k | +27.2% | +62k |
| NY Harbor ULSD | +7.0k | +2.9% | +33k |

- *Inferred:* funds are barely long crude despite $100 oil, so the drop on deal hopes is not a crowded-long unwind. They are heavily short US gas, matching EIA's 16% cut to its winter Henry Hub forecast. Brent positioning is reported by ICE, not CFTC, and is not included.

## 07.2 Corporate intelligence
- Q3-26 results are covered in the 02 brief: ExxonMobil's earnings doubled while volumes fell slightly, and Shell's Integrated Gas volumes fell 17% in 9M26.
- Market caps for about 55 listed energy and mining companies (9–10 Nov) are in the 02 company workbook.

## 07.3 Investment models
- The three-case table from the October brief still holds. *Inferred:* the Nov STEO path ($77 by 4Q27) sits at the low end of the **reopening** case, and the strip after the sell-off points the same way.
- For DCFs, refresh the near-term strip after the 29 Nov OPEC+ meeting.

## Sources
- EIA API v2 spot prices, FRED (DCOILBRENTEU, DHHNGSP, GASDESW, IMF commodity series) and CFTC disaggregated Commitments of Traders (Socrata API), pulled 10 Nov 2026. Raw CSVs are in 01.1/EIA/API_20261110 and 01.1/Other_Sources/API_20261110.
- [Morgan Downey commodity news, 10 Nov](https://commoditynews.morgandowney.com/news/2026-11-10) · [TradingNEWS, 9 Nov](https://www.tradingnews.com/news/brent-93-usd-extends-16-perent-weekly-collapse-as-iran-deal-heads-to-trump) · [AlanChand EUA quote](https://alanchand.com/en/energy) · [energate](https://www.energate-messenger.com/news/268628/euas-hold-steady-above-90-euros-per-tonne-of-co2)
