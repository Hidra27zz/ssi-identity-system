#!/bin/bash
# Chay toan bo test suite
# Chay: bash scripts/run_tests.sh

source venv/bin/activate 2>/dev/null || true

echo "=== Chay tat ca tests ==="
pytest --tb=short -v

echo ""
echo "=== Ket qua ==="
