#!/usr/bin/env python3
"""
Orchestrateur de Vague de Tests (3 Tests Préalables) pour le Workflow Text-to-SQL Gouverné.

Exécute automatiquement la boucle [Étape 1 : Stimulus -> Étape 3 : Immutabilité -> Étape 2 : Audit]
3 fois consécutives (par défaut) sur un fichier de questions unique immuable.
Produit un rapport de synthèse consolidé de la vague (RAPPORT_SYNTHESE_VAGUE_...md).

Usage :
    python run_wave.py questions_vague_01_20261015_095606.txt
    python run_wave.py questions_vague_02_20261015_140000.txt --runs 3
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Dict, Any, List

# Encodage console UTF-8 Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from tools.common.file_utils import (
    get_run_timestamp,
    get_unique_filepath,
    safe_write_text,
)


def extract_vague_id(filename: str) -> str:
    match = re.search(r"vague_(\d+)", filename, re.IGNORECASE)
    if match:
        return f"Vague {int(match.group(1)):02d}"
    return "Vague Inconnue"


def run_single_test(question_file: Path, run_idx: int, total_runs: int) -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print(f"🔄 [RUN {run_idx}/{total_runs}] EXÉCUTION DU TEST PRÉALABLE")
    print(f"📄 Corpus de test : {question_file.name}")
    print("=" * 80)

    # Capturer la liste des fichiers avant le run pour identifier les nouveaux artefacts
    base_dir = Path(".")
    existing_audits = set(base_dir.glob("audit_data_workflow_*.json"))
    existing_logs = set(base_dir.glob("workflow_execution_*.log"))
    existing_audit_mds = set(base_dir.glob("RAPPORT_AUDIT_WORKFLOW_*.md"))
    existing_exec_mds = set(base_dir.glob("RAPPORT_EXECUTION_QUESTIONS_*.md"))

    sys.stdout.flush()
    start_time = time.time()
    cmd = [
        sys.executable,
        "-u",
        "run_questions.py",
        str(question_file),
        "--report",
        "RAPPORT_EXECUTION_QUESTIONS.md",
        "--audit",
    ]

    proc = subprocess.run(cmd)
    duration = time.time() - start_time
    sys.stdout.flush()

    # Détecter les nouveaux artefacts créés
    new_audits = sorted(list(set(base_dir.glob("audit_data_workflow_*.json")) - existing_audits))
    new_logs = sorted(list(set(base_dir.glob("workflow_execution_*.log")) - existing_logs))
    new_audit_mds = sorted(list(set(base_dir.glob("RAPPORT_AUDIT_WORKFLOW_*.md")) - existing_audit_mds))
    new_exec_mds = sorted(list(set(base_dir.glob("RAPPORT_EXECUTION_QUESTIONS_*.md")) - existing_exec_mds))

    latest_audit_json = new_audits[-1] if new_audits else None
    latest_log = new_logs[-1] if new_logs else None
    latest_audit_md = new_audit_mds[-1] if new_audit_mds else None
    latest_exec_md = new_exec_mds[-1] if new_exec_mds else None

    audit_data = {}
    if latest_audit_json and latest_audit_json.exists():
        try:
            with open(latest_audit_json, "r", encoding="utf-8") as f:
                audit_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Erreur lors de la lecture du JSON d'audit : {e}")

    stats = audit_data.get("stats", {})
    runs_data = audit_data.get("runs", [])

    alerts_list = []
    for r in runs_data:
        for a in r.get("alerts", []):
            alerts_list.append({
                "run_id": r.get("run_id"),
                "question": r.get("question"),
                "severity": a.get("severity"),
                "step": a.get("step"),
                "code": a.get("code"),
                "message": a.get("message"),
            })

    return {
        "run_idx": run_idx,
        "exit_code": proc.returncode,
        "duration_sec": round(duration, 2),
        "log_file": str(latest_log) if latest_log else None,
        "audit_json": str(latest_audit_json) if latest_audit_json else None,
        "audit_md": str(latest_audit_md) if latest_audit_md else None,
        "exec_md": str(latest_exec_md) if latest_exec_md else None,
        "stats": stats,
        "alerts": alerts_list,
        "has_anomalies": len(alerts_list) > 0 or stats.get("execution_errors", 0) > 0 or stats.get("silent_fallbacks_detected", 0) > 0,
    }


def generate_wave_synthesis_report(
    vague_name: str,
    question_file: Path,
    runs_results: List[Dict[str, Any]],
    timestamp: str,
) -> Path:
    total_anomalies = sum(len(r["alerts"]) for r in runs_results)
    is_wave_perfect = (total_anomalies == 0) and all(r["exit_code"] == 0 for r in runs_results)

    md = [
        f"# Rapport de Synthèse Consolidé : {vague_name}",
        "",
        f"> **Statut Global de la Vague** : {'✅ VALIDÉE (0 anomalie)' if is_wave_perfect else '🚨 ANOMALIES DÉTECTÉES (Corrections requises)'}  ",
        f"> **Date d'exécution** : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
        f"> **Fichier Unique de Questions** : `{question_file.name}`  ",
        f"> **Nombre de Tests Préalables Exécutés** : {len(runs_results)}  ",
        "",
        "---",
        "",
        "## 1. Tableau Comparatif des 3 Tests Préalables",
        "",
        "| Métrique d'Audit Forensique | " + " | ".join([f"Test {r['run_idx']}" for r in runs_results]) + " | Verdict |",
        "| :--- | " + " | ".join([":---:" for _ in runs_results]) + " | :---: |",
    ]

    def format_row(label, values_fn, is_bad_if_positive=True):
        values = [values_fn(r) for r in runs_results]
        all_zero = all(v == 0 for v in values)
        verdict = "✅ Parfait" if (all_zero if is_bad_if_positive else not all_zero) else "❌ Écart"
        row_str = f"| **{label}** | " + " | ".join([str(v) for v in values]) + f" | {verdict} |"
        md.append(row_str)

    format_row("Questions traitées", lambda r: r["stats"].get("total_runs", 0), is_bad_if_positive=False)
    format_row("Erreurs SQL en base", lambda r: r["stats"].get("execution_errors", 0))
    format_row("Replis silencieux (Pydantic)", lambda r: r["stats"].get("silent_fallbacks_total", 0))
    format_row("Paramètres orphelins", lambda r: r["stats"].get("orphan_parameters_detected", 0))
    format_row("Divergences SQL", lambda r: r["stats"].get("sql_divergences_detected", 0))
    format_row("Circuits Courts (Fast/Candidate)", lambda r: r["stats"].get("fast_path_hits", 0) + r["stats"].get("candidate_path_hits", 0), is_bad_if_positive=False)
    format_row("Alertes totales", lambda r: len(r.get("alerts", [])))

    md.extend([
        "",
        "---",
        "",
        "## 2. Inventaire des Artefacts Forensiques Produit par Run",
        "",
        "| Run | Fichier Log Brut | Rapport d'Audit Forensique | Données Structurées JSON | Durée |",
        "| :---: | :--- | :--- | :--- | :---: |",
    ])

    for r in runs_results:
        log_name = Path(r["log_file"]).name if r["log_file"] else "-"
        audit_name = Path(r["audit_md"]).name if r["audit_md"] else "-"
        json_name = Path(r["audit_json"]).name if r["audit_json"] else "-"
        md.append(f"| Test {r['run_idx']} | `{log_name}` | [`{audit_name}`]({audit_name}) | [`{json_name}`]({json_name}) | {r['duration_sec']}s |")

    md.extend(["", "---", "", "## 3. Détail des Anomalies Détectées"])

    if total_anomalies == 0:
        md.append("\n✅ **Aucune anomalie détectée sur l'ensemble des 3 tests.** La stabilité du workflow est exemplaire.")
    else:
        for r in runs_results:
            md.append(f"\n### Test {r['run_idx']} ({len(r['alerts'])} anomalie(s))")
            if not r["alerts"]:
                md.append("✅ 0 anomalie sur ce test.")
            else:
                for a in r["alerts"]:
                    md.append(f"- **[Run {a['run_id']:02d}] « {a['question']} »** : `[{a['code']}]` {a['message']}")

    md.extend([
        "",
        "---",
        "",
        "## 4. Décision & Recommandation pour l'Étape 4",
        "",
    ])

    if is_wave_perfect:
        md.append("🏆 **Vague pleinement qualifiée.** Aucune correction requise. Prêt pour la clôture Git et le passage à la vague de complexité supérieure.")
    else:
        md.append("⚠️ **Des anomalies doivent être corrigées.** Transmettre les artefacts au Step 4 (`/safe-code-change`) avec un plan d'action générique sans duplication.")

    report_path = safe_write_text(
        f"RAPPORT_SYNTHESE_VAGUE_{re.sub(r'[^a-zA-Z0-9]', '_', vague_name).upper()}_{timestamp}.md",
        "\n".join(md),
        timestamp=timestamp,
    )
    print(f"\n📊 Rapport de synthèse de vague généré dans : {report_path.resolve()}")
    return report_path


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrateur de Vague de Tests (3 tests consécutifs) pour GPR AI."
    )
    parser.add_argument(
        "question_file",
        type=str,
        help="Chemin vers le fichier unique de questions de la vague (ex: questions_vague_01_20261015_095606.txt).",
    )
    parser.add_argument(
        "--runs",
        "-n",
        type=int,
        default=3,
        help="Nombre de tests préalables consécutifs à exécuter (défaut: 3).",
    )

    args = parser.parse_args()
    q_path = Path(args.question_file)
    if not q_path.exists():
        print(f"❌ Fichier de questions introuvable : {args.question_file}")
        sys.exit(1)

    vague_name = extract_vague_id(q_path.name)
    timestamp = get_run_timestamp()

    print("=" * 80)
    print(f"🌊 DÉMARRAGE DE LA CAMPAGNE : {vague_name.upper()} ({args.runs} TESTS PRÉALABLES)")
    print(f"📄 Fichier source : {q_path.resolve()}")
    print(f"🕒 Horodatage     : {timestamp}")
    print("=" * 80)

    runs_results = []
    for i in range(1, args.runs + 1):
        res = run_single_test(q_path, i, args.runs)
        runs_results.append(res)

    synth_report = generate_wave_synthesis_report(vague_name, q_path, runs_results, timestamp)

    total_anomalies = sum(len(r["alerts"]) for r in runs_results)
    print("\n" + "=" * 80)
    if total_anomalies == 0:
        print(f"🎉 SUCCÈS TOTAL : {vague_name} VALIDÉE À 100 % SUR LES {args.runs} TESTS (0 ANOMALIE) !")
        sys.exit(0)
    else:
        print(f"⚠️ {vague_name} : {total_anomalies} ANOMALIE(S) DÉTECTÉE(S) SUR LES {args.runs} TESTS.")
        print(f"👉 Données consolidées disponibles dans : {synth_report.name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
