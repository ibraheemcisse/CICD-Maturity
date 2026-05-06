"""
Worker Service - Processes jobs from the queue.

Demonstrates:
- Async job processing
- Resource management (OOM simulation)
- Backpressure handling
"""
import asyncio
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.logger import setup_logger
from shared.models import Job
from shared.queue import QueueClient

logger = setup_logger("worker")
queue_client = QueueClient()

# Track active jobs for observability
active_jobs = 0
processed_jobs = 0
failed_jobs = 0
worker_task = None

# OOM simulation state
oom_enabled = False
memory_leak = []

# Backpressure configuration
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "10"))
QUEUE_DEPTH_WARNING_THRESHOLD = int(os.getenv("QUEUE_DEPTH_WARNING", "50"))
QUEUE_DEPTH_CRITICAL_THRESHOLD = int(os.getenv("QUEUE_DEPTH_CRITICAL", "100"))


async def process_job(job: Job):
    """
    Process a single job.
    
    Args:
        job: Job to process
    """
    global active_jobs, processed_jobs, failed_jobs, memory_leak
    
    active_jobs += 1
    logger.info(f"Processing job {job.job_id} (type: {job.job_type})")
    
    try:
        # Handle special job types
        if job.job_type == "oom_simulation" and oom_enabled:
            # Deliberate memory leak - allocates 100MB per job
            chunk = "x" * (100 * 1024 * 1024)  # 100MB string
            memory_leak.append(chunk)
            logger.warning(
                f"OOM simulation: allocated 100MB (total leaks: {len(memory_leak)})"
            )
        
        # Simulate work
        work_duration = job.payload.get("duration", 2)
        await asyncio.sleep(work_duration)
        
        logger.info(f"Completed job {job.job_id}")
        processed_jobs += 1
        
    except MemoryError as e:
        logger.error(f"Job {job.job_id} failed with OOM: {e}")
        failed_jobs += 1
    except Exception as e:
        logger.error(f"Job {job.job_id} failed: {e}")
        failed_jobs += 1
    finally:
        active_jobs -= 1


async def check_backpressure():
    """
    Monitor queue depth and log backpressure warnings.
    
    In production, this would trigger:
    - Horizontal pod autoscaling
    - Alert notifications
    - Rate limiting at gateway
    """
    queue_depth = await queue_client.get_queue_depth()
    
    if queue_depth >= QUEUE_DEPTH_CRITICAL_THRESHOLD:
        logger.error(
            f"CRITICAL backpressure: queue depth {queue_depth} "
            f"(threshold: {QUEUE_DEPTH_CRITICAL_THRESHOLD})"
        )
    elif queue_depth >= QUEUE_DEPTH_WARNING_THRESHOLD:
        logger.warning(
            f"Backpressure detected: queue depth {queue_depth} "
            f"(threshold: {QUEUE_DEPTH_WARNING_THRESHOLD})"
        )
    
    return queue_depth


async def worker_loop():
    """Main worker loop - consumes jobs from queue with backpressure handling."""
    logger.info(
        f"Worker loop started (max concurrent jobs: {MAX_CONCURRENT_JOBS})"
    )
    
    while True:
        try:
            # Check backpressure
            await check_backpressure()
            
            # Respect concurrency limit (backpressure handling)
            if active_jobs >= MAX_CONCURRENT_JOBS:
                logger.debug(
                    f"Concurrency limit reached "
                    f"({active_jobs}/{MAX_CONCURRENT_JOBS}), waiting..."
                )
                await asyncio.sleep(1)
                continue
            
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
    queue_depth = await queue_client.get_queue_depth()
    
    # Degraded if queue depth critical
    status = "healthy"
    if queue_depth >= QUEUE_DEPTH_CRITICAL_THRESHOLD:
        status = "degraded"
    
    return JSONResponse(
        status_code=200,
        content={
            "status": status,
            "service": "worker",
            "version": "0.1.0",
            "active_jobs": active_jobs,
            "processed_jobs": processed_jobs,
            "failed_jobs": failed_jobs,
            "queue_depth": queue_depth
        }
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "worker",
        "message": "Worker service is running",
        "active_jobs": active_jobs,
        "max_concurrent_jobs": MAX_CONCURRENT_JOBS,
        "processed_jobs": processed_jobs,
        "failed_jobs": failed_jobs,
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "oom": "/oom/enable and /oom/disable",
            "backpressure": "/backpressure/config",
            "docs": "/docs"
        }
    }


@app.get("/metrics")
async def metrics():
    """Metrics endpoint with backpressure indicators."""
    queue_depth = await queue_client.get_queue_depth()
    
    # Calculate backpressure severity
    backpressure_level = "normal"
    if queue_depth >= QUEUE_DEPTH_CRITICAL_THRESHOLD:
        backpressure_level = "critical"
    elif queue_depth >= QUEUE_DEPTH_WARNING_THRESHOLD:
        backpressure_level = "warning"
    
    return {
        "active_jobs": active_jobs,
        "max_concurrent_jobs": MAX_CONCURRENT_JOBS,
        "processed_jobs": processed_jobs,
        "failed_jobs": failed_jobs,
        "queue_depth": queue_depth,
        "backpressure_level": backpressure_level,
        "oom_enabled": oom_enabled,
        "memory_leak_count": len(memory_leak),
        "service": "worker"
    }


@app.get("/backpressure/config")
async def backpressure_config():
    """Get backpressure configuration."""
    return {
        "max_concurrent_jobs": MAX_CONCURRENT_JOBS,
        "queue_depth_warning_threshold": QUEUE_DEPTH_WARNING_THRESHOLD,
        "queue_depth_critical_threshold": QUEUE_DEPTH_CRITICAL_THRESHOLD
    }


@app.post("/oom/enable")
async def enable_oom():
    """Enable OOM simulation mode."""
    global oom_enabled
    oom_enabled = True
    logger.warning("OOM simulation ENABLED")
    return {
        "status": "enabled",
        "message": "Worker will leak memory on oom_simulation jobs"
    }


@app.post("/oom/disable")
async def disable_oom():
    """Disable OOM simulation and clear leak."""
    global oom_enabled, memory_leak
    oom_enabled = False
    memory_leak.clear()
    logger.info("OOM simulation DISABLED and memory leak cleared")
    return {"status": "disabled", "message": "Memory leak cleared"}


@app.get("/oom/status")
async def oom_status():
    """Get OOM simulation status."""
    import psutil
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    return {
        "oom_enabled": oom_enabled,
        "memory_leak_allocations": len(memory_leak),
        "process_memory_mb": round(memory_mb, 2)
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
