# Windows CUDA Setup

## Purpose

This project is intended for local Windows usage with GPU acceleration when available. CPU-only operation may work for small tests, but practical long-form runs are expected to benefit from CUDA.

## Required Baseline

- Windows machine with Python 3.10 or newer
- `ffmpeg` available on `PATH`
- A virtual environment dedicated to this project
- Network access for one-time model downloads

## Recommended Setup Flow

1. Install Python 3.10+.
2. Create and activate a virtual environment inside `sandbox/local-stt-diarization/`.
3. Ensure `ffmpeg` is callable from a new shell.
4. Install project dependencies with `pip install -e .`.
5. Verify that Torch, `faster-whisper`, WhisperX, and optional `pyannote.audio` import correctly in the same environment.

Example PowerShell flow:

```powershell
cd sandbox/local-stt-diarization
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

## CUDA Notes

- The project runtime defaults to `--device cuda`.
- Torch and CUDA compatibility must be resolved in the local environment before expecting GPU acceleration to work.
- If GPU setup is incomplete, use `--device cpu` for troubleshooting rather than changing project code.
- Diarization may place additional pressure on Torch and CUDA compatibility compared with transcription-only runs.

## Dependency Expectations

- `faster-whisper` is required for the core transcription stage.
- WhisperX is optional at runtime in the sense that alignment can degrade without failing export, but the package is still part of the current dependency set.
- `pyannote.audio` is optional for successful transcript export and may be disabled with CLI flags.

## Model Downloads And Local Caches

- First use may download model weights and related artifacts.
- These downloads can take noticeable time and disk space.
- Keep model caches out of version control.
- The repository `.gitignore` already excludes common cache directories such as `.cache/`, `cache/`, `models/`, `checkpoints/`, `hf-cache/`, and `huggingface/`.

## Hugging Face Token Notes

- The diarization stage checks `HF_TOKEN` and `HUGGINGFACE_HUB_TOKEN`.
- If pyannote model access requires authentication in your environment, set one of those variables before running the CLI.
- If diarization access is not available, transcript export should still succeed when diarization is disabled or when the diarization stage degrades.

## Minimum Verification Checklist

- `python --version` reports Python 3.10+
- `ffmpeg -version` works from the same shell
- `pip install -e .` completes in the project environment
- `local-stt-diarization --help` shows the CLI
- A small sample file can be processed end-to-end before attempting long recordings
