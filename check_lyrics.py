import requests

def check_lyrics(artist, title):
    url = f"https://api.lyrics.ovh/v1/{artist}/{title}"

    try:
        response = requests.get(url)

        if response.status_code != 200:
            return "missing"

        data = response.json()
        lyrics = data.get("lyrics")

        # Check if lyrics exist and are not blank
        if lyrics and lyrics.strip():
            return "found"
        else:
            return "missing"

    except Exception:
        return "missing"