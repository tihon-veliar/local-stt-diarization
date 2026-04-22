"""Helpers for building canonical transcript documents from stage outputs."""

from __future__ import annotations

from pathlib import Path

from .transcript_contract import (
    Segment,
    SourceMetadata,
    StageStatus,
    TranscriptDocument,
    TranscriptWarning,
    build_transcript_document,
)
from .transcribe import TranscriptionResult


def build_document(
    *,
    source_path: Path,
    transcription: TranscriptionResult,
    aligned_segments: list[dict] | None,
    warnings: list[TranscriptWarning],
    stage_statuses: list[StageStatus],
    duration_seconds: float | None = None,
) -> TranscriptDocument:
    """Build the final canonical transcript document."""

    source = SourceMetadata.from_path(source_path)
    source.detected_language = transcription.language
    source.duration_seconds = duration_seconds

    segments = merge_segments(transcription, aligned_segments)
    return build_transcript_document(
        source=source,
        segments=segments,
        warnings=warnings,
        stage_statuses=stage_statuses,
    )


def merge_segments(
    transcription: TranscriptionResult,
    aligned_segments: list[dict] | None,
) -> list[Segment]:
    """Use aligned timestamps when available, otherwise keep transcription segments."""

    if not aligned_segments:
        return [
            Segment(
                id=segment.id,
                start_seconds=segment.start_seconds,
                end_seconds=segment.end_seconds,
                text=segment.text,
                confidence=segment.confidence,
            )
            for segment in transcription.segments
        ]

    merged: list[Segment] = []
    for index, segment in enumerate(transcription.segments):
        aligned = aligned_segments[index] if index < len(aligned_segments) else {}
        start_seconds = float(aligned.get("start", segment.start_seconds))
        end_seconds = float(aligned.get("end", segment.end_seconds))
        text = str(aligned.get("text", segment.text)).strip() or segment.text
        merged.append(
            Segment(
                id=segment.id,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
                text=text,
                confidence=segment.confidence,
            )
        )
    return merged
