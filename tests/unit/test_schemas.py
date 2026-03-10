import pytest
from datetime import datetime
from pydantic import ValidationError
from app.models.schemas import (
    DocumentType, FieldExtractionRequest, FieldExtractionResponse,
    FieldExtractionResult, FieldConfidence, FieldExtractionStatus,
    PIIEntity, PIIExtractionRequest, PIIExtractionResponse,
    PIIExtractionResult, AuditLogEntry, AuditLogResponse
)


class TestDocumentType:
    """Test cases for DocumentType enum"""

    def test_document_type_values(self):
        """Test DocumentType enum values"""
        assert DocumentType.EMPLOYMENT_CONTRACT.value == "employment_contract"
        assert DocumentType.INVOICE.value == "invoice"
        assert DocumentType.MEDICAL_RECORD.value == "medical_record"
        assert DocumentType.FINANCIAL_STATEMENT.value == "financial_statement"
        assert DocumentType.LEGAL_CONTRACT.value == "legal_contract"
        assert DocumentType.ACADEMIC_PAPER.value == "academic_paper"
        assert DocumentType.RESUME.value == "resume"
        assert DocumentType.EMAIL.value == "email"
        assert DocumentType.NEWS_ARTICLE.value == "news_article"

    def test_document_type_from_value(self):
        """Test DocumentType creation from string values"""
        assert DocumentType("employment_contract") == DocumentType.EMPLOYMENT_CONTRACT
        assert DocumentType("invoice") == DocumentType.INVOICE
        assert DocumentType("medical_record") == DocumentType.MEDICAL_RECORD
        assert DocumentType("financial_statement") == DocumentType.FINANCIAL_STATEMENT
        assert DocumentType("legal_contract") == DocumentType.LEGAL_CONTRACT
        assert DocumentType("academic_paper") == DocumentType.ACADEMIC_PAPER
        assert DocumentType("resume") == DocumentType.RESUME
        assert DocumentType("email") == DocumentType.EMAIL
        assert DocumentType("news_article") == DocumentType.NEWS_ARTICLE

    def test_document_type_invalid_value(self):
        """Test DocumentType with invalid value"""
        with pytest.raises(ValueError):
            DocumentType("invalid_type")


class TestFieldConfidence:
    """Test cases for FieldConfidence model"""

    def test_field_confidence_valid(self):
        """Test valid FieldConfidence creation"""
        confidence = FieldConfidence(score=0.85, level="HIGH")
        assert confidence.score == 0.85
        assert confidence.level == "HIGH"

    def test_field_confidence_medium(self):
        """Test FieldConfidence with medium confidence"""
        confidence = FieldConfidence(score=0.7, level="MEDIUM")
        assert confidence.score == 0.7
        assert confidence.level == "MEDIUM"

    def test_field_confidence_low(self):
        """Test FieldConfidence with low confidence"""
        confidence = FieldConfidence(score=0.4, level="LOW")
        assert confidence.score == 0.4
        assert confidence.level == "LOW"

    def test_field_confidence_missing(self):
        """Test FieldConfidence with missing confidence"""
        confidence = FieldConfidence(score=0.0, level="MISSING")
        assert confidence.score == 0.0
        assert confidence.level == "MISSING"

    def test_field_confidence_score_validation(self):
        """Test FieldConfidence score validation"""
        # Valid scores
        FieldConfidence(score=0.0, level="MISSING")
        FieldConfidence(score=0.5, level="LOW")
        FieldConfidence(score=1.0, level="HIGH")
        
        # Invalid scores should raise ValidationError
        with pytest.raises(ValidationError):
            FieldConfidence(score=-0.1, level="LOW")
        
        with pytest.raises(ValidationError):
            FieldConfidence(score=1.1, level="HIGH")

    def test_field_confidence_level_validation(self):
        """Test FieldConfidence level validation"""
        # Valid levels
        FieldConfidence(score=0.8, level="HIGH")
        FieldConfidence(score=0.6, level="MEDIUM")
        FieldConfidence(score=0.4, level="LOW")
        FieldConfidence(score=0.0, level="MISSING")
        
        # Invalid levels should raise ValidationError
        with pytest.raises(ValidationError):
            FieldConfidence(score=0.8, level="INVALID")


