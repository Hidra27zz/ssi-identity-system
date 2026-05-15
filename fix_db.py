from backend.models.database import get_connection
import sqlite3

conn = get_connection()
wallet = "0xab63fe861ed1ff0bab5c3044a4957a08d8345b60"
did_str = "did:ssi:0xab63fe861ed1ff0bab5c3044a4957a08d8345b60"

conn.execute(
    "UPDATE did_cache SET did=? WHERE wallet_address=?",
    (did_str, wallet)
)
conn.commit()
conn.close()
print("Fixed DB for", wallet)
