"""
pipeline.py — Full pipeline for songs with missing lyrics.

Flow per song:
  1. Download full audio via yt-dlp  → audio/{spotify_id}/original.mp3
  2. Separate vocals via Demucs      → audio/{spotify_id}/vocals.mp3
  3. Transcribe with Whisper         → uses language stored in DB per song
  4. Save to DB
"""

import os
import argparse
from database import (
    init_db,
    get_tracks_missing_lyrics,
    update_audio_path,
    update_vocals_path,
    update_transcription,
)
from audio_fetcher import fetch_audio
from vocal_separator import separate_vocals
from transcriber import transcribe


def run_pipeline(limit=None, skip_separation=False):
    init_db()
    tracks = get_tracks_missing_lyrics()

    if not tracks:
        print("No tracks with missing lyrics. Add songs first using spotify_test.py")
        return

    if limit:
        tracks = tracks[:limit]

    print(f"\nProcessing {len(tracks)} tracks.\n")
    success, failed = 0, 0

    for i, (spotify_id, title, artist, language) in enumerate(tracks, 1):
        print(f"{'='*60}")
        print(f"[{i}/{len(tracks)}] {artist} — {title} (language: {language})")
        print(f"{'='*60}")

        # ── Step 1: Download audio ──────────────────────────────────
        audio_path = fetch_audio(spotify_id, title, artist)
        if not audio_path:
            print("  ✗ Could not download audio. Skipping.\n")
            failed += 1
            continue
        update_audio_path(spotify_id, audio_path)

        # ── Step 2: Separate vocals ─────────────────────────────────
        if skip_separation:
            transcribe_input = audio_path
            print("  (Skipping vocal separation)")
        else:
            vocals_path = separate_vocals(spotify_id, audio_path)
            if not vocals_path:
                print("  ✗ Vocal separation failed — falling back to full audio.")
                transcribe_input = audio_path
            else:
                update_vocals_path(spotify_id, vocals_path)
                transcribe_input = vocals_path

        # ── Step 3: Transcribe using DB language ────────────────────
        lyrics = transcribe(transcribe_input, language=language)
        if not lyrics:
            print("  ✗ Transcription failed. Skipping.\n")
            failed += 1
            continue

        # ── Step 4: Save to DB ──────────────────────────────────────
        update_transcription(spotify_id, lyrics)
        print(f"  ✓ Done — {len(lyrics)} chars transcribed.\n")
        success += 1

    print(f"\nPipeline complete: {success} succeeded, {failed} failed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lyrics transcription pipeline")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max songs to process (default: all)")
    parser.add_argument("--no-separation", action="store_true",
                        help="Skip Demucs — transcribe full audio directly")
    args = parser.parse_args()

    run_pipeline(limit=args.limit, skip_separation=args.no_separation)