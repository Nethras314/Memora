import sqlite3

c = sqlite3.connect("memora.db")

c.execute(
    "INSERT INTO patient(name,age,gender,phone,caregiver) VALUES(?,?,?,?,?)",
    ("Raman", 75, "Male", "9000000000", "Kumar")
)

c.commit()

print(c.execute("SELECT * FROM patient").fetchall())

c.close()