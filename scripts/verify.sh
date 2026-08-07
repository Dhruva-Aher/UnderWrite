#!/usr/bin/env bash
set -eo pipefail

echo "=============================================="
echo "   UNDERWRITE VERIFICATION SCRIPT"
echo "=============================================="

echo "[1/4] Checking dependencies..."
if ! command -v npm &> /dev/null; then
    echo "npm not found. Please install Node.js."
    exit 1
fi
if ! command -v python3 &> /dev/null; then
    echo "python3 not found."
    exit 1
fi

echo "[2/4] Testing Frontend..."
cd web/frontend
npm ci
npm run build
cd ../../

echo "[3/4] Testing Backend..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/

echo "[4/4] Verifying Demo Execution..."
python demo/run_demo.py

echo "✅ Verification Complete!"
