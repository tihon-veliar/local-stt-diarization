import unittest
from pathlib import Path

from local_stt_diarization.merge import build_document
from local_stt_diarization.transcript_contract import TranscriptWarning
from local_stt_diarization.transcribe import TranscriptionResult, TranscriptionSegmentData


class MergeTests(unittest.TestCase):
    def test_build_document_falls_back_to_transcription_segments_when_alignment_is_none(self) -> None:
        transcription = TranscriptionResult(
            language="en",
            segments=[
                TranscriptionSegmentData(
                    id="seg-001",
                    start_seconds=0.0,
                    end_seconds=1.5,
                    text="hello world",
                    confidence=0.9,
                )
            ],
            raw_segments=[
                {
                    "id": "seg-001",
                    "start": 0.0,
                    "end": 1.5,
                    "text": "hello world",
                }
            ],
        )
        warnings = [
            TranscriptWarning(
                code="alignment_failed",
                stage="alignment",
                message="Alignment failed; transcript exported with transcription timestamps.",
            )
        ]

        document = build_document(
            source_path=Path("input/sample.wav"),
            transcription=transcription,
            aligned_segments=None,
            diarization_turns=None,
            warnings=warnings,
            stage_statuses=[],
            duration_seconds=1.5,
        )

        self.assertEqual(len(document.segments), 1)
        self.assertEqual(document.segments[0].start_seconds, 0.0)
        self.assertEqual(document.segments[0].end_seconds, 1.5)
        self.assertEqual(document.segments[0].text, "hello world")
