Dưới đây là nội dung phân tích thiết kế hệ thống được viết lại dưới dạng Markdown, trình bày rõ ràng, có cấu trúc để bạn có thể lưu vào file `.md` và sử dụng cho báo cáo đồ án.

```markdown
# Phân tích & Thiết kế hệ thống chi tiết – Đồ án SSI (Self‑Sovereign Identity)

## 1. Tổng quan hệ thống

Hệ thống **Định danh phi tập trung (SSI)** cho phép người dùng tự quản lý danh tính, được cấp chứng chỉ bởi các cơ quan có thẩm quyền (Identity Creator) và chia sẻ có kiểm soát với bên thứ ba (Verifier). Ứng dụng được xây dựng trên blockchain Ethereum (local), IPFS, backend FastAPI, frontend React.

### 1.1 Mục tiêu
- Tạo DID gắn với địa chỉ ví Ethereum.
- Lưu mã hash (CID) của tài liệu định danh lên blockchain, file gốc lưu trên IPFS.
- Identity Creator xác nhận tài liệu, lưu chữ ký số, mint NFT soulbound.
- Verifier kiểm tra tính hợp lệ chỉ khi được chủ sở hữu đồng ý (explicit consent).
- Đảm bảo tính riêng tư: không lưu PII on‑chain, hỗ trợ mã hóa RSA.

### 1.2 Phạm vi
- **Smart contract** (Vyper) – quản lý DID, credential, consent, NFT soulbound.
- **Backend** (FastAPI) – trung gian IPFS, lưu yêu cầu tạm thời (SQLite), cung cấp API cho frontend.
- **Frontend** (React.js) – giao diện cho 3 loại người dùng, kết nối MetaMask.

---

## 2. Kiến trúc tổng thể

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React Frontend │────▶│  FastAPI Backend │────▶│   IPFS Node     │
│  (MetaMask, UI)  │◀────│ (Web3.py, SQLite)│     │ (storage/gateway)│
└────────┬────────┘     └────────┬────────┘     └─────────────────┘
         │                        │
         │ (ethers.js)            │ (read only)
         ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Ethereum Blockchain (Geth local)             │
│                      Smart Contract: SSIdentity.vy               │
│   - DID mapping  - Credential storage  - Consent  - NFT soulbound│
└─────────────────────────────────────────────────────────────────┘
```

### 2.1 Thành phần chính

| Thành phần | Công nghệ | Vai trò |
|------------|-----------|---------|
| Blockchain | Ethereum (Geth local / Sepolia) | Lưu trạng thái bất biến: DID, credential hash, consent, NFT |
| Smart contract | Vyper 0.4.3 | Logic quản lý định danh, token soulbound |
| IPFS | IPFS daemon / Infura | Lưu file ảnh, PDF, metadata JSON – trả CID |
| Backend | FastAPI (Python), SQLite | Upload/download IPFS, quản lý yêu cầu off‑chain, REST API |
| Frontend | React.js + Ethers.js | Giao diện người dùng, kết nối MetaMask, gọi contract, mã hóa RSA |

---

## 3. Smart contract – Thiết kế chi tiết

### 3.1 Cấu trúc dữ liệu

```vyper
# DID
didOf: HashMap[address, bytes32]

# Credential
struct CredentialInfo:
    cid: bytes32               # IPFS CID (32 bytes)
    creator: address
    signature: Bytes[128]      # chữ ký của creator
    revoked: bool
    timestamp: uint256

userCredentials: HashMap[address, DynArray[bytes32, 50]]
credentialDetails: HashMap[bytes32, CredentialInfo]

# Consent
consents: HashMap[address, HashMap[address, bool]]  # user -> verifier -> bool

# NFT soulbound (ERC-721 nhưng transfer bị khóa)
nftOwner: HashMap[uint256, address]
nftBalance: HashMap[address, uint256]
nftForUser: HashMap[address, uint256]   # mỗi user 1 NFT
```

### 3.2 Hàm chính

