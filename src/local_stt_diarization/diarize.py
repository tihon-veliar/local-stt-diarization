"""Best-effort speaker diarization built around pyannote.audio."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .config import RuntimeConfig

try:
    from pyannote.audio import Pipeline
except ImportError:  # pragma: no cover - depends on local environment
    Pipeline = None

try:
    import torch
except ImportError:  # pragma: no cover - depends on local environment
    torch = None


@dataclass(slots=True)
class DiarizationTurn:
    """Canonical diarization time range before transcript merge."""

    start_seconds: float
    end_seconds: float
    speaker: str


@dataclass(slots=True)
class DiarizationResult:
    """Structured output from the diarization stage."""

    turns: list[DiarizationTurn]


def run_diarization(audio_path: Path, config: RuntimeConfig) -> DiarizationResult | None:
    """Run speaker diarization when enabled and supported."""

    if not config.features.enable_diarization:
        return None
    if Pipeline is None:
        raise RuntimeError(
            "pyannote.audio is not installed. Install project dependencies or disable diarization."
        )

    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
    pipeline_kwargs: dict[str, object] = {}
    if token:
        pipeline_kwargs["use_auth_token"] = token

    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", **pipeline_kwargs)
    if pipeline is None:
        raise RuntimeError("Unable to initialize pyannote diarization pipeline.")

    if torch is not None and hasattr(pipeline, "to") and config.device:
        try:
            pipeline.to(torch.device(config.device))
        except Exception:
            # Leave the pipeline on its default device if transfer is unsupported.
            pass

    diarization_kwargs: dict[str, int] = {}
    if config.speaker.expected_speakers is not None:
        diarization_kwargs["num_speakers"] = config.speaker.expected_speakers
    else:
        if config.speaker.min_speakers is not None:
            diarization_kwargs["min_speakers"] = config.speaker.min_speakers
        if config.speaker.max_speakers is not None:
            diarization_kwargs["max_speakers"] = config.speaker.max_speakers

    diarization = pipeline(str(audio_path), **diarization_kwargs)
    turns: list[DiarizationTurn] = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        turns.append(
            DiarizationTurn(
                start_seconds=float(turn.start),
                end_seconds=float(turn.end),
                speaker=str(speaker),
            )
        )
    return DiarizationResult(turns=turns)
