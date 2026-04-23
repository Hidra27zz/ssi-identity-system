# Huong Dan Cai Dat - He Thong SSI

## Tong Quan He Thong

### Da Hoan Thanh (Nhan - Smart Contract)
- DID_Registry.vy: Smart contract quan ly dinh danh
- Deploy thanh cong len Anvil local: `0x5FbDB2315678afecb367f032d93F642f64180aa3`
- 67 tests pass (unit tests + property-based tests)
- ABI da export: `shared/abis/DID_Registry.json`
- Constants da cap nhat: `shared/constants.py` va `shared/constants.js`

### Chua Hoan Thanh (Can Lam)
- Backend (Thuy): FastAPI + IPFS + RSA encryption
- Frontend (Phuc): 3 giao dien HTML/JS
- NFT Integration (Nhu): Soulbound Token + orchestrator

---

## Cai Dat Chung Cho Ca Nhom

### Buoc 1: Clone repo va cai dat co ban

```bash
git clone <repo-url>
cd ssi-identity-system
python3 -m venv venv
source venv/bin/activate
```

### Buoc 2: Cai dat Foundry (Anvil)

```bash
curl -L https://foundry.paradigm.xyz | bash
source ~/.zshenv
foundryup
```

### Buoc 3: Khoi dong Anvil (de chay trong terminal rieng)

```bash
anvil
```

Giu terminal nay chay. Anvil se tao 10 test accounts voi private key co dinh.

---

## Nhan (Smart Contract) - DA XONG

### Nhiem vu da hoan thanh:
- DID_Registry.vy: createDID, storeDocumentHash, updateDocumentHash, revokeDID, verifyDID
- Phan quyen: grantCreatorRole, revokeCreatorRole, transferOwnership
- Deploy script: `scripts/deploy.py`
- Tests: 67 tests (unit + property-based)

### File da ban giao:
- `shared/abis/DID_Registry.json` - ABI cho backend va frontend
- `shared/constants.py` - dia chi contract cho backend Python
- `shared/constants.js` - dia chi contract cho frontend JS
- `contracts/HANDOVER.md` - tai lieu huong dan su dung

### Khong can lam gi them.

---

## Thuy (Backend - FastAPI + IPFS + RSA)

### Nhiem vu can lam:

1. Hoan thien `backend/services/ipfs_service.py`
   - Tao tai khoan Pinata: https://app.pinata.cloud
   - Lay API Key va Secret Key
   - Test upload/retrieve file

2. Hoan thien `backend/services/crypto_service.py`
   - Da co skeleton, can test voi file thuc te

3. Hoan thien `backend/services/blockchain_service.py`
   - Da co skeleton, can kiem tra ket noi voi DID_Registry

4. Hoan thien cac routers trong `backend/routers/`
   - Da co skeleton, can test endpoints

### Cai dat:

```bash
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Cau hinh .env:

```bash
cp .env.example .env
# Dien IPFS_API_KEY va IPFS_SECRET_KEY tu Pinata
```

### Chay backend:

```bash
uvicorn backend.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Test:

```bash
pytest backend/tests/ -v
```

---

## Phuc (Frontend - HTML/JS DApp)

### Nhiem vu can lam:

1. Hoan thien `frontend/creator.html` va `frontend/js/creator.js`
   - Form upload anh + PDF
   - Nut gui hash len blockchain
   - Hien thi trang thai giao dich

2. Hoan thien `frontend/user.html` va `frontend/js/user.js`
   - Tao keypair RSA
   - Xem thong tin DID
   - Quan ly consent (phe duyet/tu choi chia se du lieu)
   - Xem Soulbound Token

3. Hoan thien `frontend/verifier.html` va `frontend/js/verifier.js`
   - Nhap dia chi vi
   - Hien thi ket qua xac minh

### Cai dat:

Khong can cai dat gi. Chi can:
- Backend dang chay o port 8000
- Mo file HTML bang Live Server (VS Code extension)

### File can import:

```javascript
import { BACKEND_URL, DID_REGISTRY_ADDRESS } from "../../shared/constants.js";
import { apiFetch, apiUpload } from "./api.js";
```

### Endpoints backend can goi:

```
POST /api/crypto/generate-keypair
POST /api/did/create
POST /api/did/store-hash
POST /api/upload
GET  /api/did/verify/{address}
GET  /api/did/record/{address}
GET  /api/consent/pending/{did}
POST /api/consent/respond
GET  /api/nft/status/{address}
```

---

## Nhu (NFT Integration - Soulbound Token)

### Nhiem vu can lam:

