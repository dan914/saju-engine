# SKY_LIZARD Canonical Dataset

This directory stores the authoritative four-pillar dataset exported from the SKY_LIZARD v10.4 instance.

## Expected layout


```
data/canonical/
├── README.md
├── lunar_to_solar_1929_2030.csv
├── lunar_to_solar_1900_2050.csv       # extended MyNobleman extract (lunar↔solar mapping only)
├── manse_master.csv
├── pillars_1930_1959.csv               # raw SKY_LIZARD export (indices, Hangul ganji)
├── pillars_1960_1989.csv
├── pillars_1990_2009.csv
├── pillars_2010_2029.csv
├── pillars_canonical_1930_1959.csv     # normalized canonical schema
├── pillars_canonical_1960_1989.csv
├── pillars_canonical_1990_2009.csv
├── pillars_canonical_2010_2029.csv
├── pillars_generated_2021_2050.csv     # engine-projected pillars using quadratic term extrapolation
├── terms/
│   └── terms_<year>.csv      # observed (1930-2020) + predicted (2021-2050) major terms
├── terms_predicted/
│   └── terms_<year>.csv      # quadratic forecasts before copying into data/
└── canonical_calendar.py     # loads year/month mappings across all canonical files
```

Each CSV should include every supported birth date/time row for its range. Use UTF-8 encoding and the following headers:

> **Note:** The raw imports (`pillars_*.csv`, `manse_master.csv`) retain the original SKY_LIZARD column set (`solar_date`, `ganji`, etc.). The generated `pillars_canonical_*.csv` files apply the canonical schema described below (local_datetime/timezone/pillars), but hour and ΔT fields remain empty until the hour-level dataset is available. Canonical term tables cover 1930–2020 from SKY_LIZARD; `terms_predicted/` extends them to 2050 via quadratic fits, and the runtime copies under `data/terms_<year>.csv` combine both sources. `pillars_generated_2021_2050.csv` captures the engine’s projected pillars for 2021–2050 using those extrapolated terms, while `lunar_to_solar_1900_2050.csv` provides lunar↔solar conversions across the broader MyNobleman range.

| column | type | description |
| --- | --- | --- |
| `local_datetime` | ISO 8601 string | Local timestamp used in the SKY_LIZARD chart (UTC offset already applied). |
| `timezone` | string | IANA zone identifier (e.g., `Asia/Seoul`), matching the user’s selection. |
| `longitude_deg` | float | Observer longitude in decimal degrees (E positive). Needed to reproduce historical LMT cases. |
| `latitude_deg` | float | Observer latitude in decimal degrees. |
| `year_pillar` | string | Sexagenary pair (e.g., `甲子`). |
| `month_pillar` | string | Sexagenary pair. |
| `day_pillar` | string | Sexagenary pair. |
| `hour_pillar` | string | Sexagenary pair. |
| `month_term` | string | Solar term label recorded by SKY_LIZARD. |
| `delta_t_seconds` | float | ΔT value used in the chart. |
| `dataset_version` | string | Source tag (e.g., `SL-DB-v10.4`). |
| `notes` | string (optional) | Freeform metadata (e.g., timezone transitions, leap months). |

If the export is delivered as Parquet or SQL dumps, normalize into the CSV layout above so the regression scripts can process it.

## Import checklist

1. Confirm coverage from 1930-01-01 through 2029-12-31 (inclusive) for every supported region.
2. Include special cases (Pyongyang DST, leap months, boundary births between 23:00-01:00).
3. Run `scripts/build_canonical_index.py` after placing the CSVs to generate summary stats used by the regression suite.
4. Run `scripts/compare_canonical.py --limit 1000` for a spot check against the current engine once the dataset is in place.
