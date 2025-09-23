#!/usr/bin/env python3
"""
EchoScan FastAPI Application
Provides REST API endpoints for EchoScan functionality including scanning and health checks.
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import echoverifier


# FastAPI app instance
app = FastAPI(
    title="EchoScan API",
    description="Math-Anchored Symbolic Detection Engine API",
    version="1.0.0"
)


class ScanRequest(BaseModel):
    """Request model for scan endpoint."""
    input: str
    mode: Optional[str] = "verify"


class ScanResponse(BaseModel):
    """Response model for scan endpoint."""
    status: str
    result: Dict[str, Any]


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "EchoScan API",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "EchoScan API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "scan": "/api/scan"
        }
    }


@app.post("/api/scan", response_model=ScanResponse)
async def scan_endpoint(request: ScanRequest):
    """
    Main scan endpoint for processing input through EchoScan detectors.
    
    Args:
        request: ScanRequest containing input data and optional mode
    
    Returns:
        ScanResponse with scan results
    """
    try:
        # Process the input through EchoVerifier
        result = echoverifier.run(request.input, mode=request.mode)
        
        return ScanResponse(
            status="success",
            result=result
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scan processing error: {str(e)}"
        )


if __name__ == "__main__":
    # Get port from environment variable, default to 8080
    port = int(os.environ.get("PORT", 8080))
    
    # Run uvicorn server
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )