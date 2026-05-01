# Handover - DID Registry Contract
# Nguoi phu trach: Nhan
# Gui cho: Phuc (Frontend), Thuy (Backend)

## Sau khi deploy xong, lay thong tin o day:

### 1. ABI
File: shared/abis/DID_Registry.json
(Tu dong tao khi chay: ape run deploy)

### 2. Dia chi contract
File: shared/constants.py  -> DID_REGISTRY_ADDRESS
File: shared/constants.js  -> DID_REGISTRY_ADDRESS

### 3. Cac ham Frontend can goi (qua Backend API)

POST /api/did/create
  - Tao DID moi cho nguoi dung
  - Body: { wallet_address, did }

POST /api/did/store-hash
  - Creator luu hash tai lieu len blockchain
  - Body: { wallet_address, doc_hash, cid, creator_address }

GET /api/did/verify/{address}
  - Kiem tra DID co hop le khong
  - Tra ve: { is_valid, did, cid, status }

GET /api/did/record/{address}
  - Lay toan bo thong tin DID
  - Tra ve: DIDRecord day du

POST /api/did/revoke
  - Thu hoi DID
  - Body: { wallet_address }

### 4. Trang thai DID (status codes)
0 = PENDING   (chua xac minh)
1 = VERIFIED  (da xac minh)
2 = REVOKED   (da thu hoi)
255 = khong ton tai

### 5. Events co the lang nghe
- DIDCreated(owner, did, timestamp)
- DocumentHashStored(owner, doc_hash, cid, verified_by, timestamp)
- DocumentHashUpdated(owner, old_hash, new_hash, new_cid, updated_by, timestamp)
- DIDRevoked(owner, did, revoked_by, timestamp)
- CreatorRoleGranted(creator, granted_by)
- CreatorRoleRevoked(creator, revoked_by)
