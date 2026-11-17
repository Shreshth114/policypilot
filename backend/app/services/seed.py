"""Restore the bundled policy PDFs on an ephemeral free-tier filesystem."""
import re
from pathlib import Path

from app.core.config import BASE_DIR
from app.core.database import get_session
from app.services.ingestion import ingest_pdf_file


def seed_bundled_policies():
    for pdf in sorted((BASE_DIR / "storage" / "pdfs").glob("*.pdf")):
        with get_session() as db:
            ingest_pdf_file(
                file_path=str(pdf),
                original_filename=re.sub(r"^[0-9a-f]{8}_", "", pdf.name),
                category="Disciplinary & Conduct",
                db=db,
            )
