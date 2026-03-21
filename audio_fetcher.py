import os
import subprocess
import re

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")

def get_song_dir(spotify_id):
    """Each song gets its own folder: audio/{spotify_id}/"""
    path = os.path.join(AUDIO_DIR, spotify_id)
    os.makedirs(path, exist_ok=True)
    return path

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def fetch_audio(spotify_id, title, artist):
    """
    Downloads audio from YouTube into audio/{spotify_id}/original.mp3
    Returns path to original.mp3, or None if failed.
    """
    song_dir = get_song_dir(spotify_id)
    final_path = os.path.join(song_dir, "original.mp3")

    if os.path.exists(final_path):
        print(f"  Audio already exists: {final_path}")
        return final_path

    output_template = os.path.join(song_dir, "original.%(ext)s")
    query = f"ytsearch1:{artist} {title} official audio"

    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--output", output_template,
        "--no-playlist",
        "--quiet",
        "--no-warnings",
        query
    ]

    print(f"  Downloading: {artist} - {title}")
    try:
        result = subprocess.run(cmd, timeout=120, capture_output=True, text=True)
        if result.returncode == 0 and os.path.exists(final_path):
            print(f"  Saved to: {final_path}")
            return final_path
        else:
            print(f"  yt-dlp failed: {result.stderr.strip()[:200]}")
            return None
    except subprocess.TimeoutExpired:
        print(f"  Timeout downloading: {title}")
        return None
    except FileNotFoundError:
        print("  ERROR: yt-dlp not found. Install with: pip install yt-dlp")
        return None