# 01.6_Weather_and_Climate_Data

Weather drivers of short-term gas and power prices.

Typical contents / sources: Heating/cooling degree days, hydro reservoir levels, wind and solar capacity factors, seasonal forecasts.

Naming: YYYYMMDD_Source_Topic_Region_Frequency_vNN.ext  (date = publication date)
Example: 20261016_EIA_STEO_Global_Monthly_v01.xlsx

## Files kept here

- `OpenMeteo_Temperature_EU_Gas_Points_Europe_Daily.csv`: daily mean 2 m temperature (deg C) since July 1995 at one city per EU gas market (DE Kassel, IT Milan, FR Paris, NL Utrecht, PL Warsaw, BE Brussels, ES Madrid, RO Bucharest, HU Budapest, AT Vienna, CZ Prague, SK Bratislava). It is a rolling file: the Friday gas pipeline pulls the last 60 days again (recent ERA5 days get revised) and appends new days. The storage model turns it into gas-weighted heating degree days (sheet Weather_Daily).
- Source: Open-Meteo historical weather API (ERA5 reanalysis), open-meteo.com. Licence CC-BY 4.0: credit "Weather data by Open-Meteo.com".
