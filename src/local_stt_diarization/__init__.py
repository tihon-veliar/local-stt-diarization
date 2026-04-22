"""local_stt_diarization package."""

from .config import FeatureFlags, RuntimeConfig, SpeakerConfig
from .diarize import DiarizationResult, DiarizationTurn
from .exporters import render_json, render_markdown, render_txt, write_exports
from .transcript_contract import (
    SCHEMA_VERSION,
    Segment,
    SourceMetadata,
    StageStatus,
    TranscriptDocument,
    TranscriptWarning,
    build_transcript_document,
)

__all__ = [
    "__version__",
    "FeatureFlags",
    "DiarizationResult",
    "DiarizationTurn",
    "RuntimeConfig",
    "SCHEMA_VERSION",
    "Segment",
    "SourceMetadata",
    "SpeakerConfig",
    "StageStatus",
    "TranscriptDocument",
    "TranscriptWarning",
    "build_transcript_document",
    "render_json",
    "render_markdown",
    "render_txt",
    "write_exports",
]

__version__ = "0.1.0"
