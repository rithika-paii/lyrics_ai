import os
import subprocess
import shutil

DEMUCS_MODEL = "htdemucs_ft"

def separate_vocals(spotify_id, original_audio_path):
    """
    Runs Demucs on original.mp3 and extracts vocals stem.
    Saves to audio/{spotify_id}/vocals.mp3
    Returns path to vocals file, or None if failed.
    """
    song_dir = os.path.dirname(original_audio_path)
    vocals_path = os.path.join(song_dir, "vocals.mp3")

    if os.path.exists(vocals_path):
        print(f"  Vocals already separated: {vocals_path}")
        return vocals_path

    if not os.path.exists(original_audio_path):
        print(f"  Original audio not found: {original_audio_path}")
        return None

    demucs_out_dir = os.path.join(song_dir, "_demucs_tmp")
    os.makedirs(demucs_out_dir, exist_ok=True)

    print(f"  Separating vocals (htdemucs_ft — takes a few minutes on M3)...")

    cmd = [
        "python", "-m", "demucs",
        "--name", DEMUCS_MODEL,
        "--out", demucs_out_dir,
        "--two-stems", "vocals",  # only split vocals vs accompaniment, faster
        #device", "mps",        # use Apple Silicon GPU
        original_audio_path
    ]

    try:
        result = subprocess.run(cmd, timeout=1800, text=True)

        if result.returncode != 0:
            # MPS might fail on some versions — fall back to CPU
            print(f"  MPS failed, retrying on CPU...")
            cmd[cmd.index("--device") + 1] = "cpu"
            result = subprocess.run(cmd, timeout=1800, text=True)

        if result.returncode != 0:
            print(f"  Demucs failed:\n{result.stderr.strip()[:400]}")
            shutil.rmtree(demucs_out_dir, ignore_errors=True)
            return None

        # Find vocals.wav in demucs output
        vocals_wav = None
        for root, dirs, files in os.walk(demucs_out_dir):
            for f in files:
                if f == "vocals.wav":
                    vocals_wav = os.path.join(root, f)
                    break

        if not vocals_wav:
            print(f"  Could not find vocals.wav in Demucs output.")
            shutil.rmtree(demucs_out_dir, ignore_errors=True)
            return None

        # Convert to mp3 with ffmpeg
        convert_cmd = [
            "ffmpeg", "-i", vocals_wav,
            "-q:a", "0", "-y",
            vocals_path
        ]
        conv = subprocess.run(convert_cmd, capture_output=True, text=True)

        if conv.returncode != 0 or not os.path.exists(vocals_path):
            # ffmpeg not available — keep as wav
            print("  ffmpeg not found, keeping vocals as .wav")
            vocals_path = os.path.join(song_dir, "vocals.wav")
            shutil.move(vocals_wav, vocals_path)
        else:
            print(f"  Vocals saved: {vocals_path}")

        shutil.rmtree(demucs_out_dir, ignore_errors=True)
        return vocals_path

    except subprocess.TimeoutExpired:
        print("  Demucs timed out.")
        shutil.rmtree(demucs_out_dir, ignore_errors=True)
        return None
    except FileNotFoundError:
        print("  ERROR: Demucs not found. Run: pip install demucs")
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python vocal_separator.py <spotify_id> <path/to/original.mp3>")
    else:
        result = separate_vocals(sys.argv[1], sys.argv[2])
        print(f"Result: {result}")