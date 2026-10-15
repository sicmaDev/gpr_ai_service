#!/usr/bin/env python3
"""
Interface CLI d'Interrogation et de Test du Workflow Text-to-SQL Gouverné (Question par Question).
Permet de tester les scénarios P1.1 à P1.5 de manière interactive ou automatisée.

Usage :
    python tools/workflow_interrogator/cli.py                     # Mode interactif pas-à-pas (défaut)
    python tools/workflow_interrogator/cli.py --all               # Exécute les 24 questions à la suite
    python tools/workflow_interrogator/cli.py --scenario P1.1     # Exécute un sous-step spécifique
    python tools/workflow_interrogator/cli.py --id 7              # Exécute la question n° 7
    python tools/workflow_interrogator/cli.py --question "Total des réclamations"
    python tools/workflow_interrogator/cli.py --report rapport.md # Exporte un rapport Markdown
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

# Encodage console UTF-8 Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Résolution des imports locaux
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from tools.workflow_interrogator.questions import QUESTIONS_CATALOG
from tools.workflow_interrogator.runner import WorkflowRunner


def _format_intent(intent: Dict[str, Any]) -> str:
    """Formate l'intention canonique en chaîne lisible."""
    if not intent or intent.get("status") != "ready":
        return f"Statut : {intent.get('status', 'non résolu')}"

    lines = []
    # Entité
    entity = intent.get("entity") or {}
    concept = entity.get("concept_id", "inconnu")
    types = entity.get("types", [])
    include_all = entity.get("include_all_types", False)
    all_str = " (tous)" if include_all else ""
    lines.append(f"  • Entité      : {concept} [types={','.join(types)}{all_str}]")

    # Mesure
    measure = intent.get("measure") or {}
    m_concept = measure.get("concept_id", "inconnu")
    op = measure.get("operation", "count")
    lbl = measure.get("label", "")
    lines.append(f"  • Mesure      : {m_concept} ({op}) - « {lbl} »")

    # Dimensions
    dims = [d.get("concept_id") for d in intent.get("dimensions", [])]
    dims_str = ", ".join(dims) if dims else "aucune (global)"
    lines.append(f"  • Dimensions  : [{dims_str}]")

    # Filtres
    filters = intent.get("filters", [])
    if filters:
        f_strs = [f"{f.get('concept_id')} {f.get('operator')} {f.get('value') or f.get('values')}" for f in filters]
        lines.append(f"  • Filtres     : [{'; '.join(f_strs)}]")
    else:
        lines.append("  • Filtres     : [aucun]")

    # Temps
    time_info = intent.get("time")
    if time_info:
        start = time_info.get("start_date")
        end = time_info.get("end_date")
        lines.append(f"  • Période     : du {start} au {end}")
    else:
        lines.append("  • Période     : aucune (zéro date par défaut)")

    return "\n".join(lines)


def _print_result(q_data: Dict[str, Any], res: Dict[str, Any], index: int, total: int) -> None:
    """Affiche élégamment le résultat d'une question exécutée."""
    print("\n" + "=" * 80)
    print(f"▶ [{index}/{total}] QUESTION : « {res['question']} »")
    if q_data.get("scenario"):
        print(f"   Scénario : {q_data['scenario']} ({q_data.get('category')}) - {q_data.get('title')}")
    print("=" * 80)

    # 1. Intention
    print("\n🎯 [ÉTAPE 1 : INTENTION CANONIQUE RÉSOLUE]")
    print(_format_intent(res.get("intent", {})))

    # 2. Mode et SQL
    print("\n⚡ [EXÉCUTION & CIRCUIT TEXT-TO-SQL]")
    print(f"  • Mode d'exécution  : {res['execution_mode']}")
    print(f"  • Query ID          : {res['query_id'] or 'aucun (inédit/rejeté)'}")
    print(f"  • Lignes retournées : {res['row_count']}")
    print(f"  • Temps d'exécution : {res['execution_time_ms']} ms")

    if res.get("sql_query"):
        print("\n📜 [REQUÊTE SQL EXÉCUTÉE]")
        print("  " + "-" * 76)
        for line in res["sql_query"].splitlines():
            print(f"  {line}")
        print("  " + "-" * 76)

    # 3. Restitution
    print("\n💬 [SYNTHÈSE DE RESTITUTION]")
    print(f"  « {res.get('summary') or res.get('answer')} »")
    print("=" * 80 + "\n")


