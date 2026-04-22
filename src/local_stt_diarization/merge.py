"""Helpers for building canonical transcript documents from stage outputs."""

from __future__ import annotations

from pathlib import Path

from .diarize import DiarizationTurn
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
    diarization_turns: list[DiarizationTurn] | None,
    warnings: list[TranscriptWarning],
    stage_statuses: list[StageStatus],
    duration_seconds: float | None = None,
) -> TranscriptDocument:
    """Build the final canonical transcript document."""

    source = SourceMetadata.from_path(source_path)
    source.detected_language = transcription.language
    source.duration_seconds = duration_seconds

    segments = merge_segments(transcription, aligned_segments, diarization_turns, warnings)
    return build_transcript_document(
        source=source,
        segments=segments,
        warnings=warnings,
        stage_statuses=stage_statuses,
    )


def merge_segments(
    transcription: TranscriptionResult,
    aligned_segments: list[dict] | None,
    diarization_turns: list[DiarizationTurn] | None,
    warnings: list[TranscriptWarning] | None = None,
) -> list[Segment]:
    """Use aligned timestamps when available, otherwise keep transcription segments."""

    aligned_segment_list = aligned_segments or []
    merged: list[Segment] = []
    for index, segment in enumerate(transcription.segments):
        aligned = aligned_segment_list[index] if index < len(aligned_segment_list) else {}
        start_seconds = float(aligned.get("start", segment.start_seconds))
        end_seconds = float(aligned.get("end", segment.end_seconds))
        text = str(aligned.get("text", segment.text)).strip() or segment.text
        speaker = _pick_speaker_for_segment(
            start_seconds,
            end_seconds,
            diarization_turns or [],
            warnings,
        )
        merged.append(
            Segment(
                id=segment.id,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
                text=text,
                speaker=speaker,
                confidence=segment.confidence,
            )
        )
    return merged


def _pick_speaker_for_segment(
    start_seconds: float,
    end_seconds: float,
    diarization_turns: list[DiarizationTurn],
    warnings: list[TranscriptWarning] | None,
) -> str | None:
    """Choose the dominant speaker label for a transcript segment when overlap is clear."""

    if not diarization_turns:
        return None

    segment_duration = max(end_seconds - start_seconds, 0.0)
    if segment_duration <= 0:
        return None

    overlaps_by_speaker: dict[str, float] = {}
    for turn in diarization_turns:
        overlap = _compute_overlap(
            start_seconds,
            end_seconds,
            turn.start_seconds,
            turn.end_seconds,
        )
        if overlap > 0:
            overlaps_by_speaker[turn.speaker] = overlaps_by_speaker.get(turn.speaker, 0.0) + overlap

    if not overlaps_by_speaker:
        return None

    ranked = sorted(overlaps_by_speaker.items(), key=lambda item: item[1], reverse=True)
    winner, winner_overlap = ranked[0]
    winner_ratio = winner_overlap / segment_duration

    if len(ranked) > 1:
        runner_up_ratio = ranked[1][1] / segment_duration
        if winner_ratio < 0.6 or (winner_ratio - runner_up_ratio) < 0.15:
            _append_ambiguity_warning(warnings)
            return None

    if winner_ratio < 0.5:
        _append_ambiguity_warning(warnings)
        return None

    return winner


def _compute_overlap(
    segment_start: float,
    segment_end: float,
    turn_start: float,
    turn_end: float,
) -> float:
    return max(0.0, min(segment_end, turn_end) - max(segment_start, turn_start))


def _append_ambiguity_warning(warnings: list[TranscriptWarning] | None) -> None:
    if warnings is None:
        return
    for warning in warnings:
        if warning.code == "speaker_assignment_ambiguous":
            return
    warnings.append(
        TranscriptWarning(
            code="speaker_assignment_ambiguous",
            stage="diarization",
            message=(
                "Some transcript segments had weak or competing diarization overlap; "
                "speaker labels were omitted for those segments."
            ),
        )
    )
