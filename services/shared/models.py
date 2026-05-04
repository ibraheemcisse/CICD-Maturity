"""
Shared data models used across services.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    """Job model for async work processing."""
    job_id: str = Field(..., description="Unique job identifier")
    job_type: str = Field(..., description="Type of job to execute")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Job payload")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current job status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(default=0, description="Number of retry attempts")

    class Config:
        use_enum_values = True


class HealthResponse(BaseModel):
    """Standard health check response."""
    status: str
    service: str
    version: str
    details: Optional[Dict[str, Any]] = None
