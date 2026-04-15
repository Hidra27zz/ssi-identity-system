"""
Dich vu ma hoa RSA + AES hybrid encryption.
Nguoi phu trach: Thuy
"""
import hashlib
import os
import struct

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_rsa_keypair() -> tuple[str, str]:
    """
    Tao cap khoa RSA 2048-bit.
    Tra ve (public_key_pem, private_key_pem) dang chuoi.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return public_pem, private_pem


def encrypt_file(file_bytes: bytes, public_key_pem: str) -> bytes:
    """
    Ma hoa file bang hybrid encryption: AES-256-GCM + RSA-OAEP.
    Format: [enc_key_len 4 bytes][enc_key][iv 12 bytes][enc_file]
    """
    public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))

    # Tao AES session key ngau nhien
    session_key = os.urandom(32)  # AES-256
    iv = os.urandom(12)           # GCM nonce

    # Ma hoa file bang AES-256-GCM
    aesgcm = AESGCM(session_key)
    encrypted_file = aesgcm.encrypt(iv, file_bytes, None)

    # Ma hoa session key bang RSA-OAEP
    encrypted_session_key = public_key.encrypt(
        session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    # Ghep: [enc_key_len][enc_key][iv][enc_file]
    enc_key_len = struct.pack(">I", len(encrypted_session_key))
    return enc_key_len + encrypted_session_key + iv + encrypted_file


def decrypt_file(encrypted_bytes: bytes, private_key_pem: str) -> bytes:
    """
    Giai ma file da ma hoa bang hybrid encryption.
    Raise ValueError neu private key khong khop.
    """
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"), password=None
    )

    # Tach cac phan
    enc_key_len = struct.unpack(">I", encrypted_bytes[:4])[0]
    offset = 4
    encrypted_session_key = encrypted_bytes[offset:offset + enc_key_len]
    offset += enc_key_len
    iv = encrypted_bytes[offset:offset + 12]
    offset += 12
    encrypted_file = encrypted_bytes[offset:]

    # Giai ma session key bang RSA
    try:
        session_key = private_key.decrypt(
            encrypted_session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except Exception:
        raise ValueError("Authentication failed: invalid private key")

    # Giai ma file bang AES-256-GCM
    aesgcm = AESGCM(session_key)
    try:
        return aesgcm.decrypt(iv, encrypted_file, None)
    except Exception:
        raise ValueError("Authentication failed: invalid private key")


def hash_document(file_bytes: bytes) -> str:
    """Tinh SHA-256 hash cua file, tra ve hex string."""
    return hashlib.sha256(file_bytes).hexdigest()
