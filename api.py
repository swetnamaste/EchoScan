#!/usr/bin/env python3
"""
EchoScan FastAPI Server
Provides HTTP API access to EchoScan detection engines.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import sys

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import EchoScan modules
try:
    import main
    from main import run_pipeline
except ImportError as e:
    print(f"Error importing main: {e}")
    main = None
    run_pipeline = None

try:
    import echoverifier
except ImportError:
    echoverifier = None

try:
    from sbsh_module import sbsh_hash, validate_sbsh_output
except ImportError:
    sbsh_hash = None
    validate_sbsh_output = None

try:
    import cli
except ImportError:
    cli = None

# Create FastAPI app
app = FastAPI(
    title="EchoScan API",
    description="Math-Anchored Symbolic Detection Engine - HTTP API for text, image, audio, and video authenticity validation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ScanRequest(BaseModel):
    input: str
    input_type: Optional[str] = "text"

class SBSHRequest(BaseModel):
    text: str
    glyph_digest: Optional[str] = None

class VerifyRequest(BaseModel):
    input: str
    mode: Optional[str] = "verify"

class SBSHCompareRequest(BaseModel):
    hash1: str
    hash2: str

class APIResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "EchoScan API",
        "version": "1.0.0",
        "description": "Math-Anchored Symbolic Detection Engine",
        "features": [
            "SBSH (Symbolic Hash)",
            "EchoLock trust stack", 
            "EchoVerifier firewall",
            "EchoSeal drift trace",
            "SDS-1 Symbolic DNA Sequencer",
            "RPS-1 Recursive Paradox Synthesizer"
        ],
        "endpoints": {
            "scan": "POST /api/scan - Full pipeline scan",
            "sbsh": "POST /api/sbsh - Generate symbolic hash", 
            "verify": "POST /api/verify - EchoVerifier analysis",
            "health": "GET /health - Health check"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "modules": {
            "main": main is not None,
            "echoverifier": echoverifier is not None,
            "sbsh_module": sbsh_hash is not None,
            "cli": cli is not None
        }
    }

# Main scan endpoint
@app.post("/api/scan")
async def scan(request: ScanRequest):
    """
    Run full EchoScan pipeline on input data.
    
    Args:
        request: ScanRequest with input text and optional input_type
    
    Returns:
        Complete pipeline analysis results
    """
    if not run_pipeline:
        raise HTTPException(status_code=500, detail="Pipeline functionality not available")
    
    try:
        result = run_pipeline(request.input, request.input_type)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

# SBSH symbolic hash endpoint
@app.post("/api/sbsh")
async def generate_sbsh(request: SBSHRequest):
    """
    Generate SBSH symbolic hash for input text.
    
    Args:
        request: SBSHRequest with text and optional glyph_digest
    
    Returns:
        SBSH hash result
    """
    if not sbsh_hash:
        raise HTTPException(status_code=500, detail="SBSH functionality not available")
    
    try:
        if cli and hasattr(cli, 'handle_symbolic_hash'):
            result = cli.handle_symbolic_hash(request.text, request.glyph_digest)
        else:
            result = sbsh_hash(request.text, glyph_digest=request.glyph_digest)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SBSH error: {str(e)}")

# SBSH comparison endpoint
@app.post("/api/sbsh/compare")
async def compare_sbsh(request: SBSHCompareRequest):
    """
    Compare two SBSH hashes.
    
    Args:
        request: SBSHCompareRequest with hash1 and hash2
    
    Returns:
        SBSH comparison result
    """
    if not cli or not hasattr(cli, 'handle_compare_sbsh'):
        raise HTTPException(status_code=500, detail="SBSH comparison not available")
    
    try:
        result = cli.handle_compare_sbsh(request.hash1, request.hash2)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SBSH comparison error: {str(e)}")

# EchoVerifier endpoint
@app.post("/api/verify")
async def verify(request: VerifyRequest):
    """
    Run EchoVerifier authenticity validation.
    
    Args:
        request: VerifyRequest with input text and optional mode
    
    Returns:
        EchoVerifier analysis result
    """
    if not echoverifier:
        raise HTTPException(status_code=500, detail="EchoVerifier not available")
    
    try:
        result = echoverifier.run(request.input, mode=request.mode)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"EchoVerifier error: {str(e)}")

# EchoLock unlock endpoint
@app.post("/api/unlock")
async def unlock(request: VerifyRequest):
    """
    Run EchoLock unlock procedure.
    
    Args:
        request: VerifyRequest with input text
    
    Returns:
        EchoLock unlock result
    """
    if not echoverifier:
        raise HTTPException(status_code=500, detail="EchoVerifier not available")
    
    try:
        result = echoverifier.run(request.input, mode="unlock")
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"EchoLock error: {str(e)}")

# Ancestry analysis endpoint
@app.post("/api/ancestry")
async def ancestry(request: VerifyRequest):
    """
    Perform ancestry depth analysis.
    
    Args:
        request: VerifyRequest with input text
    
    Returns:
        Ancestry analysis result
    """
    if not echoverifier:
        raise HTTPException(status_code=500, detail="EchoVerifier not available")
    
    try:
        result = echoverifier.run(request.input, mode="ancestry")
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ancestry analysis error: {str(e)}")

# Export verifier data endpoint
@app.post("/api/export")
async def export_verifier(request: VerifyRequest):
    """
    Export verifier data in structured format.
    
    Args:
        request: VerifyRequest with input text
    
    Returns:
        Exported verifier data
    """
    if not echoverifier:
        raise HTTPException(status_code=500, detail="EchoVerifier not available")
    
    try:
        result = echoverifier.run(request.input, mode="export")
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)