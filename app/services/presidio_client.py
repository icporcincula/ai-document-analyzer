# app/services/presidio_client.py
import httpx
import logging
from typing import List, Dict, Optional, Any
from app.models.schemas import PIIEntity, AnonymizationResult
from app.utils.config import get_settings
from app.services.custom_entity_service import CustomEntityService

logger = logging.getLogger(__name__)
settings = get_settings()


class PresidioClient:
    """Client for interacting with Presidio Analyzer and Anonymizer services with multi-language and custom entity support"""

    def __init__(self):
        self.analyzer_url = settings.presidio_analyzer_url
        self.anonymizer_url = settings.presidio_anonymizer_url
        self.custom_entity_service = CustomEntityService()

        # Multi-language entity types supported by Presidio
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
            "DEA_NUMBER",  # US Drug Enforcement Administration number
            "US_ITIN",    # US Individual Taxpayer Identification Number
            "US_EIN",    # US Employer Identification Number
            "AU_ABN",    # Australian Business Number
            "AU_ACN",    # Australian Company Number
            "AU_TFN",    # Australian Tax File Number
            "AU_MEDICARE", # Australian Medicare number
            "UK_NINO",   # UK National Insurance Number
            "UK_NHS",    # UK National Health Service number
            "ES_NIF",    # Spanish NIF (Tax Identification Number)
            "FR_SIRET",  # French SIRET number
            "FR_SIREN",  # French SIREN number
            "FR_NIR",    # French NIR (Social Security Number)
            "IT_FISCAL_CODE", # Italian Fiscal Code
            "IT_VAT_CODE",    # Italian VAT Code
            "DE_IDNR",   # German Identity Number
            "DE_STNR",   # German Tax Number
            "NL_BSN",    # Dutch Social Security Number
            "NL_BTW",    # Dutch VAT Number
            "SE_PERSONNUMMER", # Swedish Personal Number
            "SE_ORGNUMMER",    # Swedish Organization Number
            "RU_SNILS",  # Russian SNILS (Social Insurance Number)
            "RU_INN",    # Russian INN (Taxpayer Identification Number)
            "JP_MY_NUMBER",    # Japanese My Number
            "KR_RESIDENT_NUMBER", # Korean Resident Registration Number
            "CN_ID_CARD",      # Chinese ID Card Number
            "CN_PASSPORT",     # Chinese Passport Number
        ]

    async def anonymize(self, text: str, language: str = "en") -> AnonymizationResult:
        """
        Detect and anonymize PII using Presidio services.

        Args:
            text: Input text to anonymize
            language: Language code (default: en)

        Returns:
            AnonymizationResult — does NOT include original_text to avoid serializing raw PII.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Analyze
                logger.info(f"Analyzing text with Presidio Analyzer at {self.analyzer_url}")

                analyze_response = await client.post(
                    f"{self.analyzer_url}/analyze",
                    json={"text": text, "language": language, "entities": self.entity_types},
                )
                analyze_response.raise_for_status()
                analyzer_results = analyze_response.json()

                logger.info(f"Found {len(analyzer_results)} PII entities")

                # Step 2: Anonymize
                logger.info(f"Anonymizing text with Presidio Anonymizer at {self.anonymizer_url}")

                anonymize_response = await client.post(
                    f"{self.anonymizer_url}/anonymize",
                    json={
                        "text": text,
                        "analyzer_results": analyzer_results,
                        "anonymizers": {
                            "DEFAULT":       {"type": "replace", "new_value": "<REDACTED>"},
                            "PERSON":        {"type": "replace", "new_value": "<PERSON>"},
                            "EMAIL_ADDRESS": {"type": "replace", "new_value": "<EMAIL>"},
                            "PHONE_NUMBER":  {"type": "replace", "new_value": "<PHONE>"},
                            "LOCATION":      {"type": "replace", "new_value": "<LOCATION>"},
                            "DATE_TIME":     {"type": "replace", "new_value": "<DATE>"},
                            "CREDIT_CARD":   {"type": "replace", "new_value": "<CREDIT_CARD>"},
                            "US_SSN":        {"type": "replace", "new_value": "<SSN>"},
                            "IP_ADDRESS":    {"type": "replace", "new_value": "<IP_ADDRESS>"},
                            "URL":           {"type": "replace", "new_value": "<URL>"},
                        },
                    },
                )
                anonymize_response.raise_for_status()
                anonymized_result = anonymize_response.json()

                # Step 3: Build entity list (using original text offsets — do not store original_text)
                entities_found = [
                    PIIEntity(
                        entity_type=r["entity_type"],
                        text=text[r["start"]: r["end"]],
                        start=r["start"],
                        end=r["end"],
                        score=r["score"],
                    )
                    for r in analyzer_results
                ]

                # Step 4: Anonymization map (kept server-side; not returned to caller via response)
                anonymization_map = {
                    text[r["start"]: r["end"]]: f"<{r['entity_type']}>"
                    for r in analyzer_results
                }

                # Step 5: Add custom entities if available
                custom_entities = self.custom_entity_service.detect_custom_entities(text)
                if custom_entities:
                    entities_found.extend([
                        PIIEntity(
                            entity_type=entity['entity_type'],
                            text=entity['text'],
                            start=entity['start'],
                            end=entity['end'],
                            score=entity['confidence']
                        )
                        for entity in custom_entities
                    ])
                    
                    # Update anonymization map with custom entities
                    for entity in custom_entities:
                        anonymization_map[entity['text']] = f"<{entity['entity_type']}>"

                return AnonymizationResult(
                    anonymized_text=anonymized_result["text"],
                    entities_found=entities_found,
                    anonymization_map=anonymization_map,
                )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error communicating with Presidio services: {str(e)}")
            raise Exception(f"Presidio service error: {str(e)}")
        except Exception as e:
            logger.error(f"Error during anonymization: {str(e)}")
            raise

    async def detect_pii_only(self, text: str, language: str = "en") -> List[PIIEntity]:
        """
        Detect PII entities without anonymization.
        
        Args:
            text: Input text to analyze
            language: Language code (default: en)
            
        Returns:
            List of detected PII entities
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Analyze text
                analyze_response = await client.post(
                    f"{self.analyzer_url}/analyze",
                    json={"text": text, "language": language, "entities": self.entity_types},
                )
                analyze_response.raise_for_status()
                analyzer_results = analyze_response.json()

                # Build entity list
                entities_found = [
                    PIIEntity(
                        entity_type=r["entity_type"],
                        text=text[r["start"]: r["end"]],
                        start=r["start"],
                        end=r["end"],
                        score=r["score"],
                    )
                    for r in analyzer_results
                ]

                # Add custom entities
                custom_entities = self.custom_entity_service.detect_custom_entities(text)
                if custom_entities:
                    entities_found.extend([
                        PIIEntity(
                            entity_type=entity['entity_type'],
                            text=entity['text'],
                            start=entity['start'],
                            end=entity['end'],
                            score=entity['confidence']
                        )
                        for entity in custom_entities
                    ])

                return entities_found

        except httpx.HTTPError as e:
            logger.error(f"HTTP error communicating with Presidio Analyzer: {str(e)}")
            raise Exception(f"Presidio Analyzer error: {str(e)}")
        except Exception as e:
            logger.error(f"Error during PII detection: {str(e)}")
            raise

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages for PII detection.
        
        Returns:
            List of supported language codes
        """
        # Presidio supports multiple languages, here are the main ones
        return [
            'en', 'de', 'es', 'fr', 'it', 'pt', 'nl', 'ru', 'ja', 'zh', 
            'ar', 'hi', 'ko', 'tr', 'pl', 'sv', 'da', 'no', 'fi', 'cs',
            'sk', 'hu', 'ro', 'bg', 'hr', 'sr', 'el', 'th', 'vi', 'id'
        ]

    def is_language_supported(self, language: str) -> bool:
        """
        Check if a language is supported for PII detection.
        
        Args:
            language: Language code to check
            
        Returns:
            True if supported, False otherwise
        """
        return language.lower() in self.get_supported_languages()

    async def health_check(self) -> Dict[str, bool]:
        """Check health of Presidio services"""
        health = {"analyzer": False, "anonymizer": False}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                for key, url in [
                    ("analyzer", self.analyzer_url),
                    ("anonymizer", self.anonymizer_url),
                ]:
                    try:
                        resp = await client.get(f"{url}/health")
                        health[key] = resp.status_code == 200
                    except Exception:
                        pass
        except Exception:
            pass

        return health