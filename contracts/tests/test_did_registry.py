"""
Tests cho DID_Registry.vy
Nguoi phu trach: Nhan

Chay: pytest contracts/tests/ -v
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ============================================================
# CONSTANTS - khop voi Vyper contract
# ============================================================

STATUS_PENDING   = 0
STATUS_VERIFIED  = 1
STATUS_REVOKED   = 2
STATUS_NOT_FOUND = 255
MAX_UPDATE_COUNT = 10

# ============================================================
# MOCK
# ============================================================

class MockDIDRegistry:
    """Gia lap DID_Registry.vy bang Python. Logic khop chinh xac voi Vyper."""

    def __init__(self, owner: str):
        self.contract_owner = owner
        self.records: dict = {}
        self.has_did_map: dict = {}
        self.creators: dict = {owner: True}
        self.total_dids = 0
        self.total_verified = 0
        self._timestamp = 1000

    def _next_ts(self) -> int:
        self._timestamp += 1
        return self._timestamp

    def createDID(self, sender: str, did: str) -> bool:
        assert not self.has_did_map.get(sender), "DID already exists for this address"
        assert len(did) > 0, "DID string cannot be empty"
        self.records[sender] = {
            "owner": sender, "did": did,
            "doc_hash": b"\x00" * 32, "ipfs_cid": "",
            "status": STATUS_PENDING,
            "created_at": self._next_ts(), "verified_at": 0,
            "updated_at": 0, "verified_by": None, "update_count": 0,
        }
        self.has_did_map[sender] = True
        self.total_dids += 1
        return True

    def storeDocumentHash(self, sender: str, target: str, doc_hash: bytes, cid: str) -> bool:
        assert self.creators.get(sender), "Unauthorized: only Identity Creator allowed"
        assert target != "", "Invalid target address"
        assert self.has_did_map.get(target), "DID does not exist for this address"
        assert self.records[target]["status"] != STATUS_REVOKED, "Cannot verify a revoked DID"
        assert doc_hash != b"\x00" * 32, "Document hash cannot be empty"
        assert len(cid) > 0, "IPFS CID cannot be empty"
        ts = self._next_ts()
        self.records[target].update({
            "doc_hash": doc_hash, "ipfs_cid": cid,
            "status": STATUS_VERIFIED,
            "verified_at": ts, "updated_at": ts, "verified_by": sender,
        })
        self.total_verified += 1
        return True

    def updateDocumentHash(self, sender: str, target: str, new_hash: bytes, new_cid: str) -> bool:
        assert self.creators.get(sender), "Unauthorized: only Identity Creator allowed"
        assert target != "", "Invalid target address"
        assert self.has_did_map.get(target), "DID does not exist for this address"
        assert self.records[target]["status"] == STATUS_VERIFIED, "DID must be VERIFIED to update"
        assert new_hash != b"\x00" * 32, "New document hash cannot be empty"
        assert new_hash != self.records[target]["doc_hash"], "New hash must differ from current hash"
        assert len(new_cid) > 0, "New IPFS CID cannot be empty"
        assert self.records[target]["update_count"] < MAX_UPDATE_COUNT, "Update limit reached"
        self.records[target].update({
            "doc_hash": new_hash, "ipfs_cid": new_cid,
            "updated_at": self._next_ts(), "verified_by": sender,
            "update_count": self.records[target]["update_count"] + 1,
        })
        return True

    def revokeDID(self, sender: str, target: str) -> bool:
        assert self.creators.get(sender) or sender == target, \
            "Unauthorized: only Identity Creator or DID owner can revoke"
        assert self.has_did_map.get(target), "DID does not exist"
        assert self.records[target]["status"] != STATUS_REVOKED, "DID already revoked"
        self.records[target]["status"] = STATUS_REVOKED
        self.records[target]["updated_at"] = self._next_ts()
        return True

    def verifyDID(self, target: str) -> bool:
        if not self.has_did_map.get(target):
            return False
        return self.records[target]["status"] == STATUS_VERIFIED

    def getDIDStatus(self, target: str) -> int:
        if not self.has_did_map.get(target):
            return STATUS_NOT_FOUND
        return self.records[target]["status"]

    def getDIDRecord(self, target: str) -> dict:
        return self.records.get(target, {})

    def grantCreatorRole(self, sender: str, creator: str):
        assert sender == self.contract_owner, "Only contract owner can grant roles"
        assert creator != "", "Invalid address: zero address not allowed"
        assert not self.creators.get(creator), "Address already has Creator role"
        self.creators[creator] = True

    def revokeCreatorRole(self, sender: str, creator: str):
        assert sender == self.contract_owner, "Only contract owner can revoke roles"
        assert creator != self.contract_owner, "Cannot revoke owner's Creator role"
        assert self.creators.get(creator), "Address does not have Creator role"
        self.creators[creator] = False

    def transferOwnership(self, sender: str, new_owner: str):
        assert sender == self.contract_owner, "Only contract owner can transfer ownership"
        assert new_owner != "", "Invalid address: zero address not allowed"
        assert new_owner != self.contract_owner, "New owner must differ from current owner"
        self.contract_owner = new_owner
        self.creators[new_owner] = True

    def getStats(self) -> tuple:
        return self.total_dids, self.total_verified

# ============================================================
# FIXTURES
# ============================================================

OWNER    = "0xOwner"
USER_A   = "0xUserA"
USER_B   = "0xUserB"
CREATOR  = "0xCreator"
CREATOR2 = "0xCreator2"
VERIFIER = "0xVerifier"

VALID_HASH  = b"\xab" * 32
VALID_HASH2 = b"\xcd" * 32
VALID_CID   = "QmTestCID123456789"
VALID_CID2  = "QmTestCID987654321"

@pytest.fixture
def reg():
    return MockDIDRegistry(OWNER)

@pytest.fixture
def reg_did(reg):
    reg.createDID(USER_A, "did:ssi:userA")
    return reg

@pytest.fixture
def reg_verified(reg_did):
    reg_did.storeDocumentHash(OWNER, USER_A, VALID_HASH, VALID_CID)
    return reg_did

# ============================================================
# TESTS: createDID
# ============================================================

class TestCreateDID:
    def test_success(self, reg):
        assert reg.createDID(USER_A, "did:ssi:userA") is True
        assert reg.has_did_map[USER_A] is True
        assert reg.getDIDStatus(USER_A) == STATUS_PENDING

    def test_status_is_pending_not_verified(self, reg):
        reg.createDID(USER_A, "did:ssi:userA")
        assert reg.verifyDID(USER_A) is False  # PENDING != VERIFIED

    def test_record_fields_initialized_correctly(self, reg):
        reg.createDID(USER_A, "did:ssi:userA")
        r = reg.getDIDRecord(USER_A)
        assert r["did"] == "did:ssi:userA"
        assert r["owner"] == USER_A
        assert r["doc_hash"] == b"\x00" * 32
        assert r["ipfs_cid"] == ""
        assert r["verified_by"] is None
        assert r["update_count"] == 0

    def test_counter_increments(self, reg):
        assert reg.total_dids == 0
        reg.createDID(USER_A, "did:ssi:userA")
        reg.createDID(USER_B, "did:ssi:userB")
        assert reg.total_dids == 2

    def test_duplicate_rejected(self, reg):
        reg.createDID(USER_A, "did:ssi:userA")
        with pytest.raises(AssertionError, match="DID already exists"):
            reg.createDID(USER_A, "did:ssi:other")

    def test_empty_string_rejected(self, reg):
        with pytest.raises(AssertionError, match="cannot be empty"):
            reg.createDID(USER_A, "")

    def test_different_users_can_each_create_did(self, reg):
        reg.createDID(USER_A, "did:ssi:userA")
        reg.createDID(USER_B, "did:ssi:userB")
        assert reg.getDIDStatus(USER_A) == STATUS_PENDING
        assert reg.getDIDStatus(USER_B) == STATUS_PENDING

    def test_unknown_address_returns_not_found(self, reg):
        assert reg.getDIDStatus("0xUnknown") == STATUS_NOT_FOUND
        assert reg.verifyDID("0xUnknown") is False


# ============================================================
# TESTS: storeDocumentHash
# ============================================================

class TestStoreDocumentHash:
    def test_success(self, reg_did):
        assert reg_did.storeDocumentHash(OWNER, USER_A, VALID_HASH, VALID_CID) is True
        r = reg_did.getDIDRecord(USER_A)
        assert r["status"] == STATUS_VERIFIED
        assert r["doc_hash"] == VALID_HASH
        assert r["ipfs_cid"] == VALID_CID
        assert r["verified_by"] == OWNER

    def test_status_changes_to_verified(self, reg_did):
        assert reg_did.getDIDStatus(USER_A) == STATUS_PENDING
        reg_did.storeDocumentHash(OWNER, USER_A, VALID_HASH, VALID_CID)
        assert reg_did.getDIDStatus(USER_A) == STATUS_VERIFIED
        assert reg_did.verifyDID(USER_A) is True

    def test_verified_counter_increments(self, reg_did):
        assert reg_did.total_verified == 0
        reg_did.storeDocumentHash(OWNER, USER_A, VALID_HASH, VALID_CID)
        assert reg_did.total_verified == 1

    def test_unauthorized_user_rejected(self, reg_did):
        with pytest.raises(AssertionError, match="Unauthorized: only Identity Creator"):
            reg_did.storeDocumentHash(USER_B, USER_A, VALID_HASH, VALID_CID)

    def test_verifier_cannot_store_hash(self, reg_did):
        with pytest.raises(AssertionError, match="Unauthorized"):
            reg_did.storeDocumentHash(VERIFIER, USER_A, VALID_HASH, VALID_CID)

    def test_nonexistent_did_rejected(self, reg):
        with pytest.raises(AssertionError, match="DID does not exist"):
            reg.storeDocumentHash(OWNER, USER_A, VALID_HASH, VALID_CID)

    def test_zero_hash_rejected(self, reg_did):
        with pytest.raises(AssertionError, match="hash cannot be empty"):
            reg_did.storeDocumentHash(OWNER, USER_A, b"\x00" * 32, VALID_CID)

    def test_empty_cid_rejected(self, reg_did):
        with pytest.raises(AssertionError, match="CID cannot be empty"):
            reg_did.storeDocumentHash(OWNER, USER_A, VALID_HASH, "")

    def test_revoked_did_rejected(self, reg_did):
        reg_did.revokeDID(OWNER, USER_A)
        with pytest.raises(AssertionError, match="Cannot verify a revoked DID"):
            reg_did.storeDocumentHash(OWNER, USER_A, VALID_HASH, VALID_CID)

    def test_second_creator_can_also_store(self, reg_did):
        reg_did.grantCreatorRole(OWNER, CREATOR)
        assert reg_did.storeDocumentHash(CREATOR, USER_A, VALID_HASH, VALID_CID) is True
        assert reg_did.getDIDRecord(USER_A)["verified_by"] == CREATOR

    def test_store_on_already_verified_overwrites(self, reg_verified):
        # Creator co the cap nhat bang storeDocumentHash (ghi de)
        reg_verified.storeDocumentHash(OWNER, USER_A, VALID_HASH2, VALID_CID2)
        r = reg_verified.getDIDRecord(USER_A)
        assert r["doc_hash"] == VALID_HASH2
        assert r["ipfs_cid"] == VALID_CID2


# ============================================================
# TESTS: updateDocumentHash
# ============================================================

class TestUpdateDocumentHash:
    def test_success(self, reg_verified):
        assert reg_verified.updateDocumentHash(OWNER, USER_A, VALID_HASH2, VALID_CID2) is True
        r = reg_verified.getDIDRecord(USER_A)
        assert r["doc_hash"] == VALID_HASH2
        assert r["ipfs_cid"] == VALID_CID2
        assert r["update_count"] == 1

    def test_update_count_increments(self, reg_verified):
        reg_verified.updateDocumentHash(OWNER, USER_A, VALID_HASH2, VALID_CID2)
        assert reg_verified.getDIDRecord(USER_A)["update_count"] == 1

    def test_status_stays_verified_after_update(self, reg_verified):
        reg_verified.updateDocumentHash(OWNER, USER_A, VALID_HASH2, VALID_CID2)
        assert reg_verified.getDIDStatus(USER_A) == STATUS_VERIFIED

    def test_cannot_update_pending_did(self, reg_did):
        with pytest.raises(AssertionError, match="must be VERIFIED"):
            reg_did.updateDocumentHash(OWNER, USER_A, VALID_HASH2, VALID_CID2)

    def test_cannot_update_revoked_did(self, reg_verified):
        reg_verified.revokeDID(OWNER, USER_A)
        with pytest.raises(AssertionError, match="must be VERIFIED"):
            reg_verified.updateDocumentHash(OWNER, USER_A, VALID_HASH2, VALID_CID2)

    def test_same_hash_rejected(self, reg_verified):
        with pytest.raises(AssertionError, match="must differ"):
            reg_verified.updateDocumentHash(OWNER, USER_A, VALID_HASH, VALID_CID2)

    def test_zero_hash_rejected(self, reg_verified):
        with pytest.raises(AssertionError, match="hash cannot be empty"):
            reg_verified.updateDocumentHash(OWNER, USER_A, b"\x00" * 32, VALID_CID2)

    def test_empty_cid_rejected(self, reg_verified):
        with pytest.raises(AssertionError, match="CID cannot be empty"):
            reg_verified.updateDocumentHash(OWNER, USER_A, VALID_HASH2, "")

    def test_unauthorized_rejected(self, reg_verified):
        with pytest.raises(AssertionError, match="Unauthorized"):
            reg_verified.updateDocumentHash(USER_B, USER_A, VALID_HASH2, VALID_CID2)

    def test_update_limit_enforced(self, reg_verified):
        # Cap nhat MAX_UPDATE_COUNT lan
        for i in range(MAX_UPDATE_COUNT):
            h = bytes([i + 1]) * 32
            c = f"QmCID{i}"
            reg_verified.updateDocumentHash(OWNER, USER_A, h, c)
        # Lan thu MAX_UPDATE_COUNT + 1 phai bi tu choi
        with pytest.raises(AssertionError, match="Update limit reached"):
            reg_verified.updateDocumentHash(OWNER, USER_A, b"\xff" * 32, "QmFinal")


# ============================================================
# TESTS: verifyDID
# ============================================================

class TestVerifyDID:
    def test_pending_returns_false(self, reg_did):
        assert reg_did.verifyDID(USER_A) is False

    def test_verified_returns_true(self, reg_verified):
        assert reg_verified.verifyDID(USER_A) is True

    def test_revoked_returns_false(self, reg_verified):
        reg_verified.revokeDID(OWNER, USER_A)
        assert reg_verified.verifyDID(USER_A) is False

    def test_nonexistent_returns_false(self, reg):
        assert reg.verifyDID("0xUnknown") is False

    def test_after_update_still_verified(self, reg_verified):
        reg_verified.updateDocumentHash(OWNER, USER_A, VALID_HASH2, VALID_CID2)
        assert reg_verified.verifyDID(USER_A) is True


# ============================================================
# TESTS: revokeDID
# ============================================================

class TestRevokeDID:
    def test_creator_can_revoke(self, reg_verified):
        assert reg_verified.revokeDID(OWNER, USER_A) is True
        assert reg_verified.getDIDStatus(USER_A) == STATUS_REVOKED

    def test_owner_can_self_revoke(self, reg_did):
        assert reg_did.revokeDID(USER_A, USER_A) is True
        assert reg_did.getDIDStatus(USER_A) == STATUS_REVOKED

    def test_can_revoke_pending_did(self, reg_did):
        # Revoke duoc ca DID o trang thai PENDING
        assert reg_did.revokeDID(OWNER, USER_A) is True
        assert reg_did.getDIDStatus(USER_A) == STATUS_REVOKED

    def test_unauthorized_rejected(self, reg_did):
        with pytest.raises(AssertionError, match="Unauthorized"):
            reg_did.revokeDID(USER_B, USER_A)

    def test_nonexistent_did_rejected(self, reg):
        with pytest.raises(AssertionError, match="DID does not exist"):
            reg.revokeDID(OWNER, USER_A)

    def test_double_revoke_rejected(self, reg_did):
        reg_did.revokeDID(OWNER, USER_A)
        with pytest.raises(AssertionError, match="already revoked"):
            reg_did.revokeDID(OWNER, USER_A)

    def test_verify_after_revoke_returns_false(self, reg_verified):
        reg_verified.revokeDID(OWNER, USER_A)
        assert reg_verified.verifyDID(USER_A) is False

    def test_second_creator_can_revoke(self, reg_did):
        reg_did.grantCreatorRole(OWNER, CREATOR)
        assert reg_did.revokeDID(CREATOR, USER_A) is True


# ============================================================
# TESTS: Phan quyen Creator
# ============================================================

class TestCreatorRole:
    def test_grant_success(self, reg):
        reg.grantCreatorRole(OWNER, CREATOR)
        assert reg.creators[CREATOR] is True

    def test_grant_unauthorized(self, reg):
        with pytest.raises(AssertionError, match="Only contract owner"):
            reg.grantCreatorRole(USER_A, CREATOR)

    def test_grant_zero_address_rejected(self, reg):
        with pytest.raises(AssertionError, match="Invalid address"):
            reg.grantCreatorRole(OWNER, "")

    def test_grant_duplicate_rejected(self, reg):
        reg.grantCreatorRole(OWNER, CREATOR)
        with pytest.raises(AssertionError, match="already has Creator role"):
            reg.grantCreatorRole(OWNER, CREATOR)

    def test_revoke_success(self, reg):
        reg.grantCreatorRole(OWNER, CREATOR)
        reg.revokeCreatorRole(OWNER, CREATOR)
        assert reg.creators.get(CREATOR) is False

    def test_revoke_owner_role_rejected(self, reg):
        with pytest.raises(AssertionError, match="Cannot revoke owner"):
            reg.revokeCreatorRole(OWNER, OWNER)

    def test_revoke_nonexistent_role_rejected(self, reg):
        with pytest.raises(AssertionError, match="does not have Creator role"):
            reg.revokeCreatorRole(OWNER, CREATOR)

    def test_revoked_creator_cannot_store(self, reg_did):
        reg_did.grantCreatorRole(OWNER, CREATOR)
        reg_did.revokeCreatorRole(OWNER, CREATOR)
        with pytest.raises(AssertionError, match="Unauthorized"):
            reg_did.storeDocumentHash(CREATOR, USER_A, VALID_HASH, VALID_CID)

    def test_multiple_creators_independent(self, reg_did):
        reg_did.grantCreatorRole(OWNER, CREATOR)
        reg_did.grantCreatorRole(OWNER, CREATOR2)
        # Ca hai deu co the xac minh
        reg_did.createDID(USER_B, "did:ssi:userB")
        assert reg_did.storeDocumentHash(CREATOR, USER_A, VALID_HASH, VALID_CID) is True
        assert reg_did.storeDocumentHash(CREATOR2, USER_B, VALID_HASH2, VALID_CID2) is True


# ============================================================
# TESTS: transferOwnership
# ============================================================

class TestTransferOwnership:
    def test_success(self, reg):
        reg.transferOwnership(OWNER, USER_A)
        assert reg.contract_owner == USER_A
        assert reg.creators[USER_A] is True

    def test_new_owner_can_grant_roles(self, reg):
        reg.transferOwnership(OWNER, USER_A)
        reg.grantCreatorRole(USER_A, CREATOR)
        assert reg.creators[CREATOR] is True

    def test_old_owner_loses_admin(self, reg):
        reg.transferOwnership(OWNER, USER_A)
        with pytest.raises(AssertionError, match="Only contract owner"):
            reg.grantCreatorRole(OWNER, CREATOR)

    def test_unauthorized_rejected(self, reg):
        with pytest.raises(AssertionError, match="Only contract owner"):
            reg.transferOwnership(USER_A, USER_B)

    def test_zero_address_rejected(self, reg):
        with pytest.raises(AssertionError, match="Invalid address"):
            reg.transferOwnership(OWNER, "")

    def test_same_owner_rejected(self, reg):
        with pytest.raises(AssertionError, match="must differ"):
            reg.transferOwnership(OWNER, OWNER)


# ============================================================
# TESTS: End-to-end flows
# ============================================================

class TestEndToEnd:
    def test_full_flow_pending_verified_revoked(self, reg):
        reg.createDID(USER_A, "did:ssi:userA")
        assert reg.getDIDStatus(USER_A) == STATUS_PENDING
        assert reg.verifyDID(USER_A) is False

        reg.storeDocumentHash(OWNER, USER_A, VALID_HASH, VALID_CID)
        assert reg.getDIDStatus(USER_A) == STATUS_VERIFIED
        assert reg.verifyDID(USER_A) is True

        reg.updateDocumentHash(OWNER, USER_A, VALID_HASH2, VALID_CID2)
        assert reg.verifyDID(USER_A) is True

        reg.revokeDID(OWNER, USER_A)
        assert reg.getDIDStatus(USER_A) == STATUS_REVOKED
        assert reg.verifyDID(USER_A) is False

    def test_stats_tracking(self, reg):
        reg.createDID(USER_A, "did:ssi:userA")
        reg.createDID(USER_B, "did:ssi:userB")
        reg.storeDocumentHash(OWNER, USER_A, VALID_HASH, VALID_CID)
        total, verified = reg.getStats()
        assert total == 2
        assert verified == 1

    def test_multiple_users_independent(self, reg):
        reg.createDID(USER_A, "did:ssi:userA")
        reg.createDID(USER_B, "did:ssi:userB")
        reg.storeDocumentHash(OWNER, USER_A, VALID_HASH, VALID_CID)
        # Revoke USER_A khong anh huong USER_B
        reg.revokeDID(OWNER, USER_A)
        assert reg.verifyDID(USER_A) is False
        assert reg.getDIDStatus(USER_B) == STATUS_PENDING

    def test_creator_cannot_create_did_for_others(self, reg):
        # Creator chi co the xac minh, khong the tao DID thay nguoi khac
        # createDID luon dung msg.sender (USER_A tu tao cho chinh minh)
        reg.createDID(USER_A, "did:ssi:userA")
        assert reg.getDIDRecord(USER_A)["owner"] == USER_A


# ============================================================
# PROPERTY-BASED TESTS
# ============================================================

# Property 1: createDID Round-Trip
@given(did=st.text(min_size=1, max_size=128).filter(lambda s: len(s) > 0))
@settings(max_examples=100)
def test_property_create_did_roundtrip(did):
    reg = MockDIDRegistry(OWNER)
    reg.createDID(USER_A, did)
    r = reg.getDIDRecord(USER_A)
    assert r["did"] == did
    assert r["status"] == STATUS_PENDING
    assert reg.verifyDID(USER_A) is False


# Property 2: Duplicate DID bi tu choi, trang thai khong thay doi
@given(did=st.text(min_size=1, max_size=128).filter(lambda s: len(s) > 0))
@settings(max_examples=100)
def test_property_duplicate_rejected(did):
    reg = MockDIDRegistry(OWNER)
    reg.createDID(USER_A, did)
    original = reg.getDIDRecord(USER_A)["did"]
    with pytest.raises(AssertionError, match="DID already exists"):
        reg.createDID(USER_A, did + "_x")
    assert reg.getDIDRecord(USER_A)["did"] == original


# Property 3: storeDocumentHash Round-Trip
@given(
    cid=st.text(min_size=1, max_size=128).filter(lambda s: len(s) > 0),
    doc_hash=st.binary(min_size=32, max_size=32).filter(lambda b: b != b"\x00" * 32),
)
@settings(max_examples=100)
def test_property_store_hash_roundtrip(cid, doc_hash):
    reg = MockDIDRegistry(OWNER)
    reg.createDID(USER_A, "did:ssi:test")
    reg.storeDocumentHash(OWNER, USER_A, doc_hash, cid)
    r = reg.getDIDRecord(USER_A)
    assert r["doc_hash"] == doc_hash
    assert r["ipfs_cid"] == cid
    assert r["status"] == STATUS_VERIFIED


# Property 4: Revoke lam mat hieu luc DID
@given(did=st.text(min_size=1, max_size=128).filter(lambda s: len(s) > 0))
@settings(max_examples=100)
def test_property_revoke_invalidates(did):
    reg = MockDIDRegistry(OWNER)
    reg.createDID(USER_A, did)
    reg.storeDocumentHash(OWNER, USER_A, VALID_HASH, VALID_CID)
    assert reg.verifyDID(USER_A) is True
    reg.revokeDID(OWNER, USER_A)
    assert reg.verifyDID(USER_A) is False
    assert reg.getDIDStatus(USER_A) == STATUS_REVOKED


# Property 5: Unauthorized store bi tu choi, trang thai khong thay doi
@given(did=st.text(min_size=1, max_size=128).filter(lambda s: len(s) > 0))
@settings(max_examples=100)
def test_property_unauthorized_store_rejected(did):
    reg = MockDIDRegistry(OWNER)
    reg.createDID(USER_A, did)
    before = reg.getDIDStatus(USER_A)
    with pytest.raises(AssertionError, match="Unauthorized"):
        reg.storeDocumentHash(USER_B, USER_A, VALID_HASH, VALID_CID)
    assert reg.getDIDStatus(USER_A) == before


# Property 6: verifyDID chi True khi VERIFIED
@given(did=st.text(min_size=1, max_size=128).filter(lambda s: len(s) > 0))
@settings(max_examples=100)
def test_property_verify_only_true_when_verified(did):
    reg = MockDIDRegistry(OWNER)
    reg.createDID(USER_A, did)
    # PENDING -> False
    assert reg.verifyDID(USER_A) is False
    reg.storeDocumentHash(OWNER, USER_A, VALID_HASH, VALID_CID)
    # VERIFIED -> True
    assert reg.verifyDID(USER_A) is True
    reg.revokeDID(OWNER, USER_A)
    # REVOKED -> False
    assert reg.verifyDID(USER_A) is False
