"""Derived exporters built on top of the canonical transcript contract."""

from __future__ import annotations

import json
from pathlib import Path

from .transcript_contract import PartialTranscriptDocument, TranscriptDocument


def render_json(document: TranscriptDocument) -> str:
    """Render the canonical machine-readable artifact."""

    return json.dumps(document.to_dict(), ensure_ascii=False, indent=2)


def render_partial_json(document: PartialTranscriptDocument) -> str:
    """Render an in-progress checkpoint artifact."""

    return json.dumps(document.to_dict(), ensure_ascii=False, indent=2)


def render_txt(document: TranscriptDocument) -> str:
    """Render plain text from the same canonical segments and full text."""

    document.validate()
    return document.full_text


def render_markdown(document: TranscriptDocument) -> str:
    """Render a human-readable Markdown view without changing the source contract."""

    document.validate()

    lines = [
        "# Transcript",
        "",
        f"- Source: `{document.source.filename}`",
        f"- Language: `{document.source.detected_language or 'unknown'}`",
        f"- Duration seconds: `{document.source.duration_seconds if document.source.duration_seconds is not None else 'unknown'}`",
        "",
        "## Segments",
        "",
    ]

    for segment in document.segments:
        timestamp = f"[{segment.start_seconds:.2f}s - {segment.end_seconds:.2f}s]"
        speaker = f" **{segment.speaker}:**" if segment.speaker else ""
        lines.append(f"- {timestamp}{speaker} {segment.text}")

    if document.warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in document.warnings:
            lines.append(f"- `{warning.stage}` / `{warning.code}`: {warning.message}")

    return "\n".join(lines)


def write_exports(document: TranscriptDocument, output_dir: Path, stem: str) -> dict[str, Path]:
    """Write JSON, TXT, and Markdown artifacts from the canonical document."""

    output_dir.mkdir(parents=True, exist_ok=True)
    targets = {
        "json": output_dir / f"{stem}.json",
        "txt": output_dir / f"{stem}.txt",
        "md": output_dir / f"{stem}.md",
    }
    targets["json"].write_text(render_json(document), encoding="utf-8")
    targets["txt"].write_text(render_txt(document), encoding="utf-8")
    targets["md"].write_text(render_markdown(document), encoding="utf-8")
    return targets


def write_partial_checkpoint(
    document: PartialTranscriptDocument,
    output_dir: Path,
    stem: str,
) -> Path:
    """Write an in-progress checkpoint artifact under a dedicated location."""

    checkpoint_dir = output_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    target = checkpoint_dir / f"{stem}.json"
    target.write_text(render_partial_json(document), encoding="utf-8")
    return target
