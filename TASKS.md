# Danh sách Task - Dự án SSI

---

## Phần 1: Backend — Các điểm đã cải thiện

### B1. Thêm `wait_for_receipt` sau khi gửi transaction ✅ Đã xong

`_send_tx()` giờ gọi `w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)`.
Nếu `receipt.status == 0` thì raise lỗi "Transaction reverted on-chain".
Tất cả transaction đều được xác nhận trước khi trả về kết quả.

---

### B2. Revoke DID tự động invalidate NFT ✅ Đã xong

Thêm hàm `invalidate_all_tokens_of_owner()` trong `blockchain_service.py`.
`POST /api/did/revoke` giờ tự động invalidate tất cả Soulbound Token còn hiệu lực của địa chỉ đó.
Lỗi từng token được log nhưng không làm fail toàn bộ request revoke.
Response trả thêm `invalidated_nft_txs` — danh sách tx_hash đã invalidate.

---

### B3. Token-gated access ✅ Đã xong

Thêm `GET /api/nft/verify-access/{address}` trả về:
- `has_access`: true/false
- `reason`: giải thích lý do
- `has_valid_token`: có token hợp lệ không
- `token_count`: tổng số token

Frontend dùng endpoint này để gate quyền truy cập dịch vụ theo yêu cầu đề bài.

---

### B4. `generate-keypair` dùng request body ✅ Đã xong

Đổi từ query param sang `GenerateKeypairRequest` body.
Frontend gọi bằng `POST` với JSON body `{ "wallet_address": "0x..." }`.

---

### B5. Endpoint lấy public key của user ✅ Đã xong

Thêm `GET /api/did/public-key/{address}`.
Creator gọi endpoint này để lấy public key RSA của user trước khi mã hóa file.
Không cần `prompt()` trong frontend nữa.

---

### B6. Lịch sử consent ✅ Đã xong

Thêm `GET /api/consent/history/{did}` trả toàn bộ consent (pending + approved + rejected).

---

## Phần 2: Frontend — Các trang cần xây dựng

> File mẫu đã có sẵn: `user.html`, `creator.html`, `verifier.html`, `api.js`, `user.js`, `creator.js`, `verifier.js`
> Cần hoàn thiện logic và UI cho từng trang.

---

### F1. Trang User (`user.html` + `user.js`)

**1. Tạo cặp khóa RSA**
- Input: địa chỉ ví
- Gọi `POST /api/crypto/generate-keypair` với body `{ "wallet_address": "0x..." }`
- Hiển thị public key và private key
- Nút "Tải Private Key" lưu file `.pem` về máy
- Cảnh báo rõ ràng: "Đây là lần duy nhất bạn thấy private key"

**2. Tạo DID**
- Input: địa chỉ ví, chuỗi DID (gợi ý tự động: `did:ssi:{address}`)
- Gọi `POST /api/did/create`
- Hiển thị tx_hash và link block explorer

**3. Xem thông tin DID**
- Input: địa chỉ ví
- Gọi `GET /api/did/record/{address}`
- Hiển thị: DID, trạng thái (PENDING/VERIFIED/REVOKED), CID, ngày tạo, ngày xác minh, số lần cập nhật

**4. Kiểm tra Soulbound Token**
- Input: địa chỉ ví
- Gọi `GET /api/nft/status/{address}`
- Nếu có token: hiển thị danh sách token_id, nút xem chi tiết từng token
- Gọi `GET /api/nft/token/{token_id}` để hiển thị: credential_type, metadata_uri, is_valid, minted_at

**5. Quản lý consent (User phê duyệt/từ chối)**
- Input: DID của mình
- Gọi `GET /api/consent/pending/{did}` hiển thị danh sách yêu cầu đang chờ
- Mỗi yêu cầu hiển thị: ai xin (requester_address), loại dữ liệu, thời gian
- Nút "Đồng ý" gọi `POST /api/consent/respond` với `decision: "approved"`
- Nút "Từ chối" gọi `POST /api/consent/respond` với `decision: "rejected"`
- Tự động refresh danh sách sau khi phản hồi

---

### F2. Trang Creator (`creator.html` + `creator.js`)

