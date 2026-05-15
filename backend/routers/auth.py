"""
Router xac thuc bang address + password (khong can MetaMask).
Nguoi phu trach: Thuy

Endpoints:
  POST /api/auth/register  — Dang ky mat khau cho dia chi vi
  POST /api/auth/login     — Dang nhap → tra ve session token
  POST /api/auth/logout    — Xoa session
  GET  /api/auth/session   — Kiem tra session con hieu luc khong
"""
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.database import get_connection

router = APIRouter()

SESSION_TTL_HOURS = 8  # Token het han sau 8 gio


# ============================================================
# Schemas
# ============================================================

class RegisterRequest(BaseModel):
    wallet_address: str
    password: str       # plain text — backend se hash


class LoginRequest(BaseModel):
    wallet_address: str
    password: str


class AuthResponse(BaseModel):
    wallet_address: str
    session_token: str
    expires_at: str
    message: str


# ============================================================
# Helpers
# ============================================================

def _hash_password(password: str, salt: str = "") -> str:
    """SHA-256 + salt don gian (khong dung bcrypt de tranh dependency)."""
    if not salt:
        salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${digest}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == digest
    except Exception:
        return False


def _ensure_auth_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_accounts (
            wallet_address  TEXT PRIMARY KEY,
            password_hash   TEXT NOT NULL,
            created_at      TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token           TEXT PRIMARY KEY,
            wallet_address  TEXT NOT NULL,
            expires_at      TEXT NOT NULL,
            created_at      TEXT NOT NULL
        )
    """)
    conn.commit()


# ============================================================
# Endpoints
# ============================================================

@router.post("/register", response_model=AuthResponse)
def register(body: RegisterRequest):
    """
    Dang ky mat khau cho dia chi vi.
    Dia chi phai da co DID trong did_cache (da tao DID truoc).
    """
    addr = body.wallet_address.lower().strip()
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Mat khau phai co it nhat 6 ky tu.")

    conn = get_connection()
    try:
        _ensure_auth_tables(conn)

        # Kiem tra dia chi da ton tai chua
        existing = conn.execute(
            "SELECT wallet_address FROM user_accounts WHERE wallet_address=?", (addr,)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Dia chi nay da dang ky mat khau roi.")

        # Luu mat khau
        now = datetime.now(timezone.utc).isoformat()
        hashed = _hash_password(body.password)
        conn.execute(
            "INSERT INTO user_accounts (wallet_address, password_hash, created_at) VALUES (?,?,?)",
            (addr, hashed, now),
        )

        # Tao session ngay sau khi dang ky
        token = secrets.token_urlsafe(32)
        expires = (datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS)).isoformat()
        conn.execute(
            "INSERT INTO sessions (token, wallet_address, expires_at, created_at) VALUES (?,?,?,?)",
            (token, addr, expires, now),
        )
        conn.commit()
    finally:
        conn.close()

    return AuthResponse(
        wallet_address=addr,
        session_token=token,
        expires_at=expires,
        message="Dang ky thanh cong.",
    )


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest):
    """Dang nhap bang dia chi vi + mat khau."""
    addr = body.wallet_address.lower().strip()

    conn = get_connection()
    try:
        _ensure_auth_tables(conn)

        row = conn.execute(
            "SELECT password_hash FROM user_accounts WHERE wallet_address=?", (addr,)
        ).fetchone()

        if not row:
            raise HTTPException(
                status_code=401,
                detail="Dia chi nay chua dang ky mat khau. Vui long dang ky hoac dung MetaMask."
            )

        if not _verify_password(body.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Mat khau khong dung.")

        # Xoa session cu (neu co)
        conn.execute("DELETE FROM sessions WHERE wallet_address=?", (addr,))

        # Tao session moi
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc).isoformat()
        expires = (datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS)).isoformat()
        conn.execute(
            "INSERT INTO sessions (token, wallet_address, expires_at, created_at) VALUES (?,?,?,?)",
            (token, addr, expires, now),
        )
        conn.commit()
    finally:
        conn.close()

    return AuthResponse(
        wallet_address=addr,
        session_token=token,
        expires_at=expires,
        message="Dang nhap thanh cong.",
    )


@router.post("/logout")
def logout(token: str):
    """Xoa session (dang xuat)."""
    conn = get_connection()
    try:
        _ensure_auth_tables(conn)
        conn.execute("DELETE FROM sessions WHERE token=?", (token,))
        conn.commit()
    finally:
        conn.close()
    return {"message": "Da dang xuat."}


@router.get("/session")
def check_session(token: str):
    """Kiem tra session token con hieu luc khong. Dung de auth-guard validate."""
    conn = get_connection()
    try:
        _ensure_auth_tables(conn)
        row = conn.execute(
            "SELECT wallet_address, expires_at FROM sessions WHERE token=?", (token,)
        ).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Session khong hop le.")

    expires = datetime.fromisoformat(row["expires_at"])
    if datetime.now(timezone.utc) > expires:
        raise HTTPException(status_code=401, detail="Session da het han.")

    return {
        "valid": True,
        "wallet_address": row["wallet_address"],
        "expires_at": row["expires_at"],
    }
