import unittest

from local_stt_diarization.transcript_contract import (
    Segment,
    SourceMetadata,
    build_partial_transcript_document,
)


class TranscriptContractTests(unittest.TestCase):
    def test_partial_checkpoint_tracks_active_stage_separately(self) -> None:
        document = build_partial_transcript_document(
            run_state="in_progress",
            last_completed_stage="prepare",
            active_stage="transcription",
            source=SourceMetadata(path="input/sample.wav", filename="sample.wav", extension=".wav"),
            segments=[
                Segment(
                    id="seg-001",
                    start_seconds=0.0,
                    end_seconds=1.0,
                    text="hello world",
                )
            ],
        )

        payload = document.to_dict()

        self.assertEqual(payload["run_state"], "in_progress")
        self.assertEqual(payload["last_completed_stage"], "prepare")
        self.assertEqual(payload["active_stage"], "transcription")
