# app/services/pdf_service.py
from pypdf import PdfReader
import pytesseract
from pdf2image import convert_from_bytes
from io import BytesIO
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_PAGES = 50


class PDFService:
    """Service for PDF text extraction"""

    @staticmethod
    def validate(pdf_bytes: bytes) -> None:
        """
        Validate PDF file size, page count, and security before processing.
        Raises ValueError with a descriptive message on failure.
        """
        # Check file size (max 10 MB)
        if len(pdf_bytes) > MAX_FILE_SIZE:
            raise ValueError(
                f"File too large ({len(pdf_bytes) / 1024 / 1024:.1f} MB). "
                f"Maximum allowed size is {MAX_FILE_SIZE // (1024 * 1024)} MB."
            )

        # Check for malicious content indicators
        PDFService._check_malicious_content(pdf_bytes)

        pdf_file = BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        num_pages = len(reader.pages)

        if num_pages > MAX_PAGES:
            raise ValueError(
                f"Document has {num_pages} pages. "
                f"Maximum allowed is {MAX_PAGES} pages."
            )

        # Additional security checks
        PDFService._check_suspicious_pdf_features(reader)

    @staticmethod
    def extract_text(pdf_bytes: bytes, enable_ocr: bool = True) -> Tuple[str, str]:
        """
        Extract text from PDF.

        Returns:
            Tuple of (extracted_text, source)
            source is either "text" or "ocr"
        """
        try:
            # First, try direct text extraction
            text = PDFService._extract_text_direct(pdf_bytes)

            if text and len(text.strip()) > 50:
                logger.info("Text extracted directly from PDF")
                return text, "text"

            # If no text or very little text, try OCR
            if enable_ocr:
                logger.info("Attempting OCR extraction")
                text = PDFService._extract_text_ocr(pdf_bytes)
                return text, "ocr"

            return text, "text"

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise

    @staticmethod
    def _extract_text_direct(pdf_bytes: bytes) -> str:
        """Extract text directly from PDF using pypdf"""
        pdf_file = BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)

        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")

        return "\n".join(text_parts)

    @staticmethod
    def _check_malicious_content(pdf_bytes: bytes):
        """Check for potential malicious content in PDF bytes"""
        # Check for JavaScript in PDF (potential security risk)
        js_indicators = [
            b'/JavaScript',
            b'/JS',
            b'eval(',
            b'alert(',
            b'document.',
            b'window.'
        ]
        
        pdf_content = pdf_bytes.lower()
        for indicator in js_indicators:
            if indicator in pdf_content:
                raise ValueError("PDF contains potentially malicious content (JavaScript)")
        
        # Check for excessive object count (potential DoS)
        if pdf_bytes.count(b'obj') > 10000:
            raise ValueError("PDF contains too many objects, possible malformed file")

    @staticmethod
    def _check_suspicious_pdf_features(reader):
        """Check for suspicious PDF features"""
        # Check for embedded files (potential security risk)
        if hasattr(reader, '_list_attachments') and len(reader._list_attachments()) > 0:
            raise ValueError("PDFs with embedded files are not supported")
        
        # Check for excessive form fields (potential DoS)
        if hasattr(reader, 'get_fields') and reader.get_fields() and len(reader.get_fields()) > 100:
            raise ValueError("PDF contains too many form fields")

    @staticmethod
    def _extract_text_ocr(pdf_bytes: bytes) -> str:
        """Extract text using OCR"""
        images = convert_from_bytes(pdf_bytes)

        text_parts = []
        for i, image in enumerate(images):
            logger.info(f"Processing page {i + 1}/{len(images)} with OCR")
            text = pytesseract.image_to_string(image)
            text_parts.append(text)

        return "\n".join(text_parts)