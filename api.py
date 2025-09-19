#!/usr/bin/env python3
"""
EchoScan API Server
Provides REST API endpoints for EchoScan functionality including batch processing
"""

import asyncio
import concurrent.futures
import json
import time
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
import logging
import hashlib
from datetime import datetime
import os

# Import EchoScan modules
import echoverifier
import detector_registry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="EchoScan API",
    description="Math-Anchored Symbolic Detection Engine API",
    version="1.0.0"
)

# Serve dashboard as static file
if os.path.exists("dashboard.html"):
    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        with open("dashboard.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

# Request/Response models
class VerifyRequest(BaseModel):
    text: str
    mode: str = "verify"
    enable_downstream: bool = True

class BatchVerifyRequest(BaseModel):
    texts: List[str]
    mode: str = "verify"
    enable_downstream: bool = True
    max_workers: int = 4

class SignatureVerifyRequest(BaseModel):
    data: str
    signature: str
    timestamp: str = None

class VerifyResponse(BaseModel):
    input: str
    verdict: str
    explanation: str
    delta_s: float
    echo_sense: float
    glyph_id: str
    ancestry_depth: int
    vault_permission: bool
    processing_time_ms: float
    downstream: Dict[str, Any] = None

class BatchVerifyResponse(BaseModel):
    results: List[VerifyResponse]
    total_count: int
    processing_time_ms: float
    batch_id: str

# In-memory batch processing status
batch_status = {}

@app.post("/api/verify", response_model=VerifyResponse)
async def verify_text(request: VerifyRequest):
    """Verify a single text input."""
    start_time = time.time()
    
    try:
        result = echoverifier.run(
            request.text, 
            mode=request.mode,
            enable_downstream=request.enable_downstream
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return VerifyResponse(
            input=result["input"],
            verdict=result["verdict"],
            explanation=result.get("explanation", "No explanation available"),
            delta_s=result["delta_s"],
            echo_sense=result["echo_sense"],
            glyph_id=result["glyph_id"],
            ancestry_depth=result["ancestry_depth"],
            vault_permission=result["vault_permission"],
            processing_time_ms=processing_time,
            downstream=result.get("downstream")
        )
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@app.post("/api/batch", response_model=BatchVerifyResponse)
async def batch_verify(request: BatchVerifyRequest, background_tasks: BackgroundTasks):
    """Process multiple texts in batch with concurrent processing."""
    if len(request.texts) > 100:
        raise HTTPException(status_code=400, detail="Batch size too large (max 100)")
    
    start_time = time.time()
    batch_id = hashlib.sha256(
        (str(request.texts) + str(time.time())).encode()
    ).hexdigest()[:16]
    
    # Store initial batch status
    batch_status[batch_id] = {
        "status": "processing",
        "total": len(request.texts),
        "completed": 0,
        "started_at": datetime.utcnow().isoformat()
    }
    
    try:
        # Process batch concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=request.max_workers) as executor:
            futures = []
            
            for text in request.texts:
                future = executor.submit(
                    echoverifier.run, 
                    text, 
                    request.mode,
                    enable_downstream=request.enable_downstream
                )
                futures.append(future)
            
            # Collect results as they complete
            results = []
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                try:
                    result = future.result()
                    results.append(VerifyResponse(
                        input=result["input"],
                        verdict=result["verdict"],
                        explanation=result.get("explanation", "No explanation available"),
                        delta_s=result["delta_s"],
                        echo_sense=result["echo_sense"],
                        glyph_id=result["glyph_id"],
                        ancestry_depth=result["ancestry_depth"],
                        vault_permission=result["vault_permission"],
                        processing_time_ms=0.0,  # Individual timing not tracked in batch
                        downstream=result.get("downstream")
                    ))
                    
                    # Update batch status
                    batch_status[batch_id]["completed"] += 1
                    
                except Exception as e:
                    logger.error(f"Batch item {i} failed: {e}")
                    # Continue processing other items
        
        processing_time = (time.time() - start_time) * 1000
        
        # Update final batch status
        batch_status[batch_id].update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "processing_time_ms": processing_time
        })
        
        return BatchVerifyResponse(
            results=results,
            total_count=len(results),
            processing_time_ms=processing_time,
            batch_id=batch_id
        )
        
    except Exception as e:
        batch_status[batch_id]["status"] = "failed"
        batch_status[batch_id]["error"] = str(e)
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

@app.get("/api/batch/{batch_id}/status")
async def get_batch_status(batch_id: str):
    """Get the status of a batch processing job."""
    if batch_id not in batch_status:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    return batch_status[batch_id]

@app.post("/api/verify-signature")
async def verify_signature(request: SignatureVerifyRequest):
    """Verify signature of data with SHA256 + timestamp validation."""
    try:
        # Create SHA256 hash of data + timestamp
        timestamp = request.timestamp or datetime.utcnow().isoformat()
        data_to_hash = f"{request.data}{timestamp}".encode('utf-8')
        expected_signature = hashlib.sha256(data_to_hash).hexdigest()
        
        # Verify signature
        signature_valid = expected_signature == request.signature
        
        # Check timestamp recency (within 1 hour)
        try:
            request_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_diff = (datetime.utcnow() - request_time.replace(tzinfo=None)).total_seconds()
            timestamp_valid = time_diff < 3600  # 1 hour
        except:
            timestamp_valid = False
        
        return {
            "signature_valid": signature_valid,
            "timestamp_valid": timestamp_valid,
            "timestamp": timestamp,
            "expected_signature": expected_signature,
            "provided_signature": request.signature,
            "chain_verified": signature_valid and timestamp_valid
        }
        
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Signature verification failed: {str(e)}")

@app.get("/api/detectors")
async def list_detectors():
    """List all available detectors from registry."""
    registry = detector_registry.get_registry()
    return {
        "detectors": registry.list_detectors(),
        "registry_info": registry.get_registry_info()
    }

@app.get("/api/detector/{detector_name}")
async def get_detector_info(detector_name: str):
    """Get information about a specific detector."""
    registry = detector_registry.get_registry()
    detector = registry.get_detector(detector_name)
    
    if not detector:
        raise HTTPException(status_code=404, detail=f"Detector '{detector_name}' not found")
    
    return {
        "name": detector["name"],
        "description": detector["description"],
        "config": detector["config"]
    }

@app.post("/api/detector/{detector_name}/run")
async def run_detector(detector_name: str, request: VerifyRequest):
    """Run a specific detector on input text."""
    registry = detector_registry.get_registry()
    
    try:
        result = registry.run_detector(detector_name, request.text)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Detector '{detector_name}' not found or failed to run")
        
        return result
    except Exception as e:
        logger.error(f"Detector {detector_name} failed: {e}")
        raise HTTPException(status_code=500, detail=f"Detector failed: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "detectors_loaded": len(detector_registry.get_registry().detectors)
    }

@app.get("/api/stats")
async def get_stats():
    """Get API usage statistics."""
    registry = detector_registry.get_registry()
    
    return {
        "total_batches": len(batch_status),
        "active_batches": len([b for b in batch_status.values() if b["status"] == "processing"]),
        "registry_stats": registry.get_registry_info(),
        "system_info": {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": time.time()  # Simplified uptime
        }
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 EchoScan API Server starting up...")
    
    # Initialize detector registry
    registry = detector_registry.get_registry()
    info = registry.get_registry_info()
    logger.info(f"✅ Loaded {info['detector_counts']['total']} detectors")
    
    logger.info("✅ EchoScan API Server ready!")

# Run server
if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )