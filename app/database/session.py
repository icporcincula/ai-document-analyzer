"""
Database session configuration and connection management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool
import os
from typing import Generator
import logging

from app.utils.config import get_settings

logger = logging.getLogger(__name__)

# Get database URL from settings
settings = get_settings()
DATABASE_URL = settings.database_url

# Create engine
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration for development
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL logging
    )
else:
    # PostgreSQL configuration for production
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=0,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    try:
        # Import all models to ensure they are registered
        from app.database.models import AnalysisResult, ExportHistory, MetricsSnapshot, AuditLog
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise


def get_database_health() -> dict:
    """Get database health status."""
    try:
        db = SessionLocal()
        # Test connection with a simple query
        db.execute("SELECT 1").scalar()
        db.close()
        
        return {
            "status": "healthy",
            "database_url": DATABASE_URL.replace(settings.database_password, "***") if settings.database_password else DATABASE_URL,
            "connection_test": "passed"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "database_url": DATABASE_URL.replace(settings.database_password, "***") if settings.database_password else DATABASE_URL,
            "connection_test": "failed",
            "error": str(e)
        }


def migrate_database():
    """Handle database migrations."""
    try:
        from alembic.config import Config
        from alembic import command
        
        # Alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Database migration failed: {str(e)}")
        # For now, we'll continue without migrations in case alembic is not configured
        logger.warning("Continuing without migrations - this is expected in development")