class TestFieldExtractionResult:
    """Test cases for FieldExtractionResult model"""

    def test_field_extraction_result_valid(self):
        """Test valid FieldExtractionResult creation"""
        result = FieldExtractionResult(
            field_name="employee_name",
            value="John Smith",
            confidence=FieldConfidence(score=0.95, level="HIGH")
        )
        assert result.field_name == "employee_name"
        assert result.value == "John Smith"
        assert result.confidence.score == 0.95
        assert result.confidence.level == "HIGH"

    def test_field_extraction_result_empty_value(self):
        """Test FieldExtractionResult with empty value"""
        result = FieldExtractionResult(
            field_name="employee_id",
            value="",
            confidence=FieldConfidence(score=0.0, level="MISSING")
        )
        assert result.field_name == "employee_id"
        assert result.value == ""
        assert result.confidence.score == 0.0
        assert result.confidence.level == "MISSING"

    def test_field_extraction_result_none_value(self):
        """Test FieldExtractionResult with None value"""
        result = FieldExtractionResult(
            field_name="salary",
            value=None,
            confidence=FieldConfidence(score=0.0, level="MISSING")
        )
        assert result.field_name == "salary"
        assert result.value is None
        assert result.confidence.score == 0.0
        assert result.confidence.level == "MISSING"

    def test_field_extraction_result_validation(self):
        """Test FieldExtractionResult validation"""
        # Valid result
        FieldExtractionResult(
            field_name="test_field",
            value="test_value",
            confidence=FieldConfidence(score=0.8, level="HIGH")
        )
        
        # Invalid field name should raise ValidationError
        with pytest.raises(ValidationError):
            FieldExtractionResult(
                field_name="",  # Empty field name
                value="test_value",
                confidence=FieldConfidence(score=0.8, level="HIGH")
            )


class TestFieldExtractionRequest:
    """Test cases for FieldExtractionRequest model"""

    def test_field_extraction_request_valid(self):
        """Test valid FieldExtractionRequest creation"""
        request = FieldExtractionRequest(
            document_type=DocumentType.EMPLOYMENT_CONTRACT,
            fields=["employee_name", "employee_id", "start_date"],
            text_content="John Smith works at TechCorp with ID 12345 starting 2024-01-15."
        )
        assert request.document_type == DocumentType.EMPLOYMENT_CONTRACT
        assert request.fields == ["employee_name", "employee_id", "start_date"]
        assert request.text_content == "John Smith works at TechCorp with ID 12345 starting 2024-01-15."

    def test_field_extraction_request_empty_fields(self):
        """Test FieldExtractionRequest with empty fields"""
        request = FieldExtractionRequest(
            document_type=DocumentType.INVOICE,
            fields=[],
            text_content="Invoice content here."
        )
        assert request.document_type == DocumentType.INVOICE
        assert request.fields == []
        assert request.text_content == "Invoice content here."

    def test_field_extraction_request_empty_text(self):
        """Test FieldExtractionRequest with empty text content"""
        request = FieldExtractionRequest(
            document_type=DocumentType.RESUME,
            fields=["name", "email"],
            text_content=""
        )
        assert request.document_type == DocumentType.RESUME
        assert request.fields == ["name", "email"]
        assert request.text_content == ""

    def test_field_extraction_request_validation(self):
        """Test FieldExtractionRequest validation"""
        # Valid request
        FieldExtractionRequest(
            document_type=DocumentType.EMPLOYMENT_CONTRACT,
            fields=["employee_name"],
            text_content="Test content"
        )
        
        # Invalid document type should raise ValidationError
        with pytest.raises(ValidationError):
            FieldExtractionRequest(
                document_type="invalid_type",
                fields=["employee_name"],
                text_content="Test content"
            )
        
        # Invalid fields (not a list) should raise ValidationError
        with pytest.raises(ValidationError):
            FieldExtractionRequest(
                document_type=DocumentType.EMPLOYMENT_CONTRACT,
                fields="employee_name",  # Should be a list
                text_content="Test content"
            )


