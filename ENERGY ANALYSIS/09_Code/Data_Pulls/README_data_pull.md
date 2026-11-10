# Data pull scripts (free APIs)

1. `20261110_Code_Energy_Data_Pull_Global_v01.py <ENERGY ANALYSIS folder> [YYYYMMDD]` pulls:
   - Global, country level: EIA international data for every country and region (crude, liquids, oil demand, gas, coal, power, capacity, primary energy, CO2), JODI oil monthly (primary and secondary, 2025–26), Ember monthly and yearly electricity data.
   - Prices and markets: about 100 EIA and FRED series, CFTC Commitments of Traders, GIE AGSI+ EU gas storage, and an OilPriceAPI latest-price snapshot.
   Raw CSVs go to `01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/{EIA,Other_Sources}/API_<date>/`.
2. `20261110_Code_Build_Global_Workbooks_Global_v01.py <ENERGY ANALYSIS folder> <YYYYMMDD>` builds the global workbooks that lead each section: 01.4 energy balance by country, 02 production by country, 03.4 trade and stocks, 04.1 refining and oil demand, 04.2 power generation, 05 regional profiles, 06.4 CO2 by country.
3. `20261110_Code_Build_Section_Workbooks_Global_v01.py <ENERGY ANALYSIS folder> <YYYYMMDD>` builds the detail workbooks (US weekly balance, US power and refining, EU storage, prices and positioning).

Keys are read from the environment variables `EIA_API_KEY`, `FRED_API_KEY`, `GIE_API_KEY` and `OILPRICEAPI_KEY`. Never write keys into these files: the folder is mirrored to a public GitHub repository. CFTC, JODI and Ember need no key.
Add an EIA or FRED series by adding one line to `CATALOG` in the pull script; add a global EIA measure to `EIA_INTL_BULK` and `METRICS`.
