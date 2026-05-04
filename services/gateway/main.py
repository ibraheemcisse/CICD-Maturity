"""
Gateway Service - API entry point for the distributed system.

Handles:
- Job submission to queue
- Rate limiting (future)
- Circuit breaking (future)
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import uuid
from datetime import datetime

# Add parent directory to path for shared imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.models import Job, JobStatus
from shared.queue import QueueClient
from shared.logger import setup_logger

logger = setup_logger("gateway")
queue_client = QueueClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for queue connection."""
    await queue_client.connect()
    logger.info("Gateway service started")
    yield
    await queue_client.disconnect()
    logger.info("Gateway service stopped")


app = FastAPI(
    title="Gateway Service",
    description="API Gateway for distributed job processing system",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint for k8s liveness/readiness probes."""
    queue_depth = await queue_client.get_queue_depth()
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "gateway",
            "version": "0.1.0",
            "queue_depth": queue_depth
        }
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "gateway",
        "message": "Gateway service is running",
        "endpoints": {
            "health": "/health",
            "submit": "/jobs/submit",
            "docs": "/docs"
        }
    }


@app.post("/jobs/submit")
async def submit_job(job_type: str, payload: dict = None):
    """
    Submit a job to the processing queue.
    
    Args:
        job_type: Type of job to execute
        payload: Optional job payload
    """
    job = Job(
        job_id=str(uuid.uuid4()),
        job_type=job_type,
        payload=payload or {},
        status=JobStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    success = await queue_client.enqueue(job)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to enqueue job")
    
    logger.info(f"Submitted job {job.job_id}")
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "message": "Job submitted successfully"
    }


@app.get("/queue/depth")
async def queue_depth():
    """Get current queue depth for monitoring."""
    depth = await queue_client.get_queue_depth()
    return {"queue_depth": depth}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
