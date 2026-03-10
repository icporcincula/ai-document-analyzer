"""
Tests for Image Service
"""
import pytest
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch, MagicMock
import cv2
import numpy as np
from PIL import Image

from app.services.image_service import ImageService
from app.exceptions import DocumentProcessingError


class TestImageService:
    """Test cases for Image service functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = ImageService()
        
    def test_validate_image_file_valid(self):
        """Test validation of valid image file"""
        # Create a temporary PNG file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            # Create a simple image
            img = Image.new('RGB', (100, 100), color='red')
            img.save(temp_file.name, 'PNG')
            
            try:
                # Should not raise an exception
                result = self.service.validate_image_file(Path(temp_file.name))
                assert result is True
            finally:
                Path(temp_file.name).unlink()
    
    def test_validate_image_file_invalid_extension(self):
        """Test validation of file with invalid extension"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file.flush()
            
            try:
                with pytest.raises(DocumentProcessingError, match="Unsupported image extension"):
                    self.service.validate_image_file(Path(temp_file.name))
            finally:
                Path(temp_file.name).unlink()
    
    def test_validate_image_file_too_large(self):
        """Test validation of file that's too large"""
        # Mock the config to have a small max file size
        with patch.object(self.service, 'max_file_size', 100):
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                # Create a file larger than the limit
                img = Image.new('RGB', (1000, 1000), color='red')
                img.save(temp_file.name, 'PNG')
                
                try:
                    with pytest.raises(DocumentProcessingError, match="Image file too large"):
                        self.service.validate_image_file(Path(temp_file.name))
                finally:
                    Path(temp_file.name).unlink()
    
    def test_validate_image_file_corrupted(self):
        """Test validation of corrupted image file"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_file.write(b"invalid image data")
            temp_file.flush()
            
            try:
                with pytest.raises(DocumentProcessingError, match="Failed to open image file"):
                    self.service.validate_image_file(Path(temp_file.name))
            finally:
                Path(temp_file.name).unlink()
    
    @patch('app.services.image_service.cv2.imread')
    @patch('app.services.image_service.cv2.cvtColor')
    @patch('app.services.image_service.cv2.threshold')
    @patch('app.services.image_service.pytesseract.image_to_string')
    def test_extract_text_from_image_success(self, mock_tesseract, mock_threshold, mock_cvtColor, mock_imread):
        """Test successful text extraction from image"""
        # Mock image loading
        mock_image = np.array([[1, 2], [3, 4]], dtype=np.uint8)
        mock_imread.return_value = mock_image
        
        # Mock color conversion
        mock_gray = np.array([[100, 150], [200, 255]], dtype=np.uint8)
        mock_cvtColor.return_value = mock_gray
        
        # Mock threshold
        mock_threshold.return_value = (0, mock_gray)
        
        # Mock OCR
        mock_tesseract.return_value = "Extracted text"
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            # Create a simple image
            img = Image.new('RGB', (100, 100), color='white')
            img.save(temp_file.name, 'PNG')
            
            try:
                result = self.service.extract_text_from_image(Path(temp_file.name))
                
                assert 'full_text' in result
                assert result['full_text'] == "Extracted text"
                assert 'format' in result
                assert result['format'] == 'image'
                assert 'image_metadata' in result
                
            finally:
                Path(temp_file.name).unlink()
    
    def test_extract_text_from_image_invalid_file(self):
        """Test text extraction from invalid image file"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file.flush()
            
            try:
                with pytest.raises(DocumentProcessingError, match="Image processing failed"):
                    self.service.extract_text_from_image(Path(temp_file.name))
            finally:
                Path(temp_file.name).unlink()
    
    def test_get_image_metadata(self):
        """Test image metadata extraction"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            # Create a simple image
            img = Image.new('RGB', (200, 150), color='blue')
            img.save(temp_file.name, 'PNG')
            
            try:
                metadata = self.service.get_image_metadata(Path(temp_file.name))
                
                assert 'width' in metadata
                assert 'height' in metadata
                assert 'format' in metadata
                assert metadata['width'] == 200
                assert metadata['height'] == 150
                assert metadata['format'] == 'PNG'
                
            finally:
                Path(temp_file.name).unlink()
    
    def test_batch_process_images(self):
        """Test batch processing of multiple images"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test images
            image_paths = []
            for i in range(2):
                temp_file = Path(temp_dir) / f"test_{i}.png"
                img = Image.new('RGB', (100, 100), color='red')
                img.save(str(temp_file), 'PNG')
                image_paths.append(temp_file)
            
            results = self.service.batch_process_images(image_paths)
            
            assert len(results) == 2
            for result in results:
                assert 'full_text' in result
                assert 'format' in result
                assert result['format'] == 'image'
    
    def test_build_ocr_config(self):
        """Test OCR configuration building"""
        config_str = self.service._build_ocr_config()
        
        assert "--psm" in config_str
        assert "--oem" in config_str
        assert "-l" in config_str
        assert "eng" in config_str
    
    @patch('app.services.image_service.cv2.imread')
    def test_preprocess_image_success(self, mock_imread):
        """Test successful image preprocessing"""
        # Mock image loading
        mock_image = np.array([[1, 2], [3, 4]], dtype=np.uint8)
        mock_imread.return_value = mock_image
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            # Create a simple image
            img = Image.new('RGB', (100, 100), color='white')
            img.save(temp_file.name, 'PNG')
            
            try:
                result = self.service.preprocess_image(Path(temp_file.name))
                
                # Should return a numpy array
                assert isinstance(result, np.ndarray)
                
            finally:
                Path(temp_file.name).unlink()
    
    def test_preprocess_image_invalid_file(self):
        """Test preprocessing of invalid image file"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file.flush()
            
            try:
                with pytest.raises(DocumentProcessingError, match="Image preprocessing failed"):
                    self.service.preprocess_image(Path(temp_file.name))
            finally:
                Path(temp_file.name).unlink()