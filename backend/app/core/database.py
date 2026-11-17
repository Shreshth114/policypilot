"""
Database Connection & Session Management for PolicyPilot.
Handles PostgreSQL connection, vector extension initialization,
and graceful schema setup.
"""
import logging
import socket
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Global flag to denote whether pgvector extension is active
HAS_PGVECTOR_EXTENSION = False
IS_SQLITE = False

def is_postgres_listening(host: str, port: int) -> bool:
    """Instant socket check to avoid long psycopg2 connection hangs."""
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def init_postgres_db():
    """
    Connect to default 'postgres' database to ensure 'policypilot' DB exists.
    """
    if not is_postgres_listening(settings.DB_HOST, settings.DB_PORT):
        raise ConnectionError(f"PostgreSQL not listening on {settings.DB_HOST}:{settings.DB_PORT}")

    default_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/postgres"
    try:
        temp_engine = create_engine(default_url, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 2})
        with temp_engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname='{settings.DB_NAME}'")
            ).fetchone()
            if not result:
                conn.execute(text(f"CREATE DATABASE {settings.DB_NAME}"))
                logger.info(f"Created database '{settings.DB_NAME}'.")
        temp_engine.dispose()
    except Exception as e:
        logger.warning(f"Could not connect to PostgreSQL ({e}).")
        raise e

# Attempt to connect to configured PostgreSQL database
engine = None
SessionLocal = None

def get_engine():
    global engine, SessionLocal, HAS_PGVECTOR_EXTENSION, IS_SQLITE
    if engine is not None:
        return engine

    if settings.DATABASE_URL and settings.DATABASE_URL.startswith("sqlite:"):
        engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
        IS_SQLITE = True
        HAS_PGVECTOR_EXTENSION = False

    if engine is None and is_postgres_listening(settings.DB_HOST, settings.DB_PORT):
        try:
            init_postgres_db()
            db_url = settings.sync_database_url
            engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 2})
            with engine.connect() as conn:
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    conn.commit()
                    HAS_PGVECTOR_EXTENSION = True
                    logger.info("Native PostgreSQL 'vector' extension is enabled!")
                except Exception as ext_err:
                    logger.info(f"pgvector extension not loaded in PostgreSQL: {ext_err}")
                    HAS_PGVECTOR_EXTENSION = False
            IS_SQLITE = False
            logger.info(f"Connected successfully to PostgreSQL at {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        except Exception as pg_err:
            logger.warning(f"PostgreSQL connection failed ({pg_err}). Falling back to SQLite.")
            engine = None

    if engine is None:
        sqlite_path = settings.STORAGE_DIR + "/policypilot.db"
        sqlite_url = f"sqlite:///{sqlite_path}"
        engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        IS_SQLITE = True
        HAS_PGVECTOR_EXTENSION = False
        logger.info(f"Using local SQLite database at {sqlite_path}")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

def is_sqlite_active() -> bool:
    global IS_SQLITE
    return IS_SQLITE

def is_pgvector_active() -> bool:
    global HAS_PGVECTOR_EXTENSION
    return HAS_PGVECTOR_EXTENSION

def get_session():
    """Returns a new Session instance."""
    global SessionLocal
    if SessionLocal is None:
        get_engine()
    return SessionLocal()

def get_db():
    """
    FastAPI dependency yielding a database session.
    """
    db = get_session()
    try:
        yield db
    finally:
        db.close()

