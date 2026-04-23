# @version ^0.3.10
# Soulbound Token - NFT khong the chuyen nhuong dai dien cho dinh danh da xac minh
# Nguoi phu trach: Nhu

# Events
event TokenMinted:
    recipient: indexed(address)
    token_id: uint256
    metadata_uri: String[128]

event TokenInvalidated:
    owner: indexed(address)
    token_id: uint256

event MinterSet:
    minter: indexed(address)
    has_role: bool

# Structs
struct TokenData:
    owner: address
    token_id: uint256
    metadata_uri: String[128]
    is_valid: bool
    minted_at: uint256

# Storage
tokens: HashMap[address, TokenData]
has_token: HashMap[address, bool]
token_counter: uint256
authorized_minters: HashMap[address, bool]
contract_owner: address

@external
def __init__():
    self.contract_owner = msg.sender
    self.authorized_minters[msg.sender] = True
    self.token_counter = 0

@external
def mint(recipient: address, metadata_uri: String[128]) -> uint256:
    assert self.authorized_minters[msg.sender], "Unauthorized: only authorized minter"
    assert not self.has_token[recipient], "Address already has a Soulbound Token"
    assert len(metadata_uri) > 0, "metadata_uri cannot be empty"

    self.token_counter += 1
    token_id: uint256 = self.token_counter

    self.tokens[recipient] = TokenData(
        owner=recipient,
        token_id=token_id,
        metadata_uri=metadata_uri,
        is_valid=True,
        minted_at=block.timestamp,
    )
    self.has_token[recipient] = True

    log TokenMinted(recipient, token_id, metadata_uri)
    return token_id

@external
def invalidateToken(owner: address):
    assert self.authorized_minters[msg.sender] or msg.sender == self.contract_owner, "Unauthorized"
    assert self.has_token[owner], "No token found for this address"
    assert self.tokens[owner].is_valid, "Token already invalidated"

    token_id: uint256 = self.tokens[owner].token_id
    self.tokens[owner].is_valid = False

    log TokenInvalidated(owner, token_id)

@view
@external
def hasValidToken(owner: address) -> bool:
    if not self.has_token[owner]:
        return False
    return self.tokens[owner].is_valid

@view
@external
def getTokenData(owner: address) -> TokenData:
    return self.tokens[owner]

@external
def setMinterRole(minter_address: address, has_role: bool):
    assert msg.sender == self.contract_owner, "Only owner can set minter role"
    self.authorized_minters[minter_address] = has_role
    log MinterSet(minter_address, has_role)

# BLOCKED: Soulbound token khong the chuyen nhuong
@external
def transfer(to: address, token_id: uint256):
    raise "Soulbound: transfer not allowed"

@external
def approve(spender: address, token_id: uint256):
    raise "Soulbound: transfer not allowed"

@external
def transferFrom(from_addr: address, to: address, token_id: uint256):
    raise "Soulbound: transfer not allowed"
