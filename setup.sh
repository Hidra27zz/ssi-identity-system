#!/bin/bash
# Cai dat toan bo dependencies cho du an SSI
# Chay: bash setup.sh

set -e

echo "=== Kiem tra Python ==="
python3 --version

echo "=== Tao virtual environment ==="
python3 -m venv venv
source venv/bin/activate

echo "=== Cai dat backend dependencies ==="
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "=== Cai dat Ape plugins ==="
ape plugins install vyper
ape plugins install etherscan

echo "=== Compile smart contracts ==="
ape compile

echo "=== Kiem tra .env ==="
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Da tao .env tu .env.example. Hay dien cac gia tri can thiet."
else
    echo ".env da ton tai."
fi

echo ""
echo "=== Cai dat hoan tat ==="
echo ""
echo "Buoc tiep theo:"
echo "  1. Dien cac gia tri vao .env"
echo "  2. Khoi dong local node:"
echo "       anvil"
echo "     hoac:"
echo "       ganache"
echo ""
echo "  3. Deploy contracts:"
echo "       ape run contracts/deploy --network ethereum:local:http://127.0.0.1:8545"
echo "       ape run nft-integration/deploy --network ethereum:local:http://127.0.0.1:8545"
echo ""
echo "  4. Cap nhat dia chi contract vao shared/constants.py va shared/constants.js"
echo ""
echo "  5. Chay backend:"
echo "       uvicorn backend.main:app --reload --port 8000"
echo ""
echo "  6. Mo frontend trong trinh duyet:"
echo "       frontend/user.html"
echo "       frontend/creator.html"
echo "       frontend/verifier.html"
