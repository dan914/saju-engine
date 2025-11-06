#!/usr/bin/env bash
# Stage 2 Audit Runner - Shell Wrapper
set -euo pipefail

echo "=================================================="
echo "Stage 2 Audit — Pre-Stage-3 Integrity Check"
echo "=================================================="

# Check Python availability
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: python3 not found"
    exit 1
fi

# Run audit script
python3 tools/stage2_audit.py || {
    echo ""
    echo "❌ ERROR: stage2_audit.py failed"
    echo "   Check reports/ for partial results"
    exit 1
}

echo ""
echo "✅ Audit complete"
echo "   Reports written to: ./reports/"
echo ""
echo "Next steps:"
echo "  1. Review: reports/stage2_audit_summary.md"
echo "  2. Check gaps: reports/stage2_gap_list.md"
echo "  3. Follow plan: reports/stage2_action_plan.md"
echo ""
