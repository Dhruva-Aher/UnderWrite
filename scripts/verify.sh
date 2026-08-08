#!/usr/bin/env bash
set -eo pipefail

echo "=============================================="
echo "   UNDERWRITE STRICT VERIFICATION"
echo "=============================================="

VERIFY_VENV=".verify-venv"

cleanup() {
    echo "Cleaning up $VERIFY_VENV..."
    rm -rf "$VERIFY_VENV"
}

trap cleanup EXIT

echo "[1/6] Checking Source Imports (Grep)..."
# No active references to deleted modules
MATCHES=$(grep -R -E \
  --exclude-dir=.git \
  --exclude-dir=.venv \
  --exclude-dir=.verify-venv \
  --exclude-dir=node_modules \
  --exclude-dir=__pycache__ \
  --exclude="task.md" \
  --exclude="walkthrough.md" \
  "remediation_engin[e]|hypothesis_generato[r]" . || true)

if [ -n "$MATCHES" ]; then
    echo "❌ Found active references to deleted legacy modules:"
    echo "$MATCHES"
    exit 1
fi
echo "✅ No legacy modules found."

echo "[2/6] Preparing Isolated Python Environment..."
if ! command -v python3.13 &> /dev/null; then
    echo "python3.13 not found."
    exit 1
fi
python3.13 -m venv "$VERIFY_VENV"
source "$VERIFY_VENV/bin/activate"
python3.13 -m pip install -r requirements.txt

echo "[3/6] Verifying Agent Context Kit Import..."
if ! python3.13 -c "from datahub_agent_context.langchain_tools import build_langchain_tools; print('ACK import: PASS')"; then
    echo "❌ Failed to import Agent Context Kit."
    exit 1
fi

echo "[4/6] Running Test Suite..."
python3.13 -m pytest tests/

echo "[5/6] Verifying Deterministic Offline Demo Execution..."
python3.13 demo/run_demo.py --offline

echo "[6/6] Testing Frontend and Docker Build..."
if ! command -v npm &> /dev/null; then
    echo "npm not found. Please install Node.js."
    exit 1
fi
cd web/frontend
npm ci
npm run build
cd ../../

if ! command -v docker >/dev/null 2>&1; then
    DOCKER_VERIFIED=0
else
    docker build -t underwrite:verify .
    DOCKER_VERIFIED=1
fi

echo "=============================================="
if [ "$DOCKER_VERIFIED" -eq 1 ]; then
    echo "Core verification: PASS"
    echo "Docker verification: PASS"
else
    echo "Core verification: PASS"
    echo "Docker verification: NOT RUN (docker executable unavailable)"
fi
echo "=============================================="