class TestFieldExtractionResponse:
    """Test cases for FieldExtractionResponse model"""

    def test_field_extraction_response_success(self):
        """Test valid FieldExtractionResponse creation with success status"""
        response = FieldExtractionResponse(
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
        assert response.status == FieldExtractionStatus.SUCCESS
        assert len(response.results) == 1
        assert response.overall_confidence == 0.95
        assert response.message == "Extraction completed successfully"

    def test_field_extraction_response_error(self):
        """Test FieldExtractionResponse with error status"""
        response = FieldExtractionResponse(
            status=FieldExtractionStatus.ERROR,
            results=[],
            overall_confidence=0.0,
            message="Failed to extract fields"
        )
        assert response.status == FieldExtractionStatus.ERROR
        assert len(response.results) == 0
        assert response.overall_confidence == 0.0
        assert response.message == "Failed to extract fields"

    def test_field_extraction_response_partial(self):
        """Test FieldExtractionResponse with partial success status"""
        response = FieldExtractionResponse(
            status=FieldExtractionStatus.PARTIAL_SUCCESS,
            results=[
                FieldExtractionResult(
                    field_name="employee_name",
                    value="John Smith",
                    confidence=FieldConfidence(score=0.95, level="HIGH")
                ),
                FieldExtractionResult(
                    field_name="employee_id",
                    value="",
                    confidence=FieldConfidence(score=0.0, level="MISSING")
                )
            ],
            overall_confidence=0.475,
            message="Partial extraction completed"
        )
        assert response.status == FieldExtractionStatus.PARTIAL_SUCCESS
        assert len(response.results) == 2
        assert response.overall_confidence == 0.475
        assert response.message == "Partial extraction completed"

    def test_field_extraction_response_validation(self):
        """Test FieldExtractionResponse validation"""
        # Valid response
        FieldExtractionResponse(
            status=FieldExtractionStatus.SUCCESS,
            results=[],
            overall_confidence=1.0,
            message="Test message"
        )
        
        # Invalid status should raise ValidationError
        with pytest.raises(ValidationError):
            FieldExtractionResponse(
                status="invalid_status",
                results=[],
                overall_confidence=1.0,
                message="Test message"
            )
        
        # Invalid overall confidence should raise ValidationError
        with pytest.raises(ValidationError):
            FieldExtractionResponse(
                status=FieldExtractionStatus.SUCCESS,
                results=[],
                overall_confidence=1.5,  # Should be <= 1.0
                message="Test message"
            )


class TestPIIEntity:
    """Test cases for PIIEntity model"""

    def test_pii_entity_valid(self):
        """Test valid PIIEntity creation"""
        entity = PIIEntity(
            entity_type="PERSON",
            text="John Smith",
            start=0,
            end=10,
            confidence=0.95
        )
        assert entity.entity_type == "PERSON"
        assert entity.text == "John Smith"
        assert entity.start == 0
        assert entity.end == 10
        assert entity.confidence == 0.95

    def test_pii_entity_email(self):
        """Test PIIEntity with email entity"""
        entity = PIIEntity(
            entity_type="EMAIL",
            text="john@example.com",
            start=55,
            end=71,
            confidence=0.98
        )
        assert entity.entity_type == "EMAIL"
        assert entity.text == "john@example.com"
        assert entity.start == 55
        assert entity.end == 71
        assert entity.confidence == 0.98

    def test_pii_entity_phone(self):
        """Test PIIEntity with phone number entity"""
        entity = PIIEntity(
            entity_type="PHONE_NUMBER",
            text="(555) 123-4567",
            start=83,
            end=97,
            confidence=0.92
        )
        assert entity.entity_type == "PHONE_NUMBER"
        assert entity.text == "(555) 123-4567"
        assert entity.start == 83
        assert entity.end == 97
        assert entity.confidence == 0.92

    def test_pii_entity_validation(self):
        """Test PIIEntity validation"""
        # Valid entity
        PIIEntity(
            entity_type="PERSON",
            text="John Smith",
            start=0,
            end=10,
            confidence=0.95
        )
        
        # Invalid entity type should raise ValidationError
        with pytest.raises(ValidationError):
            PIIEntity(
                entity_type="",  # Empty entity type
                text="John Smith",
                start=0,
                end=10,
                confidence=0.95
            )
        
        # Invalid text should raise ValidationError
        with pytest.raises(ValidationError):
            PIIEntity(
                entity_type="PERSON",
                text="",  # Empty text
                start=0,
                end=10,
                confidence=0.95
            )
        
        # Invalid confidence should raise ValidationError
        with pytest.raises(ValidationError):
            PIIEntity(
                entity_type="PERSON",
                text="John Smith",
                start=0,
                end=10,
                confidence=1.5  # Should be <= 1.0
            )


class TestPIIExtractionRequest:
    """Test cases for PIIExtractionRequest model"""

    def test_pii_extraction_request_valid(self):
        """Test valid PIIExtractionRequest creation"""
        request = PIIExtractionRequest(
            text_content="John Smith lives at 123 Main St, Anytown, CA 90210. His email is john@example.com",
            entities=["PERSON", "EMAIL", "ADDRESS"],
            confidence_threshold=0.5
        )
        assert request.text_content == "John Smith lives at 123 Main St, Anytown, CA 90210. His email is john@example.com"
        assert request.entities == ["PERSON", "EMAIL", "ADDRESS"]
        assert request.confidence_threshold == 0.5

    def test_pii_extraction_request_default_confidence(self):
        """Test PIIExtractionRequest with default confidence threshold"""
        request = PIIExtractionRequest(
            text_content="Test content",
            entities=["PERSON", "EMAIL"]
        )
        assert request.text_content == "Test content"
        assert request.entities == ["PERSON", "EMAIL"]
        assert request.confidence_threshold == 0.5  # Default value

    def test_pii_extraction_request_empty_entities(self):
        """Test PIIExtractionRequest with empty entities list"""
        request = PIIExtractionRequest(
            text_content="Test content",
            entities=[],
            confidence_threshold=0.8
        )
        assert request.text_content == "Test content"
        assert request.entities == []
        assert request.confidence_threshold == 0.8

    def test_pii_extraction_request_validation(self):
        """Test PIIExtractionRequest validation"""
        # Valid request
        PIIExtractionRequest(
            text_content="Test content",
            entities=["PERSON"],
            confidence_threshold=0.5
        )
        
        # Invalid confidence threshold should raise ValidationError
        with pytest.raises(ValidationError):
            PIIExtractionRequest(
                text_content="Test content",
                entities=["PERSON"],
                confidence_threshold=1.5  # Should be <= 1.0
            )


class TestPIIExtractionResult:
    """Test cases for PIIExtractionResult model"""

    def test_pii_extraction_result_valid(self):
        """Test valid PIIExtractionResult creation"""
        result = PIIExtractionResult(
            entities=[
                PIIEntity(
                    entity_type="PERSON",
                    text="John Smith",
                    start=0,
                    end=10,
                    confidence=0.95
                )
            ],
            anonymized_text="REDACTED_PERSON lives at 123 Main St, Anytown, CA 90210. His email is john@example.com",
            anonymization_map={"John Smith": "REDACTED_PERSON"}
        )
        assert len(result.entities) == 1
        assert result.entities[0].entity_type == "PERSON"
        assert result.entities[0].text == "John Smith"
        assert result.anonymized_text == "REDACTED_PERSON lives at 123 Main St, Anytown, CA 90210. His email is john@example.com"
        assert result.anonymization_map == {"John Smith": "REDACTED_PERSON"}

    def test_pii_extraction_result_multiple_entities(self):
        """Test PIIExtractionResult with multiple entities"""
        result = PIIExtractionResult(
            entities=[
                PIIEntity(
                    entity_type="PERSON",
                    text="John Smith",
                    start=0,
                    end=10,
                    confidence=0.95
                ),
                PIIEntity(
                    entity_type="EMAIL",
                    text="john@example.com",
                    start=55,
                    end=71,
                    confidence=0.98
                )
            ],
            anonymized_text="REDACTED_PERSON lives at 123 Main St, Anytown, CA 90210. His email is REDACTED_EMAIL",
            anonymization_map={
                "John Smith": "REDACTED_PERSON",
                "john@example.com": "REDACTED_EMAIL"
            }
        )
        assert len(result.entities) == 2
        assert result.anonymized_text == "REDACTED_PERSON lives at 123 Main St, Anytown, CA 90210. His email is REDACTED_EMAIL"
        assert len(result.anonymization_map) == 2

    def test_pii_extraction_result_empty(self):
        """Test PIIExtractionResult with no entities"""
        result = PIIExtractionResult(
            entities=[],
            anonymized_text="No PII found in this text.",
            anonymization_map={}
        )
        assert len(result.entities) == 0
        assert result.anonymized_text == "No PII found in this text."
        assert result.anonymization_map == {}

    def test_pii_extraction_result_validation(self):
        """Test PIIExtractionResult validation"""
        # Valid result
        PIIExtractionResult(
            entities=[],
            anonymized_text="Test text",
            anonymization_map={}
        )
        
        # Invalid anonymization map (not a dict) should raise ValidationError
        with pytest.raises(ValidationError):
            PIIExtractionResult(
                entities=[],
                anonymized_text="Test text",
                anonymization_map="invalid"  # Should be a dict
            )


class TestPIIExtractionResponse:
    """Test cases for PIIExtractionResponse model"""

    def test_pii_extraction_response_success(self):
        """Test valid PIIExtractionResponse creation with success status"""
        response = PIIExtractionResponse(
            status="success",
            result=PIIExtractionResult(
                entities=[
                    PIIEntity(
                        entity_type="PERSON",
                        text="John Smith",
                        start=0,
                        end=10,
                        confidence=0.95
                    )
                ],
                anonymized_text="REDACTED_PERSON lives at 123 Main St",
                anonymization_map={"John Smith": "REDACTED_PERSON"}
            ),
            message="PII extraction completed successfully"
        )
        assert response.status == "success"
        assert len(response.result.entities) == 1
        assert response.result.anonymized_text == "REDACTED_PERSON lives at 123 Main St"
        assert response.message == "PII extraction completed successfully"

    def test_pii_extraction_response_error(self):
        """Test PIIExtractionResponse with error status"""
        response = PIIExtractionResponse(
            status="error",
            result=None,
            message="Failed to extract PII"
        )
        assert response.status == "error"
        assert response.result is None
        assert response.message == "Failed to extract PII"

    def test_pii_extraction_response_validation(self):
        """Test PIIExtractionResponse validation"""
        # Valid response
        PIIExtractionResponse(
            status="success",
            result=None,
            message="Test message"
        )
        
        # Invalid status should raise ValidationError
        with pytest.raises(ValidationError):
            PIIExtractionResponse(
                status="",  # Empty status
                result=None,
                message="Test message"
            )


class TestAuditLogEntry:
    """Test cases for AuditLogEntry model"""

    def test_audit_log_entry_valid(self):
        """Test valid AuditLogEntry creation"""
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            endpoint="/analyze",
            method="POST",
            status_code=200,
            request_size=1024,
            response_size=2048,
            processing_time=1.5,
            client_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            request_id="req_12345"
        )
        assert entry.endpoint == "/analyze"
        assert entry.method == "POST"
        assert entry.status_code == 200
        assert entry.request_size == 1024
        assert entry.response_size == 2048
        assert entry.processing_time == 1.5
        assert entry.client_ip == "192.168.1.1"
        assert entry.user_agent == "Mozilla/5.0"
        assert entry.request_id == "req_12345"

    def test_audit_log_entry_optional_fields(self):
        """Test AuditLogEntry with optional fields"""
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            endpoint="/health",
            method="GET",
            status_code=200,
            request_size=None,
            response_size=None,
            processing_time=None,
            client_ip=None,
            user_agent=None,
            request_id=None
        )
        assert entry.endpoint == "/health"
        assert entry.method == "GET"
        assert entry.status_code == 200
        assert entry.request_size is None
        assert entry.response_size is None
        assert entry.processing_time is None
        assert entry.client_ip is None
        assert entry.user_agent is None
        assert entry.request_id is None

    def test_audit_log_entry_validation(self):
        """Test AuditLogEntry validation"""
        # Valid entry
        AuditLogEntry(
            timestamp=datetime.now(),
            endpoint="/test",
            method="POST",
            status_code=200,
            request_size=100,
            response_size=200,
            processing_time=0.5,
            client_ip="127.0.0.1",
            user_agent="Test Agent",
            request_id="test_123"
        )
        
        # Invalid status code should raise ValidationError
        with pytest.raises(ValidationError):
            AuditLogEntry(
                timestamp=datetime.now(),
                endpoint="/test",
                method="POST",
                status_code=999,  # Invalid status code
                request_size=100,
                response_size=200,
                processing_time=0.5,
                client_ip="127.0.0.1",
                user_agent="Test Agent",
                request_id="test_123"
            )


class TestAuditLogResponse:
    """Test cases for AuditLogResponse model"""

    def test_audit_log_response_valid(self):
        """Test valid AuditLogResponse creation"""
        response = AuditLogResponse(
            logs=[
                AuditLogEntry(
                    timestamp=datetime.now(),
                    endpoint="/analyze",
                    method="POST",
                    status_code=200,
                    request_size=1024,
                    response_size=2048,
                    processing_time=1.5,
                    client_ip="192.168.1.1",
                    user_agent="Mozilla/5.0",
                    request_id="req_12345"
                )
            ],
            total=1,
            page=1,
            page_size=10
        )
        assert len(response.logs) == 1
        assert response.total == 1
        assert response.page == 1
        assert response.page_size == 10

    def test_audit_log_response_empty(self):
        """Test AuditLogResponse with empty logs"""
        response = AuditLogResponse(
            logs=[],
            total=0,
            page=1,
            page_size=10
        )
        assert len(response.logs) == 0
        assert response.total == 0
        assert response.page == 1
        assert response.page_size == 10

    def test_audit_log_response_validation(self):
        """Test AuditLogResponse validation"""
        # Valid response
        AuditLogResponse(
            logs=[],
            total=0,
            page=1,
            page_size=10
        )
        
        # Invalid total should raise ValidationError
        with pytest.raises(ValidationError):
            AuditLogResponse(
                logs=[],
                total=-1,  # Should be >= 0
                page=1,
                page_size=10
            )
        
        # Invalid page should raise ValidationError
        with pytest.raises(ValidationError):
            AuditLogResponse(
                logs=[],
                total=0,
                page=0,  # Should be >= 1
                page_size=10
            )