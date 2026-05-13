# He Thong Dinh Danh Phi Tap Trung (SSI)

## Phan cong module

| Thu muc | Nguoi phu trach | Nhiem vu |
|---------|----------------|---------|
| contracts/ | Nhan | Vyper Smart Contract DID_Registry |
| backend/ | Thuy | FastAPI + IPFS + RSA + SQLite |
| frontend/ | Phuc | HTML/JS DApp (3 giao dien) |
| nft-integration/ | Nhu | Soulbound NFT + Orchestrator |
| shared/ | Ca nhom | ABI, constants dung chung |

## Quy tac GitHub (tranh conflict)

- Moi nguoi chi commit vao thu muc cua minh
- Khong sua file cua nguoi khac khi chua thong bao
- shared/ chi duoc cap nhat sau khi deploy contract (Nhan + Nhu)
- Tao branch rieng: feature/nhan-contracts, feature/thuy-backend, feature/phuc-frontend, feature/nhu-nft

## Cai dat nhanh

    bash setup.sh

Lenh nay se: tao venv, cai pip packages, cai ape plugins, compile contracts.

## Chay tung buoc

### Buoc 1: Cai dat

    python3 -m venv venv
    source venv/bin/activate
    pip install -r backend/requirements.txt
    ape plugins install vyper
    ape plugins install etherscan

### Buoc 2: Cau hinh .env

    cp .env.example .env
    # Giu nguyen gia tri mac dinh de chay local

### Buoc 3: Compile contracts

    ape compile

### Buoc 4: Khoi dong local node (terminal rieng)

    # Cai Foundry neu chua co: curl -L https://foundry.paradigm.xyz | bash && foundryup
    bash scripts/start_local_node.sh
    # hoac chay truc tiep: anvil

### Buoc 5: Deploy contracts

    bash scripts/deploy_all.sh
    # hoac tung lenh:
    ape run contracts/deploy --network ethereum:local:http://127.0.0.1:8545
    ape run nft-integration/deploy --network ethereum:local:http://127.0.0.1:8545

### Buoc 6: Cap nhat dia chi contract

Sau khi deploy, copy dia chi in ra va cap nhat vao 3 file:
- .env  ->  DID_REGISTRY_ADDRESS=0x...  va  SOULBOUND_ADDRESS=0x...
- shared/constants.py  ->  DID_REGISTRY_ADDRESS  va  SOULBOUND_ADDRESS
- shared/constants.js  ->  DID_REGISTRY_ADDRESS  va  SOULBOUND_ADDRESS

### Buoc 7: Chay backend (terminal rieng)

    source venv/bin/activate
    uvicorn backend.main:app --reload --port 8000

API docs: http://localhost:8000/docs

### Buoc 8: Mo frontend

Mo truc tiep trong trinh duyet hoac dung VS Code Live Server:
- frontend/user.html
- frontend/creator.html
- frontend/verifier.html

### Buoc 9: Chay NFT orchestrator (terminal rieng)

    source venv/bin/activate
    python nft-integration/integration.py

## Chay tests

    bash scripts/run_tests.sh
    # hoac:
    pytest --tb=short -v

## Demo nhanh tren Sepolia (tai khoan MetaMask cua ban)

1. **Lay Sepolia ETH**: chuyen MetaMask sang mang **Sepolia**, lay ETH test (faucet: tim `Sepolia faucet` tren mang).
2. **Tao `.env`**: `cp .env.example .env` roi dien:
   - `RPC_URL` = endpoint Sepolia (Infura / Alchemy / `https://rpc.sepolia.org` neu phu hop).
   - `PRIVATE_KEY` = key cua **cung vi** ban muon dung de backend ky giao dich (khong commit len Git).
   - `IPFS_API_KEY` / `IPFS_SECRET_KEY` = tai khoan Pinata.
3. **Contract & mang**: `shared/constants.py` va `shared/constants.js` da dat `CHAIN_ID` = **11155111** (Sepolia) va dia chi DID Registry / Soulbound. Neu ban **tu deploy** len Sepolia, cap nhat hai dia chi do sau deploy.
4. **Vai tro Creator**: tren contract, chi dia chi co `isCreator == true` moi goi duoc `store-hash` qua backend. Vi deploy mac dinh la creator; neu ban chi la user, can owner grant quyen (hoac deploy moi bang vi cua ban).
5. **Chay backend**: `uvicorn backend.main:app --reload --port 8000` — mo `http://127.0.0.1:8000/login.html`, MetaMask chon **Sepolia**.
6. **NFT orchestrator** (tuy chon): `python nft-integration/integration.py` — `PRIVATE_KEY` (hoac `ISSUER_PRIVATE_KEY`) phai la vi **duoc phep mint** Soulbound tren contract da deploy.

## Deploy len Sepolia testnet

    # 1. Cap nhat .env voi Sepolia RPC_URL va PRIVATE_KEY thuc
    # 2. Import account vao Ape (chi can 1 lan)
    ape accounts import deployer
    # 3. Deploy
    ape run contracts/deploy --network ethereum:sepolia:infura
    ape run nft-integration/deploy --network ethereum:sepolia:infura

## Cau truc thu muc

    ssi-project/
    contracts/
        DID_Registry.vy
        Soulbound_Contract.vy   (copy tu nft-integration/ de Ape compile)
        deploy.py
        tests/
    backend/
        main.py
        routers/
        services/
        models/
        tests/
        requirements.txt
    frontend/
        creator.html
        user.html
        verifier.html
        css/
        js/
    nft-integration/
        Soulbound_Contract.vy   (file goc, sua o day)
        deploy.py
        integration.py
        tests/
    shared/
        abis/                   (tu dong tao khi deploy)
        constants.py
        constants.js
    scripts/
        start_local_node.sh
        deploy_all.sh
        run_tests.sh
    ape-config.yaml
    pyproject.toml
    setup.sh
    .env.example
    .gitignore
    README.md
