#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests unitaires pour le script de surveillance check_alerts.py (Bloc P4 - Tâche 4.3).
Valide les cas nominaux, les dépassements de seuil critique et le mode dry-run.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Import du module check_alerts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_alerts

class TestCheckAlerts(unittest.TestCase):

    @patch("check_alerts.envoyer_alerte_teams")
    @patch("check_alerts.envoyer_alerte_email")
    def test_nominal_under_threshold(self, mock_email, mock_teams):
        """Cas nominal : nb_cas <= seuil -> aucune alerte envoyée."""
        code = check_alerts.surveiller_indicateurs(
            wren_url="http://mock-wren:3005/api/v1/run_sql",
            seuil=10,
            channel="all",
            mock_count=4,
            dry_run=True
        )
        self.assertEqual(code, 0)
        mock_teams.assert_not_called()
        mock_email.assert_not_called()

    @patch("check_alerts.envoyer_alerte_teams")
    @patch("check_alerts.envoyer_alerte_email")
    def test_exceeding_threshold_triggers_alerts(self, mock_email, mock_teams):
        """Cas d'alerte : nb_cas > seuil -> déclenchement des alertes sur les canaux."""
        code = check_alerts.surveiller_indicateurs(
            wren_url="http://mock-wren:3005/api/v1/run_sql",
            seuil=10,
            channel="all",
            mock_count=14,
            dry_run=True
        )
        self.assertEqual(code, 0)
        mock_teams.assert_called_once_with(14, 10, check_alerts.DEFAULT_TEAMS_WEBHOOK, dry_run=True)
        mock_email.assert_called_once_with(14, 10, dry_run=True)

    @patch("check_alerts.requests.post")
    def test_real_wren_api_payload_parsing(self, mock_post):
        """Vérifie que la réponse JSON de run_sql est correctement analysée."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "records": [{"nb_graves_non_resolues": 12}],
            "columns": [{"name": "nb_graves_non_resolues"}]
        }
        mock_post.return_value = mock_response

        with patch("check_alerts.envoyer_alerte_teams") as mock_teams:
            code = check_alerts.surveiller_indicateurs(
                wren_url="http://mock-wren:3005/api/v1/run_sql",
                seuil=10,
                channel="teams",
                dry_run=True
            )
            self.assertEqual(code, 0)
            mock_teams.assert_called_once()

    def test_dry_run_teams_generation(self):
        """Valide la génération de la MessageCard Teams en mode dry-run."""
        success = check_alerts.envoyer_alerte_teams(nb_cas=15, seuil=10, webhook_url="", dry_run=True)
        self.assertTrue(success)

    def test_dry_run_email_generation(self):
        """Valide la génération du template HTML d'email en mode dry-run."""
        success = check_alerts.envoyer_alerte_email(nb_cas=15, seuil=10, dry_run=True)
        self.assertTrue(success)

if __name__ == "__main__":
    unittest.main()
