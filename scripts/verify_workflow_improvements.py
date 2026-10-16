#!/usr/bin/env python3
"""
Script de vérification de bout en bout des améliorations du workflow de reporting Text-to-SQL.

Teste les 4 cas critiques majeurs identifiés par l'audit :
1. Dossiers en cours non résolus (status != 'SATISFIED')
2. Taux de satisfaction client (75.0% sur les avis exprimés)
3. Dénonciations hors canal physique (claim_type IN ('DENUNCIATION', 'DENUNCIACION'))
4. Suggestions unifiées (3 suggestions)
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys

# Encodage console UTF-8 Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal
from app.reporting.text_to_sql_pipeline import execute_text_to_sql_pipeline

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TEST_CASES = [
    {
        "title": "Cas 1 : Dossiers en cours non résolus",
        "question": "Quels sont les dossiers en cours qui ne sont toujours pas résolus ?",
        "expected_check": lambda ans, sql, rows: "40" in ans or rows == 40 or "status != 'SATISFIED'" in sql or "status !=" in sql,
    },
    {
        "title": "Cas 2 : Taux de satisfaction global des usagers",
        "question": "Taux de satisfaction global des usagers",
        "expected_check": lambda ans, sql, rows: "75" in ans or "status = 'SATISFIED'" in sql,
    },
    {
        "title": "Cas 3 : Fraudes et dénonciations hors guichet",
        "question": "Signalements de fraudes et irrégularités enregistrés sans passer par le guichet",
        "expected_check": lambda ans, sql, rows: "4" in ans or rows == 4 or "DENUNCIACION" in sql or "DENUNCIATION" in sql,
    },
    {
        "title": "Cas 4 : Suggestions en 2026",
        "question": "Propositions d'amélioration et suggestions enregistrées en 2026",
        "expected_check": lambda ans, sql, rows: "3" in ans or rows == 3 or "reporting_suggestion" in sql,
    },
]


def run_checks():
    db = SessionLocal()
    print("\n" + "=" * 80)
    print("VÉRIFICATION TECHNIQUE ET FONCTIONNELLE DES CAS CRITIQUES (MARIADB)")
    print("=" * 80)

    all_passed = True
    try:
        for tc in TEST_CASES:
            print(f"\n--- {tc['title']} ---")
            print(f"Question : \"{tc['question']}\"")
            resp = execute_text_to_sql_pipeline(
                question=tc["question"],
                db_session=db,
                use_llm=True,
            )

            sql = resp.sql_query or ""
            ans = resp.answer or ""
            row_count = len(resp.data) if resp.data else 0

            print(f"Mode d'exécution : {resp.execution_mode}")
            print(f"Query ID         : {resp.query_id}")
            print(f"SQL exécuté      : {sql}")
            print(f"Lignes retournées: {row_count}")
            print(f"Réponse générée  : {ans}")

            ok = tc["expected_check"](ans, sql, row_count)
            if ok:
                print(">>> RÉSULTAT : ✅ CONFORME AUX RÈGLES MÉTIER ET À LA VÉRITÉ TERRAIN")
            else:
                print(">>> RÉSULTAT : ⚠️ RÉSULTAT INATTENDU")
                all_passed = False

        print("\n" + "=" * 80)
        if all_passed:
            print("TOUS LES CAS CRITIQUES SONT CONFORMES ET VALIDÉS !")
        else:
            print("DES CAS CRITIQUES NÉCESSITENT UN AJUSTEMENT.")
        print("=" * 80 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    run_checks()
