"""
Gateway Service - API entry point for the distributed system.

Handles:
- Request routing
- Rate limiting (future)
- Circuit breaking (future)
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os

app = FastAPI(
    title="Gateway Service",
    description="API Gateway for distributed job processing system",
    version="0.1.0"
)


@app.get("/health")
async def health_check():
    """Health check endpoint for k8s liveness/readiness probes."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "gateway",
            "version": "0.1.0"
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
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
