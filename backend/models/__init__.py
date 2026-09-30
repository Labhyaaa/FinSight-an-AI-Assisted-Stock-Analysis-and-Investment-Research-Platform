"""
FinSight – Models package.
Provides shared database cursor helper with optional psycopg2 support.
When psycopg2 is not available, models fall back to the in-memory store.
"""
from flask import g

# Conditional psycopg2 import
try:
    import psycopg2.extras
    _HAS_PSYCOPG2 = True
except ImportError:
    _HAS_PSYCOPG2 = False


def get_cursor():
    """Return a RealDictCursor for the current Flask request."""
    if not _HAS_PSYCOPG2 or not g.get("db"):
        raise RuntimeError("Database connection not available")
    return g.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def use_db():
    """Return True if PostgreSQL is available and actively connected."""
    if not _HAS_PSYCOPG2:
        return False
    try:
        from app import get_db
        return get_db() is not None
    except Exception:
        return False

