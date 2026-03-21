import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from lyrics_fetcher import check_lyrics
from database import init_db, save_track, update_lyrics

load_dotenv()

# Use SpotifyOAuth (user-level) so the lyrics endpoint works
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri="http://127.0.0.1:8888/callback",
        scope="user-read-private",
        cache_path=".spotify_token_cache",
        show_dialog=True,
    )
)

def add_track(track_url):
    track = sp.track(track_url)

    spotify_id   = track["id"]
    title        = track["name"]
    artist       = track["artists"][0]["name"]
    album        = track["album"]["name"]
    release_date = track["album"]["release_date"]

    print(f"\n  Title:        {title}")
    print(f"  Artist:       {artist}")
    print(f"  Album:        {album}")
    print(f"  Release Date: {release_date}")

    save_track(spotify_id, title, artist, album, release_date)

    print(f"\n  Checking lyrics...")
    status, source, lyrics_text = check_lyrics(spotify_id, title, artist, album)
    update_lyrics(spotify_id, status, source, lyrics_text)

    if status == "found":
        print(f"  ✓ Lyrics saved (source: {source})")
    else:
        print(f"  ✗ No lyrics found — queued for Whisper transcription")

    return spotify_id

def add_playlist(playlist_url):
    playlist_url = playlist_url.split("?")[0]  # strip ?si= tracking param
    results = sp.playlist_tracks(playlist_url)
    tracks = results["items"]
    while results["next"]:
        results = sp.next(results)
        tracks.extend(results["items"])

    print(f"\nFound {len(tracks)} tracks in playlist.\n")
    for i, item in enumerate(tracks, 1):
        track = item.get("track") or item.get("item")
        if not track:
            print(f"[{i}/{len(tracks)}] Skipping — no track data")
            continue
        print(f"[{i}/{len(tracks)}] {track['name']}")
        try:
            add_track(f"https://open.spotify.com/track/{track['id']}")
        except Exception as e:
            import traceback
            print(f"  Error: {e}")
            traceback.print_exc()
            continue

if __name__ == "__main__":
    init_db()
    print("\nOptions:")
    print("  1. Add a single track")
    print("  2. Add a full playlist")
    choice = input("\nChoice (1/2): ").strip()

    if choice == "1":
        url = input("Paste Spotify track URL: ").strip()
        add_track(url)
    elif choice == "2":
        url = input("Paste Spotify playlist URL: ").strip()
        add_playlist(url)
    else:
        print("Invalid choice.")