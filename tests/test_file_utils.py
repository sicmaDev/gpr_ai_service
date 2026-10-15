"""
Tests unitaires pour les utilitaires de gestion sécurisée des fichiers (zero-overwrite).
"""

import tempfile
import unittest
from pathlib import Path

from tools.common.file_utils import (
    get_run_timestamp,
    get_unique_filepath,
    safe_write_text,
)


class TestFileUtils(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_run_timestamp_format(self):
        ts = get_run_timestamp()
        self.assertTrue(len(ts) == 15)  # YYYYMMDD_HHMMSS
        self.assertIn("_", ts)

    def test_unique_filepath_non_existing(self):
        target = self.base_dir / "rapport.md"
        resolved = get_unique_filepath(target)
        self.assertEqual(resolved, target)

    def test_unique_filepath_existing_no_overwrite(self):
        target = self.base_dir / "rapport.md"
        target.write_text("Ancien rapport", encoding="utf-8")

        # Résolution pour un nouveau fichier avec le même nom
        resolved = get_unique_filepath(target, timestamp="20261014_120000")
        self.assertNotEqual(resolved, target)
        self.assertEqual(resolved.name, "rapport_20261014_120000.md")
        self.assertEqual(target.read_text(encoding="utf-8"), "Ancien rapport")

    def test_unique_filepath_collision_chain(self):
        target = self.base_dir / "rapport.md"
        target.write_text("Ancien 1", encoding="utf-8")

        colliding = self.base_dir / "rapport_20261014_120000.md"
        colliding.write_text("Ancien 2", encoding="utf-8")

        resolved = get_unique_filepath(target, timestamp="20261014_120000")
        self.assertEqual(resolved.name, "rapport_20261014_120000_1.md")

    def test_safe_write_text_preserves_previous_content(self):
        target = self.base_dir / "logs" / "execution.log"
        path1 = safe_write_text(target, "Run 1 data", timestamp="20261014_100000")
        self.assertTrue(path1.exists())
        self.assertEqual(path1.read_text(encoding="utf-8"), "Run 1 data")

        # Deuxième écriture sur la même cible
        path2 = safe_write_text(target, "Run 2 data", timestamp="20261014_100000")
        self.assertNotEqual(path1, path2)
        self.assertTrue(path2.exists())
        self.assertEqual(path2.read_text(encoding="utf-8"), "Run 2 data")

        # Vérifier que le fichier initial n'a PAS été écrasé
        self.assertEqual(path1.read_text(encoding="utf-8"), "Run 1 data")


if __name__ == "__main__":
    unittest.main()