1. Hoan thien `nft-integration/Soulbound_Contract.vy`
   - Da co skeleton, can kiem tra logic
   - Compile va deploy

2. Hoan thien `nft-integration/integration.py`
   - Da co skeleton
   - Lang nghe event `DocumentHashStored` tu DID_Registry
   - Tu dong mint Soulbound Token
   - Lang nghe event `DIDRevoked` va invalidate token

3. Viet tests trong `nft-integration/tests/test_soulbound.py`
   - Da co skeleton

### Cai dat:

```bash
source venv/bin/activate
pip install -r contracts/requirements.txt
```

### Deploy Soulbound Contract:

```bash
# Compile
ape compile

# Deploy (dung chung account anvil_deployer da import)
ape run nft-integration/deploy --network ethereum:local
```

### Chay orchestrator:

```bash
python nft-integration/integration.py
```

Script nay se chay lien tuc, lang nghe events va mint NFT tu dong.

---

## Quy Tac GitHub (Tranh Conflict)

### Phan chia thu muc:

```
Nhan  -> chi commit vao contracts/
Thuy  -> chi commit vao backend/
Phuc  -> chi commit vao frontend/
Nhu   -> chi commit vao nft-integration/
```

### Shared folder:

- `shared/abis/` - chi Nhan va Nhu cap nhat (sau khi deploy contract)
- `shared/constants.py` - chi Nhan va Nhu cap nhat
- `shared/constants.js` - chi Nhan va Nhu cap nhat

### Workflow:

1. Truoc khi lam viec: `git pull`
2. Tao branch rieng: `git checkout -b feature/ten-ban-module`
3. Chi sua file trong thu muc cua minh
4. Commit thuong xuyen: `git add . && git commit -m "mo ta"`
5. Push: `git push origin feature/ten-ban-module`
6. Tao Pull Request tren GitHub
7. Sau khi merge: `git checkout main && git pull`

---

## Thong Tin Quan Trong

### Dia chi contract (Local Anvil):
```
DID_Registry: 0x5FbDB2315678afecb367f032d93F642f64180aa3
Soulbound:    (chua deploy - Nhu se lam)
```

### Anvil test accounts:
```
Account [0]: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
Private Key:  0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

### Ape account passphrase:
```
Account name: anvil_deployer
Passphrase:   test123
```

Luu y: Thong tin nay CHI DUNG CHO LOCAL DEVELOPMENT. Khi deploy len Sepolia testnet se dung private key khac.

---

## Cau Truc Du An

```
ssi-identity-system/
contracts/              [NHAN - DA XONG]
  DID_Registry.vy
  deploy.py
  tests/
  requirements.txt
  HANDOVER.md

backend/                [THUY - CAN LAM]
  main.py
  routers/
  services/
  models/
  tests/
  requirements.txt

frontend/               [PHUC - CAN LAM]
  creator.html
  user.html
  verifier.html
  css/
  js/

nft-integration/        [NHU - CAN LAM]
  Soulbound_Contract.vy
  deploy.py
  integration.py
  tests/

shared/                 [DUNG CHUNG]
  abis/
    DID_Registry.json   [DA CO]
  constants.py          [DA CAP NHAT]
  constants.js          [DA CAP NHAT]

scripts/
  deploy.py             [Deploy DID_Registry]
  start_local_node.sh
  deploy_all.sh
  run_tests.sh

.env                    [KHONG COMMIT]
.env.example
.gitignore
ape-config.yaml
pyproject.toml
README.md
SETUP_GUIDE.md          [FILE NAY]
```

---

## Cau Hoi Thuong Gap

### Q: Lam sao biet backend dang chay?
A: Mo http://localhost:8000/docs - neu thay Swagger UI la backend dang chay.

### Q: Lam sao test contract sau khi sua?
A: `ape compile && pytest contracts/tests/ -v`

### Q: Lam sao deploy lai contract sau khi sua?
A: `ape run deploy --network ethereum:local` (nhap passphrase: test123)

### Q: Lam sao xem dia chi contract hien tai?
A: `cat shared/constants.py | grep DID_REGISTRY_ADDRESS`

### Q: Anvil bi tat, lam sao khoi dong lai?
A: `anvil` (terminal moi), sau do deploy lai contract.

### Q: Quen passphrase cua ape account?
A: Xoa account cu: `ape accounts delete anvil_deployer`
   Import lai: `ape accounts import anvil_deployer`

---

## Lien He

Neu gap van de, hoi trong nhom hoac xem:
- `contracts/HANDOVER.md` - tai lieu chi tiet cho Thuy va Phuc
- `README.md` - tong quan du an
- `.env.example` - cac bien moi truong can thiet
