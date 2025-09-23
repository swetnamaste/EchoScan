"""
FastAPI application for EchoScan - Math-Anchored Symbolic Detection Engine
"""

import os
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import json

# Import EchoScan modules
import echoverifier
import sbsh_module

app = FastAPI(
    title="EchoScan API",
    description="Math-Anchored Symbolic Detection Engine for authenticity and anomaly detection",
    version="1.0.0"
)

class ScanRequest(BaseModel):
    """Request model for scan endpoint"""
    input: str
    mode: Optional[str] = "verify"

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    service: str

class ScanResponse(BaseModel):
    """Response model for scan endpoint"""
    verdict: str
    delta_s: float
    glyph_id: str
    ancestry_depth: int
    echo_sense: float
    vault_permission: bool

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for DigitalOcean load balancer"""
    return HealthResponse(status="healthy", service="EchoScan")

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - also serves as health check"""
    return HealthResponse(status="healthy", service="EchoScan API")

@app.post("/api/scan", response_model=ScanResponse)
async def scan_input(request: ScanRequest):
    """
    Main scanning endpoint that processes input through EchoVerifier
    """
    try:
        # Run EchoVerifier on the input
        result = echoverifier.run(request.input, mode=request.mode)
        
        return ScanResponse(
            verdict=result.get("verdict", "Unknown"),
            delta_s=result.get("delta_s", 0.0),
            glyph_id=result.get("glyph_id", ""),
            ancestry_depth=result.get("ancestry_depth", 0),
            echo_sense=result.get("echo_sense", 0.0),
            vault_permission=result.get("vault_permission", False)
        )
    except Exception as e:
        # Return error in expected format
        return ScanResponse(
            verdict=f"Error: {str(e)}",
            delta_s=0.0,
            glyph_id="",
            ancestry_depth=0,
            echo_sense=0.0,
            vault_permission=False
        )

@app.post("/api/sbsh")
async def symbolic_hash(request: ScanRequest):
    """
    SBSH (Symbolic Hash) endpoint
    """
    try:
        result = sbsh_module.sbsh_hash(request.input)
        return result
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Get port from environment variable or default to 8080
    port = int(os.environ.get("PORT", 8080))
    
    # Start Uvicorn server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        access_log=True,
        log_level="info"
    )