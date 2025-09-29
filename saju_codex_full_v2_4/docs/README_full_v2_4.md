# Saju Engine — Full Bundle v2.4
Generated: 2025-09-27T03:28:11.088802Z

Includes policies (time/zi, seasons, strength, root/seal, yugi, relation, deltaT, telemetry, lunar/boundary/jdn/five-he), schemas (evidence v1.2–v1.4), structure rules v1.2 (정관/편재/식상/인성), and relation-structure adjust v1.

Usage:
1) Load policies/*.json in this order:
   - time_basis_policy_v1, zi_boundary_policy_v1
   - seasons_wang_map_v2, strength_adjust_v1_1
   - yugi_policy_v1_1, root_seal_policy_v2_3
   - structure_rules_v1_2, relation_priority_v1, relation_structure_adjust_v1
   - lunar_policy_v1, boundary_review_policy_v1, jdn_precision_policy_v1
   - deltaT_trace_policy_v1, telemetry_policy_v1_1
2) Implement detectStructure_v2 → applyStructureGating → Strength eval → Explain Layer (templates).

Evidence schema: see schemas/*.json.
