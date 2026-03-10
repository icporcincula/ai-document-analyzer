"""
Enhanced Extraction Service with Multi-Language Support

This service provides AI-powered field extraction with multi-language support,
custom entity integration, and enhanced document type detection.
"""

import re
import asyncio
from openai import AsyncOpenAI
import json
import logging
from enum import Enum
from typing import Dict, List, Any, Optional
from pathlib import Path

from app.models.schemas import ExtractedField
from app.utils.config import get_config
from app.services.language_detection import LanguageDetectionService
from app.services.presidio_client import PresidioClient
from app.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)
config = get_config()


class DocumentType(str, Enum):
    contract = "contract"
    invoice = "invoice"
    resume = "resume"
    legal_brief = "legal_brief"
    medical_record = "medical_record"
    bank_statement = "bank_statement"
    auto = "auto"


class ExtractionService:
    """Enhanced service for AI-powered field extraction from documents"""
    
    def __init__(self):
        """Initialize the enhanced extraction service"""
        self.client = AsyncOpenAI(
            base_url=config.openai_url,
            api_key=config.openai_api_key,
        )
        self.language_detector = LanguageDetectionService()
        self.presidio_client = PresidioClient()
        
        # Multi-language prompts
        self.language_prompts = {
            'en': "Extract fields from this document text.",
            'de': "Extrahieren Sie Felder aus diesem Dokumenttext.",
            'es': "Extraiga campos de este texto del documento.",
            'fr': "Extrayez les champs de ce texte de document.",
            'it': "Estrai i campi da questo testo del documento.",
            'pt': "Extraia campos deste texto do documento.",
            'nl': "Extraheer velden uit deze documenttekst.",
            'ru': "Извлеките поля из этого текста документа.",
            'ja': "この文書テキストから項目を抽出してください。",
            'zh': "从该文档文本中提取字段。"
        }
    
    async def extract_fields(
        self,
        text: str,
        document_type: str = "auto",
        language: str = "auto",
        enable_custom_entities: bool = True
    ) -> Dict[str, ExtractedField]:
        """
        Extract structured fields from document text using AI with multi-language support.
        
        Args:
            text: Document text (anonymized or original)
            document_type: Type of document
            language: Language code (auto for detection)
            enable_custom_entities: Whether to use custom entity detection
            
        Returns:
            Dictionary of field_name -> ExtractedField
        """
        try:
            # Detect language if not specified
            detected_language = language
            if language == "auto":
                language_result = self.language_detector.detect_language(text)
                if language_result.get('success', False):
                    detected_language = language_result.get('detected_language', 'en')
                    logger.info(f"Detected language: {detected_language}")
                else:
                    detected_language = 'en'
                    logger.warning("Language detection failed, using English as default")
            
            # Validate language support
            if not self.presidio_client.is_language_supported(detected_language):
                logger.warning(f"Language {detected_language} not fully supported, using English")
                detected_language = 'en'
            
            # Truncate if necessary to avoid LLM context limits
            max_chars = 15_000 if detected_language in ['en', 'de', 'fr', 'es'] else 10_000
            if len(text) > max_chars:
                logger.warning(
                    f"Document text truncated from {len(text)} to {max_chars} chars "
                    "before LLM extraction."
                )
                text = text[:max_chars]
            
            # Get appropriate prompt for language
            prompt_instruction = self.language_prompts.get(detected_language, self.language_prompts['en'])
            
            # Get system prompt based on document type and language
            system_prompt = self._get_system_prompt(document_type, detected_language)
            
            # Add custom entity context if enabled
            if enable_custom_entities:
                custom_entities = await self._get_custom_entity_context(text, detected_language)
                if custom_entities:
                    system_prompt += f"\n\nCUSTOM ENTITIES CONTEXT:\n{custom_entities}"
            
            response = await self.client.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{prompt_instruction}\n\n{text}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            
            raw_content = response.choices[0].message.content
            
            # Strip DeepSeek / reasoning model <tool_call> blocks
            clean_content = re.sub(r"<tool_call>.*?<tool_call>", "", raw_content, flags=re.DOTALL).strip()
            
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
                    language=detected_language
                )
            
            logger.info(f"Extracted {len(fields)} fields from {detected_language} document")
            return fields
            
        except Exception as e:
            logger.error(f"Error during field extraction: {str(e)}")
            raise DocumentProcessingError(f"Field extraction failed: {str(e)}")
    
    async def _get_custom_entity_context(self, text: str, language: str) -> Optional[str]:
        """
        Get custom entity context for enhanced extraction.
        
        Args:
            text: Document text
            language: Document language
            
        Returns:
            Custom entity context string or None
        """
        try:
            # Detect PII entities for context
            pii_entities = await self.presidio_client.detect_pii_only(text, language)
            
            if not pii_entities:
                return None
            
            # Group entities by type
            entity_types = {}
            for entity in pii_entities:
                if entity.entity_type not in entity_types:
                    entity_types[entity.entity_type] = []
                entity_types[entity.entity_type].append(entity.text)
            
            # Build context string
            context_parts = []
            for entity_type, entities in entity_types.items():
                unique_entities = list(set(entities))[:5]  # Limit to 5 examples
                context_parts.append(f"{entity_type}: {', '.join(unique_entities)}")
            
            if context_parts:
                return "The following PII entities were detected and anonymized:\n" + "\n".join(context_parts)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get custom entity context: {str(e)}")
            return None
    
    def calculate_confidence(self, fields: Dict[str, ExtractedField], pii_count: int, 
                           language_confidence: float = 1.0) -> float:
        """
        Calculate overall confidence score based on per-field scores, null ratio, and language detection.
        
        Args:
            fields: Extracted fields
            pii_count: Number of PII entities found
            language_confidence: Confidence in language detection
            
        Returns:
            Overall confidence score (0.0 to 1.0)
        """
        if not fields:
            return 0.0
        
        values = list(fields.values())
        
        # Average of per-field confidences returned by the LLM
        avg_field_confidence = sum(f.confidence for f in values) / len(values)
        
        # Penalize empty/null fields
        null_ratio = sum(1 for f in values if not f.value or f.value in ("null", "None", "")) / len(values)
        null_penalty = null_ratio * 0.2
        
        # Adjust for PII anonymization impact
        pii_penalty = min(pii_count * 0.01, 0.1)  # Max 10% penalty for PII
        
        # Language detection confidence factor
        language_factor = language_confidence * 0.1
        
        score = avg_field_confidence - null_penalty - pii_penalty + language_factor
        return round(max(0.0, min(1.0, score)), 2)
    
    def _get_system_prompt(self, document_type: str, language: str) -> str:
        """Get appropriate system prompt based on document type and language."""
        
        # Base prompt template with language support
        base_prompt = f"""You are a precise document extraction agent.
Your goal is to output a structured JSON representation of the provided text.

CRITICAL INSTRUCTIONS:
1. Output MUST be valid JSON — no preamble, no markdown fences, no reasoning text.
2. For each field, return an object with "value" and "confidence" (0.0–1.0).
3. If a field is missing, set "value" to null and "confidence" to 0.0.
4. Preserve anonymization placeholders like <PERSON>, <EMAIL>, <DATE> exactly as they appear.
5. Adapt to the document language: {language}

REQUIRED SCHEMA:
{{
  "fields": {{
    "field_name": {{ "value": "...", "confidence": 0.95 }}
  }}
}}
"""
        
        # Document-specific prompts with multi-language support
        type_specific_prompts = {
            "contract": base_prompt + f"""
For contracts in {language}, extract:
- contract_type
- parties (note if anonymized as <PERSON> or <LOCATION>)
- effective_date (note if anonymized as <DATE>)
- termination_date
- contract_value
- key_terms
- signatures_present (yes/no)
""",
            "invoice": base_prompt + f"""
For invoices in {language}, extract:
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
            "resume": base_prompt + f"""
For resumes in {language}, extract:
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
            "legal_brief": base_prompt + f"""
For legal briefs in {language}, extract:
- case_name
- case_number
- court
- judge
- parties_involved
- legal_issues
- arguments_presented
- relief_sought
- filing_date
""",
            "medical_record": base_prompt + f"""
For medical records in {language}, extract:
- patient_id (note if anonymized)
- date_of_birth
- medical_record_number
- primary_diagnosis
- procedures_performed
- medications
- attending_physician
- admission_date
- discharge_date
""",
            "bank_statement": base_prompt + f"""
For bank statements in {language}, extract:
- account_number (note if anonymized)
- statement_period
- opening_balance
- closing_balance
- total_deposits
- total_withdrawals
- bank_name
- statement_date
""",
            "auto": base_prompt + f"""
Analyze the document in {language} and automatically detect its type, then extract relevant fields.

Common types: contract, invoice, resume, legal_brief, medical_record, bank_statement, letter, form

Extract the most important 5-10 fields based on document type and language.
""",
        }
        
        return type_specific_prompts.get(document_type, type_specific_prompts["auto"])
    
    async def detect_document_type(self, text: str, language: str = "auto") -> str:
        """
        Automatically detect document type.
        
        Args:
            text: Document text
            language: Document language
            
        Returns:
            Detected document type
        """
        try:
            # Language detection if not specified
            detected_language = language
            if language == "auto":
                language_result = self.language_detector.detect_language(text)
                if language_result.get('success', False):
                    detected_language = language_result.get('detected_language', 'en')
            
            # Use LLM to classify document type
            system_prompt = f"""You are a document classification expert.
Analyze the provided text and determine the document type.

Available types: contract, invoice, resume, legal_brief, medical_record, bank_statement

Return ONLY the document type as a single word, no explanation.
Language context: {detected_language}"""
            
            response = await self.client.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Classify this document:\n\n{text[:5000]}"},
                ],
                temperature=0.1,
            )
            
            detected_type = response.choices[0].message.content.strip().lower()
            
            # Validate against known types
            valid_types = [t.value for t in DocumentType]
            if detected_type in valid_types:
                return detected_type
            else:
                return "auto"  # Fallback to auto mode
                
        except Exception as e:
            logger.error(f"Document type detection failed: {str(e)}")
            return "auto"