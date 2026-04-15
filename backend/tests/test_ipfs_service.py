"""
Tests cho ipfs_service.py
Nguoi phu trach: Thuy

Chay: pytest backend/tests/test_ipfs_service.py
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from unittest.mock import AsyncMock, patch

from backend.services.ipfs_service import (
    IPFSUnavailableError,
    build_metadata_json,
    upload_to_ipfs,
)


# --- Unit tests ---

def test_build_metadata_json_has_required_fields():
    result = build_metadata_json(
        did="did:ssi:test",
        doc_type="CCCD",
        issued_by="Bo Cong An",
        portrait_cid="QmPortrait",
        document_cid="QmDocument",
    )
    required = {"did", "documentType", "issuedBy", "portraitCID", "documentCID", "createdAt"}
    assert required.issubset(result.keys())
    for key in required:
        assert result[key] is not None
        assert result[key] != ""


def test_build_metadata_json_no_pii():
    result = build_metadata_json("did:ssi:x", "CCCD", "issuer", "cid1", "cid2")
    # Khong co truong PII plaintext
    pii_fields = {"name", "phone", "address", "dob", "id_number"}
    assert not pii_fields.intersection(result.keys())


@pytest.mark.asyncio
async def test_upload_to_ipfs_retry_3_times():
    call_count = 0

    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise Exception("Connection refused")

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        with pytest.raises(IPFSUnavailableError):
            await upload_to_ipfs(b"test data", "test.bin")

    assert call_count == 3


# --- Property-based tests ---

# Feature: decentralized-identity-ssi, Property 9: Metadata JSON Co Du Truong Bat Buoc
@given(
    did=st.text(min_size=1, max_size=64),
    doc_type=st.text(min_size=1, max_size=32),
    issued_by=st.text(min_size=1, max_size=64),
    portrait_cid=st.text(min_size=1, max_size=64),
    document_cid=st.text(min_size=1, max_size=64),
)
@settings(max_examples=100)
def test_property_metadata_has_all_fields(did, doc_type, issued_by, portrait_cid, document_cid):
    result = build_metadata_json(did, doc_type, issued_by, portrait_cid, document_cid)
    required = {"did", "documentType", "issuedBy", "portraitCID", "documentCID", "createdAt"}
    assert required.issubset(result.keys())
    for key in required:
        assert result[key] is not None


# Feature: decentralized-identity-ssi, Property 12: IPFS Retry Toi Da 3 Lan
@pytest.mark.asyncio
async def test_property_ipfs_retry_exactly_3():
    """IPFS phai thu lai dung 3 lan truoc khi raise exception."""
    call_count = 0

    async def always_fail(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise Exception("IPFS down")

    with patch("httpx.AsyncClient.post", side_effect=always_fail):
        with pytest.raises(IPFSUnavailableError):
            await upload_to_ipfs(b"data", "file.bin")

    assert call_count == 3, f"Expected 3 retries, got {call_count}"
