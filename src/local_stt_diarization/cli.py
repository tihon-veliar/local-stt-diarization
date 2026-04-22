"""CLI entrypoint for transcript-first single-file processing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .align import run_alignment
from .audio import ensure_output_dir, prepare_audio, validate_input_audio
from .config import FeatureFlags, RuntimeConfig, SpeakerConfig
from .diarize import run_diarization
from .exporters import write_exports
from .merge import build_document
from .transcript_contract import StageStatus, TranscriptWarning
from .transcribe import run_transcription


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for single-file transcription."""

    parser = argparse.ArgumentParser(
        prog="local-stt-diarization",
        description="Transcribe a single audio file into canonical JSON, TXT, and Markdown outputs.",
    )
    parser.add_argument("input_path", help="Path to a supported audio file (.wav, .mp3, .m4a).")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for exported transcript artifacts. Default: ./output",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Optional language hint such as 'en' or 'ru'. Auto-detect when omitted.",
    )
    parser.add_argument(
        "--model",
        default="large-v3",
        help="faster-whisper model name. Default: large-v3",
    )
    parser.add_argument(
        "--device",
        default="cuda",
        help="Inference device for faster-whisper and WhisperX. Default: cuda",
    )
    parser.add_argument(
        "--compute-type",
        default="float16",
        help="Model compute type. Default: float16",
    )
    parser.add_argument(
        "--disable-alignment",
        action="store_true",
        help="Skip best-effort WhisperX alignment.",
    )
    parser.add_argument(
        "--disable-diarization",
        action="store_true",
        help="Skip optional pyannote speaker diarization.",
    )
    parser.add_argument(
        "--speakers",
        type=int,
        default=None,
        help="Optional exact speaker-count hint for diarization.",
    )
    parser.add_argument(
        "--min-speakers",
        type=int,
        default=None,
        help="Optional lower bound for automatic speaker estimation.",
    )
    parser.add_argument(
        "--max-speakers",
        type=int,
        default=None,
        help="Optional upper bound for automatic speaker estimation.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the transcript-first single-file pipeline."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = RuntimeConfig(
            input_path=validate_input_audio(Path(args.input_path)),
            output_dir=ensure_output_dir(Path(args.output_dir)),
            language=args.language,
            transcription_model=args.model,
            compute_type=args.compute_type,
            device=args.device,
            features=FeatureFlags(
                enable_alignment=not args.disable_alignment,
                enable_diarization=not args.disable_diarization,
            ),
            speaker=SpeakerConfig(
                expected_speakers=args.speakers,
                min_speakers=args.min_speakers,
                max_speakers=args.max_speakers,
            ),
        )
        config.validate()
        return run_pipeline(config)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def run_pipeline(config: RuntimeConfig) -> int:
    """Execute the synchronous pipeline and emit transcript artifacts."""

    warnings: list[TranscriptWarning] = []
    stage_statuses: list[StageStatus] = []

    prepared_audio = prepare_audio(config.input_path, config.output_dir)

    transcription = run_transcription(prepared_audio.normalized_path, config)
    stage_statuses.append(
        StageStatus(
            stage="transcription",
            status="completed",
            details=f"Generated {len(transcription.segments)} transcript segments.",
        )
    )

    aligned_segments = None
    if config.features.enable_alignment:
        try:
            aligned = run_alignment(prepared_audio.normalized_path, transcription, config)
            aligned_segments = aligned.segments if aligned is not None else None
            if aligned_segments:
                stage_statuses.append(
                    StageStatus(
                        stage="alignment",
                        status="completed",
                        details=f"Aligned {len(aligned_segments)} transcript segments.",
                    )
                )
            else:
                stage_statuses.append(
                    StageStatus(
                        stage="alignment",
                        status="skipped",
                        details="Alignment disabled or unavailable for this run.",
                    )
                )
        except Exception as exc:
            warnings.append(
                TranscriptWarning(
                    code="alignment_failed",
                    stage="alignment",
                    message=f"Alignment failed; transcript exported with transcription timestamps. {exc}",
                )
            )
            stage_statuses.append(
                StageStatus(
                    stage="alignment",
                    status="degraded",
                    details=str(exc),
                )
            )
    else:
        warnings.append(
            TranscriptWarning(
                code="alignment_unavailable",
                stage="alignment",
                message="Alignment disabled by configuration.",
            )
        )
        stage_statuses.append(
            StageStatus(
                stage="alignment",
                status="skipped",
                details="Alignment disabled by configuration.",
            )
        )

    diarization_turns = None
    if config.features.enable_diarization:
        try:
            diarization = run_diarization(prepared_audio.normalized_path, config)
            diarization_turns = diarization.turns if diarization is not None else None
            if diarization_turns:
                stage_statuses.append(
                    StageStatus(
                        stage="diarization",
                        status="completed",
                        details=f"Generated {len(diarization_turns)} diarization turns.",
                    )
                )
            else:
                warnings.append(
                    TranscriptWarning(
                        code="diarization_unavailable",
                        stage="diarization",
                        message="Diarization returned no speaker turns; transcript exported without speaker labels.",
                    )
                )
                stage_statuses.append(
                    StageStatus(
                        stage="diarization",
                        status="degraded",
                        details="No diarization turns were returned.",
                    )
                )
        except Exception as exc:
            warnings.append(
                TranscriptWarning(
                    code="diarization_failed",
                    stage="diarization",
                    message=f"Diarization failed; transcript exported without speaker labels. {exc}",
                )
            )
            stage_statuses.append(
                StageStatus(
                    stage="diarization",
                    status="degraded",
                    details=str(exc),
                )
            )
    else:
        warnings.append(
            TranscriptWarning(
                code="diarization_disabled",
                stage="diarization",
                message="Diarization disabled by configuration.",
            )
        )
        stage_statuses.append(
            StageStatus(
                stage="diarization",
                status="skipped",
                details="Diarization disabled by configuration.",
            )
        )

    stage_statuses.append(
        StageStatus(
            stage="export",
            status="completed",
            details="Writing canonical JSON, TXT, and Markdown artifacts.",
        )
    )

    document = build_document(
        source_path=config.input_path,
        transcription=transcription,
        aligned_segments=aligned_segments,
        diarization_turns=diarization_turns,
        warnings=warnings,
        stage_statuses=stage_statuses,
        duration_seconds=prepared_audio.duration_seconds,
    )
    targets = write_exports(document, config.output_dir, config.input_path.stem)

    print(f"Transcript written to: {targets['json']}")
    print(f"Plain text written to: {targets['txt']}")
    print(f"Markdown written to: {targets['md']}")
    for warning in warnings:
        print(f"Warning [{warning.stage}/{warning.code}]: {warning.message}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
