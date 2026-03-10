# app/api/routes.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
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
from app.services.language_detection import LanguageDetectionService
from app.services.custom_entity_service import CustomEntityService
from app.services.preprocessing_service import FormatDetectionService
from app.services.task_result_service import TaskResultService
from app.services.export_service import ExportService
from app.middleware.auth import get_api_key_auth
from app.middleware.rate_limit import limiter
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)
router = APIRouter()

# Single instances — thread-safe for async use
pdf_service = PDFService()
presidio_client = PresidioClient()
extraction_service = ExtractionService()
task_result_service = TaskResultService()
export_service = ExportService()

class AnalyzeDocumentRequest(BaseModel):
    """Enhanced request validation for document analysis"""
    document_type: DocumentType = Field(
        default=DocumentType.auto,
        description="Type of document: contract, invoice, resume, auto"
    )
    enable_ocr: bool = Field(
        default=True,
        description="Enable OCR for scanned PDFs"
    )
    anonymize_pii: bool = Field(
        default=True,
        description="Anonymize PII before sending to LLM"
    )
    
    @validator('document_type')
    def validate_document_type(cls, v):
        """Validate document type enum values strictly"""
        valid_types = [dt.value for dt in DocumentType]
        if v.value not in valid_types:
            raise ValueError(f"Invalid document type. Must be one of: {', '.join(valid_types)}")
        return v


@router.get("/health", response_model=HealthResponse)
@limiter.limit("100 per minute")
async def health_check(
    auth: str = Depends(get_api_key_auth)
):
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
@limiter.limit("10 per minute")
async def analyze_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Query(
        default=DocumentType.auto,
        description="Type of document: contract, invoice, resume, auto",
    ),
    enable_ocr: bool = Query(default=True, description="Enable OCR for scanned PDFs"),
    anonymize_pii: bool = Query(default=True, description="Anonymize PII before sending to LLM"),
    auth: str = Depends(get_api_key_auth)
):
    """Enhanced parameter validation for document analysis endpoint"""
    
    # Validate document type parameter
    if document_type.value not in [dt.value for dt in DocumentType]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type. Must be one of: {', '.join([dt.value for dt in DocumentType])}"
        )
    
    # Validate boolean parameters
    if not isinstance(enable_ocr, bool):
        raise HTTPException(
            status_code=400,
            detail="enable_ocr must be a boolean value"
        )
    
    if not isinstance(anonymize_pii, bool):
        raise HTTPException(
            status_code=400,
            detail="anonymize_pii must be a boolean value"
        )
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


@router.get("/results/{task_id}")
@limiter.limit("100 per minute")
async def get_analysis_results(
    task_id: str,
    auth: str = Depends(get_api_key_auth)
):
    """Get analysis results for a specific task."""
    try:
        result = await task_result_service.get_task_result(task_id)
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving results for task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving results: {str(e)}")


@router.get("/history")
@limiter.limit("50 per minute")
async def get_document_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    search: str = Query("", description="Search term"),
    auth: str = Depends(get_api_key_auth)
):
    """Get document processing history with pagination and search."""
    try:
        history = await task_result_service.get_task_history(
            page=page,
            page_size=page_size,
            search=search
        )
        return history
    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@router.delete("/history/{task_id}")
@limiter.limit("20 per minute")
async def delete_document_result(
    task_id: str,
    auth: str = Depends(get_api_key_auth)
):
    """Delete a specific document result."""
    try:
        success = await task_result_service.delete_task_result(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": "Task deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")


@router.get("/export/{task_id}/csv")
@limiter.limit("20 per minute")
async def export_to_csv(
    task_id: str,
    auth: str = Depends(get_api_key_auth)
):
    """Export analysis results to CSV format."""
    try:
        csv_content = await export_service.export_to_csv(task_id)
        if not csv_content:
            raise HTTPException(status_code=404, detail="Task not found")
        
        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=results_{task_id}.csv"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting CSV for task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting CSV: {str(e)}")


