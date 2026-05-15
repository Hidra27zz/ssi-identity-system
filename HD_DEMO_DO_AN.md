# 📘 Hướng Dẫn Kịch Bản Demo Đồ Án SSI (Decentralized Identity)

Tài liệu này hướng dẫn chi tiết từng bước để biểu diễn các chức năng của đồ án một cách trơn tru và thuyết phục nhất trước hội đồng bảo vệ.

---

## 1. Chuẩn Bị Trước Khi Lên Bục

### 🔑 Các Tài Khoản MetaMask Cần Có:
Bạn cần chuẩn bị sẵn ít nhất **3 tài khoản (Account)** trên MetaMask:
- **Account 1 (Admin/Creator):** Ví đã dùng để deploy Smart Contract. Ví này mặc định có quyền là `Creator`. (Ví dụ: Đại diện Trường Đại Học).
- **Account 2 (User):** Ví của một người dùng bình thường (Ví dụ: Sinh viên). Đảm bảo ví này có một ít Sepolia ETH để trả phí gas.
- **Account 3 (Verifier):** Ví của bên thứ ba (Ví dụ: Công ty tuyển dụng, Ngân hàng).

### 📁 Chuẩn Bị File:
- Chuẩn bị 1 file ảnh (JPG/PNG) đại diện cho ảnh chân dung.
- Chuẩn bị 1 file PDF đại diện cho giấy tờ (CMND, Bằng cấp,...).

---

## 2. Kịch Bản Demo Chi Tiết (4 Trường Hợp)

### 🚀 Case 1: Đăng Ký Định Danh (User) & Cấp Thẻ (Creator)
**Mục tiêu:** Chứng minh hệ thống phi tập trung, mã hóa dữ liệu an toàn và cấp phát Soulbound NFT.

1. **User tự tạo khóa:**
   - Mở trình duyệt, đăng nhập với MetaMask **Account 2 (User)**.
   - Mở tab **User Dashboard** $\rightarrow$ Bấm **Tạo Keypair**.
   - **(Giải thích):** *"Hệ thống sẽ tải về file `private_key.pem`. File này hoàn toàn nằm trên máy cá nhân, hệ thống không lưu giữ để đảm bảo an toàn tuyệt đối."*
   - Cuộn xuống bấm **Tạo DID**. MetaMask hiện ra $\rightarrow$ Bấm Confirm. Đợi thông báo thành công.

2. **Creator xác minh & Mã hóa tài liệu:**
   - Đổi MetaMask sang **Account 1 (Creator)**. Đăng nhập vào tab **Creator Dashboard**.
   - Ở Bước 1: Nhập địa chỉ ví của User (Account 2) vào $\rightarrow$ Bấm **Lấy Public Key của User**.
   - Ở Bước 2: Upload file Ảnh và file PDF lên. 
   - Điền thông tin (Loại giấy tờ, Cơ quan cấp) $\rightarrow$ Bấm **Tạo và Upload Metadata JSON**.
   - **(Giải thích):** *"Hệ thống sử dụng Public Key của User để mã hóa toàn bộ file trước khi ném lên IPFS. Dù file nằm trên mạng công cộng nhưng chỉ User mới có chìa khóa để mở."*

3. **Ghi nhận Blockchain & Cấp NFT:**
   - Bấm **Gửi Hash lên Blockchain** $\rightarrow$ Xác nhận giao dịch.
   - Cuộn xuống phần Mint NFT, chọn loại giấy tờ $\rightarrow$ Bấm **Mint Soulbound NFT** $\rightarrow$ Xác nhận giao dịch.
   - **(Giải thích):** *"Lúc này User đã có 1 định danh vĩnh viễn trên mạng lưới và nhận được 1 thẻ Soulbound Token không thể chuyển nhượng."*

---

### 🛡️ Case 2: Xác Thực Bằng Token (Token-Gated Access)
**Mục tiêu:** Trình diễn cách kiểm tra quyền mà không cần xin thông tin cá nhân.

