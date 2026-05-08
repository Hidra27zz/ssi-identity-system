# Changelog — SSI Identity System

Tong hop tat ca cac thay doi da thuc hien trong qua trinh phat trien.

---

## Backend

### backend/main.py
- Them `StaticFiles` de serve frontend tai `/` va `shared/` tai `/shared/`
- Doi `allow_origins=["*"]` de frontend cung origin hoat dong
- Them import `StaticFiles`, `RedirectResponse`, `Path`
- Ket qua: chay 1 lenh `uvicorn` la co ca API lan website

### backend/services/blockchain_service.py
- `_send_tx()`: them `wait_for_transaction_receipt(timeout=120)` — biet tx thanh cong hay fail
- Them `get_did_record_full()`: tra ve day du tat ca fields cua DIDRecord (created_at, verified_at, updated_at, doc_hash)
- Them `invalidate_all_tokens_of_owner()`: invalidate tat ca NFT con hieu luc khi revoke DID
- Them `verify_nft_access()`: kiem tra quyen truy cap dua tren Soulbound Token (token-gated access)
- Them `get_soulbound_token_data()`: lay chi tiet 1 token theo token_id
- Sua `mint_soulbound_token()`: them tham so `credential_type` (contract moi yeu cau 3 tham so)
- Sua `check_soulbound_token()`: tra ve `tokens` (list) thay vi `token_id` don le
- Sua `invalidate_soulbound_token()`: nhan `token_id` (int) thay vi `owner_address`

### backend/routers/did.py
- `POST /store-hash`: sua thu tu — goi blockchain TRUOC, ghi DB SAU (tranh inconsistent state)
- `POST /store-hash`: them kiem tra wallet co trong cache truoc khi xu ly
- `GET /record/{address}`: goi `get_did_record_full()` thay vi `verify_did_on_chain()` — tra ve day du fields
- `POST /revoke`: tu dong goi `invalidate_all_tokens_of_owner()` sau khi revoke DID
- `POST /revoke`: response tra them `invalidated_nft_txs`
- Them `GET /public-key/{address}`: lay public key RSA cua user tu did_cache
- Them `GET /stats`: thong ke tong DID

### backend/routers/ipfs.py
- Them ham `_require_creator_role()`: RBAC check — chi Identity Creator moi duoc upload
- `POST /upload`: them tham so `creator_address`, goi RBAC check truoc khi xu ly
- `POST /upload/metadata`: them tham so `creator_address`, goi RBAC check
- `POST /retrieve/{cid}`: doi tu GET sang POST — private key truyen qua body, khong qua URL
- `POST /retrieve/{cid}`: them kiem tra `expires_at` — consent het han thi tu choi
- Them docstring giai thich RBAC cho tung endpoint

### backend/routers/nft.py
- Sua `POST /mint`: them tham so `credential_type` trong `MintRequest`
- Them `GET /token/{token_id}`: lay chi tiet 1 token
- Them `POST /invalidate/{token_id}`: vo hieu hoa token theo token_id
- Them `GET /verify-access/{address}`: kiem tra quyen truy cap (token-gated access)

### backend/routers/crypto.py
- `POST /generate-keypair`: doi tu query param sang request body (`GenerateKeypairRequest`)

### backend/routers/consent.py
- Them `GET /history/{did}`: lay lich su tat ca consent (pending + approved + rejected)
- Them docstring cho `GET /pending/{did}`

### backend/models/database.py
- Khong thay doi schema, giu nguyen 4 bang

### backend/tests/test_crypto_service.py
- Them `deadline=None` vao 2 property-based tests — fix loi Hypothesis DeadlineExceeded
- RSA key generation mat ~200-500ms, vuot deadline mac dinh 200ms cua Hypothesis

---

## Frontend

### frontend/main.py (backend/main.py)
- Frontend duoc serve boi FastAPI — mo trinh duyet vao `http://localhost:8000/user.html`

### frontend/user.html
- Viet lai hoan toan tu skeleton
- Them nav links giua 3 trang
- Them role badge "User"
- 5 card day du: Tao Keypair, Tao DID, Xem DID, Soulbound Token, Consent
- Them step numbers, warning box cho private key

### frontend/creator.html
- Viet lai hoan toan tu skeleton
- 6 buoc ro rang: Thong tin user, Upload anh, Upload PDF, Upload metadata, Gui hash, Danh sach cho
- Them preview anh truoc khi upload
- Them truong `creator_address` de RBAC check

### frontend/verifier.html
- Viet lai hoan toan tu skeleton
- 4 chuc nang: Xac minh DID, Kiem tra NFT/token-gated, Xin consent, Tai file
- Them nut "Xem chi tiet day du" goi `/api/did/record/{address}`
- Them section tai file voi private key input

### frontend/js/api.js
- Viet lai hoan toan
- Them `showToast()`: toast notification thay cho alert()
- Them `setLoading()`: loading state cho buttons
- Them `apiPost()`: helper cho POST JSON
- Them `apiRetrieve()`: helper tra ve Blob (cho tai file)
- Them `store`: localStorage/sessionStorage helpers
- Them `statusBadge()`, `formatTs()`: helper hien thi
- `BACKEND_URL = ""`: same origin, khong can hardcode port

