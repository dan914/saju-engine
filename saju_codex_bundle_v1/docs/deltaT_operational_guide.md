
# ΔT Models, Range, and Uncertainty — Operational Guide (1600–2200)

## Why it matters
ΔT=TT−UT1 affects solar-term boundaries and day/hour edges. A few seconds can flip classifications at boundaries.

## Models in scope
- EM (Espenak–Meeus/NASA): primary compute; piecewise polynomials; extrapolates in future.
- S&M (Stephenson & Morrison): historical authority; uncertainties tabulated.
- Meeus–Simons: 1620–2000 high-accuracy fit (≤~3.2 s); validation use.
- IERS EOP: near-term authoritative UT1–UTC; millisecond-scale; no long-range forecasts.
- JPL Horizons: uses EOP near-term; freezes ΔT beyond range → underestimates far-future growth.

## Uncertainty by era (rule-of-thumb σ)
1600≈±20 s → 1700≈±5 s → 1800≈±1 s → 1900≈±0.1 s → modern≈ms. Future: 2050≈±5–10 s, 2100≈tens of s, 2200≈minute scale.

## Alerts & thresholds
- Standard: **≥5 s** ΔT uncertainty/difference → warn.
- High-precision: **≥1–2 s** → warn.
- Engine discrepancy: **>1 s** between two engines for same event → hold/verify.
- EM vs Horizons divergence: **≥2–3 s** → treat as out-of-range → safe mode.
- Near-boundary: **≤5 s** (standard) / **≤1 s** (strict) separation → boundary caution.

## Fallbacks
- Prefer **precomputed solar-term tables** when uncertainty high (or far-future).
- If engines differ >1 s: cross-check third source, do not autopublish.
- If near-boundary: present both possibilities or fetch max-precision source.
- For far-future divergence: choose conservative model or mark provisional.

## Integration points
- Engine must emit: `deltaT_sec`, `uncertainty_sec`, `boundary_margin_sec`, and any engine diffs.
- UI shows a warning banner + “근거 보기” with the above fields.
- PDF includes ΔT line in the evidence appendix.
