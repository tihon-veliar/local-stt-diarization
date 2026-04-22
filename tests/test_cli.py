import argparse
import shutil
import unittest
from pathlib import Path

from local_stt_diarization.cli import StagePlan, build_runtime_config_from_args


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = Path(__file__).resolve().parent / "_tmp_cli"
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True)

    def tearDown(self) -> None:
        if self.workspace.exists():
            shutil.rmtree(self.workspace)

    def test_stage_plan_marks_disabled_optional_stages_as_skipped(self) -> None:
        input_path = self.workspace / "sample.wav"
        input_path.write_bytes(b"wav")

        args = argparse.Namespace(
            input_path=str(input_path),
            output_dir=str(self.workspace / "output"),
            language=None,
            model="large-v3",
            device="cpu",
            compute_type="int8",
            disable_alignment=True,
            disable_diarization=True,
            speakers=None,
            min_speakers=None,
            max_speakers=None,
            no_txt=False,
            no_md=False,
        )
        config = build_runtime_config_from_args(args)
        plan = StagePlan(("prepare", "transcription", "alignment", "diarization", "export"))

        lines = plan.render_lines(config)

        self.assertIn("  3/5 alignment [skipped] - disabled by configuration", lines)
        self.assertIn("  4/5 diarization [skipped] - disabled by configuration", lines)

    def test_build_runtime_config_from_args_respects_export_toggles(self) -> None:
        input_path = self.workspace / "sample.wav"
        input_path.write_bytes(b"wav")

        args = argparse.Namespace(
            input_path=str(input_path),
            output_dir=str(self.workspace / "output"),
            language="en",
            model="large-v3",
            device="cuda",
            compute_type="float16",
            disable_alignment=False,
            disable_diarization=False,
            speakers=None,
            min_speakers=None,
            max_speakers=None,
            no_txt=True,
            no_md=False,
        )

        config = build_runtime_config_from_args(args)

        self.assertFalse(config.exports.write_txt)
        self.assertTrue(config.exports.write_md)
