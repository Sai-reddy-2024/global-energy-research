# Global Energy Equity Screener: Framework

Agreed 10 Nov 2026 · Version 1 · Living copy: https://claude.ai/artifact/RqKBQu8sfKsCrqodZGppgn

## Purpose

The screener turns the global house view into a shortlist of about 10 listed energy names worth a full write-up, with the best long and short candidates ranked against their own peers.

- **It answers:** given our view on oil, gas and power, which companies are mispriced relative to peers and to that view?
- **It does not:** pick stocks on its own, replace a model, or rank an E&P against a utility. A high score only earns a name a closer look.
- **Success test:** each monthly run produces 3 to 5 names you can defend in an interview, plus one name you would short.

## Universe

The starting universe is about 100 to 120 listed companies worldwide, tagged by subsector and region so every comparison is like for like.

**Inclusion rules**

1. Listed on a major exchange, with market cap above $2bn.
2. Average daily traded value above $5m, so a position could actually be built.
3. At least half of revenue or EBITDA from energy. Conglomerates such as Reliance are tagged, not excluded.
4. One line per company, using the primary listing. ADRs are used only when the home listing has no data.

**Subsectors**

| Subsector | What drives it | Example names |
| --- | --- | --- |
| Integrated majors and NOCs | Oil and gas prices, refining margins, capital returns | ExxonMobil, Shell, TotalEnergies, Saudi Aramco, PetroChina, Petrobras |
| Exploration and production | Oil or gas price, volume growth, cost per barrel | ConocoPhillips, CNOOC, Woodside, Aker BP, Canadian Natural |
| Refining and marketing | Crack spreads, especially diesel | Valero, Neste, ENEOS, S-Oil, Indian Oil |
| LNG and gas | Global gas spreads (Henry Hub vs TTF and JKM), contract cover | Cheniere, Venture Global, Santos, Novatek (sanctions flag) |
| Midstream and pipelines | Volumes, fee contracts, interest rates | Enbridge, Williams, Kinder Morgan, Snam |
| Oilfield services and equipment | Upstream capex cycle, offshore activity | SLB, Baker Hughes, Tenaris, Saipem, Subsea7 |
| Coal | Thermal and met coal prices, Asian power demand | China Shenhua, Coal India, Whitehaven, Glencore |
| Uranium and nuclear | Uranium price, reactor restarts and new builds | Cameco, Kazatomprom, NexGen |
| Power and renewables | Power prices, data-centre demand, rates, subsidies | Iberdrola, Enel, RWE, Orsted, Vestas, NextEra |

**Regions:** North America, Europe, Middle East, Asia-Pacific, Latin America, Africa. Each company is tagged by where its assets sit, not where it is listed.

## Factor pillars

Five pillars score every company. A sixth, commodity sensitivity, is not scored. It is used to match names to the macro view.

| Pillar | Metrics | Why it matters in energy | Free data? |
| --- | --- | --- | --- |
| Valuation | EV/EBITDA (next 12 months), free-cash-flow yield, P/E, price to book | Energy trades on cash flow; earnings swing with prices | Yes |
| Balance sheet | Net debt / EBITDA, net debt / capital employed | Leverage decides who survives a price fall | Yes |
| Shareholder returns | Dividend yield, buyback yield, payout ratio | The main reason investors own the sector today | Partly; buybacks from cash flow statements |
| Quality | Return on capital employed, EBITDA margin, earnings stability over 5 years | Separates low-cost operators from price-takers | Yes |
| Momentum and sentiment | 3, 6 and 12-month returns, distance from 52-week high | Shows what the market already prices in | Yes |
| Commodity sensitivity (not scored) | 1-year beta to Brent, TTF and Henry Hub; correlation to the diesel crack | Tells you what the stock really bets on | Yes, computed from prices |

**Subsector KPIs (phase 2, from company reports)**

| Subsector | Key extra metrics |
| --- | --- |
| E&P and integrated | Production growth, reserve life, cash cost per barrel, cash breakeven Brent |
| Refining | Capacity, complexity, diesel yield, regional crack exposure |
| LNG | Contracted share of capacity, contract tenor, project start-up dates |
| Midstream | Fee-based share of EBITDA, contract life |
| Services | Backlog / revenue, international and offshore share |
| Power and renewables | Contracted or regulated share, pipeline in GW, cost of debt |

## Scoring

Each metric is ranked as a percentile within its own subsector, the pillars are averaged, and a weighted composite from 0 to 100 sorts the list.

