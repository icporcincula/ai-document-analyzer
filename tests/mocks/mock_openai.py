from typing import Dict, Any, List, Optional, Union
from unittest.mock import Mock, AsyncMock
import json
from app.models.schemas import DocumentType


class MockOpenAIClient:
    """Mock OpenAI client for testing"""
    
    def __init__(self, responses: List[Dict[str, Any]] = None, 
                 should_raise_error: bool = False, error_message: str = "Mock error"):
        """
        Initialize mock OpenAI client
        
        Args:
            responses: List of responses to return in sequence
            should_raise_error: Whether to raise an error on API calls
            error_message: Error message to raise
        """
        self.responses = responses or self._get_default_responses()
        self.should_raise_error = should_raise_error
        self.error_message = error_message
        self.call_count = 0
        self.last_request = None
        self.request_history = []
    
    def _get_default_responses(self) -> List[Dict[str, Any]]:
        """Get default test responses"""
        return [
            {
                "employee_name": "John Smith",
                "employee_id": "12345",
                "start_date": "2024-01-15",
                "salary": "$75,000",
                "department": "Engineering"
            },
            {
                "vendor_name": "Tech Supplies Inc.",
                "invoice_number": "INV-2024-001",
                "invoice_date": "2024-01-10",
                "total_amount": "$1,250.00",
                "due_date": "2024-02-10"
            },
            {
                "patient_name": "Jane Doe",
                "patient_id": "P123456",
                "diagnosis": "Hypertension",
                "prescription": "Lisinopril 10mg",
                "date": "2024-01-15"
            }
        ]
    
    def set_responses(self, responses: List[Dict[str, Any]]):
        """Set custom responses"""
        self.responses = responses
    
    def set_error_behavior(self, should_raise_error: bool, error_message: str = "Mock error"):
        """Set error behavior"""
        self.should_raise_error = should_raise_error
        self.error_message = error_message
    
    def set_default_responses(self):
        """Reset to default responses"""
        self.responses = self._get_default_responses()
    
    def create_chat_completion(self, model: str, messages: List[Dict[str, str]], 
                              max_tokens: int = 1000, temperature: float = 0.1, 
                              **kwargs) -> Dict[str, Any]:
        """
        Mock chat completion method
        
        Args:
            model: Model name
            messages: List of messages
            max_tokens: Maximum tokens
            temperature: Temperature setting
            **kwargs: Additional arguments
            
        Returns:
            Mock completion response
        """
        if self.should_raise_error:
            raise Exception(self.error_message)
        
        self.call_count += 1
        
        # Store request details
        request_details = {
            'model': model,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'kwargs': kwargs
        }
        self.last_request = request_details
        self.request_history.append(request_details)
        
        # Return response based on call count
        response_index = (self.call_count - 1) % len(self.responses)
        response_data = self.responses[response_index]
        
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(response_data)
                    }
                }
            ]
        }
    
    def reset(self):
        """Reset mock state"""
        self.call_count = 0
        self.last_request = None
        self.request_history = []
        self.should_raise_error = False
        self.error_message = "Mock error"
        self.responses = self._get_default_responses()


class MockOpenAIChat:
    """Mock OpenAI chat interface"""
    
    def __init__(self, client: MockOpenAIClient):
        """
        Initialize mock chat interface
        
        Args:
            client: Mock OpenAI client
        """
        self.client = client
        self.completions = MockOpenAICompletions(client)


class MockOpenAICompletions:
    """Mock OpenAI completions interface"""
    
    def __init__(self, client: MockOpenAIClient):
        """
        Initialize mock completions interface
        
        Args:
            client: Mock OpenAI client
        """
        self.client = client
    
    def create(self, **kwargs) -> Dict[str, Any]:
        """
        Mock completions create method
        
        Args:
            **kwargs: Arguments for completion creation
            
        Returns:
            Mock completion response
        """
        return self.client.create_chat_completion(**kwargs)


