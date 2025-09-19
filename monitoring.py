"""
EchoScan Operational Hardening and Monitoring Module
Handles edge case logging, anomaly detection, and performance monitoring.
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps


class EdgeCaseMonitor:
    """Monitor and log edge cases and anomalies."""
    
    def __init__(self, log_path="edge_cases.log", quarantine_dir="quarantine"):
        self.log_path = log_path
        self.quarantine_dir = quarantine_dir
        self.setup_directories()
        self.setup_logging()
    
    def setup_directories(self):
        """Create necessary directories for monitoring."""
        if not os.path.exists(self.quarantine_dir):
            os.makedirs(self.quarantine_dir)
    
    def setup_logging(self):
        """Setup edge case logging."""
        logging.basicConfig(
            filename=self.log_path,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filemode='a'
        )
        self.logger = logging.getLogger('edge_case_monitor')
    
    def log_user_feedback(self, input_data: str, anomaly_description: str, user_context: Optional[Dict] = None):
        """Log user-reported anomalies to edge_cases.log."""
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "user_feedback",
            "input_sample": input_data[:100] + "..." if len(input_data) > 100 else input_data,
            "anomaly_description": anomaly_description,
            "user_context": user_context or {},
            "input_hash": hash(input_data)
        }
        
        self.logger.info(f"USER_FEEDBACK: {json.dumps(feedback_entry)}")
        print(f"✅ Anomaly logged to {self.log_path}")
        return feedback_entry
    
    def check_drift_anomaly(self, input_data: str, delta_s: float, result: Dict[str, Any]) -> bool:
        """Check if input should be quarantined due to ΔS drift > 0.02."""
        if delta_s > 0.02:
            self.quarantine_input(input_data, "delta_s_drift", {
                "delta_s": delta_s,
                "threshold": 0.02,
                "result_summary": {
                    "verdict": result.get("verdict"),
                    "glyph_id": result.get("glyph_id"),
                    "echo_sense": result.get("echo_sense")
                }
            })
            return True
        return False
    
    def check_glyph_anomaly(self, input_data: str, glyph_id: str, result: Dict[str, Any]) -> bool:
        """Check if input should be quarantined due to unclassified glyph."""
        # Consider glyphs starting with "UNK" or containing "???" as unclassified
        if glyph_id.startswith("UNK") or "???" in glyph_id:
            self.quarantine_input(input_data, "unclassified_glyph", {
                "glyph_id": glyph_id,
                "result_summary": {
                    "verdict": result.get("verdict"),
                    "delta_s": result.get("delta_s"),
                    "echo_sense": result.get("echo_sense")
                }
            })
            return True
        return False
    
    def quarantine_input(self, input_data: str, reason: str, metadata: Dict[str, Any]):
        """Store problematic input in quarantine folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{reason}_{timestamp}_{hash(input_data) % 10000:04X}.json"
        filepath = os.path.join(self.quarantine_dir, filename)
        
        quarantine_entry = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "input_data": input_data,
            "metadata": metadata,
            "input_hash": hash(input_data)
        }
        
        with open(filepath, 'w') as f:
            json.dump(quarantine_entry, f, indent=2)
        
        # Also log to edge_cases.log
        self.logger.warning(f"QUARANTINE_{reason.upper()}: {json.dumps({
            'file': filename,
            'reason': reason,
            'metadata': metadata
        })}")
        
        print(f"⚠️  Input quarantined: {filepath}")


class PerformanceMonitor:
    """Monitor request performance and log latency."""
    
    def __init__(self, log_path="perf.log"):
        self.log_path = log_path
        self.setup_logging()
    
    def setup_logging(self):
        """Setup performance logging."""
        logging.basicConfig(
            filename=self.log_path,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filemode='a'
        )
        self.perf_logger = logging.getLogger('performance_monitor')
    
    def monitor_request(self, operation_name: str = "unknown"):
        """Decorator to monitor request performance."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                
                latency = end_time - start_time
                self.log_performance(operation_name, latency, args, kwargs)
                
                return result
            return wrapper
        return decorator
    
    def log_performance(self, operation: str, latency: float, args: tuple, kwargs: dict):
        """Log performance metrics."""
        perf_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "latency_ms": round(latency * 1000, 2),
            "input_size": len(str(args[0])) if args else 0
        }
        
        # Determine thresholds
        is_batch = kwargs.get("batch", False) or "batch" in operation.lower()
        threshold = 5000 if is_batch else 500  # 5s for batch, 500ms for single
        
        if latency * 1000 > threshold:
            perf_entry["advisory_flag"] = "perf_spike"
            perf_entry["threshold_ms"] = threshold
            self.perf_logger.warning(f"PERF_SPIKE: {json.dumps(perf_entry)}")
            print(f"🚨 Performance spike detected: {latency*1000:.2f}ms > {threshold}ms")
        else:
            self.perf_logger.info(f"PERF_LOG: {json.dumps(perf_entry)}")


class VaultFailsafe:
    """Handle vault logging failures with retry and safe fallback."""
    
    def __init__(self, max_retries=3, fallback_dir="vault_fallback"):
        self.max_retries = max_retries
        self.fallback_dir = fallback_dir
        self.setup_directories()
    
    def setup_directories(self):
        """Create fallback directory."""
        if not os.path.exists(self.fallback_dir):
            os.makedirs(self.fallback_dir)
    
    def safe_vault_log(self, vault, data: Dict[str, Any]) -> bool:
        """Safely log to vault with retry and fallback."""
        for attempt in range(self.max_retries):
            try:
                vault.log(data)
                return True
            except Exception as e:
                print(f"⚠️  Vault log attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    # Final fallback: save to local file
                    return self.fallback_log(data, str(e))
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
        
        return False
    
    def fallback_log(self, data: Dict[str, Any], error_msg: str) -> bool:
        """Save data to fallback location."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vault_fallback_{timestamp}_{hash(str(data)) % 10000:04X}.json"
            filepath = os.path.join(self.fallback_dir, filename)
            
            fallback_entry = {
                "timestamp": datetime.now().isoformat(),
                "error": error_msg,
                "data": data,
                "fallback_reason": "vault_logging_failure"
            }
            
            with open(filepath, 'w') as f:
                json.dump(fallback_entry, f, indent=2)
            
            print(f"💾 Data saved to fallback: {filepath}")
            return True
            
        except Exception as fallback_error:
            print(f"❌ Fallback logging also failed: {fallback_error}")
            return False


# Global monitoring instances
edge_monitor = EdgeCaseMonitor()
perf_monitor = PerformanceMonitor()
vault_failsafe = VaultFailsafe()


def log_user_anomaly(input_data: str, description: str) -> Dict[str, Any]:
    """Convenience function for logging user-reported anomalies."""
    return edge_monitor.log_user_feedback(input_data, description)