### frontend/js/user.js
- Viet lai hoan toan tu skeleton
- Auto-fill tu localStorage khi load trang
- `generateKeypair()`: goi POST voi body (da fix tu query param)
- Them `createDID()`: tao DID tren blockchain
- Them `autoFillDID()`: tu dong dien `did:ssi:{address}`
- `loadDIDInfo()`: hien thi day du fields (created_at, verified_at, update_count)
- `checkNFT()`: goi ca `/nft/status` va `/nft/verify-access`, hien thi tung token chi tiet
- `loadPendingConsents()`: hien thi danh sach dep, co nut Dong y / Tu choi
- Them `savePrivateKeyToSession()`: luu private key vao sessionStorage

### frontend/js/creator.js
- Viet lai hoan toan tu skeleton
- `fetchPublicKey()`: goi `GET /api/did/public-key/{address}` thay vi prompt()
- `previewPortrait()`: hien thi preview anh truoc khi upload
- `uploadFile()`: truyen them `creator_address` vao FormData (RBAC)
- `uploadMetadata()`: truyen them `creator_address` vao FormData (RBAC)
- `storeHash()`: hien thi trang thai ro rang, link Etherscan
- `loadPendingList()`: hien thi danh sach DID cho xac minh
- `fillFromPending()`: dien nhanh thong tin tu danh sach cho

### frontend/js/verifier.js
- Viet lai hoan toan tu skeleton
- `verifyDID()`: hien thi status box mau sac, auto-fill consent form
- `loadFullRecord()`: goi `/api/did/record/{address}` hien thi doc_hash, timestamps
- `checkNFTAccess()`: goi `/api/nft/verify-access/{address}`, hien thi ro co/khong co quyen
- `requestConsent()`: co input field thay vi prompt()
- `retrieveFile()`: tai file tu IPFS, giai ma, hien thi anh hoac mo PDF

### frontend/css/style.css
- Viet lai hoan toan
- Them: page-header, role-badge, nav-links, step-number, card-title
- Them: btn-row, btn-success, btn-danger, btn-sm
- Them: info-row, info-label, info-value
- Them: token-item, consent-item, consent-actions
- Them: access-granted, access-denied
- Them: spinner animation, toast animation
- Them: file-preview, warning-box
- Them: responsive cho man hinh nho

---

## NFT Integration

### nft-integration/deploy.py
- Tao moi — file nay chua ton tai truoc do
- Deploy `Soulbound_Contract.vy` bang Ape Framework
- Tu dong export ABI vao `shared/abis/Soulbound_Contract.json`
- Tu dong cap nhat `SOULBOUND_ADDRESS` trong `constants.py` va `constants.js`

### nft-integration/integration.py
- Xoa emoji trong assert messages va FileNotFoundError (theo rule no-emoji)

---

## Shared

### shared/constants.js
- `BACKEND_URL = ""`: doi tu `http://localhost:8000` sang empty string (same origin)
- Contracts tren Sepolia da co dia chi thuc

### shared/constants.py
- `CHAIN_ID = CHAIN_ID_SEPOLIA`: dang tro Sepolia (11155111)

---

## Scripts

### scripts/deploy.py
- Xoa — trung lap voi `contracts/deploy.py`

### scripts/deploy_web3.py
- Xoa — trung lap voi `contracts/deploy.py`

### scripts/deploy_all.sh
- Viet lai co dau tieng Viet
- Them ghi chu nhac cap nhat CHAIN_ID khi chay local

---

## Config

### .env
- `RPC_URL`: doi sang `https://ethereum-sepolia-rpc.publicnode.com` (public Sepolia RPC, khong can key)
- `DID_REGISTRY_ADDRESS`: `0x4442864E86805E1c5C8759ED1047Ef4802Ce15Ee` (Sepolia)
- `SOULBOUND_ADDRESS`: `0xD3B88E485c8Ad25FeCeF28f9eb0DD7f7e73EdC2D` (Sepolia)
- `IPFS_API_KEY` va `IPFS_SECRET_KEY`: da dien key Pinata thuc
- `CHAIN_ID`: 11155111 (Sepolia)
- Con thieu: `PRIVATE_KEY` — can dien private key vi Sepolia de gui transaction

### .env.example
- Them canh bao ro rang: private key Anvil chi dung cho local, khong dung tren Sepolia/Mainnet

### .kiro/steering/code-style.md
- Tao moi — rule: khong dung emoji trong source code (.py, .js, .vy, .sh, .yaml)
- Emoji chi duoc phep trong file .md

---

## Tests

Ket qua cuoi cung: **89 passed, 0 failed**

```
backend/tests/test_crypto_service.py   8 tests  (fix deadline=None cho 2 property tests)
backend/tests/test_ipfs_service.py     5 tests
contracts/tests/test_did_registry.py  67 tests
nft-integration/tests/test_soulbound.py 9 tests
```

---

## Cach chay he thong

```bash
# Cai dat (chi can 1 lan)
bash setup.sh

# Chay backend + frontend (1 lenh duy nhat)
source venv/bin/activate
uvicorn backend.main:app --reload --port 8000

# Mo trinh duyet
http://localhost:8000/user.html      -- Identity User
http://localhost:8000/creator.html   -- Identity Creator
http://localhost:8000/verifier.html  -- Identity Verifier
http://localhost:8000/docs           -- API Documentation

# Chay NFT Orchestrator (terminal rieng, tuy chon)
source venv/bin/activate
python nft-integration/integration.py
```

**Luu y quan trong:** Dien `PRIVATE_KEY` cua vi Sepolia vao `.env` truoc khi demo.
Khong co private key thi chi doc duoc du lieu, khong gui duoc transaction.
