"""
Module d'analyse automatique et d'audit des logs du Workflow Text-to-SQL Gouverné.
Permet d'extraire l'ensemble des 7 étapes pour chaque question avec ses contrats stricts (JSON, SQL, AST, BDD),
et de détecter automatiquement les anomalies critiques, divergences SQL et replis silencieux.
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class WorkflowLogAnalyzer:
    """
    Analyseur autonome des logs d'exécution du workflow analytique Text-to-SQL.
    Extrait pour chaque question l'intégralité des 7 étapes et leurs contrats officiels.
    """

    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        if not self.log_path.exists():
            raise FileNotFoundError(f"Le fichier de log spécifié est introuvable : {log_path}")

    def load_content(self) -> str:
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            with open(self.log_path, "r", encoding="cp1252", errors="ignore") as f:
                return f.read()

    @staticmethod
    def _extract_between_delimiters(text: str, start_marker: str, end_marker: str) -> Optional[str]:
        if start_marker not in text:
            return None
        parts = text.split(start_marker, 1)
        if len(parts) > 1 and end_marker in parts[1]:
            return parts[1].split(end_marker, 1)[0].strip()
        return None

    @staticmethod
    def _clean_json_str(raw: str) -> Optional[Dict[str, Any]]:
        if not raw:
            return None
        clean = raw.strip()
        if "```json" in clean:
            clean = clean.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in clean:
            clean = clean.split("```", 1)[1].split("```", 1)[0].strip()
        try:
            return json.loads(clean)
        except Exception:
            start_idx = clean.find("{")
            end_idx = clean.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                try:
                    return json.loads(clean[start_idx : end_idx + 1])
                except Exception:
                    pass
        return None

    def parse(self) -> Dict[str, Any]:
        content = self.load_content()
        blocks = content.split(">>> [WORKFLOW TEXT-TO-SQL GOUVERNE] TRAITEMENT D'UNE QUESTION ANALYTIQUE")

        stats = {
            "total_runs": len(blocks) - 1,
            "fast_path_hits": 0,
            "candidate_path_hits": 0,
            "generative_llm_calls": 0,
            "silent_fallbacks_total": 0,
            "step1_pydantic_errors": 0,
            "step4_pydantic_errors": 0,
            "sql_divergences_detected": 0,
            "temporal_mismatches_detected": 0,
            "orphan_parameters_detected": 0,
            "semantic_synthesis_corruptions": 0,
            "pii_leak_detected": 0,
            "execution_errors": 0,
        }

        runs_data = []

        for idx, block in enumerate(blocks[1:], 1):
            alerts: List[Dict[str, str]] = []

            # Question posée
            q_match = re.search(r"\* Question posee\s*:\s*\"([^\"]+)\"", block)
            question = q_match.group(1).strip() if q_match else f"Question_Run_{idx}"

            # -------------------------------------------------------------
            # ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE (TextToSQLIntent)
            # -------------------------------------------------------------
            raw_e1_text = self._extract_between_delimiters(
                block,
                ">>> [REPONSE BRUTE RECUE DU LLM (ETAPE 1 : INTENTION) - nemotron-3-super]\n  ============================================================================",
                "============================================================================"
            )
            raw_e1_json = self._clean_json_str(raw_e1_text) if raw_e1_text else None

            # Contrat JSON validé affiché dans le log
            intent_json_match = re.search(r"INTENTION ANALYTIQUE DE L'UTILISATEUR\s*:\s*```json\s*(\{[\s\S]*?\})\s*```", block)
            validated_intent_json = self._clean_json_str(intent_json_match.group(1)) if intent_json_match else raw_e1_json

            e1_statut = re.search(r"\* Statut resolu\s*:\s*([^\n\r]+)", block)
            e1_entite = re.search(r"\* Entite cible\s*:\s*([^\n\r]+)", block)
            e1_mesure = re.search(r"\* Mesure calculee\s*:\s*([^\n\r]+)", block)
            e1_dims = re.search(r"\* Dimensions demandees\s*:\s*([^\n\r]+)", block)
            e1_time = re.search(r"\* Periode temporelle\s*:\s*([^\n\r]+)", block)
            e1_filtres = re.search(r"\* Filtres appliques\s*:\s*([^\n\r]+)", block)

            time_str = e1_time.group(1).strip() if e1_time else "aucune (global sur toute la base)"
            has_time_filter = "aucune" not in time_str.lower()

            # Détection de repli silencieux Étape 1
            e1_pydantic_error = None
            m_e1_err = re.search(
                r"(?:Échec de résolution d'intention LLM|Échec de parsing intention LLM)\s*\(([^)]+)\)",
                block,
            )
            intent_source = "GENERATIVE_LLM_NEMOTRON"
            if m_e1_err:
                e1_pydantic_error = m_e1_err.group(1).strip()
                intent_source = "FALLBACK_DETERMINISTE_MOTS_CLES"
                stats["step1_pydantic_errors"] += 1
                stats["silent_fallbacks_total"] += 1
                alerts.append({
                    "severity": "CRITICAL",
                    "step": "Étape 1 (Intention)",
                    "code": "SILENT_FALLBACK_INTENT",
                    "message": f"Échec de validation Pydantic de l'intention LLM ({e1_pydantic_error}). Repli silencieux vers le résolveur déterministe."
                })

            step1_data = {
                "source": intent_source,
                "status": e1_statut.group(1).strip() if e1_statut else "N/A",
                "entity": e1_entite.group(1).strip() if e1_entite else "N/A",
                "measure": e1_mesure.group(1).strip() if e1_mesure else "N/A",
                "dimensions": e1_dims.group(1).strip() if e1_dims else "N/A",
                "time": time_str,
                "filters": e1_filtres.group(1).strip() if e1_filtres else "aucun",
                "contract_json": validated_intent_json,
                "raw_llm_json": raw_e1_json,
                "pydantic_error": e1_pydantic_error,
            }

            # -------------------------------------------------------------
            # ÉTAPE 2 : FAST-PATH & CANDIDATE-PATH
            # -------------------------------------------------------------
            is_fast_path = bool(re.search(r"\* Resultat Fast-Path\s*:\s*\[HIT\]", block))
            is_cand_path = "[ETAPE 2 : CANDIDATE-PATH EN ATTENTE]" in block

            if is_fast_path:
                routing = "FAST_PATH_HOMOLOGATED"
                stats["fast_path_hits"] += 1
            elif is_cand_path:
                routing = "CANDIDATE_PATH_PENDING"
                stats["candidate_path_hits"] += 1
            else:
                routing = "GENERATIVE_LLM"
                stats["generative_llm_calls"] += 1

            e2_qid_m = re.search(r"(?:\* Identifiant Query\s*:\s*|query_id=['\"])([A-Za-z0-9_-]+)", block)
            e2_qid = e2_qid_m.group(1).strip() if e2_qid_m else None

            e2_libelle_m = re.search(r"\* Libelle Metier\s*:\s*\"([^\"]+)\"", block)
            e2_libelle = e2_libelle_m.group(1).strip() if e2_libelle_m else None

            e2_sql_m = re.search(r"REQUETE VALIDEE SELECTIONNEE[^:]*:\s*-+\s*([\s\S]*?)\s*-+", block)
            e2_template_sql = e2_sql_m.group(1).strip() if e2_sql_m else None

            # Surveillance Dérive Temporelle sur Candidate-Path
            temporal_mismatch = False
            temporal_markers = ["2026", "2025", "mars", "janvier", "trimestre", "mois", "annee", "semaine"]
            question_has_dates = any(tm in question.lower() for tm in temporal_markers)
            if is_cand_path and (has_time_filter or question_has_dates):
                # Vérification effective : la désynchronisation n'existe que si la requête ne contient AUCUN filtre temporel
                has_temporal_filter = any(
                    marker in block.lower()
                    for marker in ["start_date", "end_date", "receipt_at", "recorded_at", "resolved_at", "created_at"]
                )
                if not has_temporal_filter:
                    temporal_mismatch = True
                    stats["temporal_mismatches_detected"] += 1
                    alerts.append({
                        "severity": "HIGH",
                        "step": "Étape 2 (Candidate-Path)",
                        "code": "TEMPORAL_MISMATCH_CANDIDATE",
                        "message": f"Désynchronisation temporelle : L'intention exige une période temporelle ({time_str}), mais le Candidate-Path a réutilisé la requête en attente ({e2_qid}) sans filtre temporel dans le SQL."
                    })

            step2_data = {
                "routing": routing,
                "query_id": e2_qid,
                "libelle_metier": e2_libelle,
                "template_sql": e2_template_sql,
                "temporal_mismatch": temporal_mismatch,
            }

            # -------------------------------------------------------------
            # ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL
            # -------------------------------------------------------------
            e3_tables_m = re.search(r"\* Tables autorisees\s*:\s*([^\n\r]+)", block)
            e3_tables = e3_tables_m.group(1).strip() if e3_tables_m else ""

            # Vérification fuite de colonnes sensibles dans la définition de table
            pii_leak = False
            schema_section = re.search(r"SCHEMA DE LA BASE DE DONNEES FOURNI AU LLM :[\s\S]*?(?=\[ETAPE 4|\Z)", block)
            if schema_section:
                sec_text = schema_section.group(0)
                for sens_col in ["- `client_code`", "- `content`", "- `solution`", "- `motif_rejet`"]:
                    if sens_col in sec_text:
                        pii_leak = True
                        stats["pii_leak_detected"] += 1
                        alerts.append({
                            "severity": "CRITICAL",
                            "step": "Étape 3 (Sous-schéma)",
                            "code": "PII_LEAK_IN_PROMPT",
                            "message": f"Colonne sensible détectée dans le schéma fourni au LLM : {sens_col}"
                        })

            step3_data = {
                "allowed_tables": e3_tables,
                "pii_protected": not pii_leak,
            }

            # -------------------------------------------------------------
            # ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ (TextToSQLCandidate)
            # -------------------------------------------------------------
            raw_e4_text = self._extract_between_delimiters(
                block,
                ">>> [REPONSE BRUTE RECUE DU LLM (ETAPE 4 : GENERATION SQL) - nemotron-3-super]\n  ============================================================================",
                "============================================================================"
            )
            raw_e4_json = self._clean_json_str(raw_e4_text) if raw_e4_text else None

            # Détection de repli silencieux Étape 4
            e4_pydantic_error = None
            m_e4_err = re.search(
                r"(?:Échec de parsing candidat LLM|Échec de parsing candidat)\s*\(([^)]+)\)",
                block,
            )
            if m_e4_err:
                e4_pydantic_error = m_e4_err.group(1).strip()
                stats["step4_pydantic_errors"] += 1
                stats["silent_fallbacks_total"] += 1
                alerts.append({
                    "severity": "CRITICAL",
                    "step": "Étape 4 (Générateur SQL)",
                    "code": "SILENT_FALLBACK_CANDIDATE",
                    "message": f"Échec de validation Pydantic TextToSQLCandidate ({e4_pydantic_error}). Repli silencieux vers le générateur déterministe."
                })

            raw_llm_sql = raw_e4_json.get("sql") if raw_e4_json else None
            raw_parameters = raw_e4_json.get("parameters", {}) if raw_e4_json else {}
            raw_columns = raw_e4_json.get("result_columns", []) if raw_e4_json else []
            raw_assumptions = raw_e4_json.get("assumptions", []) if raw_e4_json else []

            # Requête candidate finale produite (ou issue du fallback)
            cand_sql = None
            m_cand = re.search(r"REQUETE SQL CANDIDATE GENEREE[^:]*:\s*-+\s*([\s\S]*?)\s*-+", block)
            if m_cand:
                cand_sql = m_cand.group(1).strip()

            # Anti-patterns injectés dans le prompt
            anti_patterns_found = []
            m_anti = re.search(r"PI[EÈ]GES M[EÉ]TIER ET ERREURS [AÀ] [EÉ]VITER[\s\S]*?(?=FORMAT DE SORTIE ATTENDU)", block)
            if m_anti:
                for line in m_anti.group(0).splitlines():
                    if "REQUÊTE REJETÉE" in line or "REQUETE REJETEE" in line:
                        anti_patterns_found.append(line.strip())

            # Surveillance Divergence SQL Brut LLM vs SQL Exécuté
            sql_divergence = False
            divergence_details = None
            if raw_llm_sql and cand_sql:
                r_norm = " ".join(raw_llm_sql.split()).strip().rstrip(";")
                c_norm = " ".join(cand_sql.split()).strip().rstrip(";")

                if "plainte_count" in c_norm and "plainte_count" not in r_norm:
                    sql_divergence = True
                    stats["sql_divergences_detected"] += 1
                    divergence_details = "Le LLM a proposé une requête spécifique mais le système a exécuté le fallback global 'plainte_count' !"
                    alerts.append({
                        "severity": "CRITICAL",
                        "step": "Étape 4 (Générateur SQL)",
                        "code": "RAW_VS_CANDIDATE_SQL_DIVERGENCE",
                        "message": f"{divergence_details} (Proposé: {r_norm[:60]}... | Exécuté: {c_norm[:60]}...)"
                    })
                elif r_norm.replace(" ", "") != c_norm.replace(" ", ""):
                    if not (":risk_level" in r_norm and ("'MOYEN'" in c_norm or "'GRAVE'" in c_norm)):
                        sql_divergence = True
                        stats["sql_divergences_detected"] += 1
                        divergence_details = "Différence structurelle entre le SQL brut du LLM et le SQL candidat exécuté."
                        alerts.append({
                            "severity": "HIGH",
                            "step": "Étape 4 (Générateur SQL)",
                            "code": "SQL_STRUCTURAL_DIFF",
                            "message": f"{divergence_details} (Proposé: {r_norm[:60]}... | Exécuté: {c_norm[:60]}...)"
                        })

            # Paramètres Orphelins (déclarés dans parameters mais absents du SQL)
            orphan_params = []
            if raw_llm_sql and isinstance(raw_parameters, dict):
                for p_name in raw_parameters.keys():
                    p_key = p_name.lstrip(":")
                    if f":{p_key}" not in raw_llm_sql and p_name not in raw_llm_sql:
                        orphan_params.append(p_name)
                if orphan_params:
                    stats["orphan_parameters_detected"] += 1
                    alerts.append({
                        "severity": "MEDIUM",
                        "step": "Étape 4 (Générateur SQL)",
                        "code": "ORPHAN_PARAMETERS",
                        "message": f"Paramètres déclarés dans le contrat mais absents de la clause SQL : {orphan_params}"
                    })

            step4_data = {
                "raw_llm_json": raw_e4_json,
                "raw_llm_sql": raw_llm_sql,
                "candidate_sql": cand_sql,
                "parameters": raw_parameters,
                "result_columns": raw_columns,
                "assumptions": raw_assumptions,
                "pydantic_error": e4_pydantic_error,
                "sql_divergence": sql_divergence,
                "divergence_details": divergence_details,
                "orphan_parameters": orphan_params,
                "anti_patterns_in_prompt": anti_patterns_found,
            }

            # -------------------------------------------------------------
            # ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT (SqlValidationResult)
            # -------------------------------------------------------------
            e5_val = re.search(r"\* Validation syntaxique\s*:\s*\[([^\]]+)\]", block)
            ast_valid = e5_val.group(1).strip() if e5_val else "NON_EVALUE"

            e5_ctrl = re.search(r"\* Controles valides\s*:\s*([^\n\r]+)", block)
            ast_controls = e5_ctrl.group(1).strip() if e5_ctrl else ""

            if ast_valid not in ["VALIDE", "NON_EVALUE"]:
                alerts.append({
                    "severity": "CRITICAL",
                    "step": "Étape 5 (Bouclier AST)",
                    "code": "AST_VALIDATION_FAILED",
                    "message": f"Rejet par le validateur AST : {ast_valid}"
                })

            step5_data = {
                "ast_valid": ast_valid,
                "controls_passed": ast_controls,
            }

            # -------------------------------------------------------------
            # ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE
            # -------------------------------------------------------------
            e6_statut = re.search(r"\* Statut execution\s*:\s*([^\n\r]+)", block)
            exec_status = e6_statut.group(1).strip() if e6_statut else "N/A"
            if exec_status not in ["SUCCESS", "N/A"]:
                stats["execution_errors"] += 1
                alerts.append({
                    "severity": "CRITICAL",
                    "step": "Étape 6 (Exécution SQL)",
                    "code": "SQL_EXECUTION_ERROR",
                    "message": f"Échec d'exécution de la requête en base de données : {exec_status}"
                })

            e6_lignes = re.search(r"\* Lignes retournees\s*:\s*([^\n\r]+)", block)
            lignes = e6_lignes.group(1).strip() if e6_lignes else "0"

            e6_duree = re.search(r"\* Duree d'execution\s*:\s*([^\n\r]+)", block)
            duree = e6_duree.group(1).strip() if e6_duree else "0 ms"

            e6_cycle = re.search(r"\* Cycle de vie\s*:\s*\[([^\]]+)\]", block)
            lifecycle = e6_cycle.group(1).strip() if e6_cycle else "N/A"

            step6_data = {
                "execution_status": exec_status,
                "rows_returned": lignes,
                "duration": duree,
                "lifecycle_status": lifecycle,
            }

            # -------------------------------------------------------------
            # ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND (ReportingResponse)
            # -------------------------------------------------------------
            e7_mode = re.search(r"\* Mode d'execution\s*:\s*([^\n\r]+)", block)
            e7_qid = re.search(r"\* Query ID final\s*:\s*([^\n\r]+)", block)
            final_qid = e7_qid.group(1).strip() if e7_qid else (e2_qid or "N/A")

            e7_vis = re.search(r"\* Type Visualisation\s*:\s*([^\n\r]+)", block)
            vis_type = e7_vis.group(1).strip() if e7_vis else "aucune"

            e7_syn = re.search(r"\* Synthese formulee\s*:\s*\"([^\"]+)\"", block)
            synthese = e7_syn.group(1).strip() if e7_syn else ""

            # Détection Incohérence Sémantique Restitution
            semantic_corrupted = False
            if sql_divergence and ("52" in synthese or "plainte_count" in synthese) and "plainte" not in question.lower() and "dossier" not in question.lower():
                semantic_corrupted = True
                stats["semantic_synthesis_corruptions"] += 1
                alerts.append({
                    "severity": "CRITICAL",
                    "step": "Étape 7 (Restitution)",
                    "code": "SEMANTIC_SYNTHESIS_CORRUPTED",
                    "message": f"Incohérence sémantique majeure : La synthèse formule '{synthese}' sur la base d'un comptage brut (52) issu du fallback déterministe."
                })

            step7_data = {
                "execution_mode": e7_mode.group(1).strip() if e7_mode else routing,
                "final_query_id": final_qid,
                "visualization": vis_type,
                "synthesis": synthese,
                "semantic_corrupted": semantic_corrupted,
            }

            runs_data.append({
                "run_id": idx,
                "question": question,
                "routing": routing,
                "final_qid": final_qid,
                "lifecycle_status": lifecycle,
                "step1_intent": step1_data,
                "step2_routing": step2_data,
                "step3_subschema": step3_data,
                "step4_candidate_sql": step4_data,
                "step5_ast_shield": step5_data,
                "step6_execution": step6_data,
                "step7_restitution": step7_data,
                "alerts": alerts,
            })

        return {"stats": stats, "runs": runs_data}

    def generate_markdown_report(self, parsed_data: Dict[str, Any], detailed: bool = True) -> str:
        stats = parsed_data["stats"]
        runs = parsed_data["runs"]

        md = []
        md.append("# 🏛️ Rapport d'Audit Exhaustif du Workflow Text-to-SQL Gouverné")
        md.append(f"**Fichier audité :** `{self.log_path.name}`\n")
        
        md.append("## 1. Tableau de Bord Exécutif & Indicateurs de Risque")
        md.append(f"- **Nombre total de requêtes auditées :** {stats['total_runs']}")
        md.append(f"- **Hits Fast-Path (Catalogue Homologué) :** {stats['fast_path_hits']}")
        md.append(f"- **Hits Candidate-Path (Requêtes en Attente) :** {stats['candidate_path_hits']}")
        md.append(f"- **Générations LLM Nemotron :** {stats['generative_llm_calls']}")
        md.append(f"- 🚨 **Replis silencieux (Failures Pydantic) :** {stats['silent_fallbacks_total']} (Étape 1: {stats['step1_pydantic_errors']}, Étape 4: {stats['step4_pydantic_errors']})")
        md.append(f"- 🚨 **Divergences SQL Brut LLM vs SQL Exécuté :** {stats['sql_divergences_detected']}")
        md.append(f"- 🚨 **Incohérences sémantiques dans la synthèse :** {stats['semantic_synthesis_corruptions']}")
        md.append(f"- ⚠️ **Désynchronisations temporelles (Candidate-Path) :** {stats['temporal_mismatches_detected']}")
        md.append(f"- ⚠️ **Requêtes avec paramètres orphelins :** {stats['orphan_parameters_detected']}")
        md.append(f"- 🔒 **Fuites potentielles de données sensibles (PII) :** {stats['pii_leak_detected']}")
        md.append(f"- ❌ **Erreurs d'exécution base de données :** {stats['execution_errors']}\n")

        md.append("## 2. Matrice Récapitulative des Requêtes\n")
        md.append("| # | Question | Circuit | Query ID | SQL Divergent ? | Repli Silencieux ? | Alerte Temporelle ? | Statut BDD |")
        md.append("|---|---|---|---|---|---|---|---|")
        for r in runs:
            has_div = "🚨 OUI" if r["step4_candidate_sql"]["sql_divergence"] else "Non"
            has_fb = "🚨 OUI" if (r["step1_intent"]["pydantic_error"] or r["step4_candidate_sql"]["pydantic_error"]) else "Non"
            has_time_mismatch = "⚠️ OUI" if r["step2_routing"]["temporal_mismatch"] else "Non"
            md.append(f"| {r['run_id']:02d} | {r['question']} | `{r['routing']}` | `{r['final_qid']}` | {has_div} | {has_fb} | {has_time_mismatch} | {r['step6_execution']['execution_status']} |")
        md.append("\n" + "=" * 80 + "\n")

        if detailed:
            md.append("## 3. Détail Exhaustif des 7 Contrats par Question\n")
            for r in runs:
                s1 = r["step1_intent"]
                s2 = r["step2_routing"]
                s3 = r["step3_subschema"]
                s4 = r["step4_candidate_sql"]
                s5 = r["step5_ast_shield"]
                s6 = r["step6_execution"]
                s7 = r["step7_restitution"]

                md.append(f"### [Requête N° {r['run_id']:02d}] \"{r['question']}\"")
                md.append(f"**Aiguillage Global :** `{r['routing']}` | **Query ID Final :** `{r['final_qid']}` | **Statut Cycle de Vie :** `{r['lifecycle_status']}`\n")

                if r["alerts"]:
                    md.append("#### 🚨 Alertes & Anomalies Détectées :")
                    for a in r["alerts"]:
                        icon = "🚨" if a["severity"] == "CRITICAL" else ("⚠️" if a["severity"] == "HIGH" else "ℹ️")
                        md.append(f"- {icon} **[{a['step']}] {a['code']}** : {a['message']}")
                    md.append("")

                # Étape 1
                md.append("#### [ÉTAPE 1 : RÉSOLUTION D'INTENTION CANONIQUE]")
                md.append(f"- **Source de résolution :** `{s1['source']}`")
                md.append(f"- **Statut résolu :** `{s1['status']}` | **Entité :** `{s1['entity']}` | **Mesure :** `{s1['measure']}`")
                md.append(f"- **Dimensions :** `{s1['dimensions']}` | **Filtres :** `{s1['filters']}` | **Période :** `{s1['time']}`")
                if s1["contract_json"]:
                    md.append("```json\n" + json.dumps(s1["contract_json"], indent=2, ensure_ascii=False) + "\n```")
                if s1["pydantic_error"]:
                    md.append(f"> ❌ **Échec Pydantic Étape 1** : `{s1['pydantic_error']}`\n")

                # Étape 2
                md.append("#### [ÉTAPE 2 : CIRCUIT FAST-PATH & CANDIDATE-PATH]")
                md.append(f"- **Circuit retenu :** `{s2['routing']}`")
                md.append(f"- **Query ID associé :** `{s2['query_id']}`")
                if s2["libelle_metier"]:
                    md.append(f"- **Libellé métier homologué :** \"{s2['libelle_metier']}\"")
                if s2["template_sql"]:
                    md.append(f"```sql\n-- SQL DU TEMPLATE HOMOLOGUÉ :\n{s2['template_sql']}\n```")
                if s2["temporal_mismatch"]:
                    md.append(f"> ⚠️ **Désynchronisation Temporelle** : Requête réutilisée sans filtre temporel alors que la question précisait une date !\n")

                # Étape 3
                md.append("#### [ÉTAPE 3 : EXTRACTION DU SOUS-SCHÉMA MINIMAL]")
                md.append(f"- **Tables autorisées :** `{s3['allowed_tables']}`")
                md.append(f"- **Étanchéité PII / RGPD :** {'✅ Strictement respectée (aucune colonne sensible)' if s3['pii_protected'] else '❌ FUITE DÉTECTÉE'}\n")

                # Étape 4
                md.append("#### [ÉTAPE 4 : GÉNÉRATEUR SQL GOUVERNÉ]")
                if s4["raw_llm_json"]:
                    md.append("**Contrat JSON Brut émis par le LLM (Nemotron) :**")
                    md.append("```json\n" + json.dumps(s4["raw_llm_json"], indent=2, ensure_ascii=False) + "\n```")
                if s4["pydantic_error"]:
                    md.append(f"> ❌ **Erreur Pydantic Candidate** : `{s4['pydantic_error']}`")
                    md.append(f"> ⚠️ **Action Système** : Repli silencieux immédiat vers le générateur déterministe (`generate_candidate_fallback`) !")
                if s4["candidate_sql"]:
                    md.append(f"```sql\n-- REQUÊTE SQL CANDIDATE RETENUE :\n{s4['candidate_sql']}\n```")
                if s4["orphan_parameters"]:
                    md.append(f"- ⚠️ **Paramètres orphelins déclarés :** `{s4['orphan_parameters']}`")
                if s4["anti_patterns_in_prompt"]:
                    md.append(f"- **Anti-patterns injectés dans le prompt ({len(s4['anti_patterns_in_prompt'])}) :**")
                    for ap in s4["anti_patterns_in_prompt"][:2]:
                        md.append(f"  * {ap}")

                # Étape 5
                md.append("#### [ÉTAPE 5 : BOUCLIER DE SÉCURITÉ AST SQLGLOT]")
                md.append(f"- **Validation syntaxique :** `[{s5['ast_valid']}]`")
                md.append(f"- **Contrôles validés :** {s5['controls_passed'] or 'Contrôles nominaux'}\n")

                # Étape 6
                md.append("#### [ÉTAPE 6 : EXÉCUTION SQL SÉCURISÉE & CYCLE DE VIE]")
                md.append(f"- **Statut d'exécution BDD :** `{s6['execution_status']}`")
                md.append(f"- **Lignes retournées :** `{s6['rows_returned']}` | **Durée :** `{s6['duration']}`")
                md.append(f"- **Cycle de vie :** `{s6['lifecycle_status']}`\n")

                # Étape 7
                md.append("#### [ÉTAPE 7 : RESTITUTION & CONTRAT FRONTEND]")
                md.append(f"- **Mode d'exécution :** `{s7['execution_mode']}` | **Visualisation :** `{s7['visualization']}`")
                md.append(f"- **Synthèse formulée :** \"{s7['synthesis']}\"")
                if s7["semantic_corrupted"]:
                    md.append("> 🚨 **INCOHÉRENCE SÉMANTIQUE DÉTECTÉE** : Un comptage brut de dossiers a été présenté sous l'intitulé d'une métrique différente !\n")

                md.append("-" * 80 + "\n")

        return "\n".join(md)
