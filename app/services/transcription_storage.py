import json
from datetime import datetime, timezone
from typing import Any


STORAGE_SCHEMA_VERSION = "1.0"


def build_transcription_storage_payload(
    response: dict[str, Any],
    *,
    audio_original: str | None = None,
) -> dict[str, Any]:
    """Construit un payload stable pour la persistance côté backend."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": STORAGE_SCHEMA_VERSION,
        "audio_original": audio_original or response.get("source"),
        "transcription_raw": response.get("transcription_raw", ""),
        "transcription_corrected": response.get("transcription_corrected", ""),
        "segments_json": json.dumps(response.get("segments", []), ensure_ascii=False),
        "speakers_json": json.dumps(response.get("speakers") or [], ensure_ascii=False),
        "language": response.get("language"),
        "duration": response.get("duration"),
        "transcription_status": response.get("transcription_status", "FAILED"),
        "transcription_error": response.get("transcription_error"),
        "model_name": response.get("model"),
        "created_at": now,
        "updated_at": now,
    }
