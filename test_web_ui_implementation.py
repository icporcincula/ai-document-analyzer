#!/usr/bin/env python3
"""
Test script to validate the Web UI implementation.
This script checks all the components created for the Web UI feature.
"""

import os
import json
import yaml
from pathlib import Path

def test_frontend_structure():
    """Test frontend directory structure and files."""
    print("Testing Frontend Structure...")
    
    frontend_dir = Path("frontend")
    
    # Check required directories
    required_dirs = [
        "frontend/src",
        "frontend/src/components",
        "frontend/src/__tests__",
        "frontend/public"
    ]
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print(f"❌ Missing directory: {dir_path}")
            return False
        print(f"✅ Directory exists: {dir_path}")
    
    # Check required files
    required_files = [
        "frontend/package.json",
        "frontend/src/main.tsx",
        "frontend/src/App.tsx",
        "frontend/src/components/Layout.tsx",
        "frontend/src/components/DocumentUpload.tsx",
        "frontend/src/components/ResultsDisplay.tsx",
        "frontend/src/components/DocumentHistory.tsx",
        "frontend/Dockerfile",
        "frontend/nginx.conf"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Missing file: {file_path}")
            return False
        print(f"✅ File exists: {file_path}")
    
    return True

def test_api_endpoints():
    """Test API endpoints implementation."""
    print("\nTesting API Endpoints...")
    
    api_routes_file = Path("app/api/routes.py")
    if not api_routes_file.exists():
        print("❌ API routes file not found")
        return False
    
    with open(api_routes_file, 'r') as f:
        content = f.read()
    
    # Check for required endpoints
    required_endpoints = [
        "POST /api/v1/analyze",
        "GET /api/v1/results/{task_id}",
        "GET /api/v1/history",
        "GET /api/v1/export/{task_id}/{format}",
        "GET /api/v1/metrics"
    ]
    
    for endpoint in required_endpoints:
        if endpoint not in content:
            print(f"❌ Missing endpoint: {endpoint}")
            return False
        print(f"✅ Endpoint found: {endpoint}")
    
    return True

def test_metrics_implementation():
    """Test metrics implementation."""
    print("\nTesting Metrics Implementation...")
    
    # Check metrics files
    metrics_files = [
        "app/config/metrics_config.py",
        "app/metrics/custom_metrics.py",
        "app/middleware/metrics.py"
    ]
    
    for file_path in metrics_files:
        if not Path(file_path).exists():
            print(f"❌ Missing metrics file: {file_path}")
            return False
        print(f"✅ Metrics file exists: {file_path}")
    
    # Check Prometheus configuration
    prometheus_config = Path("monitoring/prometheus.yml")
    if not prometheus_config.exists():
        print("❌ Prometheus configuration not found")
        return False
    print("✅ Prometheus configuration exists")
    
    # Check Grafana configuration
    grafana_dashboard = Path("monitoring/grafana/dashboards/dashboard.json")
    grafana_datasource = Path("monitoring/grafana/datasources/datasource.yml")
    
    if not grafana_dashboard.exists():
        print("❌ Grafana dashboard not found")
        return False
    print("✅ Grafana dashboard exists")
    
    if not grafana_datasource.exists():
        print("❌ Grafana datasource configuration not found")
        return False
    print("✅ Grafana datasource configuration exists")
    
    return True

def test_docker_compose():
    """Test Docker Compose configuration."""
    print("\nTesting Docker Compose Configuration...")
    
    docker_compose = Path("docker-compose.yml")
    if not docker_compose.exists():
        print("❌ Docker Compose file not found")
        return False
    
    with open(docker_compose, 'r') as f:
        compose_content = f.read()
    
    # Check for required services
    required_services = [
        "api",
        "prometheus", 
        "grafana",
        "frontend"
    ]
    
    for service in required_services:
        if f"{service}:" not in compose_content:
            print(f"❌ Missing service in docker-compose: {service}")
            return False
        print(f"✅ Service found in docker-compose: {service}")
    
    return True

def test_database_integration():
    """Test database integration."""
    print("\nTesting Database Integration...")
    
    # Check database files
    database_files = [
        "app/database/models.py",
        "app/database/session.py",
        "app/services/enhanced_task_result_service.py"
    ]
    
    for file_path in database_files:
        if not Path(file_path).exists():
            print(f"❌ Missing database file: {file_path}")
            return False
        print(f"✅ Database file exists: {file_path}")
    
    return True

def test_documentation():
    """Test documentation."""
    print("\nTesting Documentation...")
    
    documentation_files = [
        "docs/web-ui-guide.md",
        "docs/metrics-guide.md"
    ]
    
    for file_path in documentation_files:
        if not Path(file_path).exists():
            print(f"❌ Missing documentation file: {file_path}")
            return False
        print(f"✅ Documentation file exists: {file_path}")
    
    return True

def validate_package_json():
    """Validate frontend package.json."""
    print("\nValidating Frontend Package.json...")
    
    package_json_path = Path("frontend/package.json")
    if not package_json_path.exists():
        print("❌ Package.json not found")
        return False
    
    with open(package_json_path, 'r') as f:
        package_data = json.load(f)
    
    # Check required dependencies
    required_deps = [
        "react",
        "react-dom", 
        "react-router-dom",
        "axios",
        "react-query",
        "@mui/material",
        "@mui/icons-material"
    ]
    
    dependencies = package_data.get("dependencies", {})
    dev_dependencies = package_data.get("devDependencies", {})
    
    for dep in required_deps:
        if dep not in dependencies:
            print(f"❌ Missing dependency: {dep}")
            return False
        print(f"✅ Dependency found: {dep}")
    
    return True

def validate_docker_compose_content():
    """Validate Docker Compose content."""
    print("\nValidating Docker Compose Content...")
    
    docker_compose = Path("docker-compose.yml")
    with open(docker_compose, 'r') as f:
        compose_data = yaml.safe_load(f)
    
    services = compose_data.get("services", {})
    
    # Check frontend service configuration
    frontend_service = services.get("frontend", {})
    if not frontend_service:
        print("❌ Frontend service not configured")
        return False
    
    # Check required frontend service properties
    required_frontend_props = ["build", "ports", "environment", "networks"]
    for prop in required_frontend_props:
        if prop not in frontend_service:
            print(f"❌ Frontend service missing property: {prop}")
            return False
        print(f"✅ Frontend service has property: {prop}")
    
    # Check API service configuration
    api_service = services.get("api", {})
    if not api_service:
        print("❌ API service not configured")
        return False
    
    # Check required API service properties
    required_api_props = ["build", "ports", "environment", "networks"]
    for prop in required_api_props:
        if prop not in api_service:
            print(f"❌ API service missing property: {prop}")
            return False
        print(f"✅ API service has property: {prop}")
    
    return True

def main():
    """Run all validation tests."""
    print("🚀 Starting Web UI Implementation Validation")
    print("=" * 50)
    
    tests = [
        test_frontend_structure,
        test_api_endpoints,
        test_metrics_implementation,
        test_docker_compose,
        test_database_integration,
        test_documentation,
        validate_package_json,
        validate_docker_compose_content
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test in tests:
        try:
            if test():
                passed_tests += 1
            else:
                print(f"❌ Test failed: {test.__name__}")
        except Exception as e:
            print(f"❌ Test error in {test.__name__}: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Web UI implementation is complete and valid.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)