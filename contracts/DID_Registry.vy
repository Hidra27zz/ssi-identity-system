# @version ^0.3.10
#
# DID Registry - He thong quan ly dinh danh phi tap trung
# Nguoi phu trach: Nhan
#
# Luong nghiep vu:
#   1. Identity User goi createDID()         -> tao dinh danh gan voi dia chi vi
#   2. Identity Creator goi storeDocumentHash() -> xac minh tai lieu, luu hash + CID
#   3. Identity Creator goi updateDocumentHash() -> cap nhat hash khi tai lieu thay doi
#   4. Identity Verifier goi verifyDID()     -> kiem tra tinh hop le (chi doc)
#   5. Identity Creator / User goi revokeDID() -> thu hoi dinh danh
#
# Phan quyen:
#   - contract_owner : nguoi deploy, cap/thu hoi quyen Creator, chuyen quyen so huu
#   - Identity Creator: duoc cap quyen boi owner, xac minh / cap nhat / thu hoi DID
#   - Identity User  : bat ky ai, tu tao DID cho chinh minh
#   - Identity Verifier: bat ky ai, chi goi view functions
#
# Tat ca rang buoc logic dung assert (tuong duong require trong Solidity)

# ============================================================
# EVENTS
# ============================================================

event DIDCreated:
    owner:     indexed(address)
    did:       String[128]
    timestamp: uint256

event DocumentHashStored:
    owner:       indexed(address)
    doc_hash:    bytes32
    cid:         String[128]
    verified_by: address
    timestamp:   uint256

event DocumentHashUpdated:
    owner:       indexed(address)
    old_hash:    bytes32
    new_hash:    bytes32
    new_cid:     String[128]
    updated_by:  address
    timestamp:   uint256

event DIDRevoked:
    owner:      indexed(address)
    did:        String[128]
    revoked_by: address
    timestamp:  uint256

event CreatorRoleGranted:
    creator:    indexed(address)
    granted_by: address

event CreatorRoleRevoked:
    creator:    indexed(address)
    revoked_by: address

event OwnershipTransferred:
    old_owner: indexed(address)
    new_owner: indexed(address)

# ============================================================
# STRUCTS
# ============================================================

# Trang thai DID:
#   PENDING  (0): da tao, chua duoc Creator xac minh
#   VERIFIED (1): Creator da xac minh, co hash + CID hop le
#   REVOKED  (2): da bi thu hoi, khong the dung nua
struct DIDRecord:
    owner:        address      # Dia chi vi so huu DID
    did:          String[128]  # Chuoi DID (vd: "did:ssi:0xABC...")
    doc_hash:     bytes32      # SHA-256 hash tai lieu goc (zero neu chua xac minh)
    ipfs_cid:     String[128]  # CID tren IPFS (rong neu chua xac minh)
    status:       uint8        # 0=PENDING, 1=VERIFIED, 2=REVOKED
    created_at:   uint256      # Block timestamp khi tao DID
    verified_at:  uint256      # Block timestamp khi xac minh lan dau (0 neu chua)
    updated_at:   uint256      # Block timestamp khi cap nhat hash lan cuoi
    verified_by:  address      # Creator da xac minh (zero address neu chua)
    update_count: uint8        # So lan cap nhat hash (toi da 255)

# ============================================================
# CONSTANTS
# ============================================================

STATUS_PENDING:   constant(uint8) = 0
STATUS_VERIFIED:  constant(uint8) = 1
STATUS_REVOKED:   constant(uint8) = 2
STATUS_NOT_FOUND: constant(uint8) = 255

MAX_UPDATE_COUNT: constant(uint8) = 10  # Gioi han cap nhat hash de tranh spam

# ============================================================
# STORAGE
# ============================================================

records:        HashMap[address, DIDRecord]  # Ban ghi DID theo dia chi vi
has_did:        HashMap[address, bool]       # Kiem tra nhanh co DID chua
creators:       HashMap[address, bool]       # Danh sach Identity Creator
contract_owner: address                      # Chu so huu contract
total_dids:     uint256                      # Tong so DID da tao
total_verified: uint256                      # Tong so DID da xac minh

# ============================================================
# CONSTRUCTOR
# ============================================================

@external
def __init__():
    self.contract_owner = msg.sender
    self.creators[msg.sender] = True
    self.total_dids    = 0
    self.total_verified = 0

# ============================================================
# CHUC NANG CHINH
# ============================================================

