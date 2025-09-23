"""
FastAPI application entrypoint for EchoScan.
"""

from fastapi import FastAPI

# Create FastAPI application instance
app = FastAPI(
    title="EchoScan API",
    description="Math-Anchored Symbolic Detection Engine API",
    version="1.0.0"
)

@app.get("/")
def read_root():
    """Root endpoint returning basic API information."""
    return {
        "message": "Welcome to EchoScan API",
        "description": "Math-Anchored Symbolic Detection Engine",
        "version": "1.0.0",
        "endpoints": {
            "root": "/",
            "health": "/health"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "EchoScan API"}