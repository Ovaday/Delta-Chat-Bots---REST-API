# This file is for debugging purposes only.
# It allows you to directly access the SQLite database used by Delta Chat.
# You can run this file to see the contents of the database and verify that your bot is correctly configured.

import sqlite3

conn = sqlite3.connect(r"accounts\*****************\dc.db") # specify there where your dc.db is located
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
cur.execute("SELECT * FROM config")
print(cur.fetchall())
