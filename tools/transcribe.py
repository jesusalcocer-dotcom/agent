#!/usr/bin/env python3
"""
transcribe.py — Transcribe video or audio with OpenAI Whisper.

Usage:
    python transcribe.py <media-file> [--language es] [--out path]

Default behavior:
    - Extracts audio from video with ffmpeg (mono 16kHz 64kbps mp3).
    - Auto-chunks files larger than ~20 MB (Whisper limit is 25 MB).
    - Writes transcript to <project>/transcripts/<basename>.txt
      if the input lives inside a project with a transcripts/ folder.
    - Reads OPENAI_API_KEY from the nearest .env file walking up from CWD.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

WHISPER_CHUNK_SECONDS = 1500           # 25-minute chunks
CHUNK_MAX_SIZE = 20 * 1024 * 1024      # 20 MB safety margin under Whisper's 25 MB cap


def load_env(env_path: Path) -> dict:
    """Parse a simple .env file. No quoting magic — just KEY=VALUE."""
    env = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def find_env() -> Path | None:
    """Walk up from CWD looking for a .env file."""
    here = Path.cwd().resolve()
    for d in [here, *here.parents]:
        env = d / ".env"
        if env.exists():
            return env
    return None


def extract_audio(input_path: Path, output_path: Path) -> None:
    """ffmpeg: any media → mono 16 kHz 64 kbps mp3 (Whisper-friendly)."""
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k",
        "-f", "mp3", str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def chunk_audio(input_path: Path, chunk_dir: Path) -> list[Path]:
    """ffmpeg segment: split into 25-minute chunks."""
    chunk_dir.mkdir(parents=True, exist_ok=True)
    pattern = chunk_dir / "chunk_%03d.mp3"
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-f", "segment", "-segment_time", str(WHISPER_CHUNK_SECONDS),
        "-c", "copy", str(pattern),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return sorted(chunk_dir.glob("chunk_*.mp3"))


def transcribe_file(client, path: Path, language: str | None) -> str:
    with open(path, "rb") as f:
        params = {"model": "whisper-1", "file": f}
        if language:
            params["language"] = language
        result = client.audio.transcriptions.create(**params)
    return result.text


def resolve_output_path(media_path: Path, override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    # Look for a sibling transcripts/ folder one level up
    transcripts_dir = media_path.parent.parent / "transcripts"
    if transcripts_dir.exists() and transcripts_dir.is_dir():
        return transcripts_dir / (media_path.stem + ".txt")
    return media_path.with_suffix(".txt")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("media", help="Video or audio file to transcribe")
    parser.add_argument("--language", default="es", help="ISO 639-1 language code (default: es)")
    parser.add_argument("--out", help="Output transcript path (default: ../transcripts/<basename>.txt)")
    args = parser.parse_args()

    media_path = Path(args.media).expanduser().resolve()
    if not media_path.exists():
        sys.exit(f"❌ File not found: {media_path}")

    env_path = find_env()
    if not env_path:
        sys.exit("❌ No .env file found in CWD or parents. Expected OPENAI_API_KEY there.")
    api_key = load_env(env_path).get("OPENAI_API_KEY")
    if not api_key:
        sys.exit(f"❌ OPENAI_API_KEY not set in {env_path}")

    out_path = resolve_output_path(media_path, args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"📁 Input:    {media_path}")
    print(f"📝 Output:   {out_path}")
    print(f"🌐 Language: {args.language}")

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        audio_path = tmpdir / "audio.mp3"
        print("🔊 Extracting audio (mono 16kHz mp3)...")
        extract_audio(media_path, audio_path)
        size = audio_path.stat().st_size
        print(f"   Audio size: {size / 1024 / 1024:.1f} MB")

        if size <= CHUNK_MAX_SIZE:
            print("📡 Sending to Whisper (single shot)...")
            text = transcribe_file(client, audio_path, args.language)
        else:
            print("   Too large for single request — chunking...")
            chunks = chunk_audio(audio_path, tmpdir / "chunks")
            print(f"   {len(chunks)} chunks created")
            parts = []
            for i, chunk in enumerate(chunks, 1):
                mb = chunk.stat().st_size / 1024 / 1024
                print(f"   📡 Chunk {i}/{len(chunks)} ({mb:.1f} MB)...")
                parts.append(transcribe_file(client, chunk, args.language))
            text = "\n\n".join(parts)

    out_path.write_text(text, encoding="utf-8")
    word_count = len(text.split())
    print(f"✅ Done. {word_count:,} words → {out_path}")


if __name__ == "__main__":
    main()
