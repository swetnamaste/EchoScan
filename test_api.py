"""
Test for the FastAPI application in api.py
"""

import pytest
import os
import sys
import subprocess
import time
import requests

def test_api_can_be_imported():
    """Test that api.py can be imported without errors"""
    import api
    assert api.app is not None


def test_api_health_check():
    """Test API health check endpoint via subprocess"""
    # Start API server in background
    env = os.environ.copy()
    env["PORT"] = "8081"  # Use different port for testing
    
    process = subprocess.Popen(
        [sys.executable, "api.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    
    try:
        # Wait for server to start
        time.sleep(3)
        
        # Test health endpoint
        response = requests.get("http://localhost:8081/health", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "EchoScan"
        
    except Exception as e:
        # If anything fails, still clean up
        process.terminate()
        process.wait()
        pytest.fail(f"Health check test failed: {e}")
    finally:
        # Clean up process
        process.terminate()
        process.wait()


def test_api_scan_endpoint():
    """Test API scan endpoint via subprocess"""
    # Start API server in background
    env = os.environ.copy()
    env["PORT"] = "8082"  # Use different port for testing
    
    process = subprocess.Popen(
        [sys.executable, "api.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    
    try:
        # Wait for server to start
        time.sleep(3)
        
        # Test scan endpoint
        response = requests.post(
            "http://localhost:8082/api/scan",
            json={"input": "test input"},
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "verdict" in data
        assert "delta_s" in data
        assert "glyph_id" in data
        
    except Exception as e:
        # If anything fails, still clean up
        process.terminate()
        process.wait()
        pytest.fail(f"Scan endpoint test failed: {e}")
    finally:
        # Clean up process
        process.terminate()
        process.wait()


if __name__ == "__main__":
    # Run basic tests
    test_api_can_be_imported()
    print("✓ API import test passed")
    
    test_api_health_check()
    print("✓ API health check test passed")
    
    test_api_scan_endpoint()
    print("✓ API scan endpoint test passed")
    
    print("All API tests passed!")