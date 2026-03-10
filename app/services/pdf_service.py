"""
Unified Document Processing Service

This service handles multiple document formats including PDF, DOCX, and images.
It provides format detection, preprocessing, and text extraction capabilities.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import tempfile
import pypdf
from pypdf.errors import PdfReadError
from pdf2image import convert_from_path
import pytesseract

from app.utils.config import get_config
from app.exceptions import DocumentProcessingError
from app.services.docx_service import DOCXService
from app.services.image_service import ImageService
from app.services.language_detection import LanguageDetectionService
from app.services.preprocessing_service import DocumentPreprocessingService

logger = logging.getLogger(__name__)
config = get_config()


class PDFService:
    """Unified service for processing multiple document formats"""
    
    def __init__(self):
        """Initialize the unified document service"""
        self.docx_service = DOCXService()
        self.image_service = ImageService()
        self.language_detector = LanguageDetectionService()
        self.preprocessor = DocumentPreprocessingService()
        
        # Supported formats and their services
        self.format_services = {
            'pdf': self._process_pdf,
            'docx': self._process_docx,
            'image': self._process_image,
            'text': self._process_text
        }
    
    def process_document(self, file_path: Path, enable_ocr: bool = True, 
                        detect_language: bool = True) -> Dict[str, Any]:
        """
        Process a document of any supported format.
        
        Args:
            file_path: Path to the document file
            enable_ocr: Whether to enable OCR for image-based content
            detect_language: Whether to detect document language
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            logger.info(f"Processing document: {file_path}")
            
            # Preprocess document
            preprocessing_result = self.preprocessor.preprocess_document(file_path)
            
            if not preprocessing_result.get('success', True):
                raise DocumentProcessingError(f"Preprocessing failed: {preprocessing_result.get('error', 'Unknown error')}")
            
            # Get suggested service
            suggested_service = preprocessing_result.get('suggested_service', 'generic_service')
            detected_format = preprocessing_result.get('detected_format')
            
            # Process with appropriate service
            if detected_format in self.format_services:
                result = self.format_services[detected_format](file_path, enable_ocr)
            else:
                result = self._process_generic(file_path)
            
            # Add preprocessing metadata
            result.update({
                'preprocessing': preprocessing_result,
                'format_detection_confidence': preprocessing_result.get('format_confidence', 0.0)
            })
            
            # Detect language if requested
            if detect_language and result.get('full_text'):
                language_result = self.language_detector.detect_language(result['full_text'])
                result['language_detection'] = language_result
                
                # Use detected language for PII processing if confident
                if language_result.get('success', False):
                    result['detected_language'] = language_result.get('detected_language', 'en')
                else:
                    result['detected_language'] = 'en'  # Default fallback
            else:
                result['detected_language'] = 'en'
            
            logger.info(f"Successfully processed {detected_format} document: {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process document {file_path}: {str(e)}")
            raise DocumentProcessingError(f"Document processing failed: {str(e)}")
    
    def _process_pdf(self, file_path: Path, enable_ocr: bool = True) -> Dict[str, Any]:
        """
        Process PDF document with text extraction and OCR fallback.
        
        Args:
            file_path: Path to PDF file
            enable_ocr: Whether to enable OCR for scanned PDFs
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Validate PDF
            self._validate_pdf(file_path)
            
            # Try text extraction first
            text_result = self._extract_pdf_text(file_path)
            
            if text_result['has_text'] and len(text_result['text']) > 50:
                logger.info(f"Extracted text directly from PDF: {file_path}")
                return {
                    'full_text': text_result['text'],
                    'extraction_method': 'text_extraction',
                    'page_count': text_result['page_count'],
                    'text_length': len(text_result['text']),
                    'format': 'pdf'
                }
            
            # Fallback to OCR if text extraction failed
            if enable_ocr:
                logger.info(f"Using OCR for PDF: {file_path}")
                ocr_result = self._extract_pdf_ocr(file_path)
                return {
                    'full_text': ocr_result['text'],
                    'extraction_method': 'ocr',
                    'page_count': ocr_result['page_count'],
                    'ocr_confidence': ocr_result.get('confidence', 0.0),
                    'text_length': len(ocr_result['text']),
                    'format': 'pdf'
                }
            
            # Return what we have
            return {
                'full_text': text_result['text'],
                'extraction_method': 'text_extraction',
                'page_count': text_result['page_count'],
                'text_length': len(text_result['text']),
                'format': 'pdf',
                'warning': 'OCR disabled, limited text extracted'
            }
            
        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            raise DocumentProcessingError(f"PDF processing failed: {str(e)}")
    
    def _process_docx(self, file_path: Path, enable_ocr: bool = True) -> Dict[str, Any]:
        """
        Process DOCX document.
        
        Args:
            file_path: Path to DOCX file
            enable_ocr: Ignored for DOCX (not applicable)
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            result = self.docx_service.process_docx_file(file_path)
            result['extraction_method'] = 'docx_extraction'
            return result
            
        except Exception as e:
            logger.error(f"DOCX processing failed: {str(e)}")
            raise DocumentProcessingError(f"DOCX processing failed: {str(e)}")
    
    def _process_image(self, file_path: Path, enable_ocr: bool = True) -> Dict[str, Any]:
        """
        Process image document with OCR.
        
        Args:
            file_path: Path to image file
            enable_ocr: Whether to enable OCR (required for images)
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            if not enable_ocr:
                raise DocumentProcessingError("OCR is required for image processing")
            
            result = self.image_service.extract_text_from_image(file_path)
            result['extraction_method'] = 'image_ocr'
            return result
            
        except Exception as e:
            logger.error(f"Image processing failed: {str(e)}")
            raise DocumentProcessingError(f"Image processing failed: {str(e)}")
    
    def _process_text(self, file_path: Path, enable_ocr: bool = True) -> Dict[str, Any]:
        """
        Process plain text document.
        
        Args:
            file_path: Path to text file
            enable_ocr: Ignored for text files (not applicable)
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            return {
                'full_text': text,
                'extraction_method': 'text_file',
                'text_length': len(text),
                'format': 'text',
                'file_size': file_path.stat().st_size
            }
            
        except Exception as e:
            logger.error(f"Text file processing failed: {str(e)}")
            raise DocumentProcessingError(f"Text file processing failed: {str(e)}")
    
    def _process_generic(self, file_path: Path) -> Dict[str, Any]:
        """
        Generic document processing fallback.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with error information
        """
        return {
            'error': f'Unsupported document format: {file_path.suffix}',
            'file_path': str(file_path),
            'success': False,
            'format': 'unknown'
        }
    
    def _validate_pdf(self, file_path: Path) -> None:
        """
        Validate PDF file for processing.
        
        Args:
            file_path: Path to PDF file
            
        Raises:
            DocumentProcessingError: If PDF is invalid
        """
        try:
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > config.pdf.max_file_size:
                raise DocumentProcessingError(
                    f"PDF file too large: {file_size} bytes (max: {config.pdf.max_file_size})"
                )
            
            # Try to open PDF
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                
                # Check for security restrictions
                if reader.is_encrypted:
                    raise DocumentProcessingError("Encrypted PDFs are not supported")
                
                # Check page count
                if len(reader.pages) > 100:  # Reasonable limit
                    raise DocumentProcessingError("PDF has too many pages (max: 100)")
                
        except PdfReadError as e:
            raise DocumentProcessingError(f"Invalid PDF file: {str(e)}")
        except Exception as e:
            raise DocumentProcessingError(f"PDF validation failed: {str(e)}")
    
    def _extract_pdf_text(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract text directly from PDF.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with extraction results
        """
        try:
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                
                text_parts = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                
                full_text = '\n'.join(text_parts)
                
                return {
                    'text': full_text,
                    'has_text': len(full_text.strip()) > 0,
                    'page_count': len(reader.pages),
                    'text_length': len(full_text)
                }
                
        except Exception as e:
            logger.error(f"PDF text extraction failed: {str(e)}")
            return {
                'text': '',
                'has_text': False,
                'page_count': 0,
                'text_length': 0,
                'error': str(e)
            }
    
    def _extract_pdf_ocr(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract text from PDF using OCR.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with OCR results
        """
        try:
            # Convert PDF to images
            images = convert_from_path(
                str(file_path),
                dpi=config.pdf.pdf_ocr_dpi,
                fmt='jpeg'
            )
            
            text_parts = []
            confidences = []
            
            for i, image in enumerate(images):
                # Configure OCR
                ocr_config = f"--psm 6 --oem 3 -l {config.pdf.pdf_ocr_language}"
                
                # Extract text
                text = pytesseract.image_to_string(image, config=ocr_config)
                text_parts.append(text)
                
                # Get confidence if available
                try:
                    data = pytesseract.image_to_data(image, config=ocr_config, output_type=pytesseract.Output.DICT)
                    page_confidences = [conf for conf in data['conf'] if conf > 0]
                    if page_confidences:
                        confidences.append(sum(page_confidences) / len(page_confidences))
                except:
                    pass
            
            full_text = '\n'.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return {
                'text': full_text,
                'page_count': len(images),
                'confidence': avg_confidence,
                'text_length': len(full_text)
            }
            
        except Exception as e:
            logger.error(f"PDF OCR extraction failed: {str(e)}")
            return {
                'text': '',
                'page_count': 0,
                'confidence': 0.0,
                'text_length': 0,
                'error': str(e)
            }
    
    def batch_process_documents(self, file_paths: List[Path], 
                              enable_ocr: bool = True,
                              detect_language: bool = True) -> List[Dict[str, Any]]:
        """
        Process multiple documents in batch.
        
        Args:
            file_paths: List of document paths
            enable_ocr: Whether to enable OCR
            detect_language: Whether to detect languages
            
        Returns:
            List of processing results
        """
        results = []
        
        for file_path in file_paths:
            try:
                result = self.process_document(file_path, enable_ocr, detect_language)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process document {file_path}: {str(e)}")
                results.append({
                    'error': str(e),
                    'file_path': str(file_path),
                    'success': False
                })
        
        return results