# AGENTS.md

## Purpose

This repository is a standalone sandbox project for local speech-to-text transcription with optional speaker diarization enrichment.

The core product rule is:
- transcript generation is mandatory
- alignment is preferred when the environment supports it
- diarization is best-effort and must not block transcript output

## Working Rules

- Treat this folder as its own repository boundary.
- Keep implementation local to this project unless a change explicitly belongs in the parent workspace.
- Preserve transcript-first reliability over feature expansion.
- Keep runtime assets, model caches, output files, and temporary files out of version control.
- Prefer explicit contracts and readable code over hidden fallback behavior.

## Expected Project Shape

- `src/local_stt_diarization/` owns the application package
- `docs/` holds setup, usage, and troubleshooting material
- `tests/` holds automated coverage
- `examples/` and `config/` hold small reusable supporting artifacts

## Delivery Alignment

This project is being implemented from the parent delivery package `delivery/local_stt_diarization/`.

When continuing work:
- preserve the canonical JSON contract once it is defined
- keep diarization optional
- avoid introducing batch orchestration or service APIs in the MVP unless scope is explicitly changed
