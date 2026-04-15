#!/bin/bash
# Deploy ca 2 contracts len local node va cap nhat constants
# Chay: bash scripts/deploy_all.sh
#
# Yeu cau: anvil dang chay o port 8545

set -e

source venv/bin/activate 2>/dev/null || true

NETWORK="ethereum:local:http://127.0.0.1:8545"

echo "=== Deploy DID_Registry ==="
ape run contracts/deploy --network $NETWORK

echo ""
echo "=== Deploy Soulbound_Contract ==="
ape run nft-integration/deploy --network $NETWORK

echo ""
echo "=== ABI da duoc export vao shared/abis/ ==="
ls -la shared/abis/

echo ""
echo "Hay cap nhat DID_REGISTRY_ADDRESS va SOULBOUND_ADDRESS trong:"
echo "  - .env"
echo "  - shared/constants.py"
echo "  - shared/constants.js"
