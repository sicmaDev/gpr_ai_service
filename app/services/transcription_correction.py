import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

_PROTECTED_PATTERNS = (
    r"\b\d[\d\s.,/-]*\b",
    r"\b(?:pas|jamais|aucun|aucune|sans|ne|n')\b",
    r"\b(?:franc|fcfa|xaf|euro|euros|f|f cfa)\b",
    r"\b(?:jour|jours|semaine|semaines|mois|an|ans|année|années)\b",
)


def _enabled() -> bool:
    value = os.getenv("TRANSCRIPTION_AI_CORRECTION", "true").strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError("TRANSCRIPTION_AI_CORRECTION doit être true/false, 1/0, yes/no ou on/off.")


def _protected_markers(text: str) -> list[str]:
    markers = []
    for pattern in _PROTECTED_PATTERNS:
        markers.extend(match.group(0).lower().strip() for match in re.finditer(pattern, text, re.IGNORECASE))
    return markers


def _needs_review(original: str, corrected: str) -> str | None:
    original_markers = _protected_markers(original)
    corrected_lower = corrected.lower()
    missing = [marker for marker in original_markers if marker not in corrected_lower]
    if missing:
        return f"Informations protégées absentes après correction: {', '.join(dict.fromkeys(missing))}"
    return None


def correct_transcription(text: str, vocabulary_terms: list[str] | None = None) -> dict[str, Any]:
    if not text.strip():
        logger.info("[TRANSCRIPTION][CORRECTION] Texte vide: correction ignorée.")
        return {"text": text, "status": "EMPTY", "applied": False}
    if not _enabled():
        logger.info("[TRANSCRIPTION][CORRECTION] Correction IA désactivée.")
        return {"text": text, "status": "DISABLED", "applied": False}

    try:
        from app.services.llm_service import DEFAULT_MODEL, ollama_client

        if not DEFAULT_MODEL or not os.getenv("LLM_BASE_URL"):
            raise RuntimeError("La configuration LLM de correction est absente.")

        terms = ", ".join(vocabulary_terms or [])
        logger.info(
            "[TRANSCRIPTION][CORRECTION] Appel LLM: modèle=%s termes=%d caractères_entrée=%d.",
            DEFAULT_MODEL,
            len(vocabulary_terms or []),
            len(text),
        )
        system_prompt = (
            "Tu corriges une transcription française bancaire. Retourne uniquement le texte corrigé. "
            "Corrige ponctuation, majuscules, fautes évidentes et termes métier connus. "
            "Ne résume pas, n'ajoute rien, ne supprime aucune information et conserve les incertitudes. "
            "Si un passage est incompréhensible, conserve-le au lieu de l'inventer."
        )
        user_prompt = f"Vocabulaire autorisé : {terms}\n\nTranscription à corriger :\n{text}"
        response = ollama_client.chat(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0},
        )
        corrected = response["message"]["content"].strip()
        if not corrected:
            raise RuntimeError("Le modèle de correction a retourné un texte vide.")
        review_reason = _needs_review(text, corrected)
        if review_reason:
            logger.warning("[TRANSCRIPTION][CORRECTION] Validation requise: %s", review_reason)
            return {
                "text": text,
                "status": "REVIEW_REQUIRED",
                "applied": False,
                "proposed_text": corrected,
                "review_reason": review_reason,
            }
        logger.info(
            "[TRANSCRIPTION][CORRECTION] Réponse LLM: caractères_sortie=%d modification=%s.",
            len(corrected),
            corrected != text,
        )
        return {
            "text": corrected,
            "status": "APPLIED",
            "applied": corrected != text,
        }
    except (KeyError, RuntimeError, TypeError, ValueError, OSError) as exc:
        logger.warning("Correction IA indisponible: %s", exc)
        return {"text": text, "status": "FALLBACK_RAW", "applied": False, "error": str(exc)}
