import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.extraction_service import ExtractionService, ExtractionError
from app.models.schemas import (
    DocumentType, FieldExtractionRequest, FieldExtractionResponse, 
    FieldExtractionResult, FieldConfidence, FieldExtractionStatus
)


class TestExtractionService:
    """Test cases for ExtractionService"""

    @pytest.fixture
    def extraction_service(self):
        """Create ExtractionService instance for testing"""
        return ExtractionService()

    @pytest.fixture
    def sample_text_content(self):
        """Sample text content for testing"""
        return """
        EMPLOYEE CONTRACT
        This agreement is made between TechCorp Inc. and John Smith
        Employee ID: 12345
        Start Date: 2024-01-15
        Salary: $75,000 per year
        Department: Engineering
        Manager: Sarah Johnson
        """

    @pytest.fixture
    def sample_field_request(self):
        """Sample field extraction request"""
        return FieldExtractionRequest(
            document_type=DocumentType.EMPLOYMENT_CONTRACT,
            fields=["employee_name", "employee_id", "start_date", "salary", "department"],
            text_content="John Smith works at TechCorp with ID 12345 starting 2024-01-15 earning $75,000 in Engineering."
        )

    @pytest.fixture
    def sample_llm_response(self):
        """Sample LLM response for testing"""
        return {
            "employee_name": "John Smith",
            "employee_id": "12345",
            "start_date": "2024-01-15",
            "salary": "$75,000",
            "department": "Engineering"
        }

    @pytest.fixture
    def sample_llm_response_with_confidence(self):
        """Sample LLM response with confidence scores"""
        return {
            "employee_name": {"value": "John Smith", "confidence": 0.95},
            "employee_id": {"value": "12345", "confidence": 0.90},
            "start_date": {"value": "2024-01-15", "confidence": 0.85},
            "salary": {"value": "$75,000", "confidence": 0.80},
            "department": {"value": "Engineering", "confidence": 0.92}
        }

    @pytest.fixture
    def sample_llm_response_malformed(self):
        """Sample malformed LLM response"""
        return {
            "employee_name": "John Smith",
            "invalid_field": "some value",  # Field not in request
            "salary": "$75,000"
        }

    def test_get_system_prompt_employment_contract(self, extraction_service):
        """Test system prompt generation for employment contract"""
        prompt = extraction_service._get_system_prompt(DocumentType.EMPLOYMENT_CONTRACT)
        
        assert "employment contract" in prompt.lower()
        assert "employee" in prompt.lower()
        assert "contract" in prompt.lower()
        assert "json" in prompt.lower()

    def test_get_system_prompt_invoice(self, extraction_service):
        """Test system prompt generation for invoice"""
        prompt = extraction_service._get_system_prompt(DocumentType.INVOICE)
        
        assert "invoice" in prompt.lower()
        assert "vendor" in prompt.lower()
        assert "amount" in prompt.lower()
        assert "json" in prompt.lower()

    def test_get_system_prompt_unknown(self, extraction_service):
        """Test system prompt generation for unknown document type"""
        prompt = extraction_service._get_system_prompt("UNKNOWN_TYPE")
        
        assert "document" in prompt.lower()
        assert "extract" in prompt.lower()
        assert "json" in prompt.lower()

    def test_get_system_prompt_medical_record(self, extraction_service):
        """Test system prompt generation for medical record"""
        prompt = extraction_service._get_system_prompt(DocumentType.MEDICAL_RECORD)
        
        assert "medical" in prompt.lower()
        assert "patient" in prompt.lower()
        assert "diagnosis" in prompt.lower()
        assert "json" in prompt.lower()

    def test_get_system_prompt_financial_statement(self, extraction_service):
        """Test system prompt generation for financial statement"""
        prompt = extraction_service._get_system_prompt(DocumentType.FINANCIAL_STATEMENT)
        
        assert "financial" in prompt.lower()
        assert "revenue" in prompt.lower()
        assert "profit" in prompt.lower()
        assert "json" in prompt.lower()

    def test_get_system_prompt_legal_contract(self, extraction_service):
        """Test system prompt generation for legal contract"""
        prompt = extraction_service._get_system_prompt(DocumentType.LEGAL_CONTRACT)
        
        assert "legal" in prompt.lower()
        assert "contract" in prompt.lower()
        assert "parties" in prompt.lower()
        assert "json" in prompt.lower()

    def test_get_system_prompt_academic_paper(self, extraction_service):
        """Test system prompt generation for academic paper"""
        prompt = extraction_service._get_system_prompt(DocumentType.ACADEMIC_PAPER)
        
        assert "academic" in prompt.lower()
        assert "paper" in prompt.lower()
        assert "author" in prompt.lower()
        assert "json" in prompt.lower()

    def test_get_system_prompt_resume(self, extraction_service):
        """Test system prompt generation for resume"""
        prompt = extraction_service._get_system_prompt(DocumentType.RESUME)
        
        assert "resume" in prompt.lower()
        assert "candidate" in prompt.lower()
        assert "experience" in prompt.lower()
        assert "json" in prompt.lower()

    def test_get_system_prompt_email(self, extraction_service):
        """Test system prompt generation for email"""
        prompt = extraction_service._get_system_prompt(DocumentType.EMAIL)
        
        assert "email" in prompt.lower()
        assert "sender" in prompt.lower()
        assert "subject" in prompt.lower()
        assert "json" in prompt.lower()

    def test_get_system_prompt_news_article(self, extraction_service):
        """Test system prompt generation for news article"""
        prompt = extraction_service._get_system_prompt(DocumentType.NEWS_ARTICLE)
        
        assert "news" in prompt.lower()
        assert "article" in prompt.lower()
        assert "headline" in prompt.lower()
        assert "json" in prompt.lower()

    def test_get_system_prompt_custom(self, extraction_service):
        """Test system prompt generation for custom document type"""
        prompt = extraction_service._get_system_prompt("CUSTOM_DOCUMENT")
        
        assert "custom_document" in prompt.lower()
        assert "document" in prompt.lower()
        assert "extract" in prompt.lower()
        assert "json" in prompt.lower()

    def test_calculate_confidence_high(self, extraction_service, sample_field_request, sample_llm_response):
        """Test confidence calculation with high confidence values"""
        results = extraction_service._calculate_confidence(
            sample_field_request.fields, 
            sample_llm_response
        )
        
        assert len(results) == 5
        for result in results:
            assert result.confidence.score >= 0.8
            assert result.confidence.level == "HIGH"

    def test_calculate_confidence_medium(self, extraction_service, sample_field_request, sample_llm_response_with_confidence):
        """Test confidence calculation with medium confidence values"""
        results = extraction_service._calculate_confidence(
            sample_field_request.fields, 
            sample_llm_response_with_confidence
        )
        
        assert len(results) == 5
        for result in results:
            assert 0.6 <= result.confidence.score <= 0.9
            assert result.confidence.level in ["MEDIUM", "HIGH"]

    def test_calculate_confidence_low(self, extraction_service, sample_field_request):
        """Test confidence calculation with low confidence values"""
        response = {
            "employee_name": {"value": "John Smith", "confidence": 0.4},
            "employee_id": {"value": "12345", "confidence": 0.3},
            "start_date": {"value": "2024-01-15", "confidence": 0.5},
            "salary": {"value": "$75,000", "confidence": 0.45},
            "department": {"value": "Engineering", "confidence": 0.35}
        }
        
        results = extraction_service._calculate_confidence(
            sample_field_request.fields, 
            response
        )
        
        assert len(results) == 5
        for result in results:
            assert result.confidence.score <= 0.6
            assert result.confidence.level == "LOW"

    def test_calculate_confidence_mixed(self, extraction_service, sample_field_request):
        """Test confidence calculation with mixed confidence values"""
        response = {
            "employee_name": {"value": "John Smith", "confidence": 0.95},
            "employee_id": {"value": "12345", "confidence": 0.4},
            "start_date": {"value": "2024-01-15", "confidence": 0.85},
            "salary": {"value": "$75,000", "confidence": 0.3},
            "department": {"value": "Engineering", "confidence": 0.92}
        }
        
        results = extraction_service._calculate_confidence(
            sample_field_request.fields, 
            response
        )
        
        assert len(results) == 5
        high_confidence = [r for r in results if r.confidence.level == "HIGH"]
        low_confidence = [r for r in results if r.confidence.level == "LOW"]
        
        assert len(high_confidence) == 3  # employee_name, start_date, department
        assert len(low_confidence) == 2   # employee_id, salary

    def test_calculate_confidence_missing_fields(self, extraction_service, sample_field_request):
        """Test confidence calculation with missing fields"""
        response = {
            "employee_name": {"value": "John Smith", "confidence": 0.95},
            "salary": {"value": "$75,000", "confidence": 0.80}
            # Missing employee_id, start_date, department
        }
        
        results = extraction_service._calculate_confidence(
            sample_field_request.fields, 
            response
        )
        
        assert len(results) == 5
        missing_results = [r for r in results if r.confidence.level == "MISSING"]
        assert len(missing_results) == 3

    def test_calculate_confidence_empty_response(self, extraction_service, sample_field_request):
        """Test confidence calculation with empty response"""
        results = extraction_service._calculate_confidence(
            sample_field_request.fields, 
            {}
        )
        
        assert len(results) == 5
        for result in results:
            assert result.confidence.level == "MISSING"
            assert result.confidence.score == 0.0

    def test_calculate_confidence_no_confidence_scores(self, extraction_service, sample_field_request, sample_llm_response):
        """Test confidence calculation when response has no confidence scores"""
        results = extraction_service._calculate_confidence(
            sample_field_request.fields, 
            sample_llm_response
        )
        
        assert len(results) == 5
        for result in results:
            assert result.confidence.score == 1.0
            assert result.confidence.level == "HIGH"

    def test_calculate_confidence_partial_confidence_scores(self, extraction_service, sample_field_request):
        """Test confidence calculation with partial confidence scores"""
        response = {
            "employee_name": {"value": "John Smith", "confidence": 0.95},
            "employee_id": "12345",  # No confidence score
            "start_date": {"value": "2024-01-15", "confidence": 0.85},
            "salary": "$75,000",    # No confidence score
            "department": {"value": "Engineering", "confidence": 0.92}
        }
        
        results = extraction_service._calculate_confidence(
            sample_field_request.fields, 
            response
        )
        
        assert len(results) == 5
        for result in results:
            if result.field_name in ["employee_name", "start_date", "department"]:
                assert result.confidence.score >= 0.8
            else:
                assert result.confidence.score == 1.0

    def test_parse_llm_response_valid(self, extraction_service, sample_llm_response):
        """Test parsing valid LLM response"""
        response_text = str(sample_llm_response)
        result = extraction_service._parse_llm_response(response_text)
        
        assert result == sample_llm_response

    def test_parse_llm_response_json_string(self, extraction_service, sample_llm_response):
        """Test parsing LLM response as JSON string"""
        import json
        response_text = json.dumps(sample_llm_response)
        result = extraction_service._parse_llm_response(response_text)
        
        assert result == sample_llm_response

    def test_parse_llm_response_malformed(self, extraction_service):
        """Test parsing malformed LLM response"""
        response_text = "This is not JSON"
        result = extraction_service._parse_llm_response(response_text)
        
        assert result == {}

    def test_parse_llm_response_empty(self, extraction_service):
        """Test parsing empty LLM response"""
        response_text = ""
        result = extraction_service._parse_llm_response(response_text)
        
        assert result == {}

    def test_parse_llm_response_none(self, extraction_service):
        """Test parsing None LLM response"""
        response_text = None
        result = extraction_service._parse_llm_response(response_text)
        
        assert result == {}

    def test_parse_llm_response_invalid_json(self, extraction_service):
        """Test parsing invalid JSON LLM response"""
        response_text = '{"invalid": json}'
        result = extraction_service._parse_llm_response(response_text)
        
        assert result == {}

    def test_filter_response_fields_valid(self, extraction_service, sample_field_request, sample_llm_response):
        """Test filtering LLM response to only requested fields"""
        filtered = extraction_service._filter_response_fields(
            sample_llm_response, 
            sample_field_request.fields
        )
        
        assert len(filtered) == 5
        assert set(filtered.keys()) == set(sample_field_request.fields)
        for field in sample_field_request.fields:
            assert field in filtered

    def test_filter_response_fields_extra_fields(self, extraction_service, sample_field_request, sample_llm_response_malformed):
        """Test filtering LLM response with extra fields"""
        filtered = extraction_service._filter_response_fields(
            sample_llm_response_malformed, 
            sample_field_request.fields
        )
        
        assert len(filtered) == 2  # Only employee_name and salary are in requested fields
        assert "employee_name" in filtered
        assert "salary" in filtered
        assert "invalid_field" not in filtered

    def test_filter_response_fields_missing_fields(self, extraction_service, sample_field_request):
        """Test filtering LLM response with missing fields"""
        response = {"employee_name": "John Smith"}
        filtered = extraction_service._filter_response_fields(
            response, 
            sample_field_request.fields
        )
        
        assert len(filtered) == 1
        assert "employee_name" in filtered
        assert set(filtered.keys()) == {"employee_name"}

    def test_filter_response_fields_empty(self, extraction_service, sample_field_request):
        """Test filtering empty LLM response"""
        filtered = extraction_service._filter_response_fields(
            {}, 
            sample_field_request.fields
        )
        
        assert filtered == {}

    def test_filter_response_fields_none(self, extraction_service, sample_field_request):
        """Test filtering None LLM response"""
        filtered = extraction_service._filter_response_fields(
            None, 
            sample_field_request.fields
        )
        
        assert filtered == {}

    @patch('app.services.extraction_service.openai.AsyncOpenAI')
    async def test_extract_fields_success(self, mock_openai, extraction_service, sample_field_request, sample_llm_response):
        """Test successful field extraction"""
        # Setup mock
        mock_client = AsyncMock()
        mock_chat = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat = mock_chat
        
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message = Mock()
        mock_completion.choices[0].message.content = str(sample_llm_response)
        mock_chat.completions.create.return_value = mock_completion
        
        # Test
        result = await extraction_service.extract_fields(sample_field_request)
        
        # Assertions
        assert isinstance(result, FieldExtractionResponse)
        assert result.status == FieldExtractionStatus.SUCCESS
        assert len(result.results) == 5
        assert result.overall_confidence >= 0.8
        
        # Verify OpenAI call
        mock_chat.completions.create.assert_called_once()
        call_args = mock_chat.completions.create.call_args
        assert call_args[1]['model'] == "gpt-4"
        assert call_args[1]['max_tokens'] == 1000
        assert call_args[1]['temperature'] == 0.1

    @patch('app.services.extraction_service.openai.AsyncOpenAI')
    async def test_extract_fields_llm_error(self, mock_openai, extraction_service, sample_field_request):
        """Test field extraction with LLM error"""
        # Setup mock
        mock_client = AsyncMock()
        mock_chat = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat = mock_chat
        
        mock_chat.completions.create.side_effect = Exception("LLM Service Error")
        
        # Test and assert
        with pytest.raises(ExtractionError, match="Failed to extract fields from LLM"):
            await extraction_service.extract_fields(sample_field_request)

    @patch('app.services.extraction_service.openai.AsyncOpenAI')
    async def test_extract_fields_empty_text(self, mock_openai, extraction_service):
        """Test field extraction with empty text content"""
        request = FieldExtractionRequest(
            document_type=DocumentType.EMPLOYMENT_CONTRACT,
            fields=["employee_name"],
            text_content=""
        )
        
        # Setup mock
        mock_client = AsyncMock()
        mock_chat = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat = mock_chat
        
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message = Mock()
        mock_completion.choices[0].message.content = "{}"
        mock_chat.completions.create.return_value = mock_completion
        
        # Test
        result = await extraction_service.extract_fields(request)
        
        # Assertions
        assert isinstance(result, FieldExtractionResponse)
        assert result.status == FieldExtractionStatus.SUCCESS
        assert len(result.results) == 1
        assert result.results[0].confidence.level == "MISSING"

    @patch('app.services.extraction_service.openai.AsyncOpenAI')
    async def test_extract_fields_malformed_response(self, mock_openai, extraction_service, sample_field_request):
        """Test field extraction with malformed LLM response"""
        # Setup mock
        mock_client = AsyncMock()
        mock_chat = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat = mock_chat
        
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message = Mock()
        mock_completion.choices[0].message.content = "This is not JSON"
        mock_chat.completions.create.return_value = mock_completion
        
        # Test
        result = await extraction_service.extract_fields(sample_field_request)
        
        # Assertions
        assert isinstance(result, FieldExtractionResponse)
        assert result.status == FieldExtractionStatus.SUCCESS
        assert len(result.results) == 5
        for field_result in result.results:
            assert field_result.confidence.level == "MISSING"

    @patch('app.services.extraction_service.openai.AsyncOpenAI')
    async def test_extract_fields_single_field(self, mock_openai, extraction_service):
        """Test field extraction with single field"""
        request = FieldExtractionRequest(
            document_type=DocumentType.EMPLOYMENT_CONTRACT,
            fields=["employee_name"],
            text_content="John Smith works at TechCorp."
        )
        
        # Setup mock
        mock_client = AsyncMock()
        mock_chat = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat = mock_chat
        
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message = Mock()
        mock_completion.choices[0].message.content = '{"employee_name": "John Smith"}'
        mock_chat.completions.create.return_value = mock_completion
        
        # Test
        result = await extraction_service.extract_fields(request)
        
        # Assertions
        assert isinstance(result, FieldExtractionResponse)
        assert result.status == FieldExtractionStatus.SUCCESS
        assert len(result.results) == 1
        assert result.results[0].field_name == "employee_name"
        assert result.results[0].value == "John Smith"

    @patch('app.services.extraction_service.openai.AsyncOpenAI')
    async def test_extract_fields_custom_model(self, mock_openai, extraction_service, sample_field_request):
        """Test field extraction with custom model"""
        # Setup mock
        mock_client = AsyncMock()
        mock_chat = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat = mock_chat
        
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message = Mock()
        mock_completion.choices[0].message.content = str(sample_llm_response)
        mock_chat.completions.create.return_value = mock_completion
        
        # Test with custom model
        result = await extraction_service.extract_fields(sample_field_request, model="gpt-3.5-turbo")
        
        # Assertions
        assert isinstance(result, FieldExtractionResponse)
        assert result.status == FieldExtractionStatus.SUCCESS
        
        # Verify OpenAI call with custom model
        mock_chat.completions.create.assert_called_once()
        call_args = mock_chat.completions.create.call_args
        assert call_args[1]['model'] == "gpt-3.5-turbo"

    @patch('app.services.extraction_service.openai.AsyncOpenAI')
    async def test_extract_fields_custom_temperature(self, mock_openai, extraction_service, sample_field_request):
        """Test field extraction with custom temperature"""
        # Setup mock
        mock_client = AsyncMock()
        mock_chat = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat = mock_chat
        
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message = Mock()
        mock_completion.choices[0].message.content = str(sample_llm_response)
        mock_chat.completions.create.return_value = mock_completion
        
        # Test with custom temperature
        result = await extraction_service.extract_fields(sample_field_request, temperature=0.5)
        
        # Assertions
        assert isinstance(result, FieldExtractionResponse)
        assert result.status == FieldExtractionStatus.SUCCESS
        
        # Verify OpenAI call with custom temperature
        mock_chat.completions.create.assert_called_once()
        call_args = mock_chat.completions.create.call_args
        assert call_args[1]['temperature'] == 0.5

    def test_calculate_overall_confidence_all_high(self, extraction_service, sample_field_request, sample_llm_response):
        """Test overall confidence calculation with all high confidence fields"""
        results = extraction_service._calculate_confidence(
            sample_field_request.fields, 
            sample_llm_response
        )
        
        overall_confidence = extraction_service._calculate_overall_confidence(results)
        
        assert overall_confidence >= 0.8
        assert overall_confidence <= 1.0

    def test_calculate_overall_confidence_mixed(self, extraction_service, sample_field_request):
        """Test overall confidence calculation with mixed confidence fields"""
        response = {
            "employee_name": {"value": "John Smith", "confidence": 0.95},
            "employee_id": {"value": "12345", "confidence": 0.4},
            "start_date": {"value": "2024-01-15", "confidence": 0.85},
            "salary": {"value": "$75,000", "confidence": 0.3},
            "department": {"value": "Engineering", "confidence": 0.92}
        }
        
        results = extraction_service._calculate_confidence(
            sample_field_request.fields, 
            response
        )
        
        overall_confidence = extraction_service._calculate_overall_confidence(results)
        
        assert overall_confidence >= 0.0
        assert overall_confidence <= 1.0
        # Should be lower due to low confidence fields
        assert overall_confidence < 0.8

    def test_calculate_overall_confidence_all_missing(self, extraction_service, sample_field_request):
        """Test overall confidence calculation with all missing fields"""
        results = extraction_service._calculate_confidence(
            sample_field_request.fields, 
            {}
        )
        
        overall_confidence = extraction_service._calculate_overall_confidence(results)
        
        assert overall_confidence == 0.0

    def test_calculate_overall_confidence_empty_results(self, extraction_service):
        """Test overall confidence calculation with empty results"""
        overall_confidence = extraction_service._calculate_overall_confidence([])
        
        assert overall_confidence == 0.0