import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from app.services.pdf_service import PDFService, PDFValidationError
from app.models.schemas import DocumentType


class TestPDFService:
    """Test cases for PDFService"""

    @pytest.fixture
    def pdf_service(self):
        """Create PDFService instance for testing"""
        return PDFService()

    @pytest.fixture
    def mock_pdf_file(self):
        """Create a mock PDF file for testing"""
        mock_file = Mock()
        mock_file.filename = "test.pdf"
        mock_file.file = Mock()
        return mock_file

    @pytest.fixture
    def sample_text_content(self):
        """Sample text content for PDF testing"""
        return "This is a test PDF document with some content for testing purposes."

    @patch('app.services.pdf_service.PyPDF2.PdfReader')
    def test_validate_pdf_valid_file(self, mock_pdf_reader, pdf_service, mock_pdf_file):
        """Test PDF validation with a valid file"""
        # Setup mock
        mock_reader = Mock()
        mock_reader.pages = [Mock(), Mock()]  # 2 pages
        mock_pdf_reader.return_value = mock_reader
        
        # Test
        result = pdf_service.validate_pdf(mock_pdf_file)
        
        # Assertions
        assert result is True
        mock_pdf_reader.assert_called_once()

    @patch('app.services.pdf_service.PyPDF2.PdfReader')
    def test_validate_pdf_empty_file(self, mock_pdf_reader, pdf_service, mock_pdf_file):
        """Test PDF validation with empty file"""
        # Setup mock
        mock_reader = Mock()
        mock_reader.pages = []  # Empty PDF
        mock_pdf_reader.return_value = mock_reader
        
        # Test and assert
        with pytest.raises(PDFValidationError, match="PDF file is empty"):
            pdf_service.validate_pdf(mock_pdf_file)

    @patch('app.services.pdf_service.PyPDF2.PdfReader')
    def test_validate_pdf_too_many_pages(self, mock_pdf_reader, pdf_service, mock_pdf_file):
        """Test PDF validation with too many pages"""
        # Setup mock
        mock_reader = Mock()
        mock_reader.pages = [Mock()] * 51  # 51 pages (over limit)
        mock_pdf_reader.return_value = mock_reader
        
        # Test and assert
        with pytest.raises(PDFValidationError, match="PDF exceeds maximum page limit"):
            pdf_service.validate_pdf(mock_pdf_file)

    @patch('app.services.pdf_service.PyPDF2.PdfReader')
    def test_validate_pdf_corrupted_file(self, mock_pdf_reader, pdf_service, mock_pdf_file):
        """Test PDF validation with corrupted file"""
        # Setup mock to raise exception
        mock_pdf_reader.side_effect = Exception("Corrupted PDF")
        
        # Test and assert
        with pytest.raises(PDFValidationError, match="Invalid PDF file"):
            pdf_service.validate_pdf(mock_pdf_file)

    @patch('app.services.pdf_service.PyPDF2.PdfReader')
    def test_extract_text_from_pdf_direct(self, mock_pdf_reader, pdf_service, mock_pdf_file, sample_text_content):
        """Test direct text extraction from PDF"""
        # Setup mock
        mock_page = Mock()
        mock_page.extract_text.return_value = sample_text_content
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        # Test
        result = pdf_service.extract_text_from_pdf(mock_pdf_file)
        
        # Assertions
        assert result == sample_text_content
        mock_page.extract_text.assert_called_once()

    @patch('app.services.pdf_service.pytesseract.image_to_string')
    @patch('app.services.pdf_service.convert_from_path')
    @patch('app.services.pdf_service.PyPDF2.PdfReader')
    def test_extract_text_from_pdf_ocr(self, mock_pdf_reader, mock_convert, mock_tesseract, pdf_service, mock_pdf_file, sample_text_content):
        """Test OCR text extraction from scanned PDF"""
        # Setup mocks
        mock_reader = Mock()
        mock_reader.pages = [Mock()]  # 1 page
        mock_pdf_reader.return_value = mock_reader
        
        mock_image = Mock()
        mock_convert.return_value = [mock_image]
        mock_tesseract.return_value = sample_text_content
        
        # Test
        result = pdf_service.extract_text_from_pdf(mock_pdf_file)
        
        # Assertions
        assert result == sample_text_content
        mock_convert.assert_called_once()
        mock_tesseract.assert_called_once_with(mock_image)

    @patch('app.services.pdf_service.PyPDF2.PdfReader')
    def test_extract_text_from_pdf_empty_content(self, mock_pdf_reader, pdf_service, mock_pdf_file):
        """Test text extraction with empty content"""
        # Setup mock
        mock_page = Mock()
        mock_page.extract_text.return_value = ""
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        # Test and assert
        with pytest.raises(PDFValidationError, match="No text content found in PDF"):
            pdf_service.extract_text_from_pdf(mock_pdf_file)

    @patch('app.services.pdf_service.PyPDF2.PdfReader')
    def test_extract_text_from_pdf_corrupted(self, mock_pdf_reader, pdf_service, mock_pdf_file):
        """Test text extraction with corrupted PDF"""
        # Setup mock to raise exception
        mock_pdf_reader.side_effect = Exception("Corrupted PDF")
        
        # Test and assert
        with pytest.raises(PDFValidationError, match="Failed to extract text from PDF"):
            pdf_service.extract_text_from_pdf(mock_pdf_file)

    def test_validate_file_size_within_limit(self, pdf_service):
        """Test file size validation within limit"""
        # Create a temporary file within size limit
        test_file = Mock()
        test_file.file = Mock()
        test_file.file.seek = Mock()
        test_file.file.tell = Mock(return_value=1000000)  # 1MB
        test_file.file.seek.return_value = None
        
        # Test
        result = pdf_service.validate_file_size(test_file)
        
        # Assertions
        assert result is True
        test_file.file.seek.assert_called_with(0, 2)  # Seek to end
        test_file.file.tell.assert_called_once()

    def test_validate_file_size_exceeds_limit(self, pdf_service):
        """Test file size validation exceeding limit"""
        # Create a temporary file exceeding size limit
        test_file = Mock()
        test_file.file = Mock()
        test_file.file.seek = Mock()
        test_file.file.tell = Mock(return_value=11000000)  # 11MB
        test_file.file.seek.return_value = None
        
        # Test and assert
        with pytest.raises(PDFValidationError, match="File size exceeds"):
            pdf_service.validate_file_size(test_file)

    def test_validate_page_count_within_limit(self, pdf_service):
        """Test page count validation within limit"""
        # Test with valid page count
        result = pdf_service.validate_page_count(10)
        assert result is True
        
        result = pdf_service.validate_page_count(50)
        assert result is True

    def test_validate_page_count_exceeds_limit(self, pdf_service):
        """Test page count validation exceeding limit"""
        # Test with page count exceeding limit
        with pytest.raises(PDFValidationError, match="PDF exceeds maximum page limit"):
            pdf_service.validate_page_count(51)

    def test_validate_page_count_zero(self, pdf_service):
        """Test page count validation with zero pages"""
        # Test with zero pages
        with pytest.raises(PDFValidationError, match="PDF file is empty"):
            pdf_service.validate_page_count(0)

    @patch('app.services.pdf_service.PyPDF2.PdfReader')
    def test_get_page_count(self, mock_pdf_reader, pdf_service, mock_pdf_file):
        """Test getting page count from PDF"""
        # Setup mock
        mock_reader = Mock()
        mock_reader.pages = [Mock(), Mock(), Mock()]  # 3 pages
        mock_pdf_reader.return_value = mock_reader
        
        # Test
        result = pdf_service.get_page_count(mock_pdf_file)
        
        # Assertions
        assert result == 3
        mock_pdf_reader.assert_called_once()

    @patch('app.services.pdf_service.PyPDF2.PdfReader')
    def test_get_page_count_corrupted(self, mock_pdf_reader, pdf_service, mock_pdf_file):
        """Test getting page count from corrupted PDF"""
        # Setup mock to raise exception
        mock_pdf_reader.side_effect = Exception("Corrupted PDF")
        
        # Test and assert
        with pytest.raises(PDFValidationError, match="Failed to read PDF file"):
            pdf_service.get_page_count(mock_pdf_file)

    def test_is_scanned_pdf_true(self, pdf_service, sample_text_content):
        """Test detection of scanned PDF"""
        # Test with content that looks like scanned text
        scanned_content = " " * 1000  # Mostly whitespace
        result = pdf_service.is_scanned_pdf(scanned_content)
        assert result is True

    def test_is_scanned_pdf_false(self, pdf_service, sample_text_content):
        """Test detection of text-based PDF"""
        # Test with normal text content
        result = pdf_service.is_scanned_pdf(sample_text_content)
        assert result is False

    def test_is_scanned_pdf_short_content(self, pdf_service):
        """Test scanned PDF detection with short content"""
        # Test with short content
        short_content = "Short text"
        result = pdf_service.is_scanned_pdf(short_content)
        assert result is False

    def test_is_scanned_pdf_empty_content(self, pdf_service):
        """Test scanned PDF detection with empty content"""
        # Test with empty content
        result = pdf_service.is_scanned_pdf("")
        assert result is False

    @patch('app.services.pdf_service.PyPDF2.PdfReader')
    def test_extract_text_with_page_limit(self, mock_pdf_reader, pdf_service, mock_pdf_file, sample_text_content):
        """Test text extraction with page limit"""
        # Setup mock with multiple pages
        mock_pages = []
        for i in range(3):
            mock_page = Mock()
            mock_page.extract_text.return_value = f"Page {i+1} content"
            mock_pages.append(mock_page)
        
        mock_reader = Mock()
        mock_reader.pages = mock_pages
        mock_pdf_reader.return_value = mock_reader
        
        # Test with page limit
        result = pdf_service.extract_text_from_pdf(mock_pdf_file, max_pages=2)
        
        # Assertions
        assert "Page 1 content" in result
        assert "Page 2 content" in result
        assert "Page 3 content" not in result
        assert mock_pages[0].extract_text.called
        assert mock_pages[1].extract_text.called
        assert not mock_pages[2].extract_text.called

    def test_validate_file_size_zero_bytes(self, pdf_service):
        """Test file size validation with zero bytes"""
        # Create a temporary file with zero size
        test_file = Mock()
        test_file.file = Mock()
        test_file.file.seek = Mock()
        test_file.file.tell = Mock(return_value=0)
        test_file.file.seek.return_value = None
        
        # Test and assert
        with pytest.raises(PDFValidationError, match="File size exceeds"):
            pdf_service.validate_file_size(test_file)

    def test_validate_file_size_negative(self, pdf_service):
        """Test file size validation with negative size"""
        # Create a temporary file with negative size (edge case)
        test_file = Mock()
        test_file.file = Mock()
        test_file.file.seek = Mock()
        test_file.file.tell = Mock(return_value=-1)
        test_file.file.seek.return_value = None
        
        # Test and assert
        with pytest.raises(PDFValidationError, match="File size exceeds"):
            pdf_service.validate_file_size(test_file)