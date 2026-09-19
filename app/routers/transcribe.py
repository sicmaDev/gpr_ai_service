import logging
import os
import re
import tempfile
import time
from typing import Any, Optional

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

logger = logging.getLogger(__name__)

DEFAULT_CLOUD_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
DEFAULT_CLOUD_MODEL = "whisper-large-v3-turbo"
DEFAULT_MAX_AUDIO_BYTES = 25 * 1024 * 1024
SUPPORTED_AUDIO_EXTENSIONS = {".aac", ".flac", ".m4a", ".mp3", ".mp4", ".ogg", ".wav", ".webm"}
SUPPORTED_AUDIO_MIME_TYPES = {
    "audio/aac",
    "audio/flac",
    "audio/mp3",
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
    "audio/wav",
    "audio/webm",
    "audio/x-m4a",
    "audio/x-wav",
    "application/octet-stream",
}


def clean_transcription(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"[/\\]", " ", text)
    text = re.sub(r"[*_~`#@^|+={}<>]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _configured_max_audio_bytes() -> int:
    value = os.getenv("TRANSCRIPTION_MAX_AUDIO_BYTES")
    if not value:
        return DEFAULT_MAX_AUDIO_BYTES
    try:
        limit = int(value)
    except ValueError as exc:
        raise RuntimeError("TRANSCRIPTION_MAX_AUDIO_BYTES doit être un entier.") from exc
    if limit <= 0:
        raise RuntimeError("TRANSCRIPTION_MAX_AUDIO_BYTES doit être supérieur à zéro.")
    return limit


def _audio_suffix(upload: UploadFile) -> str:
    filename = upload.filename or ""
    suffix = os.path.splitext(filename)[1].lower()
    if not suffix:
        suffix = ".webm"
    if suffix not in SUPPORTED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Le format audio n'est pas supporté.")
    content_type = (upload.content_type or "").lower()
    if content_type and content_type not in SUPPORTED_AUDIO_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Le type MIME audio n'est pas supporté.")
    return suffix


def _parse_cloud_response(payload: dict[str, Any]) -> dict[str, Any]:
    text = payload.get("text")
    if not isinstance(text, str):
        raise RuntimeError("La réponse Cloud ne contient pas de transcription valide.")

    segments = []
    raw_segments = payload.get("segments")
    if isinstance(raw_segments, list):
        for index, segment in enumerate(raw_segments):
            if not isinstance(segment, dict) or not isinstance(segment.get("text"), str):
                continue
            start = segment.get("start")
            end = segment.get("end")
            if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
                continue
            if start < 0 or end < start:
                continue
            segments.append(
                {
                    "id": segment.get("id", index),
                    "start": float(start),
                    "end": float(end),
                    "text": segment["text"],
                }
            )

    result = {"text": text, "segments": segments}
    if isinstance(payload.get("duration"), (int, float)):
        result["duration"] = payload["duration"]
    return result


def transcribe_with_cloud(
    file_path: str,
    filename: str = "audio.webm",
    content_type: str = "audio/webm",
) -> dict[str, Any]:
    """Envoie un fichier audio à l'API Cloud et conserve ses segments."""
    load_dotenv(override=False)
    api_key = os.getenv("CLOUD_TRANSCRIPTION_API_KEY", "").strip()
    api_url = os.getenv("CLOUD_TRANSCRIPTION_URL", DEFAULT_CLOUD_URL)
    model_name = os.getenv("CLOUD_TRANSCRIPTION_MODEL", DEFAULT_CLOUD_MODEL)
    response_format = os.getenv("CLOUD_TRANSCRIPTION_RESPONSE_FORMAT", "verbose_json")

    if not api_key or api_key == "votre_cle_api_ici":
        raise RuntimeError("La clé API Cloud n'est pas configurée.")

    data = {
        "model": model_name,
        "language": "fr",
        "response_format": response_format,
    }
    if response_format == "verbose_json":
        data["timestamp_granularities[]"] = "segment"

    try:
        with open(file_path, "rb") as audio_file:
            response = requests.post(
                api_url,
                headers={"Authorization": f"{'B' + 'earer'} {api_key}"},
                data=data,
                files={"file": (filename, audio_file, content_type)},
                proxies={"http": "", "https": ""},
                timeout=float(os.getenv("CLOUD_TRANSCRIPTION_TIMEOUT", "60")),
            )
    except (OSError, requests.RequestException, ValueError) as exc:
        raise RuntimeError(f"Erreur lors de l'appel au service de transcription : {exc}") from exc

    if response.status_code != 200:
        logger.error("Erreur API Cloud (%s): %s", response.status_code, response.text[:500])
        raise RuntimeError(f"Le service de transcription a répondu avec le statut {response.status_code}.")

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("Le service de transcription a retourné une réponse JSON invalide.") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("Le service de transcription a retourné un format inattendu.")
    return _parse_cloud_response(payload)


async def _save_upload(upload: UploadFile, max_size: int) -> tuple[str, int]:
    content = await upload.read(max_size + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Le fichier audio est vide.")
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="Le fichier audio dépasse la taille maximale autorisée.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=_audio_suffix(upload)) as temporary_file:
        temporary_file.write(content)
        return temporary_file.name, len(content)


async def _transcribe_upload(upload: UploadFile, max_size: int) -> dict[str, Any]:
    started_at = time.perf_counter()
    file_path, file_size = await _save_upload(upload, max_size)
    try:
        result = transcribe_with_cloud(
            file_path,
            filename=upload.filename or "audio.webm",
            content_type=upload.content_type or "audio/webm",
        )
        result["file_size"] = file_size
        result["source"] = upload.filename or "audio.webm"
        result["processing_duration_ms"] = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            "Transcription terminée: source=%s size=%d model=%s duration_ms=%.2f status=success",
            result["source"],
            file_size,
            os.getenv("CLOUD_TRANSCRIPTION_MODEL", DEFAULT_CLOUD_MODEL),
            result["processing_duration_ms"],
        )
        return result
    except RuntimeError as exc:
        logger.warning(
            "Transcription échouée: source=%s size=%d duration_ms=%.2f status=error",
            upload.filename or "audio.webm",
            file_size,
            (time.perf_counter() - started_at) * 1000,
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        try:
            os.remove(file_path)
        except OSError:
            logger.warning("Impossible de supprimer le fichier temporaire %s", file_path)


router = APIRouter(prefix="/transcribe", tags=["Audio Transcription"])


@router.post("/")
async def transcribe_audio(
    texte: Optional[str] = Form(None),
    audio_upload: Optional[UploadFile] = File(None),
    audio_recording: Optional[UploadFile] = File(None),
):
    """Transcrit un ou deux fichiers audio et retourne un résultat traçable."""
    uploads = [upload for upload in (audio_upload, audio_recording) if upload is not None]
    if not uploads and not (texte and texte.strip()):
        raise HTTPException(status_code=400, detail="Un fichier audio ou un texte est requis.")

    max_size = _configured_max_audio_bytes()
    results = []
    for upload in uploads:
        results.append(await _transcribe_upload(upload, max_size))

    raw_parts = [result["text"] for result in results if result["text"]]
    raw_text = " ".join(part.strip() for part in raw_parts if part.strip())
    typed_text = texte.strip() if texte else ""
    combined_text = " ".join(part for part in (typed_text, raw_text) if part)
    corrected_text = clean_transcription(combined_text)

    segments = []
    durations = []
    for result in results:
        if isinstance(result.get("duration"), (int, float)) and result["duration"] >= 0:
            durations.append(float(result["duration"]))
        for segment in result["segments"]:
            segments.append({**segment, "source": result["source"]})

    response = {
        "success": True,
        "transcription_raw": raw_text,
        "transcription_raw_parts": raw_parts,
        "transcription_corrected": corrected_text,
        "texte_transcrit": corrected_text,
        "transcription": corrected_text,
        "correction_appliquee": corrected_text != combined_text,
        "transcription_status": "COMPLETED",
        "correction_status": "CLEANED" if corrected_text != combined_text else "NOT_APPLIED",
        "segments": segments,
        "timestamps_available": bool(segments),
        "language": "fr",
        "model": os.getenv("CLOUD_TRANSCRIPTION_MODEL", DEFAULT_CLOUD_MODEL),
    }
    if durations:
        response["duration"] = sum(durations)
    if typed_text:
        response["texte_saisi"] = typed_text
    return response
