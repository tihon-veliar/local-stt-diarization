"""Canonical transcript contract shared by the pipeline and exporters."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from .config import StageName, WarningCode

SCHEMA_VERSION = "1.0"
RunState = Literal["in_progress", "failed", "interrupted", "completed"]


@dataclass(slots=True)
class TranscriptWarning:
    """Warning emitted when an optional stage degrades or is skipped."""

    code: WarningCode
    stage: StageName
    message: str


@dataclass(slots=True)
class SourceMetadata:
    """Stable metadata about the processed source asset."""

    path: str
    filename: str
    extension: str
    detected_language: str | None = None
    duration_seconds: float | None = None

    @classmethod
    def from_path(cls, path: Path) -> "SourceMetadata":
        return cls(
            path=str(path),
            filename=path.name,
            extension=path.suffix.lower(),
        )


@dataclass(slots=True)
class Segment:
    """Canonical transcript segment used by all output renderers."""

    id: str
    start_seconds: float
    end_seconds: float
    text: str
    speaker: str | None = None
    confidence: float | None = None

    def validate(self) -> None:
        if not self.id.strip():
            raise ValueError("segment id is required")
        if self.start_seconds < 0:
            raise ValueError("segment start_seconds must be >= 0")
        if self.end_seconds < self.start_seconds:
            raise ValueError("segment end_seconds must be >= start_seconds")
        if not self.text.strip():
            raise ValueError("segment text is required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("segment confidence must be between 0.0 and 1.0")


@dataclass(slots=True)
class StageStatus:
    """Execution outcome recorded for each major pipeline stage."""

    stage: StageName
    status: str
    details: str | None = None


@dataclass(slots=True)
class TranscriptDocument:
    """Canonical machine-readable transcript document."""

    schema_version: str
    created_at: str
    source: SourceMetadata
    full_text: str
    segments: list[Segment]
    warnings: list[TranscriptWarning] = field(default_factory=list)
    stage_statuses: list[StageStatus] = field(default_factory=list)

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema version: {self.schema_version}")
        if not self.created_at.strip():
            raise ValueError("created_at is required")
        if not self.full_text.strip():
            raise ValueError("full_text is required")
        if not self.segments:
            raise ValueError("at least one segment is required")
        for segment in self.segments:
            segment.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(slots=True)
class PartialTranscriptDocument:
    """Operational checkpoint document for in-progress or failed runs."""

    schema_version: str
    artifact_kind: str
    run_state: RunState
    updated_at: str
    last_completed_stage: str | None
    source: SourceMetadata
    full_text: str
    segments: list[Segment]
    warnings: list[TranscriptWarning] = field(default_factory=list)
    stage_statuses: list[StageStatus] = field(default_factory=list)

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema version: {self.schema_version}")
        if self.artifact_kind != "checkpoint":
            raise ValueError("partial transcript artifact_kind must be 'checkpoint'")
        if not self.updated_at.strip():
            raise ValueError("updated_at is required")
        if not self.run_state.strip():
            raise ValueError("run_state is required")
        for segment in self.segments:
            segment.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def build_transcript_document(
    *,
    source: SourceMetadata,
    segments: list[Segment],
    warnings: list[TranscriptWarning] | None = None,
    stage_statuses: list[StageStatus] | None = None,
) -> TranscriptDocument:
    """Create a validated transcript document from canonical pieces."""

    document = TranscriptDocument(
        schema_version=SCHEMA_VERSION,
        created_at=datetime.now(UTC).isoformat(),
        source=source,
        full_text=_join_segment_text(segments),
        segments=segments,
        warnings=warnings or [],
        stage_statuses=stage_statuses or [],
    )
    document.validate()
    return document


def build_partial_transcript_document(
    *,
    run_state: RunState,
    last_completed_stage: str | None,
    source: SourceMetadata,
    segments: list[Segment],
    warnings: list[TranscriptWarning] | None = None,
    stage_statuses: list[StageStatus] | None = None,
) -> PartialTranscriptDocument:
    """Create an operational checkpoint artifact for an active or failed run."""

    document = PartialTranscriptDocument(
        schema_version=SCHEMA_VERSION,
        artifact_kind="checkpoint",
        run_state=run_state,
        updated_at=datetime.now(UTC).isoformat(),
        last_completed_stage=last_completed_stage,
        source=source,
        full_text=_join_segment_text(segments),
        segments=segments,
        warnings=warnings or [],
        stage_statuses=stage_statuses or [],
    )
    document.validate()
    return document


def _join_segment_text(segments: list[Segment]) -> str:
    return "\n".join(segment.text.strip() for segment in segments if segment.text.strip())
