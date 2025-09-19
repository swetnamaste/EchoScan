"""
Continuous Logger - Field testing and anomaly tracking for EchoScan
Enables ongoing logging to edge_cases.log for anomaly tracking and rapid field patching
"""

import json
import time
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from collections import deque

class ContinuousLogger:
    """Handles continuous logging of anomalies and field test data."""
    
    def __init__(self, 
                 log_dir: str = "logs",
                 edge_cases_file: str = "edge_cases.log",
                 field_test_file: str = "field_test.log",
                 performance_file: str = "performance.log",
                 max_log_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        """Initialize continuous logger.
        
        Args:
            log_dir: Directory for log files
            edge_cases_file: Filename for edge cases log
            field_test_file: Filename for field test log
            performance_file: Filename for performance log
            max_log_size: Maximum size per log file before rotation
            backup_count: Number of backup files to keep
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.edge_cases_file = self.log_dir / edge_cases_file
        self.field_test_file = self.log_dir / field_test_file
        self.performance_file = self.log_dir / performance_file
        
        self.max_log_size = max_log_size
        self.backup_count = backup_count
        self.lock = threading.Lock()
        
        # Initialize loggers
        self._setup_loggers()
        
        # Statistics
        self.stats = {
            "edge_cases_logged": 0,
            "field_tests_logged": 0,
            "performance_logs": 0,
            "start_time": datetime.now().isoformat()
        }
        
        # Recent anomaly tracking for rapid response
        self.recent_anomalies = deque(maxlen=100)
    
    def _setup_loggers(self):
        """Set up rotating file loggers."""
        from logging.handlers import RotatingFileHandler
        
        # Edge cases logger
        self.edge_cases_logger = logging.getLogger('edge_cases')
        self.edge_cases_logger.setLevel(logging.INFO)
        edge_handler = RotatingFileHandler(
            self.edge_cases_file, 
            maxBytes=self.max_log_size, 
            backupCount=self.backup_count
        )
        edge_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.edge_cases_logger.addHandler(edge_handler)
        
        # Field test logger
        self.field_test_logger = logging.getLogger('field_test')
        self.field_test_logger.setLevel(logging.INFO)
        field_handler = RotatingFileHandler(
            self.field_test_file,
            maxBytes=self.max_log_size,
            backupCount=self.backup_count
        )
        field_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.field_test_logger.addHandler(field_handler)
        
        # Performance logger
        self.performance_logger = logging.getLogger('performance')
        self.performance_logger.setLevel(logging.INFO)
        perf_handler = RotatingFileHandler(
            self.performance_file,
            maxBytes=self.max_log_size,
            backupCount=self.backup_count
        )
        perf_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.performance_logger.addHandler(perf_handler)
    
    def log_edge_case(self, 
                      input_data: str, 
                      result: Dict[str, Any], 
                      anomaly_type: str,
                      severity: str = "medium",
                      additional_metadata: Optional[Dict[str, Any]] = None):
        """Log an edge case or anomaly for tracking.
        
        Args:
            input_data: Original input that caused the edge case
            result: EchoVerifier result
            anomaly_type: Type of anomaly (drift, glyph, symbolic, etc.)
            severity: Severity level (low, medium, high, critical)
            additional_metadata: Additional metadata to include
        """
        with self.lock:
            self.stats["edge_cases_logged"] += 1
        
        edge_case_entry = {
            "timestamp": datetime.now().isoformat(),
            "anomaly_type": anomaly_type,
            "severity": severity,
            "input_hash": hash(input_data),
            "input_length": len(input_data),
            "input_preview": input_data[:100] + "..." if len(input_data) > 100 else input_data,
            "result": {
                "verdict": result.get("verdict"),
                "delta_s": result.get("delta_s"),
                "echo_sense": result.get("echo_sense"),
                "glyph_id": result.get("glyph_id"),
                "vault_permission": result.get("vault_permission")
            },
            "metadata": additional_metadata or {}
        }
        
        # Add to recent anomalies for rapid response
        self.recent_anomalies.append(edge_case_entry)
        
        # Log to file
        try:
            self.edge_cases_logger.info(json.dumps(edge_case_entry))
            print(f"[EDGE CASE LOG] {anomaly_type} anomaly logged (severity: {severity})")
        except Exception as e:
            print(f"[EDGE CASE LOG ERROR] Failed to log edge case: {e}")
    
    def log_field_test(self, 
                       operation: str,
                       input_data: str,
                       result: Dict[str, Any],
                       performance_metrics: Dict[str, Any],
                       test_metadata: Optional[Dict[str, Any]] = None):
        """Log field test data for continuous improvement.
        
        Args:
            operation: Operation being tested
            input_data: Test input data
            result: Operation result
            performance_metrics: Performance data (latency, etc.)
            test_metadata: Additional test metadata
        """
        with self.lock:
            self.stats["field_tests_logged"] += 1
        
        field_test_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "input_hash": hash(input_data),
            "input_length": len(input_data),
            "input_type": self._classify_input_type(input_data),
            "result_summary": {
                "verdict": result.get("verdict"),
                "delta_s": result.get("delta_s"),
                "echo_sense": result.get("echo_sense"),
                "vault_permission": result.get("vault_permission"),
                "quarantined": result.get("quarantine", {}).get("quarantined", False)
            },
            "performance": performance_metrics,
            "test_metadata": test_metadata or {},
            "success": "error" not in result
        }
        
        try:
            self.field_test_logger.info(json.dumps(field_test_entry))
        except Exception as e:
            print(f"[FIELD TEST LOG ERROR] Failed to log field test: {e}")
    
    def log_performance(self, 
                        operation: str,
                        latency: float,
                        memory_usage: Optional[float] = None,
                        cpu_usage: Optional[float] = None,
                        additional_metrics: Optional[Dict[str, Any]] = None):
        """Log performance metrics for monitoring.
        
        Args:
            operation: Operation name
            latency: Operation latency in seconds
            memory_usage: Memory usage in MB (optional)
            cpu_usage: CPU usage percentage (optional)
            additional_metrics: Additional performance metrics
        """
        with self.lock:
            self.stats["performance_logs"] += 1
        
        perf_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "latency": latency,
            "memory_usage_mb": memory_usage,
            "cpu_usage_percent": cpu_usage,
            "additional_metrics": additional_metrics or {}
        }
        
        try:
            self.performance_logger.info(json.dumps(perf_entry))
        except Exception as e:
            print(f"[PERFORMANCE LOG ERROR] Failed to log performance: {e}")
    
    def _classify_input_type(self, input_data: str) -> str:
        """Classify input data type for analysis.
        
        Args:
            input_data: Input string to classify
            
        Returns:
            Classification string
        """
        if not input_data:
            return "empty"
        
        if len(input_data) < 10:
            return "short"
        elif len(input_data) > 1000:
            return "long"
        
        # Check for patterns
        if input_data.isdigit():
            return "numeric"
        elif input_data.isalpha():
            return "alphabetic"
        elif any(char in input_data for char in "{}[]()<>"):
            return "structured"
        elif any(char in input_data for char in "!@#$%^&*"):
            return "special_chars"
        else:
            return "mixed"
    
    def get_recent_anomalies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent anomalies for rapid response.
        
        Args:
            limit: Maximum number of anomalies to return
            
        Returns:
            List of recent anomaly entries
        """
        with self.lock:
            return list(self.recent_anomalies)[-limit:]
    
    def get_anomaly_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of anomalies from recent hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Summary of anomalies
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_anomalies = []
        for anomaly in self.recent_anomalies:
            anomaly_time = datetime.fromisoformat(anomaly["timestamp"])
            if anomaly_time >= cutoff_time:
                recent_anomalies.append(anomaly)
        
        # Analyze anomalies
        if not recent_anomalies:
            return {
                "total_anomalies": 0,
                "time_window_hours": hours,
                "summary": "No anomalies in the specified time window"
            }
        
        anomaly_types = {}
        severity_counts = {}
        
        for anomaly in recent_anomalies:
            anomaly_type = anomaly.get("anomaly_type", "unknown")
            severity = anomaly.get("severity", "unknown")
            
            anomaly_types[anomaly_type] = anomaly_types.get(anomaly_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_anomalies": len(recent_anomalies),
            "time_window_hours": hours,
            "anomaly_types": anomaly_types,
            "severity_distribution": severity_counts,
            "most_common_type": max(anomaly_types.items(), key=lambda x: x[1])[0] if anomaly_types else None,
            "critical_count": severity_counts.get("critical", 0),
            "high_count": severity_counts.get("high", 0)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get continuous logger statistics.
        
        Returns:
            Dictionary with logger statistics
        """
        with self.lock:
            stats = self.stats.copy()
        
        stats.update({
            "log_files": {
                "edge_cases": str(self.edge_cases_file),
                "field_test": str(self.field_test_file), 
                "performance": str(self.performance_file)
            },
            "recent_anomalies_count": len(self.recent_anomalies),
            "uptime_minutes": (datetime.now() - datetime.fromisoformat(stats["start_time"])).total_seconds() / 60
        })
        
        return stats
    
    def export_logs(self, output_file: str, log_type: str = "all", hours: int = 24) -> bool:
        """Export logs to a file for analysis.
        
        Args:
            output_file: Output file path
            log_type: Type of logs to export ("edge_cases", "field_test", "performance", "all")
            hours: Number of hours to look back
            
        Returns:
            True if export was successful
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            exported_data = {
                "export_timestamp": datetime.now().isoformat(),
                "time_window_hours": hours,
                "log_type": log_type,
                "data": {}
            }
            
            if log_type in ["edge_cases", "all"]:
                exported_data["data"]["edge_cases"] = self._export_log_file(
                    self.edge_cases_file, cutoff_time
                )
            
            if log_type in ["field_test", "all"]:
                exported_data["data"]["field_test"] = self._export_log_file(
                    self.field_test_file, cutoff_time
                )
            
            if log_type in ["performance", "all"]:
                exported_data["data"]["performance"] = self._export_log_file(
                    self.performance_file, cutoff_time
                )
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(exported_data, f, indent=2)
            
            print(f"[EXPORT] Logs exported to {output_file}")
            return True
            
        except Exception as e:
            print(f"[EXPORT ERROR] Failed to export logs: {e}")
            return False
    
    def _export_log_file(self, log_file: Path, cutoff_time: datetime) -> List[Dict[str, Any]]:
        """Export entries from a log file within the time window.
        
        Args:
            log_file: Path to log file
            cutoff_time: Cutoff time for entries
            
        Returns:
            List of log entries
        """
        entries = []
        
        if not log_file.exists():
            return entries
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if ' - {' in line:  # JSON log entry
                        try:
                            json_part = line.split(' - ', 1)[1]
                            entry = json.loads(json_part)
                            entry_time = datetime.fromisoformat(entry["timestamp"])
                            
                            if entry_time >= cutoff_time:
                                entries.append(entry)
                        except (json.JSONDecodeError, KeyError, ValueError):
                            continue
        except Exception as e:
            print(f"[EXPORT ERROR] Failed to read log file {log_file}: {e}")
        
        return entries


# Global continuous logger instance
continuous_logger = ContinuousLogger()