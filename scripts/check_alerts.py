#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de surveillance et d'alerte automatisée basé sur Wren AI & GPR Banque.
Surveille en temps réel les réclamations de niveau GRAVE non résolues et les dépassements de SLA.
Référence : GUIDE_API_DASHBOARD_ET_ALERTING.md (§9 Alerting & Notifications Automatisées, §10 Planification).

Usage:
    python check_alerts.py [--dry-run] [--seuil 10] [--channel all|teams|email] [--wren-url URL]
"""

import os
import sys
import json
import argparse
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import requests
except ImportError:
    print("ERREUR: Le module 'requests' est requis. Installez-le via 'pip install requests'.", file=sys.stderr)
    sys.exit(1)

# ==============================================================================
# 1. CONFIGURATION PAR DÉFAUT & VARIABLES D'ENVIRONNEMENT
# ==============================================================================
DEFAULT_WREN_URL = os.getenv("WREN_API_URL", "http://92.113.31.9:3005/api/v1/run_sql")
DEFAULT_TEAMS_WEBHOOK = os.getenv("TEAMS_WEBHOOK_URL", "")
DEFAULT_SEUIL_CRITIQUE = int(os.getenv("SEUIL_CRITIQUE", "10"))
GPR_DASHBOARD_URL = os.getenv("GPR_DASHBOARD_URL", "http://127.0.0.1:3020/#/rapports/ia")

# Configuration SMTP
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "alertes-reporting-ia@gprbanque.com")
RECEIVER_EMAIL = os.getenv("ALERT_RECIPIENT", "direction-reclamations@gprbanque.com")

# Requête SQL gouvernée certifiée (Guide §9.2)
SQL_ALERT_QUERY = """
SELECT count(c.id) AS nb_graves_non_resolues 
FROM gpr_sicma_online_gps_claim c 
JOIN gpr_sicma_online_gps_objet o ON c.objet_id = o.id 
WHERE c.is_deleted = 0 
  AND c.status != 'SATISFIED' 
  AND o.risque_level = 'GRAVE';
"""

def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

# ==============================================================================
# 2. EXPÉDITION D'ALERTE MICROSOFT TEAMS (MESSAGECARD)
# ==============================================================================
def envoyer_alerte_teams(nb_cas, seuil, webhook_url, dry_run=False):
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "E81123",  # Rouge critique
        "summary": "ALERTE GPR BANQUE : Seuil de réclamations critiques dépassé",
        "sections": [{
            "activityTitle": "🚨 ALERTE GPR BANQUE : Seuil Critique de Réclamations Dépassé",
            "activitySubtitle": f"Notification automatique de surveillance IA générée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            "facts": [
                {"name": "Dossiers critiques en souffrance :", "value": f"**{nb_cas} dossiers**"},
                {"name": "Seuil d'alerte maximal autorisé :", "value": f"{seuil} dossiers"},
                {"name": "Typologie du risque :", "value": "Niveau GRAVE non résolus (SLA dépassé)"},
                {"name": "Recommandation :", "value": "Relance prioritaire des directeurs d'agences et traitement immédiat"}
            ],
            "markdown": True
        }],
        "potentialAction": [
            {
                "@type": "OpenURIOption",
                "name": "Consulter le Tableau de Bord GPR Banque",
                "targets": [{"os": "default", "uri": GPR_DASHBOARD_URL}]
            }
        ]
    }

    if dry_run or not webhook_url:
        log(f"[DRY-RUN] Alerte Microsoft Teams simulée avec succès pour {nb_cas} cas critiques.")
        log(f"[DRY-RUN] Payload Teams : {json.dumps(payload, indent=2, ensure_ascii=False)}")
        return True

    try:
        res = requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
        if res.status_code == 200:
            log(">>> Alerte Microsoft Teams délivrée avec succès.")
            return True
        else:
            log(f">>> Erreur réponse Teams : HTTP {res.status_code} - {res.text}", level="ERROR")
            return False
    except Exception as e:
        log(f">>> Exception réseau vers webhook Teams : {e}", level="ERROR")
        return False

# ==============================================================================
# 3. EXPÉDITION D'ALERTE EMAIL (SMTP HTML)
# ==============================================================================
def envoyer_alerte_email(nb_cas, seuil, dry_run=False):
    html_content = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.5; }}
          .banner {{ background-color: #dc2626; color: white; padding: 18px 24px; border-radius: 8px 8px 0 0; }}
          .card {{ border: 1px solid #e2e8f0; border-radius: 8px; max-width: 600px; margin: 20px auto; overflow: hidden; }}
          .content {{ padding: 24px; }}
          .metric {{ font-size: 32px; font-weight: 800; color: #dc2626; margin: 8px 0; }}
          .btn {{ display: inline-block; background-color: #1d72cd; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: 600; margin-top: 16px; }}
        </style>
      </head>
      <body>
        <div class="card">
          <div class="banner">
            <h2 style="margin: 0; font-size: 18px;">🚨 ALERTE GPR BANQUE : Seuil de Réclamations Critiques</h2>
          </div>
          <div class="content">
            <p>Le système de surveillance automatisée du <b>Module de Reporting IA</b> a détecté un dépassement du seuil de tolérance :</p>
            <div class="metric">{nb_cas} dossiers GRAVES</div>
            <p style="color: #64748b; font-size: 13px;">Seuil d'alerte autorisé : <b>{seuil} dossiers</b>.</p>
            <p>Ces réclamations requièrent une affectation prioritaire immédiate pour préserver les engagements de conformité SLA.</p>
            <a href="{GPR_DASHBOARD_URL}" class="btn">Ouvrir le Tableau de Bord IA GPR Banque</a>
            <p style="font-size: 11px; color: #94a3b8; margin-top: 24px;">Message automatique généré par le moteur de reporting Wren AI (GPR Sicma).</p>
          </div>
        </div>
      </body>
    </html>
    """

    if dry_run or not SMTP_USER:
        log(f"[DRY-RUN] Alerte Email SMTP simulée avec succès pour {nb_cas} cas critiques vers {RECEIVER_EMAIL}.")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 ALERTE GPR BANQUE : {nb_cas} réclamations graves non résolues"
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())

        log(f">>> Alerte Email délivrée avec succès à {RECEIVER_EMAIL}.")
        return True
    except Exception as e:
        log(f">>> Erreur expédition Email SMTP : {e}", level="ERROR")
        return False

