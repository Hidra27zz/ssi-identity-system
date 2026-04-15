"""
SQLite schema va helper functions.
Nguoi phu trach: Thuy
"""
import sqlite3
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("SQLITE_DB_PATH", "./backend/ssi.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS did_cache (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_address  TEXT NOT NULL UNIQUE,
            did             TEXT NOT NULL,
            ipfs_cid        TEXT,
            status          TEXT NOT NULL DEFAULT 'active',
            public_key_pem  TEXT,
            last_synced_at  TEXT NOT NULL,
            created_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pending_verifications (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_address  TEXT NOT NULL,
            did             TEXT NOT NULL,
            doc_hash        TEXT NOT NULL,
            ipfs_cid        TEXT NOT NULL,
            creator_address TEXT NOT NULL,
            tx_hash         TEXT,
            status          TEXT NOT NULL DEFAULT 'pending',
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS consent_records (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_did           TEXT NOT NULL,
            requester_address   TEXT NOT NULL,
            data_type           TEXT NOT NULL,
            status              TEXT NOT NULL DEFAULT 'pending',
            requested_at        TEXT NOT NULL,
            responded_at        TEXT,
            expires_at          TEXT
        );

        CREATE TABLE IF NOT EXISTS upload_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_did       TEXT NOT NULL,
            ipfs_cid        TEXT NOT NULL,
            file_type       TEXT NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            encrypted       INTEGER NOT NULL DEFAULT 1,
            uploaded_at     TEXT NOT NULL
        );
    """)

    conn.commit()
    conn.close()
