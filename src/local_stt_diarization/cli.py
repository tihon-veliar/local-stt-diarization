"""CLI entrypoint for transcript-first single-file processing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .align import run_alignment
from .audio import ensure_output_dir, prepare_audio, validate_input_audio
from .config import ExportOptions, FeatureFlags, RuntimeConfig, SpeakerConfig
from .diarize import run_diarization
from .exporters import write_exports, write_partial_checkpoint
from .merge import build_document
from .terminal_ui import run_guided_wizard
from .transcript_contract import (
    RunState,
    Segment,
    SourceMetadata,
    StageStatus,
    TranscriptWarning,
    build_partial_transcript_document,
)
from .transcribe import TranscriptionSegmentData, run_transcription


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for single-file transcription."""

    parser = argparse.ArgumentParser(
        prog="local-stt-diarization",
        description="Transcribe a single audio file into canonical JSON plus optional TXT and Markdown outputs.",
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        help="Path to a supported audio file (.wav, .mp3, .m4a).",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for exported transcript artifacts. Default: ./output",
    )
    parser.add_argument(
        "--guided",
        action="store_true",
        help="Launch guided terminal prompts for normal operator-driven runs.",
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
    parser.add_argument(
        "--no-txt",
        action="store_true",
        help="Skip the adjacent TXT export. Canonical JSON still writes.",
    )
    parser.add_argument(
        "--no-md",
        action="store_true",
        help="Skip the adjacent Markdown export. Canonical JSON still writes.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the transcript-first single-file pipeline."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.guided:
            config = run_guided_wizard(Path.cwd())
        else:
            if args.input_path is None:
                parser.error("input_path is required unless --guided is used")
            config = build_runtime_config_from_args(args)
        config.validate()
        return run_pipeline(config)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def build_runtime_config_from_args(args: argparse.Namespace) -> RuntimeConfig:
    """Create the canonical runtime config from raw CLI arguments."""

    return RuntimeConfig(
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
        exports=ExportOptions(
            write_txt=not args.no_txt,
            write_md=not args.no_md,
        ),
    )


def run_pipeline(config: RuntimeConfig) -> int:
    """Execute the synchronous pipeline and emit transcript artifacts."""

    warnings: list[TranscriptWarning] = []
    stage_statuses: list[StageStatus] = []
    checkpoint_segments: list[Segment] = []
    checkpoint_source = SourceMetadata.from_path(config.input_path)
    checkpoint_source.detected_language = config.language
    checkpoint_target: Path | None = None
    last_completed_stage: str | None = None

    def write_checkpoint(run_state: RunState, stage_name: str | None) -> None:
        nonlocal checkpoint_target
        if not checkpoint_segments:
            return
        document = build_partial_transcript_document(
            run_state=run_state,
            last_completed_stage=stage_name,
            source=checkpoint_source,
            segments=list(checkpoint_segments),
            warnings=list(warnings),
            stage_statuses=list(stage_statuses),
        )
        checkpoint_target = write_partial_checkpoint(document, config.output_dir, config.input_path.stem)

    try:
        _print_stage("prepare", "started", f"Preparing audio from {config.input_path.name}")
        prepared_audio = prepare_audio(config.input_path, config.output_dir)
        checkpoint_source.duration_seconds = prepared_audio.duration_seconds
        last_completed_stage = "prepare"
        _print_stage(
            "prepare",
            "completed",
            f"Audio ready at {prepared_audio.normalized_path.name}",
        )

        _print_stage("transcription", "started", f"Running model {config.transcription_model}")

        def on_transcription_segment(segment: TranscriptionSegmentData, count: int) -> None:
            checkpoint_segments.append(
                Segment(
                    id=segment.id,
                    start_seconds=segment.start_seconds,
                    end_seconds=segment.end_seconds,
                    text=segment.text,
                    confidence=segment.confidence,
                )
            )
            if count == 1 or count % 5 == 0:
                _print_stage("transcription", "progress", f"Captured {count} transcript segments so far")
                write_checkpoint("in_progress", last_completed_stage)

        transcription = run_transcription(
            prepared_audio.normalized_path,
            config,
            on_segment=on_transcription_segment,
        )
        checkpoint_source.detected_language = transcription.language
        stage_statuses.append(
            StageStatus(
                stage="transcription",
                status="completed",
                details=f"Generated {len(transcription.segments)} transcript segments.",
            )
        )
        last_completed_stage = "transcription"
        write_checkpoint("in_progress", last_completed_stage)
        _print_stage(
            "transcription",
            "completed",
            f"Generated {len(transcription.segments)} transcript segments.",
        )

        aligned_segments = None
        if config.features.enable_alignment:
            _print_stage("alignment", "started", "Running best-effort alignment")
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
                    last_completed_stage = "alignment"
                    _print_stage(
                        "alignment",
                        "completed",
                        f"Aligned {len(aligned_segments)} transcript segments.",
                    )
                else:
                    stage_statuses.append(
                        StageStatus(
                            stage="alignment",
                            status="skipped",
                            details="Alignment disabled or unavailable for this run.",
                        )
                    )
                    _print_stage(
                        "alignment",
                        "skipped",
                        "Alignment unavailable; keeping transcription timestamps.",
                    )
                write_checkpoint("in_progress", last_completed_stage)
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
                _print_warning("alignment", "alignment_failed", str(exc))
                write_checkpoint("in_progress", last_completed_stage)
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
            _print_stage("alignment", "skipped", "Alignment disabled by configuration.")
            write_checkpoint("in_progress", last_completed_stage)

        diarization_turns = None
        if config.features.enable_diarization:
            _print_stage("diarization", "started", "Running best-effort diarization")
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
                    last_completed_stage = "diarization"
                    _print_stage(
                        "diarization",
                        "completed",
                        f"Generated {len(diarization_turns)} diarization turns.",
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
                    _print_warning(
                        "diarization",
                        "diarization_unavailable",
                        "No speaker turns were returned; continuing without speaker labels.",
                    )
                write_checkpoint("in_progress", last_completed_stage)
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
                _print_warning("diarization", "diarization_failed", str(exc))
                write_checkpoint("in_progress", last_completed_stage)
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
            _print_stage("diarization", "skipped", "Diarization disabled by configuration.")
            write_checkpoint("in_progress", last_completed_stage)

        _print_stage("export", "started", "Writing final transcript artifacts")
        selected_formats = ", ".join(config.exports.selected_formats()).upper()
        stage_statuses.append(
            StageStatus(
                stage="export",
                status="completed",
                details=f"Writing export artifacts: {selected_formats}.",
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
        checkpoint_segments[:] = [segment for segment in document.segments]
        last_completed_stage = "export"
        write_checkpoint("completed", last_completed_stage)

        targets = write_exports(
            document,
            config.output_dir,
            config.input_path.stem,
            export_options=config.exports,
        )

        _print_stage("export", "completed", "Final artifacts written successfully")
        print(f"Transcript written to: {targets['json']}")
        if "txt" in targets:
            print(f"Plain text written to: {targets['txt']}")
        if "md" in targets:
            print(f"Markdown written to: {targets['md']}")
        if checkpoint_target is not None:
            print(f"Checkpoint written to: {checkpoint_target}")
        for warning in warnings:
            _print_warning(warning.stage, warning.code, warning.message)
        return 0
    except Exception:
        write_checkpoint("failed", last_completed_stage)
        raise


def _print_stage(stage: str, event: str, details: str) -> None:
    print(f"[{stage}] {event}: {details}")


def _print_warning(stage: str, code: str, message: str) -> None:
    print(f"Warning [{stage}/{code}]: {message}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
