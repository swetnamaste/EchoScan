"""
EchoScan API - Enhanced REST API with full metrics and monitoring
Supports frontend integration with comprehensive data export
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import os
from datetime import datetime, timedelta

# Import EchoScan components
import echoverifier
from quarantine_manager import quarantine_manager
from performance_monitor import performance_monitor
from continuous_logger import continuous_logger
from vault.vault import vault

app = FastAPI(
    title="EchoScan API",
    description="Math-Anchored Symbolic Detection Engine with Advanced Monitoring",
    version="1.0.0"
)

# Request/Response Models
class VerifyRequest(BaseModel):
    input_data: str
    mode: str = "verify"
    enable_downstream: bool = True

class VerifyResponse(BaseModel):
    verdict: str
    delta_s: float
    echo_sense: float
    glyph_id: str
    ancestry_depth: int
    vault_permission: bool
    confidence_band: Dict[str, Any]
    provenance: Dict[str, Any]
    advisory_flags: List[str]
    quarantine: Dict[str, Any]
    vault_status: Dict[str, Any]
    processing_time: float

class StatusResponse(BaseModel):
    status: str
    uptime: float
    performance: Dict[str, Any]
    quarantine_stats: Dict[str, Any]
    vault_stats: Dict[str, Any]
    logger_stats: Dict[str, Any]

@app.get("/", response_model=Dict[str, str])
async def root():
    """API root endpoint."""
    return {
        "message": "EchoScan API v1.0.0",
        "status": "operational",
        "endpoints": {
            "verify": "/verify",
            "status": "/status", 
            "metrics": "/metrics",
            "quarantine": "/quarantine",
            "logs": "/logs",
            "export": "/export"
        }
    }

@app.post("/verify", response_model=Dict[str, Any])
async def verify_input(request: VerifyRequest, background_tasks: BackgroundTasks):
    """
    Verify input data using EchoScan pipeline.
    Returns comprehensive verification results including all metrics.
    """
    try:
        start_time = datetime.now()
        
        # Run verification
        result = echoverifier.run(
            input_data=request.input_data,
            mode=request.mode,
            enable_downstream=request.enable_downstream
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Add processing time to result
        result["processing_time"] = processing_time
        result["timestamp"] = end_time.isoformat()
        
        # Log performance metrics in background
        background_tasks.add_task(
            performance_monitor.record_measurement,
            "api_verify",
            processing_time,
            input_length=len(request.input_data),
            mode=request.mode
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@app.get("/status", response_model=Dict[str, Any])
async def get_status():
    """Get comprehensive system status and statistics."""
    try:
        uptime = datetime.now() - datetime(2024, 1, 1)  # Placeholder start time
        
        return {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime.total_seconds(),
            "performance": performance_monitor.get_statistics(),
            "quarantine_stats": quarantine_manager.get_quarantine_stats(),
            "vault_stats": vault.get_vault_stats(),
            "logger_stats": continuous_logger.get_statistics()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.get("/metrics")
async def get_metrics(
    operation: Optional[str] = Query(None, description="Filter by operation type"),
    hours: int = Query(24, description="Time window in hours")
):
    """Get detailed performance metrics."""
    try:
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "time_window_hours": hours,
            "performance": performance_monitor.get_statistics(),
            "anomaly_summary": continuous_logger.get_anomaly_summary(hours),
            "recent_anomalies": continuous_logger.get_recent_anomalies(limit=20)
        }
        
        if operation:
            # Filter metrics by operation
            perf_stats = metrics["performance"].get("operations", {})
            if operation in perf_stats:
                metrics["operation_specific"] = perf_stats[operation]
            else:
                metrics["operation_specific"] = None
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

@app.get("/quarantine")
async def get_quarantine_info(
    category: Optional[str] = Query(None, description="Filter by quarantine category"),
    limit: int = Query(50, description="Maximum number of entries to return")
):
    """Get quarantine information and statistics."""
    try:
        stats = quarantine_manager.get_quarantine_stats()
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "statistics": stats,
            "categories": list(stats.get("by_category", {}).keys())
        }
        
        if category:
            result["category_filter"] = category
            # Could add category-specific data here
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quarantine info retrieval failed: {str(e)}")

@app.get("/logs")
async def get_logs(
    log_type: str = Query("edge_cases", description="Type of logs (edge_cases, field_test, performance)"),
    hours: int = Query(24, description="Time window in hours"),
    limit: int = Query(100, description="Maximum number of entries")
):
    """Get log entries for analysis."""
    try:
        if log_type == "edge_cases":
            return {
                "log_type": log_type,
                "time_window_hours": hours,
                "recent_anomalies": continuous_logger.get_recent_anomalies(limit),
                "anomaly_summary": continuous_logger.get_anomaly_summary(hours)
            }
        else:
            return {
                "log_type": log_type,
                "message": f"Log type '{log_type}' data would be returned here",
                "statistics": continuous_logger.get_statistics()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Log retrieval failed: {str(e)}")

@app.post("/export")
async def export_data(
    background_tasks: BackgroundTasks,
    data_type: str = Query("all", description="Type of data to export (logs, metrics, quarantine, all)"),
    format: str = Query("json", description="Export format (json, csv)"),
    hours: int = Query(24, description="Time window in hours")
):
    """Export data for analysis."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"echoscan_export_{data_type}_{timestamp}.{format}"
        filepath = f"exports/{filename}"
        
        # Ensure exports directory exists
        os.makedirs("exports", exist_ok=True)
        
        export_data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "data_type": data_type,
                "format": format,
                "time_window_hours": hours
            }
        }
        
        if data_type in ["logs", "all"]:
            export_data["logs"] = {
                "recent_anomalies": continuous_logger.get_recent_anomalies(50),
                "anomaly_summary": continuous_logger.get_anomaly_summary(hours),
                "logger_stats": continuous_logger.get_statistics()
            }
        
        if data_type in ["metrics", "all"]:
            export_data["metrics"] = {
                "performance": performance_monitor.get_statistics()
            }
        
        if data_type in ["quarantine", "all"]:
            export_data["quarantine"] = quarantine_manager.get_quarantine_stats()
        
        if data_type in ["vault", "all"]:
            export_data["vault"] = vault.get_vault_stats()
        
        # Save export file
        with open(filepath, 'w', encoding='utf-8') as f:
            if format == "json":
                json.dump(export_data, f, indent=2)
            else:  # CSV format would require different processing
                json.dump(export_data, f, indent=2)  # Fallback to JSON
        
        return {
            "export_status": "completed",
            "filename": filename,
            "filepath": filepath,
            "download_url": f"/download/{filename}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/download/{filename}")
async def download_export(filename: str):
    """Download exported data file."""
    try:
        filepath = f"exports/{filename}"
        if os.path.exists(filepath):
            return FileResponse(
                filepath, 
                media_type='application/json',
                filename=filename
            )
        else:
            raise HTTPException(status_code=404, detail="Export file not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": "The requested endpoint does not exist",
            "available_endpoints": ["/", "/verify", "/status", "/metrics", "/quarantine", "/logs", "/export"]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)