class MockAsyncOpenAIClient:
    """Mock async OpenAI client for testing"""
    
    def __init__(self, responses: List[Dict[str, Any]] = None, 
                 should_raise_error: bool = False, error_message: str = "Mock error"):
        """
        Initialize mock async OpenAI client
        
        Args:
            responses: List of responses to return in sequence
            should_raise_error: Whether to raise an error on API calls
            error_message: Error message to raise
        """
        self.client = MockOpenAIClient(responses, should_raise_error, error_message)
    
    async def create_chat_completion(self, model: str, messages: List[Dict[str, str]], 
                                   max_tokens: int = 1000, temperature: float = 0.1, 
                                   **kwargs) -> Dict[str, Any]:
        """
        Mock async chat completion method
        
        Args:
            model: Model name
            messages: List of messages
            max_tokens: Maximum tokens
            temperature: Temperature setting
            **kwargs: Additional arguments
            
        Returns:
            Mock completion response
        """
        # Simulate async behavior
        import asyncio
        await asyncio.sleep(0.001)  # Small delay to simulate async
        
        return self.client.create_chat_completion(
            model=model, 
            messages=messages, 
            max_tokens=max_tokens, 
            temperature=temperature, 
            **kwargs
        )
    
    def reset(self):
        """Reset mock state"""
        self.client.reset()


class MockAsyncOpenAIChat:
    """Mock async OpenAI chat interface"""
    
    def __init__(self, client: MockAsyncOpenAIClient):
        """
        Initialize mock async chat interface
        
        Args:
            client: Mock async OpenAI client
        """
        self.client = client
        self.completions = MockAsyncOpenAICompletions(client)


class MockAsyncOpenAICompletions:
    """Mock async OpenAI completions interface"""
    
    def __init__(self, client: MockAsyncOpenAIClient):
        """
        Initialize mock async completions interface
        
        Args:
            client: Mock async OpenAI client
        """
        self.client = client
    
    async def create(self, **kwargs) -> Dict[str, Any]:
        """
        Mock async completions create method
        
        Args:
            **kwargs: Arguments for completion creation
            
        Returns:
            Mock completion response
        """
        return await self.client.create_chat_completion(**kwargs)


def create_mock_openai_client(responses: List[Dict[str, Any]] = None, 
                             should_raise_error: bool = False, 
                             error_message: str = "Mock error") -> MockOpenAIClient:
    """
    Factory function to create a mock OpenAI client
    
    Args:
        responses: List of responses to return
        should_raise_error: Whether to raise errors
        error_message: Error message to use
        
    Returns:
        Configured mock OpenAI client
    """
    return MockOpenAIClient(responses, should_raise_error, error_message)


def create_mock_async_openai_client(responses: List[Dict[str, Any]] = None, 
                                   should_raise_error: bool = False, 
                                   error_message: str = "Mock error") -> MockAsyncOpenAIClient:
    """
    Factory function to create a mock async OpenAI client
    
    Args:
        responses: List of responses to return
        should_raise_error: Whether to raise errors
        error_message: Error message to use
        
    Returns:
        Configured mock async OpenAI client
    """
    return MockAsyncOpenAIClient(responses, should_raise_error, error_message)


