# Luck Start — v1.1

Start age (years) = (birth → next solar-term entry interval in days) / 3.0

- birth: civil local → tzdb/DST → UTC
- next solar-term: precomputed 定氣(UTC)
- seconds→days(÷86400), ms까지 기록

Evidence 예:
"luck_calc": {
  "prev_term":"立春","next_term":"驚蟄",
  "interval_days":29.42,"days_from_prev":12.30,"start_age":4.10
}

경계/불확실:
±1s 또는 ΔT flag → boundary_review_policy_v1 적용
