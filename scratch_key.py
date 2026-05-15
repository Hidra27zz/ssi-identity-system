import sqlite3
conn = sqlite3.connect("backend/ssi.db")
row = conn.execute("SELECT public_key_pem FROM did_cache WHERE wallet_address='0xab63fe861ed1ff0bab5c3044a4957a08d8345b60'").fetchone()
if row:
    print(row[0])
