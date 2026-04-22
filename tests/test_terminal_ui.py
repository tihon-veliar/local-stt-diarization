import shutil
import unittest
from pathlib import Path

from local_stt_diarization.terminal_ui import (
    GuidedSelection,
    build_runtime_config_from_guided_selection,
    list_input_candidates,
)


class TerminalUiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = Path(__file__).resolve().parent / "_tmp_terminal_ui"
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True)

    def tearDown(self) -> None:
        if self.workspace.exists():
            shutil.rmtree(self.workspace)

    def test_list_input_candidates_uses_top_level_only(self) -> None:
        input_dir = self.workspace / "input"
        nested_dir = input_dir / "nested"
        nested_dir.mkdir(parents=True)
        top_level = input_dir / "clip.wav"
        nested = nested_dir / "nested.mp3"
        ignored = input_dir / "notes.txt"
        top_level.write_bytes(b"wav")
        nested.write_bytes(b"mp3")
        ignored.write_text("ignore me", encoding="utf-8")

        candidates = list_input_candidates(input_dir)

        self.assertEqual(candidates, [top_level.resolve()])

    def test_build_runtime_config_from_guided_selection_maps_safe_cpu_contract(self) -> None:
        input_path = self.workspace / "sample.wav"
        input_path.write_bytes(b"wav")
        output_dir = self.workspace / "output" / "sample"

        config = build_runtime_config_from_guided_selection(
            GuidedSelection(
                input_path=input_path,
                output_dir=output_dir,
                preset="safe_cpu",
                language="en",
                speaker_mode="none",
                write_txt=False,
                write_md=True,
            )
        )

        self.assertEqual(config.device, "cpu")
        self.assertEqual(config.compute_type, "int8")
        self.assertFalse(config.features.enable_alignment)
        self.assertFalse(config.features.enable_diarization)
        self.assertFalse(config.exports.write_txt)
        self.assertTrue(config.exports.write_md)

    def test_build_runtime_config_from_guided_selection_maps_speaker_range(self) -> None:
        input_path = self.workspace / "sample.wav"
        input_path.write_bytes(b"wav")
        output_dir = self.workspace / "output" / "sample"

        config = build_runtime_config_from_guided_selection(
            GuidedSelection(
                input_path=input_path,
                output_dir=output_dir,
                preset="full",
                speaker_mode="range",
                min_speakers=2,
                max_speakers=4,
            )
        )

        self.assertTrue(config.features.enable_diarization)
        self.assertEqual(config.speaker.min_speakers, 2)
        self.assertEqual(config.speaker.max_speakers, 4)
