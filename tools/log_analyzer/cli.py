#!/usr/bin/env python3
"""
Interface en ligne de commande (CLI) de l'Analyseur de Logs du Workflow Text-to-SQL Gouverné.
Permet d'auditer et d'extraire l'intégralité des 7 contrats pour chaque étape.
Usage :
    python tools/log_analyzer/cli.py <chemin_du_fichier_log> [--report rapport.md] [--json data.json] [--run <N>]
"""

import sys
import argparse
import json
from pathlib import Path

# Assurer la bonne gestion de l'encodage sur la console Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Permettre l'import local même si exécuté directement
current_dir = Path(__file__).resolve().parent
if str(current_dir.parent.parent) not in sys.path:
    sys.path.insert(0, str(current_dir.parent.parent))

from tools.common.file_utils import (
    get_run_timestamp,
    get_unique_filepath,
    safe_write_text,
)
from tools.log_analyzer.analyzer import WorkflowLogAnalyzer


def main():
    parser = argparse.ArgumentParser(
        description="Audit et extraction des contrats des 7 étapes du Workflow Text-to-SQL Gouverné."
    )
    parser.add_argument(
        "log_file",
        type=str,
        help="Chemin vers le fichier de logs (ex: uvicorn_output.log ou fichier de test)",
    )
    parser.add_argument(
        "--report",
        "-r",
        type=str,
        default=None,
        help="Chemin de sortie optionnel pour le rapport Markdown (ex: audit_report.md)",
    )
    parser.add_argument(
        "--json",
        "-j",
        type=str,
        default=None,
        help="Chemin de sortie optionnel pour les données structurées JSON (ex: audit.json)",
    )
    parser.add_argument(
        "--run",
        type=int,
        default=None,
        help="Audite et affiche les 7 contrats uniquement pour le numéro de run spécifié (1-indexé).",
    )
    parser.add_argument(
        "--divergences-only",
        action="store_true",
        help="N'affiche dans le terminal que les runs comportant des divergences SQL ou replis silencieux.",
    )

    args = parser.parse_args()

    try:
        analyzer = WorkflowLogAnalyzer(args.log_file)
        result = analyzer.parse()
    except Exception as exc:
        print(f"❌ Erreur lors de l'analyse du fichier : {exc}")
        sys.exit(1)

    stats = result["stats"]
    runs = result["runs"]

    # Affichage terminal synthétique
    print("\n" + "=" * 80)
    print("   📊 AUDIT & CONTRATS DES 7 ÉTAPES DU WORKFLOW TEXT-TO-SQL GOUVERNÉ")
    print("=" * 80)
    print(f"📁 Fichier analysé : {Path(args.log_file).name}")
    print(f"🔹 Total des requêtes traitées        : {stats['total_runs']}")
    print(f"🔹 Hits Fast-Path (Homologués)        : {stats['fast_path_hits']}")
    print(f"🔹 Hits Candidate-Path (En attente)   : {stats['candidate_path_hits']}")
    print(f"🔹 Générations LLM Nemotron           : {stats['generative_llm_calls']}")
    print("-" * 80)
    print(f"🚨 Replis silencieux détectés         : {stats['silent_fallbacks_total']}")
    print(f"   ↳ Étape 1 (Intention)              : {stats['step1_pydantic_errors']}")
    print(f"   ↳ Étape 4 (Générateur SQL)         : {stats['step4_pydantic_errors']}")
    print(f"🚨 Divergences SQL LLM vs Exécuté     : {stats['sql_divergences_detected']}")
    print(f"🚨 Incohérences sémantiques synthèse  : {stats['semantic_synthesis_corruptions']}")
    print(f"⚠️  Désynchronisations temporelles     : {stats['temporal_mismatches_detected']}")
    print(f"⚠️  Paramètres orphelins               : {stats['orphan_parameters_detected']}")
    print(f"🔒 Fuites PII potentielles            : {stats['pii_leak_detected']}")
    print(f"❌ Erreurs d'exécution SQL            : {stats['execution_errors']}")
    print("=" * 80 + "\n")

    # Si filtrage sur un run spécifique
    if args.run:
        target_runs = [r for r in runs if r["run_id"] == args.run]
        if not target_runs:
            print(f"❌ Run n° {args.run} introuvable (total: {len(runs)})")
            sys.exit(1)
        r = target_runs[0]
        print(f"🔍 DÉTAIL DES 7 CONTRATS POUR LE RUN N° {r['run_id']} : \"{r['question']}\"")
        print("-" * 80)
        print(f"[ÉTAPE 1 : INTENTION]  Source: {r['step1_intent']['source']} | Statut: {r['step1_intent']['status']}")
        if r['step1_intent']['contract_json']:
            print(json.dumps(r['step1_intent']['contract_json'], indent=2, ensure_ascii=False))
        print(f"\n[ÉTAPE 2 : AIGUILLAGE] Circuit: {r['step2_routing']['routing']} | QID: {r['step2_routing']['query_id']}")
        if r['step2_routing']['template_sql']:
            print(f"SQL Template : {r['step2_routing']['template_sql']}")
        print(f"\n[ÉTAPE 3 : SOUS-SCHÉMA] Tables: {r['step3_subschema']['allowed_tables']}")
        print(f"\n[ÉTAPE 4 : SQL CANDIDAT] SQL Retenu :\n{r['step4_candidate_sql']['candidate_sql']}")
        if r['step4_candidate_sql']['pydantic_error']:
            print(f"❌ Erreur Pydantic : {r['step4_candidate_sql']['pydantic_error']}")
        print(f"\n[ÉTAPE 5 : BOUCLIER AST] Statut: [{r['step5_ast_shield']['ast_valid']}]")
        print(f"\n[ÉTAPE 6 : EXÉCUTION BDD] Statut: {r['step6_execution']['execution_status']} | Lignes: {r['step6_execution']['rows_returned']} | Durée: {r['step6_execution']['duration']}")
        print(f"\n[ÉTAPE 7 : RESTITUTION] Synthèse : \"{r['step7_restitution']['synthesis']}\" | Visualisation : {r['step7_restitution']['visualization']}")
        print("=" * 80 + "\n")
    else:
        # Affichage standard par run avec anomalies
        print("🔎 ANOMALIES & DIVERGENCES PAR RUN :")
        print("-" * 80)
        alerts_count = 0
        for r in runs:
            if args.divergences_only and not r["step4_candidate_sql"]["sql_divergence"] and not (r["step1_intent"]["pydantic_error"] or r["step4_candidate_sql"]["pydantic_error"]):
                continue

            if r["alerts"]:
                alerts_count += 1
                print(f"\n[RUN {r['run_id']:02d}] \"{r['question']}\"")
                print(f"   Routage : {r['routing']} | Query ID : {r['final_qid']} | Statut : {r['lifecycle_status']}")
                for a in r["alerts"]:
                    icon = "🚨" if a["severity"] == "CRITICAL" else ("⚠️" if a["severity"] == "HIGH" else "ℹ️")
                    print(f"   {icon} [{a['step']}] {a['code']} : {a['message']}")

                if r["step4_candidate_sql"]["raw_llm_sql"] and r["step4_candidate_sql"]["candidate_sql"] and r["step4_candidate_sql"]["sql_divergence"]:
                    print("   --- PROPOSÉ PAR LE LLM :")
                    print(f"   {r['step4_candidate_sql']['raw_llm_sql']}")
                    print("   --- EXÉCUTÉ PAR LE WORKFLOW (FALLBACK) :")
                    print(f"   {r['step4_candidate_sql']['candidate_sql']}")

        if alerts_count == 0:
            print("✅ Aucune anomalie détectée selon les filtres sélectionnés.")

    print("\n" + "=" * 80)

    run_timestamp = get_run_timestamp()

    # Export Markdown automatique par défaut (sans écrasement)
    target_report = args.report if args.report else f"RAPPORT_AUDIT_WORKFLOW_{run_timestamp}.md"
    report_md = analyzer.generate_markdown_report(result, detailed=True)
    report_file_path = safe_write_text(target_report, report_md, timestamp=run_timestamp)
    print(f"📄 Rapport Markdown complet (7 contrats) généré : {report_file_path.resolve()}")

    # Export JSON automatique par défaut (sans écrasement)
    target_json = args.json if args.json else f"audit_data_workflow_{run_timestamp}.json"
    json_file_path = safe_write_text(
        target_json,
        json.dumps(result, indent=2, ensure_ascii=False),
        timestamp=run_timestamp,
    )
    print(f"💾 Données JSON structurées exportées : {json_file_path.resolve()}")



if __name__ == "__main__":
    main()
