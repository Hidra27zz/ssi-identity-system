# Hướng dẫn Demo cho Giáo viên

## Chuẩn bị trước khi demo (5 phút)

### Bước 1 — Khởi động backend

Mở terminal, chạy:

```bash
cd /Users/hidra/Downloads/HK6/Project/GitHub/ssi-identity-system
source venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

Kiểm tra: mở trình duyệt vào `http://localhost:8000` — thấy trang chủ là OK.

### Bước 2 — Chạy test suite (chứng minh code hoạt động)

Mở terminal thứ 2:

```bash
source venv/bin/activate
python -m pytest backend/tests/ contracts/tests/ nft-integration/tests/ --tb=short -v
```

Kết quả mong đợi: **89 passed, 0 failed**

---

## Kịch bản demo (15-20 phút)

### Phần 1 — Giới thiệu hệ thống (2 phút)

Mở `http://localhost:8000` — giải thích:

- Hệ thống SSI (Self-Sovereign Identity) — người dùng tự sở hữu danh tính
- 3 vai trò: User (người dùng), Creator (cơ quan cấp), Verifier (bên xác minh)
- Công nghệ: Ethereum Sepolia + IPFS Pinata + RSA encryption
- Contracts đã deploy trên Sepolia testnet

Mở `https://sepolia.etherscan.io/address/0x4442864E86805E1c5C8759ED1047Ef4802Ce15Ee` — chứng minh contract live.

---

### Phần 2 — Demo Verifier (đọc dữ liệu thực, không cần ví) (5 phút)

Mở `http://localhost:8000/verifier.html`

**Thao tác 1 — Xác minh DID đã có trên chain:**

Nhập vào ô tìm kiếm:
```
0x32268B487ebaB849d8f40B1a12776a543fdFb79a
```
Nhấn Enter hoặc "Xác minh".

Kết quả hiển thị:
- Trạng thái: **VERIFIED** (viền xanh)
- DID: `Nhu_Student_Profile`
- Đây là dữ liệu thực từ blockchain Sepolia

**Thao tác 2 — Kiểm tra Token-gated access:**

Nhập cùng địa chỉ vào ô "Kiểm tra quyền truy cập", nhấn nút.

Giải thích: NFT Soulbound gắn với ví, không thể chuyển nhượng — đây là bằng chứng định danh.

**Thao tác 3 — Xem API docs:**

Mở `http://localhost:8000/docs` — chứng minh 27 endpoints hoạt động.

---

### Phần 3 — Demo User tạo Keypair (không cần ví, không cần ETH) (3 phút)

Mở `http://localhost:8000/user.html`

**Thao tác — Tạo cặp khóa RSA:**

Nhập địa chỉ ví bất kỳ vào ô "Địa chỉ ví Ethereum":
```
0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
```
Nhấn "Tạo Keypair".

Kết quả:
- Public Key hiển thị (đã lưu vào database)
- Private Key hiển thị (chỉ 1 lần, người dùng tự bảo quản)
- Nhấn "Tải Private Key (.pem)" — file tải về máy

Giải thích: Đây là bước 1 của quy trình SSI — người dùng tự tạo khóa, hệ thống không lưu private key.

---

### Phần 4 — Demo Creator upload IPFS (cần Pinata key — đã cấu hình) (5 phút)

Mở `http://localhost:8000/creator.html`

**Bước 2 — Nhập thông tin:**
- Địa chỉ ví người dùng: `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266`
- DID: `did:ssi:0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266`
- Địa chỉ Creator: `0x32268B487ebaB849d8f40B1a12776a543fdFb79a`
- Nhấn "Lấy Public Key của User"

**Bước 3 — Upload file:**
- Chọn 1 ảnh JPG bất kỳ → nhấn "Upload ảnh"
- Chọn 1 file PDF bất kỳ → nhấn "Upload PDF"
- Điền "Cơ quan cấp": `Trường Đại học ABC`
- Nhấn "Tạo và Upload Metadata JSON"

Kết quả: 3 CID xuất hiện — chứng minh IPFS hoạt động.

Mở `https://gateway.pinata.cloud/ipfs/{CID}` để xem file đã lên IPFS.

---

### Phần 5 — Chứng minh mã hóa RSA (1 phút)

Giải thích khi upload:
- File được mã hóa bằng AES-256-GCM + RSA-OAEP trước khi lên IPFS
- Chỉ người có private key mới giải mã được
- Ngay cả admin hệ thống cũng không đọc được file gốc

---

### Phần 6 — Chạy test (2 phút)

Chuyển sang terminal đang chạy test, chỉ kết quả:

```
89 passed, 0 failed in 44s
```

Giải thích:
- 67 tests cho Smart Contract (unit + property-based + end-to-end)
- 13 tests cho Backend (crypto + IPFS)
- 9 tests cho Soulbound NFT

---

## Dữ liệu thực trên Sepolia để demo

| Thông tin | Giá trị |
|-----------|---------|
| DID Registry Contract | `0x4442864E86805E1c5C8759ED1047Ef4802Ce15Ee` |
| Soulbound Contract | `0xD3B88E485c8Ad25FeCeF28f9eb0DD7f7e73EdC2D` |
| Địa chỉ có DID VERIFIED | `0x32268B487ebaB849d8f40B1a12776a543fdFb79a` |
| DID của địa chỉ trên | `Nhu_Student_Profile` |
| Tổng DID trên chain | 2 |
| Tổng đã xác minh | 11 |
| Network | Ethereum Sepolia (Chain ID: 11155111) |

---

## Nếu giáo viên hỏi "tại sao không demo tạo DID mới?"

Tạo DID cần gửi transaction lên blockchain — cần ETH Sepolia và private key thật.
Để demo đầy đủ luồng ghi blockchain, cần:
1. Có ví MetaMask với ETH Sepolia (lấy miễn phí tại sepoliafaucet.com)
2. Điền private key vào `.env`

Nếu không có, vẫn demo được:
- Đọc dữ liệu từ blockchain (Verifier)
- Tạo keypair RSA (User)
- Upload IPFS (Creator — đã có Pinata key)
- Chạy test suite

---

## Thứ tự mở tab cho giáo viên

1. `http://localhost:8000` — Trang chủ
2. `http://localhost:8000/verifier.html` — Demo xác minh DID thực
3. `http://localhost:8000/user.html` — Demo tạo keypair
4. `http://localhost:8000/creator.html` — Demo upload IPFS
5. `http://localhost:8000/docs` — API documentation
6. `https://sepolia.etherscan.io/address/0x4442864E86805E1c5C8759ED1047Ef4802Ce15Ee` — Contract trên blockchain
7. Terminal — Kết quả test 89 passed
