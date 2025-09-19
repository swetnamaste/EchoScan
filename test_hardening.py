"""
Test hardening features - quarantine, performance monitoring, and continuous logging
"""

import pytest
import json
import os
import tempfile
from pathlib import Path

def test_quarantine_manager():
    """Test quarantine manager functionality."""
    from quarantine_manager import QuarantineManager
    
    # Create temporary quarantine directory
    with tempfile.TemporaryDirectory() as temp_dir:
        qm = QuarantineManager(quarantine_dir=temp_dir)
        
        # Test edge case detection
        test_result = {
            "verdict": "Hallucination", 
            "delta_s": 0.025,  # High drift
            "glyph_id": "unclassified",  # Unclassified glyph
            "echo_sense": 0.05  # Low authenticity
        }
        
        should_quarantine, reason = qm.should_quarantine(test_result)
        
        assert should_quarantine == True
        assert "High drift detected" in reason
        assert "Unclassified glyph" in reason
        assert "Low authenticity" in reason
        
        # Test quarantine processing
        test_input = "Test input that should be quarantined"
        filepath = qm.quarantine_input(test_input, test_result, reason)
        
        assert os.path.exists(filepath)
        
        # Verify quarantine file contents
        with open(filepath, 'r') as f:
            quarantine_data = json.load(f)
        
        assert quarantine_data["reason"] == reason
        assert quarantine_data["input_length"] == len(test_input)
        assert "timestamp" in quarantine_data
        
        # Test stats
        stats = qm.get_quarantine_stats()
        assert stats["total_quarantined"] >= 1

def test_performance_monitor():
    """Test performance monitoring functionality."""
    from performance_monitor import PerformanceMonitor
    
    pm = PerformanceMonitor(latency_threshold=1.0)
    
    # Test measurement recording
    pm.record_measurement("test_operation", 0.5)
    pm.record_measurement("test_operation", 0.7)
    pm.record_measurement("test_operation", 0.6)
    
    stats = pm.get_statistics()
    
    assert stats["total_requests"] == 3
    assert "test_operation" in stats["operations"]
    assert stats["operations"]["test_operation"]["count"] == 3
    assert stats["operations"]["test_operation"]["average_latency"] == pytest.approx(0.6, rel=1e-2)
    
    # Test context manager
    with pm.measure_operation("context_test") as measurement:
        pass  # Quick operation
    
    updated_stats = pm.get_statistics()
    assert "context_test" in updated_stats["operations"]

def test_continuous_logger():
    """Test continuous logger functionality."""
    from continuous_logger import ContinuousLogger
    
    # Create temporary log directory
    with tempfile.TemporaryDirectory() as temp_dir:
        cl = ContinuousLogger(log_dir=temp_dir)
        
        # Test edge case logging
        test_input = "Test input for logging"
        test_result = {"verdict": "Hallucination", "delta_s": 0.03}
        
        cl.log_edge_case(
            input_data=test_input,
            result=test_result, 
            anomaly_type="drift",
            severity="high"
        )
        
        # Check that anomaly was recorded
        recent_anomalies = cl.get_recent_anomalies()
        assert len(recent_anomalies) >= 1
        
        anomaly = recent_anomalies[0]
        assert anomaly["anomaly_type"] == "drift"
        assert anomaly["severity"] == "high"
        
        # Test summary
        summary = cl.get_anomaly_summary(hours=24)
        assert summary["total_anomalies"] >= 1
        assert "drift" in summary["anomaly_types"]
        
        # Test field test logging
        cl.log_field_test(
            operation="test_verify",
            input_data=test_input,
            result=test_result,
            performance_metrics={"latency": 0.5}
        )
        
        stats = cl.get_statistics()
        assert stats["field_tests_logged"] >= 1

def test_enhanced_vault():
    """Test enhanced vault with retry and backup."""
    from vault.vault import Vault
    
    # Create temporary vault with backup
    with tempfile.TemporaryDirectory() as temp_dir:
        vault = Vault(backup_dir=temp_dir)
        
        test_data = {"test": "data", "timestamp": "2024-01-01"}
        
        # Test successful logging
        success = vault.log(test_data)
        assert success == True
        assert len(vault.entries) >= 1
        
        # Test safe logging
        status = vault.safe_log(test_data, critical=True)
        assert status["vault_logged"] == True
        assert "timestamp" in status
        
        # Test stats
        stats = vault.get_vault_stats()
        assert stats["total_entries"] >= 1
        assert stats["log_attempts"] >= 2
        assert stats["success_rate"] > 0

def test_integrated_hardening():
    """Test integrated hardening features with EchoVerifier."""
    import echoverifier
    
    # Test input that should trigger quarantine
    test_input = "This is a test input that should trigger various hardening features"
    
    result = echoverifier.run(test_input, mode="verify")
    
    # Verify enhanced fields are present
    assert "quarantine" in result
    assert "vault_status" in result
    assert "confidence_band" in result
    assert "provenance" in result
    assert "advisory_flags" in result
    
    # Verify quarantine processing occurred
    quarantine_info = result["quarantine"]
    assert "quarantined" in quarantine_info
    assert "reason" in quarantine_info
    
    # Verify vault status
    vault_status = result["vault_status"]
    assert "vault_logged" in vault_status
    assert "timestamp" in vault_status
    
    # Verify comprehensive metadata
    metadata = result["metadata"]
    assert "sbsm" in metadata
    assert "delta_s_result" in metadata
    assert "glyph_result" in metadata

def test_cli_hardening_flags():
    """Test new CLI flags for hardening features."""
    from quarantine_manager import quarantine_manager
    from performance_monitor import performance_monitor
    from continuous_logger import continuous_logger
    from vault.vault import vault
    
    # These should not raise exceptions
    qstats = quarantine_manager.get_quarantine_stats()
    assert "total_quarantined" in qstats
    
    pstats = performance_monitor.get_statistics()
    assert "total_requests" in pstats
    
    lstats = continuous_logger.get_statistics()
    assert "edge_cases_logged" in lstats
    
    vstats = vault.get_vault_stats()
    assert "total_entries" in vstats

if __name__ == "__main__":
    pytest.main([__file__, "-v"])