| Hàm | Modifier | Mô tả |
|-----|----------|-------|
| `createDID(did: bytes32)` | public | User tự đăng ký DID. |
| `storeCredential(user, cid, signature)` | onlyCreator | Lưu credential, ghi nhận creator, timestamp. |
| `revokeCredential(user, cid)` | onlyCreator / user | Đánh dấu revoked = true. |
| `grantConsent(verifier)` | public | User cấp quyền cho verifier. |
| `revokeConsent(verifier)` | public | Thu hồi quyền. |
| `verifyCredential(user, cid)` | view, có kiểm tra consent | Trả về (valid, creator, timestamp). |
| `mintIdentityNFT(user, tokenId)` | onlyCreator | Tạo NFT soulbound, không thể transfer. |
| `balanceOf`, `ownerOf` | view | Chuẩn ERC-721. |

### 3.3 Bảo mật
- `onlyCreator` được kiểm tra qua mapping `isCreator`.
- `verifyCredential` yêu cầu `consents[user][msg.sender] == True`.
- Hàm `transferFrom` và `safeTransferFrom` luôn `revert` để đảm bảo soulbound.

---

## 4. Backend FastAPI – Thiết kế API

### 4.1 Công nghệ
- Python 3.10, FastAPI, Uvicorn.
- SQLite lưu: `verification_requests`, `consent_requests`, `users` (tùy chọn).
- IPFS: dùng `ipfshttpclient` kết nối daemon local hoặc HTTP API của Pinata/Infura.

### 4.2 Các endpoint chính

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/ipfs/upload` | POST | Nhận file, upload lên IPFS, trả CID. |
| `/api/ipfs/get/<cid>` | GET | Proxy tải file từ IPFS gateway. |
| `/api/request/create` | POST | Tạo yêu cầu xác thực (user gửi đến creator). |
| `/api/request/list/<creator_address>` | GET | Lấy danh sách yêu cầu chờ của creator. |
| `/api/request/update/<id>` | PUT | Cập nhật trạng thái (approved/rejected). |
| `/api/consent/request` | POST | Verifier gửi yêu cầu consent đến user. |
| `/api/consent/requests/<user_address>` | GET | User xem danh sách yêu cầu consent. |
| `/api/nft/metadata/<tokenId>` | GET | Trả về metadata JSON cho NFT (từ DB hoặc IPFS). |
| `/api/user/role/<address>` | GET | Xác định role – dựa vào `isCreator` của contract. |

> **Lưu ý**: Backend không lưu private key. Mọi giao dịch ghi (storeCredential, mint, grantConsent) do frontend gọi trực tiếp contract qua MetaMask.

### 4.3 Xử lý IPFS
- **Upload**: nhận file → tạm lưu → gọi client.add → xóa file tạm → trả CID.
- **Download**: nhận CID → lấy từ IPFS gateway → stream về client.

---

## 5. Frontend React – Thiết kế chi tiết

### 5.1 Công nghệ
- React 18, Vite, React Router DOM.
- Ethers.js (kết nối MetaMask, gọi contract).
- Axios (gọi backend API).
- Web Crypto API (mã hóa RSA), react-dropzone (upload file).
- Chakra UI hoặc Material-UI (tuỳ chọn).

### 5.2 Cấu trúc thư mục

```
src/
├── components/
│   ├── Layout/           (Header, Sidebar)
│   ├── WalletConnector/  (kết nối MetaMask)
│   ├── IPFSUploader/     (upload file, hiển thị CID)
│   ├── TransactionToast/ (thông báo giao dịch)
│   └── ConsentManager/   (quản lý consent)
├── pages/
│   ├── UserDashboard/
│   ├── CreatorDashboard/
│   ├── VerifierDashboard/
│   └── PremiumGate/      (token-gated content)
├── hooks/
│   ├── useWeb3.js
│   ├── useContract.js
│   └── useIPFS.js
├── services/
│   ├── api.js
│   └── metadata.js
├── utils/
│   ├── rsa.js
│   └── constants.js
├── App.jsx
└── main.jsx
```

### 5.3 Luồng giao diện từng role

#### User Dashboard
- **Thông tin DID**: hiển thị, nút “Create DID”.
- **Upload file**: kéo thả file (ảnh, PDF, JSON), tùy chọn mã hóa RSA bằng public key Creator → upload → hiển thị CID.
- **Yêu cầu xác thực**: chọn CID, chọn Creator → gửi yêu cầu (backend).
- **Credential đã cấp**: hiển thị CID, trạng thái, nút revoke.
- **Quản lý Consent**: danh sách verifier đã cấp quyền, danh sách yêu cầu mới → nút approve/revoke.
- **NFT Soulbound**: hiển thị tokenId và metadata.

#### Creator Dashboard
- Chỉ hiển thị nếu địa chỉ có `isCreator == true`.
- **Danh sách yêu cầu**: mỗi yêu cầu có CID, nút “View File” (tải từ IPFS), nếu file mã hóa thì yêu cầu nhập private key RSA để giải mã.
- **Nút Approve**: ký bằng MetaMask (payload user + CID) → gọi `storeCredential` → gọi `mintIdentityNFT`.
- **Lịch sử credential đã cấp**: xem danh sách.

#### Verifier Dashboard
- **Tìm kiếm user**: nhập địa chỉ.
- **Chọn credential**: dropdown lấy từ `userCredentials[user]`.
- **Yêu cầu consent**: gửi request qua backend.
- **Kiểm tra consent**: gọi contract `consents[user][verifier]`.
- **Xác minh**: gọi `verifyCredential` → hiển thị kết quả.
- **Xem metadata**: tải từ IPFS.

#### Premium Content (Token-gated)
- Đường dẫn `/premium` kiểm tra `balanceOf(account) > 0` → nếu đúng mới hiển thị nội dung.

---

## 6. Cơ sở dữ liệu SQLite (backend)

```sql
CREATE TABLE verification_requests (
    id INTEGER PRIMARY KEY,
    user_address TEXT NOT NULL,
    creator_address TEXT NOT NULL,
    cid TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- 'pending', 'approved', 'rejected'
    created_at INTEGER DEFAULT (strftime('%s','now'))
);

