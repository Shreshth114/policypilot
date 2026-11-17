"""
Main FastAPI Application Entrypoint for PolicyPilot.
"""
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_engine, get_db, Base, is_sqlite_active, is_pgvector_active
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.retrieval import router as retrieval_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("policypilot")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables are created
    logger.info("Initializing database tables...")
    eng = get_engine()
    Base.metadata.create_all(bind=eng)
    logger.info("Database initialized successfully.")
    if settings.SEED_POLICIES:
        from app.services.seed import seed_bundled_policies
        seed_bundled_policies()
    yield
    # Shutdown
    logger.info("Shutting down PolicyPilot backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Campus Policy Discovery Assistant with HyDE, Hybrid Search & MCP",
    lifespan=lifespan
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])
app.include_router(retrieval_router, prefix="/api/retrieval", tags=["Retrieval"])

@app.get("/", tags=["Root"])
def root():
    index = Path(__file__).resolve().parents[2] / "frontend" / "dist" / "index.html"
    if index.is_file():
        return FileResponse(index)
    return {
        "service": "PolicyPilot Backend",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """
    Verify application health, database connectivity, and vector capabilities.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1")).fetchone()
    except Exception as e:
        db_status = f"unhealthy: {e}"

    return {
        "status": "healthy" if "unhealthy" not in db_status else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": {
            "status": db_status,
            "backend": "sqlite" if (is_sqlite_active() or getattr(db.bind.dialect, "name", "") == "sqlite") else "postgresql",
            "pgvector_active": is_pgvector_active()
        },
        "config": {
            "llm_provider": settings.LLM_PROVIDER,
            "embedding_provider": settings.EMBEDDING_PROVIDER,
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP,
            "rrf_k": settings.RRF_K,
            "demo_mode": settings.DEMO_MODE
        }
    }


# Register after API routes so missing API endpoints keep their JSON 404s.
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="website")