1. Đổi MetaMask sang **Account 3 (Verifier)**. Mở tab **Verifier Dashboard**.
2. Nhập địa chỉ ví của User (Account 2) vào ô đầu tiên $\rightarrow$ Bấm **Xác minh**. (Màn hình xanh: ĐỊNH DANH HỢP LỆ).
3. Ở phần **Kiểm tra quyền truy cập**, nhập ví User $\rightarrow$ Bấm **Kiểm tra**.
4. **(Giải thích):** *"Hệ thống báo CÓ QUYỀN TRUY CẬP. Thay vì bắt người dùng nộp lại CMND, Verifier chỉ cần quét xem ví của họ có chứa Soulbound NFT do cơ quan uy tín cấp hay không là đủ để cho phép qua cổng."*

---

### 🤝 Case 3: Yêu Cầu Truy Cập (Consent) & Giải Mã File
**Mục tiêu:** Chứng minh cơ chế Zero-Knowledge, người dùng nắm quyền quyết định dữ liệu.

1. **Verifier gửi yêu cầu:** 
   - Tại tab Verifier, cuộn xuống phần Yêu cầu truy cập $\rightarrow$ Nhập DID của User $\rightarrow$ Bấm **Gửi yêu cầu truy cập**.
2. **User phê duyệt:** 
   - Quay lại tab **User Dashboard** (không cần đổi ví).
   - Cuộn xuống "Quản lý yêu cầu", bấm **Tải danh sách** $\rightarrow$ Nhấn **Phê duyệt (Approve)**.
3. **Verifier tải & giải mã:**
   - Quay lại tab **Verifier Dashboard**, kéo xuống cuối cùng.
   - Nhập **IPFS CID của file** (Copy từ kết quả xác minh ở trên).
   - Bấm **Tải lại** $\rightarrow$ Hệ thống sẽ đọc Metadata và hiện ra bảng chứa CID của Ảnh và PDF.
   - Copy CID của Ảnh (hoặc PDF) dán vào ô nhập.
   - Mở file `private_key.pem` (của User), copy nội dung dán vào ô Private Key.
   - Bấm **Tải và Giải Mã** $\rightarrow$ File/Ảnh sẽ được giải mã và hiển thị lên màn hình!

---

### 🚫 Case 4: Thu Hồi Định Danh (Revoke)
**Mục tiêu:** Trình diễn nghiệp vụ tước quyền lợi khi CMND bị mất hoặc hết hạn.

1. Đổi MetaMask sang **Account 1 (Creator)**.
2. Mở tab **Creator Dashboard**, cuộn xuống dưới cùng (Phần *Quản lý & Thu hồi DID*).
3. Nhập ví của User (Account 2) vào $\rightarrow$ Bấm **Thu hồi vĩnh viễn**. Xác nhận MetaMask.
4. **Kiểm chứng:** Quay lại tab **Verifier Dashboard**, nhập ví User kiểm tra lại.
   - Trạng thái DID: Chuyển sang màu đỏ **ĐỊNH DANH ĐÃ BỊ THU HỒI**.
   - Kiểm tra Token: Báo **KHÔNG CÓ QUYỀN TRUY CẬP** (Token đã bị vô hiệu hóa).

---

## 3. Cách Thêm Một Tài Khoản CREATOR Mới
Chỉ ví Admin (người deploy) mới được vào trang Creator. Nếu giảng viên yêu cầu "Thêm 1 trường đại học khác làm Creator", hãy làm theo các bước sau:

1. Tạo một tài khoản mới trên MetaMask (vd: Account 4). Copy địa chỉ ví đó.
2. Mở file `grant_creator.py` trong dự án. Kéo xuống dòng cuối cùng và thêm lệnh sau:
   ```python
   grant_creator("0xĐỊA_CHỈ_VÍ_MỚI")
   ```
3. Mở Terminal trong VS Code, chạy lệnh:
   ```bash
   venv/bin/python grant_creator.py
   ```
4. Chờ 10 giây báo `Success!`. Giờ đây ví mới đã có quyền truy cập tab Creator.

---
**💡 Chú ý:** 
- Khi dùng MetaMask để gửi transaction (Tạo DID, Gửi Hash, Mint NFT), đảm bảo bạn đang chọn ĐÚNG tài khoản (Account) trên ví MetaMask khớp với địa chỉ bạn đã gõ trên web. Nếu chọn sai, web sẽ báo lỗi *"MetaMask đang chọn tài khoản khác"*.
- Nếu bị lệch, hãy F5 tải lại trang web để code đọc lại ví.
