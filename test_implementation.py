#!/usr/bin/env python3
"""
Simple test script to verify our Phase 3 implementation
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all our modules can be imported"""
    try:
        # Test basic imports
        from app.utils.config import Config
        from app.models.schemas import DocumentType, FieldExtractionRequest
        from app.services.pdf_service import PDFService
        from app.services.presidio_client import PresidioClient
        from app.services.extraction_service import ExtractionService
        
        print("✓ All core modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    try:
        from app.utils.config import Config
        config = Config()
        
        # Test basic properties
        assert hasattr(config, 'app_env')
        assert hasattr(config, 'debug')
        assert hasattr(config, 'host')
        assert hasattr(config, 'port')
        
        print("✓ Configuration class works correctly")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_schemas():
    """Test schema validation"""
    try:
        from app.models.schemas import DocumentType, FieldExtractionRequest, FieldConfidence
        
        # Test DocumentType enum
        assert DocumentType.EMPLOYMENT_CONTRACT.value == "employment_contract"
        
        # Test FieldConfidence validation
        confidence = FieldConfidence(score=0.85, level="HIGH")
        assert confidence.score == 0.85
        assert confidence.level == "HIGH"
        
        print("✓ Schema validation works correctly")
        return True
    except Exception as e:
        print(f"✗ Schema test failed: {e}")
        return False

def test_pytest_config():
    """Test pytest configuration"""
    try:
        import pytest
        print("✓ pytest is available")
        return True
    except ImportError:
        print("✗ pytest not available")
        return False

def test_dependencies():
    """Test that required dependencies are available"""
    required_deps = [
        'pytest', 'pytest_asyncio', 'pytest_cov', 'factory_boy',
        'black', 'ruff', 'mypy'
    ]
    
    missing_deps = []
    for dep in required_deps:
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"✗ Missing dependencies: {missing_deps}")
        return False
    else:
        print("✓ All test dependencies available")
        return True

def main():
    """Run all tests"""
    print("Testing Phase 3 Implementation...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_schemas,
        test_pytest_config,
        test_dependencies
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Phase 3 implementation is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())