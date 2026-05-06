"""
PostgreSQL database client and models.
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, Enum as SQLEnum
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from datetime import datetime
from typing import Optional
import enum

from .config import Config
from .logger import setup_logger

logger = setup_logger("database")

Base = declarative_base()


class JobStatusDB(str, enum.Enum):
    """Job status for database storage."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobRecord(Base):
    """Job persistence model."""
    __tablename__ = "jobs"
    
    job_id = Column(String(36), primary_key=True)
    job_type = Column(String(50), nullable=False, index=True)
    payload = Column(Text, nullable=False)  # JSON string
    status = Column(SQLEnum(JobStatusDB), nullable=False, default=JobStatusDB.PENDING, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)


class DatabaseClient:
    """Async PostgreSQL client."""
    
    def __init__(self):
        # Use asyncpg driver
        db_url = Config.get_postgres_url().replace("postgresql://", "postgresql+asyncpg://")
        self.engine = create_async_engine(db_url, echo=False)
        self.SessionLocal = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def create_tables(self):
        """Create database tables if they don't exist."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")
    
    async def close(self):
        """Close database connections."""
        await self.engine.dispose()
        logger.info("Database connections closed")
    
    def get_session(self) -> AsyncSession:
        """Get a new database session."""
        return self.SessionLocal()
