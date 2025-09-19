"""
Test suite for EchoScan pipeline enhancements.
Tests validation, configuration hot-reload, and error reporting functionality.
"""

import pytest
import json
import tempfile
import time
import os
from pathlib import Path

from validation import ValidationUtility, SBSHHashSchema, EchoVerifierSchema, PipelineResultSchema
from config_hot_reload import ConfigManager
from error_report import ErrorReporter
import main


class TestValidation:
    """Test schema validation functionality."""
    
    def test_sbsh_validation_valid(self):
        """Test SBSH output validation with valid data."""
        validator = ValidationUtility()
        valid_sbsh = {
            "delta_hash": "0.12345",
            "fold_hash": "1a2b3c4d",
            "glyph_hash": None,
            "status": "LOCKED"
        }
        assert validator.validate_sbsh_output(valid_sbsh) == True
    
    def test_sbsh_validation_invalid(self):
        """Test SBSH output validation with invalid data."""
        validator = ValidationUtility()
        invalid_sbsh = {
            "delta_hash": "not_a_number",
            "fold_hash": "1a2b3c4d",
            "status": "LOCKED"
        }
        assert validator.validate_sbsh_output(invalid_sbsh) == False
    
    def test_echoverifier_validation_valid(self):
        """Test EchoVerifier output validation with valid data."""
        validator = ValidationUtility()
        valid_ev = {
            "input": "test input",
            "verdict": "Authentic",
            "delta_s": 0.5,
            "fold_vector": [0.1, 0.2, 0.3, 0.4],
            "glyph_id": "GHX-1234",
            "ancestry_depth": 5,
            "echo_sense": 0.8,
            "vault_permission": True
        }
        assert validator.validate_echoverifier_output(valid_ev) == True
    
    def test_echoverifier_validation_invalid(self):
        """Test EchoVerifier output validation with invalid data."""
        validator = ValidationUtility()
        invalid_ev = {
            "input": "test input",
            "verdict": "Invalid_Verdict",  # Invalid verdict
            "delta_s": 1.5,  # Out of range
            "fold_vector": [0.1, 2.0],  # Out of range values
            "glyph_id": "INVALID-ID",  # Invalid format
            "ancestry_depth": 25,  # Out of range
            "echo_sense": 1.2,  # Out of range
            "vault_permission": True
        }
        assert validator.validate_echoverifier_output(invalid_ev) == False
    
    def test_pipeline_validation_valid(self):
        """Test pipeline output validation with valid data."""
        validator = ValidationUtility()
        valid_pipeline = {
            "EchoScore": 75.5,
            "Decision": "Authentic",
            "AdvisoryFlags": ["Test flag"],
            "FullResults": {"test": {}}
        }
        assert validator.validate_pipeline_output(valid_pipeline) == True
    
    def test_pipeline_validation_invalid(self):
        """Test pipeline output validation with invalid data."""
        validator = ValidationUtility()
        invalid_pipeline = {
            "EchoScore": 150.0,  # Out of range
            "Decision": "InvalidDecision",  # Invalid decision
            "FullResults": {}
            # Missing AdvisoryFlags
        }
        assert validator.validate_pipeline_output(invalid_pipeline) == False


