import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.presidio_client import PresidioClient, PresidioError
from app.models.schemas import PIIEntity, PIIExtractionResult


class TestPresidioClient:
    """Test cases for PresidioClient"""

    @pytest.fixture
    def presidio_client(self):
        """Create PresidioClient instance for testing"""
        return PresidioClient()

    @pytest.fixture
    def sample_text(self):
        """Sample text with PII for testing"""
        return "John Smith lives at 123 Main St, Anytown, CA 90210. His email is john@example.com and phone is (555) 123-4567."

    @pytest.fixture
    def sample_pii_entities(self):
        """Sample PII entities for testing"""
        return [
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
            ),
            PIIEntity(
                entity_type="PHONE_NUMBER",
                text="(555) 123-4567",
                start=83,
                end=97,
                confidence=0.92
            )
        ]

    @pytest.fixture
    def mock_analyzer_response(self):
        """Mock analyzer response for testing"""
        return [
            {
                "entity_type": "PERSON",
                "text": "John Smith",
                "start": 0,
                "end": 10,
                "score": 0.95
            },
            {
                "entity_type": "EMAIL",
                "text": "john@example.com",
                "start": 55,
                "end": 71,
                "score": 0.98
            }
        ]

    @pytest.fixture
    def mock_anonymizer_response(self):
        """Mock anonymizer response for testing"""
        return {
            "text": "REDACTED_PERSON lives at 123 Main St, Anytown, CA 90210. His email is REDACTED_EMAIL and phone is (555) 123-4567.",
            "items": [
                {
                    "text": "John Smith",
                    "start": 0,
                    "end": 10,
                    "operator": "redact"
                },
                {
                    "text": "john@example.com",
                    "start": 55,
                    "end": 71,
                    "operator": "redact"
                }
            ]
        }

    @patch('app.services.presidio_client.httpx.AsyncClient.post')
    async def test_analyze_text_success(self, mock_post, presidio_client, sample_text, mock_analyzer_response):
        """Test successful PII analysis"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_analyzer_response
        mock_post.return_value = mock_response
        
        # Test
        result = await presidio_client.analyze_text(sample_text)
        
        # Assertions
        assert len(result) == 2
        assert result[0].entity_type == "PERSON"
        assert result[0].text == "John Smith"
        assert result[0].confidence == 0.95
        assert result[1].entity_type == "EMAIL"
        assert result[1].text == "john@example.com"
        assert result[1].confidence == 0.98
        
        mock_post.assert_called_once_with(
            f"{presidio_client.analyzer_url}/analyze",
            json={
                "text": sample_text,
                "language": "en",
                "entities": presidio_client.supported_entities,
                "score_threshold": presidio_client.min_confidence
            },
            timeout=30.0
        )

    @patch('app.services.presidio_client.httpx.AsyncClient.post')
    async def test_analyze_text_empty_response(self, mock_post, presidio_client, sample_text):
        """Test PII analysis with empty response"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_post.return_value = mock_response
        
        # Test
        result = await presidio_client.analyze_text(sample_text)
        
        # Assertions
        assert result == []
        mock_post.assert_called_once()

    @patch('app.services.presidio_client.httpx.AsyncClient.post')
    async def test_analyze_text_http_error(self, mock_post, presidio_client, sample_text):
        """Test PII analysis with HTTP error"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        # Test and assert
        with pytest.raises(PresidioError, match="Presidio analyzer service error"):
            await presidio_client.analyze_text(sample_text)

    @patch('app.services.presidio_client.httpx.AsyncClient.post')
    async def test_analyze_text_network_error(self, mock_post, presidio_client, sample_text):
        """Test PII analysis with network error"""
        # Setup mock
        mock_post.side_effect = Exception("Connection failed")
        
        # Test and assert
        with pytest.raises(PresidioError, match="Failed to connect to Presidio analyzer"):
            await presidio_client.analyze_text(sample_text)

    @patch('app.services.presidio_client.httpx.AsyncClient.post')
    async def test_anonymize_text_success(self, mock_post, presidio_client, sample_text, mock_anonymizer_response):
        """Test successful text anonymization"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_anonymizer_response
        mock_post.return_value = mock_response
        
        # Test
        result_text, anonymization_map = await presidio_client.anonymize_text(sample_text)
        
        # Assertions
        assert result_text == mock_anonymizer_response["text"]
        assert len(anonymization_map) == 2
        assert anonymization_map["John Smith"] == "REDACTED_PERSON"
        assert anonymization_map["john@example.com"] == "REDACTED_EMAIL"
        
        mock_post.assert_called_once_with(
            f"{presidio_client.anonymizer_url}/anonymize",
            json={
                "text": sample_text,
                "anonymizers": {
                    "DEFAULT": {"type": "redact"}
                }
            },
            timeout=30.0
        )

    @patch('app.services.presidio_client.httpx.AsyncClient.post')
    async def test_anonymize_text_http_error(self, mock_post, presidio_client, sample_text):
        """Test text anonymization with HTTP error"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        # Test and assert
        with pytest.raises(PresidioError, match="Presidio anonymizer service error"):
            await presidio_client.anonymize_text(sample_text)

    @patch('app.services.presidio_client.httpx.AsyncClient.post')
    async def test_anonymize_text_network_error(self, mock_post, presidio_client, sample_text):
        """Test text anonymization with network error"""
        # Setup mock
        mock_post.side_effect = Exception("Connection failed")
        
        # Test and assert
        with pytest.raises(PresidioError, match="Failed to connect to Presidio anonymizer"):
            await presidio_client.anonymize_text(sample_text)

    @patch('app.services.presidio_client.httpx.AsyncClient.get')
    async def test_health_check_success(self, mock_get, presidio_client):
        """Test successful health check"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Healthy"
        mock_get.return_value = mock_response
        
        # Test
        result = await presidio_client.health_check()
        
        # Assertions
        assert result is True
        mock_get.assert_called_once_with(
            f"{presidio_client.analyzer_url}/health",
            timeout=10.0
        )

    @patch('app.services.presidio_client.httpx.AsyncClient.get')
    async def test_health_check_failure(self, mock_get, presidio_client):
        """Test health check failure"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Service Unavailable"
        mock_get.return_value = mock_response
        
        # Test
        result = await presidio_client.health_check()
        
        # Assertions
        assert result is False
        mock_get.assert_called_once()

    @patch('app.services.presidio_client.httpx.AsyncClient.get')
    async def test_health_check_network_error(self, mock_get, presidio_client):
        """Test health check with network error"""
        # Setup mock
        mock_get.side_effect = Exception("Connection failed")
        
        # Test
        result = await presidio_client.health_check()
        
        # Assertions
        assert result is False
        mock_get.assert_called_once()

    def test_create_anonymization_map(self, presidio_client, sample_pii_entities):
        """Test creation of anonymization map"""
        # Test
        result = presidio_client._create_anonymization_map(sample_pii_entities)
        
        # Assertions
        assert len(result) == 3
        assert result["John Smith"] == "REDACTED_PERSON"
        assert result["john@example.com"] == "REDACTED_EMAIL"
        assert result["(555) 123-4567"] == "REDACTED_PHONE_NUMBER"

    def test_create_anonymization_map_empty(self, presidio_client):
        """Test creation of anonymization map with empty entities"""
        # Test
        result = presidio_client._create_anonymization_map([])
        
        # Assertions
        assert result == {}

    def test_create_anonymization_map_duplicate_entities(self, presidio_client):
        """Test creation of anonymization map with duplicate entities"""
        entities = [
            PIIEntity(
                entity_type="PERSON",
                text="John Smith",
                start=0,
                end=10,
                confidence=0.95
            ),
            PIIEntity(
                entity_type="PERSON",
                text="John Smith",
                start=50,
                end=60,
                confidence=0.90
            )
        ]
        
        # Test
        result = presidio_client._create_anonymization_map(entities)
        
        # Assertions
        assert len(result) == 1
        assert result["John Smith"] == "REDACTED_PERSON"

    def test_get_entity_type_mapping(self, presidio_client):
        """Test entity type to anonymization mapping"""
        # Test various entity types
        assert presidio_client._get_entity_type_mapping("PERSON") == "REDACTED_PERSON"
        assert presidio_client._get_entity_type_mapping("EMAIL") == "REDACTED_EMAIL"
        assert presidio_client._get_entity_type_mapping("PHONE_NUMBER") == "REDACTED_PHONE_NUMBER"
        assert presidio_client._get_entity_type_mapping("ADDRESS") == "REDACTED_ADDRESS"
        assert presidio_client._get_entity_type_mapping("UNKNOWN") == "REDACTED"

    def test_get_entity_type_mapping_case_insensitive(self, presidio_client):
        """Test entity type mapping is case insensitive"""
        # Test case insensitive mapping
        assert presidio_client._get_entity_type_mapping("person") == "REDACTED_PERSON"
        assert presidio_client._get_entity_type_mapping("EMAIL") == "REDACTED_EMAIL"
        assert presidio_client._get_entity_type_mapping("Phone_Number") == "REDACTED_PHONE_NUMBER"

    def test_supported_entities_property(self, presidio_client):
        """Test supported entities property"""
        # Test
        entities = presidio_client.supported_entities
        
        # Assertions
        assert "PERSON" in entities
        assert "EMAIL" in entities
        assert "PHONE_NUMBER" in entities
        assert "ADDRESS" in entities
        assert "CREDIT_CARD" in entities

    def test_min_confidence_property(self, presidio_client):
        """Test minimum confidence property"""
        # Test
        confidence = presidio_client.min_confidence
        
        # Assertions
        assert confidence == 0.5

    @patch('app.services.presidio_client.httpx.AsyncClient.post')
    async def test_analyze_text_with_custom_entities(self, mock_post, presidio_client, sample_text):
        """Test PII analysis with custom entities"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_post.return_value = mock_response
        
        # Test with custom entities
        custom_entities = ["PERSON", "EMAIL"]
        result = await presidio_client.analyze_text(sample_text, entities=custom_entities)
        
        # Assertions
        mock_post.assert_called_once_with(
            f"{presidio_client.analyzer_url}/analyze",
            json={
                "text": sample_text,
                "language": "en",
                "entities": custom_entities,
                "score_threshold": presidio_client.min_confidence
            },
            timeout=30.0
        )

    @patch('app.services.presidio_client.httpx.AsyncClient.post')
    async def test_analyze_text_with_custom_confidence(self, mock_post, presidio_client, sample_text):
        """Test PII analysis with custom confidence threshold"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_post.return_value = mock_response
        
        # Test with custom confidence
        custom_confidence = 0.8
        result = await presidio_client.analyze_text(sample_text, confidence_threshold=custom_confidence)
        
        # Assertions
        mock_post.assert_called_once_with(
            f"{presidio_client.analyzer_url}/analyze",
            json={
                "text": sample_text,
                "language": "en",
                "entities": presidio_client.supported_entities,
                "score_threshold": custom_confidence
            },
            timeout=30.0
        )

    @patch('app.services.presidio_client.httpx.AsyncClient.post')
    async def test_anonymize_text_with_custom_anonymizers(self, mock_post, presidio_client, sample_text):
        """Test text anonymization with custom anonymizers"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "text": "ANONYMIZED_PERSON lives at 123 Main St, Anytown, CA 90210. His email is ANONYMIZED_EMAIL and phone is (555) 123-4567.",
            "items": []
        }
        mock_post.return_value = mock_response
        
        # Test with custom anonymizers
        custom_anonymizers = {
            "PERSON": {"type": "replace", "new_value": "ANONYMIZED_PERSON"},
            "EMAIL": {"type": "replace", "new_value": "ANONYMIZED_EMAIL"}
        }
        result_text, anonymization_map = await presidio_client.anonymize_text(sample_text, anonymizers=custom_anonymizers)
        
        # Assertions
        assert "ANONYMIZED_PERSON" in result_text
        assert "ANONYMIZED_EMAIL" in result_text
        mock_post.assert_called_once_with(
            f"{presidio_client.anonymizer_url}/anonymize",
            json={
                "text": sample_text,
                "anonymizers": custom_anonymizers
            },
            timeout=30.0
        )

    def test_entity_type_mapping_special_characters(self, presidio_client):
        """Test entity type mapping with special characters"""
        # Test with entity types containing special characters
        assert presidio_client._get_entity_type_mapping("CREDIT_CARD") == "REDACTED_CREDIT_CARD"
        assert presidio_client._get_entity_type_mapping("US_SSN") == "REDACTED_US_SSN"
        assert presidio_client._get_entity_type_mapping("IP_ADDRESS") == "REDACTED_IP_ADDRESS"

    def test_entity_type_mapping_empty_string(self, presidio_client):
        """Test entity type mapping with empty string"""
        # Test with empty string
        result = presidio_client._get_entity_type_mapping("")
        assert result == "REDACTED"

    def test_entity_type_mapping_none(self, presidio_client):
        """Test entity type mapping with None"""
        # Test with None
        result = presidio_client._get_entity_type_mapping(None)
        assert result == "REDACTED"