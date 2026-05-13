# Tài khoản Demo — Dùng để chạy hệ thống

## 3 Account mới tạo (chưa có ETH Sepolia)

| Vai trò | Địa chỉ ví | Private Key |
|---------|-----------|-------------|
| User (Sinh viên) | `0x01b3d559557693D1BB874056CDe8573Ee1d57638` | `0xec13014a7bd82ce40a43098b7a3eab545bc5a871eb0e24a7da8dc632460ef60d` |
| Creator (Trường ĐH) | `0x07e315b1319e94657f0026307DD5aF6243423F78` | `0x3e8473a2c6c81e183f354ebc12b83c685235d16c0c217324b4b48e4dd6f1c1da` |
| Verifier (Công ty) | `0xa51Baf28eFd56e78678d0f59e011476D116EbcbE` | `0x73205d948e30574817dac94ea73cff676f33d226b6e1a8bfb3f7a98f14889beb` |

## Account cũ đã có ETH Sepolia (dùng để gửi transaction)

| Vai trò | Địa chỉ ví | ETH | Ghi chú |
|---------|-----------|-----|---------|
| Creator/Deployer | `0x32268B487ebaB849d8f40B1a12776a543fdFb79a` | 0.148 ETH | Đã deploy contracts, có DID VERIFIED |

---

## Kết quả đã chạy — User mới (seed vào DB)

| Thông tin | Giá trị |
|-----------|---------|
| User address | `0x01b3d559557693D1BB874056CDe8573Ee1d57638` |
| User DID | `did:ssi:0x01b3d559557693d1bb874056cde8573ee1d57638` |
| Ảnh chân dung CID | `QmRt1oDWnW65nLZXMb96GqNge7FhVPRwBPLbkYga8eXB5T` |
| PDF bằng tốt nghiệp CID | `QmULCg3SfsxGLgMbdyEZnDF1GYkG5VaAFirTxShoyS6dTW` |
| Metadata JSON CID | `QmbDC783MXpbQQQrEpniDMEPz1UywRexepH2GGL1ZDK9NL` |
| Doc Hash (SHA-256) | `c7282a86fcc0afbef8dfded63e153d3e8b9ab4b4abd9db6f1fe923040b1d0091` |
| Consent ID (đã approved) | `4` |
| Verifier | `0xa51Baf28eFd56e78678d0f59e011476D116EbcbE` |

---

## Quy trình demo trên frontend

### Bước 1 — Trang User (`http://localhost:8000/user.html`)
- Ô địa chỉ ví: `0x01b3d559557693D1BB874056CDe8573Ee1d57638`
- Nhấn "Tạo Keypair" → tải private key
- Ô DID: `did:ssi:0x01b3d559557693d1bb874056cde8573ee1d57638`

### Bước 2 — Trang Verifier (`http://localhost:8000/verifier.html`)
- Xác minh địa chỉ có DID VERIFIED thực: `0x32268B487ebaB849d8f40B1a12776a543fdFb79a`
- Kết quả: VERIFIED (từ Sepolia blockchain thực)

### Bước 3 — Trang Creator (`http://localhost:8000/creator.html`)
- Nhấn "Tải danh sách" → thấy User đang chờ
- Upload ảnh JPG bất kỳ → thấy CID
- Upload PDF bất kỳ → thấy CID
- Nhấn "Tạo & Upload Metadata JSON" → thấy CID thứ 3

### Bước 4 — Trang Verifier
- DID chủ sở hữu: `did:ssi:0x01b3d559557693d1bb874056cde8573ee1d57638`
- Địa chỉ Verifier: `0xa51Baf28eFd56e78678d0f59e011476D116EbcbE`
- Nhấn "Gửi yêu cầu truy cập"

### Bước 5 — Trang User
- DID: `did:ssi:0x01b3d559557693d1bb874056cde8573ee1d57638`
- Nhấn "Tải danh sách yêu cầu" → thấy yêu cầu từ Verifier
- Nhấn "Đồng ý"

---

## Verifier có bao nhiêu account?

**Không giới hạn.** Bất kỳ địa chỉ ví Ethereum nào cũng có thể là Verifier.
Chỉ cần nhập địa chỉ ví của mình vào ô "Địa chỉ ví của bạn (Verifier)" khi xin consent.
Không cần đăng ký hay cấp quyền.

## Creator có bao nhiêu account?

**Có giới hạn.** Creator phải được contract owner cấp quyền bằng hàm `grantCreatorRole()`.
Hiện tại chỉ có `0x32268B487...` là Creator được cấp quyền trên Sepolia.

## Để thêm Creator mới

Gọi API (cần private key của contract owner):
```
POST /api/did/grant-creator
Body: { "creator_address": "0x..." }
```
Hoặc gọi trực tiếp contract trên Etherscan → Write Contract → grantCreatorRole.