@external
def createDID(did: String[128]) -> bool:
    """
    Tao dinh danh phi tap trung moi cho msg.sender.

    Rang buoc:
    - Moi dia chi vi chi duoc tao 1 DID duy nhat
    - Chuoi DID khong duoc rong
    - DID duoc tao o trang thai PENDING

    Tham so:
    - did: Chuoi dinh danh (vd: "did:ssi:0xABC...")

    Tra ve: True neu thanh cong
    """
    assert not self.has_did[msg.sender], "DID already exists for this address"
    assert len(did) > 0, "DID string cannot be empty"

    self.records[msg.sender].owner        = msg.sender
    self.records[msg.sender].did          = did
    self.records[msg.sender].doc_hash     = empty(bytes32)
    self.records[msg.sender].ipfs_cid     = ""
    self.records[msg.sender].status       = STATUS_PENDING
    self.records[msg.sender].created_at   = block.timestamp
    self.records[msg.sender].verified_at  = 0
    self.records[msg.sender].updated_at   = 0
    self.records[msg.sender].verified_by  = empty(address)
    self.records[msg.sender].update_count = 0
    self.has_did[msg.sender] = True
    self.total_dids += 1

    log DIDCreated(msg.sender, did, block.timestamp)
    return True


@external
def storeDocumentHash(
    target_address: address,
    doc_hash:       bytes32,
    cid:            String[128]
) -> bool:
    """
    Luu hash tai lieu va CID IPFS len blockchain (xac minh lan dau).
    Chi Identity Creator moi duoc goi.

    Rang buoc:
    - Chi Identity Creator duoc goi
    - target_address phai hop le (khac zero address)
    - DID phai ton tai
    - DID khong duoc o trang thai REVOKED
    - doc_hash khong duoc la bytes32 zero
    - CID khong duoc rong

    Tham so:
    - target_address: Dia chi vi cua Identity User
    - doc_hash: SHA-256 hash cua tai lieu goc
    - cid: IPFS CID cua file da ma hoa

    Tra ve: True neu thanh cong
    """
    assert self.creators[msg.sender], "Unauthorized: only Identity Creator allowed"
    assert target_address != empty(address), "Invalid target address"
    assert self.has_did[target_address], "DID does not exist for this address"
    assert self.records[target_address].status != STATUS_REVOKED, "Cannot verify a revoked DID"
    assert doc_hash != empty(bytes32), "Document hash cannot be empty"
    assert len(cid) > 0, "IPFS CID cannot be empty"

    self.records[target_address].doc_hash    = doc_hash
    self.records[target_address].ipfs_cid    = cid
    self.records[target_address].status      = STATUS_VERIFIED
    self.records[target_address].verified_at = block.timestamp
    self.records[target_address].updated_at  = block.timestamp
    self.records[target_address].verified_by = msg.sender

    self.total_verified += 1

    log DocumentHashStored(target_address, doc_hash, cid, msg.sender, block.timestamp)
    return True


@external
def updateDocumentHash(
    target_address: address,
    new_hash:       bytes32,
    new_cid:        String[128]
) -> bool:
    """
    Cap nhat hash tai lieu khi tai lieu thay doi (vd: gia han, cap nhat thong tin).
    Chi Identity Creator moi duoc goi.
    DID phai o trang thai VERIFIED truoc khi cap nhat.

    Rang buoc:
    - Chi Identity Creator duoc goi
    - DID phai o trang thai VERIFIED (khong cap nhat PENDING hoac REVOKED)
    - new_hash khong duoc rong va phai khac hash cu
    - new_cid khong duoc rong
    - So lan cap nhat khong vuot qua MAX_UPDATE_COUNT

    Tra ve: True neu thanh cong
    """
    assert self.creators[msg.sender], "Unauthorized: only Identity Creator allowed"
    assert target_address != empty(address), "Invalid target address"
    assert self.has_did[target_address], "DID does not exist for this address"
    assert self.records[target_address].status == STATUS_VERIFIED, "DID must be VERIFIED to update"
    assert new_hash != empty(bytes32), "New document hash cannot be empty"
    assert new_hash != self.records[target_address].doc_hash, "New hash must differ from current hash"
    assert len(new_cid) > 0, "New IPFS CID cannot be empty"
    assert self.records[target_address].update_count < MAX_UPDATE_COUNT, "Update limit reached"

    old_hash: bytes32 = self.records[target_address].doc_hash

    self.records[target_address].doc_hash     = new_hash
    self.records[target_address].ipfs_cid     = new_cid
    self.records[target_address].updated_at   = block.timestamp
    self.records[target_address].verified_by  = msg.sender
    self.records[target_address].update_count += 1

    log DocumentHashUpdated(target_address, old_hash, new_hash, new_cid, msg.sender, block.timestamp)
    return True


