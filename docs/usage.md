# Usage Guide

## Scope

This CLI currently supports one local audio file per run and exports canonical JSON plus derived TXT and Markdown artifacts.

For long runs, the agreed next-step behavior is:

- the CLI should show visible stage progress while the process is active
- the pipeline may write a checkpoint-style partial transcript artifact before final export completes

The current runtime surface is the raw CLI. The approved next operator-facing contract also defines a guided terminal mode for normal human-operated runs without changing the underlying pipeline behavior.

## Approved Guided Flow

When guided mode is implemented, the normal operator sequence should be:

1. Choose one supported audio file from the top level of `input/`.
2. Accept or adjust the default output target under `output/<input-stem>/`.
3. Choose a run preset.
4. Choose language as `auto`, `en`, or `ru`.
5. Choose speaker behavior.
6. Review export formats with `JSON` always enabled.
7. Optionally open advanced settings for low-level overrides.
8. Review the run summary and start processing.

Guided mode must stay a thin wrapper over the same runtime path used by the raw CLI.

## Preset Contract

- `Fast transcript` keeps alignment enabled and diarization disabled for a quicker transcript-first run.
- `Full transcript + diarization` keeps both optional enrichment stages enabled.
- `Safe CPU / troubleshooting` forces CPU-safe execution and disables optional enrichment stages to isolate environment issues.
- `Custom` starts from the full transcript baseline and opens the advanced branch for low-level overrides.

## Speaker Contract

- `No diarization` disables diarization entirely.
- `Auto detect` enables diarization without explicit speaker-count hints.
- `Exact speaker count` enables diarization and sets one exact speaker count.
- `Speaker range` enables diarization and sets minimum plus maximum speaker counts.

## Export Contract

- `JSON` remains mandatory and cannot be deselected.
- `TXT` starts enabled and may be deselected.
- `Markdown` starts enabled and may be deselected.
- Export choices must not suppress the canonical JSON artifact.

## Basic Command

```bash
local-stt-diarization "C:/recordings/session01.m4a" --output-dir output
```

## Common Inputs

- `.wav`
- `.mp3`
- `.m4a`

Compressed inputs are normalized before transcription. Normalized intermediates are written under the chosen output directory.

## Common Options

- `--output-dir output`
- `--language en`
- `--model large-v3`
- `--device cuda`
- `--compute-type float16`
- `--disable-alignment`
- `--disable-diarization`
- `--speakers 2`
- `--min-speakers 2 --max-speakers 4`

## Example Commands

Transcribe with default settings:

```bash
local-stt-diarization "C:/recordings/session01.m4a" --output-dir output
```

Force CPU while debugging environment setup:

```bash
local-stt-diarization "C:/recordings/session01.m4a" --output-dir output --device cpu --compute-type int8
```

Disable optional enrichment stages to isolate transcription:

```bash
local-stt-diarization "C:/recordings/session01.m4a" --output-dir output --disable-alignment --disable-diarization
```

Provide an exact speaker hint:

```bash
local-stt-diarization "C:/recordings/interview.wav" --output-dir output --speakers 2
```

Constrain automatic speaker estimation:

```bash
local-stt-diarization "C:/recordings/meeting.wav" --output-dir output --min-speakers 2 --max-speakers 4
```

## Output Files

Each successful run writes:

- `<stem>.json` as the canonical contract
- `<stem>.txt` as a plain-text rendering
- `<stem>.md` as a Markdown rendering

The JSON artifact is the source of truth for downstream tooling. TXT and Markdown are derived from the same in-memory document.

For long-running processing, the follow-up contract also allows an in-progress checkpoint artifact under a dedicated location such as:

- `output/checkpoints/<stem>.json`

That checkpoint artifact is operational state, not a replacement for the completed canonical JSON.

## Runtime Visibility Expectations

The CLI should not stay completely silent during long processing. The agreed progress model is:

- print the planned stage sequence before execution starts
- show stable stage counters such as `1/5`
- announce stage start
- announce stage completion
- surface degraded optional stages honestly
- show simple forward movement counters when the current pipeline can do so safely
- keep disabled optional stages visible as `skipped` entries rather than removing them from the total plan

Expected visible stage names:

- `prepare`
- `transcription`
- `alignment`
- `diarization`
- `export`

## Interpreting Warnings

- `alignment_unavailable` or `alignment_failed` means timestamps came from the transcription layer rather than alignment.
- `diarization_disabled`, `diarization_unavailable`, or `diarization_failed` means transcript export succeeded without reliable speaker labeling.
- `speaker_assignment_ambiguous` means the merge logic intentionally left some segment speakers unset.

Warnings should be treated as signal about optional-stage quality, not as proof that the transcript itself failed.

If a partial checkpoint exists during a run, do not treat it as proof that the run completed successfully. The final completed JSON remains the authoritative finished artifact.

## Recommended Operating Order

1. Validate the pipeline on a short non-sensitive recording.
2. Confirm exported JSON shape and warnings.
3. Try a realistic single-file recording.
4. Add diarization only after the base transcription path behaves acceptably on the machine.

## Current MVP Boundaries

- Single-file local CLI only
- No batch orchestration
- No cloud workflow
- No downstream LLM integration in this repository
