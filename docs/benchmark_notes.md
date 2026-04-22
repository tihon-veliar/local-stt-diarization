# Benchmark And Acceptance Notes

## Intent

This document records only observed validation and known gaps. It does not promise generalized throughput, memory, or diarization quality numbers that have not been measured in this repository.

## Observed Local Artifact

An ignored smoke-output artifact exists under `output/test-smoke/` with exported JSON, TXT, Markdown, and normalized audio output.

Observed from `output/test-smoke/out/sample.json`:

- source file: `sample.wav`
- detected language: `en`
- duration: `1.0` second
- transcript export succeeded
- alignment was disabled for that smoke run
- diarization was not recorded in the stage statuses for that artifact

This confirms the canonical export path has been exercised at least once on a tiny sample input, but it is not a substitute for a realistic long-form acceptance pass.

## Current Measurement Gaps

The following have not been recorded in version-controlled benchmark notes yet:

- end-to-end runtime for realistic long recordings
- peak RAM usage
- peak VRAM usage
- diarization usefulness on overlapping or noisy multi-speaker audio
- transcript completeness against curated reference text

## Acceptance Status

Current acceptance evidence is limited to:

- code inspection across transcription, alignment, diarization, merge, and export paths
- successful Python source compilation
- ignored smoke-output artifacts from a short sample run

Current acceptance is not yet a strong real-world long-form benchmark.

## Recommended Manual Acceptance Pass

When a non-sensitive realistic recording is available, capture at minimum:

- input duration and rough scenario type
- command line used
- whether first-run model download occurred
- total wall-clock runtime
- rough RAM and VRAM observations
- whether transcript export completed
- whether alignment degraded
- whether diarization labels were useful, weak, or omitted

## Fixture Handling Rule

Do not commit real recordings. If sensitive recordings are the only available source material, record only sanitized metadata and observed behavior.
