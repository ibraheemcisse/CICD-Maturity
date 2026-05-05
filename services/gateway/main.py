"""
Gateway Service - API entry point for the distributed system.

Handles:
- Job submission to queue
- Circuit breaking for queue failures
- Rate limiting (future)
"""
import os
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from shared.logger import setup_logger
from shared.models import Job, JobStatus
from shared.queue import QueueClient

logger = setup_logger("gateway")
queue_client = QueueClient()

# Circuit breaker for queue operations
queue_breaker = CircuitBreaker(
    name="redis_queue",
    config=CircuitBreakerConfig(
        failure_threshold=3,
        timeout=30,
        success_threshold=2
    )
)


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
    try:
        queue_depth = await queue_client.get_queue_depth()
        circuit_state = queue_breaker.get_state()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": "gateway",
                "version": "0.1.0",
                "queue_depth": queue_depth,
                "circuit_breaker": circuit_state
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "gateway",
                "error": str(e)
            }
        )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "gateway",
        "message": "Gateway service is running",
        "circuit_breaker": queue_breaker.get_state(),
        "endpoints": {
            "health": "/health",
            "submit": "/jobs/submit",
            "circuit": "/circuit/status",
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
    # Check circuit breaker
    if not queue_breaker.allow_request():
        logger.warning("Circuit breaker OPEN - rejecting request")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable (circuit breaker open)"
        )
    
    job = Job(
        job_id=str(uuid.uuid4()),
        job_type=job_type,
        payload=payload or {},
        status=JobStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    try:
        success = await queue_client.enqueue(job)
        
        if not success:
            queue_breaker.record_failure()
            raise HTTPException(status_code=500, detail="Failed to enqueue job")
        
        queue_breaker.record_success()
        logger.info(f"Submitted job {job.job_id}")
        
        return {
            "job_id": job.job_id,
            "status": job.status,
            "message": "Job submitted successfully"
        }
    except Exception as e:
        queue_breaker.record_failure()
        logger.error(f"Job submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queue/depth")
async def queue_depth():
    """Get current queue depth for monitoring."""
    try:
        depth = await queue_client.get_queue_depth()
        return {"queue_depth": depth}
    except Exception as e:
        logger.error(f"Failed to get queue depth: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/circuit/status")
async def circuit_status():
    """Get circuit breaker status."""
    return queue_breaker.get_state()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
