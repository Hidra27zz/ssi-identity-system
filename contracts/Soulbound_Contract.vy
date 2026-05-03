
# @version ^0.3.10
# Soulbound Token - Improved & Safe Version
# Nguoi phu trach: Nhu

# ========== EVENTS ==========
event TokenMinted:
    recipient: indexed(address)
    token_id: uint256
    credential_type: String[32]
    metadata_uri: String[256]

event TokenInvalidated:
    owner: indexed(address)
    token_id: uint256

event MinterSet:
    minter: indexed(address)
    has_role: bool


# ========== STRUCT ==========
struct TokenData:
    owner: address
    issuer: address
    token_id: uint256
    credential_type: String[32]
    metadata_uri: String[256]
    is_valid: bool
    minted_at: uint256


# ========== STORAGE ==========
tokens: HashMap[uint256, TokenData]                      # token_id → data
owner_tokens: HashMap[address, DynArray[uint256, 20]]    # owner → list token_id
authorized_minters: HashMap[address, bool]

token_counter: uint256
contract_owner: address


# ========== INIT ==========
@external
def __init__():
    self.contract_owner = msg.sender
    self.authorized_minters[msg.sender] = True
    self.token_counter = 0


# ========== INTERNAL ==========
@internal
@view
def _exists(token_id: uint256) -> bool:
    return self.tokens[token_id].owner != empty(address)


# ========== MINT ==========
@external
def mint(
    recipient: address,
    credential_type: String[32],
    metadata_uri: String[256]
) -> uint256:

    # --- Validate ---
    assert self.authorized_minters[msg.sender], "Not authorized"
    assert recipient != empty(address), "Invalid address"
    assert len(metadata_uri) > 0, "Metadata required"
    assert len(credential_type) > 0, "Type required"

    # Giới hạn số credential/user (tránh crash DynArray)
    assert len(self.owner_tokens[recipient]) < 20, "Max tokens reached"

    # --- Create token ---
    self.token_counter += 1
    token_id: uint256 = self.token_counter

    self.tokens[token_id] = TokenData({
        owner: recipient,
        issuer: msg.sender,
        token_id: token_id,
        credential_type: credential_type,
        metadata_uri: metadata_uri,
        is_valid: True,
        minted_at: block.timestamp
    })

    # --- Add to owner ---
    self.owner_tokens[recipient].append(token_id)

    # --- Emit event ---
    log TokenMinted(recipient, token_id, credential_type, metadata_uri)

    return token_id


# ========== INVALIDATE ==========
@external
def invalidateToken(token_id: uint256):

    assert self.authorized_minters[msg.sender] or msg.sender == self.contract_owner, "Unauthorized"
    assert self._exists(token_id), "Token not exist"

    token: TokenData = self.tokens[token_id]
    assert token.is_valid, "Already invalidated"

    self.tokens[token_id].is_valid = False

    log TokenInvalidated(token.owner, token_id)


# ========== VIEW FUNCTIONS ==========
@view
@external
def getTokenData(token_id: uint256) -> TokenData:
    assert self._exists(token_id), "Token not exist"
    return self.tokens[token_id]


@view
@external
def getTokensOfOwner(owner: address) -> DynArray[uint256, 20]:
    return self.owner_tokens[owner]


@view
@external
def hasValidToken(owner: address) -> bool:
    tokens_list: DynArray[uint256, 20] = self.owner_tokens[owner]

    for token_id in tokens_list:
        if self.tokens[token_id].is_valid:
            return True

    return False


@view
@external
def isTokenValid(token_id: uint256) -> bool:
    assert self._exists(token_id), "Token not exist"
    return self.tokens[token_id].is_valid


# ========== ADMIN ==========
@external
def setMinterRole(minter: address, has_role: bool):
    assert msg.sender == self.contract_owner, "Only owner"
    self.authorized_minters[minter] = has_role

    log MinterSet(minter, has_role)


# ========== SOULBOUND (BLOCK TRANSFER) ==========
@external
def transfer(to: address, token_id: uint256):
    raise "Soulbound: transfer not allowed"


@external
def approve(spender: address, token_id: uint256):
    raise "Soulbound: transfer not allowed"


@external
def transferFrom(from_addr: address, to: address, token_id: uint256):
    raise "Soulbound: transfer not allowed"