def generate_markdown_report(results: List[Dict[str, Any]], output_path: str) -> None:
    """Génère un rapport d'audit Markdown complet pour toutes les questions testées."""
    md = [
        "# Rapport d'Exécution : Interrogation du Workflow Text-to-SQL Gouverné",
        "",
        f"**Date d'exécution** : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
        f"**Nombre de questions traitées** : {len(results)}  ",
        "",
        "## Tableau Récapitulatif des Questions Testées",
        "",
        "| N° | Scénario | Question | Mode | Query ID | Durée | Statut |",
        "|---|---|---|---|---|---|---|",
    ]

    for r in results:
        q_meta = r.get("metadata", {})
        sc = q_meta.get("scenario", "-")
        stat = "✅ Succès" if r.get("is_success") else "❌ Échec"
        q_id = r.get("query_id") or "-"
        dur = f"{r.get('execution_time_ms', 0)} ms"
        mode = r.get("execution_mode", "-")
        q_txt = r.get("question", "").replace("|", "\\|")
        md.append(f"| {q_meta.get('id', '-')} | `{sc}` | {q_txt} | `{mode}` | `{q_id}` | {dur} | {stat} |")

    md.extend([
        "",
        "## Détail des Requêtes et des Intentions Extraites",
        "",
    ])

    for r in results:
        q_meta = r.get("metadata", {})
        sc = q_meta.get("scenario", "-")
        q_txt = r.get("question", "")
        md.append(f"### Scénario `{sc}` : {q_txt}")
        md.append("")
        md.append(f"- **Mode d'exécution** : `{r.get('execution_mode')}`")
        md.append(f"- **Query ID** : `{r.get('query_id') or 'N/A'}`")
        md.append(f"- **Synthèse** : {r.get('summary') or r.get('answer')}")
        if r.get("sql_query"):
            md.append("```sql")
            md.append(r["sql_query"])
            md.append("```")
        md.append("")

    Path(output_path).write_text("\n".join(md), encoding="utf-8")
    print(f"📄 Rapport Markdown généré avec succès dans : {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Outil d'interrogation pas-à-pas du Workflow de Reporting IA Text-to-SQL."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Exécute automatiquement toutes les 24 questions du catalogue de test.",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Filtre sur un préfixe de scénario (ex: P1.1, P1.2, P1.3, P1.4, P1.5).",
    )
    parser.add_argument(
        "--id",
        type=int,
        default=None,
        help="Exécute uniquement la question correspondant à l'identifiant spécifié (1 à 24).",
    )
    parser.add_argument(
        "--question",
        "-q",
        type=str,
        default=None,
        help="Exécute une question ad-hoc personnalisée en langage naturel.",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Active le mode pas-à-pas interactif avec pause et prompt entre chaque question.",
    )
    parser.add_argument(
        "--sqlite",
        action="store_true",
        help="Force l'utilisation d'une base de données SQLite en mémoire avec données d'essai.",
    )
    parser.add_argument(
        "--http",
        type=str,
        default=None,
        help="Interroge le service via HTTP FastAPI (ex: http://localhost:8000).",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Désactive les appels au LLM Nemotron et force le mode supervisé/déterministe.",
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        default=None,
        help="Chemin vers un fichier texte contenant une liste de questions (1 question par ligne).",
    )
    parser.add_argument(
        "--report",
        "-r",
        type=str,
        default=None,
        help="Chemin de sortie pour exporter un rapport Markdown d'exécution (ex: audit_run.md).",
    )
    parser.add_argument(
        "--json",
        "-j",
        type=str,
        default=None,
        help="Chemin de sortie pour exporter les résultats bruts en JSON.",
    )

    args = parser.parse_args()

    # Détermination du mode interactif
    # Si --all ou --file ou --scenario ou --id ou --question est spécifié -> exécution automatique
    has_batch_target = args.all or bool(args.file) or (args.scenario is not None) or (args.id is not None) or (args.question is not None)
    is_interactive = args.interactive or (not has_batch_target)

    # Sélection des questions à exécuter
    selected_questions: List[Dict[str, Any]] = []

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ Fichier de questions introuvable : {args.file}")
            sys.exit(1)
        raw_lines = file_path.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(raw_lines, start=1):
            cleaned = line.strip()
            if not cleaned or cleaned.startswith("#"):
                continue
            # Nettoyer les numérotations initiales éventuelles (ex: "1. Combien de...")
            import re
            cleaned_q = re.sub(r"^\d+[\.\)\-]\s*", "", cleaned)
            selected_questions.append({
                "id": idx,
                "scenario": f"FILE-{idx}",
                "category": "Fichier Externe",
                "title": f"Ligne {idx}",
                "question": cleaned_q,
            })
        if not selected_questions:
            print(f"⚠️ Le fichier {args.file} ne contient aucune question valide.")
            sys.exit(1)
    elif args.question:
        selected_questions = [{
            "id": 999,
            "scenario": "CUSTOM",
            "category": "Personnalisée",
            "title": "Question ad-hoc saisie",
            "question": args.question,
        }]
    elif args.id:
        selected_questions = [q for q in QUESTIONS_CATALOG if q["id"] == args.id]
        if not selected_questions:
            print(f"❌ Question avec ID={args.id} introuvable.")
            sys.exit(1)
    elif args.scenario:
        selected_questions = [q for q in QUESTIONS_CATALOG if q["scenario"].startswith(args.scenario.upper())]
        if not selected_questions:
            print(f"❌ Aucun scénario trouvé pour le filtre '{args.scenario}'.")
            sys.exit(1)
    else:
        selected_questions = list(QUESTIONS_CATALOG)

    print("\n" + "=" * 80)
    print("   🚀 INTERROGATION DU WORKFLOW TEXT-TO-SQL GOUVERNÉ (REPORTING IA)")
    print("=" * 80)
    print(f"🔹 Nombre de questions sélectionnées : {len(selected_questions)}")
    print(f"🔹 Mode d'exécution                  : {'HTTP API (' + args.http + ')' if args.http else ('SQLite Mémoire' if args.sqlite else 'MySQL / Hybride')}")
    print(f"🔹 Générateur LLM Nemotron           : {'Désactivé (Supervisé)' if args.no_llm else 'Actif'}")
    print(f"🔹 Navigation                        : {'Pas-à-pas interactif' if is_interactive else 'Automatisée'}")
    print("=" * 80)

    runner = WorkflowRunner(
        use_sqlite=args.sqlite,
        http_base_url=args.http,
        use_llm=not args.no_llm,
    )

    results: List[Dict[str, Any]] = []

    try:
        idx = 0
        while idx < len(selected_questions):
            q_data = selected_questions[idx]
            q_txt = q_data["question"]

            if is_interactive:
                print(f"\n[Question {idx + 1}/{len(selected_questions)}] {q_data.get('scenario', '')} - « {q_txt} »")
                choice = input("  👉 [Entrée]: Exécuter | [s]: Sauter | [c]: Personnalisée | [q]: Quitter > ").strip().lower()

                if choice == "q":
                    print("\nArrêt demandé par l'utilisateur.")
                    break
                elif choice == "s":
                    print("  ⏭️ Question sautée.")
                    idx += 1
                    continue
                elif choice == "c":
                    custom_q = input("  ✍️ Saisir votre question : ").strip()
                    if custom_q:
                        q_data = {
                            "id": 999,
                            "scenario": "CUSTOM",
                            "category": "Personnalisée",
                            "title": "Saisie utilisateur",
                            "question": custom_q,
                        }
                        q_txt = custom_q

            res = runner.execute_question(q_txt)
            res["metadata"] = q_data
            results.append(res)

            _print_result(q_data, res, idx + 1, len(selected_questions))

            idx += 1

    finally:
        runner.close()

    # Export des rapports
    if args.report and results:
        generate_markdown_report(results, args.report)

    if args.json and results:
        Path(args.json).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"📦 Résultats JSON exportés dans : {args.json}")


if __name__ == "__main__":
    main()