@router.get("/export/{task_id}/excel")
@limiter.limit("20 per minute")
async def export_to_excel(
    task_id: str,
    auth: str = Depends(get_api_key_auth)
):
    """Export analysis results to Excel format."""
    try:
        excel_content = await export_service.export_to_excel(task_id)
        if not excel_content:
            raise HTTPException(status_code=404, detail="Task not found")
        
        from fastapi.responses import Response
        return Response(
            content=excel_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=results_{task_id}.xlsx"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting Excel for task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting Excel: {str(e)}")


@router.get("/export/{task_id}/json")
@limiter.limit("20 per minute")
async def export_to_json(
    task_id: str,
    auth: str = Depends(get_api_key_auth)
):
    """Export analysis results to JSON format."""
    try:
        json_content = await export_service.export_to_json(task_id)
        if not json_content:
            raise HTTPException(status_code=404, detail="Task not found")
        
        from fastapi.responses import Response
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=results_{task_id}.json"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting JSON for task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting JSON: {str(e)}")


@router.get("/export/history/csv")
@limiter.limit("10 per minute")
async def export_history_to_csv(
    search: str = Query("", description="Search term"),
    auth: str = Depends(get_api_key_auth)
):
    """Export document history to CSV format."""
    try:
        csv_content = await export_service.export_history_to_csv(search=search)
        
        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=document_history.csv"}
        )
    except Exception as e:
        logger.error(f"Error exporting history CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting history CSV: {str(e)}")


