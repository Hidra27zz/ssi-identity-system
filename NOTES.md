# SSI Identity System - Academic Credentials

Hệ thống quản lý định danh phi tập trung (SSI) ứng dụng trong việc cấp phát chứng chỉ học thuật sử dụng **Soulbound Tokens (SBT)**.

## My Contributions & Implementation Details

### 1. Smart Contract Development

- Thiết kế và triển khai mã nguồn **Soulbound Token (SBT)** bằng ngôn ngữ **Vyper** (`Soulbound_Contract.vy`).
- Đảm bảo tính chất "Soulbound": Token gắn chặt với danh tính, không thể chuyển nhượng.
- Xây dựng cơ chế **DID Registry** để quản lý định danh phi tập trung.

### 2. Decentralized Identity (SSI) Logic

- Xây dựng script triển khai hệ thống định danh:
  - `create_did.py`: Tạo định danh phi tập trung (DID) cho sinh viên.
  - `issue_did.py`: Cấp phát chứng chỉ số dưới dạng danh tính xác thực.

### 3. Backend & Testing Suite

- Sử dụng **Ape Framework** để tự động hóa:
  - `deploy_sbt.py`: Biên dịch và triển khai contract lên mạng **Sepolia**.
  - `integration.py`: Kết nối logic giữa định danh và Smart Contract.
- Viết Unit Test chuyên sâu (`test_soulbound.py`) để kiểm tra ràng buộc và bảo mật.

---

## Project Structure & File Descriptions

### 🔹 Root Directory

- `.env`: Lưu trữ biến môi trường nhạy cảm (Private Keys, API Keys).
- `.gitignore`: Danh sách file Git sẽ bỏ qua (venv, .env).
- `ape-config.yaml`: Cấu hình chính cho Ape Framework.
- `pyproject.toml`: Cấu hình công cụ Python và đường dẫn testing.

### 🔹 `contracts/`

- `Soulbound_Contract.vy`: Smart Contract chính triển khai logic SBT chứng chỉ.

### 🔹 `nft-integration/`

- `tests/test_soulbound.py`: Các Unit Test kiểm tra tính đúng đắn của contract.
- `integration.py`: Script kết nối ứng dụng và Smart Contract.

### 🔹 `scripts/`

- `create_did.py`: Khởi tạo định danh phi tập trung (DID) cho sinh viên.
- `deploy_sbt.py`: Tự động hóa triển khai contract lên mạng thử nghiệm.
- `issue_did.py`: Thực hiện cấp phát chứng chỉ danh tính số.

### 🔹 `shared/`

- `abis/`: Chứa file JSON giao diện contract (`DID_Registry.json`, `Soulbound_Contract.json`).
- `constants.js` & `constants.py`: Lưu trữ hằng số dùng chung (Address, Chain ID).

---

## Proof of Deployment & Transactions

Phần này trình bày các bằng chứng thực tế về việc triển khai hệ thống và thực hiện giao dịch trên mạng thử nghiệm **Sepolia Testnet**.

### 1. Cấu hình ví MetaMask

Để mô phỏng quy trình cấp phát chứng chỉ, hệ thống sử dụng các ví thực thể riêng biệt nhằm đảm bảo tính phân quyền giữa tổ chức cấp phát và người nhận.

- **MetaMask Wallet Configuration**: Danh sách các tài khoản thực thể bao gồm **Identity Creator (University)** và **Identity User (Student)**.
  <img width="472" height="680" alt="MetaMask Wallet" src="https://github.com/user-attachments/assets/d4206adb-6313-43a0-a9be-cc462704af04" />
- **Identity Creator Wallet Details**: Chi tiết ví của tổ chức cấp phát với số dư **0,148 SepoliaETH**, sẵn sàng cho các hoạt động trên Blockchain.
  <img width="472" height="861" alt="Identity Creator Wallet Details" src="https://github.com/user-attachments/assets/a4dba958-e6cc-4fd2-b1e0-7c2a3ff2d7b2" />

### 2. Triển khai Smart Contracts (Deployment)

Các hợp đồng thông minh cốt lõi được triển khai thành công để thiết lập hạ tầng cho hệ thống định danh phi tập trung.

- **Giao dịch triển khai DID Registry**: Xác nhận triển khai thành công hệ thống quản lý định danh (địa chỉ kết thúc bằng `...2ce15ee`).
  <img width="1912" height="982" alt="Giao dịch triển khai DID Registry" src="https://github.com/user-attachments/assets/60deaadc-06f4-419c-b542-c6809289bba9" />

- **Giao dịch triển khai Soulbound Contract**: Xác nhận triển khai thành công hợp đồng dùng để phát hành chứng chỉ số (địa chỉ kết thúc bằng `...7e73edc2d`).
  <img width="1917" height="889" alt="Giao dịch triển khai Soulbound Contract" src="https://github.com/user-attachments/assets/c6ac0fca-bb63-464f-97a3-18f9bf42eedf" />

### 3. Cấp phát chứng chỉ số (Mint SBT)

Minh chứng cho luồng hoạt động chính: Cấp phát Soulbound Token (SBT) làm chứng chỉ học thuật cho sinh viên.

- **Giao dịch cấp phát chứng chỉ số (Mint SBT)**: Giao dịch gọi hàm **Mint** thành công, xác nhận việc phát hành chứng chỉ số và gắn chặt với định danh sinh viên trên sổ cái.
  <img width="1912" height="868" alt="Giao dịch cấp phát chứng chỉ số (Mint SBT)" src="https://github.com/user-attachments/assets/a46f52ea-3255-478b-8cd6-f4e7c8b78d52" />
