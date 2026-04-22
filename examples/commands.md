# Example Commands

## Default Run

```bash
local-stt-diarization "C:/recordings/session01.m4a" --output-dir output
```

## CPU Debug Run

```bash
local-stt-diarization "C:/recordings/session01.m4a" --output-dir output --device cpu --compute-type int8
```

## Transcription-Only Isolation

```bash
local-stt-diarization "C:/recordings/session01.m4a" --output-dir output --disable-alignment --disable-diarization
```

## Exact Speaker Hint

```bash
local-stt-diarization "C:/recordings/interview.wav" --output-dir output --speakers 2
```

## Bounded Speaker Estimation

```bash
local-stt-diarization "C:/recordings/meeting.wav" --output-dir output --min-speakers 2 --max-speakers 4
```
