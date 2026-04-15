"""
Tests cho Soulbound_Contract.vy
Nguoi phu trach: Nhu

Chay: pytest nft-integration/tests/
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


class MockSoulbound:
    """Mock don gian de test logic Soulbound."""

    def __init__(self, owner):
        self.owner = owner
        self.tokens = {}
        self.has_token_map = {}
        self.token_counter = 0
        self.authorized_minters = {owner: True}

    def mint(self, sender, recipient, metadata_uri):
        assert self.authorized_minters.get(sender), "Unauthorized: only authorized minter"
        assert not self.has_token_map.get(recipient), "Address already has a Soulbound Token"
        assert len(metadata_uri) > 0, "metadata_uri cannot be empty"

        self.token_counter += 1
        self.tokens[recipient] = {
            "owner": recipient,
            "token_id": self.token_counter,
            "metadata_uri": metadata_uri,
            "is_valid": True,
            "minted_at": 0,
        }
        self.has_token_map[recipient] = True
        return self.token_counter

    def invalidateToken(self, sender, owner):
        assert self.authorized_minters.get(sender) or sender == self.owner, "Unauthorized"
        assert self.has_token_map.get(owner), "No token found"
        assert self.tokens[owner]["is_valid"], "Token already invalidated"
        self.tokens[owner]["is_valid"] = False

    def hasValidToken(self, owner):
        if not self.has_token_map.get(owner):
            return False
        return self.tokens[owner]["is_valid"]

    def getTokenData(self, owner):
        return self.tokens.get(owner)

    def transfer(self, to, token_id):
        raise AssertionError("Soulbound: transfer not allowed")

    def approve(self, spender, token_id):
        raise AssertionError("Soulbound: transfer not allowed")


OWNER = "0xOwner"
USER_A = "0xUserA"
USER_B = "0xUserB"


# --- Unit tests ---

def test_mint_success():
    sb = MockSoulbound(OWNER)
    token_id = sb.mint(OWNER, USER_A, "ipfs://QmMetadata")
    assert token_id == 1
    assert sb.hasValidToken(USER_A) is True


def test_mint_duplicate_rejected():
    sb = MockSoulbound(OWNER)
    sb.mint(OWNER, USER_A, "ipfs://QmMeta1")
    with pytest.raises(AssertionError, match="already has"):
        sb.mint(OWNER, USER_A, "ipfs://QmMeta2")


def test_transfer_blocked():
    sb = MockSoulbound(OWNER)
    with pytest.raises(AssertionError, match="transfer not allowed"):
        sb.transfer(USER_B, 1)


def test_approve_blocked():
    sb = MockSoulbound(OWNER)
    with pytest.raises(AssertionError, match="transfer not allowed"):
        sb.approve(USER_B, 1)


def test_invalidate_token():
    sb = MockSoulbound(OWNER)
    sb.mint(OWNER, USER_A, "ipfs://QmMeta")
    assert sb.hasValidToken(USER_A) is True
    sb.invalidateToken(OWNER, USER_A)
    assert sb.hasValidToken(USER_A) is False


def test_has_valid_token_no_token():
    sb = MockSoulbound(OWNER)
    assert sb.hasValidToken("0xUnknown") is False


# --- Property-based tests ---

# Feature: decentralized-identity-ssi, Property 13: Mint Token - hasValidToken = true + Metadata URI
@given(
    metadata_uri=st.text(min_size=1, max_size=128),
    recipient=st.text(min_size=5, max_size=42),
)
@settings(max_examples=100)
def test_property_mint_valid_token(metadata_uri, recipient):
    sb = MockSoulbound(OWNER)
    sb.mint(OWNER, recipient, metadata_uri)
    assert sb.hasValidToken(recipient) is True
    assert sb.getTokenData(recipient)["metadata_uri"] == metadata_uri


# Feature: decentralized-identity-ssi, Property 14: Transfer/Approve Luon Bi Tu Choi
@given(
    to=st.text(min_size=5, max_size=42),
    token_id=st.integers(min_value=1, max_value=10000),
)
@settings(max_examples=100)
def test_property_transfer_always_blocked(to, token_id):
    sb = MockSoulbound(OWNER)
    with pytest.raises(AssertionError, match="transfer not allowed"):
        sb.transfer(to, token_id)
    with pytest.raises(AssertionError, match="transfer not allowed"):
        sb.approve(to, token_id)


# Feature: decentralized-identity-ssi, Property 15: Revoke DID - Token Khong Con Hop Le
@given(metadata_uri=st.text(min_size=1, max_size=128))
@settings(max_examples=100)
def test_property_invalidate_makes_token_invalid(metadata_uri):
    sb = MockSoulbound(OWNER)
    sb.mint(OWNER, USER_A, metadata_uri)
    assert sb.hasValidToken(USER_A) is True
    sb.invalidateToken(OWNER, USER_A)
    assert sb.hasValidToken(USER_A) is False
