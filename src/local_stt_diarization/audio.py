"""Audio validation and normalization helpers."""

from __future__ import annotations

import shutil
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a"}


@dataclass(slots=True)
class PreparedAudio:
    """Normalized audio asset ready for downstream processing."""

    source_path: Path
    normalized_path: Path
    extension: str
    normalization_applied: bool
    duration_seconds: float | None


def validate_input_audio(path: Path) -> Path:
    """Validate that the input exists and uses a supported extension."""

    if not path.exists():
        raise FileNotFoundError(f"Input audio file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"Input path must be a file: {path}")
    extension = path.suffix.lower()
    if extension not in SUPPORTED_AUDIO_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_AUDIO_EXTENSIONS))
        raise ValueError(f"Unsupported audio extension '{extension}'. Supported: {supported}")
    return path.resolve()


def ensure_output_dir(path: Path) -> Path:
    """Create the output directory when needed and return its resolved path."""

    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def prepare_audio(input_path: Path, output_dir: Path) -> PreparedAudio:
    """Normalize the source audio into a WAV file for downstream tooling."""

    extension = input_path.suffix.lower()
    normalized_path = output_dir / f"{input_path.stem}.normalized.wav"

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        if extension == ".wav":
            return PreparedAudio(
                source_path=input_path,
                normalized_path=input_path,
                extension=extension,
                normalization_applied=False,
                duration_seconds=_read_wav_duration_seconds(input_path),
            )
        raise RuntimeError(
            "ffmpeg is required to normalize non-WAV inputs. Install ffmpeg or provide a WAV file."
        )

    command = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(normalized_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or "unknown ffmpeg error"
        raise RuntimeError(f"Audio normalization failed: {stderr}")

    return PreparedAudio(
        source_path=input_path,
        normalized_path=normalized_path,
        extension=extension,
        normalization_applied=True,
        duration_seconds=_read_wav_duration_seconds(normalized_path),
    )


def _read_wav_duration_seconds(path: Path) -> float | None:
    """Read duration from a WAV file when possible."""

    try:
        with wave.open(str(path), "rb") as handle:
            frame_rate = handle.getframerate()
            frame_count = handle.getnframes()
        if frame_rate <= 0:
            return None
        return round(frame_count / frame_rate, 3)
    except (wave.Error, OSError):
        return None
