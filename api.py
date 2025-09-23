"""
FastAPI entrypoint for EchoScan - Math-Anchored Symbolic Detection Engine
"""
import os
from fastapi import FastAPI
from pydantic import BaseModel
import echoverifier

app = FastAPI(
    title="EchoScan API",
    description="Math-Anchored Symbolic Detection Engine for authenticity and anomaly detection",
    version="1.0.0"
)

class ScanRequest(BaseModel):
    input: str
    mode: str = "verify"

class ScanResponse(BaseModel):
    input: str
    verdict: str
    delta_s: float
    fold_vector: list
    glyph_id: str
    ancestry_depth: int
    echo_sense: float
    vault_permission: bool

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "EchoScan API - Math-Anchored Symbolic Detection Engine",
        "version": "1.0.0",
        "endpoints": {
            "/api/scan": "POST - Scan input for authenticity",
            "/health": "GET - Health check"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "echoscan-api"}

@app.post("/api/scan")
async def scan_input(request: ScanRequest):
    """
    Scan input text for authenticity using EchoVerifier
    """
    try:
        result = echoverifier.run(request.input, mode=request.mode)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "input": request.input,
            "verdict": "Error"
        }

if __name__ == "__main__":
    import uvicorn
    
    # Read port from environment variable, default to 8080 for DigitalOcean App Platform
    port = int(os.environ.get("PORT", 8080))
    
    print(f"🚀 Starting EchoScan API on port {port}")
    print(f"📍 Environment PORT: {os.environ.get('PORT', 'not set (using default 8080)')}")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )