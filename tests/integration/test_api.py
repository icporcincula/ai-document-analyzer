import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app
from app.models.schemas import DocumentType, FieldExtractionRequest, PIIExtractionRequest


class TestAPIEndpoints:
    """Integration tests for API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def sample_pdf_content(self):
        """Sample PDF content for testing"""
        return b"""
        %PDF-1.4
        1 0 obj
        << /Type /Catalog /Pages 2 0 R >>
        endobj
        2 0 obj
        << /Type /Pages /Kids [3 0 R] /Count 1 >>
        endobj
        3 0 obj
        << /Type /Page /Parent 2 0 R /Contents 4 0 R >>
        endobj
        4 0 obj
        << /Length 44 >>
        stream
        BT
        /F1 12 Tf
        72 720 Td
        (John Smith works at TechCorp with ID 12345) Tj
        ET
        endstream
        endobj
        xref
        0 5
        0000000000 65535 f 
        0000000009 00000 n 
        0000000058 00000 n 
        0000000117 00000 n 
        0000000176 00000 n 
        trailer
        << /Size 5 /Root 1 0 R >>
        startxref
        295
        %%EOF
        """

    @pytest.fixture
    def sample_text_content(self):
        """Sample text content for testing"""
        return "John Smith works at TechCorp with ID 12345 starting 2024-01-15 earning $75,000 in Engineering."

    @pytest.fixture
    def mock_presidio_client(self):
        """Mock Presidio client for testing"""
        mock_client = MagicMock()
        mock_client.analyze_text = AsyncMock(return_value=[])
        mock_client.anonymize_text = AsyncMock(return_value=("Anonymized text", {}))
        mock_client.health_check = AsyncMock(return_value=True)
        return mock_client

    @pytest.fixture
    def mock_extraction_service(self):
        """Mock extraction service for testing"""
        mock_service = MagicMock()
        mock_service.extract_fields = AsyncMock(return_value=None)
        return mock_service

    def test_health_endpoint(self, client):
        """Test /health endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"

    def test_analyze_endpoint_success(self, client, sample_pdf_content, mock_presidio_client, mock_extraction_service):
        """Test /analyze endpoint with successful processing"""
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file_path = temp_file.name

        try:
            # Mock dependencies
            with patch('app.api.routes.PresidioClient', return_value=mock_presidio_client), \
                 patch('app.api.routes.ExtractionService', return_value=mock_extraction_service):
                
                # Mock extraction service response
                from app.models.schemas import FieldExtractionResponse, FieldExtractionStatus, FieldExtractionResult, FieldConfidence
                mock_response = FieldExtractionResponse(
                    status=FieldExtractionStatus.SUCCESS,
                    results=[
                        FieldExtractionResult(
                            field_name="employee_name",
                            value="John Smith",
                            confidence=FieldConfidence(score=0.95, level="HIGH")
                        )
                    ],
                    overall_confidence=0.95,
                    message="Extraction completed successfully"
                )
                mock_extraction_service.extract_fields.return_value = mock_response
                
                # Test request
                with open(temp_file_path, 'rb') as pdf_file:
                    files = {"file": ("test.pdf", pdf_file, "application/pdf")}
                    data = {
                        "document_type": "employment_contract",
                        "fields": ["employee_name", "employee_id", "start_date"]
                    }
                    
                    response = client.post("/analyze", files=files, data=data)
                
                # Assertions
                assert response.status_code == 200
                result = response.json()
                assert result["status"] == "success"
                assert "extraction_result" in result
                assert "pii_result" in result
                assert "processing_time" in result

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_analyze_endpoint_invalid_file_type(self, client):
        """Test /analyze endpoint with invalid file type"""
        # Test with invalid file type
        files = {"file": ("test.txt", b"not a pdf", "text/plain")}
        data = {
            "document_type": "employment_contract",
            "fields": ["employee_name"]
        }
        
        response = client.post("/analyze", files=files, data=data)
        
        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "Invalid file type" in result["error"]

    def test_analyze_endpoint_missing_file(self, client):
        """Test /analyze endpoint without file"""
        data = {
            "document_type": "employment_contract",
            "fields": ["employee_name"]
        }
        
        response = client.post("/analyze", data=data)
        
        assert response.status_code == 422  # Validation error

    def test_analyze_endpoint_missing_document_type(self, client, sample_pdf_content):
        """Test /analyze endpoint without document type"""
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as pdf_file:
                files = {"file": ("test.pdf", pdf_file, "application/pdf")}
                data = {"fields": ["employee_name"]}
                
                response = client.post("/analyze", files=files, data=data)
            
            assert response.status_code == 422  # Validation error

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_analyze_endpoint_missing_fields(self, client, sample_pdf_content):
        """Test /analyze endpoint without fields"""
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as pdf_file:
                files = {"file": ("test.pdf", pdf_file, "application/pdf")}
                data = {"document_type": "employment_contract"}
                
                response = client.post("/analyze", files=files, data=data)
            
            assert response.status_code == 422  # Validation error

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_analyze_endpoint_large_file(self, client):
        """Test /analyze endpoint with file too large"""
        # Create a large file content
        large_content = b"A" * (11 * 1024 * 1024)  # 11MB
        
        files = {"file": ("large.pdf", large_content, "application/pdf")}
        data = {
            "document_type": "employment_contract",
            "fields": ["employee_name"]
        }
        
        response = client.post("/analyze", files=files, data=data)
        
        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "File size exceeds" in result["error"]

    def test_analyze_endpoint_corrupted_pdf(self, client):
        """Test /analyze endpoint with corrupted PDF"""
        # Create corrupted PDF content
        corrupted_content = b"This is not a valid PDF file"
        
        files = {"file": ("corrupted.pdf", corrupted_content, "application/pdf")}
        data = {
            "document_type": "employment_contract",
            "fields": ["employee_name"]
        }
        
        response = client.post("/analyze", files=files, data=data)
        
        assert response.status_code == 400
        result = response.json()
        assert "error" in result
        assert "Failed to process PDF file" in result["error"]

    def test_analyze_endpoint_pii_extraction_error(self, client, sample_pdf_content, mock_presidio_client):
        """Test /analyze endpoint with PII extraction error"""
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file_path = temp_file.name

        try:
            # Mock Presidio client to raise error
            mock_presidio_client.analyze_text.side_effect = Exception("Presidio error")
            
            with patch('app.api.routes.PresidioClient', return_value=mock_presidio_client):
                with open(temp_file_path, 'rb') as pdf_file:
                    files = {"file": ("test.pdf", pdf_file, "application/pdf")}
                    data = {
                        "document_type": "employment_contract",
                        "fields": ["employee_name"]
                    }
                    
                    response = client.post("/analyze", files=files, data=data)
                
                # Should still succeed but with PII extraction error
                assert response.status_code == 200
                result = response.json()
                assert result["status"] == "success"
                assert "extraction_result" in result

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_analyze_endpoint_extraction_error(self, client, sample_pdf_content, mock_presidio_client, mock_extraction_service):
        """Test /analyze endpoint with field extraction error"""
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file_path = temp_file.name

        try:
            # Mock extraction service to raise error
            from app.services.extraction_service import ExtractionError
            mock_extraction_service.extract_fields.side_effect = ExtractionError("Extraction failed")
            
            with patch('app.api.routes.PresidioClient', return_value=mock_presidio_client), \
                 patch('app.api.routes.ExtractionService', return_value=mock_extraction_service):
                
                with open(temp_file_path, 'rb') as pdf_file:
                    files = {"file": ("test.pdf", pdf_file, "application/pdf")}
                    data = {
                        "document_type": "employment_contract",
                        "fields": ["employee_name"]
                    }
                    
                    response = client.post("/analyze", files=files, data=data)
                
                # Should still succeed but with extraction error
                assert response.status_code == 200
                result = response.json()
                assert result["status"] == "success"
                assert "extraction_result" in result

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_analyze_endpoint_unsupported_document_type(self, client, sample_pdf_content, mock_presidio_client):
        """Test /analyze endpoint with unsupported document type"""
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file_path = temp_file.name

        try:
            with patch('app.api.routes.PresidioClient', return_value=mock_presidio_client):
                with open(temp_file_path, 'rb') as pdf_file:
                    files = {"file": ("test.pdf", pdf_file, "application/pdf")}
                    data = {
                        "document_type": "unsupported_type",
                        "fields": ["employee_name"]
                    }
                    
                    response = client.post("/analyze", files=files, data=data)
                
                # Should succeed but may have different behavior
                assert response.status_code == 200

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_analyze_endpoint_multiple_fields(self, client, sample_pdf_content, mock_presidio_client, mock_extraction_service):
        """Test /analyze endpoint with multiple fields"""
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file_path = temp_file.name

        try:
            # Mock extraction service response with multiple fields
            from app.models.schemas import FieldExtractionResponse, FieldExtractionStatus, FieldExtractionResult, FieldConfidence
            mock_response = FieldExtractionResponse(
                status=FieldExtractionStatus.SUCCESS,
                results=[
                    FieldExtractionResult(
                        field_name="employee_name",
                        value="John Smith",
                        confidence=FieldConfidence(score=0.95, level="HIGH")
                    ),
                    FieldExtractionResult(
                        field_name="employee_id",
                        value="12345",
                        confidence=FieldConfidence(score=0.90, level="HIGH")
                    ),
                    FieldExtractionResult(
                        field_name="start_date",
                        value="2024-01-15",
                        confidence=FieldConfidence(score=0.85, level="MEDIUM")
                    )
                ],
                overall_confidence=0.90,
                message="Extraction completed successfully"
            )
            mock_extraction_service.extract_fields.return_value = mock_response
            
            with patch('app.api.routes.PresidioClient', return_value=mock_presidio_client), \
                 patch('app.api.routes.ExtractionService', return_value=mock_extraction_service):
                
                with open(temp_file_path, 'rb') as pdf_file:
                    files = {"file": ("test.pdf", pdf_file, "application/pdf")}
                    data = {
                        "document_type": "employment_contract",
                        "fields": ["employee_name", "employee_id", "start_date", "salary", "department"]
                    }
                    
                    response = client.post("/analyze", files=files, data=data)
                
                # Assertions
                assert response.status_code == 200
                result = response.json()
                assert result["status"] == "success"
                assert "extraction_result" in result
                extraction_result = result["extraction_result"]
                assert extraction_result["status"] == "success"
                assert len(extraction_result["results"]) == 5  # All requested fields

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_analyze_endpoint_empty_fields_list(self, client, sample_pdf_content, mock_presidio_client):
        """Test /analyze endpoint with empty fields list"""
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file_path = temp_file.name

        try:
            with patch('app.api.routes.PresidioClient', return_value=mock_presidio_client):
                with open(temp_file_path, 'rb') as pdf_file:
                    files = {"file": ("test.pdf", pdf_file, "application/pdf")}
                    data = {
                        "document_type": "employment_contract",
                        "fields": []
                    }
                    
                    response = client.post("/analyze", files=files, data=data)
                
                # Should succeed with empty extraction
                assert response.status_code == 200
                result = response.json()
                assert result["status"] == "success"

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_analyze_endpoint_different_document_types(self, client, sample_pdf_content, mock_presidio_client, mock_extraction_service):
        """Test /analyze endpoint with different document types"""
        document_types = [
            "employment_contract",
            "invoice", 
            "medical_record",
            "financial_statement",
            "legal_contract",
            "academic_paper",
            "resume",
            "email",
            "news_article"
        ]
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file_path = temp_file.name

        try:
            # Mock extraction service response
            from app.models.schemas import FieldExtractionResponse, FieldExtractionStatus, FieldExtractionResult, FieldConfidence
            mock_response = FieldExtractionResponse(
                status=FieldExtractionStatus.SUCCESS,
                results=[
                    FieldExtractionResult(
                        field_name="test_field",
                        value="test_value",
                        confidence=FieldConfidence(score=0.9, level="HIGH")
                    )
                ],
                overall_confidence=0.9,
                message="Extraction completed successfully"
            )
            mock_extraction_service.extract_fields.return_value = mock_response
            
            with patch('app.api.routes.PresidioClient', return_value=mock_presidio_client), \
                 patch('app.api.routes.ExtractionService', return_value=mock_extraction_service):
                
                for doc_type in document_types:
                    with open(temp_file_path, 'rb') as pdf_file:
                        files = {"file": ("test.pdf", pdf_file, "application/pdf")}
                        data = {
                            "document_type": doc_type,
                            "fields": ["test_field"]
                        }
                        
                        response = client.post("/analyze", files=files, data=data)
                    
                    # Should succeed for all document types
                    assert response.status_code == 200
                    result = response.json()
                    assert result["status"] == "success"

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_analyze_endpoint_with_authentication_disabled(self, client, sample_pdf_content, mock_presidio_client):
        """Test /analyze endpoint when authentication is disabled"""
        # This test verifies the endpoint works when auth is disabled (default)
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file_path = temp_file.name

        try:
            with patch('app.api.routes.PresidioClient', return_value=mock_presidio_client):
                with open(temp_file_path, 'rb') as pdf_file:
                    files = {"file": ("test.pdf", pdf_file, "application/pdf")}
                    data = {
                        "document_type": "employment_contract",
                        "fields": ["employee_name"]
                    }
                    
                    response = client.post("/analyze", files=files, data=data)
                
                # Should succeed without authentication
                assert response.status_code == 200

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)