import re
from typing import Any


_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in _SENTENCE_BOUNDARY.split(text.strip()) if part.strip()]


def structure_transcription(
    text: str,
    segments: list[dict[str, Any]] | None = None,
    *,
    max_paragraph_chars: int = 600,
) -> dict[str, Any]:
    """Organise le texte sans le résumer ni modifier son contenu."""
    if max_paragraph_chars <= 0:
        raise ValueError("max_paragraph_chars doit être supérieur à zéro.")

    normalized = text.strip()
    valid_segments = [
        segment
        for segment in (segments or [])
        if isinstance(segment, dict) and isinstance(segment.get("text"), str)
    ]
    paragraphs: list[dict[str, Any]] = []
    current_parts: list[str] = []
    current_segments: list[dict[str, Any]] = []
    current_length = 0

    def flush() -> None:
        if not current_parts:
            return
        paragraph_text = " ".join(current_parts).strip()
        paragraph: dict[str, Any] = {
            "index": len(paragraphs),
            "text": paragraph_text,
            "sentences": _sentences(paragraph_text),
        }
        if current_segments:
            paragraph["segment_ids"] = [
                segment["id"] for segment in current_segments if "id" in segment
            ]
            starts = [segment["start"] for segment in current_segments if isinstance(segment.get("start"), (int, float))]
            ends = [segment["end"] for segment in current_segments if isinstance(segment.get("end"), (int, float))]
            if starts:
                paragraph["start"] = min(starts)
            if ends:
                paragraph["end"] = max(ends)
        paragraphs.append(paragraph)
        current_parts.clear()
        current_segments.clear()

    for segment in valid_segments:
        segment_text = segment["text"].strip()
        if not segment_text:
            continue
        extra_length = len(segment_text) + (1 if current_parts else 0)
        if current_parts and current_length + extra_length > max_paragraph_chars:
            flush()
            current_length = 0
        current_parts.append(segment_text)
        current_segments.append(segment)
        current_length += len(segment_text) + (1 if len(current_parts) > 1 else 0)
    flush()

    if not paragraphs and normalized:
        parts: list[str] = []
        current = ""
        for sentence in _sentences(normalized):
            candidate = f"{current} {sentence}".strip()
            if current and len(candidate) > max_paragraph_chars:
                parts.append(current)
                current = sentence
            else:
                current = candidate
        if current:
            parts.append(current)
        paragraphs = [
            {"index": index, "text": paragraph, "sentences": _sentences(paragraph)}
            for index, paragraph in enumerate(parts)
        ]

    return {
        "text": normalized,
        "paragraphs": paragraphs,
        "paragraph_count": len(paragraphs),
        "sentence_count": sum(len(paragraph["sentences"]) for paragraph in paragraphs),
        "word_count": len(normalized.split()) if normalized else 0,
        "character_count": len(normalized),
    }
