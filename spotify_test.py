import os
import sqlite3
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from check_lyrics import check_lyrics

# Load environment variables
load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

# Authenticate with Spotify
sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
)

track_url = input("Paste Spotify track URL: ")

track = sp.track(track_url)

spotify_id = track["id"] # type: ignore
title = track["name"] # type: ignore
song_name = track["name"] # type: ignore
artist = track["artists"][0]["name"] # type: ignore
album = track["album"]["name"] # type: ignore
release_date = track["album"]["release_date"] # type: ignore

print("\n Song Infor")
print("--------------")
print("Title: ", song_name)
print("Artist: ", artist)
print("Album: ", album)
print("Release Date: ", release_date)

lyrics_status = check_lyrics(artist, title)

print("Lyrics status: ", lyrics_status)

conn = sqlite3.connect("songs.db")
cursor = conn.cursor()

cursor.execute("""
               INSERT OR IGNORE INTO TRACKS (spotify_id, title, artist, album, release_date, lyrics_status)
               VALUES (?, ?, ?, ?, ?, ?)
               """, (spotify_id, title, artist, album, release_date, lyrics_status))

conn.commit()
conn.close()

print("\n Song saved to database.")