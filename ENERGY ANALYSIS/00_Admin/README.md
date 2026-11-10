# Global Energy Analysis

Project folder for analysing global energy markets across the value chain:
upstream production -> midstream logistics -> downstream refining and end use
-> regional markets -> policy -> finance and trading.

## Folder structure

- 00_Admin
- 01_Market_Foundations_and_Data
  - 01.1_Raw_Data_Downloads
    - IEA
    - EIA
    - OPEC
    - Energy_Institute
    - Other_Sources
  - 01.2_Sankey_and_Flow_Charts
  - 01.3_Macro_Economic_Indicators
  - 01.4_Supply_Demand_Balances
  - 01.5_Scenarios_and_Outlooks
  - 01.6_Weather_and_Climate_Data
- 02_Upstream_Production_by_Source
  - 02.1_Fossil_Fuels
    - Crude_Oil
    - Natural_Gas
    - Coal
  - 02.2_Nuclear_and_Hydro
  - 02.3_Renewables_and_Alternatives
    - Solar
    - Wind
    - Hydrogen
    - Biomass
  - 02.4_Production_Costs
  - 02.5_Critical_Minerals
- 03_Midstream_Logistics_and_Transportation
  - 03.1_Maritime_Shipping
  - 03.2_Pipeline_Networks
  - 03.3_Storage_and_Terminals
  - 03.4_Trade_Flows_and_Sanctions
- 04_Downstream_Refining_and_End_Use
  - 04.1_Refining_and_Processing
  - 04.2_Power_Generation_and_Grids
  - 04.3_Demand_Sectors
    - Industrial
    - Transportation
    - Residential_Commercial
    - Agriculture
    - Data_Centers_and_AI
  - 04.4_Energy_Storage
- 05_Regional_Markets_and_Geopolitics
  - 05.1_OPEC_and_Allies
  - 05.2_North_America
  - 05.3_Major_Demand_Hubs
    - Europe
    - China
    - India
    - Emerging_Economies
  - 05.4_Russia_and_Caspian
  - 05.5_Latin_America
  - 05.6_Africa
  - 05.7_Gulf_LNG_and_Qatar
- 06_Policy_Regulation_and_Carbon
  - 06.1_Climate_Accords_and_Targets
  - 06.2_Carbon_Markets
  - 06.3_Subsidies_and_Taxes
  - 06.4_Emissions_Data
- 07_Financial_Analysis_and_Trading
  - 07.1_Commodity_Pricing
  - 07.2_Corporate_Intelligence
  - 07.3_Investment_Models
- 08_Outputs
  - Reports
  - Dashboards
  - Charts
  - Presentations
- 09_Code
  - Data_Pulls
  - Notebooks
  - Utilities
- 99_Archive

Each folder contains a _README.md describing what belongs there.

## Naming standard

    YYYYMMDD_Source_Topic_Region_Frequency_vNN.ext

- Date = the PUBLICATION date of the data or report (record the download date in Source_Log.xlsx).
- Source = issuing body: IEA, EIA, OPEC, EI, JODI, IMF, WB, etc.
- Region = ISO 3-letter country code (USA, SAU, CHN) or Global / OECD / EU / etc.
- Frequency = Daily, Weekly, Monthly, Quarterly, Annual (omit for one-off reports).
- Version = v01, v02 ... for your own edited or processed files.
- Use underscores, no spaces, no '&' or other special characters.

Examples:
    20261016_EIA_STEO_Global_Monthly_v01.xlsx
    20260625_EI_Statistical_Review_Global_Annual.xlsx
    20261014_IEA_Oil_Market_Report_Global_Monthly.pdf

## Working rules

1. Raw files are never edited. Keep originals in 01.1_Raw_Data_Downloads; copy before changing.
2. Log every download in 00_Admin/Source_Log.xlsx (URL, dates, license).
3. Superseded versions go to 99_Archive, not the recycle bin.
4. Convert units with 00_Admin/Reference_Tables.xlsx so all work uses the same factors.
5. Check the release calendar (Reference_Tables.xlsx) to keep datasets current.

Created: 2026-10-16
