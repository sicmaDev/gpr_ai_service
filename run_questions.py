#!/usr/bin/env python3
"""
Script direct d'exécution automatique d'une liste de questions sur le service de reporting Text-to-SQL Gouverné.

Usage :
    python run_questions.py                          # Exécute automatiquement questions.txt
    python run_questions.py questions.txt            # Exécute un fichier de questions
    python run_questions.py "Combien de réclamations ?"  # Exécute une ou plusieurs questions directes
    python run_questions.py questions.txt --audit    # Exécute et lance immédiatement l'audit forensique
    python run_questions.py questions.txt --report rapport.md  # Génère un rapport Markdown
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time

# Encodage console UTF-8 Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from tools.common.file_utils import (
    get_run_timestamp,
    get_unique_filepath,
    safe_write_text,
)
from tools.workflow_interrogator.runner import WorkflowRunner


def generate_markdown_report(results, output_path: str, timestamp: str = None) -> Path:
    md = [

        "# Rapport d'Exécution : Interrogation du Workflow Text-to-SQL Gouverné",
        "",
        f"**Date d'exécution** : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
        f"**Nombre de questions traitées** : {len(results)}  ",
        "",
        "## Synthèse des Résultats",
        "",
        "| N° | Question | Statut | Mode | Query ID | Durée | SQL Exécuté |",
        "|---|---|---|---|---|---|---|",
    ]
    for idx, r in enumerate(results, start=1):
        q = r.get("question", "").replace("|", "\\|")
        stat = "✅ Succès" if r.get("is_success") else "❌ Échec"
        mode = r.get("execution_mode", "-")
        qid = r.get("query_id") or "-"
        dur = f"{r.get('execution_time_ms', 0)} ms"
        sql = (" ".join(r.get("sql_query", "").split())[:60] + "...") if r.get("sql_query") else "-"
        md.append(f"| {idx} | {q} | {stat} | `{mode}` | `{qid}` | {dur} | `{sql}` |")

    md.extend(["", "## Détail des Réponses formulées", ""])
    for idx, r in enumerate(results, start=1):
        md.append(f"### {idx}. « {r.get('question')} »")
        md.append(f"- **Mode** : `{r.get('execution_mode')}`")
        md.append(f"- **Synthèse** : {r.get('summary') or r.get('answer')}")
        if r.get("sql_query"):
            md.append("```sql")
            md.append(r["sql_query"])
            md.append("```")
        md.append("")

    saved_path = safe_write_text(output_path, "\n".join(md), timestamp=timestamp)
    print(f"\n📄 Rapport Markdown généré dans : {saved_path.resolve()}")
    return saved_path



def main():
    parser = argparse.ArgumentParser(
        description="Script direct d'exécution automatique d'une liste de questions sur le service de reporting."
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        default=["questions.txt"],
        help="Chemin vers un fichier .txt OU une ou plusieurs questions en langage naturel.",
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        default=None,
        help="Chemin explicite vers un fichier texte contenant les questions.",
    )
    parser.add_argument(
        "--sqlite",
        action="store_true",
        help="Force l'utilisation d'une base SQLite mémoire avec jeu de test.",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Désactive le LLM pour forcer le mode supervisé déterministe.",
    )
    parser.add_argument(
        "--http",
        type=str,
        default=None,
        help="URL de l'API HTTP FastAPI (ex: http://localhost:8000).",
    )
    parser.add_argument(
        "--report",
        "-r",
        type=str,
        default=None,
        help="Génère un rapport Markdown de synthèse (ex: RAPPORT_QUESTIONS.md).",
    )
    parser.add_argument(
        "--json",
        "-j",
        type=str,
        default=None,
        help="Exporte les résultats bruts en JSON (ex: resultats.json).",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Exécute automatiquement l'analyse forensique des logs via tools/log_analyzer.",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Fichier de capture des logs pour l'audit (défaut: workflow_execution_<timestamp>.log).",
    )

    args = parser.parse_args()
    run_timestamp = get_run_timestamp()
    log_file_base = args.log_file if args.log_file else f"workflow_execution_{run_timestamp}.log"
    actual_log_path = get_unique_filepath(log_file_base, timestamp=run_timestamp)


    questions = []

    # 1. Si --file est spécifié
    if args.file:
        f_path = Path(args.file)
        if not f_path.exists():
            print(f"❌ Fichier de questions introuvable : {args.file}")
            sys.exit(1)
        for line in f_path.read_text(encoding="utf-8").splitlines():
            cl = line.strip()
            if cl and not cl.startswith("#"):
                questions.append(re.sub(r"^\d+[\.\)\-]\s*", "", cl))

    # 2. Sinon, analyser inputs
    elif args.inputs:
        first_input = args.inputs[0]
        f_path = Path(first_input)
        if f_path.exists() and f_path.is_file():
            for line in f_path.read_text(encoding="utf-8").splitlines():
                cl = line.strip()
                if cl and not cl.startswith("#"):
                    questions.append(re.sub(r"^\d+[\.\)\-]\s*", "", cl))
        else:
            for item in args.inputs:
                cl = item.strip()
                if cl and not cl.startswith("#"):
                    for subline in cl.splitlines():
                        sub_cl = subline.strip()
                        if sub_cl and not sub_cl.startswith("#"):
                            questions.append(re.sub(r"^\d+[\.\)\-]\s*", "", sub_cl))

    if not questions:
        print("⚠️ Aucune question fournie à exécuter.")
        sys.exit(1)

    print("=" * 80)
    print(f"🚀 EXÉCUTION AUTOMATIQUE DE {len(questions)} QUESTIONS SUR LE SERVICE DE REPORTING")
    print(f"🔹 Base de données   : {'SQLite Mémoire' if args.sqlite else 'MySQL / Détectée'}")
    print(f"🔹 Moteur LLM        : {'Désactivé (Supervisé)' if args.no_llm else 'Actif (Nemotron)'}")
    if args.http:
        print(f"🔹 Serveur cible     : HTTP API ({args.http})")
    if args.audit:
        print(f"🔹 Audit automatique : Activé (Fichier log: {actual_log_path.name})")

    print("=" * 80)

    # Capture des logs pour l'audit si --audit
    original_stdout_write = sys.stdout.write

    class LogCaptureWriter:
        def __init__(self, original_write):
            self.original_write = original_write
            self.lines = []

        def write(self, s):
            self.original_write(s)
            self.lines.append(s)

        def flush(self):
            sys.stdout.flush()

    capture_writer = None
    if args.audit:
        capture_writer = LogCaptureWriter(original_stdout_write)
        sys.stdout.write = capture_writer.write

    runner = WorkflowRunner(
        use_sqlite=args.sqlite,
        http_base_url=args.http,
        use_llm=not args.no_llm,
    )

    results = []

    try:
        for idx, question in enumerate(questions, start=1):
            print(f"\n▶ [{idx}/{len(questions)}] QUESTION : « {question} »")
            print("-" * 80)

            res = runner.execute_question(question)
            results.append(res)

            intent = res.get("intent") or {}
            entity_dict = intent.get("entity") or {}
            entity = entity_dict.get("concept_id", "inconnu") if isinstance(entity_dict, dict) else "inconnu"
            measure_dict = intent.get("measure") or {}
            measure = measure_dict.get("concept_id", "inconnu") if isinstance(measure_dict, dict) else "inconnu"

            print(f"  🎯 Intention     : Entité={entity} | Mesure={measure} | Statut={res.get('status')}")
            print(f"  ⚡ Circuit       : {res.get('execution_mode')} (Query ID: {res.get('query_id') or 'N/A'})")
            print(f"  ⏱️  Performance   : {res.get('execution_time_ms')} ms ({res.get('row_count')} ligne(s))")

            if res.get("sql_query"):
                sql_one_line = " ".join(res["sql_query"].split())
                print(f"  📜 SQL           : {sql_one_line[:120]}{'...' if len(sql_one_line) > 120 else ''}")

            print(f"  💬 Synthèse      : {res.get('summary') or res.get('answer')}")

    finally:
        runner.close()
        if capture_writer:
            sys.stdout.write = original_stdout_write
            full_log = "".join(capture_writer.lines)
            actual_log_path = safe_write_text(actual_log_path, full_log, timestamp=run_timestamp)
            print(f"\n📝 Journal d'exécution sauvegardé dans : {actual_log_path.resolve()}")

    print("\n" + "=" * 80)
    print("✅ TOUTES LES QUESTIONS ONT ÉTÉ EXÉCUTÉES AVEC SUCCÈS")
    print("=" * 80)

    # Export Markdown si demandé
    if args.report and results:
        generate_markdown_report(results, args.report, timestamp=run_timestamp)

    # Export JSON si demandé
    if args.json and results:
        actual_json_path = safe_write_text(
            args.json,
            json.dumps(results, indent=2, ensure_ascii=False),
            timestamp=run_timestamp,
        )
        print(f"📦 Résultats JSON exportés dans : {actual_json_path.resolve()}")

    # Déclenchement de l'audit automatique si --audit
    if args.audit and actual_log_path.exists():
        print("\n" + "=" * 80)
        print("🔍 LANCEMENT DE L'AUDIT FORENSIQUE DES 7 ÉTAPES (/gpr-ai-audit-log)")
        print("=" * 80)
        import subprocess
        audit_report_target = f"RAPPORT_AUDIT_WORKFLOW_{run_timestamp}.md"
        audit_json_target = f"audit_data_workflow_{run_timestamp}.json"
        subprocess.run([
            sys.executable,
            "tools/log_analyzer/cli.py",
            str(actual_log_path),
            "--report",
            audit_report_target,
            "--json",
            audit_json_target,
        ])



if __name__ == "__main__":
    main()
