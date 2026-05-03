import os
import json
from web3 import Web3
from dotenv import load_dotenv
from pathlib import Path

# Load cấu hình
load_dotenv()
RPC_URL = os.getenv("RPC_URL")
issuer_key = os.getenv("ISSUER_PRIVATE_KEY")
DID_REGISTRY_ADDRESS = os.getenv("DID_REGISTRY_ADDRESS")

# Kết nối mạng
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(issuer_key)
print(f"Ví đang thực hiện giao dịch: {account.address}")

# Cách viết này sẽ giúp máy tự tìm đường dẫn tuyệt đối dựa trên vị trí file script
base_path = Path(__file__).resolve().parent.parent
abi_path = base_path / "shared" / "abis" / "DID_Registry.json"

with open(abi_path) as f:
    abi = json.load(f)

contract = w3.eth.contract(address=DID_REGISTRY_ADDRESS, abi=abi)

def store_hash_test():
    # 1. Địa chỉ ví nhận định danh (thường là chính ví của Như)
    target_wallet = account.address 
    
    # 2. Mã định danh (Document ID) - Yêu cầu kiểu bytes32
    # Như có thể dùng hàm encode() để biến một chuỗi thành bytes
    doc_id = Web3.keccak(text="STUDENT_ID_001") 
    
    # 3. Nội dung hoặc CID từ IPFS
    sample_cid = "QmTest1234567890Example"
    
    print(f"--- Đang gửi Document Hash lên Sepolia ---")
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Sửa lại dòng này cho đủ 3 tham số: address, bytes32, string
    tx = contract.functions.storeDocumentHash(
        target_wallet, 
        doc_id,
        sample_cid
    ).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 300000, # Tăng gas lên một chút cho chắc ăn
        'gasPrice': w3.eth.gas_price
    })

    signed_tx = w3.eth.account.sign_transaction(tx, issuer_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    print(f"✅ Giao dịch đã gửi! Hash: {tx_hash.hex()}")

if __name__ == "__main__":
    store_hash_test()