CREATE TABLE consent_requests (
    id INTEGER PRIMARY KEY,
    user_address TEXT NOT NULL,
    verifier_address TEXT NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'approved'
    created_at INTEGER
);

CREATE TABLE nft_metadata (
    tokenId INTEGER PRIMARY KEY,
    name TEXT,
    description TEXT,
    image_url TEXT,
    attributes TEXT
);
```

---

## 7. Bảo mật và quyền riêng tư

- **Không lưu PII on‑chain**: chỉ lưu CID và chữ ký. Nội dung nhạy cảm có thể mã hóa trước khi lên IPFS.
- **Explicit consent**: mọi xác minh đều cần user chủ động gọi `grantConsent`.
- **Soulbound NFT**: không thể chuyển nhượng, định danh gắn liền với user.
- **Private key**: không lưu trong backend; frontend dùng MetaMask, user tự quản lý.
- **JWT (tùy chọn)**: backend có thể phát token sau khi xác thực bằng chữ ký Ethereum (SIWE).

---

## 8. Luồng chính – Tóm tắt bằng sơ đồ

```
[User]                 [Backend]            [Blockchain]           [Creator]            [Verifier]
   |                       |                      |                     |                    |
   |-- createDID() --------------------------------->|                     |                    |
   |-- upload file ------->|                      |                     |                    |
   |<-- CID --------------|                       |                     |                    |
   |-- request verification ----------------------->| (lưu SQLite)        |                    |
   |                       |                      |                     |                    |
   |                       |<-- list requests ----|                    |
   |                       |-- approve & sign ------------------------------>| (MetaMask)       |
   |                       |                      |<-- storeCredential ---|                    |
   |                       |                      |<-- mintNFT -----------|                    |
   |                       |                      |                     |                    |
   |                       |                      |                     |-- request consent->| (backend)
   |<-- consent request ---|                      |                     |                    |
   |-- grantConsent() ----------------------------->|                     |                    |
   |                       |                      |                     |                    |
   |                       |                      |<-- verifyCredential ----------------| (Verifier)
   |                       |                      |-- result ---------->|                    |
```

---

## 9. Kết luận

Hệ thống SSI được thiết kế đáp ứng đầy đủ 4 tiêu chí: smart contract quản lý DID/credential/consent, frontend 3 role, IPFS, NFT soulbound. Kiến trúc phân tách rõ ràng: blockchain lưu trạng thái bất biến, backend hỗ trợ off‑chain, frontend cung cấp trải nghiệm người dùng. Áp dụng các kỹ thuật từ 5 lab thực hành: Vyper, Web3.py, DApp GUI, mã hóa RSA, NFT. Đây là nền tảng vững chắc để triển khai mã nguồn và báo cáo đồ án.
```