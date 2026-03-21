"""
lyrics_fetcher.py — Try multiple sources in order:
  1. lrclib.net (free, crowd-sourced, synced lyrics)
  2. lrclib.net search (fuzzy — handles transliteration variants)
  3. Genius

Returns ("found", source, lyrics_text) or ("missing", None, None)
"""

import os
import re
import requests
import lyricsgenius
from dotenv import load_dotenv

load_dotenv()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_timestamps(synced):
    """Convert LRC synced lyrics to plain text."""
    plain = re.sub(r"\[\d+:\d+\.\d+\]", "", synced).strip()
    return "\n".join(line.strip() for line in plain.splitlines() if line.strip())

def _clean_title(title):
    """Strip feat., version, remaster etc. for broader matching."""
    title = re.sub(r"\(feat\..*?\)", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\(with.*?\)", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\(.*?version.*?\)", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\(.*?remaster.*?\)", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*-\s*(Telugu|Tamil|Kannada|Hindi|Malayalam)\s*$", "", title, flags=re.IGNORECASE)
    return title.strip()

# ── lrclib.net exact match ────────────────────────────────────────────────────

def fetch_lrclib_lyrics(title, artist, album=None):
    """Exact match query on lrclib.net."""
    try:
        # Try 1: full title + artist + album
        params = {"track_name": title, "artist_name": artist}
        if album:
            params["album_name"] = album

        resp = requests.get(
            "https://lrclib.net/api/get",
            params=params,
            timeout=10,
            headers={"User-Agent": "KannadaLyricsDB/1.0"}
        )
        result = _parse_lrclib_response(resp)
        if result:
            return result

        # Try 2: clean title (strip feat/version) + artist, no album
        clean = _clean_title(title)
        if clean != title:
            params2 = {"track_name": clean, "artist_name": artist}
            resp2 = requests.get(
                "https://lrclib.net/api/get",
                params=params2,
                timeout=10,
                headers={"User-Agent": "KannadaLyricsDB/1.0"}
            )
            result = _parse_lrclib_response(resp2)
            if result:
                return result

        return None
    except Exception as e:
        print(f"    lrclib error: {e}")
        return None

def _parse_lrclib_response(resp):
    if resp.status_code not in (200,):
        return None
    data = resp.json()
    plain = data.get("plainLyrics", "").strip()
    if plain:
        return plain
    synced = data.get("syncedLyrics", "").strip()
    if synced:
        return _strip_timestamps(synced)
    return None

# ── lrclib.net fuzzy search ───────────────────────────────────────────────────

def fetch_lrclib_search(title, artist):
    """
    Uses lrclib search endpoint — more forgiving with transliteration variants.
    Returns lyrics of the best matching result or None.
    """
    try:
        # Try with artist name
        queries = [
            f"{title} {artist}",
            _clean_title(title),
        ]
        for q in queries:
            resp = requests.get(
                "https://lrclib.net/api/search",
                params={"q": q},
                timeout=10,
                headers={"User-Agent": "KannadaLyricsDB/1.0"}
            )
            if resp.status_code != 200:
                continue

            results = resp.json()
            if not results:
                continue

            # Pick best match — prefer results where artist name appears
            for r in results[:5]:
                r_artist = r.get("artistName", "").lower()
                r_title = r.get("trackName", "").lower()
                title_lower = title.lower()
                artist_lower = artist.lower()

                # Loose match: either title or artist partially matches
                title_match = any(w in r_title for w in title_lower.split() if len(w) > 3)
                artist_match = any(w in r_artist for w in artist_lower.split() if len(w) > 3)

                if title_match or artist_match:
                    # Fetch full lyrics for this track
                    lyrics = fetch_lrclib_lyrics(r["trackName"], r["artistName"])
                    if lyrics:
                        return lyrics

        return None
    except Exception as e:
        print(f"    lrclib search error: {e}")
        return None

# ── Genius ────────────────────────────────────────────────────────────────────

_genius = None

def _get_genius():
    global _genius
    if _genius is None:
        token = os.getenv("GENIUS_ACCESS_TOKEN")
        if not token:
            return None
        _genius = lyricsgenius.Genius(
            token,
            timeout=10,
            retries=2,
            verbose=False,
            remove_section_headers=True,
        )
    return _genius

def fetch_genius_lyrics(title, artist):
    """Try Genius with full title, then cleaned title."""
    try:
        genius = _get_genius()
        if not genius:
            return None

        # Try 1: full title
        song = genius.search_song(title, artist)
        if song and song.lyrics:
            return song.lyrics.strip()

        # Try 2: cleaned title
        clean = _clean_title(title)
        if clean != title:
            song = genius.search_song(clean, artist)
            if song and song.lyrics:
                return song.lyrics.strip()

        return None
    except Exception as e:
        print(f"    Genius error: {e}")
        return None

# ── Main entrypoint ───────────────────────────────────────────────────────────

def check_lyrics(spotify_id, title, artist, album=None):
    """
    Try all sources in order. Returns (status, source, lyrics_text).
    status is 'found' or 'missing'.
    source is 'lrclib' | 'lrclib_search' | 'genius' | None
    """

    # 1. lrclib exact
    print(f"    Trying lrclib...", end=" ", flush=True)
    lyrics = fetch_lrclib_lyrics(title, artist, album)
    if lyrics:
        print("✓ found")
        return "found", "lrclib", lyrics
    print("✗")

    # 2. lrclib fuzzy search
    print(f"    Trying lrclib search...", end=" ", flush=True)
    lyrics = fetch_lrclib_search(title, artist)
    if lyrics:
        print("✓ found")
        return "found", "lrclib_search", lyrics
    print("✗")

    # 3. Genius
    print(f"    Trying Genius...", end=" ", flush=True)
    lyrics = fetch_genius_lyrics(title, artist)
    if lyrics:
        print("✓ found")
        return "found", "genius", lyrics
    print("✗")

    return "missing", None, None