1. **Normalise.** Convert everything to US dollars. Use the trading currency for market values and the reporting currency for financials (Shell trades in pence but reports in dollars). Use trailing 12 months, with next-12-month estimates where available.
2. **Clean.** Cap extreme values at the 5th and 95th percentile. Treat negative EBITDA or earnings as missing, not as cheap.
3. **Rank within subsector.** Each metric becomes a percentile among peers, flipped so higher always means better (low EV/EBITDA scores high).
4. **Pillar score.** Average the metric percentiles in each pillar. A company missing more than half a pillar gets a data flag.
5. **Composite.** Apply the weights below. Show both the composite and each pillar, because the pillar mix tells the story.

| Pillar | Weight |
| --- | --- |
| Valuation | 35% |
| Balance sheet | 20% |
| Shareholder returns | 15% |
| Quality | 20% |
| Momentum | 10% |

**Reading it:** a long candidate scores high on valuation and quality but low on momentum, meaning cheap and good but ignored. A short candidate is expensive, highly levered, and has run hard.

## Macro overlay

The screen finds cheap names; the house view decides which cheap names fit the next 12 months. Each run is read against the scenarios in the monthly house view.

| Scenario (from the October review) | What moves | Subsectors that should benefit | Subsectors at risk |
| --- | --- | --- | --- |
| Hormuz stays shut through winter | Brent stays near $100+, diesel and LNG stay tight | Non-Gulf producers, North American LNG exporters, refiners outside Asia | Asian and European refiners and utilities that import fuel |
| Hormuz reopens, Brent heads toward the EIA's $74 by 4Q27 | Prices and backwardation fall, freight eases | Low-cost, low-debt producers; Asian refiners as feedstock costs drop | High-cost and highly levered E&Ps, names priced for crisis margins |
| Lost demand in Asia and Europe does not come back | Structurally lower oil demand; power and renewables gain share | Power, grids, renewables, uranium | Oil-weighted names with long reserve lives |

These pairings are working hypotheses to test, not conclusions. Commodity beta from the factor table is what checks them: a supposed Hormuz winner whose shares do not move with Brent is not one.

## Red flags and exclusions

These names stay in the data but are flagged, and they never reach the shortlist without a written reason.

- **Sanctions:** Russian companies (Rosneft, Lukoil, Novatek, Gazprom) cannot be bought by most funds. Show them for context only.
- **State control:** majority-government ownership (Aramco, PetroChina, ONGC, Coal India) means minority shareholders come second. Apply a governance discount in the write-up.
- **Value traps:** low EV/EBITDA plus falling production or a short reserve life is cheap for a reason.
- **Data quality:** a missing pillar, a stale fiscal year, or a currency mismatch. Check by hand before using.
- **Liquidity:** below the trading-value floor, or a free float under 15%.
- **One-offs:** large impairments, asset sales or windfall taxes that distort the trailing numbers.

## Workflow, cadence and data

Run the screen monthly, right after the house view, and carry about 10 names forward into a one-page tear sheet each.

1. **Screen** about 100 to 120 names and score them (automated script, monthly).
2. **Overlay** the house-view scenarios and cut to about 25 names.
3. **Tear sheets** for about 10 names: thesis in two lines, valuation versus peers, catalyst, key risk.
4. **Pitches:** two full write-ups, one long and one short, each with a model.
5. **Call log:** record each pitch with its date, entry price, target and stop, then review monthly.

**Data sources and limits**

- **Yahoo Finance (free):** global prices, valuation and financial statements. Unofficial and sometimes wrong for foreign listings, so spot-check the top names against company reports. Its terms do not allow republishing, so the screener output stays private and only commentary goes on the website.
- **Own feeds:** Brent, TTF and Henry Hub from FRED and EIA for commodity beta.
- **FMP:** the free plan covers US stocks only, so it serves as a cross-check for US names.
- **Paid upgrade at the finish line:** consensus estimates and segment data (FMP paid, Daloopa or similar) would add forward multiples and the phase-2 KPIs.

**Output:** an Excel workbook in 07.2 Corporate Intelligence with sheets for the full screen, subsector medians, the shortlist and data flags, plus a script in 09_Code that rebuilds it.

## Decisions (agreed 10 Nov 2026)

| Decision | Agreed setting |
| --- | --- |
| Market-cap floor | $2bn |
| Power and renewables | Same universe, scored only within their own subsector |
| Pillar weights | Valuation 35%, balance sheet 20%, quality 20%, shareholder returns 15%, momentum 10% |
| Sanctioned Russian names | Shown for context, flagged, never shortlisted |
| Direction | Both longs and shorts |
| Build order | Version 1 now on free data; phase-2 subsector KPIs later |

## Change log

| Date | Change |
| --- | --- |
| 2026-11-10 | Framework v01 agreed |
