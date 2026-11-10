# 07 Financial Analysis and Trading: October 2026 brief

Prepared 2026-10-17. Prices are indicative snapshots from the sources cited. Verify them against exchange data before trading or modelling. *Inferred* marks my own reading.

## 07.1 Commodity pricing

| Benchmark | Latest | Context |
|---|---|---|
| Brent futures | ~$107/bbl (mid-Oct, IEA) | Up ~13% since early Sep. 2026 YTD range ~$60 to $131 (spot) |
| North Sea Dated | ~$134/bbl (IEA, at report time) | Sep average $116.89 (+$26 m/m) |
| WTI | ~$98/bbl (16 Oct, Buckhead) | Brent–WTI spread >$15 in Mar, the widest in 11 years |
| Urals | $90.7 (Sep average) | ~$23 discount to Brent |
| Henry Hub | ~$3.18/MMBtu (16 Oct) | EIA: $3.48 for 2026, $3.16 for 2027 |
| TTF | ~$24/MMBtu (5 Oct) | Mid-Sep peak $28. OIES model: >$30 by Mar-27 |
| JKM | ~$25.4/MMBtu (5 Oct) | Asia spot >65% above pre-crisis on average |
| EU ETS | €86.28/t (12 Oct auction) | Highest since January |
| Diesel | record >$200/bbl in Sep | EU cracks eased from ~$100 to ~$60 |

**Curve structure:**
- **Oil** is in steep backwardation. Dated ($134) sits well above front-month Brent ($107), which sits well above the EIA's 2027 average ($84). The market is pricing scarcity now and normalisation later.
- **TTF** is backwardated into 2028, with Q2-28 around $12 against $24 spot. The Q1-27 over Q2-27 spread is about $5, reflecting a winter scarcity premium.

**Forecast deck (EIA, Oct-26):** Brent $105 in 4Q26, $87 in 2Q27 and $74 in 4Q27. Annual averages are $96 for 2026 and $84 for 2027. The IMF assumes $95.74 and $87.39.

## 07.2 Corporate intelligence
- **Q2-26 results:** the eight majors earned about $93bn combined, against about $50bn in Q2-25. Aramco's net income rose 34% to more than $33bn, despite strikes on its assets. Chevron reported $12bn adjusted, including $8.2bn upstream. BP made $5.73bn, its best quarter since Q3-22.
- Q3-26 results arrive in late October and early November. Expect a further step-up, since Q3 Brent was higher and diesel cracks hit records (*inferred*).
- **Winners:** US upstream and LNG exporters, North American refiners, tanker owners (VLCC values up 18–61%), coal miners and Atlantic-basin producers.
- **Losers:** Asian and European utilities and chemicals companies with gas exposure, airlines, and Gulf assets under direct attack.
- **Deals:** LNG Canada Phase 2 FID (28 Sep). Texas LNG, Ksi Lisims and Sabine Pass expansion FIDs are pending.

## 07.3 Investment models: suggested setup
Link to the 01.5 scenarios. The following is *inferred* guidance, not a forecast.

| Assumption | Reopening (base) | Prolonged restriction | Escalation |
|---|---|---|---|
| Brent 2027 average | $80–85 | $95–110 | $120+ |
| Henry Hub 2027 | $3.0–3.2 | $3.5 | $4+ |
| TTF 2027 | $14–18 | $25–30 | $35+ |
| Gulf output back to pre-war | End-2Q27 | 2028 | Not before 2028 |
| Key trigger | US–Iran deal, Hormuz MOU | Stalemate persists | Bypass pipelines or Red Sea hit |

- Use the backwardated strip for the first 12–18 months and long-run deck prices after that (for example $70–75 Brent) for upstream DCFs.
- Run sensitivity on freight and insurance for any Gulf-sourced asset.
- For power and data-centre assets, the PJM capacity prices ($329/MW-day, and a 2027/28 shortfall) are the key revenue driver.

## Sources
- [IEA OMR Oct 2026](https://www.iea.org/reports/oil-market-report-october-2026) · [EIA STEO Oct 2026](https://www.eia.gov/outlooks/steo/pdf/steo_text.pdf)
- [Buckhead Energy prices, 16 Oct](https://www.buckheadenergy.com/oil-gas-prices) · [LNG Insights prices, 5 Oct](https://lnginsights.com/prices)
- [OIES Gas Review #34](https://www.oxfordenergy.org/wpcms/wp-content/uploads/2026/10/OIES-Quarterly-Gas-Review-Issue-34.pdf)
- [Oilprice: majors' windfall](https://oilprice.com/Energy/Energy-General/Oil-Majors-Reap-93-Billion-Windfall-From-the-Iran-War.html)
- [CBAM Guide ETS](https://cbamguide.com/news/2026-10-12-environment-council-ets-review-cbam-phase-in-carbon-price/) · [CREA Sep 2026](https://energyandcleanair.org/september-2026-monthly-analysis-of-russian-fossil-fuel-exports-and-sanctions/)
- [IMF WEO via SteelOrbis](https://www.steelorbis.com/steel-news/latest-news/imf-forecasts-global-economic-growth-to-slow-to-31-percent-in-2026-amid-energy-price-pressures-1483524.htm)
