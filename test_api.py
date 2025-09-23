#!/usr/bin/env python3
"""
Test API functionality to verify the FastAPI application works correctly.
"""

import pytest
import os
import subprocess
import time
import requests
import signal


def test_api_health_check():
    """Test that the API starts and responds to health checks."""
    # Start the API server in a subprocess
    env = os.environ.copy()
    env['PORT'] = '8081'  # Use different port to avoid conflicts
    
    process = subprocess.Popen(
        ['python', 'api.py'], 
        cwd='/home/runner/work/EchoScan/EchoScan',
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        # Give the server time to start
        time.sleep(3)
        
        # Test health endpoint
        response = requests.get('http://localhost:8081/health', timeout=5)
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data['status'] == 'healthy'
        assert health_data['service'] == 'EchoScan API'
        assert health_data['version'] == '1.0.0'
        
        # Test root endpoint
        response = requests.get('http://localhost:8081/', timeout=5)
        assert response.status_code == 200
        
        root_data = response.json()
        assert root_data['message'] == 'EchoScan API'
        assert 'endpoints' in root_data
        
        # Test scan endpoint
        scan_data = {'input': 'test message', 'mode': 'verify'}
        response = requests.post(
            'http://localhost:8081/api/scan',
            json=scan_data,
            timeout=10
        )
        assert response.status_code == 200
        
        scan_result = response.json()
        assert scan_result['status'] == 'success'
        assert 'result' in scan_result
        assert scan_result['result']['input'] == 'test message'
        assert 'verdict' in scan_result['result']
        
    finally:
        # Clean up: terminate the server process
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def test_api_default_port():
    """Test that the API uses default port 8080 when PORT env var is not set."""
    # Test with no PORT environment variable
    env = os.environ.copy()
    if 'PORT' in env:
        del env['PORT']
    
    process = subprocess.Popen(
        ['python', 'api.py'], 
        cwd='/home/runner/work/EchoScan/EchoScan',
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        # Give the server time to start
        time.sleep(3)
        
        # Test that it's running on default port 8080
        response = requests.get('http://localhost:8080/health', timeout=5)
        assert response.status_code == 200
        
    finally:
        # Clean up: terminate the server process
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == '__main__':
    test_api_health_check()
    test_api_default_port()
    print("All API tests passed!")