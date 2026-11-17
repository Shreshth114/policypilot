"""Integration checks for the free demo; no network calls or local DB writes."""
import os
import re
import tempfile
import unittest

from pathlib import Path

temporary_storage = tempfile.TemporaryDirectory()
os.environ.update(
    SEED_POLICIES="true",
    STORAGE_DIR=temporary_storage.name,
    DATABASE_URL=f"sqlite:///{temporary_storage.name}/test.db",
    LLM_PROVIDER="local",
    EMBEDDING_PROVIDER="local",
)

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_engine


class DeploymentTests(unittest.TestCase):
    def test_website_and_bundled_catalog_survive_repeated_startup(self):
        self.assertTrue(Path("frontend/dist/index.html").is_file(), "Build the frontend first")
        for _ in range(2):
            with TestClient(app) as client:
                health = client.get("/api/health").json()
                self.assertEqual(health["status"], "healthy")
                self.assertEqual(health["database"]["backend"], "sqlite")
                page = client.get("/")
                self.assertIn('id="root"', page.text)
                assets = re.findall(r'(?:src|href)="(/assets/[^\"]+)"', page.text)
                self.assertTrue(assets)
                for asset in assets:
                    self.assertEqual(client.get(asset).status_code, 200)
                documents = client.get("/api/documents").json()
                self.assertEqual(
                    {d["document_name"] for d in documents},
                    {"code_conduct_MSRIT.pdf", "GEFConductRules.pdf"},
                )
                self.assertEqual(len(documents), 2)
                self.assertTrue(all(d["total_chunks"] > 0 for d in documents))
                search = client.post("/api/retrieval/search", json={
                    "query": "ragging", "mode": "keyword", "top_k": 3,
                })
                self.assertEqual(search.status_code, 200)
                self.assertTrue(search.json()["results"])
                self.assertEqual(client.delete('/api/documents/nonexistent').status_code, 404)
                self.assertEqual(client.post("/api/documents/upload", files={
                    "file": ("test.pdf", b"not a PDF", "application/pdf"),
                }).status_code, 400)
                evaluation = client.post("/api/retrieval/evaluate")
                self.assertEqual(evaluation.status_code, 200)
                self.assertEqual(evaluation.json()["test_queries_evaluated"], 6)
                self.assertEqual(set(evaluation.json()["modes"]), {
                    "semantic", "semantic_hyde", "keyword", "hybrid", "hybrid_hyde",
                })
                self.assertEqual(client.get("/api/nonexistent").status_code, 404)
                self.assertEqual(client.get("/.env").status_code, 404)


if __name__ == "__main__":
    try:
        unittest.main()
    finally:
        get_engine().dispose()
        temporary_storage.cleanup()
