# Troubleshooting

## Transcript Export Fails Before Output

Check the mandatory path first:

- confirm the input file exists and has a supported extension
- confirm `ffmpeg` is available when using `.mp3` or `.m4a`
- verify the Python environment contains project dependencies
- try `--device cpu` if CUDA setup is still uncertain

If transcription fails, the run should fail explicitly rather than emitting a misleading transcript artifact.

## Alignment Fails But Transcript Still Exports

This is expected fail-soft behavior.

Typical responses:

- inspect warnings in stderr and in the canonical JSON
- retry with `--disable-alignment` to isolate the issue
- confirm WhisperX and its Torch dependencies import correctly

The transcript should still export using transcription timestamps.

## Diarization Fails, Returns Nothing, Or Is Too Weak

This is also expected fail-soft behavior.

Typical responses:

- retry with `--disable-diarization` to keep the transcript path moving
- verify pyannote dependencies import correctly
- set `HF_TOKEN` or `HUGGINGFACE_HUB_TOKEN` if model access requires authentication
- provide `--speakers`, or `--min-speakers` and `--max-speakers`, when the recording structure is known

If overlap is weak or competing speakers are too close, the merge logic may intentionally omit `speaker` on some transcript segments.

## Long Recording Concerns

For longer files:

- confirm sufficient free disk space for caches and normalized audio
- monitor RAM and VRAM during the first realistic run
- test transcription-only mode before enabling all optional stages
- expect first-run latency to be worse because of model downloads

This repository does not yet claim general benchmark guarantees for long recordings.

## CUDA Or Torch Issues

Common mitigation order:

1. verify the active environment is the one that received `pip install -e .`
2. test with `--device cpu`
3. re-check Torch and CUDA compatibility in that same environment
4. retry without diarization, since diarization can amplify Torch-related issues

Use troubleshooting runs to confirm behavior, not to silently relax the output contract.

## Unexpected Speaker Labels

Remember the current merge policy:

- transcript text and timestamps are primary
- speaker labels are conservative
- ambiguous overlap should leave speakers unset instead of guessing

If you need more stable diarization evaluation, compare against known fixture shapes and inspect the warnings rather than trusting labels at face value.

## Model Download Confusion

First use may spend time downloading dependencies and weights. If a run appears stalled:

- wait for the initial download to finish
- confirm cache directories are writable
- retry with transcription-only mode if you need to narrow the failing stage

Keep downloaded caches outside version control.
