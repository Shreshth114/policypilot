"""
Document Management Endpoints for PolicyPilot.
Handles PDF upload, document listing, and document deletion.
"""
import os
import shutil
import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.policy import Policy
from app.models.schemas import DocumentResponse, DocumentUploadResponse
from app.services.ingestion import ingest_pdf_file

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("General"),
    version: str = Form("1.0"),
    effective_date: str = Form("2026-2027"),
    db: Session = Depends(get_db)
):
    """
    Upload a university policy PDF.
    Extracts text per page, chunks text, generates embeddings, and saves to database.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported."
        )

    # Save to disk
    safe_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = os.path.join(settings.STORAGE_DIR, safe_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        policy = ingest_pdf_file(
            file_path=file_path,
            original_filename=file.filename,
            category=category,
            version=version,
            effective_date=effective_date,
            db=db
        )

        return {
            "message": f"Successfully ingested policy '{policy.document_name}' ({policy.total_chunks} chunks).",
            "document": policy.to_dict()
        }
    except ValueError as ve:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"Error during document ingestion: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ingestion failed: {e}")

@router.get("", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    """List all indexed university policies."""
    policies = db.query(Policy).order_by(Policy.upload_date.desc()).all()
    return [p.to_dict() for p in policies]

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a policy and all associated chunks."""
    policy = db.query(Policy).filter(Policy.id == document_id).first()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")

    # Remove file from disk if present
    if os.path.exists(policy.file_path):
        try:
            os.remove(policy.file_path)
        except Exception as e:
            logger.warning(f"Could not remove PDF file from disk: {e}")

    db.delete(policy)
    db.commit()
    return {"message": f"Policy '{policy.document_name}' deleted successfully."}
