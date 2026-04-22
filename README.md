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

Project boundary and packaging baseline are in place. The transcript contract and runtime configuration baseline are also defined so later pipeline stages can target one shared model.

## Canonical Contract

The canonical machine-readable output is JSON with:

- source metadata
- full transcript text
- ordered transcript segments
- optional warnings for degraded optional stages
- coarse stage status records for support and debugging

TXT and Markdown are derived views of the same canonical transcript document. See `docs/transcript_contract.md` for the schema and exporter rules.

## Installation

Create a Python 3.10+ environment inside this repository and install the package:

```bash
pip install -e .
```

The CLI expects local access to:

- `ffmpeg` for normalization of `.mp3` and `.m4a`
- `faster-whisper` for mandatory transcription
- `WhisperX` for optional alignment
- `pyannote.audio` for optional diarization

## CLI Usage

Happy path example:

```bash
local-stt-diarization "C:/recordings/session01.m4a" --output-dir output
```

Useful options:

- `--language en` or `--language ru` to provide a language hint
- `--model large-v3` to choose the transcription model
- `--device cuda` to target the GPU
- `--compute-type float16` for GPU-friendly inference
- `--disable-alignment` to skip WhisperX when debugging the environment
- `--disable-diarization` to skip pyannote when debugging the environment
- `--speakers 2` to provide an exact speaker hint
- `--min-speakers 2 --max-speakers 4` to constrain automatic speaker estimation

The command writes:

- `output/<stem>.json`
- `output/<stem>.txt`
- `output/<stem>.md`

If alignment is unavailable or fails, the transcript still exports with warnings and transcription timestamps.

If diarization is unavailable, weak, or fails, the transcript still exports and speaker labels are omitted where confidence is not strong enough to justify them.
