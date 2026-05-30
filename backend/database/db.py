"""
Database connection & session management
========================================
Uses SQLite by default (file: edusakhi.db) — no server needed.
Switch to PostgreSQL later by setting the DATABASE_URL env var.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# ── Database URL ──────────────────────────────────────────────────────────────
# Default: a local SQLite file in the backend folder.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./edusakhi.db")

# SQLite needs check_same_thread=False so FastAPI can use it across threads.
connect_args = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all ORM models inherit from.
Base = declarative_base()


# ── FastAPI dependency ────────────────────────────────────────────────────────
def get_db():
    """Yield a database session and always close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables defined on Base. Safe to call multiple times."""
    # Importing models registers them on Base.metadata.
    from database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
