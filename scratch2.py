from backend.services.blockchain_service import get_web3, _signing_account, _get_did_contract
from backend.models.database import get_connection
from web3 import Web3

w3 = get_web3()
contract = _get_did_contract(w3)
account = _signing_account(w3)

conn = get_connection()
row = conn.execute("SELECT wallet_address FROM did_cache ORDER BY created_at DESC LIMIT 1").fetchone()
if not row:
    print("No pending DID found")
    exit()

wallet = Web3.to_checksum_address(row["wallet_address"])
doc_hash = "1234567890123456789012345678901234567890123456789012345678901234"
doc_hash_bytes = bytes.fromhex(doc_hash)
cid = "QmXxx"

print(f"Testing for wallet: {wallet}")

# Check conditions manually
is_creator = contract.functions.isCreator(account.address).call()
print(f"Is backend a creator? {is_creator}")

has_did = contract.functions.hasDID(wallet).call()
print(f"Does wallet have DID on-chain? {has_did}")

if has_did:
    record = contract.functions.getDIDRecord(wallet).call()
    print(f"Record status: {record[4]}")

# Try gas estimation to see the error
try:
    contract.functions.storeDocumentHash(
        wallet,
        doc_hash_bytes,
        cid
    ).estimate_gas({"from": account.address})
    print("Gas estimation SUCCESS")
except Exception as e:
    print(f"Estimation FAILED: {e}")