# ==============================================================================
# 4. SURVEILLANCE & LOGIQUE PRINCIPALE
# ==============================================================================
def surveiller_indicateurs(wren_url, seuil, channel="all", webhook_url=DEFAULT_TEAMS_WEBHOOK, dry_run=False, mock_count=None):
    log("=== Démarrage de la surveillance proactive des alertes GPR Banque ===")
    log(f"Point d'accès Wren AI : {wren_url}")
    log(f"Seuil critique d'alerte : {seuil} dossiers")
    log(f"Canaux de notification configurés : {channel}")

    nb_cas = 0
    if mock_count is not None:
        nb_cas = int(mock_count)
        log(f"[TEST] Donnée injectée : {nb_cas} cas graves non résolus.")
    else:
        try:
            log("Interrogation du moteur SQL certifié Wren AI...")
            res = requests.post(
                wren_url,
                json={"sql": SQL_ALERT_QUERY},
                headers={"Content-Type": "application/json"},
                timeout=12
            )

            if res.status_code != 200:
                log(f"Erreur HTTP API Wren AI ({res.status_code}) : {res.text}", level="ERROR")
                return 1

            data = res.json()
            records = data.get("records", [])
            if not records:
                log("Aucun enregistrement retourné par Wren AI. Situation nominale.", level="INFO")
                return 0

            nb_cas = int(records[0].get("nb_graves_non_resolues", 0))
            log(f">>> Statut actuel : {nb_cas} réclamation(s) grave(s) non résolue(s).")
        except Exception as e:
            log(f"Exception lors de l'appel à Wren AI : {e}", level="ERROR")
            if not dry_run:
                return 1
            nb_cas = 14  # Valeur par défaut pour dry-run

    # Évaluation du seuil critique
    if nb_cas > seuil:
        log(f"⚠️ DÉPASSEMENT DE SEUIL DÉTECTÉ : {nb_cas} > {seuil} ! Déclenchement des alertes...", level="WARNING")
        
        if channel in ("all", "teams"):
            envoyer_alerte_teams(nb_cas, seuil, webhook_url, dry_run=dry_run)
            
        if channel in ("all", "email"):
            envoyer_alerte_email(nb_cas, seuil, dry_run=dry_run)
    else:
        log(f"✅ Situation sous contrôle. Le volume actuel ({nb_cas}) ne dépasse pas le seuil maximal ({seuil}).")

    log("=== Surveillance terminée avec succès. ===")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Surveillance automatisée des réclamations critiques GPR Banque")
    parser.add_argument("--dry-run", action="store_true", help="Simule l'exécution et l'envoi d'alertes sans requêtes externes réelles")
    parser.add_argument("--seuil", type=int, default=DEFAULT_SEUIL_CRITIQUE, help="Seuil critique de dossiers graves non résolus")
    parser.add_argument("--channel", choices=["all", "teams", "email"], default="all", help="Canal de notification")
    parser.add_argument("--wren-url", default=DEFAULT_WREN_URL, help="URL de l'API run_sql de Wren AI")
    parser.add_argument("--teams-webhook", default=DEFAULT_TEAMS_WEBHOOK, help="URL Webhook Microsoft Teams")
    parser.add_argument("--mock-count", type=int, default=None, help="Force un nombre de dossiers pour validation")

    args = parser.parse_args()

    code = surveiller_indicateurs(
        wren_url=args.wren_url,
        seuil=args.seuil,
        channel=args.channel,
        webhook_url=args.teams_webhook,
        dry_run=args.dry_run,
        mock_count=args.mock_count
    )
    sys.exit(code)

if __name__ == "__main__":
    main()
