# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    contract = "contract"
    invoice = "invoice"
    resume = "resume"
    auto = "auto"


class PIIEntity(BaseModel):
    """Detected PII entity"""
    entity_type: str
    text: str
    start: int
    end: int
    score: float


class AnonymizationResult(BaseModel):
    """Result of PII anonymization — original_text is intentionally excluded from this model
    to prevent raw PII being serialized outside the processing pipeline."""
    anonymized_text: str
    entities_found: List[PIIEntity]
    anonymization_map: Dict[str, str]  # original -> anonymized placeholder


class ExtractedField(BaseModel):
    """Single extracted field from document"""
    field_name: str
    value: str
    confidence: float
    source: str  # "ai_extraction" | "text" | "ocr"


class DocumentAnalysisRequest(BaseModel):
    """Request to analyze document"""
    document_type: Optional[DocumentType] = Field(
        default=DocumentType.auto,
        description="Type of document: contract, invoice, resume, auto",
    )
    enable_ocr: bool = Field(
        default=True,
        description="Enable OCR for scanned documents",
    )
    anonymize_pii: bool = Field(
        default=True,
        description="Anonymize PII before sending to LLM",
    )


class DocumentAnalysisResponse(BaseModel):
    """Response from document analysis"""
    document_id: str
    document_type: str
    extracted_fields: Dict[str, ExtractedField]
    anonymization_performed: bool
    pii_entities_found: List[PIIEntity]
    confidence: float
    processing_time_seconds: float
    processed_at: datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    services: Optional[Dict[str, bool]] = None