"""
Tests cho Soulbound_Contract.vy
Nguoi phu trach: Nhu

Chay: pytest nft-integration/tests/
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# =========================
# MOCK SOULBOUND (NEW LOGIC)
# =========================
class MockSoulbound:
    """
    Mock theo đúng contract mới:
    - 1 user có thể có nhiều token
    - token quản lý theo token_id
    """

    def __init__(self, owner):
        self.owner = owner
        self.tokens = {}  # token_id -> data
        self.owner_tokens = {}  # address -> list token_id
        self.token_counter = 0
        self.authorized_minters = {owner: True}

    def mint(self, sender, recipient, metadata_uri):
        assert self.authorized_minters.get(sender), "Unauthorized"
        assert len(metadata_uri) > 0, "metadata_uri cannot be empty"

        self.token_counter += 1
        token_id = self.token_counter

        self.tokens[token_id] = {
            "owner": recipient,
            "token_id": token_id,
            "metadata_uri": metadata_uri,
            "is_valid": True,
        }

        if recipient not in self.owner_tokens:
            self.owner_tokens[recipient] = []

        self.owner_tokens[recipient].append(token_id)

        return token_id

    def invalidateToken(self, sender, token_id):
        assert self.authorized_minters.get(sender) or sender == self.owner, "Unauthorized"
        assert token_id in self.tokens, "Token not found"
        assert self.tokens[token_id]["is_valid"], "Already invalidated"

        self.tokens[token_id]["is_valid"] = False

    def hasValidToken(self, owner):
        for token_id in self.owner_tokens.get(owner, []):
            if self.tokens[token_id]["is_valid"]:
                return True
        return False

    def getTokenData(self, token_id):
        return self.tokens.get(token_id)

    def getTokensOfOwner(self, owner):
        return self.owner_tokens.get(owner, [])

    def transfer(self, to, token_id):
        raise AssertionError("Soulbound: transfer not allowed")

    def approve(self, spender, token_id):
        raise AssertionError("Soulbound: transfer not allowed")


# =========================
# CONSTANTS
# =========================
OWNER = "0xOwner"
USER_A = "0xUserA"
USER_B = "0xUserB"


# =========================
# UNIT TESTS
# =========================

def test_mint_success():
    sb = MockSoulbound(OWNER)

    token_id = sb.mint(OWNER, USER_A, "ipfs://QmMeta")

    assert token_id == 1
    assert sb.hasValidToken(USER_A) is True


def test_mint_multiple_tokens():
    sb = MockSoulbound(OWNER)

    t1 = sb.mint(OWNER, USER_A, "ipfs://1")
    t2 = sb.mint(OWNER, USER_A, "ipfs://2")

    tokens = sb.getTokensOfOwner(USER_A)

    assert len(tokens) == 2
    assert t1 in tokens and t2 in tokens
    assert sb.hasValidToken(USER_A) is True


def test_invalidate_token():
    sb = MockSoulbound(OWNER)

    token_id = sb.mint(OWNER, USER_A, "ipfs://meta")

    assert sb.hasValidToken(USER_A) is True

    sb.invalidateToken(OWNER, token_id)

    assert sb.hasValidToken(USER_A) is False


def test_has_valid_token_no_token():
    sb = MockSoulbound(OWNER)

    assert sb.hasValidToken("0xUnknown") is False


def test_transfer_blocked():
    sb = MockSoulbound(OWNER)

    with pytest.raises(AssertionError, match="transfer not allowed"):
        sb.transfer(USER_B, 1)


def test_approve_blocked():
    sb = MockSoulbound(OWNER)

    with pytest.raises(AssertionError, match="transfer not allowed"):
        sb.approve(USER_B, 1)


# =========================
# PROPERTY-BASED TESTS
# =========================

@given(
    metadata_uri=st.text(min_size=1, max_size=128),
    recipient=st.text(min_size=5, max_size=42),
)
@settings(max_examples=100)
def test_property_mint_valid_token(metadata_uri, recipient):
    sb = MockSoulbound(OWNER)

    token_id = sb.mint(OWNER, recipient, metadata_uri)

    assert sb.hasValidToken(recipient) is True
    assert sb.getTokenData(token_id)["metadata_uri"] == metadata_uri


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


@given(metadata_uri=st.text(min_size=1, max_size=128))
@settings(max_examples=100)
def test_property_invalidate_makes_token_invalid(metadata_uri):
    sb = MockSoulbound(OWNER)

    token_id = sb.mint(OWNER, USER_A, metadata_uri)

    assert sb.hasValidToken(USER_A) is True

    sb.invalidateToken(OWNER, token_id)

    assert sb.hasValidToken(USER_A) is False