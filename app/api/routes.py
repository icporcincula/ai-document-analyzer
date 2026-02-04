# app/api/routes.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import time
import uuid
from datetime import datetime
import logging

from app.models.schemas import (
    DocumentAnalysisRequest,
    DocumentAnalysisResponse,
    HealthResponse,
    ExtractedField
)
from app.services.pdf_service import PDFService
from app.services.presidio_client import PresidioClient
from app.services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
pdf_service = PDFService()
presidio_client = PresidioClient()
extraction_service = ExtractionService()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    presidio_health = await presidio_client.health_check()
    
    return {
        "status": "healthy" if all(presidio_health.values()) else "degraded",
        "timestamp": datetime.utcnow(),
        "services": {
            "presidio_analyzer": presidio_health["analyzer"],
            "presidio_anonymizer": presidio_health["anonymizer"]
        }
    }

@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(
    file: UploadFile = File(...),
    document_type: str = "auto",
    enable_ocr: bool = True,
    anonymize_pii: bool = True
):
    """
    Analyze a PDF document with optional PII anonymization
    
    Args:
        file: PDF file to analyze
        document_type: Type of document (contract, invoice, resume, auto)
        enable_ocr: Enable OCR for scanned documents
        anonymize_pii: Anonymize PII before sending to LLM
        
    Returns:
        DocumentAnalysisResponse with extracted fields and PII info
    """
    start_time = time.time()
    document_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Processing document {document_id}")
        
        # Step 1: Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Step 2: Read PDF bytes
        pdf_bytes = await file.read()
        logger.info(f"Read {len(pdf_bytes)} bytes from PDF")
        
        # Step 3: Extract text from PDF
        extracted_text, extraction_source = pdf_service.extract_text(
            pdf_bytes, 
            enable_ocr=enable_ocr
        )
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF. File may be empty or corrupted."
            )
        
        logger.info(f"Extracted {len(extracted_text)} characters from PDF")
        
        # Step 4: Anonymize PII if requested
        pii_entities = []
        text_to_process = extracted_text
        anonymization_map = {}
        
        if anonymize_pii:
            logger.info("Anonymizing PII")
            anonymization_result = await presidio_client.anonymize(extracted_text)
            text_to_process = anonymization_result.anonymized_text
            pii_entities = anonymization_result.entities_found
            anonymization_map = anonymization_result.anonymization_map
            
            logger.info(f"Found and anonymized {len(pii_entities)} PII entities")
        
        # Step 5: Extract fields using AI
        logger.info("Extracting fields with AI")
        extracted_fields = extraction_service.extract_fields(
            text_to_process,
            document_type=document_type
        )
        
        # Step 6: Calculate confidence
        confidence = ExtractionService._calculate_confidence(
            extracted_fields,
            len(pii_entities)
        )
        
        # Step 7: Build response
        processing_time = time.time() - start_time
        
        response = DocumentAnalysisResponse(
            document_id=document_id,
            document_type=document_type,
            extracted_fields=extracted_fields,
            anonymization_performed=anonymize_pii,
            pii_entities_found=pii_entities,
            confidence=confidence,
            processing_time_seconds=round(processing_time, 2),
            processed_at=datetime.utcnow()
        )
        
        logger.info(f"Document {document_id} processed successfully in {processing_time:.2f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )

# Add helper method to ExtractionService
def _calculate_confidence(fields: dict, pii_count: int) -> float:
    """Calculate overall confidence score"""
    if not fields:
        return 0.0
    
    # Base confidence on number of fields extracted
    field_confidence = min(len(fields) / 10, 1.0) * 0.7
    
    # Adjust for PII detection (more PII = more thorough analysis)
    pii_confidence = min(pii_count / 5, 1.0) * 0.3
    
    return round(field_confidence + pii_confidence, 2)


# Monkey-patch the method
ExtractionService._calculate_confidence = staticmethod(_calculate_confidence)