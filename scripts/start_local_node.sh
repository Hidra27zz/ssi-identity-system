#!/bin/bash
# Khoi dong local Ethereum node (Anvil)
# Anvil la local node nhanh nhat, co san trong Foundry
#
# Cai Foundry: curl -L https://foundry.paradigm.xyz | bash
# Sau do: foundryup

echo "Khoi dong Anvil local node tai http://127.0.0.1:8545 ..."
echo "Chain ID: 31337 (local)"
echo "Nhan Ctrl+C de dung"
echo ""

anvil \
  --host 127.0.0.1 \
  --port 8545 \
  --chain-id 31337 \
  --accounts 10 \
  --balance 10000 \
  --block-time 1
