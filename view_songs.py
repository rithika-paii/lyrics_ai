import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "songs.db")

SOURCE_LABELS = {
    "lrclib_search": "lrclib~",
    "lrclib":        "lrclib",
    "genius":        "genius",
    "whisper":       "whisper",
    None:            "-",
}

def view_all():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, artist, lyrics_status, lyrics_source, transcription_status
        FROM tracks ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No tracks in database yet.")
        return

    print(f"\n{'ID':<4} {'Title':<32} {'Artist':<22} {'Status':<10} {'Source':<9} {'Transcription'}")
    print("-" * 95)
    for row in rows:
        id_, title, artist, l_status, source, t_status = row
        src = SOURCE_LABELS.get(source, source or "-")
        print(f"{id_:<4} {(title or '')[:31]:<32} {(artist or '')[:21]:<22} "
              f"{(l_status or ''):<10} {src:<9} {t_status or ''}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT lyrics_status, COUNT(*) FROM tracks GROUP BY lyrics_status")
    stats = cursor.fetchall()
    conn.close()

    print(f"\nTotal: {len(rows)} tracks")
    for status, count in stats:
        print(f"  {status}: {count}")

def view_lyrics(track_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, artist, lyrics_status, lyrics_source, lyrics_text
        FROM tracks WHERE id = ?
    """, (track_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"No track with id {track_id}")
        return

    title, artist, status, source, lyrics = row
    src = SOURCE_LABELS.get(source, source or "none")
    print(f"\n{title} — {artist}")
    print(f"Status: {status}  |  Source: {src}")
    print("=" * 50)
    print(lyrics if lyrics else "(no lyrics saved yet)")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        view_lyrics(int(sys.argv[1]))
    else:
        view_all()