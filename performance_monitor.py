"""
Performance Monitor - Latency and performance spike detection for EchoScan
Monitors pipeline latency and raises alerts when thresholds are exceeded
"""

import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from collections import deque
import threading
import os

class PerformanceMonitor:
    """Monitors performance and latency of EchoScan operations."""
    
    def __init__(self, 
                 latency_threshold: float = 5.0,  # seconds
                 spike_threshold_multiplier: float = 3.0,  # 3x average latency
                 history_size: int = 100,  # number of recent measurements to keep
                 alert_cooldown: int = 300):  # 5 minutes cooldown between alerts
        """Initialize performance monitor.
        
        Args:
            latency_threshold: Absolute latency threshold in seconds
            spike_threshold_multiplier: Multiplier for dynamic spike detection  
            history_size: Number of recent measurements to keep
            alert_cooldown: Cooldown period between alerts in seconds
        """
        self.latency_threshold = latency_threshold
        self.spike_threshold_multiplier = spike_threshold_multiplier
        self.history_size = history_size
        self.alert_cooldown = alert_cooldown
        
        # Thread-safe collections for measurements
        self.measurements = deque(maxlen=history_size)
        self.measurements_lock = threading.Lock()
        
        # Alert state management
        self.last_alert_time = {}
        self.alert_callbacks = []
        
        # Performance statistics
        self.total_requests = 0
        self.total_time = 0.0
        self.start_time = time.time()
        
    def add_alert_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback function for alerts.
        
        Args:
            callback: Function to call when alert is triggered
        """
        self.alert_callbacks.append(callback)
    
    def record_measurement(self, operation: str, latency: float, **metadata):
        """Record a performance measurement.
        
        Args:
            operation: Name of the operation (e.g., 'verify', 'unlock')
            latency: Time taken in seconds
            **metadata: Additional metadata about the operation
        """
        measurement = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "latency": latency,
            "metadata": metadata
        }
        
        with self.measurements_lock:
            self.measurements.append(measurement)
            self.total_requests += 1
            self.total_time += latency
        
        # Check for alerts
        self._check_alerts(measurement)
    
    def _check_alerts(self, measurement: Dict[str, Any]):
        """Check if measurement triggers any alerts."""
        operation = measurement["operation"]
        latency = measurement["latency"]
        current_time = time.time()
        
        # Check absolute latency threshold
        if latency > self.latency_threshold:
            alert_key = f"absolute_latency_{operation}"
            if self._should_send_alert(alert_key, current_time):
                self._send_alert({
                    "type": "absolute_latency",
                    "operation": operation,
                    "latency": latency,
                    "threshold": self.latency_threshold,
                    "message": f"High latency detected: {operation} took {latency:.2f}s (threshold: {self.latency_threshold}s)",
                    "severity": "warning" if latency < self.latency_threshold * 2 else "critical"
                })
        
        # Check spike threshold (relative to recent average)
        with self.measurements_lock:
            if len(self.measurements) >= 5:  # Need some history for comparison
                recent_latencies = [m["latency"] for m in list(self.measurements)[-20:] 
                                  if m["operation"] == operation]
                
                if len(recent_latencies) >= 3:
                    avg_latency = statistics.mean(recent_latencies[:-1])  # Exclude current measurement
                    spike_threshold = avg_latency * self.spike_threshold_multiplier
                    
                    if latency > spike_threshold and latency > 1.0:  # Only alert for spikes > 1s
                        alert_key = f"spike_{operation}"
                        if self._should_send_alert(alert_key, current_time):
                            self._send_alert({
                                "type": "performance_spike",
                                "operation": operation,
                                "latency": latency,
                                "average_latency": avg_latency,
                                "spike_threshold": spike_threshold,
                                "spike_ratio": latency / avg_latency,
                                "message": f"Performance spike: {operation} took {latency:.2f}s ({latency/avg_latency:.1f}x average)",
                                "severity": "warning"
                            })
    
    def _should_send_alert(self, alert_key: str, current_time: float) -> bool:
        """Check if enough time has passed since last alert of this type."""
        last_alert = self.last_alert_time.get(alert_key, 0)
        if current_time - last_alert > self.alert_cooldown:
            self.last_alert_time[alert_key] = current_time
            return True
        return False
    
    def _send_alert(self, alert_data: Dict[str, Any]):
        """Send alert to all registered callbacks."""
        alert_data["timestamp"] = datetime.now().isoformat()
        
        print(f"[PERFORMANCE ALERT] {alert_data['message']}")
        
        # Log alert to file
        try:
            os.makedirs("logs", exist_ok=True)
            with open("logs/performance_alerts.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(alert_data) + "\n")
        except Exception as e:
            print(f"[PERFORMANCE MONITOR] Failed to log alert: {e}")
        
        # Call registered callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                print(f"[PERFORMANCE MONITOR] Alert callback failed: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics.
        
        Returns:
            Dictionary with performance statistics
        """
        with self.measurements_lock:
            if not self.measurements:
                return {
                    "total_requests": 0,
                    "average_latency": 0.0,
                    "uptime_seconds": time.time() - self.start_time,
                    "operations": {}
                }
            
            # Overall statistics
            latencies = [m["latency"] for m in self.measurements]
            
            stats = {
                "total_requests": self.total_requests,
                "recent_requests": len(self.measurements),
                "average_latency": statistics.mean(latencies),
                "median_latency": statistics.median(latencies),
                "max_latency": max(latencies),
                "min_latency": min(latencies),
                "uptime_seconds": time.time() - self.start_time,
                "requests_per_second": self.total_requests / (time.time() - self.start_time),
                "operations": {}
            }
            
            # Per-operation statistics
            operations = set(m["operation"] for m in self.measurements)
            for operation in operations:
                op_measurements = [m for m in self.measurements if m["operation"] == operation]
                op_latencies = [m["latency"] for m in op_measurements]
                
                stats["operations"][operation] = {
                    "count": len(op_measurements),
                    "average_latency": statistics.mean(op_latencies),
                    "median_latency": statistics.median(op_latencies),
                    "max_latency": max(op_latencies),
                    "min_latency": min(op_latencies)
                }
        
        return stats
    
    def measure_operation(self, operation: str, **metadata):
        """Context manager for measuring operation performance.
        
        Args:
            operation: Name of the operation
            **metadata: Additional metadata to record
        
        Usage:
            with performance_monitor.measure_operation("verify"):
                result = verifier.verify(input_data)
        """
        return PerformanceMeasurement(self, operation, metadata)


class PerformanceMeasurement:
    """Context manager for measuring operation performance."""
    
    def __init__(self, monitor: PerformanceMonitor, operation: str, metadata: Dict[str, Any]):
        self.monitor = monitor
        self.operation = operation
        self.metadata = metadata
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            latency = time.time() - self.start_time
            
            # Add exception info to metadata if an error occurred
            if exc_type is not None:
                self.metadata["error"] = str(exc_val)
                self.metadata["error_type"] = exc_type.__name__
            
            self.monitor.record_measurement(self.operation, latency, **self.metadata)


# Webhook/Slack alert function (placeholder - can be extended)
def webhook_alert_callback(alert_data: Dict[str, Any]):
    """Example webhook alert callback.
    
    This could be extended to send alerts to Slack, Discord, email, etc.
    """
    # This is a placeholder - in a real implementation, you would:
    # 1. Format the alert for your webhook service
    # 2. Send HTTP request to webhook URL
    # 3. Handle failures gracefully
    
    print(f"[WEBHOOK ALERT] {alert_data['type']}: {alert_data['message']}")
    

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Register default webhook callback
performance_monitor.add_alert_callback(webhook_alert_callback)