**1. Nhập thông tin người dùng**
- Input: địa chỉ ví người dùng, DID người dùng
- Nút "Lấy public key" gọi `GET /api/did/public-key/{address}`
- Hiển thị trạng thái: "Đã lấy public key" (ẩn giá trị, chỉ dùng nội bộ)

**2. Upload ảnh chân dung**
- Input: chọn file JPG/PNG
- Hiển thị preview ảnh trước khi upload
- Gọi `POST /api/upload` với file + public_key + did
- Hiển thị CID sau khi upload thành công

**3. Upload file PDF**
- Input: chọn file PDF
- Gọi `POST /api/upload` với file + public_key + did
- Hiển thị CID và doc_hash sau khi upload thành công
- doc_hash và CID tự động điền vào form bước tiếp theo

**4. Upload metadata JSON**
- Sau khi có cả 2 CID (ảnh + PDF), hiển thị nút "Tạo Metadata"
- Gọi `POST /api/upload/metadata` với: did, doc_type, issued_by, portrait_cid, document_cid
- Hiển thị metadata CID

**5. Gửi hash lên blockchain**
- Hiển thị tóm tắt: wallet_address, doc_hash, cid, creator_address
- Nút "Xác nhận và Gửi" gọi `POST /api/did/store-hash`
- Hiển thị tx_hash và link block explorer
- Hiển thị trạng thái: "Đang xử lý..." → "Thành công" / "Thất bại"

**6. Xem danh sách chờ xác minh**
- Gọi `GET /api/did/pending`
- Hiển thị danh sách các DID đang ở trạng thái "submitted"
- Mỗi item có nút "Xác minh" để điền nhanh vào form

---

### F3. Trang Verifier (`verifier.html` + `verifier.js`)

**1. Xác minh DID**
- Input: địa chỉ ví
- Gọi `GET /api/did/verify/{address}`
- Hiển thị rõ ràng: VERIFIED (xanh) / PENDING (vàng) / REVOKED (đỏ) / NOT FOUND (xám)
- Hiển thị thêm: DID, CID, verified_by, update_count

**2. Xem chi tiết DID Record**
- Sau khi verify, nút "Xem chi tiết" gọi `GET /api/did/record/{address}`
- Hiển thị đầy đủ: created_at, verified_at, updated_at, doc_hash

**3. Kiểm tra NFT — Token-gated access**
- Input: địa chỉ ví
- Gọi `GET /api/nft/verify-access/{address}`
- Hiển thị rõ: "Có quyền truy cập" (xanh) / "Không có quyền" (đỏ) + lý do
- Đây là bước thể hiện token-gated access theo yêu cầu đề bài

**4. Yêu cầu truy cập dữ liệu — Consent flow**
- Input: DID của chủ sở hữu, loại dữ liệu (portrait/document/metadata), địa chỉ ví của mình
- Gọi `POST /api/consent/request`
- Hiển thị consent_id và hướng dẫn: "Chờ chủ sở hữu phê duyệt"

**5. Tải và xem file (sau khi có consent)**
- Input: CID (lấy từ kết quả verify), private key của mình
- Gọi `POST /api/retrieve/{cid}` với body: `{ "private_key": "...", "owner_did": "...", "requester_address": "..." }`
- Hiển thị file: nếu là ảnh thì render `<img>`, nếu là PDF thì mở tab mới

---

### F4. Yêu cầu chung cho cả 3 trang

**UX / Trạng thái:**
- Mỗi nút bấm phải có trạng thái loading (disable nút + hiển thị "Đang xử lý...")
- Hiển thị lỗi rõ ràng khi API thất bại, không dùng `alert()` thuần túy
- Sau khi thành công hiển thị thông báo xanh, thất bại hiển thị đỏ

**CSS cần bổ sung:**
- Badge trạng thái: `pending` (vàng), `verified` (xanh), `revoked` (đỏ), `not_found` (xám) — đã có skeleton trong `style.css`
- Loading spinner
- Toast notification thay cho `alert()`
- Responsive cho màn hình nhỏ

