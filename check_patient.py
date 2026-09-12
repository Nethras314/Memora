import sqlite3

c = sqlite3.connect("memora.db")

print(c.execute("PRAGMA table_info(patient)").fetchall())

c.close()