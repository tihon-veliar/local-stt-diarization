# local-stt-diarization

Standalone local Windows CLI project for long-form conversation transcription with transcript-first reliability and optional speaker diarization enrichment.

## Project Boundary

This project intentionally lives under `sandbox/` in the parent workspace, but it is its own repository boundary and should be treated as an independent codebase.

- Work on this project inside `sandbox/local-stt-diarization/`.
- Do not fold its source files into the parent repository structure.
- Keep runtime assets, model caches, outputs, and temporary files out of version control.

## MVP Direction

The planned MVP is a synchronous single-file CLI pipeline:

1. validate and normalize an input audio file
2. run local transcription
3. align timestamps when supported
4. enrich with diarization when available
5. export canonical JSON plus derived TXT and Markdown

Transcript completion is the primary success condition. Alignment and diarization are fail-soft enhancements.

## Planned Stack

- Python 3.10+
- `faster-whisper`
- `WhisperX`
- `pyannote.audio`
- Windows with NVIDIA CUDA support

## Initial Layout

- `src/local_stt_diarization/` - application package
- `docs/` - setup, usage, and troubleshooting documentation
- `examples/` - example commands and non-sensitive fixtures
- `config/` - sample configuration files when they become necessary
- `scripts/` - local helper scripts
- `tests/` - automated tests
- `output/` - generated artifacts, ignored by Git

## Current Status

Project boundary and packaging baseline are in place. Pipeline implementation is intentionally not part of this initial setup task.