@external
def revokeDID(target_address: address) -> bool:
    """
    Thu hoi dinh danh. Sau khi revoke khong the xac minh hay cap nhat.

    Rang buoc:
    - Chi Identity Creator HOAC chinh chu so huu DID moi duoc thu hoi
    - DID phai ton tai
    - DID chua bi thu hoi truoc do

    Tham so:
    - target_address: Dia chi vi can thu hoi DID

    Tra ve: True neu thanh cong
    """
    assert self.creators[msg.sender] or msg.sender == target_address, \
        "Unauthorized: only Identity Creator or DID owner can revoke"
    assert self.has_did[target_address], "DID does not exist"
    assert self.records[target_address].status != STATUS_REVOKED, "DID already revoked"

    self.records[target_address].status     = STATUS_REVOKED
    self.records[target_address].updated_at = block.timestamp

    log DIDRevoked(
        target_address,
        self.records[target_address].did,
        msg.sender,
        block.timestamp
    )
    return True

# ============================================================
# VIEW FUNCTIONS
# ============================================================

@view
@external
def verifyDID(target_address: address) -> bool:
    """
    Kiem tra DID co hop le khong.
    Tra ve True chi khi status == VERIFIED.
    PENDING va REVOKED deu tra ve False.
    """
    if not self.has_did[target_address]:
        return False
    return self.records[target_address].status == STATUS_VERIFIED


@view
@external
def getDIDStatus(target_address: address) -> uint8:
    """
    Lay trang thai DID:
    0=PENDING, 1=VERIFIED, 2=REVOKED, 255=khong ton tai
    """
    if not self.has_did[target_address]:
        return STATUS_NOT_FOUND
    return self.records[target_address].status


@view
@external
def getDIDRecord(target_address: address) -> DIDRecord:
    """Lay toan bo ban ghi DID. Tra ve struct rong neu chua co DID."""
    return self.records[target_address]


@view
@external
def getDocumentHash(target_address: address) -> bytes32:
    """Lay hash tai lieu hien tai. Tra ve bytes32 zero neu chua xac minh."""
    return self.records[target_address].doc_hash


@view
@external
def getIPFSCid(target_address: address) -> String[128]:
    """Lay CID IPFS hien tai."""
    return self.records[target_address].ipfs_cid


@view
@external
def isCreator(addr: address) -> bool:
    """Kiem tra dia chi co quyen Identity Creator khong."""
    return self.creators[addr]


@view
@external
def hasDID(addr: address) -> bool:
    """Kiem tra dia chi da tao DID chua."""
    return self.has_did[addr]


@view
@external
def getStats() -> (uint256, uint256):
    """Tra ve (tong DID da tao, tong DID da xac minh)."""
    return self.total_dids, self.total_verified


@view
@external
def getOwner() -> address:
    """Lay dia chi contract owner."""
    return self.contract_owner

# ============================================================
# QUAN LY PHAN QUYEN
# ============================================================

@external
def grantCreatorRole(creator_address: address):
    """
    Cap quyen Identity Creator. Chi contract_owner duoc goi.

    Rang buoc:
    - Chi owner duoc goi
    - Dia chi phai hop le (khac zero)
    - Dia chi chua co quyen Creator
    """
    assert msg.sender == self.contract_owner, "Only contract owner can grant roles"
    assert creator_address != empty(address), "Invalid address: zero address not allowed"
    assert not self.creators[creator_address], "Address already has Creator role"

    self.creators[creator_address] = True
    log CreatorRoleGranted(creator_address, msg.sender)


@external
def revokeCreatorRole(creator_address: address):
    """
    Thu hoi quyen Identity Creator. Chi contract_owner duoc goi.

    Rang buoc:
    - Chi owner duoc goi
    - Khong the thu hoi quyen cua chinh owner
    - Dia chi phai dang co quyen Creator
    """
    assert msg.sender == self.contract_owner, "Only contract owner can revoke roles"
    assert creator_address != self.contract_owner, "Cannot revoke owner's Creator role"
    assert self.creators[creator_address], "Address does not have Creator role"

    self.creators[creator_address] = False
    log CreatorRoleRevoked(creator_address, msg.sender)


@external
def transferOwnership(new_owner: address):
    """
    Chuyen quyen so huu contract sang dia chi moi.

    Rang buoc:
    - Chi owner hien tai duoc goi
    - new_owner phai hop le (khac zero)
    - new_owner phai khac owner hien tai
    """
    assert msg.sender == self.contract_owner, "Only contract owner can transfer ownership"
    assert new_owner != empty(address), "Invalid address: zero address not allowed"
    assert new_owner != self.contract_owner, "New owner must differ from current owner"

    old_owner: address = self.contract_owner
    self.contract_owner = new_owner
    # Cap quyen Creator cho owner moi
    self.creators[new_owner] = True

    log OwnershipTransferred(old_owner, new_owner)
