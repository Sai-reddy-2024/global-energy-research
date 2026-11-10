# 01 Market Foundations and Data: November 2026 brief

Prepared 2026-11-10. Updates the 17 Oct brief with the Energy Institute Statistical Review 2026 baseline (full-year 2025), the October agency reports, the EIA's November STEO (10 Nov) and price moves to 10 Nov. Figures are as published; *inferred* marks my own reading. The numbers sit in the Key Indicators workbook (v02) in 01.4.

## Big picture

The 2025 baseline was a record year for every energy source, which is why the 2026 Hormuz shock hurt less than feared. Oil output grew 3.5% in 2025, much faster than demand (+1.3%), and China built stocks. The Americas now produce about 20% more oil than the Middle East; twenty years ago it was 20% less (EI).

Eight months into the Iran war, crude flows are close to pre-war levels but LNG and refined products are not. Brent futures fell about 22% from $117.64 on 30 Oct to around $90 on 10 Nov (October's spot average was $123.93, EIA) on hopes of a US–Iran deal after the midterms, while European diesel is still near $175/bbl and TTF near €81/MWh.

## 01.1 Raw data downloads: status

After the network change on 10 Nov, the EIA STEO tables and report and the Dallas Fed survey charts were downloaded unaltered into 01.1 (EIA and Other_Sources). EI, OPEC, IEA and SEC still refuse automated downloads at the site, and Ember's file server is not reachable, so these still need a manual download. Every source is logged in the Source Log with its URL and target folder. Pull these first:

| Release | Published | Save to |
|---|---|---|
| EI Statistical Review 2026 workbook | 30 Jun 2026 | 01.1/Energy_Institute |
| OPEC MOMR (Oct; Nov due 11 Nov) | 13 Oct 2026 | 01.1/OPEC |
| OPEC Annual Statistical Bulletin 2026 | 29 Apr 2026 | 01.1/OPEC |
| EIA STEO November | 10 Nov 2026 | done: 01.1/EIA |
| IEA Global Gas Security Review 2026 | Oct 2026 | 01.1/IEA |
| USGS Mineral Commodity Summaries 2026 data release | Feb 2026 | 02.5 |
| IEA World Energy Outlook 2026 | due ~18–23 Nov | 01.5 |

## 2025 baseline (EI Statistical Review 2026)

| Indicator | 2025 | Change |
|---|---|---|
| Total energy supply | >600 EJ | +1.7%; fossil fuels 86% |
| Oil production | 100.6 mb/d | +3.5% |
| Oil consumption | 103 mb/d | +1.3% |
| Gas production | 4,196 bcm | +1.6% (US 1,074 bcm = 26%) |
| LNG trade | 495 bcm | +6.5% |
| Coal production | 180.8 EJ | flat; top five = 83% |
| Battery storage capacity | 302 GW | +66% |
| Data centre power use | 788 TWh | +20% |

Renewables were the largest source of supply growth for the first time outside a recession, with solar 71% of that growth.

## 01.4 Supply/demand balances: October agency views

| Agency | 2026 demand | 2027 demand | Call on OPEC+ crude, 4Q26 |
|---|---|---|---|
| IEA (14 Oct) | 102.4 mb/d, −2.6 | ~104.4, +2.0 | 35.7 mb/d |
| OPEC (13 Oct) | 105.7 mb/d, +0.2 | 108.3, +2.6 | 45.2 mb/d |
| EIA (6 Oct) | 102.4 mb/d, −2.0 | – | 33.3 mb/d |

- The gap between OPEC and the IEA/EIA is now about 3 mb/d on demand and 10–12 mb/d on the call on OPEC+ crude. OPEC treats lost 2026 demand as deferred to 2027; the IEA treats much of it as destroyed.
- **OPEC+ output is recovering.** OPEC+ crude rose 0.9 mb/d to 39.1 mb/d in September, led by Saudi Arabia (+0.74 to 8.0 mb/d). A Bloomberg survey puts OPEC at 22.8 mb/d in October, about 88% of February. The UAE left OPEC and OPEC+ on 1 May 2026.
- **Spare capacity is almost gone** as output recovers: the IEA puts effective OPEC spare capacity at only ~0.16 mb/d versus September output.
- **US:** crude output ~14.0 mb/d (weekly, end-Oct); commercial crude stocks 409.8 mb; SPR 282.2 mb after the IEA-coordinated release.
- **Gas:** global LNG output fell 6% (~20 bcm) in Mar–Oct; the IEA expects Middle East gas output down 18% (~140 bcm) in 2026, the steepest fall on record. US dry gas output is heading for a second record (112.2 bcf/d in 2026).

## EIA November STEO (10 Nov)
| Item | Nov STEO | Oct STEO |
|---|---|---|
| Brent 4Q26 | $109/b (Nov–Dec ~$100) | $105 |
| Brent 2026 / 2027 | $97 / $86 | $96 / $84 |
| Brent 4Q27 | $77 | $74 |
| Henry Hub 2026 / 2027 | $3.37 / $2.88 | $3.48 / $3.16 |
| World oil demand 2026 / 2027 | 102.4 (−2.0) / 104.4 (+2.0) mb/d | 102.4 (−2.0) |
| US crude output 2026 / 2027 | 13.9 / 14.3 mb/d (record) | 13.9 / 14.3 |
| US LNG exports 2027 | 19.0 bcf/d (+26% vs 2025) | 19 |

- The EIA expects Middle East output outside Iran back to pre-war levels by mid-2027, and a large global stock build in 2027 (~4 mb/d), which is what pulls Brent into the $70s.
- US commercial crude stocks were 410 mb at end-October, the lowest for the time of year since 2014. Diesel stays expensive: $5.03/gal retail in 2027, 12% above last month's forecast.
- *Inferred:* the EIA's 2027 path is closest to the **reopening** case; its oversupply call is much bigger than OPEC's, which sees 2027 demand at 108.3 mb/d.

## 01.5 Scenarios and outlooks

- Three-case framework from the October brief still holds. *Inferred:* the post-midterm price drop moves weight toward the **reopening** case, but the IEA's "fragile recovery" and continued attacks near Hormuz (nine in 29 Oct–3 Nov) keep the **prolonged restriction** case live.
- Long-term views are diverging: TotalEnergies (2 Nov) pulled its oil demand peak forward to 2035–2040, OPEC's World Oil Outlook (Jun) still sees 124 mb/d by 2050, and the IEA's Renewables 2026 (6 Nov) expects ~4,800 GW of new renewables in 2026–31. The IEA WEO-2026 is due this month.

## What to update next

1. OPEC MOMR November (11 Nov): refresh the agency comparison. EIA's next STEO is 8 Dec.
2. IEA OMR November and WEO-2026.
3. Replace secondary transcriptions of EI tables with the official workbook once downloaded.

## Sources
- [EIA STEO November 2026](https://www.eia.gov/outlooks/steo/) (tables and report saved in 01.1/EIA) · [Dallas Fed Energy Survey](https://www.dallasfed.org/research/surveys/des)
- [Energy Institute Statistical Review 2026](https://www.energyinst.org/statistical-review) · [EI country tables via energyfactbook](https://energyfactbook.com/world/producers/) · [KPMG EI summary](https://assets.kpmg.com/content/dam/kpmgsites/au/pdf/2026/statistical-review-of-world-energy.pdf)
- [IEA OMR Oct 2026](https://www.iea.org/reports/oil-market-report-october-2026) · [IEF comparison of monthly reports, 15 Oct 2026](https://www.ief.org/news/comparative-analysis-of-monthly-reports-on-the-oil-market-80)
- [OPEC MOMR Oct 2026 via Argus](https://www.argusmedia.com/en/news-and-insights/latest-market-news/2890051-opec-sees-china-oil-demand-falling-in-2026) · [OPEC secondary sources via The Edge](https://edgeconsultancykw.com/opec-crude-output-october-2026-saudi-arabia-pre-war-levels/)
- [IEA Global Gas Security Review 2026](https://www.iea.org/files/42bb838f-d20d-4815-8554-32146033967d/GlobalGasSecurityReview2026.pdf) · [IEA Renewables 2026](https://www.iea.org/news/energy-security-concerns-spur-faster-renewables-growth-across-a-widening-constellation-of-countries)
- [Saxo market note, 10 Nov 2026](https://www.home.saxo/en-gb/content/articles/macro/market-quick-take---wall-street-rebounds-and-brent-slides-below-usd-92---10-november-2026-10112026) · [Oil Authority on EIA weekly data](https://oilauthority.com/news/brent-94-29-wti-88-54-midterm-result-iran-peace-hopes)
- [TotalEnergies Energy Outlook coverage](https://forbesmiddleeast.com/industry/energy/totalenergies-says-hormuz-crisis-could-accelerate-energy-transition)
