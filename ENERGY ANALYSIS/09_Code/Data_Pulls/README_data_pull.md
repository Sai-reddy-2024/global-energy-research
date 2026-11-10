# Data pull scripts (free APIs)

1. `20261110_Code_Energy_Data_Pull_Global_v01.py <ENERGY ANALYSIS folder> [YYYYMMDD]` pulls about 100 series from the EIA API v2 and FRED, plus CFTC Commitments of Traders for WTI, Henry Hub, RBOB and ULSD, GIE AGSI+ EU gas storage, the Ember yearly electricity CSV and an OilPriceAPI latest-price snapshot. Raw CSVs go to `01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/{EIA,Other_Sources}/API_<date>/`.
2. `20261110_Code_Build_Section_Workbooks_Global_v01.py <ENERGY ANALYSIS folder> <YYYYMMDD>` builds the section workbooks (01.3, 01.4, 02.1, 03.3, 04.1, 04.2, 06.4, 07.1) from those CSVs.

Keys are read from the environment variables `EIA_API_KEY`, `FRED_API_KEY`, `GIE_API_KEY` and `OILPRICEAPI_KEY`. Never write keys into these files: the folder is mirrored to a public GitHub repository. CFTC needs no key.
Add a series by adding one line to `CATALOG` in the pull script.
