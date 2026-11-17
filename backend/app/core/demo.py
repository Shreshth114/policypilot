"""Keep the public free-tier deployment's policy catalog read-only."""
from fastapi import HTTPException

from app.core.config import settings


def require_writable_catalog():
    if settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Policy changes are disabled in the public demo.")
