import logging
import json
import os
import unicodedata
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from typing import Any, Optional

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from app.services.vocabulary_selector import load_vocabulary, parse_bool, select_vocabulary
from app.services.transcription_correction import correct_transcription
from app.services.transcription_diarization import apply_diarization
from app.services.transcription_structure import structure_transcription
from app.services.transcription_storage import build_transcription_storage_payload

logger = logging.getLogger(__name__)

DEFAULT_CLOUD_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
DEFAULT_CLOUD_MODEL = "whisper-large-v3-turbo"
DEFAULT_MAX_AUDIO_BYTES = 25 * 1024 * 1024
DEFAULT_AUDIO_SAMPLE_RATE = 16000
VOCABULARY_PATH = Path(__file__).resolve().parents[1] / "data" / "transcription_vocabulary.json"
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


def _log_block(title: str, **details: Any) -> None:
    def label(value: str) -> str:
        return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")

    lines = [f"========== {label(title)} =========="]
    lines.extend(f"{label(str(key))}: {value}" for key, value in details.items())
    lines.append("=" * len(lines[0]))
    logger.info("\n%s", "\n".join(lines))


def _env_bool(name: str, default: bool) -> bool:
    return parse_bool(os.getenv(name), default=default)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} doit être un nombre.") from exc


def _format_words(words: list[dict[str, Any]]) -> str:
    if not words:
        return "<non retournés par le fournisseur>"
    return "\n".join(
        f"  {index}. texte={word.get('text', '')!r} "
        f"start={word.get('start', '?')} end={word.get('end', '?')} "
        f"confiance={word.get('confidence', '<non fournie>')}"
        for index, word in enumerate(words, start=1)
    )


def load_transcription_vocabulary() -> dict[str, Any]:
    return load_vocabulary()


def build_vocabulary_prompt(vocabulary: dict[str, Any]) -> str:
    terms = list(vocabulary.get("global_terms", []))
    for category in vocabulary.get("categories", {}).values():
        if isinstance(category, list):
            terms.extend(category)
    return "Termes bancaires français à reconnaître : " + ", ".join(
        dict.fromkeys(term for term in terms if isinstance(term, str))
    )


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


def _second_pass_enabled() -> bool:
    return parse_bool(os.getenv("TRANSCRIPTION_SECOND_PASS"), default=True)


def _vocabulary_limits() -> dict[str, int]:
    limits = {key: int(os.getenv(env_name, default)) for key, (env_name, default) in {
        "max_terms": ("TRANSCRIPTION_VOCABULARY_MAX_TERMS", 50),
        "max_chars": ("TRANSCRIPTION_VOCABULARY_MAX_CHARS", 1200),
    }.items()}
    if any(value <= 0 for value in limits.values()):
        raise RuntimeError("Les limites du vocabulaire doivent être positives.")
    return limits


def _preprocessing_enabled() -> bool:
    return os.getenv("TRANSCRIPTION_AUDIO_PREPROCESSING", "true").lower() in {"1", "true", "yes", "on"}


def _preprocess_audio(file_path: str) -> tuple[str, bool]:
    """Normalise l'audio avec FFmpeg sans modifier le fichier original."""
    if not _preprocessing_enabled():
        _log_block("PRÉTRAITEMENT AUDIO", statut="DÉSACTIVÉ")
        return file_path, False

    ffmpeg_path = shutil.which(os.getenv("FFMPEG_BINARY", "ffmpeg"))
    if not ffmpeg_path:
        logger.warning("FFmpeg indisponible: transcription effectuée avec l'audio original.")
        return file_path, False

    _log_block(
        "PRÉTRAITEMENT AUDIO - DÉBUT",
        format="WAV mono",
        fréquence=f"{DEFAULT_AUDIO_SAMPLE_RATE} Hz",
        filtre="highpass 80 Hz | lowpass 12000 Hz | loudnorm",
    )

    processed_path = f"{file_path}.normalized.wav"
    command = [
        ffmpeg_path,
        "-y",
        "-i",
        file_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(DEFAULT_AUDIO_SAMPLE_RATE),
        "-af",
        "highpass=f=80,lowpass=f=12000,loudnorm=I=-16:TP=-1.5:LRA=11",
        processed_path,
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=float(os.getenv("TRANSCRIPTION_AUDIO_PREPROCESSING_TIMEOUT", "120")),
            check=False,
        )
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        logger.warning("Prétraitement audio indisponible: %s", exc)
        return file_path, False

    if completed.returncode != 0 or not os.path.exists(processed_path):
        logger.warning(
            "Prétraitement audio échoué (code=%s): %s",
            completed.returncode,
            completed.stderr[-500:],
        )
        try:
            os.remove(processed_path)
        except OSError:
            pass
        return file_path, False

    _log_block("PRÉTRAITEMENT AUDIO - FIN", statut="SUCCÈS", fichier="audio.normalized.wav")
    return processed_path, True


