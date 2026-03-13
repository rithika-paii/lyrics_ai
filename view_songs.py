import sqlite3

conn = sqlite3.connect("songs.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM tracks")

rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()