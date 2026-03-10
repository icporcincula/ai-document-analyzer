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