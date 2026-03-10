# app/api/routes.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Optional
import time
import uuid
from datetime import datetime
import logging

from app.models.schemas import (
    DocumentAnalysisResponse,
    DocumentType,
    HealthResponse,
)
from app.services.pdf_service import PDFService
from app.services.presidio_client import PresidioClient
from app.services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)
router = APIRouter()

# Single instances — thread-safe for async use
pdf_service = PDFService()
presidio_client = PresidioClient()
extraction_service = ExtractionService()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint — reports status of Presidio dependencies."""
    presidio_health = await presidio_client.health_check()

    return HealthResponse(
        status="healthy" if all(presidio_health.values()) else "degraded",
        timestamp=datetime.utcnow(),
        services={
            "presidio_analyzer": presidio_health["analyzer"],
            "presidio_anonymizer": presidio_health["anonymizer"],
        },
    )


@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Query(
        default=DocumentType.auto,
        description="Type of document: contract, invoice, resume, auto",
    ),
    enable_ocr: bool = Query(default=True, description="Enable OCR for scanned PDFs"),
    anonymize_pii: bool = Query(default=True, description="Anonymize PII before sending to LLM"),
):
    """
    Analyze a PDF document with optional PII anonymization.

    - Validates file size (max 10 MB) and page count (max 50 pages)
    - Extracts text (direct or OCR)
    - Anonymizes PII via Presidio (when enabled)
    - Extracts structured fields via LLM
    """
    start_time = time.time()
    document_id = str(uuid.uuid4())

    try:
        logger.info(f"Processing document {document_id}")

        # Step 1: Validate content type
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        # Step 2: Read bytes
        pdf_bytes = await file.read()
        logger.info(f"Read {len(pdf_bytes)} bytes from upload")

        # Step 3: Validate size and page count (raises ValueError on failure)
        try:
            pdf_service.validate(pdf_bytes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Step 4: Extract text
        extracted_text, extraction_source = pdf_service.extract_text(
            pdf_bytes, enable_ocr=enable_ocr
        )

        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF. File may be empty or corrupted.",
            )

        logger.info(f"Extracted {len(extracted_text)} characters via {extraction_source}")

        # Step 5: Anonymize PII
        pii_entities = []
        text_to_process = extracted_text

        if anonymize_pii:
            logger.info("Anonymizing PII")
            anonymization_result = await presidio_client.anonymize(extracted_text)
            text_to_process = anonymization_result.anonymized_text
            pii_entities = anonymization_result.entities_found
            logger.info(f"Anonymized {len(pii_entities)} PII entities")

        # Step 6: Extract fields via LLM (async — does not block event loop)
        logger.info("Extracting fields with AI")
        extracted_fields = await extraction_service.extract_fields(
            text_to_process,
            document_type=document_type.value,
        )

        # Step 7: Calculate confidence
        confidence = extraction_service.calculate_confidence(extracted_fields, len(pii_entities))

        processing_time = time.time() - start_time

        response = DocumentAnalysisResponse(
            document_id=document_id,
            document_type=document_type.value,
            extracted_fields=extracted_fields,
            anonymization_performed=anonymize_pii,
            pii_entities_found=pii_entities,
            confidence=confidence,
            processing_time_seconds=round(processing_time, 2),
            processed_at=datetime.utcnow(),
        )

        logger.info(f"Document {document_id} processed in {processing_time:.2f}s")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")