# app/services/extraction_service.py
import re
import asyncio
from openai import AsyncOpenAI
import json
import logging
from enum import Enum
from typing import Dict
from app.models.schemas import ExtractedField
from app.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

MAX_CHARS = 15_000  # Truncate input to avoid LLM context overflows


class DocumentType(str, Enum):
    contract = "contract"
    invoice = "invoice"
    resume = "resume"
    auto = "auto"


class ExtractionService:
    """Service for AI-powered field extraction from documents"""

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.openai_url,
            api_key=settings.openai_api_key,
        )

    async def extract_fields(
        self,
        text: str,
        document_type: str = "auto",
    ) -> Dict[str, ExtractedField]:
        """
        Extract structured fields from document text using AI.

        Args:
            text: Document text (anonymized or original)
            document_type: Type of document (contract, invoice, resume, auto)

        Returns:
            Dictionary of field_name -> ExtractedField
        """
        # Truncate if necessary to avoid LLM context limits
        if len(text) > MAX_CHARS:
            logger.warning(
                f"Document text truncated from {len(text)} to {MAX_CHARS} chars "
                "before LLM extraction."
            )
            text = text[:MAX_CHARS]

        try:
            system_prompt = self._get_system_prompt(document_type)

            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract fields from this document:\n\n{text}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            raw_content = response.choices[0].message.content

            # Strip DeepSeek / reasoning model <think> blocks
            clean_content = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.DOTALL).strip()

            try:
                extracted_data = json.loads(clean_content)
            except json.JSONDecodeError:
                # Fallback: some models wrap JSON in markdown code fences
                json_match = re.search(r"\{.*\}", clean_content, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group(0))
                else:
                    raise

            fields: Dict[str, ExtractedField] = {}
            for field_name, field_data in extracted_data.get("fields", {}).items():
                # The LLM returns either a plain value or a {value, confidence} dict
                if isinstance(field_data, dict):
                    value = str(field_data.get("value", ""))
                    confidence = float(field_data.get("confidence", 0.8))
                else:
                    value = str(field_data) if field_data is not None else ""
                    confidence = 0.8

                fields[field_name] = ExtractedField(
                    field_name=field_name,
                    value=value,
                    confidence=confidence,
                    source="ai_extraction",
                )

            logger.info(f"Extracted {len(fields)} fields from document")
            return fields

        except Exception as e:
            logger.error(f"Error during field extraction: {str(e)}")
            raise

    def calculate_confidence(self, fields: Dict[str, ExtractedField], pii_count: int) -> float:
        """
        Calculate overall confidence score based on per-field scores and null ratio.
        """
        if not fields:
            return 0.0

        values = list(fields.values())

        # Average of per-field confidences returned by the LLM
        avg_field_confidence = sum(f.confidence for f in values) / len(values)

        # Penalise empty/null fields
        null_ratio = sum(1 for f in values if not f.value or f.value in ("null", "None", "")) / len(values)
        null_penalty = null_ratio * 0.2

        score = avg_field_confidence - null_penalty
        return round(max(0.0, min(1.0, score)), 2)

    def _get_system_prompt(self, document_type: str) -> str:
        """Get appropriate system prompt based on document type."""

        base_prompt = """You are a precise document extraction agent.
Your goal is to output a structured JSON representation of the provided text.

CRITICAL INSTRUCTIONS:
1. Output MUST be valid JSON — no preamble, no markdown fences, no reasoning text.
2. For each field, return an object with "value" and "confidence" (0.0–1.0).
3. If a field is missing, set "value" to null and "confidence" to 0.0.
4. Preserve anonymization placeholders like <PERSON>, <EMAIL>, <DATE> exactly as they appear.

REQUIRED SCHEMA:
{
  "fields": {
    "field_name": { "value": "...", "confidence": 0.95 }
  }
}
"""

        type_specific_prompts = {
            "contract": base_prompt + """
For contracts, extract:
- contract_type
- parties (note if anonymized as <PERSON> or <LOCATION>)
- effective_date (note if anonymized as <DATE>)
- termination_date
- contract_value
- key_terms
- signatures_present (yes/no)
""",
            "invoice": base_prompt + """
For invoices, extract:
- invoice_number
- invoice_date
- due_date
- vendor (note if anonymized)
- customer (note if anonymized)
- total_amount
- currency
- line_items (summarize)
- payment_terms
""",
            "resume": base_prompt + """
For resumes, extract:
- candidate_name (note if anonymized as <PERSON>)
- email (note if anonymized as <EMAIL>)
- phone (note if anonymized as <PHONE>)
- location (note if anonymized as <LOCATION>)
- current_title
- years_of_experience
- education
- key_skills (list as comma-separated string)
- most_recent_employer
""",
            "auto": base_prompt + """
Analyze the document and automatically detect its type, then extract relevant fields.

Common types: contract, invoice, resume, letter, form

Extract the most important 5-10 fields based on document type.
""",
        }

        return type_specific_prompts.get(document_type, type_specific_prompts["auto"])