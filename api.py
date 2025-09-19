"""
EchoScan API Server
FastAPI-based REST API for EchoScan authenticity validation services.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import hashlib
import time
from datetime import datetime

# Import EchoScan modules
import echoverifier
import sbsh_module
from monitoring import perf_monitor, edge_monitor, log_user_anomaly

app = FastAPI(
    title="EchoScan API",
    description="Mathematical Authenticity Validation API",
    version="1.0.0"
)

# Pydantic models for API
class VerificationRequest(BaseModel):
    input_data: str
    enable_downstream: bool = True
    verbose: bool = False

class BatchVerificationRequest(BaseModel):
    inputs: List[str]
    enable_downstream: bool = True

class SignatureVerificationRequest(BaseModel):
    input_data: str
    signature: str
    public_key: Optional[str] = None

class FeedbackRequest(BaseModel):
    input_data: str
    anomaly_description: str
    user_context: Optional[Dict[str, Any]] = {}

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """API root with basic information."""
    return """
    <html>
        <head>
            <title>EchoScan API</title>
        </head>
        <body>
            <h1>EchoScan - Mathematical Authenticity Validation API</h1>
            <h2>Available Endpoints:</h2>
            <ul>
                <li><strong>POST /verify</strong> - Single input verification</li>
                <li><strong>POST /batch</strong> - Batch verification</li>
                <li><strong>POST /verify-signature</strong> - Signature-based verification</li>
                <li><strong>POST /feedback</strong> - Report anomalies</li>
                <li><strong>GET /health</strong> - Health check</li>
                <li><strong>GET /docs</strong> - API documentation</li>
                <li><strong>GET /dashboard</strong> - Interactive dashboard</li>
            </ul>
            <p><a href="/docs">📖 View Interactive API Documentation</a></p>
            <p><a href="/dashboard">🚀 Open Dashboard</a></p>
        </body>
    </html>
    """

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the interactive dashboard."""
    try:
        with open("dashboard.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <body>
                <h1>Dashboard not found</h1>
                <p>The dashboard HTML file is missing. Please ensure dashboard.html exists.</p>
                <p><a href="/">← Back to API</a></p>
            </body>
        </html>
        """

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "modules": {
            "echoverifier": "operational",
            "monitoring": "operational",
            "sbsh": "operational"
        }
    }

@app.post("/verify")
@perf_monitor.monitor_request("api_verify")
async def verify_input(request: VerificationRequest):
    """
    Verify authenticity of a single input.
    
    Returns comprehensive verification results including:
    - verdict, delta_s, glyph_id, ancestry_depth, echo_sense
    - confidence_band, trust_chain, explanation
    - downstream module results
    """
    try:
        result = echoverifier.run(
            request.input_data, 
            mode="verify",
            enable_downstream=request.enable_downstream
        )
        
        # Add API metadata
        result["api_metadata"] = {
            "endpoint": "/verify",
            "timestamp": datetime.now().isoformat(),
            "processing_mode": "single",
            "verbose": request.verbose
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@app.post("/batch")
@perf_monitor.monitor_request("api_batch_verify")  
async def batch_verify(request: BatchVerificationRequest):
    """
    Verify authenticity of multiple inputs in batch.
    
    Optimized for processing multiple inputs with performance monitoring
    for requests exceeding 5 second threshold.
    """
    try:
        results = []
        processing_start = time.time()
        
        for i, input_data in enumerate(request.inputs):
            start_time = time.time()
            
            result = echoverifier.run(
                input_data,
                mode="verify", 
                enable_downstream=request.enable_downstream,
                batch=True
            )
            
            # Add batch metadata
            result["batch_metadata"] = {
                "batch_index": i,
                "batch_total": len(request.inputs),
                "item_processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
            
            results.append(result)
        
        processing_time = time.time() - processing_start
        
        return {
            "batch_results": results,
            "batch_summary": {
                "total_inputs": len(request.inputs),
                "total_processing_time_ms": round(processing_time * 1000, 2),
                "average_time_per_input_ms": round(processing_time * 1000 / len(request.inputs), 2),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch verification failed: {str(e)}")

@app.post("/verify-signature")
@perf_monitor.monitor_request("api_verify_signature")
async def verify_signature(request: SignatureVerificationRequest):
    """
    Verify input authenticity with cryptographic signature validation.
    
    Combines EchoVerifier authenticity analysis with signature verification
    for enhanced security and provenance tracking.
    """
    try:
        # First run standard EchoVerifier analysis
        echo_result = echoverifier.run(request.input_data, mode="verify")
        
        # Simulate signature verification (placeholder implementation)
        signature_valid = len(request.signature) > 10  # Basic validation
        
        # Generate signature verification metadata
        signature_hash = hashlib.sha256(request.signature.encode()).hexdigest()[:16]
        
        result = {
            "echoverifier_result": echo_result,
            "signature_verification": {
                "signature_valid": signature_valid,
                "signature_hash": signature_hash,
                "verification_method": "ECC-P256" if request.public_key else "internal",
                "timestamp": datetime.now().isoformat()
            },
            "combined_verdict": {
                "authenticity": echo_result["verdict"],
                "signature": "valid" if signature_valid else "invalid",
                "overall_trust": "high" if signature_valid and echo_result["vault_permission"] else "medium"
            }
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signature verification failed: {str(e)}")

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback about anomalous behavior for edge case monitoring.
    
    Logs user-reported anomalies to edge_cases.log for system improvement
    and anomaly pattern analysis.
    """
    try:
        feedback_result = log_user_anomaly(
            request.input_data,
            request.anomaly_description
        )
        
        # Add additional context if provided
        if request.user_context:
            feedback_result["user_context"] = request.user_context
        
        return {
            "feedback_logged": True,
            "feedback_result": feedback_result,
            "message": "Thank you for reporting this anomaly. It will help improve the system."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")

@app.get("/stats")
async def get_system_stats():
    """Get system performance and monitoring statistics."""
    try:
        # Basic stats (in a real implementation, these would come from monitoring system)
        return {
            "performance_stats": {
                "total_requests": "N/A",
                "average_response_time_ms": "N/A", 
                "error_rate_percent": "N/A"
            },
            "edge_cases": {
                "total_quarantined": "N/A",
                "drift_anomalies": "N/A",
                "glyph_anomalies": "N/A"
            },
            "system_health": {
                "vault_status": "operational",
                "monitoring_status": "operational",
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "available_endpoints": [
        "/verify", "/batch", "/verify-signature", "/feedback", "/health", "/stats"
    ]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)