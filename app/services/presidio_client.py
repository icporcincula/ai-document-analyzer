# app/services/presidio_client.py
import httpx
import logging
from typing import List, Dict
from app.models.schemas import PIIEntity, AnonymizationResult
from app.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class PresidioClient:
    """Client for interacting with Presidio Analyzer and Anonymizer services"""
    
    def __init__(self):
        self.analyzer_url = settings.presidio_analyzer_url
        self.anonymizer_url = settings.presidio_anonymizer_url
        
        # Entity types to detect
        self.entity_types = [
            "PERSON",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "CREDIT_CARD",
            "IBAN_CODE",
            "IP_ADDRESS",
            "LOCATION",
            "DATE_TIME",
            "NRP",
            "MEDICAL_LICENSE",
            "US_SSN",
            "US_PASSPORT",
            "US_DRIVER_LICENSE",
            "US_BANK_NUMBER",
            "URL",
        ]
    
    async def anonymize(self, text: str, language: str = "en") -> AnonymizationResult:
        """
        Detect and anonymize PII using Presidio services
        
        Args:
            text: Input text to anonymize
            language: Language code (default: en)
            
        Returns:
            AnonymizationResult with anonymized text and detected entities
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Analyze text for PII
                logger.info(f"Analyzing text with Presidio Analyzer at {self.analyzer_url}")
                
                analyze_request = {
                    "text": text,
                    "language": language,
                    "entities": self.entity_types
                }
                
                analyze_response = await client.post(
                    f"{self.analyzer_url}/analyze",
                    json=analyze_request
                )
                analyze_response.raise_for_status()
                analyzer_results = analyze_response.json()
                
                logger.info(f"Found {len(analyzer_results)} PII entities")
                
                # Step 2: Anonymize detected PII
                logger.info(f"Anonymizing text with Presidio Anonymizer at {self.anonymizer_url}")
                
                anonymize_request = {
                    "text": text,
                    "analyzer_results": analyzer_results,
                    "anonymizers": {
                        "DEFAULT": {"type": "replace", "new_value": "<REDACTED>"},
                        "PERSON": {"type": "replace", "new_value": "<PERSON>"},
                        "EMAIL_ADDRESS": {"type": "replace", "new_value": "<EMAIL>"},
                        "PHONE_NUMBER": {"type": "replace", "new_value": "<PHONE>"},
                        "LOCATION": {"type": "replace", "new_value": "<LOCATION>"},
                        "DATE_TIME": {"type": "replace", "new_value": "<DATE>"},
                        "CREDIT_CARD": {"type": "replace", "new_value": "<CREDIT_CARD>"},
                        "US_SSN": {"type": "replace", "new_value": "<SSN>"},
                        "IP_ADDRESS": {"type": "replace", "new_value": "<IP_ADDRESS>"},
                        "URL": {"type": "replace", "new_value": "<URL>"},
                    }
                }
                
                anonymize_response = await client.post(
                    f"{self.anonymizer_url}/anonymize",
                    json=anonymize_request
                )
                anonymize_response.raise_for_status()
                anonymized_result = anonymize_response.json()
                
                # Step 3: Build entity list
                entities_found = [
                    PIIEntity(
                        entity_type=result["entity_type"],
                        text=text[result["start"]:result["end"]],
                        start=result["start"],
                        end=result["end"],
                        score=result["score"]
                    )
                    for result in analyzer_results
                ]
                
                # Step 4: Build anonymization map
                anonymization_map = self._build_anonymization_map(text, analyzer_results)
                
                return AnonymizationResult(
                    original_text=text,
                    anonymized_text=anonymized_result["text"],
                    entities_found=entities_found,
                    anonymization_map=anonymization_map
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error communicating with Presidio services: {str(e)}")
            raise Exception(f"Presidio service error: {str(e)}")
        except Exception as e:
            logger.error(f"Error during anonymization: {str(e)}")
            raise
    
    def _build_anonymization_map(self, text: str, analyzer_results: List[Dict]) -> Dict[str, str]:
        """Build mapping of original values to anonymized placeholders"""
        mapping = {}
        
        for result in analyzer_results:
            original = text[result["start"]:result["end"]]
            anonymized = f"<{result['entity_type']}>"
            mapping[original] = anonymized
        
        return mapping
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of Presidio services"""
        health = {
            "analyzer": False,
            "anonymizer": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Check analyzer
                try:
                    resp = await client.get(f"{self.analyzer_url}/health")
                    health["analyzer"] = resp.status_code == 200
                except:
                    pass
                
                # Check anonymizer
                try:
                    resp = await client.get(f"{self.anonymizer_url}/health")
                    health["anonymizer"] = resp.status_code == 200
                except:
                    pass
        except:
            pass
        
        return health