class TestConfigManager:
    """Test configuration hot-reload functionality."""
    
    def test_config_loading(self):
        """Test basic configuration loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "test_config.json")
            test_config = {
                "echosense_weights": {
                    "delta_component": 0.4,
                    "fold_component": 0.3,
                    "glyph_component": 0.2,
                    "ancestry_component": 0.1
                }
            }
            
            with open(config_path, 'w') as f:
                json.dump(test_config, f)
            
            config_manager = ConfigManager(config_path)
            weights = config_manager.get_echosense_weights()
            
            assert weights["delta_component"] == 0.4
            assert weights["fold_component"] == 0.3
            assert sum(weights.values()) == 1.0
    
    def test_config_reload(self):
        """Test configuration hot-reload functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "test_config.json")
            
            # Initial config
            test_config = {
                "echosense_weights": {
                    "delta_component": 0.3,
                    "fold_component": 0.3,
                    "glyph_component": 0.2,
                    "ancestry_component": 0.2
                }
            }
            
            with open(config_path, 'w') as f:
                json.dump(test_config, f)
            
            config_manager = ConfigManager(config_path)
            initial_weights = config_manager.get_echosense_weights()
            assert initial_weights["delta_component"] == 0.3
            
            # Update config
            test_config["echosense_weights"]["delta_component"] = 0.5
            with open(config_path, 'w') as f:
                json.dump(test_config, f)
            
            # Wait a bit and reload
            time.sleep(0.1)
            config_manager.reload_config()
            updated_weights = config_manager.get_echosense_weights()
            assert updated_weights["delta_component"] == 0.5
            
            config_manager.stop_watching()
    
    def test_default_config_creation(self):
        """Test default configuration creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "nonexistent_config.json")
            config_manager = ConfigManager(config_path)
            
            # Should create default config
            assert os.path.exists(config_path)
            
            weights = config_manager.get_echosense_weights()
            assert "delta_component" in weights
            assert "fold_component" in weights
            
            config_manager.stop_watching()


class TestErrorReporter:
    """Test centralized error reporting functionality."""
    
    def test_error_logging(self):
        """Test basic error logging functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            error_reporter = ErrorReporter(temp_dir)
            
            error_reporter.log_error("TestError", "Test error message", {"test": "context"})
            
            summary = error_reporter.get_error_summary()
            assert summary["total_errors"] == 1
            assert summary["error_counts"]["general"] == 1
            
            recent_errors = error_reporter.get_recent_errors()
            assert len(recent_errors) == 1
            assert recent_errors[0]["error_type"] == "TestError"
    
    def test_validation_error_logging(self):
        """Test validation-specific error logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            error_reporter = ErrorReporter(temp_dir)
            
            error_reporter.log_validation_error("Validation failed", {"field": "test"})
            
            summary = error_reporter.get_error_summary()
            assert summary["error_counts"]["validation"] == 1
    
    def test_config_error_logging(self):
        """Test config-specific error logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            error_reporter = ErrorReporter(temp_dir)
            
            error_reporter.log_config_error("Config load failed", {"path": "test.json"})
            
            summary = error_reporter.get_error_summary()
            assert summary["error_counts"]["config"] == 1
    
    def test_error_report_creation(self):
        """Test comprehensive error report creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            error_reporter = ErrorReporter(temp_dir)
            
            error_reporter.log_error("TestError1", "Message 1")
            error_reporter.log_validation_error("Validation error")
            error_reporter.log_config_error("Config error")
            
            report_path = os.path.join(temp_dir, "test_report.json")
            result_path = error_reporter.create_error_report(report_path)
            
            assert result_path == report_path
            assert os.path.exists(report_path)
            
            with open(report_path, 'r') as f:
                report_data = json.load(f)
            
            assert report_data["summary"]["total_errors"] == 3
            assert len(report_data["recent_errors"]) == 3


class TestPipelineIntegration:
    """Test complete pipeline integration with all enhancements."""
    
    def test_pipeline_with_validation(self):
        """Test pipeline runs with validation enabled."""
        result = main.run_pipeline("Hello world test", "text")
        
        # Should have all required fields
        required_fields = ["EchoScore", "Decision", "AdvisoryFlags", "FullResults"]
        for field in required_fields:
            assert field in result
        
        # Should have numeric echo score
        assert isinstance(result["EchoScore"], (int, float))
        assert 0 <= result["EchoScore"] <= 100
        
        # Should have valid decision
        valid_decisions = ["Authentic", "Plausible", "Synthetic", "Questionable", "Error"]
        assert result["Decision"] in valid_decisions
        
        # Should have advisory flags list
        assert isinstance(result["AdvisoryFlags"], list)
        
        # Should have full results
        assert isinstance(result["FullResults"], dict)
        assert "echoverifier" in result["FullResults"]
    
    def test_pipeline_with_config_integration(self):
        """Test pipeline uses configuration values correctly."""
        # Test with different config values
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "pipeline_config.json")
            test_config = {
                "echosense_weights": {
                    "delta_component": 0.5,
                    "fold_component": 0.2,
                    "glyph_component": 0.2,
                    "ancestry_component": 0.1
                },
                "vault_access": {
                    "min_echo_sense": 0.9,
                    "min_ancestry_depth": 5
                }
            }
            
            with open(config_path, 'w') as f:
                json.dump(test_config, f)
            
            # Create new config manager instance
            from config_hot_reload import ConfigManager
            temp_config_manager = ConfigManager(config_path)
            
            # Test that weights are loaded correctly
            weights = temp_config_manager.get_echosense_weights()
            assert weights["delta_component"] == 0.5
            assert weights["fold_component"] == 0.2
            
            vault_config = temp_config_manager.get_vault_access_config()
            assert vault_config["min_echo_sense"] == 0.9
            assert vault_config["min_ancestry_depth"] == 5
            
            temp_config_manager.stop_watching()
    
    def test_pipeline_error_handling(self):
        """Test pipeline handles errors gracefully."""
        # Test with empty input
        result = main.run_pipeline("", "text")
        assert "error" in result
        assert result["Decision"] == "Error"
        
        # Test with invalid file
        result = main.run_pipeline("/nonexistent/file.txt", "file")
        assert "error" in result
        assert result["Decision"] == "Error"


if __name__ == "__main__":
    # Run tests manually without pytest if needed
    print("Running EchoScan Enhancement Tests...")
    
    # Test validation
    print("\n=== Testing Validation ===")
    test_validation = TestValidation()
    try:
        test_validation.test_sbsh_validation_valid()
        test_validation.test_sbsh_validation_invalid()
        test_validation.test_echoverifier_validation_valid()
        test_validation.test_echoverifier_validation_invalid()
        test_validation.test_pipeline_validation_valid()
        test_validation.test_pipeline_validation_invalid()
        print("✅ All validation tests passed")
    except Exception as e:
        print(f"❌ Validation tests failed: {e}")
    
    # Test config manager
    print("\n=== Testing Configuration Manager ===")
    test_config = TestConfigManager()
    try:
        test_config.test_config_loading()
        test_config.test_config_reload()
        test_config.test_default_config_creation()
        print("✅ All configuration tests passed")
    except Exception as e:
        print(f"❌ Configuration tests failed: {e}")
    
    # Test error reporter
    print("\n=== Testing Error Reporter ===")
    test_error = TestErrorReporter()
    try:
        test_error.test_error_logging()
        test_error.test_validation_error_logging()
        test_error.test_config_error_logging()
        test_error.test_error_report_creation()
        print("✅ All error reporting tests passed")
    except Exception as e:
        print(f"❌ Error reporting tests failed: {e}")
    
    # Test pipeline integration
    print("\n=== Testing Pipeline Integration ===")
    test_pipeline = TestPipelineIntegration()
    try:
        test_pipeline.test_pipeline_with_validation()
        test_pipeline.test_pipeline_with_config_integration()
        test_pipeline.test_pipeline_error_handling()
        print("✅ All pipeline integration tests passed")
    except Exception as e:
        print(f"❌ Pipeline integration tests failed: {e}")
    
    print("\n=== Test Suite Complete ===")