# Common test scenarios
class OpenAITestScenarios:
    """Common test scenarios for OpenAI mocking"""
    
    @staticmethod
    def employment_contract_response() -> List[Dict[str, Any]]:
        """Return employment contract extraction response"""
        return [
            {
                "employee_name": "John Smith",
                "employee_id": "12345",
                "start_date": "2024-01-15",
                "salary": "$75,000",
                "department": "Engineering"
            }
        ]
    
    @staticmethod
    def invoice_response() -> List[Dict[str, Any]]:
        """Return invoice extraction response"""
        return [
            {
                "vendor_name": "Tech Supplies Inc.",
                "invoice_number": "INV-2024-001",
                "invoice_date": "2024-01-10",
                "total_amount": "$1,250.00",
                "due_date": "2024-02-10"
            }
        ]
    
    @staticmethod
    def medical_record_response() -> List[Dict[str, Any]]:
        """Return medical record extraction response"""
        return [
            {
                "patient_name": "Jane Doe",
                "patient_id": "P123456",
                "diagnosis": "Hypertension",
                "prescription": "Lisinopril 10mg",
                "date": "2024-01-15"
            }
        ]
    
    @staticmethod
    def malformed_response() -> List[Dict[str, Any]]:
        """Return malformed response"""
        return [
            {
                "invalid_field": "some value",
                "another_invalid": "another value"
            }
        ]
    
    @staticmethod
    def empty_response() -> List[Dict[str, Any]]:
        """Return empty response"""
        return [{}]
    
    @staticmethod
    def multiple_responses() -> List[Dict[str, Any]]:
        """Return multiple responses for sequential calls"""
        return [
            {
                "employee_name": "John Smith",
                "employee_id": "12345"
            },
            {
                "vendor_name": "Tech Supplies Inc.",
                "invoice_number": "INV-2024-001"
            },
            {
                "patient_name": "Jane Doe",
                "patient_id": "P123456"
            }
        ]
    
    @staticmethod
    def response_with_confidence() -> List[Dict[str, Any]]:
        """Return response with confidence scores"""
        return [
            {
                "employee_name": {"value": "John Smith", "confidence": 0.95},
                "employee_id": {"value": "12345", "confidence": 0.90},
                "start_date": {"value": "2024-01-15", "confidence": 0.85}
            }
        ]


class MockExtractionService:
    """Mock extraction service for testing"""
    
    def __init__(self, responses: List[Dict[str, Any]] = None, 
                 should_raise_error: bool = False, error_message: str = "Mock error"):
        """
        Initialize mock extraction service
        
        Args:
            responses: List of responses to return
            should_raise_error: Whether to raise errors
            error_message: Error message to use
        """
        self.openai_client = create_mock_async_openai_client(responses, should_raise_error, error_message)
        self.call_count = 0
        self.last_request = None
    
    async def extract_fields(self, request, model: str = "gpt-4", temperature: float = 0.1):
        """
        Mock extract_fields method
        
        Args:
            request: Field extraction request
            model: Model to use
            temperature: Temperature setting
            
        Returns:
            Mock extraction response
        """
        from app.models.schemas import FieldExtractionResponse, FieldExtractionStatus, FieldExtractionResult, FieldConfidence
        
        if self.openai_client.client.should_raise_error:
            from app.services.extraction_service import ExtractionError
            raise ExtractionError(self.openai_client.client.error_message)
        
        self.call_count += 1
        self.last_request = request
        
        # Get mock response
        mock_response = await self.openai_client.create_chat_completion(
            model=model,
            messages=[{"role": "user", "content": request.text_content}],
            max_tokens=1000,
            temperature=temperature
        )
        
        # Parse response
        import json
        try:
            extracted_data = json.loads(mock_response["choices"][0]["message"]["content"])
        except:
            extracted_data = {}
        
        # Create field results
        results = []
        for field_name in request.fields:
            if field_name in extracted_data:
                value = extracted_data[field_name]
                confidence = FieldConfidence(score=0.9, level="HIGH")
            else:
                value = ""
                confidence = FieldConfidence(score=0.0, level="MISSING")
            
            results.append(FieldExtractionResult(
                field_name=field_name,
                value=value,
                confidence=confidence
            ))
        
        # Calculate overall confidence
        total_confidence = sum(result.confidence.score for result in results)
        overall_confidence = total_confidence / len(results) if results else 0.0
        
        return FieldExtractionResponse(
            status=FieldExtractionStatus.SUCCESS,
            results=results,
            overall_confidence=overall_confidence,
            message="Mock extraction completed successfully"
        )
    
    def reset(self):
        """Reset mock state"""
        self.openai_client.reset()
        self.call_count = 0
        self.last_request = None