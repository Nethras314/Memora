import sqlite3

c = sqlite3.connect("memora.db")

cols = [r[1] for r in c.execute("PRAGMA table_info(memories)")]

if "patient_id" not in cols:
    c.execute("ALTER TABLE memories ADD COLUMN patient_id INTEGER")

c.execute("UPDATE memories SET patient_id = 1 WHERE patient_id IS NULL")

c.commit()

print(c.execute("PRAGMA table_info(memories)").fetchall())
print(c.execute("SELECT id, category, title, details, patient_id FROM memories").fetchall())
c.close()