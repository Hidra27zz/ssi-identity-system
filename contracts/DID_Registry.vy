# @version ^0.3.10
# DID Registry - Quan ly dinh danh phi tap trung
# Nguoi phu trach: Nhan

# Events
event DIDCreated:
    owner: indexed(address)
    did: String[64]
    timestamp: uint256

event DocumentHashStored:
    owner: indexed(address)
    doc_hash: bytes32
    cid: String[64]
    verified_by: address

event DIDRevoked:
    owner: indexed(address)
    did: String[64]
    timestamp: uint256

event CreatorRoleSet:
    creator: indexed(address)
    has_role: bool

# Structs
struct DIDRecord:
    owner: address
    did: String[64]
    doc_hash: bytes32
    ipfs_cid: String[64]
    is_active: bool
    created_at: uint256
    verified_by: address

# Storage
records: HashMap[address, DIDRecord]
has_did: HashMap[address, bool]
creators: HashMap[address, bool]
owner: address

@deploy
def __init__():
    self.owner = msg.sender
    self.creators[msg.sender] = True

@external
def createDID(did: String[64]) -> bool:
    assert not self.has_did[msg.sender], "DID already exists"
    assert len(did) > 0, "DID cannot be empty"

    self.records[msg.sender] = DIDRecord(
        owner=msg.sender,
        did=did,
        doc_hash=empty(bytes32),
        ipfs_cid="",
        is_active=True,
        created_at=block.timestamp,
        verified_by=empty(address)
    )
    self.has_did[msg.sender] = True

    log DIDCreated(msg.sender, did, block.timestamp)
    return True

@external
def storeDocumentHash(target_address: address, doc_hash: bytes32, cid: String[64]) -> bool:
    assert self.creators[msg.sender], "Unauthorized: only Identity Creator allowed"
    assert self.has_did[target_address], "DID does not exist"
    assert self.records[target_address].is_active, "DID has been revoked"

    self.records[target_address].doc_hash = doc_hash
    self.records[target_address].ipfs_cid = cid
    self.records[target_address].verified_by = msg.sender

    log DocumentHashStored(target_address, doc_hash, cid, msg.sender)
    return True

@external
def revokeDID(target_address: address) -> bool:
    assert self.creators[msg.sender] or msg.sender == target_address, "Unauthorized"
    assert self.has_did[target_address], "DID does not exist"
    assert self.records[target_address].is_active, "DID already revoked"

    self.records[target_address].is_active = False

    log DIDRevoked(target_address, self.records[target_address].did, block.timestamp)
    return True

@view
@external
def verifyDID(target_address: address) -> bool:
    if not self.has_did[target_address]:
        return False
    return self.records[target_address].is_active

@view
@external
def getDIDRecord(target_address: address) -> DIDRecord:
    return self.records[target_address]

@external
def setCreatorRole(creator_address: address, has_role: bool):
    assert msg.sender == self.owner, "Only owner can set creator role"
    self.creators[creator_address] = has_role
    log CreatorRoleSet(creator_address, has_role)

@view
@external
def isCreator(addr: address) -> bool:
    return self.creators[addr]