**Lưu trữ local:**
- Lưu `walletAddress` vào `localStorage` để không phải nhập lại
- Lưu `privateKey` vào `sessionStorage` (chỉ trong phiên làm việc, xóa khi đóng tab)
- Lưu `did` vào `localStorage`

**Kết nối API:**
- `api.js` đã có `apiFetch` và `apiUpload` — dùng lại, không viết lại
- Thêm hàm `apiPost(path, body)` cho các POST request JSON cho gọn
- Xử lý lỗi 403 (hết consent / không có quyền) và 503 (IPFS down) riêng biệt

---

## Phần 3: Deploy — Các vấn đề cần lưu ý

### D1. Thiếu deploy script cho Soulbound Contract ⚠️

`scripts/deploy_all.sh` gọi `ape run nft-integration/deploy` nhưng file `nft-integration/deploy.py` không tồn tại.
Chỉ có `contracts/deploy.py` và `scripts/deploy.py` cho DID_Registry.

**Cần tạo:** `nft-integration/deploy.py` để deploy `Soulbound_Contract.vy` và export ABI.

### D2. Hai file deploy trùng lặp

`contracts/deploy.py` và `scripts/deploy.py` đều deploy DID_Registry với logic gần giống nhau.
- `contracts/deploy.py` dùng `accounts.test_accounts[0]` cho local (không cần import account)
- `scripts/deploy.py` dùng `accounts.load("anvil_deployer")` (cần import account trước)

**Khuyến nghị:** Dùng `contracts/deploy.py` làm chuẩn vì đơn giản hơn cho môi trường local.

### D3. `deploy_all.sh` dùng sai đường dẫn

```bash
# Hiện tại (sai — không có file này)
ape run nft-integration/deploy --network $NETWORK

# Nên là
ape run nft-integration/deploy --network $NETWORK
# Nhưng cần tạo nft-integration/deploy.py trước (xem D1)
```

### D4. `scripts/deploy_web3.py` cần có ABI và bytecode trước khi chạy

Script này đọc `DID_Registry.json` và `DID_Registry.bin` từ `shared/abis/` nhưng 2 file này chỉ có sau khi compile bằng Ape.
Thứ tự đúng: compile bằng Ape → chạy `deploy_web3.py`.

### D5. `shared/constants.py` hiện đang trỏ đến Sepolia

```python
# Hiện tại
CHAIN_ID = CHAIN_ID_SEPOLIA  # 11155111
```

Khi chạy local cần đổi thành `CHAIN_ID = CHAIN_ID_LOCAL` (31337).
Script deploy tự động cập nhật địa chỉ contract nhưng không cập nhật CHAIN_ID.

---

## Tóm tắt theo mức độ ưu tiên

### Backend (đã hoàn thành)
| # | Task | Trạng thái |
|---|------|-----------|
| B1 | wait_for_receipt | Đã xong |
| B2 | Revoke DID tự động invalidate NFT | Đã xong |
| B3 | Token-gated access endpoint | Đã xong |
| B4 | generate-keypair dùng body | Đã xong |
| B5 | Endpoint lấy public key | Đã xong |
| B6 | Lịch sử consent | Đã xong |

### Frontend (Phúc làm)
| # | Trang | Mức độ |
|---|-------|--------|
| F1 | user.html — Tạo keypair, tạo DID, xem DID, quản lý consent | Cao |
| F2 | creator.html — Upload 3 loại file, gửi hash blockchain | Cao |
| F3 | verifier.html — Verify DID, check NFT, consent flow, tải file | Cao |
| F4 | Chung — Loading state, error handling, localStorage | Trung bình |

### Deploy (cần xử lý trước khi demo)
| # | Task | Mức độ |
|---|------|--------|
| D1 | Tạo `nft-integration/deploy.py` cho Soulbound Contract | Cao |
| D2 | Thống nhất dùng 1 deploy script cho DID_Registry | Thấp |
| D3 | Fix `deploy_all.sh` sau khi có D1 | Cao |
| D4 | Đảm bảo compile trước khi chạy `deploy_web3.py` | Trung bình |
| D5 | Cập nhật CHAIN_ID trong `shared/constants.py` khi chạy local | Trung bình |
