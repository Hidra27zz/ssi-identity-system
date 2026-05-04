#!/bin/bash
# Deploy cả 2 contracts lên local node và cập nhật constants
# Chạy: bash scripts/deploy_all.sh
#
# Yêu cầu: anvil đang chạy ở port 8545

set -e

source venv/bin/activate 2>/dev/null || true

NETWORK="ethereum:local:http://127.0.0.1:8545"

echo "=== Deploy DID_Registry ==="
ape run contracts/deploy --network $NETWORK

echo ""
echo "=== Deploy Soulbound_Contract ==="
ape run nft-integration/deploy --network $NETWORK

echo ""
echo "=== ABI đã được export vào shared/abis/ ==="
ls -la shared/abis/

echo ""
echo "Hãy cập nhật DID_REGISTRY_ADDRESS và SOULBOUND_ADDRESS trong:"
echo "  - .env"
echo "  - shared/constants.py  (CHAIN_ID = CHAIN_ID_LOCAL nếu chạy local)"
echo "  - shared/constants.js"
