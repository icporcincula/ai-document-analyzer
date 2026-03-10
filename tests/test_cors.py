# tests/test_cors.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_cors_allowed_origin():
    """Test that CORS allows configured origins"""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type"
    }
    
    response = client.options("/api/v1/analyze", headers=headers)
    
    # Should allow the request
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

def test_cors_disallowed_origin():
    """Test that CORS blocks unauthorized origins"""
    headers = {
        "Origin": "http://malicious-site.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type"
    }
    
    response = client.options("/api/v1/analyze", headers=headers)
    
    # Should block the request
    assert response.status_code == 400

def test_cors_preflight_request():
    """Test CORS preflight OPTIONS request"""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type,Authorization"
    }
    
    response = client.options("/api/v1/analyze", headers=headers)
    
    assert response.status_code == 200
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers

def test_cors_simple_request():
    """Test simple CORS request"""
    headers = {
        "Origin": "http://localhost:3000"
    }
    
    response = client.get("/api/v1/health", headers=headers)
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers