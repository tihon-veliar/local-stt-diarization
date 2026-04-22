# local-stt-diarization

Standalone local Windows CLI project for long-form conversation transcription with transcript-first reliability and optional speaker diarization enrichment.

## Project Boundary

This project intentionally lives under `sandbox/` in the parent workspace, but it is its own repository boundary and should be treated as an independent codebase.

- Work on this project inside `sandbox/local-stt-diarization/`.
- Do not fold its source files into the parent repository structure.
- Keep runtime assets, model caches, outputs, and temporary files out of version control.

## MVP Direction

The MVP is a synchronous single-file CLI pipeline:

1. validate and normalize an input audio file
2. run local transcription
3. align timestamps when supported
4. enrich with diarization when available
5. export canonical JSON plus derived TXT and Markdown

Transcript completion is the primary success condition. Alignment and diarization are fail-soft enhancements.

## Stack

- Python 3.10+
- `faster-whisper`
- `WhisperX`
- `pyannote.audio`
- `Rich`
- `questionary`
- Windows with NVIDIA CUDA support preferred for practical long-form use

## Repository Layout

- `src/local_stt_diarization/` - application package
- `docs/` - setup, usage, troubleshooting, and benchmark notes
- `examples/` - reusable command examples and non-sensitive fixtures
- `config/` - sample configuration files when they become necessary
- `scripts/` - local helper scripts
- `tests/` - automated coverage and fixture guidance
- `output/` - generated artifacts, ignored by Git

## Quick Start

1. Create and activate a Python 3.10+ environment.
2. Install the package with `pip install -e .`.
3. Ensure `ffmpeg` is available on `PATH`.
4. Provide local model download access for `faster-whisper`, WhisperX, and optionally `pyannote.audio`.
5. Run the CLI against a single recording.

Happy path example:

```bash
local-stt-diarization "C:/recordings/session01.m4a" --output-dir output
```

Guided-mode example:

```bash
local-stt-diarization --guided
```

Useful options:

- `--guided` to launch the guided terminal flow
- `--language en` or `--language ru` to provide a language hint
- `--model large-v3` to choose the transcription model
- `--device cuda` to target the GPU
- `--compute-type float16` for GPU-friendly inference
- `--disable-alignment` to skip WhisperX when debugging the environment
- `--disable-diarization` to skip pyannote when debugging the environment
- `--speakers 2` to provide an exact speaker hint
- `--min-speakers 2 --max-speakers 4` to constrain automatic speaker estimation
- `--no-txt` or `--no-md` to skip adjacent derived exports while keeping JSON mandatory

The command writes:

- `output/<stem>.json`
- `output/<stem>.txt`
- `output/<stem>.md`

For long-running runs, the follow-up contract also allows a dedicated in-progress checkpoint artifact under `output/checkpoints/`. That checkpoint state is operational only and must remain distinct from the final completed export set.

## Guided Mode

The project now supports two coordinated terminal surfaces:

- a guided terminal flow for normal human-run usage
- a raw flag-driven CLI for debugging, support, and automation

The guided flow:

- scan only top-level supported audio files under `input/`
- default each run to `output/<input-stem>/`
- offer presets for `Fast transcript`, `Full transcript + diarization`, `Safe CPU / troubleshooting`, and `Custom`
- keep `JSON` mandatory while leaving `TXT` and `Markdown` enabled by default but user-selectable
- keep full low-level override prompts behind the `Custom` branch
- end by invoking the same pipeline used by the raw CLI

The raw CLI remains the support, automation, and troubleshooting fallback.

## Behavior Summary

- Transcription is the required success path.
- Alignment may degrade without failing the run.
- Diarization may degrade, be disabled, or be unavailable without failing the run.
- Weak or ambiguous speaker overlap leaves `speaker` unset rather than overstating certainty.
- Runtime console progress is user-facing liveness feedback for the active run.
- Partial transcript checkpoints are allowed for long processing, but they are not final completed outputs.

## Documentation Map

- `docs/setup_windows_cuda.md` - Windows setup expectations and dependency notes
- `docs/usage.md` - CLI workflow and sample commands
- `docs/troubleshooting.md` - common local failure modes and recovery steps
- `docs/transcript_contract.md` - canonical JSON and exporter contract
- `docs/benchmark_notes.md` - observed validation notes and current measurement gaps
- `examples/commands.md` - copy-paste command examples
- `tests/README.md` - fixture expectations and current validation scope

## Canonical Contract

The canonical machine-readable output is JSON with:

- source metadata
- full transcript text
- ordered transcript segments
- optional warnings for degraded optional stages
- coarse stage status records for support and debugging

TXT and Markdown are derived views of the same canonical transcript document. See `docs/transcript_contract.md` for the schema and exporter rules.

## Current Validation State

The repository includes a smoke-output example under ignored `output/` artifacts, and the documentation records what has and has not been validated so far. Long-form acceptance and benchmark numbers still depend on locally available non-sensitive recordings.
