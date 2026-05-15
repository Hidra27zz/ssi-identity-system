from backend.services.blockchain_service import get_web3, _signing_account, is_creator_on_chain
w3 = get_web3()
account = _signing_account(w3)
print(f"Backend address: {account.address}")
print(f"Is creator: {is_creator_on_chain(account.address)}")
