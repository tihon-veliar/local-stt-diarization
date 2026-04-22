"""Best-effort timestamp alignment built around WhisperX."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import RuntimeConfig
from .transcribe import TranscriptionResult

try:
    import whisperx
except ImportError:  # pragma: no cover - depends on local environment
    whisperx = None


@dataclass(slots=True)
class AlignmentResult:
    """Best-effort aligned segment payload."""

    segments: list[dict[str, Any]]


def run_alignment(
    audio_path: Path,
    transcription: TranscriptionResult,
    config: RuntimeConfig,
) -> AlignmentResult | None:
    """Align transcript segments when WhisperX is available and enabled."""

    if not config.features.enable_alignment:
        return None
    if whisperx is None:
        raise RuntimeError(
            "WhisperX is not installed. Install project dependencies or disable alignment."
        )

    language = transcription.language or config.language
    if language is None:
        raise RuntimeError("Alignment requires a known language.")

    audio = whisperx.load_audio(str(audio_path))
    model_a, metadata = whisperx.load_align_model(language_code=language, device=config.device)
    aligned = whisperx.align(
        transcription.raw_segments,
        model_a,
        metadata,
        audio,
        config.device,
        return_char_alignments=False,
    )
    return AlignmentResult(segments=list(aligned.get("segments", [])))
