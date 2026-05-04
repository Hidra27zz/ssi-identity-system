"""
Tests cho crypto_service.py
Nguoi phu trach: Thuy

Chay: pytest backend/tests/test_crypto_service.py
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backend.services.crypto_service import (
    decrypt_file,
    encrypt_file,
    generate_rsa_keypair,
    hash_document,
)


# --- Unit tests ---

def test_generate_keypair_returns_pem():
    pub, priv = generate_rsa_keypair()
    assert pub.startswith("-----BEGIN PUBLIC KEY-----")
    assert priv.startswith("-----BEGIN PRIVATE KEY-----")


def test_encrypt_decrypt_small_file():
    pub, priv = generate_rsa_keypair()
    data = b"Hello SSI system"
    encrypted = encrypt_file(data, pub)
    decrypted = decrypt_file(encrypted, priv)
    assert decrypted == data


def test_wrong_private_key_raises():
    pub, _ = generate_rsa_keypair()
    _, wrong_priv = generate_rsa_keypair()
    data = b"test data"
    encrypted = encrypt_file(data, pub)
    with pytest.raises(ValueError, match="Authentication failed"):
        decrypt_file(encrypted, wrong_priv)


def test_hash_document_is_hex_64_chars():
    result = hash_document(b"test content")
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_hash_document_deterministic():
    data = b"same content"
    assert hash_document(data) == hash_document(data)


def test_hash_document_different_for_different_content():
    assert hash_document(b"content A") != hash_document(b"content B")


# --- Property-based tests ---

# Feature: decentralized-identity-ssi, Property 16: RSA Keypair Generation Round-Trip
# deadline=None vi RSA key generation mat ~200-500ms, vuot deadline mac dinh cua Hypothesis
@given(data=st.binary(min_size=1, max_size=2048))
@settings(max_examples=100, deadline=None)
def test_property_encrypt_decrypt_roundtrip(data):
    pub, priv = generate_rsa_keypair()
    encrypted = encrypt_file(data, pub)
    decrypted = decrypt_file(encrypted, priv)
    assert decrypted == data


# Feature: decentralized-identity-ssi, Property 17: Sai Private Key - Decrypt That Bai
# deadline=None vi RSA key generation mat ~200-500ms, vuot deadline mac dinh cua Hypothesis
@given(data=st.binary(min_size=1, max_size=512))
@settings(max_examples=50, deadline=None)
def test_property_wrong_key_fails(data):
    pub, _ = generate_rsa_keypair()
    _, wrong_priv = generate_rsa_keypair()
    encrypted = encrypt_file(data, pub)
    with pytest.raises(ValueError):
        decrypt_file(encrypted, wrong_priv)
