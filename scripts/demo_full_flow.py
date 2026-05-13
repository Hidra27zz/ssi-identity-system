"""
Script demo toàn bộ luồng hệ thống SSI.
Chạy: python scripts/demo_full_flow.py

Yêu cầu:
- Backend đang chạy tại http://localhost:8000
- File ảnh: scripts/demo_portrait.jpg
- File PDF : scripts/demo_document.pdf
"""

import asyncio
import os
import sys
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import httpx
from web3 import Web3

# Thêm root vào path để import backend modules
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

os.environ["IPFS_API_KEY"]    = "289c4a512c80d0823169"
os.environ["IPFS_SECRET_KEY"] = "4d6aa764fe7bd905196995a36641459cec8f6508155ff36f62dd98fa9e182267"

from backend.services.crypto_service import (
    generate_rsa_keypair, encrypt_file, hash_document
)
from backend.services.ipfs_service import (
    upload_to_ipfs, upload_json_to_ipfs, retrieve_from_ipfs
)

BASE     = "http://localhost:8000"
DB_PATH  = str(ROOT / "backend" / "ssi.db")
PORTRAIT = str(ROOT / "scripts" / "demo_portrait.jpg")
PDF_FILE = str(ROOT / "scripts" / "demo_document.pdf")


def sep(title=""):
    print()
    print("=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def ok(msg):  print(f"  [OK] {msg}")
def info(msg): print(f"       {msg}")
def err(msg): print(f"  [LOI] {msg}")


async def main():
    # ── Tạo 3 account mới ────────────────────────────────────
    sep("KHỞI TẠO — TẠO 3 TÀI KHOẢN MỚI")
    w3 = Web3()
    user     = w3.eth.account.create()
    creator  = w3.eth.account.create()
    verifier = w3.eth.account.create()

    USER_ADDR     = user.address
    CREATOR_ADDR  = creator.address
    VERIFIER_ADDR = verifier.address
    USER_DID      = f"did:ssi:{USER_ADDR.lower()}"
    now           = datetime.now(timezone.utc).isoformat()

    info(f"User    (Sinh viên) : {USER_ADDR}")
    info(f"Creator (Trường ĐH) : {CREATOR_ADDR}")
    info(f"Verifier (Công ty)  : {VERIFIER_ADDR}")

    # ── Bước 1: User tạo keypair RSA ─────────────────────────
    sep("BƯỚC 1 — USER TẠO CẶP KHÓA RSA")
    info(f"Input: wallet_address = {USER_ADDR}")

    r = httpx.post(f"{BASE}/api/crypto/generate-keypair",
                   json={"wallet_address": USER_ADDR}, timeout=30)

    if r.status_code != 200:
        err(f"Lỗi: {r.text[:200]}")
        return

    pub_key  = r.json()["public_key"]
    priv_key = r.json()["private_key"]
    ok("Keypair RSA 2048-bit đã tạo")
    info(f"Public key  : {pub_key[27:67]}...")
    info(f"Private key : {priv_key[28:68]}...")
    info("Public key đã lưu vào DB, private key chỉ hiển thị 1 lần")

    # Lưu private key ra file để dùng sau
    pk_file = ROOT / "scripts" / "demo_private_key.pem"
    pk_file.write_text(priv_key)
    ok(f"Private key đã lưu: {pk_file}")

    # ── Bước 2: User tạo DID ─────────────────────────────────
    sep("BƯỚC 2 — USER TẠO DID TRÊN BLOCKCHAIN")
    info(f"Input: wallet_address = {USER_ADDR}")
    info(f"Input: did            = {USER_DID}")
    info("(Seed vào DB vì chưa có ETH Sepolia để gửi transaction)")

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO did_cache "
        "(wallet_address, did, status, public_key_pem, last_synced_at, created_at) "
        "VALUES (?,?,?,?,?,?)",
        (USER_ADDR, USER_DID, "pending", pub_key, now, now)
    )
    conn.commit()
    conn.close()

    ok(f"DID đã tạo: {USER_DID}")
    info("Trạng thái: PENDING (chờ Creator xác minh)")

    # ── Bước 3: Creator upload 3 loại file lên IPFS ──────────
    sep("BƯỚC 3 — CREATOR UPLOAD 3 LOẠI FILE LÊN IPFS")

    # 3a. Ảnh chân dung
    info(f"Input file ảnh: {PORTRAIT}")
    if not Path(PORTRAIT).exists():
        err(f"Không tìm thấy file: {PORTRAIT}")
        return

    portrait_bytes = Path(PORTRAIT).read_bytes()
    info(f"Kích thước ảnh: {len(portrait_bytes):,} bytes")
    info("Đang mã hóa bằng RSA-OAEP + AES-256-GCM...")
    portrait_enc  = encrypt_file(portrait_bytes, pub_key)
    portrait_hash = hash_document(portrait_bytes)
    info("Đang upload lên IPFS (Pinata)...")
    portrait_cid  = await upload_to_ipfs(portrait_enc, "portrait.jpg")
    ok(f"Ảnh chân dung đã upload")
    info(f"SHA-256 hash : {portrait_hash}")
    info(f"IPFS CID     : {portrait_cid}")
    info(f"Gateway URL  : https://gateway.pinata.cloud/ipfs/{portrait_cid}")

    # 3b. File PDF
    info(f"\nInput file PDF: {PDF_FILE}")
    if not Path(PDF_FILE).exists():
        err(f"Không tìm thấy file: {PDF_FILE}")
        return

    pdf_bytes = Path(PDF_FILE).read_bytes()
    info(f"Kích thước PDF: {len(pdf_bytes):,} bytes")
    info("Đang mã hóa và upload...")
    pdf_enc  = encrypt_file(pdf_bytes, pub_key)
    pdf_hash = hash_document(pdf_bytes)
    pdf_cid  = await upload_to_ipfs(pdf_enc, "document.pdf")
    ok(f"File PDF đã upload")
    info(f"SHA-256 hash : {pdf_hash}")
    info(f"IPFS CID     : {pdf_cid}")
    info(f"Gateway URL  : https://gateway.pinata.cloud/ipfs/{pdf_cid}")

    # 3c. Metadata JSON
    info("\nTạo Metadata JSON từ 2 CID trên...")
    metadata = {
        "did":         USER_DID,
        "documentType": "BangTotNghiep",
        "issuedBy":    "Truong Dai Hoc Cong Nghe Thong Tin",
        "portraitCID": portrait_cid,
        "documentCID": pdf_cid,
        "createdAt":   now,
    }
    meta_cid = await upload_json_to_ipfs(metadata)
    ok("Metadata JSON đã upload")
    info(f"IPFS CID     : {meta_cid}")
    info(f"Gateway URL  : https://gateway.pinata.cloud/ipfs/{meta_cid}")
    info(f"Nội dung     : {metadata}")

    # ── Bước 4: Creator gửi hash lên blockchain ──────────────
    sep("BƯỚC 4 — CREATOR XÁC MINH (SEED VERIFIED VÀO DB)")
    info(f"Input: wallet_address   = {USER_ADDR}")
    info(f"Input: doc_hash         = {pdf_hash}")
    info(f"Input: cid              = {pdf_cid}")
    info(f"Input: creator_address  = {CREATOR_ADDR}")
    info("(Trên Sepolia thực: cần ETH để gửi transaction)")

    conn2 = sqlite3.connect(DB_PATH)
    conn2.execute(
        "UPDATE did_cache SET status=?, ipfs_cid=?, last_synced_at=? WHERE wallet_address=?",
        ("verified", pdf_cid, now, USER_ADDR)
    )
    conn2.execute(
        "INSERT INTO pending_verifications "
        "(wallet_address, did, doc_hash, ipfs_cid, creator_address, status, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (USER_ADDR, USER_DID, pdf_hash, pdf_cid, CREATOR_ADDR, "confirmed", now, now)
    )
    conn2.commit()
    conn2.close()

    ok("Hash đã lưu, DID chuyển PENDING → VERIFIED")
    info("Trên Sepolia thực: TX hash sẽ xuất hiện trên Etherscan")

    # ── Bước 5: Verifier xác minh DID ────────────────────────
    sep("BƯỚC 5 — VERIFIER XÁC MINH DID")
    info(f"Input: address = {USER_ADDR}")

    r2 = httpx.get(f"{BASE}/api/did/verify/{USER_ADDR}", timeout=20)
    d2 = r2.json()
    status = d2.get("status", "").upper()
    ok(f"Kết quả xác minh: {status}")
    info(f"DID    : {d2.get('did')}")
    info(f"CID    : {d2.get('cid')}")
    info(f"is_valid: {d2.get('is_valid')}")

    # Xác minh địa chỉ có DID VERIFIED thực trên Sepolia
    info("\nXác minh địa chỉ có DID VERIFIED thực trên Sepolia:")
    REAL_ADDR = "0x32268B487ebaB849d8f40B1a12776a543fdFb79a"
    info(f"Input: address = {REAL_ADDR}")
    r2b = httpx.get(f"{BASE}/api/did/verify/{REAL_ADDR}", timeout=20)
    d2b = r2b.json()
    ok(f"Kết quả: {d2b.get('status','').upper()}")
    info(f"DID    : {d2b.get('did')}")

    # ── Bước 6: Verifier xin consent ─────────────────────────
    sep("BƯỚC 6 — VERIFIER GỬI YÊU CẦU CONSENT")
    info(f"Input: owner_did          = {USER_DID}")
    info(f"Input: requester_address  = {VERIFIER_ADDR}")
    info(f"Input: data_type          = document")

    r3 = httpx.post(f"{BASE}/api/consent/request", json={
        "owner_did":          USER_DID,
        "requester_address":  VERIFIER_ADDR,
        "data_type":          "document",
    }, timeout=15)
    consent_id = r3.json().get("consent_id")
    ok(f"Yêu cầu đã gửi — Consent ID: {consent_id}")
    info("Trạng thái: pending — chờ User phê duyệt")

    # ── Bước 7: User phê duyệt consent ───────────────────────
    sep("BƯỚC 7 — USER PHÊ DUYỆT CONSENT")
    info(f"Input: consent_id = {consent_id}")
    info(f"Input: owner_did  = {USER_DID}")
    info(f"Input: decision   = approved")

    r4 = httpx.post(f"{BASE}/api/consent/respond", json={
        "consent_id": consent_id,
        "owner_did":  USER_DID,
        "decision":   "approved",
    }, timeout=15)
    ok(f"Kết quả: {r4.json().get('status')}")
    info("Verifier có 24 giờ để truy cập file")

    # ── Bước 8: Verifier tải và giải mã file ─────────────────
    sep("BƯỚC 8 — VERIFIER TẢI VÀ GIẢI MÃ FILE TỪ IPFS")
    info(f"Input: cid               = {pdf_cid}")
    info(f"Input: owner_did         = {USER_DID}")
    info(f"Input: requester_address = {VERIFIER_ADDR}")
    info(f"Input: private_key       = (đọc từ file)")

    # Đọc private key từ file đã lưu
    saved_priv_key = pk_file.read_text()

    # Tải file từ IPFS
    info("Đang tải file từ IPFS...")
    encrypted_bytes = await retrieve_from_ipfs(pdf_cid)
    info(f"Đã tải {len(encrypted_bytes):,} bytes (đã mã hóa)")

    # Giải mã
    from backend.services.crypto_service import decrypt_file
    info("Đang giải mã bằng private key...")
    decrypted = decrypt_file(encrypted_bytes, saved_priv_key)
    ok(f"Giải mã thành công — {len(decrypted):,} bytes")
    info(f"Nội dung (50 bytes đầu): {decrypted[:50]}")

    # Lưu file đã giải mã
    out_file = ROOT / "scripts" / "demo_retrieved_document.pdf"
    out_file.write_bytes(decrypted)
    ok(f"File đã lưu: {out_file}")

    # ── Bước 9: Kiểm tra NFT token-gated ─────────────────────
    sep("BƯỚC 9 — KIỂM TRA SOULBOUND NFT (TOKEN-GATED ACCESS)")
    info(f"Input: address = {USER_ADDR}")

    r5 = httpx.get(f"{BASE}/api/nft/verify-access/{USER_ADDR}", timeout=20)
    d5 = r5.json()
    ok(f"Có quyền truy cập: {d5.get('has_access')}")
    info(f"Lý do: {d5.get('reason')}")

    # Kiểm tra địa chỉ có NFT thực
    info(f"\nKiểm tra địa chỉ có NFT thực: {REAL_ADDR}")
    r5b = httpx.get(f"{BASE}/api/nft/verify-access/{REAL_ADDR}", timeout=20)
    d5b = r5b.json()
    ok(f"Có quyền: {d5b.get('has_access')} — {d5b.get('reason')}")

    # ── Tổng kết ─────────────────────────────────────────────
    sep("TỔNG KẾT — LƯU LẠI ĐỂ DEMO")
    print(f"""
  User address  : {USER_ADDR}
  User DID      : {USER_DID}
  Creator       : {CREATOR_ADDR}
  Verifier      : {VERIFIER_ADDR}

  Ảnh CID       : {portrait_cid}
  PDF CID       : {pdf_cid}
  Metadata CID  : {meta_cid}
  Doc Hash      : {pdf_hash}
  Consent ID    : {consent_id} (approved)

  File đã lưu:
    Private key : scripts/demo_private_key.pem
    File giải mã: scripts/demo_retrieved_document.pdf

  Demo trên frontend:
    Trang Verifier -> nhập: {USER_ADDR}
    Trang User DID -> nhập: {USER_DID}
    Địa chỉ VERIFIED thực: 0x32268B487ebaB849d8f40B1a12776a543fdFb79a
""")


if __name__ == "__main__":
    # Kiểm tra backend đang chạy
    try:
        r = httpx.get(f"{BASE}/health", timeout=5)
        if r.status_code != 200:
            print("Backend chưa chạy. Chạy: uvicorn backend.main:app --reload --port 8000")
            sys.exit(1)
    except Exception:
        print("Backend chưa chạy. Chạy: uvicorn backend.main:app --reload --port 8000")
        sys.exit(1)

    # Kiểm tra file ảnh và PDF
    for f in [PORTRAIT, PDF_FILE]:
        if not Path(f).exists():
            print(f"Thiếu file: {f}")
            print("Chạy trước: python scripts/demo_full_flow.py --create-samples")
            sys.exit(1)

    asyncio.run(main())
