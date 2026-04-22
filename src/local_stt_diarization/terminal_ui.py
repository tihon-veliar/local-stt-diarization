"""Guided terminal prompts for human-operated runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .audio import SUPPORTED_AUDIO_EXTENSIONS, ensure_output_dir, validate_input_audio
from .config import ExportOptions, FeatureFlags, RuntimeConfig, SpeakerConfig

try:
    import questionary
    from rich.console import Console
    from rich.panel import Panel
except ImportError as exc:  # pragma: no cover
    questionary = None
    Console = None
    Panel = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


GuidedPreset = Literal["fast", "full", "safe_cpu", "custom"]
SpeakerMode = Literal["none", "auto", "exact", "range"]

DEFAULT_MODEL = "large-v3"
DEFAULT_GPU_DEVICE = "cuda"
DEFAULT_GPU_COMPUTE_TYPE = "float16"
DEFAULT_CPU_DEVICE = "cpu"
DEFAULT_CPU_COMPUTE_TYPE = "int8"


@dataclass(slots=True)
class GuidedSelection:
    """Collected operator choices before they are mapped into runtime config."""

    input_path: Path
    output_dir: Path
    preset: GuidedPreset
    language: str | None = None
    speaker_mode: SpeakerMode = "auto"
    expected_speakers: int | None = None
    min_speakers: int | None = None
    max_speakers: int | None = None
    write_txt: bool = True
    write_md: bool = True
    transcription_model: str | None = None
    device: str | None = None
    compute_type: str | None = None
    enable_alignment: bool | None = None


def run_guided_wizard(project_root: Path) -> RuntimeConfig:
    """Prompt for guided-mode choices and return the resulting runtime config."""

    _ensure_prompt_dependencies()

    console = Console()
    input_dir = project_root / "input"
    output_root = project_root / "output"
    input_candidates = list_input_candidates(input_dir)
    if not input_candidates:
        input_dir.mkdir(parents=True, exist_ok=True)
        output_root.mkdir(parents=True, exist_ok=True)
        raise RuntimeError(
            f"No supported audio files were found in {input_dir}. Place a .wav, .mp3, or .m4a file there and retry."
        )

    console.print(
        Panel.fit(
            "Guided mode configures the same transcript-first pipeline as the raw CLI.\n"
            "Canonical JSON stays mandatory. TXT and Markdown remain optional adjacent exports.",
            title="local-stt-diarization",
        )
    )

    input_path = _prompt_input_file(input_candidates)
    default_output_dir = output_root / input_path.stem
    output_dir = _prompt_output_dir(default_output_dir)
    preset = _prompt_preset()
    language = _prompt_language()
    speaker_mode, expected_speakers, min_speakers, max_speakers = _prompt_speaker_mode(preset)
    write_txt, write_md = _prompt_export_options()

    selection = GuidedSelection(
        input_path=input_path,
        output_dir=output_dir,
        preset=preset,
        language=language,
        speaker_mode=speaker_mode,
        expected_speakers=expected_speakers,
        min_speakers=min_speakers,
        max_speakers=max_speakers,
        write_txt=write_txt,
        write_md=write_md,
    )
    if _should_open_advanced_settings(preset):
        selection = _apply_advanced_overrides(selection)

    config = build_runtime_config_from_guided_selection(selection)
    console.print(_build_summary_panel(config))
    if not questionary.confirm("Start processing with this configuration?", default=True).ask():
        raise RuntimeError("Guided run cancelled before processing started.")
    return config


def list_input_candidates(input_dir: Path) -> list[Path]:
    """Return supported top-level files from input/ without recursive discovery."""

    if not input_dir.exists():
        return []
    return sorted(
        [
            path.resolve()
            for path in input_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
        ],
        key=lambda path: path.name.lower(),
    )


def build_runtime_config_from_guided_selection(selection: GuidedSelection) -> RuntimeConfig:
    """Translate approved guided-mode choices into the canonical runtime config."""

    config = _config_for_preset(selection)

    if selection.speaker_mode == "none":
        config.features.enable_diarization = False
        config.speaker = SpeakerConfig()
    elif selection.speaker_mode == "auto":
        config.features.enable_diarization = True
        config.speaker = SpeakerConfig()
    elif selection.speaker_mode == "exact":
        config.features.enable_diarization = True
        config.speaker = SpeakerConfig(expected_speakers=selection.expected_speakers)
    elif selection.speaker_mode == "range":
        config.features.enable_diarization = True
        config.speaker = SpeakerConfig(
            min_speakers=selection.min_speakers,
            max_speakers=selection.max_speakers,
        )
    else:
        raise ValueError(f"Unsupported speaker mode: {selection.speaker_mode}")

    config.exports = ExportOptions(write_txt=selection.write_txt, write_md=selection.write_md)
    config.validate()
    return config


def _config_for_preset(selection: GuidedSelection) -> RuntimeConfig:
    features = FeatureFlags(enable_alignment=True, enable_diarization=True)
    device = DEFAULT_GPU_DEVICE
    compute_type = DEFAULT_GPU_COMPUTE_TYPE
    model = DEFAULT_MODEL

    if selection.preset == "fast":
        features.enable_diarization = False
    elif selection.preset == "full":
        pass
    elif selection.preset == "safe_cpu":
        device = DEFAULT_CPU_DEVICE
        compute_type = DEFAULT_CPU_COMPUTE_TYPE
        features.enable_alignment = False
        features.enable_diarization = False
    elif selection.preset == "custom":
        pass
    else:
        raise ValueError(f"Unsupported guided preset: {selection.preset}")

    config = RuntimeConfig(
        input_path=validate_input_audio(selection.input_path),
        output_dir=ensure_output_dir(selection.output_dir),
        language=selection.language,
        transcription_model=selection.transcription_model or model,
        compute_type=selection.compute_type or compute_type,
        device=selection.device or device,
        features=features,
        speaker=SpeakerConfig(),
        exports=ExportOptions(write_txt=selection.write_txt, write_md=selection.write_md),
    )

    if selection.enable_alignment is not None:
        config.features.enable_alignment = selection.enable_alignment
    return config


def _prompt_input_file(input_candidates: list[Path]) -> Path:
    choice = questionary.select(
        "Choose an input file from input/:",
        choices=[questionary.Choice(title=path.name, value=path) for path in input_candidates],
    ).ask()
    if choice is None:
        raise RuntimeError("Guided run cancelled while choosing an input file.")
    return choice


def _prompt_output_dir(default_output_dir: Path) -> Path:
    answer = questionary.text("Output directory:", default=str(default_output_dir)).ask()
    if answer is None:
        raise RuntimeError("Guided run cancelled while choosing the output directory.")
    return Path(answer).expanduser()


def _prompt_preset() -> GuidedPreset:
    choice = questionary.select(
        "Choose a run preset:",
        choices=[
            questionary.Choice("Fast transcript", value="fast"),
            questionary.Choice("Full transcript + diarization", value="full"),
            questionary.Choice("Safe CPU / troubleshooting", value="safe_cpu"),
            questionary.Choice("Custom", value="custom"),
        ],
        default="full",
    ).ask()
    if choice is None:
        raise RuntimeError("Guided run cancelled while choosing the preset.")
    return choice


def _prompt_language() -> str | None:
    asked = questionary.select(
        "Choose language:",
        choices=[
            questionary.Choice("Auto detect", value="auto"),
            questionary.Choice("English (en)", value="en"),
            questionary.Choice("Russian (ru)", value="ru"),
        ],
        default="auto",
    ).ask()
    if asked is None:
        raise RuntimeError("Guided run cancelled while choosing the language.")
    return None if asked == "auto" else asked


def _prompt_speaker_mode(
    preset: GuidedPreset,
) -> tuple[SpeakerMode, int | None, int | None, int | None]:
    if preset in {"fast", "safe_cpu"}:
        return ("none", None, None, None)

    mode = questionary.select(
        "Choose speaker behavior:",
        choices=[
            questionary.Choice("No diarization", value="none"),
            questionary.Choice("Auto detect", value="auto"),
            questionary.Choice("Exact speaker count", value="exact"),
            questionary.Choice("Speaker range", value="range"),
        ],
        default="auto",
    ).ask()
    if mode is None:
        raise RuntimeError("Guided run cancelled while choosing speaker behavior.")

    if mode == "exact":
        expected = _prompt_int("Exact speaker count:", minimum=1)
        return ("exact", expected, None, None)
    if mode == "range":
        minimum = _prompt_int("Minimum speaker count:", minimum=1)
        maximum = _prompt_int("Maximum speaker count:", minimum=minimum)
        return ("range", None, minimum, maximum)
    return (mode, None, None, None)


def _prompt_export_options() -> tuple[bool, bool]:
    selections = questionary.checkbox(
        "Choose adjacent exports. JSON stays enabled automatically.",
        choices=[
            questionary.Choice("TXT", value="txt", checked=True),
            questionary.Choice("Markdown", value="md", checked=True),
        ],
    ).ask()
    if selections is None:
        raise RuntimeError("Guided run cancelled while choosing export formats.")
    return ("txt" in selections, "md" in selections)


def _should_open_advanced_settings(preset: GuidedPreset) -> bool:
    if preset != "custom":
        return False
    decision = questionary.confirm(
        "Open advanced settings?",
        default=True,
    ).ask()
    if decision is None:
        raise RuntimeError("Guided run cancelled while choosing the advanced-settings branch.")
    return bool(decision)


def _apply_advanced_overrides(selection: GuidedSelection) -> GuidedSelection:
    model = questionary.text("Transcription model:", default=selection.transcription_model or DEFAULT_MODEL).ask()
    if model is None:
        raise RuntimeError("Guided run cancelled while editing the model setting.")

    default_device = selection.device or (
        DEFAULT_CPU_DEVICE if selection.preset == "safe_cpu" else DEFAULT_GPU_DEVICE
    )
    device = questionary.select(
        "Inference device:",
        choices=[
            questionary.Choice("CUDA", value="cuda"),
            questionary.Choice("CPU", value="cpu"),
        ],
        default=default_device,
    ).ask()
    if device is None:
        raise RuntimeError("Guided run cancelled while choosing the device.")

    default_compute_type = selection.compute_type or (
        DEFAULT_CPU_COMPUTE_TYPE if device == "cpu" else DEFAULT_GPU_COMPUTE_TYPE
    )
    compute_type = questionary.text("Compute type:", default=default_compute_type).ask()
    if compute_type is None:
        raise RuntimeError("Guided run cancelled while editing the compute type.")

    enable_alignment = questionary.confirm(
        "Enable alignment?",
        default=(selection.preset != "safe_cpu"),
    ).ask()
    if enable_alignment is None:
        raise RuntimeError("Guided run cancelled while choosing alignment behavior.")

    return GuidedSelection(
        input_path=selection.input_path,
        output_dir=selection.output_dir,
        preset=selection.preset,
        language=selection.language,
        speaker_mode=selection.speaker_mode,
        expected_speakers=selection.expected_speakers,
        min_speakers=selection.min_speakers,
        max_speakers=selection.max_speakers,
        write_txt=selection.write_txt,
        write_md=selection.write_md,
        transcription_model=model.strip() or DEFAULT_MODEL,
        device=device,
        compute_type=compute_type.strip() or default_compute_type,
        enable_alignment=bool(enable_alignment),
    )


def _prompt_int(message: str, *, minimum: int) -> int:
    while True:
        answer = questionary.text(message).ask()
        if answer is None:
            raise RuntimeError("Guided run cancelled while entering a numeric value.")
        stripped = answer.strip()
        if not stripped.isdigit():
            print(f"Enter a whole number >= {minimum}.")
            continue
        value = int(stripped)
        if value < minimum:
            print(f"Enter a whole number >= {minimum}.")
            continue
        return value


def _build_summary_panel(config: RuntimeConfig):
    formats = ", ".join(config.exports.selected_formats())
    diarization_label = "enabled" if config.features.enable_diarization else "disabled"
    alignment_label = "enabled" if config.features.enable_alignment else "disabled"
    speaker_hint = _describe_speaker_config(config.speaker)
    body = (
        f"Input: {config.input_path}\n"
        f"Output: {config.output_dir}\n"
        f"Language: {config.language or 'auto'}\n"
        f"Model: {config.transcription_model}\n"
        f"Device: {config.device}\n"
        f"Compute type: {config.compute_type}\n"
        f"Alignment: {alignment_label}\n"
        f"Diarization: {diarization_label}\n"
        f"Speaker hints: {speaker_hint}\n"
        f"Exports: {formats}"
    )
    return Panel.fit(body, title="Run Summary")


def _describe_speaker_config(speaker: SpeakerConfig) -> str:
    if speaker.expected_speakers is not None:
        return f"exact={speaker.expected_speakers}"
    if speaker.min_speakers is not None or speaker.max_speakers is not None:
        return f"range={speaker.min_speakers}-{speaker.max_speakers}"
    return "none"


def _ensure_prompt_dependencies() -> None:
    if IMPORT_ERROR is not None:
        raise RuntimeError(
            "Guided mode requires the 'rich' and 'questionary' packages. Reinstall the project dependencies and retry."
        ) from IMPORT_ERROR
