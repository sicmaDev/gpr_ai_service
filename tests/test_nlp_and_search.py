import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from main import app


class NlpAndSearchIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_app_starts_and_reporting_router_is_not_registered(self):
        """Vérifie que l'application démarre sans reporting et que les routes d'analyse/recherche sont actives."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "online")

        # Vérifier que les routes de reporting ne sont plus présentes
        routes = [route.path for route in app.routes]
        self.assertNotIn("/reporting/dashboard", routes)
        self.assertNotIn("/reporting/query", routes)
        self.assertNotIn("/reporting/feedback", routes)

        # Vérifier que les routes NLP / Search / Transcribe sont bien actives
        self.assertIn("/analyze/", routes)
        self.assertIn("/analyze/stream", routes)
        self.assertIn("/search/", routes)
        self.assertIn("/search/stream", routes)
        self.assertIn("/transcribe/", routes)

    def test_analyze_route_handles_request_gracefully(self):
        """Vérifie que la route /analyze fonctionne sans régression."""
        with patch("app.routers.analyze.analyze_sentiment_and_urgency") as mock_nlp:
            mock_nlp.return_value = (
                "FAIBLE",
                "NEGATIF",
                ["carte", "distributeur"],
                "Cartes bancaires",
                "Carte avalée",
                "Le client signale une carte bloquée."
            )
            response = self.client.post(
                "/analyze/",
                json={"texte": "Ma carte a été avalée par le distributeur hier soir."},
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["urgence"], "FAIBLE")
            self.assertEqual(data["sentiment"], "NEGATIF")
            self.assertEqual(data["categorie_suggeree"], "Cartes bancaires")
            self.assertEqual(data["motif_suggere"], "Carte avalée")

    def test_search_route_handles_request_gracefully(self):
        """Vérifie que la route /search fonctionne sans régression."""
        with patch("app.routers.search.vector_db.search_similar", return_value=[]):
            response = self.client.post(
                "/search/",
                json={"texte_actuel": "Comment réinitialiser un mot de passe ?"},
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["resultats_trouves"], 0)
            self.assertEqual(data["similar_claims"], [])
            self.assertEqual(data["message"], "Aucune similarité trouvée.")


if __name__ == "__main__":
    unittest.main()
