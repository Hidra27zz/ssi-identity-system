"""
Tests cho DID_Registry.vy
Nguoi phu trach: Nhan

Chay: pytest contracts/tests/
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# --- Helpers (thay bang brownie/ape fixtures khi co moi truong) ---

class MockDIDRegistry:
    """Mock don gian de test logic, thay bang contract thuc khi deploy."""

    def __init__(self, owner):
        self.owner = owner
        self.records = {}
        self.has_did = {}
        self.creators = {owner: True}

    def createDID(self, sender, did):
        assert not self.has_did.get(sender), "DID already exists"
        assert len(did) > 0, "DID cannot be empty"
        self.records[sender] = {
            "owner": sender,
            "did": did,
            "doc_hash": None,
            "ipfs_cid": "",
            "is_active": True,
            "verified_by": None,
        }
        self.has_did[sender] = True
        return True

    def storeDocumentHash(self, sender, target, doc_hash, cid):
        assert self.creators.get(sender), "Unauthorized: only Identity Creator allowed"
        assert self.has_did.get(target), "DID does not exist"
        assert self.records[target]["is_active"], "DID has been revoked"
        self.records[target]["doc_hash"] = doc_hash
        self.records[target]["ipfs_cid"] = cid
        self.records[target]["verified_by"] = sender
        return True

    def revokeDID(self, sender, target):
        assert self.creators.get(sender) or sender == target, "Unauthorized"
        assert self.has_did.get(target), "DID does not exist"
        assert self.records[target]["is_active"], "DID already revoked"
        self.records[target]["is_active"] = False
        return True

    def verifyDID(self, target):
        if not self.has_did.get(target):
            return False
        return self.records[target]["is_active"]

    def getDIDRecord(self, target):
        return self.records.get(target)

    def setCreatorRole(self, sender, creator, has_role):
        assert sender == self.owner, "Only owner can set creator role"
        self.creators[creator] = has_role


OWNER = "0xOwner"
USER_A = "0xUserA"
USER_B = "0xUserB"
CREATOR = "0xCreator"


# --- Unit tests ---

def test_create_did_success():
    registry = MockDIDRegistry(OWNER)
    result = registry.createDID(USER_A, "did:ssi:userA")
    assert result is True
    record = registry.getDIDRecord(USER_A)
    assert record["did"] == "did:ssi:userA"
    assert record["is_active"] is True


def test_create_did_duplicate_rejected():
    registry = MockDIDRegistry(OWNER)
    registry.createDID(USER_A, "did:ssi:userA")
    with pytest.raises(AssertionError, match="DID already exists"):
        registry.createDID(USER_A, "did:ssi:userA2")


def test_store_hash_success():
    registry = MockDIDRegistry(OWNER)
    registry.createDID(USER_A, "did:ssi:userA")
    result = registry.storeDocumentHash(OWNER, USER_A, b"hash" * 8, "QmCID123")
    assert result is True
    record = registry.getDIDRecord(USER_A)
    assert record["ipfs_cid"] == "QmCID123"
    assert record["verified_by"] == OWNER


def test_store_hash_unauthorized():
    registry = MockDIDRegistry(OWNER)
    registry.createDID(USER_A, "did:ssi:userA")
    with pytest.raises(AssertionError, match="Unauthorized"):
        registry.storeDocumentHash(USER_B, USER_A, b"hash" * 8, "QmCID123")


def test_revoke_did():
    registry = MockDIDRegistry(OWNER)
    registry.createDID(USER_A, "did:ssi:userA")
    registry.revokeDID(OWNER, USER_A)
    assert registry.verifyDID(USER_A) is False


def test_verify_did_not_found():
    registry = MockDIDRegistry(OWNER)
    assert registry.verifyDID("0xUnknown") is False


def test_verify_revoked_did_returns_false():
    registry = MockDIDRegistry(OWNER)
    registry.createDID(USER_A, "did:ssi:userA")
    registry.storeDocumentHash(OWNER, USER_A, b"hash" * 8, "QmCID")
    registry.revokeDID(OWNER, USER_A)
    assert registry.verifyDID(USER_A) is False


# --- Property-based tests ---

# Feature: decentralized-identity-ssi, Property 1: createDID Round-Trip
@given(did=st.text(min_size=1, max_size=64, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=":_-")))
@settings(max_examples=100)
def test_property_create_did_roundtrip(did):
    registry = MockDIDRegistry(OWNER)
    registry.createDID(USER_A, did)
    record = registry.getDIDRecord(USER_A)
    assert record["did"] == did
    assert record["is_active"] is True


# Feature: decentralized-identity-ssi, Property 2: Duplicate DID Bi Tu Choi
@given(did=st.text(min_size=1, max_size=64))
@settings(max_examples=100)
def test_property_duplicate_did_rejected(did):
    registry = MockDIDRegistry(OWNER)
    registry.createDID(USER_A, did)
    with pytest.raises(AssertionError, match="DID already exists"):
        registry.createDID(USER_A, did + "_2")
    # Trang thai khong thay doi
    assert registry.getDIDRecord(USER_A)["did"] == did


# Feature: decentralized-identity-ssi, Property 3: storeDocumentHash Round-Trip
@given(
    cid=st.text(min_size=1, max_size=64, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    doc_hash=st.binary(min_size=32, max_size=32),
)
@settings(max_examples=100)
def test_property_store_hash_roundtrip(cid, doc_hash):
    registry = MockDIDRegistry(OWNER)
    registry.createDID(USER_A, "did:ssi:test")
    registry.storeDocumentHash(OWNER, USER_A, doc_hash, cid)
    record = registry.getDIDRecord(USER_A)
    assert record["ipfs_cid"] == cid
    assert record["doc_hash"] == doc_hash


# Feature: decentralized-identity-ssi, Property 4: Revoke Lam Mat Hieu Luc DID
@given(did=st.text(min_size=1, max_size=64))
@settings(max_examples=100)
def test_property_revoke_invalidates_did(did):
    registry = MockDIDRegistry(OWNER)
    registry.createDID(USER_A, did)
    assert registry.verifyDID(USER_A) is True
    registry.revokeDID(OWNER, USER_A)
    assert registry.verifyDID(USER_A) is False
    assert registry.getDIDRecord(USER_A)["is_active"] is False


# Feature: decentralized-identity-ssi, Property 5: Unauthorized Access Bi Tu Choi
@given(did=st.text(min_size=1, max_size=64))
@settings(max_examples=100)
def test_property_unauthorized_rejected(did):
    registry = MockDIDRegistry(OWNER)
    registry.createDID(USER_A, did)
    original_record = dict(registry.getDIDRecord(USER_A))
    with pytest.raises(AssertionError, match="Unauthorized"):
        registry.storeDocumentHash(USER_B, USER_A, b"x" * 32, "QmCID")
    # Trang thai contract khong thay doi
    assert registry.getDIDRecord(USER_A)["ipfs_cid"] == original_record["ipfs_cid"]
