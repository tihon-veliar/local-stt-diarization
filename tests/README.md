# Test And Fixture Notes

## Current State

This repository does not yet contain committed automated tests for the pipeline stages. The current validation baseline is documentation-driven plus local smoke evidence.

## Recommended Fixture Shape

Use non-sensitive local files that cover:

- short single-speaker audio for smoke testing
- longer single-speaker audio for runtime and completeness checks
- at least one multi-speaker recording when diarization is being evaluated
- noisy or overlapping speech only when you are explicitly checking conservative speaker-label behavior

## What To Record During Manual Validation

- command used
- environment notes such as CPU or CUDA
- whether first-run downloads occurred
- whether visible stage progress appeared during the run
- whether a checkpoint artifact appeared under `output/checkpoints/`
- stage warnings emitted
- whether canonical JSON, TXT, and Markdown were all written
- whether `speaker` fields were omitted conservatively when overlap was ambiguous

## Do Not Commit

- real recordings
- sensitive transcripts
- large generated outputs

Keep fixtures local and summarize findings in documentation instead.
