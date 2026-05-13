# Hướng dẫn chạy hệ thống SSI trên trình duyệt

## Bước 0 — Khởi động backend (bắt buộc)

Mở terminal, chạy lệnh sau:

```bash
cd /Users/hidra/Downloads/HK6/Project/GitHub/ssi-identity-system
source venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

Kiểm tra: mở trình duyệt vào `http://localhost:8000/health` — thấy `{"status":"ok"}` là thành công.

---

## Bước 1 — Mở trang web

Mở trình duyệt vào:

```
http://localhost:8000
```

Trang chủ hiện ra với 3 vai trò: **User**, **Creator**, **Verifier**.

---

## Bước 2 — Trang User: Tạo tài khoản

Mở `http://localhost:8000/user.html`

### 2.1 Tạo cặp khóa RSA

| Ô nhập | Giá trị |
|--------|---------|
| Địa chỉ ví | `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` |

Nhấn **"Tạo Keypair"** → tải file `private_key.pem` về máy ngay.

### 2.2 Tạo DID

| Ô nhập | Giá trị |
|--------|---------|
| Địa chỉ ví | `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` |

Ô **"Chuỗi DID"** tự động điền thành `did:ssi:0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266` — không cần nhập tay.

Nhấn **"Tạo DID"** → gửi giao dịch lên blockchain Sepolia.

### 2.3 Xem thông tin DID

| Ô nhập | Giá trị |
|--------|---------|
| Địa chỉ ví | `0x32268B487ebaB849d8f40B1a12776a543fdFb79a` |

Nhấn **"Xem thông tin"** → thấy DID, trạng thái **VERIFIED**, CID từ blockchain thực.

---

## Bước 3 — Trang Creator: Xác minh tài liệu

Mở `http://localhost:8000/creator.html`

### 3.1 Xem danh sách chờ

Nhấn **"Tải danh sách"** → thấy các DID đang chờ xác minh.

### 3.2 Nhập thông tin người dùng

| Ô nhập | Giá trị |
|--------|---------|
| Địa chỉ ví người dùng | `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` |
| DID người dùng | `did:ssi:0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266` |

### 3.3 Upload ảnh chân dung

- Chọn file ảnh JPG hoặc PNG bất kỳ (tối đa 5MB)
- Nhấn **"Upload ảnh"** → thấy CID trả về từ IPFS

### 3.4 Upload file PDF

- Chọn file PDF bất kỳ (tối đa 10MB)
- Nhấn **"Upload PDF"** → thấy CID và hash

### 3.5 Tạo Metadata JSON

- Điền **"Cơ quan cấp"**: `Trường Đại Học ABC`
- Nhấn **"Tạo & Upload Metadata JSON"** → thấy CID thứ 3

### 3.6 Gửi hash lên blockchain

- Điền **"Địa chỉ Creator"**: `0x32268B487ebaB849d8f40B1a12776a543fdFb79a`
- Nhấn **"Gửi Hash lên Blockchain"** → giao dịch gửi lên Sepolia

---

## Bước 4 — Trang Verifier: Xác minh định danh

Mở `http://localhost:8000/verifier.html`

### 4.1 Xác minh DID

| Ô nhập | Giá trị |
|--------|---------|
| Địa chỉ ví | `0x32268B487ebaB849d8f40B1a12776a543fdFb79a` |

Nhấn **"Xác minh"** → thấy kết quả **VERIFIED** (viền xanh) từ blockchain Sepolia thực.

### 4.2 Kiểm tra Soulbound NFT

| Ô nhập | Giá trị |
|--------|---------|
| Địa chỉ ví | `0x32268B487ebaB849d8f40B1a12776a543fdFb79a` |

Nhấn **"Kiểm tra quyền truy cập"** → thấy **CÓ QUYỀN TRUY CẬP**.

### 4.3 Xin consent để xem tài liệu

| Ô nhập | Giá trị |
|--------|---------|
| DID chủ sở hữu | `did:ssi:0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266` |
| Địa chỉ ví của bạn | `0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC` |
| Loại dữ liệu | Tài liệu PDF |

Nhấn **"Gửi yêu cầu truy cập"** → thấy Consent ID.

---

## Bước 5 — Trang User: Phê duyệt consent

Quay lại `http://localhost:8000/user.html`

### 5.1 Xem yêu cầu đang chờ

| Ô nhập | Giá trị |
|--------|---------|
| DID của bạn | Tự động điền khi nhập địa chỉ ví ở bước 1 |

Nếu chưa tự điền, nhập: `did:ssi:0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266`

Nhấn **"Tải danh sách yêu cầu"** → thấy yêu cầu từ Verifier.

Nhấn **"Đồng ý"** → Verifier có 24 giờ để truy cập file.

---

## Tài khoản demo có sẵn

| Vai trò | Địa chỉ ví |
|---------|-----------|
| Creator (có DID VERIFIED thực) | `0x32268B487ebaB849d8f40B1a12776a543fdFb79a` |
| User 1 | `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` |
| User 2 | `0x70997970C51812dc3A010C7d01b50e0d17dc79C8` |
| Verifier | `0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC` |

---

## Chạy script demo tự động (không cần thao tác tay)

```bash
source venv/bin/activate
python scripts/demo_full_flow.py
```

Script sẽ tự động:
1. Tạo 3 account mới
2. Tạo keypair RSA
3. Upload ảnh + PDF + metadata lên IPFS
4. Xác minh DID
5. Gửi và phê duyệt consent
6. Tải và giải mã file từ IPFS
7. Kiểm tra Soulbound NFT

---

## Xem kết quả trên blockchain

- DID Registry Contract: https://sepolia.etherscan.io/address/0x4442864E86805E1c5C8759ED1047Ef4802Ce15Ee
- Soulbound NFT Contract: https://sepolia.etherscan.io/address/0xD3B88E485c8Ad25FeCeF28f9eb0DD7f7e73EdC2D
- Tất cả transactions: https://sepolia.etherscan.io/address/0x32268B487ebaB849d8f40B1a12776a543fdFb79a

---

## Xem API documentation

```
http://localhost:8000/docs
```

---

## Chạy test

```bash
source venv/bin/activate
python -m pytest backend/tests/ contracts/tests/ nft-integration/tests/ -v
```

Kết quả mong đợi: **89 passed, 0 failed**
