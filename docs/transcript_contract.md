# Canonical Transcript Contract

## Purpose

The canonical transcript JSON is the machine-readable source of truth for the project.

- JSON is the persistent public contract.
- TXT and Markdown are derived renderings from the same in-memory document.
- Library-specific raw outputs from `faster-whisper`, WhisperX, or `pyannote.audio` must not become the stored contract.

## Design Rules

- Transcript success is mandatory for a successful run.
- Alignment and diarization are optional enrichment stages.
- Optional stage degradation must be representable without invalidating the final transcript artifact.
- The contract should stay compact enough for downstream LLM tooling without fragile post-processing.
- Runtime console progress is operational feedback for the current run, not part of the final transcript contract.
- In-progress transcript persistence is allowed for long runs, but partial artifacts must stay distinct from completed canonical exports.

## Canonical JSON Shape

```json
{
  "schema_version": "1.0",
  "created_at": "2026-04-22T08:00:00+00:00",
  "source": {
    "path": "C:/recordings/session01.m4a",
    "filename": "session01.m4a",
    "extension": ".m4a",
    "detected_language": "en",
    "duration_seconds": 2412.3
  },
  "full_text": "Full transcript text...",
  "segments": [
    {
      "id": "seg-0001",
      "start_seconds": 0.42,
      "end_seconds": 5.18,
      "text": "Hello and welcome.",
      "speaker": "SPEAKER_00",
      "confidence": 0.91
    }
  ],
  "warnings": [
    {
      "code": "diarization_unavailable",
      "stage": "diarization",
      "message": "Diarization dependency was not available; transcript exported without speaker labels."
    }
  ],
  "stage_statuses": [
    {
      "stage": "transcription",
      "status": "completed",
      "details": "Transcript generated with faster-whisper."
    },
    {
      "stage": "alignment",
      "status": "skipped",
      "details": "Alignment disabled by configuration."
    }
  ]
}
```

## Field Notes

- `schema_version`: version gate for downstream consumers.
- `created_at`: UTC ISO-8601 timestamp of artifact creation.
- `source`: stable file-level metadata that stays useful across exporters.
- `full_text`: complete transcript text derived from the segment list.
- `segments`: canonical ordered transcript units shared by all exporters.
- `warnings`: fail-soft notices for optional-stage degradation or ambiguity.
- `stage_statuses`: coarse operational record for debugging and support.

## Segment Rules

- `id`, `start_seconds`, `end_seconds`, and `text` are required.
- `speaker` is optional and may be absent when diarization is disabled, unavailable, or ambiguous.
- `confidence` is optional and should be omitted when the source value is unreliable or unavailable.
- Segments should preserve transcript completeness and timestamp integrity over aggressive speaker labeling.

## Runtime Configuration Ownership

Runtime configuration is owned by `RuntimeConfig` in `src/local_stt_diarization/config.py`.

Current supported boundaries:
- `input_path`
- `output_dir`
- `language`
- `transcription_model`
- `compute_type`
- `device`
- `features.enable_alignment`
- `features.enable_diarization`
- `speaker.expected_speakers`
- `speaker.min_speakers`
- `speaker.max_speakers`

These options are intentionally limited to single-file local CLI processing. Batch orchestration and service settings are out of scope for the MVP.

## Runtime Progress Contract

The CLI progress model for long-running local execution should be intentionally small and operational:

- emit stage-start messages
- emit stage-completion messages
- surface degraded optional stages as warnings or degraded stage outcomes
- surface simple forward-movement counters only when they are already available from the current pipeline

The visible runtime stages should be:

- `prepare`
- `transcription`
- `alignment`
- `diarization`
- `export`

This progress channel is user-facing feedback for the active process. It is not the persistent source of truth for downstream consumers.

## Partial Transcript Artifact Contract

Long runs may persist an in-progress transcript artifact before final export completes.

The agreed boundary for the follow-up implementation pass is:

- keep final canonical JSON, TXT, and Markdown as the authoritative completed-run outputs
- place in-progress artifacts under a dedicated checkpoint location such as `output/checkpoints/`
- avoid writing partial artifacts next to final outputs under confusingly similar names
- start partial persistence from the transcription layer first, with later stages enriching the completed run rather than redefining the partial artifact model

Recommended example path:

- `output/checkpoints/<stem>.json`

## Partial Artifact Rules

An in-progress artifact must be distinguishable from a completed canonical transcript.

Minimum expectations:

- explicit run-state markers such as `in_progress`, `failed`, `interrupted`, or `completed`
- explicit indication of the last completed stage
- explicit indication of the currently active stage when a checkpoint is captured mid-stage
- accumulated transcript segments so far
- updated timestamp for the current checkpoint state

Partial artifacts are for operator confidence and recoverability. They must not be presented as completed final transcript exports to downstream consumers.

## Write-Frequency Guidance

Partial persistence should balance recoverability against excessive disk churn.

Implementation guidance for the next task:

- write on meaningful transcript growth rather than every internal event
- allow writes on stage completion
- avoid overly chatty checkpoint updates when no useful transcript progress has occurred

## Warning And Degradation Rules

- If transcription fails, the run fails and no transcript artifact should be presented as successful.
- If alignment is unavailable or fails, transcript export still succeeds and a warning is recorded.
- If diarization is disabled, unavailable, weak, or fails, transcript export still succeeds and speaker labels may be partially absent.
- Warnings should describe what degraded, not overstate certainty, and remain readable to both humans and downstream tooling.

## Diarization Merge Behavior

- Diarization is applied only after transcript segments already exist.
- Speaker labels are assigned by time-overlap against each transcript segment.
- A speaker label is written only when one speaker has clearly dominant overlap for that segment.
- If overlap is weak or competing speakers are too close, the segment keeps `speaker: null` and a `speaker_assignment_ambiguous` warning may be added.
- Transcript text and timestamps take priority over aggressive speaker attribution.

## Exporter Expectations

- JSON exporter writes the canonical document unchanged.
- TXT exporter uses the canonical `full_text`.
- Markdown exporter uses the canonical segment list and warning list.
- Exporters must not inject library-specific data that does not belong to the contract.
