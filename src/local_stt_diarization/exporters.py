"""Derived exporters built on top of the canonical transcript contract."""

from __future__ import annotations

import json

from .transcript_contract import TranscriptDocument


def render_json(document: TranscriptDocument) -> str:
    """Render the canonical machine-readable artifact."""

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
