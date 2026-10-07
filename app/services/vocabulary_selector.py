import json
from pathlib import Path
from typing import Any

VOCABULARY_PATH = Path(__file__).resolve().parents[1] / "data" / "transcription_vocabulary.json"
DEFAULT_MAX_TERMS = 50
DEFAULT_MAX_CHARS = 1200
DEFAULT_GLOBAL_TERMS = 15
DEFAULT_CONTEXT_TERMS = 25
DEFAULT_PRODUCT_TERMS = 10

CONTEXT_ALIASES = {
    "reclamation": "reclamations_service_client",
    "réclamation": "reclamations_service_client",
    "client": "reclamations_service_client",
    "carte": "cartes_paiements",
    "paiement": "cartes_paiements",
    "compte": "comptes",
    "credit": "credits",
    "crédit": "credits",
    "fraude": "securite_fraude",
    "uemoa": "uemoa_bceao",
    "bceao": "uemoa_bceao",
}


def load_vocabulary() -> dict[str, Any]:
    try:
        with VOCABULARY_PATH.open(encoding="utf-8") as vocabulary_file:
            vocabulary = json.load(vocabulary_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Le vocabulaire de transcription est indisponible ou invalide.") from exc
    if not isinstance(vocabulary, dict) or not isinstance(vocabulary.get("categories"), dict):
        raise RuntimeError("Le vocabulaire de transcription a un format invalide.")
    return vocabulary


def parse_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError("TRANSCRIPTION_SECOND_PASS doit être true/false, 1/0, yes/no ou on/off.")


def _terms_from_category(category: Any) -> list[str]:
    if isinstance(category, list):
        return [term for term in category if isinstance(term, str)]
    if isinstance(category, dict):
        terms = []
        for key in ("priority_terms", "acronyms", "related_terms", "terms"):
            values = category.get(key, [])
            if isinstance(values, list):
                terms.extend(term for term in values if isinstance(term, str))
        return terms
    return []


def _matching_categories(text: str, categories: dict[str, Any]) -> list[dict[str, Any]]:
    normalized_text = text.casefold()
    scores = []
    for name, category in categories.items():
        terms = _terms_from_category(category)
        matches = sum(1 for term in terms if term.casefold() in normalized_text)
        if matches:
            score = min(1.0, matches / 5)
            scores.append({"name": name, "score": round(score, 2), "matches": matches})
    return sorted(scores, key=lambda item: (-item["score"], item["name"]))


def select_vocabulary(
    vocabulary: dict[str, Any],
    *,
    context: str | None = None,
    claim_category: str | None = None,
    product: str | None = None,
    reason: str | None = None,
    text: str | None = None,
    max_terms: int = DEFAULT_MAX_TERMS,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> dict[str, Any]:
    categories = vocabulary["categories"]
    explicit_context = context or claim_category
    context_key = CONTEXT_ALIASES.get((explicit_context or "").strip().casefold(), (explicit_context or "").strip())
    category_scores = _matching_categories(" ".join(filter(None, (context, product, reason, text))), categories)
    selected_categories = []
    if context_key in categories:
        selected_categories.append({"name": context_key, "score": 1.0, "source": "front"})
    for item in category_scores:
        if item["name"] not in {entry["name"] for entry in selected_categories} and item["score"] >= 0.4:
            selected_categories.append({"name": item["name"], "score": item["score"], "source": "content"})
        if len(selected_categories) >= 3:
            break

    all_terms = []
    for term in vocabulary.get("global_terms", []):
        if isinstance(term, str):
            all_terms.append(("global", term))
    for item in selected_categories:
        for term in _terms_from_category(categories[item["name"]]):
            all_terms.append(("context", term))
    if product:
        all_terms.insert(0, ("product", product.strip()))

    selected = []
    seen = set()
    limits = {"global": DEFAULT_GLOBAL_TERMS, "context": DEFAULT_CONTEXT_TERMS, "product": DEFAULT_PRODUCT_TERMS}
    counts = {key: 0 for key in limits}
    total_chars = 0
    for source, term in all_terms:
        normalized = term.casefold()
        if not term.strip() or normalized in seen or counts.get(source, 0) >= limits.get(source, 0):
            continue
        addition = len(term) + (2 if selected else 0)
        if len(selected) >= max_terms or total_chars + addition > max_chars:
            break
        selected.append(term)
        seen.add(normalized)
        counts[source] = counts.get(source, 0) + 1
        total_chars += addition

    return {
        "terms": selected,
        "categories": selected_categories,
        "confidence": selected_categories[0]["score"] if selected_categories else 0.0,
        "chars": total_chars,
    }
