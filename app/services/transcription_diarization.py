import os
from typing import Any


def diarization_enabled() -> bool:
    value = os.getenv("TRANSCRIPTION_DIARIZATION", "false").strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(
        "TRANSCRIPTION_DIARIZATION doit être true/false, 1/0, yes/no ou on/off."
    )


def apply_diarization(segments: list[dict[str, Any]]) -> dict[str, Any]:
    """Normalise les locuteurs fournis par le moteur de transcription."""
    if not diarization_enabled():
        return {"segments": segments, "speakers": [], "status": "DISABLED"}

    speaker_names: dict[str, str] = {}
    diarized_segments: list[dict[str, Any]] = []
    for segment in segments:
        speaker = segment.get("speaker")
        if not isinstance(speaker, str) or not speaker.strip():
            diarized_segments.append(segment)
            continue
        speaker_key = speaker.strip()
        speaker_name = speaker_names.setdefault(
            speaker_key, f"SPEAKER_{len(speaker_names):02d}"
        )
        diarized_segments.append({**segment, "speaker": speaker_name})

    speakers = sorted(set(speaker_names.values()))
    return {
        "segments": diarized_segments,
        "speakers": speakers,
        "status": "APPLIED" if speakers else "UNAVAILABLE",
    }
