# Luck Start (起運) Policy — v1.0
- Formula (standard): **start_age_years = (time_to_next_jieqi_in_days) / 3.0**
- Where `time_to_next_jieqi` is the exact interval from birth instant (local civil time, tzdb/DST) to the next solar term boundary (入節) in **days (including fractions)**.
- Direction: traditional_sex (male forward, female reverse) by default; alternatives: year_stem_yinyang, manual.
- Notes:
  - Use precomputed solar-term tables (1600–2200) with ΔT policy.
  - Boundary badges if |ΔT uncertainty| > threshold or birth within ±5s of term.