@router.get("/metrics")
@limiter.limit("100 per minute")
async def get_metrics(
    auth: str = Depends(get_api_key_auth)
):
    """Get application metrics summary."""
    try:
        from app.metrics.custom_metrics import get_metrics
        metrics = get_metrics()
        summary = metrics.get_metrics_summary()
        
        return {
            "success": True,
            "metrics": summary,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")


@router.post("/analyze-multi-format", response_model=DocumentAnalysisResponse)
@limiter.limit("10 per minute")
async def analyze_multi_format_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Query(
        default=DocumentType.auto,
        description="Type of document: contract, invoice, resume, legal_brief, medical_record, bank_statement, auto",
    ),
    enable_ocr: bool = Query(default=True, description="Enable OCR for image-based content"),
    detect_language: bool = Query(default=True, description="Automatically detect document language"),
    anonymize_pii: bool = Query(default=True, description="Anonymize PII before sending to LLM"),
    auth: str = Depends(get_api_key_auth)
):
    """
    Analyze documents in multiple formats (PDF, DOCX, images) with multi-language support.
    
    - Supports PDF, DOCX, PNG, JPG, BMP, TIFF formats
    - Automatic language detection and multi-language PII processing
    - Format detection and preprocessing
    - Enhanced document type detection
    """
    start_time = time.time()
    document_id = str(uuid.uuid4())

    try:
        logger.info(f"Processing multi-format document {document_id}")

        # Step 1: Validate file size
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        # Step 2: Save to temporary file for processing
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        try:
            # Step 3: Process with unified service
            processing_result = pdf_service.process_document(
                Path(temp_file_path),
                enable_ocr=enable_ocr,
                detect_language=detect_language
            )

            extracted_text = processing_result.get('full_text', '')
            detected_language = processing_result.get('detected_language', 'en')
            format_info = processing_result.get('format', 'unknown')

            if not extracted_text or len(extracted_text.strip()) < 10:
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not extract text from {format_info} file. File may be empty or corrupted."
                )

            logger.info(f"Extracted {len(extracted_text)} characters from {format_info} document")

            # Step 4: Anonymize PII with language support
            pii_entities = []
            text_to_process = extracted_text

            if anonymize_pii:
                logger.info(f"Anonymizing PII in {detected_language}")
                anonymization_result = await presidio_client.anonymize(text_to_process, detected_language)
                text_to_process = anonymization_result.anonymized_text
                pii_entities = anonymization_result.entities_found
                logger.info(f"Anonymized {len(pii_entities)} PII entities")

            # Step 5: Extract fields with language-aware processing
            logger.info(f"Extracting fields with AI for {detected_language} document")
            extracted_fields = await extraction_service.extract_fields(
                text_to_process,
                document_type=document_type.value,
                language=detected_language,
                enable_custom_entities=True
            )

            # Step 6: Calculate enhanced confidence
            language_confidence = processing_result.get('language_detection', {}).get('confidence', 1.0)
            confidence = extraction_service.calculate_confidence(
                extracted_fields, 
                len(pii_entities), 
                language_confidence
            )

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
                metadata={
                    'format_detected': format_info,
                    'language_detected': detected_language,
                    'extraction_method': processing_result.get('extraction_method', 'unknown'),
                    'format_confidence': processing_result.get('format_detection_confidence', 0.0),
                    'text_length': len(extracted_text)
                }
            )

            logger.info(f"Multi-format document {document_id} processed in {processing_time:.2f}s")
            return response

        finally:
            # Clean up temporary file
            import os
            try:
                os.unlink(temp_file_path)
            except:
                pass

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing multi-format document {document_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.post("/detect-language")
@limiter.limit("50 per minute")
async def detect_document_language(
    file: UploadFile = File(...),
    auth: str = Depends(get_api_key_auth)
):
    """
    Detect the language of a document's text content.
    
    Returns language detection results with confidence scores.
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        try:
            # Process document to extract text
            processing_result = pdf_service.process_document(
                Path(temp_file_path),
                enable_ocr=True,
                detect_language=False  # We'll do our own detection
            )
            
            extracted_text = processing_result.get('full_text', '')
            
            if not extracted_text:
                raise HTTPException(status_code=400, detail="Could not extract text from document")
            
            # Detect language
            language_result = language_detector.detect_language(extracted_text)
            
            return {
                "success": True,
                "detected_language": language_result,
                "text_length": len(extracted_text),
                "format": processing_result.get('format', 'unknown')
            }
            
        finally:
            # Clean up
            import os
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Language detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")


@router.get("/supported-languages")
@limiter.limit("100 per minute")
async def get_supported_languages(
    auth: str = Depends(get_api_key_auth)
):
    """Get list of supported languages for PII detection and document processing."""
    return {
        "languages": presidio_client.get_supported_languages(),
        "total": len(presidio_client.get_supported_languages()),
        "multi_language_pii": True,
        "custom_entities": True
    }


@router.get("/format-detection")
@limiter.limit("50 per minute")
async def detect_document_format(
    file: UploadFile = File(...),
    auth: str = Depends(get_api_key_auth)
):
    """Detect the format of an uploaded document file."""
    try:
        # Read file content
        file_content = await file.read()
        
        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        try:
            # Detect format
            format_detector = FormatDetectionService()
            detection_result = format_detector.detect_format(Path(temp_file_path))
            
            return {
                "success": True,
                "format_detection": detection_result,
                "file_size": len(file_content),
                "file_name": file.filename
            }
            
        finally:
            # Clean up
            import os
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Format detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Format detection failed: {str(e)}")


@router.get("/custom-entities")
@limiter.limit("100 per minute")
async def get_custom_entities(
    auth: str = Depends(get_api_key_auth)
):
    """Get list of configured custom PII entities."""
    try:
        custom_entity_service = CustomEntityService()
        entities = custom_entity_service.get_custom_entities()
        
        return {
            "success": True,
            "custom_entities": entities,
            "total_entities": len(entities),
            "enabled_entities": len([e for e in entities if e.get('enabled', True)])
        }
        
    except Exception as e:
        logger.error(f"Failed to get custom entities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get custom entities: {str(e)}")


@router.post("/test-custom-entity")
@limiter.limit("20 per minute")
async def test_custom_entity(
    text: str,
    entity_name: str,
    auth: str = Depends(get_api_key_auth)
):
    """Test a custom entity pattern against text."""
    try:
        custom_entity_service = CustomEntityService()
        
        # Get entity
        entity = custom_entity_service.get_entity_by_name(entity_name)
        if not entity:
            raise HTTPException(status_code=404, detail=f"Custom entity '{entity_name}' not found")
        
        # Test detection
        detected_entities = custom_entity_service.detect_custom_entities(text)
        matching_entities = [e for e in detected_entities if e['entity_type'] == entity_name]
        
        return {
            "success": True,
            "entity_name": entity_name,
            "entity_pattern": entity['pattern'],
            "detected_matches": matching_entities,
            "text_length": len(text),
            "total_matches": len(matching_entities)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Custom entity test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Custom entity test failed: {str(e)}")
