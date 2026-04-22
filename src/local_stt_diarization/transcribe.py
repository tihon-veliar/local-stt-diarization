"""Transcription adapter built around faster-whisper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import RuntimeConfig

try:
    from faster_whisper import WhisperModel
except ImportError:  # pragma: no cover - depends on local environment
    WhisperModel = None


@dataclass(slots=True)
class TranscriptionSegmentData:
    """Minimal transcription segment data before alignment or export."""

    id: str
    start_seconds: float
    end_seconds: float
    text: str
    confidence: float | None = None


@dataclass(slots=True)
class TranscriptionResult:
    """Structured transcript result from the transcription stage."""

    language: str | None
    segments: list[TranscriptionSegmentData]
    raw_segments: list[dict[str, Any]]


def run_transcription(audio_path: Path, config: RuntimeConfig) -> TranscriptionResult:
    """Run the mandatory transcription stage using faster-whisper."""

    if WhisperModel is None:
        raise RuntimeError(
            "faster-whisper is not installed. Install project dependencies before running the CLI."
        )

    model = WhisperModel(
        config.transcription_model,
        device=config.device,
        compute_type=config.compute_type,
    )
    segment_iter, info = model.transcribe(
        str(audio_path),
        language=config.language,
        vad_filter=False,
    )

    segments: list[TranscriptionSegmentData] = []
    raw_segments: list[dict[str, Any]] = []
    for index, segment in enumerate(segment_iter, start=1):
        text = (segment.text or "").strip()
        if not text:
            continue

        confidence = _confidence_from_avg_logprob(getattr(segment, "avg_logprob", None))
        canonical = TranscriptionSegmentData(
            id=f"seg-{index:04d}",
            start_seconds=float(segment.start),
            end_seconds=float(segment.end),
            text=text,
            confidence=confidence,
        )
        segments.append(canonical)
        raw_segments.append(
            {
                "id": canonical.id,
                "start": canonical.start_seconds,
                "end": canonical.end_seconds,
                "text": canonical.text,
            }
        )

    if not segments:
        raise RuntimeError("Transcription produced no segments.")

    return TranscriptionResult(
        language=getattr(info, "language", None),
        segments=segments,
        raw_segments=raw_segments,
    )


def _confidence_from_avg_logprob(avg_logprob: float | None) -> float | None:
    """Map avg_logprob into a bounded confidence when available."""

    if avg_logprob is None:
        return None
    normalized = 1.0 + (float(avg_logprob) / 5.0)
    if normalized < 0.0:
        return 0.0
    if normalized > 1.0:
        return 1.0
    return round(normalized, 4)
