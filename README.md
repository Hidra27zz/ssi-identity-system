# He Thong Dinh Danh Phi Tap Trung (SSI)


Bài Tập 01: XÂY DỰNG HỆ THỐNG ĐỊNH DANH PHI TẬP TRUNG (SSI)
1. Yêu cầu thực hiện
Tiêu chí 1: Xây dựng & Triển khai Hợp đồng thông minh (10 điểm)
Thực logic quản lý định danh (Identity Management) trên Ethereum.
3 Nghiệp vụ chính:
Khởi tạo Định danh (Create DID): Hàm đăng ký một mã định danh phi tập trung (Decentralized Identifier - DID) gắn liền với địa chỉ ví của người dùng.
Quản lý mã Hash bằng cấp/chứng chỉ: Hàm cho phép "Identity Creator" (ví dụ: Trường đại học, Cơ quan nhà nước) xác nhận và lưu trữ mã hash của tài liệu định danh lên blockchain.
Xác minh & Truy xuất: Hàm cho phép bên thứ ba (Verifier) kiểm tra tính hợp lệ của mã định danh mà không cần xem dữ liệu gốc.
2 Ràng buộc logic:
Sử dụng require để đảm bảo chỉ "Identity Creator" (được cấp quyền) mới có thể xác thực tài liệu cho người dùng.
Kiểm tra trạng thái của định danh (ví dụ: định danh đã bị thu hồi/revoke hay chưa) trước khi xác minh thành công.
Tiêu chí 2: Tương tác qua Web3.py / Frontend (10 điểm)
Xây dựng giao diện cho 3 đối tượng tham gia: Identity Creator (Người cấp), Identity User (Người dùng), và Identity Manager/Verifier (Người xác minh).
Chức năng tương tác:
User Dashboard: Hiển thị thông tin định danh và cho phép người dùng phê duyệt quyền chia sẻ dữ liệu (explicit consent).
Gửi giao dịch: Nhấn nút để gửi mã hash tài liệu từ Frontend lên Smart Contract.
Mã hóa: Áp dụng thuật toán RSA hoặc mã hóa bất đối xứng để bảo vệ thông tin trước khi lưu trữ hoặc chia sẻ.
Tiêu chí 3: Tích hợp IPFS (10 điểm)
Do thông tin định danh (ảnh thẻ, bản quét hộ chiếu, metadata JSON) có kích thước lớn phải sử dụng IPFS để lưu trữ.
Dữ liệu lưu trữ: Tối thiểu 3 loại (Ảnh chân dung, File PDF căn cước, Metadata JSON chứa thông tin cá nhân).
Thao tác:
Upload: Khi người dùng đăng ký, Frontend đẩy file lên IPFS, lấy mã CID (Content Identifier).
Retrieve: Khi xác minh, hệ thống lấy mã CID từ Blockchain để truy xuất lại file gốc trên IPFS.
Tiêu chí 4: Token ERC-20 / NFT Marketplace (10 điểm)
Ứng dụng Token vào quản lý định danh để tăng tính thực tế:
NFT Định danh (Soulbound Token): Tạo một NFT không thể chuyển nhượng đại diện cho định danh cá nhân hoặc bằng cấp của người dùng (ví dụ bằng lái xe hoặc bảo hiểm xã hội).
Nghiệp vụ:
Cấp phát (Mint): Cơ quan có thẩm quyền "mint" một NFT định danh vào ví người dùng sau khi xác minh thành công.
Xác thực: Sử dụng sự tồn tại của NFT trong ví để cấp quyền truy cập vào các dịch vụ khác (Token-gated access).
2. Quy trình thực hiện 
Bước 1 - Khởi tạo: Người dùng cài đặt ứng dụng (Mobile App/Web) và tạo cặp khóa Public/Private Key. Public Key sẽ được dùng để tạo địa chỉ ví trên Ethereum.
Bước 2 - Xác thực tài liệu: Người dùng gửi bản quét giấy tờ thực cho "Identity Creator". Đơn vị này xác minh, tạo mã hash của tài liệu và ký xác nhận.
Bước 3 - Lưu trữ: File gốc được lưu trên IPFS. Mã hash (CID) của file và chữ ký số của đơn vị cấp được lưu trên Smart Contract để đảm bảo tính bất biến.
Bước 4 - Sử dụng: Khi cần chứng minh danh tính (ví dụ: mở tài khoản ngân hàng), người dùng cung cấp mã định danh. Ngân hàng sẽ truy vấn Smart Contract để xác nhận tài liệu này đã được cơ quan có thẩm quyền xác thực hay chưa mà không cần lưu trữ lại bản sao giấy tờ.
3. Lưu ý về Bảo mật & Quyền riêng tư
Quyền kiểm soát: phải thể hiện được triết lý "Self-Sovereign": không thông tin nào được chia sẻ với bên thứ ba nếu không có sự đồng ý trực tiếp của chủ sở hữu.
Không lưu PII on-chain: Tuyệt đối không lưu thông tin cá nhân trực tiếp (tên, số điện thoại) lên Blockchain. Chỉ lưu mã Hash hoặc mã CID của IPFS


