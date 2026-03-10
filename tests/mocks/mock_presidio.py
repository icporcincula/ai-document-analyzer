from typing import List, Optional, Dict, Any
from unittest.mock import Mock, AsyncMock
from app.models.schemas import PIIEntity


class MockPresidioAnalyzer:
    """Mock Presidio analyzer service for testing"""
    
    def __init__(self, entities: List[Dict[str, Any]] = None, confidence_threshold: float = 0.5):
        """
        Initialize mock analyzer
        
        Args:
            entities: List of entities to return, if None returns default test entities
            confidence_threshold: Minimum confidence threshold for filtering
        """
        self.entities = entities or self._get_default_entities()
        self.confidence_threshold = confidence_threshold
        self.call_count = 0
        self.last_request = None
    
    def _get_default_entities(self) -> List[Dict[str, Any]]:
        """Get default test entities"""
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
            },
            {
                "entity_type": "PHONE_NUMBER",
                "text": "(555) 123-4567",
                "start": 83,
                "end": 97,
                "score": 0.92
            },
            {
                "entity_type": "ADDRESS",
                "text": "123 Main St, Anytown, CA 90210",
                "start": 25,
                "end": 54,
                "score": 0.88
            }
        ]
    
    def set_entities(self, entities: List[Dict[str, Any]]):
        """Set custom entities to return"""
        self.entities = entities
    
    def set_confidence_threshold(self, threshold: float):
        """Set confidence threshold"""
        self.confidence_threshold = threshold
    
    def analyze(self, text: str, entities: List[str] = None, language: str = "en", 
                score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Mock analyze method that returns predefined entities
        
        Args:
            text: Text to analyze
            entities: List of entity types to detect (if None, use all)
            language: Language of the text
            score_threshold: Minimum confidence score
            
        Returns:
            List of detected entities
        """
        self.call_count += 1
        self.last_request = {
            'text': text,
            'entities': entities,
            'language': language,
            'score_threshold': score_threshold
        }
        
        # Filter entities by requested types if specified
        if entities:
            filtered_entities = [
                entity for entity in self.entities 
                if entity['entity_type'] in entities
            ]
        else:
            filtered_entities = self.entities.copy()
        
        # Filter by confidence threshold
        filtered_entities = [
            entity for entity in filtered_entities 
            if entity['score'] >= max(score_threshold, self.confidence_threshold)
        ]
        
        return filtered_entities
    
    def reset(self):
        """Reset mock state"""
        self.call_count = 0
        self.last_request = None
        self.entities = self._get_default_entities()
        self.confidence_threshold = 0.5


class MockPresidioAnonymizer:
    """Mock Presidio anonymizer service for testing"""
    
    def __init__(self, anonymization_map: Dict[str, str] = None):
        """
        Initialize mock anonymizer
        
        Args:
            anonymization_map: Custom anonymization map, if None uses default
        """
        self.anonymization_map = anonymization_map or self._get_default_map()
        self.call_count = 0
        self.last_request = None
        self.anonymizers = None
    
    def _get_default_map(self) -> Dict[str, str]:
        """Get default anonymization map"""
        return {
            "John Smith": "REDACTED_PERSON",
            "john@example.com": "REDACTED_EMAIL", 
            "(555) 123-4567": "REDACTED_PHONE_NUMBER",
            "123 Main St, Anytown, CA 90210": "REDACTED_ADDRESS"
        }
    
    def set_anonymization_map(self, anonymization_map: Dict[str, str]):
        """Set custom anonymization map"""
        self.anonymization_map = anonymization_map
    
    def anonymize(self, text: str, anonymizers: Dict[str, Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Mock anonymize method that replaces entities with anonymized versions
        
        Args:
            text: Text to anonymize
            anonymizers: Custom anonymizers configuration
            
        Returns:
            Dict with anonymized text and anonymization items
        """
        self.call_count += 1
        self.last_request = {
            'text': text,
            'anonymizers': anonymizers
        }
        self.anonymizers = anonymizers
        
        anonymized_text = text
        anonymization_items = []
        
        # Apply anonymization map
        for original, anonymized in self.anonymization_map.items():
            if original in anonymized_text:
                start = anonymized_text.find(original)
                end = start + len(original)
                
                anonymized_text = anonymized_text.replace(original, anonymized)
                
                anonymization_items.append({
                    "text": original,
                    "start": start,
                    "end": end,
                    "operator": "redact"
                })
        
        return {
            "text": anonymized_text,
            "items": anonymization_items
        }
    
    def reset(self):
        """Reset mock state"""
        self.call_count = 0
        self.last_request = None
        self.anonymization_map = self._get_default_map()
        self.anonymizers = None


class MockPresidioClient:
    """Mock Presidio client that combines analyzer and anonymizer"""
    
    def __init__(self, analyzer_entities: List[Dict[str, Any]] = None, 
                 anonymization_map: Dict[str, str] = None):
        """
        Initialize mock client
        
        Args:
            analyzer_entities: Entities for analyzer mock
            anonymization_map: Map for anonymizer mock
        """
        self.analyzer = MockPresidioAnalyzer(analyzer_entities)
        self.anonymizer = MockPresidioAnonymizer(anonymization_map)
        self.health_status = True
    
    def set_analyzer_entities(self, entities: List[Dict[str, Any]]):
        """Set analyzer entities"""
        self.analyzer.set_entities(entities)
    
    def set_anonymization_map(self, anonymization_map: Dict[str, str]):
        """Set anonymization map"""
        self.anonymizer.set_anonymization_map(anonymization_map)
    
    def set_health_status(self, status: bool):
        """Set health check status"""
        self.health_status = status
    
    def reset(self):
        """Reset all mocks"""
        self.analyzer.reset()
        self.anonymizer.reset()
        self.health_status = True


def create_mock_presidio_client(entities: List[Dict[str, Any]] = None, 
                               anonymization_map: Dict[str, str] = None) -> MockPresidioClient:
    """
    Factory function to create a mock Presidio client
    
    Args:
        entities: Entities to return from analyzer
        anonymization_map: Map for anonymizer
        
    Returns:
        Configured mock Presidio client
    """
    return MockPresidioClient(entities, anonymization_map)


def create_mock_presidio_analyzer(entities: List[Dict[str, Any]] = None) -> MockPresidioAnalyzer:
    """
    Factory function to create a mock Presidio analyzer
    
    Args:
        entities: Entities to return
        
    Returns:
        Configured mock Presidio analyzer
    """
    return MockPresidioAnalyzer(entities)


def create_mock_presidio_anonymizer(anonymization_map: Dict[str, str] = None) -> MockPresidioAnonymizer:
    """
    Factory function to create a mock Presidio anonymizer
    
    Args:
        anonymization_map: Map for anonymization
        
    Returns:
        Configured mock Presidio anonymizer
    """
    return MockPresidioAnonymizer(anonymization_map)


# Common test scenarios
class PresidioTestScenarios:
    """Common test scenarios for Presidio mocking"""
    
    @staticmethod
    def no_pii_entities() -> List[Dict[str, Any]]:
        """Return empty entities list"""
        return []
    
    @staticmethod
    def single_person_entity() -> List[Dict[str, Any]]:
        """Return single person entity"""
        return [
            {
                "entity_type": "PERSON",
                "text": "John Smith",
                "start": 0,
                "end": 10,
                "score": 0.95
            }
        ]
    
    @staticmethod
    def multiple_entities() -> List[Dict[str, Any]]:
        """Return multiple entities"""
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
            },
            {
                "entity_type": "PHONE_NUMBER",
                "text": "(555) 123-4567",
                "start": 83,
                "end": 97,
                "score": 0.92
            }
        ]
    
    @staticmethod
    def low_confidence_entities() -> List[Dict[str, Any]]:
        """Return entities with low confidence scores"""
        return [
            {
                "entity_type": "PERSON",
                "text": "John Smith",
                "start": 0,
                "end": 10,
                "score": 0.3
            },
            {
                "entity_type": "EMAIL",
                "text": "john@example.com",
                "start": 55,
                "end": 71,
                "score": 0.4
            }
        ]
    
    @staticmethod
    def default_anonymization_map() -> Dict[str, str]:
        """Return default anonymization map"""
        return {
            "John Smith": "REDACTED_PERSON",
            "john@example.com": "REDACTED_EMAIL",
            "(555) 123-4567": "REDACTED_PHONE_NUMBER",
            "123 Main St": "REDACTED_ADDRESS"
        }
    
    @staticmethod
    def custom_anonymization_map() -> Dict[str, str]:
        """Return custom anonymization map"""
        return {
            "John Smith": "ANONYMIZED_PERSON",
            "john@example.com": "ANONYMIZED_EMAIL"
        }