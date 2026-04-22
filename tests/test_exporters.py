import shutil
import unittest
from pathlib import Path

from local_stt_diarization.config import ExportOptions
from local_stt_diarization.exporters import write_exports
from local_stt_diarization.transcript_contract import Segment, SourceMetadata, build_transcript_document


class ExporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = Path(__file__).resolve().parent / "_tmp_exporters"
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True)

    def tearDown(self) -> None:
        if self.workspace.exists():
            shutil.rmtree(self.workspace)

    def test_write_exports_keeps_json_mandatory(self) -> None:
        document = build_transcript_document(
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

        targets = write_exports(
            document,
            self.workspace,
            "sample",
            export_options=ExportOptions(write_txt=False, write_md=False),
        )

        self.assertEqual(set(targets), {"json"})
        self.assertTrue((self.workspace / "sample.json").exists())
        self.assertFalse((self.workspace / "sample.txt").exists())
        self.assertFalse((self.workspace / "sample.md").exists())