def _audio_suffix(upload: UploadFile) -> str:
    filename = upload.filename or ""
    suffix = os.path.splitext(filename)[1].lower()
    if not suffix:
        suffix = ".webm"
    if suffix not in SUPPORTED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Le format audio n'est pas supporté.")
    content_type = (upload.content_type or "").lower().split(";", 1)[0].strip()
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
            for metric in ("avg_logprob", "no_speech_prob", "compression_ratio", "temperature"):
                if isinstance(segment.get(metric), (int, float)):
                    segments[-1][metric] = segment[metric]
            words = []
            raw_words = segment.get("words")
            if isinstance(raw_words, list):
                for word in raw_words:
                    if not isinstance(word, dict) or not isinstance(word.get("word"), str):
                        continue
                    word_start = word.get("start")
                    word_end = word.get("end")
                    if (
                        not isinstance(word_start, (int, float))
                        or not isinstance(word_end, (int, float))
                        or word_start < 0
                        or word_end < word_start
                    ):
                        continue
                    parsed_word = {
                        "text": word["word"],
                        "start": float(word_start),
                        "end": float(word_end),
                    }
                    if isinstance(word.get("probability"), (int, float)):
                        parsed_word["confidence"] = float(word["probability"])
                    words.append(parsed_word)
            if words:
                segments[-1]["words"] = words
            if isinstance(segment.get("speaker"), str) and segment["speaker"].strip():
                segments[-1]["speaker"] = segment["speaker"].strip()

    result = {
        "text": text,
        "segments": segments,
        "words": [word for segment in segments for word in segment.get("words", [])],
    }
    if isinstance(payload.get("duration"), (int, float)):
        result["duration"] = payload["duration"]
    return result


def transcribe_with_cloud(
    file_path: str,
    filename: str = "audio.webm",
    content_type: str = "audio/webm",
    vocabulary_terms: list[str] | None = None,
) -> dict[str, Any]:
    """Envoie un fichier audio à l'API Cloud et conserve ses segments."""
    load_dotenv(override=False)
    api_key = os.getenv("CLOUD_TRANSCRIPTION_API_KEY", "").strip()
    api_url = os.getenv("CLOUD_TRANSCRIPTION_URL", DEFAULT_CLOUD_URL)
    model_name = os.getenv("CLOUD_TRANSCRIPTION_MODEL", DEFAULT_CLOUD_MODEL)
    response_format = os.getenv("CLOUD_TRANSCRIPTION_RESPONSE_FORMAT", "verbose_json")
    word_timestamps = _env_bool("TRANSCRIPTION_WORD_TIMESTAMPS", default=True)
    temperature = _env_float("TRANSCRIPTION_ASR_TEMPERATURE", default=0.0)

    if not api_key or api_key == "votre_cle_api_ici":
        raise RuntimeError("La clé API Cloud n'est pas configurée.")

    data = {
        "model": model_name,
        "language": "fr",
        "response_format": response_format,
        "temperature": str(temperature),
    }
    prompt = ""
    if vocabulary_terms:
        prompt = "Termes bancaires français à reconnaître : " + ", ".join(vocabulary_terms)
        data["prompt"] = prompt
    if response_format == "verbose_json":
        data["timestamp_granularities[]"] = "segment"
        if word_timestamps:
            data["timestamp_granularities[]"] = ["segment", "word"]

    _log_block(
        "ASR - CONFIGURATION",
        modèle=model_name,
        format_réponse=response_format,
        langue="fr",
        température=temperature,
        timestamps_mot=word_timestamps,
        granularités=data.get("timestamp_granularities[]", "<non disponibles>"),
        prompt=prompt or "<aucun>",
        fichier=filename,
    )
    _log_block(
        "ASR - APPEL",
        modèle=model_name,
        fichier=filename,
        chemin_audio=file_path,
        timeout=f"{os.getenv('CLOUD_TRANSCRIPTION_TIMEOUT', '60')} s",
    )
    request_started = time.perf_counter()
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
        logger.exception(
            "[TRANSCRIPTION] Appel STT Cloud interrompu après %.2f s.",
            time.perf_counter() - request_started,
        )
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
    parsed = _parse_cloud_response(payload)
    segment_details = []
    for index, segment in enumerate(parsed["segments"]):
        segment_details.append(
            "\n".join(
                [
                    f"SEGMENT {index}",
                    f"start: {segment['start']}",
                    f"end: {segment['end']}",
                    f"text: {segment['text']}",
                    f"avg_logprob: {segment.get('avg_logprob', '<non fourni>')}",
                    f"no_speech_prob: {segment.get('no_speech_prob', '<non fourni>')}",
                    f"compression_ratio: {segment.get('compression_ratio', '<non fourni>')}",
                    "mots:",
                    _format_words(segment.get("words", [])),
                ]
            )
        )
    _log_block(
        "ASR - RÉPONSE",
        statut_http=response.status_code,
        durée_appel=f"{time.perf_counter() - request_started:.2f} s",
        caractères=len(parsed["text"]),
        segments=len(parsed["segments"]),
        durée_audio=parsed.get("duration", "inconnue"),
        timestamps_mot=bool(parsed["words"]),
        détail_segments="\n\n".join(segment_details) or "<aucun segment>",
        transcription=parsed["text"],
    )
    return parsed


