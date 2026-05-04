"""
Worker Service - Processes jobs from the queue.

Demonstrates:
- Async job processing
- Resource management (OOM simulation)
- Backpressure handling
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import asyncio

# Add parent directory to path for shared imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.models import Job, JobStatus
from shared.queue import QueueClient
from shared.logger import setup_logger

logger = setup_logger("worker")
queue_client = QueueClient()

# Track active jobs for observability
active_jobs = 0
processed_jobs = 0
worker_task = None


async def process_job(job: Job):
    """
    Process a single job.
    
    Args:
        job: Job to process
    """
    global active_jobs, processed_jobs
    
    active_jobs += 1
    logger.info(f"Processing job {job.job_id} (type: {job.job_type})")
    
    try:
        # Simulate work
        await asyncio.sleep(2)
        
        logger.info(f"Completed job {job.job_id}")
        processed_jobs += 1
        
    except Exception as e:
        logger.error(f"Job {job.job_id} failed: {e}")
    finally:
        active_jobs -= 1


async def worker_loop():
    """Main worker loop - consumes jobs from queue."""
    logger.info("Worker loop started")
    
    while True:
        try:
            job = await queue_client.dequeue(timeout=5)
            
            if job:
                # Process job asynchronously
                asyncio.create_task(process_job(job))
            else:
                # No jobs available, continue polling
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management."""
    global worker_task
    
    await queue_client.connect()
    worker_task = asyncio.create_task(worker_loop())
    logger.info("Worker service started")
    
    yield
    
    if worker_task:
        worker_task.cancel()
    await queue_client.disconnect()
    logger.info("Worker service stopped")


app = FastAPI(
    title="Worker Service",
    description="Async job processor for distributed system",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint for k8s liveness/readiness probes."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "worker",
            "version": "0.1.0",
            "active_jobs": active_jobs,
            "processed_jobs": processed_jobs
        }
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "worker",
        "message": "Worker service is running",
        "active_jobs": active_jobs,
        "processed_jobs": processed_jobs,
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }


@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint."""
    queue_depth = await queue_client.get_queue_depth()
    return {
        "active_jobs": active_jobs,
        "processed_jobs": processed_jobs,
        "queue_depth": queue_depth,
        "service": "worker"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
