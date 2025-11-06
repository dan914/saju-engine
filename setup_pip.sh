#!/bin/bash
# Setup script for pip-based development environment (Poetry-free)

set -e  # Exit on error

echo "========================================================================"
echo "🐍 Setting up saju-engine with pip (Poetry-free)"
echo "========================================================================"
echo ""

# 1. Check Python version
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $PYTHON_VERSION"

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo "❌ Error: Python 3.11+ required"
    exit 1
fi
echo "   ✅ Python version OK"
echo ""

# 2. Create virtual environment
echo "🔧 Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "   ⚠️  .venv already exists, removing..."
    rm -rf .venv
fi

python3 -m venv .venv
echo "   ✅ Virtual environment created"
echo ""

# 3. Activate virtual environment
echo "🚀 Activating virtual environment..."
source .venv/bin/activate
echo "   ✅ Activated: $(which python3)"
echo ""

# 4. Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel --quiet
echo "   ✅ pip upgraded: $(pip --version)"
echo ""

# 5. Install dependencies
echo "📦 Installing dependencies from requirements.txt..."
START_TIME=$(date +%s)
pip install -r requirements.txt
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "   ✅ Dependencies installed (${DURATION}s)"
echo ""

# 6. Setup development environment (add service paths)
echo "🔗 Setting up service paths..."
python3 scripts/setup_dev_environment.py
echo "   ✅ Service paths configured"
echo ""

# 7. Verify installation
echo "🧪 Verifying installation..."
python3 -c "from app.main import app; print('   ✅ FastAPI app imports successfully')"
echo ""

# 8. Run health check test
echo "🏥 Running health check test..."
pytest services/analysis-service/tests/test_health.py -q
echo ""

echo "========================================================================"
echo "✅ Setup complete!"
echo "========================================================================"
echo ""
echo "📝 Next steps:"
echo ""
echo "   1. Activate environment:"
echo "      source .venv/bin/activate"
echo ""
echo "   2. Run tests:"
echo "      pytest services/analysis-service/tests/"
echo ""
echo "   3. Start development server:"
echo "      cd services/analysis-service"
echo "      uvicorn app.main:app --reload"
echo ""
echo "🎯 Performance note:"
echo "   This pip-based setup should be MUCH faster than Poetry 1.8.4"
echo "   Expected startup time: <5 seconds (vs. 5-6 minutes with Poetry)"
echo ""
