#!/usr/bin/env python3
"""
EchoScan FastAPI Application
Provides REST API interface for EchoScan authenticity detection.
"""

import os
import sys
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main as pipeline_module
import echoverifier
import sbsh_module

# FastAPI app instance
app = FastAPI(
    title="EchoScan API",
    description="Math-Anchored Symbolic Detection Engine for authenticity validation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Request models
class ScanRequest(BaseModel):
    input: str
    input_type: Optional[str] = "text"
    mode: Optional[str] = "verify"

class SBSHRequest(BaseModel):
    input: str
    glyph_digest: Optional[bool] = False

# Response models
class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

class ScanResponse(BaseModel):
    echo_score: float
    decision_label: str
    advisory_flags: list
    full_results: dict
    status: str

# Health check endpoint for DigitalOcean and other platforms
@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for container orchestration platforms."""
    return HealthResponse(
        status="healthy",
        message="EchoScan API is running",
        version="1.0.0"
    )

# Main scan endpoint
@app.post("/api/scan", response_model=ScanResponse)
async def scan_content(request: ScanRequest):
    """
    Perform authenticity scan on input content.
    
    This endpoint runs the full EchoScan pipeline on the provided input
    and returns authenticity assessment results.
    """
    try:
        # Special handling for quarantine trigger (for testing/demos)
        if request.input == "QUARANTINE_TRIGGER":
            return ScanResponse(
                echo_score=0.0,
                decision_label="Quarantine",
                advisory_flags=["QUARANTINE: Test trigger activated"],
                full_results={"quarantine_test": True},
                status="quarantine"
            )
        
        # Run the pipeline
        result = pipeline_module.run_pipeline(request.input, request.input_type)
        
        return ScanResponse(
            echo_score=result.get("EchoScore", 0),
            decision_label=result.get("Decision Label", "Unknown"),
            advisory_flags=result.get("Advisory Flags", []),
            full_results=result.get("FullResults", {}),
            status=result.get("Status", "completed")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan error: {str(e)}")

# EchoVerifier endpoint
@app.post("/api/echoverifier")
async def echoverifier_scan(request: ScanRequest):
    """Run EchoVerifier analysis on input content."""
    try:
        result = echoverifier.run(request.input, mode=request.mode)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"EchoVerifier error: {str(e)}")

# SBSH endpoint
@app.post("/api/sbsh")
async def sbsh_hash_endpoint(request: SBSHRequest):
    """Generate SBSH symbolic hash for input content."""
    try:
        if not hasattr(sbsh_module, 'sbsh_hash'):
            raise HTTPException(status_code=501, detail="SBSH module not available")
        
        result = sbsh_module.sbsh_hash(request.input)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SBSH error: {str(e)}")

# Status endpoint
@app.get("/api/status")
async def get_status():
    """Get API status and available modules."""
    modules_status = {
        "echoverifier": True,
        "sbsh": hasattr(sbsh_module, 'sbsh_hash'),
        "pipeline": True
    }
    
    return {
        "status": "running",
        "modules": modules_status,
        "endpoints": [
            "/health",
            "/api/scan",
            "/api/echoverifier", 
            "/api/sbsh",
            "/api/status"
        ]
    }

def start_server():
    """Main entry point for the FastAPI application."""
    # Get port from environment variable, defaulting to 8080
    port = int(os.getenv("PORT", 8080))
    
    # Run the FastAPI application
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )

if __name__ == "__main__":
    start_server()