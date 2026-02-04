# app/services/extraction_service.py
import re
from openai import OpenAI
import json
import logging
from typing import Dict
from app.models.schemas import ExtractedField
from app.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ExtractionService:
    """Service for AI-powered field extraction from documents"""
    
    def __init__(self):
        self.client = OpenAI(base_url=settings.openai_url,api_key=settings.openai_api_key)
    
    def extract_fields(
        self, 
        text: str, 
        document_type: str = "auto"
    ) -> Dict[str, ExtractedField]:
        """
        Extract structured fields from document text using AI
        
        Args:
            text: Document text (anonymized or original)
            document_type: Type of document (contract, invoice, resume, auto)
            
        Returns:
            Dictionary of field_name -> ExtractedField
        """
        try:
            # Build prompt based on document type
            system_prompt = self._get_system_prompt(document_type)
            
            # Call OpenAI with structured output
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract fields from this document:\n\n{text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistent extraction
            )
            
            # Parse response
            # 1. Capture the raw response text
            raw_content = response.choices[0].message.content
            
            # 2. STRIP DEEPSEEK THINKING BLOCK
            # This removes everything between <think> and </think>
            clean_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()
            
            # 3. Parse the cleaned JSON
            try:
                extracted_data = json.loads(clean_content)
            except json.JSONDecodeError:
                # Fallback: DeepSeek sometimes puts JSON in markdown code blocks
                json_match = re.search(r'\{.*\}', clean_content, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group(0))
                else:
                    raise
            
            # Convert to ExtractedField objects
            fields = {}
            for field_name, value in extracted_data.get("fields", {}).items():
                fields[field_name] = ExtractedField(
                    field_name=field_name,
                    value=str(value),
                    confidence=0.9,  # Could enhance with actual confidence scoring
                    source="ai_extraction"
                )
            
            logger.info(f"Extracted {len(fields)} fields from document")
            return fields
            
        except Exception as e:
            logger.error(f"Error during field extraction: {str(e)}")
            raise
    
    def _get_system_prompt(self, document_type: str) -> str:
        """Get appropriate system prompt based on document type"""
        
        base_prompt = """You are a precise document extraction agent. 
Your goal is to output a structured JSON representation of the provided text.

CRITICAL INSTRUCTIONS:
1. Output MUST be valid JSON.
2. If a field is missing, use null (not the string "None").
3. Preserve placeholders like <PERSON> or <LOCATION> exactly as they appear.
4. Do not include any text, reasoning, or preamble outside of the JSON object.

REQUIRED SCHEMA:
{
  "fields": {
    "key_name": "value"
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
- key_skills (list)
- most_recent_employer
""",
            "auto": base_prompt + """
Analyze the document and automatically detect its type, then extract relevant fields.

Common types: contract, invoice, resume, letter, form

Extract the most important 5-10 fields based on document type.
"""
        }
        
        return type_specific_prompts.get(document_type, type_specific_prompts["auto"])