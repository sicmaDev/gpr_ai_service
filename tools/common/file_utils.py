"""
Utilitaires de gestion sécurisée des fichiers pour la gouvernance IA GPR.
Garantit le principe strict de non-écrasement des fichiers générés (logs, rapports, exports JSON).
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union


def get_run_timestamp() -> str:
    """Retourne un horodatage compact et standardisé UTC pour les runs : YYYYMMDD_HHMMSS."""
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def get_unique_filepath(
    base_path: Union[str, Path],
    timestamp: Optional[str] = None,
    force_timestamp: bool = False,
) -> Path:
    """
    Retourne un chemin de fichier unique garanti sans écrasement.
    
    Règles :
    1. Si force_timestamp est True, le timestamp est systématiquement injecté avant l'extension.
    2. Si le fichier cible existe déjà sur le disque (même si un nom statique était demandé),
       un timestamp ou un compteur incrémental est ajouté pour interdire TOUT écrasement.
    """
    p = Path(base_path)
    ts = timestamp or get_run_timestamp()
    parent = p.parent
    stem = p.stem
    suffix = p.suffix

    if force_timestamp:
        target = parent / f"{stem}_{ts}{suffix}"
    else:
        target = p

    # Si le fichier cible n'existe pas encore, on peut l'utiliser
    if not target.exists():
        return target

    # Si le fichier cible existe déjà, interdiction absolue d'écraser : on cherche un nom libre
    candidate = parent / f"{stem}_{ts}{suffix}"
    if not candidate.exists():
        return candidate

    counter = 1
    while True:
        candidate = parent / f"{stem}_{ts}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def safe_write_text(
    target_path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    timestamp: Optional[str] = None,
    force_timestamp: bool = False,
) -> Path:
    """
    Écrit du contenu texte dans un fichier en garantissant l'absence totale d'écrasement.
    Crée automatiquement les répertoires parents si nécessaire.
    Retourne le chemin effectif du fichier créé.
    """
    final_path = get_unique_filepath(target_path, timestamp=timestamp, force_timestamp=force_timestamp)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(content, encoding=encoding)
    return final_path
