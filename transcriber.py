import os
import whisper

MODEL_SIZE = os.getenv("WHISPER_MODEL", "medium")

print(f"Loading Whisper model: {MODEL_SIZE} ...")
_model = None

def get_model():
    global _model
    if _model is None:
        _model = whisper.load_model(MODEL_SIZE)
    return _model

def transcribe(audio_path, language="kn"):
    """
    Transcribes audio file using Whisper.
    language: ISO 639-1 code e.g. "kn" (Kannada), "te" (Telugu),
              "ta" (Tamil), "hi" (Hindi), "en" (English)
              Pass None to auto-detect.
    """
    if not os.path.exists(audio_path):
        print(f"  Audio file not found: {audio_path}")
        return None

    lang_display = language if language else "auto-detect"
    print(f"  Transcribing: {os.path.basename(audio_path)} (language: {lang_display})")
    try:
        model = get_model()
        result = model.transcribe(
            audio_path,
            language=language,      # None = auto-detect, "kn" = force Kannada
            task="transcribe",
            fp16=False,
            verbose=False
        )
        text = result["text"].strip()
        detected = result.get("language", "unknown")
        print(f"  Detected language: {detected}")
        print(f"  Done. ({len(text)} chars)")
        return text
    except Exception as e:
        print(f"  Transcription error: {e}")
        return None

if __name__ == "__main__":
    import sys
    lang = sys.argv[2] if len(sys.argv) > 2 else "kn"
    if len(sys.argv) < 2:
        print("Usage: python transcriber.py <audio_file.mp3> [language_code]")
        print("Examples:")
        print("  python transcriber.py song.mp3 kn   # Kannada")
        print("  python transcriber.py song.mp3 te   # Telugu")
        print("  python transcriber.py song.mp3 en   # English")
        print("  python transcriber.py song.mp3      # auto-detect")
    else:
        text = transcribe(sys.argv[1], language=lang)
        print("\n--- TRANSCRIPTION ---")
        print(text)