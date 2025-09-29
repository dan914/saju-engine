# LMT (Local Mean Time) Specification — KR_trad mode

- Longitude sign: East positive (+), West negative (−), degrees in [-180, +180].
- Offset seconds: `LMT_offset_sec = longitude_deg * 240.0` (since 1° = 4 minutes = 240 s).
- Pipeline (trad mode):
  1) Parse civil local time (IANA tz, DST-aware) → UTC.
  2) Compute `local_LMT = UTC + LMT_offset_sec`.
  3) Apply day/hour boundaries (LCRO, Zi start at 23:00) on `local_LMT` clock only.
  4) Solar terms remain based on UTC ephemeris; do not LMT-shift ephemeris.
- Evidence:
  Add to evidence_log:
  ```json
  "LMT":{"applied":true,"offset_sec":<float>,"lon_deg":<float>}
  ```
