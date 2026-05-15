import sqlite3
conn = sqlite3.connect("backend/ssi.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT created_at, last_synced_at FROM did_cache WHERE wallet_address='0xab63fe861ed1ff0bab5c3044a4957a08d8345b60'").fetchall()
for r in rows:
    print(dict(r))
