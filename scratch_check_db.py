import sqlite3
conn = sqlite3.connect("backend/ssi.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT * FROM upload_history WHERE ipfs_cid='QmQukhGymyMQ5uoFKdbbNnNBt76WEN7HZrjbQKKksYpGe3'").fetchall()
for r in rows:
    print(dict(r))
