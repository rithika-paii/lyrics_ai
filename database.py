import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "songs.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tracks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spotify_id TEXT UNIQUE,
        title TEXT,
        artist TEXT,
        album TEXT,
        release_date TEXT,
        language TEXT DEFAULT 'kn',
        lyrics_status TEXT DEFAULT 'unchecked',
        lyrics_source TEXT,
        lyrics_text TEXT,
        audio_path TEXT,
        vocals_path TEXT,
        transcription_status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Migrate existing DB
    existing_cols = {row[1] for row in cursor.execute("PRAGMA table_info(tracks)")}
    new_cols = {
        "language":             "TEXT DEFAULT 'kn'",
        "lyrics_source":        "TEXT",
        "lyrics_text":          "TEXT",
        "audio_path":           "TEXT",
        "vocals_path":          "TEXT",
        "transcription_status": "TEXT",
        "created_at":           "DATETIME",
        "updated_at":           "DATETIME",
    }
    for col, col_type in new_cols.items():
        if col not in existing_cols:
            cursor.execute(f"ALTER TABLE tracks ADD COLUMN {col} {col_type}")
            print(f"  Migrated: added column '{col}'")

    conn.commit()
    conn.close()
    print("Database ready.")

def save_track(spotify_id, title, artist, album, release_date, language="kn"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO tracks (spotify_id, title, artist, album, release_date, language)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (spotify_id, title, artist, album, release_date, language))
    conn.commit()
    conn.close()

def update_lyrics(spotify_id, lyrics_status, lyrics_source, lyrics_text):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tracks
        SET lyrics_status = ?, lyrics_source = ?, lyrics_text = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE spotify_id = ?
    """, (lyrics_status, lyrics_source, lyrics_text, spotify_id))
    conn.commit()
    conn.close()

def update_audio_path(spotify_id, audio_path):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tracks SET audio_path = ?, updated_at = CURRENT_TIMESTAMP
        WHERE spotify_id = ?
    """, (audio_path, spotify_id))
    conn.commit()
    conn.close()

def update_vocals_path(spotify_id, vocals_path):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tracks SET vocals_path = ?, updated_at = CURRENT_TIMESTAMP
        WHERE spotify_id = ?
    """, (vocals_path, spotify_id))
    conn.commit()
    conn.close()

def update_transcription(spotify_id, lyrics_text):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tracks
        SET lyrics_text = ?, lyrics_source = 'whisper',
            transcription_status = 'done', lyrics_status = 'transcribed',
            updated_at = CURRENT_TIMESTAMP
        WHERE spotify_id = ?
    """, (lyrics_text, spotify_id))
    conn.commit()
    conn.close()

def get_tracks_missing_lyrics():
    """Returns (spotify_id, title, artist, language) for all missing tracks."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT spotify_id, title, artist, language FROM tracks
        WHERE lyrics_status = 'missing'
        AND transcription_status = 'pending'
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def set_language(spotify_id, language):
    """Manually set language for a track."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tracks SET language = ?, updated_at = CURRENT_TIMESTAMP
        WHERE spotify_id = ?
    """, (language, spotify_id))
    conn.commit()
    conn.close()

def get_all_tracks():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, artist, album, language, lyrics_status, lyrics_source, transcription_status
        FROM tracks ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()