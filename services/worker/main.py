"""
Worker Service - Processes jobs from the queue.

Demonstrates:
- Async job processing
- Resource management (OOM simulation)
- Backpressure handling
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import asyncio

app = FastAPI(
    title="Worker Service",
    description="Async job processor for distributed system",
    version="0.1.0"
)

# Track active jobs for observability
active_jobs = 0


@app.get("/health")
async def health_check():
    """Health check endpoint for k8s liveness/readiness probes."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "worker",
            "version": "0.1.0",
            "active_jobs": active_jobs
        }
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "worker",
        "message": "Worker service is running",
        "active_jobs": active_jobs,
        "endpoints": {
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint (Prometheus format later)."""
    return {
        "active_jobs": active_jobs,
        "service": "worker"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