## Phan cong module

| Thu muc | Nguoi phu trach | Nhiem vu |
|---------|----------------|---------|
| contracts/ | Nhan | Vyper Smart Contract DID_Registry |
| backend/ | Thuy | FastAPI + IPFS + RSA + SQLite |
| frontend/ | Phuc | HTML/JS DApp (3 giao dien) |
| nft-integration/ | Nhu | Soulbound NFT + Orchestrator |
| shared/ | Ca nhom | ABI, constants dung chung |

## Quy tac GitHub (tranh conflict)

- Moi nguoi chi commit vao thu muc cua minh
- Khong sua file cua nguoi khac khi chua thong bao
- shared/ chi duoc cap nhat sau khi deploy contract (Nhan + Nhu)
- Tao branch rieng: feature/nhan-contracts, feature/thuy-backend, feature/phuc-frontend, feature/nhu-nft

## Cai dat nhanh

    bash setup.sh

Lenh nay se: tao venv, cai pip packages, cai ape plugins, compile contracts.

## Chay tung buoc

### Buoc 1: Cai dat

    python3 -m venv venv
    source venv/bin/activate
    pip install -r backend/requirements.txt
    ape plugins install vyper
    ape plugins install etherscan

### Buoc 2: Cau hinh .env

    cp .env.example .env
    # Giu nguyen gia tri mac dinh de chay local

### Buoc 3: Compile contracts

    ape compile

### Buoc 4: Khoi dong local node (terminal rieng)

    # Cai Foundry neu chua co: curl -L https://foundry.paradigm.xyz | bash && foundryup
    bash scripts/start_local_node.sh
    # hoac chay truc tiep: anvil

### Buoc 5: Deploy contracts

    bash scripts/deploy_all.sh
    # hoac tung lenh:
    ape run contracts/deploy --network ethereum:local:http://127.0.0.1:8545
    ape run nft-integration/deploy --network ethereum:local:http://127.0.0.1:8545

### Buoc 6: Cap nhat dia chi contract

Sau khi deploy, copy dia chi in ra va cap nhat vao 3 file:
- .env  ->  DID_REGISTRY_ADDRESS=0x...  va  SOULBOUND_ADDRESS=0x...
- shared/constants.py  ->  DID_REGISTRY_ADDRESS  va  SOULBOUND_ADDRESS
- shared/constants.js  ->  DID_REGISTRY_ADDRESS  va  SOULBOUND_ADDRESS

### Buoc 7: Chay backend (terminal rieng)

    source venv/bin/activate
    uvicorn backend.main:app --reload --port 8000

API docs: http://localhost:8000/docs

### Buoc 8: Mo frontend

Mo truc tiep trong trinh duyet hoac dung VS Code Live Server:
- frontend/user.html
- frontend/creator.html
- frontend/verifier.html

### Buoc 9: Chay NFT orchestrator (terminal rieng)

    source venv/bin/activate
    python nft-integration/integration.py

## Chay tests

    bash scripts/run_tests.sh
    # hoac:
    pytest --tb=short -v

## Deploy len Sepolia testnet

    # 1. Cap nhat .env voi Sepolia RPC_URL va PRIVATE_KEY thuc
    # 2. Import account vao Ape (chi can 1 lan)
    ape accounts import deployer
    # 3. Deploy
    ape run contracts/deploy --network ethereum:sepolia:infura
    ape run nft-integration/deploy --network ethereum:sepolia:infura

## Cau truc thu muc

    ssi-project/
    contracts/
        DID_Registry.vy
        Soulbound_Contract.vy   (copy tu nft-integration/ de Ape compile)
        deploy.py
        tests/
    backend/
        main.py
        routers/
        services/
        models/
        tests/
        requirements.txt
    frontend/
        creator.html
        user.html
        verifier.html
        css/
        js/
    nft-integration/
        Soulbound_Contract.vy   (file goc, sua o day)
        deploy.py
        integration.py
        tests/
    shared/
        abis/                   (tu dong tao khi deploy)
        constants.py
        constants.js
    scripts/
        start_local_node.sh
        deploy_all.sh
        run_tests.sh
    ape-config.yaml
    pyproject.toml
    setup.sh
    .env.example
    .gitignore
    README.md