async def _save_upload(upload: UploadFile, max_size: int) -> tuple[str, int]:
    _log_block(
        "UPLOAD - VALIDATION",
        nom=upload.filename or "<sans nom>",
        MIME=upload.content_type or "<absent>",
        limite=f"{max_size} octets",
    )
    content = await upload.read(max_size + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Le fichier audio est vide.")
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="Le fichier audio dépasse la taille maximale autorisée.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=_audio_suffix(upload)) as temporary_file:
        temporary_file.write(content)
        _log_block(
            "UPLOAD - FICHIER TEMPORAIRE",
            taille=f"{len(content)} octets",
            extension=os.path.splitext(temporary_file.name)[1],
        )
        return temporary_file.name, len(content)


async def _transcribe_upload(
    upload: UploadFile,
    max_size: int,
    *,
    front_context: str | None = None,
    claim_category: str | None = None,
    product: str | None = None,
    reason: str | None = None,
    front_text: str = "",
    second_pass: bool = True,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    upload_name = upload.filename or "audio.webm"
    _log_block(
        "FICHIER - DÉBUT",
        nom=upload_name,
        taille_max=f"{max_size} octets",
        seconde_passe=second_pass,
    )
    file_path, file_size = await _save_upload(upload, max_size)
    transcription_path = file_path
    preprocessed = False
    try:
        transcription_path, preprocessed = _preprocess_audio(file_path)
        vocabulary = load_vocabulary()
        limits = _vocabulary_limits()
        _log_block(
            "VOCABULAIRE - CHARGEMENT",
            catégories=len(vocabulary.get("categories", {})),
            limites=limits,
            contexte_front=bool(front_context or claim_category or product or reason or front_text),
        )
        first_selection = select_vocabulary(
            vocabulary,
            context=front_context,
            claim_category=claim_category,
            product=product,
            reason=reason,
            text=front_text,
            **limits,
        )
        _log_block(
            "VOCABULAIRE - PASSE 1",
            catégories=[item["name"] for item in first_selection["categories"]],
            termes=len(first_selection["terms"]),
            caractères=first_selection["chars"],
            confiance=first_selection["confidence"],
            termes_sélectionnés=first_selection["terms"],
        )
        result = transcribe_with_cloud(
            transcription_path,
            filename="audio.normalized.wav" if preprocessed else (upload.filename or "audio.webm"),
            content_type="audio/wav" if preprocessed else (upload.content_type or "audio/webm"),
            vocabulary_terms=first_selection["terms"],
        )
        pass1 = result
        _log_block(
            "ASR - PASSE 1",
            segments=len(result["segments"]),
            mots=len(result.get("words", [])),
            timestamps_mot=bool(result.get("words")),
            transcription=result["text"],
        )
        pass2 = None
        second_selection = first_selection
        if second_pass:
            second_selection = select_vocabulary(
                vocabulary,
                context=front_context,
                claim_category=claim_category,
                product=product,
                reason=reason,
                text=result["text"],
                **limits,
            )
            pass2 = transcribe_with_cloud(
                transcription_path,
                filename="audio.normalized.wav" if preprocessed else (upload.filename or "audio.webm"),
                content_type="audio/wav" if preprocessed else (upload.content_type or "audio/webm"),
                vocabulary_terms=second_selection["terms"],
            )
            result = pass2
            _log_block(
                "ASR - PASSE 2",
                catégories=[item["name"] for item in second_selection["categories"]],
                termes_sélectionnés=second_selection["terms"],
                segments=len(result["segments"]),
                mots=len(result.get("words", [])),
                timestamps_mot=bool(result.get("words")),
                transcription=result["text"],
            )
        result["file_size"] = file_size
        result["source"] = upload.filename or "audio.webm"
        result["audio_preprocessed"] = preprocessed
        result["transcription_pass1_raw"] = pass1["text"]
        result["transcription_pass2_raw"] = pass2["text"] if pass2 else None
        result["transcription_passes"] = 2 if pass2 else 1
        result["second_pass_enabled"] = second_pass
        result["vocabulary_selection_pass1"] = first_selection
        result["vocabulary_selection_pass2"] = second_selection if pass2 else None
        result["processing_duration_ms"] = round((time.perf_counter() - started_at) * 1000, 2)
        _log_block(
            "FICHIER - FIN",
            source=result["source"],
            taille=f"{file_size} octets",
            passes=result["transcription_passes"],
            prétraité=preprocessed,
            segments=len(result["segments"]),
            durée=f"{result['processing_duration_ms']:.2f} ms",
            statut="SUCCÈS",
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
        if transcription_path != file_path:
            try:
                os.remove(transcription_path)
            except OSError:
                logger.warning("Impossible de supprimer l'audio prétraité %s", transcription_path)
        try:
            os.remove(file_path)
        except OSError:
            logger.warning("Impossible de supprimer le fichier temporaire %s", file_path)


router = APIRouter(prefix="/transcribe", tags=["Audio Transcription"])


@router.post("/")
async def transcribe_audio(
    texte: Optional[str] = Form(None),
    vocabulary_context: Optional[str] = Form(None),
    claim_category: Optional[str] = Form(None),
    product: Optional[str] = Form(None),
    reason: Optional[str] = Form(None),
    audio_upload: Optional[UploadFile] = File(None),
    audio_recording: Optional[UploadFile] = File(None),
):
    """Transcrit un ou deux fichiers audio et retourne un résultat traçable."""
    request_id = uuid.uuid4().hex[:12]
    _log_block(
        f"REQUÊTE {request_id} - RÉCEPTION",
        uploads=sum(upload is not None for upload in (audio_upload, audio_recording)),
        texte_présent=bool(texte and texte.strip()),
        seconde_passe_env=os.getenv("TRANSCRIPTION_SECOND_PASS", "<par défaut>"),
    )
    uploads = [upload for upload in (audio_upload, audio_recording) if upload is not None]
    if not uploads and not (texte and texte.strip()):
        raise HTTPException(status_code=400, detail="Un fichier audio ou un texte est requis.")

    max_size = _configured_max_audio_bytes()
    try:
        second_pass = _second_pass_enabled()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    _log_block(
        f"REQUÊTE {request_id} - CONFIGURATION",
        taille_max=f"{max_size} octets",
        seconde_passe=second_pass,
    )
    results = []
    for upload in uploads:
        try:
            results.append(
                await _transcribe_upload(
                    upload,
                    max_size,
                    front_context=vocabulary_context,
                    claim_category=claim_category,
                    product=product,
                    reason=reason,
                    front_text=texte or "",
                    second_pass=second_pass,
                )
            )
            _log_block(
                f"REQUÊTE {request_id} - FICHIER TRAITÉ",
                numéro=f"{len(results)}/{len(uploads)}",
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    raw_parts = [result["text"] for result in results if result["text"]]
    raw_text = " ".join(part.strip() for part in raw_parts if part.strip())
    typed_text = texte.strip() if texte else ""
    combined_text = " ".join(part for part in (typed_text, raw_text) if part)
    cleaned_text = clean_transcription(combined_text)
    vocabulary_terms = []
    for result in results:
        selection = result.get("vocabulary_selection_pass2") or result.get("vocabulary_selection_pass1") or {}
        vocabulary_terms.extend(selection.get("terms", []))
    correction = correct_transcription(
        cleaned_text,
        vocabulary_terms=list(dict.fromkeys(vocabulary_terms)),
    )
    corrected_text = correction["text"]
    _log_block(
        f"REQUÊTE {request_id} - CORRECTION IA",
        statut=correction["status"],
        appliquée=correction["applied"],
        proposition=correction.get("proposed_text", "<aucune>"),
        motif_relecture=correction.get("review_reason", "<aucun>"),
        transcription=corrected_text,
    )

    segments = []
    durations = []
    for result in results:
        if isinstance(result.get("duration"), (int, float)) and result["duration"] >= 0:
            durations.append(float(result["duration"]))
        for segment in result["segments"]:
            segments.append({**segment, "source": result["source"]})
    diarization = apply_diarization(segments)
    segments = diarization["segments"]
    _log_block(
        f"REQUÊTE {request_id} - STRUCTURATION",
        segments=len(segments),
        durée=sum(durations) if durations else "inconnue",
        diarisation=diarization["status"],
        locuteurs=len(diarization["speakers"]),
    )

    response = {
        "success": True,
        "transcription_raw": raw_text,
        "transcription_raw_parts": raw_parts,
        "transcription_cleaned": cleaned_text,
        "transcription_corrected": corrected_text,
        "texte_transcrit": corrected_text,
        "transcription": corrected_text,
        "correction_appliquee": corrected_text != combined_text,
        "transcription_status": "COMPLETED",
        "transcription_mode": "TWO_PASS" if second_pass else "SINGLE_PASS",
        "transcription_passes": 2 if second_pass else 1,
        "second_pass_enabled": second_pass,
        "correction_status": "CLEANED" if corrected_text != combined_text else "NOT_APPLIED",
        "correction_ai_status": correction["status"],
        "correction_ai_error": correction.get("error"),
        "correction_proposed_text": correction.get("proposed_text"),
        "correction_review_reason": correction.get("review_reason"),
        "segments": segments,
        "timestamps_available": bool(segments),
        "speakers": diarization["speakers"] or None,
        "diarization_status": diarization["status"],
        "diarization_enabled": diarization["status"] != "DISABLED",
        "language": "fr",
        "model": os.getenv("CLOUD_TRANSCRIPTION_MODEL", DEFAULT_CLOUD_MODEL),
    }
    if durations:
        response["duration"] = sum(durations)
    if typed_text:
        response["texte_saisi"] = typed_text
    structure = structure_transcription(corrected_text, segments)
    response["transcription_structuree"] = structure
    response["paragraphes"] = structure["paragraphs"]
    response["structure_status"] = "COMPLETED"
    response["metadata"] = {
        "language": response["language"],
        "duration": response.get("duration"),
        "word_count": structure["word_count"],
        "character_count": structure["character_count"],
        "paragraph_count": structure["paragraph_count"],
        "sentence_count": structure["sentence_count"],
    }
    response["transcription_pass1_raw"] = " ".join(
        result.get("transcription_pass1_raw", result.get("text", ""))
        for result in results
        if result.get("transcription_pass1_raw", result.get("text"))
    )
    response["transcription_pass2_raw"] = " ".join(
        result["transcription_pass2_raw"] for result in results if result.get("transcription_pass2_raw")
    ) or None
    response["vocabulary_selection"] = [
        result.get("vocabulary_selection_pass2")
        or result.get("vocabulary_selection_pass1")
        or {}
        for result in results
    ]
    response["storage_payload"] = build_transcription_storage_payload(
        response,
        audio_original=response.get("source"),
    )
    _log_block(
        f"REQUÊTE {request_id} - RÉSUMÉ",
        statut="COMPLETED",
        modèle=response["model"],
        passes_asr=response["transcription_passes"],
        segments=len(segments),
        mots=len(response.get("transcription_pass1_raw", "").split()),
        correction_ia=correction["status"],
        diarisation=diarization["status"],
    )
    _log_block(
        f"REQUÊTE {request_id} - FIN",
        statut="COMPLETED",
        caractères_bruts=len(raw_text),
        caractères_corrigés=len(corrected_text),
        durée_totale=f"{sum(result.get('processing_duration_ms', 0) for result in results):.2f} ms",
        transcription_brute=raw_text,
        transcription_corrigée=corrected_text,
    )
    return response
