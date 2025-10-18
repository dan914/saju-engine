# Policy Signature Verification Report

**Total Files Checked:** 5
**Results:** ✅ 5 OK | ⚠️  0 UNSIGNED | ❌ 0 ERROR

---

## Verification Results

## Policy File Signatures
✅ OK   : policy/gyeokguk_policy_v1.json
✅ OK   : policy/llm_guard_policy_v1.1.json
✅ OK   : policy/llm_guard_policy_v1.json
✅ OK   : policy/relation_weight_policy_v1.0.json
✅ OK   : policy/yongshin_selector_policy_v1.json

## Schema File Sidecar Hashes
📄 HASH  : schema/gyeokguk_input_schema_v1.json → 89c85edc2072d2f4...
📄 HASH  : schema/gyeokguk_output_schema_v1.json → b9e19920f2833e95...
📄 HASH  : schema/llm_guard_input_schema_v1.json → 66e09574fac912aa...
📄 HASH  : schema/llm_guard_input_v1.1.json → 3819d3d34ba17db6...
📄 HASH  : schema/llm_guard_output_schema_v1.json → 1bc9c582285bd6a3...
📄 HASH  : schema/llm_guard_output_v1.1.json → 23ccb9ddea78ba1e...
📄 HASH  : schema/relation_weight.schema.json → d0b92ff87e52c09b...
📄 HASH  : schema/yongshin_input_schema_v1.json → ae1a14ebfa048ab8...
📄 HASH  : schema/yongshin_output_schema_v1.json → a24505da09ff6fdd...

---

# Detailed Policy Signature Verification

## Known Policy Signatures

| Policy | Status | Expected Hash | Actual Hash |
|--------|--------|---------------|-------------|
| LLM Guard v1.0 | ✅ MATCH | `a4dec83545592db3...` | `a4dec83545592db3...` |
| LLM Guard v1.1 | ✅ MATCH | `591f3f6270efb090...` | `591f3f6270efb090...` |
| Relation Weight v1.0 | ✅ MATCH | `704cf74d323a034c...` | `704cf74d323a034c...` |
| Yongshin Selector v1.0 | ✅ MATCH | `e0c95f3fdb1d382b...` | `e0c95f3fdb1d382b...` |
| Gyeokguk Classifier v1.0 | ✅ MATCH | `05089c0a3f0577c1...` | `05089c0a3f0577c1...` |

---

## Recommendations

1. **UNSIGNED policies:** Run Policy Signature Auditor to sign
2. **MISMATCH policies:** Re-sign with current content
3. **ERROR policies:** Check JSON validity and retry

**Command to sign:**
```bash
PYTHONPATH="." python3 policy_signature_auditor/psa_cli.py sign <policy_file>
```
