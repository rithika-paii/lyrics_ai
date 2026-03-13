import sqlite3

# Connect to database (creates it if it doesn't exist)
conn = sqlite3.connect("songs.db")

cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spotify_id TEXT UNIQUE,
    title TEXT,
    artist TEXT,
    album TEXT,
    release_date TEXT,
    lyrics_status TEXT
)
""")

conn.commit()
conn.close()

print("Database and table created.")