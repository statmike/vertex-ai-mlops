# hurricanes per year
SELECT
  EXTRACT(YEAR FROM iso_time) AS report_year,
  COUNT(DISTINCT sid) AS number_of_hurricanes
FROM `bigquery-public-data.noaa_hurricanes.hurricanes`
WHERE
  iso_time IS NOT NULL
  AND basin = 'NA' -- North Atlantic Basin
GROUP BY report_year
ORDER BY number_of_hurricanes DESC
;

# hurricanes in specific year range
SELECT
  EXTRACT(YEAR FROM iso_time) AS report_year,
  COUNT(DISTINCT sid) AS number_of_hurricanes
FROM `bigquery-public-data.noaa_hurricanes.hurricanes`
WHERE
  iso_time IS NOT NULL
  AND basin = 'NA' -- North Atlantic Basin
  AND EXTRACT(YEAR FROM iso_time) >= 2005
  AND EXTRACT(YEAR FROM iso_time) <= 2005
GROUP BY report_year
ORDER BY number_of_hurricanes DESC
;

# hurricanes with highest wind speeds
SELECT
  ANY_VALUE(name) AS name,
  EXTRACT(YEAR FROM iso_time) AS report_year,
  MAX(usa_wind) AS max_wind_knots
FROM `bigquery-public-data.noaa_hurricanes.hurricanes`
WHERE
  iso_time IS NOT NULL
  AND basin = 'NA' -- North Atlantic Basin
  AND usa_wind IS NOT NULL
GROUP BY sid, report_year
ORDER BY max_wind_knots DESC
LIMIT 15
;

# hurricanes with highest wind speeds setting year range and speed threshold
SELECT
  ANY_VALUE(name) AS name,
  EXTRACT(YEAR FROM iso_time) AS report_year,
  MAX(usa_wind) AS max_wind_knots
FROM `bigquery-public-data.noaa_hurricanes.hurricanes`
WHERE
  iso_time IS NOT NULL
  AND basin = 'NA' -- North Atlantic Basin
  AND usa_wind IS NOT NULL
  AND EXTRACT(YEAR FROM iso_time) >= 2005 --PARAMETER: Replace 2005 with the desired earliest year
  AND EXTRACT(YEAR FROM iso_time) <= 2005 --PARAMETER: Repalce 2005 with the diesired latest year
GROUP BY sid, report_year
HAVING max_wind_knots >= 96 --PARAMETER: Replace 96 with desired wind threshold in knots
ORDER BY max_wind_knots DESC
LIMIT 15
;


# hurricanes with longest duration
SELECT
  ANY_VALUE(name) AS name,
  EXTRACT(YEAR FROM iso_time) AS report_year,
  TIMESTAMP_DIFF(MAX(iso_time), MIN(iso_time), HOUR) AS duration_hours,
  ROUND(TIMESTAMP_DIFF(MAX(iso_time), MIN(iso_time), HOUR) / 24.0, 1) AS duration_days
FROM `bigquery-public-data.noaa_hurricanes.hurricanes`
WHERE
  iso_time IS NOT NULL
  AND basin = 'NA' -- North Atlantic Basin
GROUP BY sid, report_year
ORDER BY duration_hours DESC
LIMIT 15
;


# hurricanes with longest duration for specific year ranges
SELECT
  ANY_VALUE(name) AS name,
  EXTRACT(YEAR FROM iso_time) AS report_year,
  TIMESTAMP_DIFF(MAX(iso_time), MIN(iso_time), HOUR) AS duration_hours,
  ROUND(TIMESTAMP_DIFF(MAX(iso_time), MIN(iso_time), HOUR) / 24.0, 1) AS duration_days
FROM `bigquery-public-data.noaa_hurricanes.hurricanes`
WHERE
  iso_time IS NOT NULL
  AND basin = 'NA' -- North Atlantic Basin
  AND EXTRACT(YEAR FROM iso_time) >= 2005 --PARAMETER: Replace 2005 with the desired earliest year
  AND EXTRACT(YEAR FROM iso_time) <= 2005 --PARAMETER: Repalce 2005 with the diesired latest year
GROUP BY sid, report_year
ORDER BY duration_hours DESC
LIMIT 15
;
