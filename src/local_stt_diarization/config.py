"""Runtime configuration primitives for the local STT pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


StageName = Literal["transcription", "alignment", "diarization", "export"]
WarningCode = Literal[
    "alignment_unavailable",
    "alignment_failed",
    "diarization_disabled",
    "diarization_unavailable",
    "diarization_failed",
    "speaker_assignment_ambiguous",
]


@dataclass(slots=True)
class FeatureFlags:
    """Optional enrichment stages that may degrade without failing the run."""

    enable_alignment: bool = True
    enable_diarization: bool = True


@dataclass(slots=True)
class SpeakerConfig:
    """Speaker diarization controls owned by the CLI/runtime layer."""

    expected_speakers: int | None = None
    min_speakers: int | None = None
    max_speakers: int | None = None

    def validate(self) -> None:
        if self.expected_speakers is not None and self.expected_speakers < 1:
            raise ValueError("expected_speakers must be >= 1")
        if self.min_speakers is not None and self.min_speakers < 1:
            raise ValueError("min_speakers must be >= 1")
        if self.max_speakers is not None and self.max_speakers < 1:
            raise ValueError("max_speakers must be >= 1")
        if (
            self.min_speakers is not None
            and self.max_speakers is not None
            and self.min_speakers > self.max_speakers
        ):
            raise ValueError("min_speakers cannot be greater than max_speakers")
        if (
            self.expected_speakers is not None
            and self.min_speakers is not None
            and self.expected_speakers < self.min_speakers
        ):
            raise ValueError("expected_speakers cannot be smaller than min_speakers")
        if (
            self.expected_speakers is not None
            and self.max_speakers is not None
            and self.expected_speakers > self.max_speakers
        ):
            raise ValueError("expected_speakers cannot be greater than max_speakers")


@dataclass(slots=True)
class RuntimeConfig:
    """Canonical runtime inputs shared by later pipeline stages."""

    input_path: Path
    output_dir: Path
    language: str | None = None
    transcription_model: str = "large-v3"
    compute_type: str = "float16"
    device: str = "cuda"
    features: FeatureFlags = field(default_factory=FeatureFlags)
    speaker: SpeakerConfig = field(default_factory=SpeakerConfig)

    def validate(self) -> None:
        if not self.input_path:
            raise ValueError("input_path is required")
        if not self.output_dir:
            raise ValueError("output_dir is required")
        if self.language is not None and not self.language.strip():
            raise ValueError("language cannot be blank when provided")
        if not self.transcription_model.strip():
            raise ValueError("transcription_model is required")
        if not self.compute_type.strip():
            raise ValueError("compute_type is required")
        if not self.device.strip():
            raise ValueError("device is required")
        self.speaker.validate()
