"""
Image Service for text extraction from image files.

This service handles image file processing including OCR, preprocessing,
and format support for various image types.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

from app.utils.config import get_config
from app.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)


class ImageService:
    """Service for extracting text from image files using OCR."""
    
    def __init__(self):
        """Initialize image service with configuration."""
        self.config = get_config()
        self.max_file_size = self.config.image.max_file_size
        self.supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
        self.ocr_config = self.config.image.ocr_config
        
    def validate_image_file(self, file_path: Path) -> bool:
        """
        Validate image file for processing.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            True if file is valid, False otherwise
            
        Raises:
            DocumentProcessingError: If file validation fails
        """
        try:
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                raise DocumentProcessingError(
                    f"Image file too large: {file_size} bytes (max: {self.max_file_size})"
                )
            
            # Check file extension
            if file_path.suffix.lower() not in self.supported_extensions:
                raise DocumentProcessingError(
                    f"Unsupported image extension: {file_path.suffix}"
                )
            
            # Try to open the image
            try:
                with Image.open(file_path) as img:
                    # Basic validation
                    if img.size[0] == 0 or img.size[1] == 0:
                        raise DocumentProcessingError("Image has zero dimensions")
                    
                    # Check if image is corrupted
                    img.verify()
                    
            except Exception as e:
                raise DocumentProcessingError(f"Failed to open image file: {str(e)}")
                
            return True
            
        except OSError as e:
            raise DocumentProcessingError(f"File system error: {str(e)}")
        except Exception as e:
            raise DocumentProcessingError(f"Unexpected error during image validation: {str(e)}")
    
    def preprocess_image(self, image_path: Path) -> np.ndarray:
        """
        Preprocess image for better OCR results.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed image as numpy array
        """
        try:
            # Load image using OpenCV
            image = cv2.imread(str(image_path))
            if image is None:
                raise DocumentProcessingError("Failed to load image")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply preprocessing based on configuration
            if self.ocr_config.get('enhance_contrast', True):
                # Enhance contrast
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gray = clahe.apply(gray)
            
            if self.ocr_config.get('denoise', True):
                # Denoise
                gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            if self.ocr_config.get('threshold', True):
                # Apply threshold
                _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Handle rotation and skew correction
            if self.ocr_config.get('correct_rotation', True):
                gray = self._correct_image_rotation(gray)
            
            # Enhance image quality
            if self.ocr_config.get('enhance_quality', True):
                gray = self._enhance_image_quality(gray)
            
            return gray
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {str(e)}")
            raise DocumentProcessingError(f"Image preprocessing failed: {str(e)}")
    
    def _correct_image_rotation(self, image: np.ndarray) -> np.ndarray:
        """
        Correct image rotation and skew.
        
        Args:
            image: Input image
            
        Returns:
            Corrected image
        """
        try:
            # Find contours
            contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return image
            
            # Get the largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Get minimum area rectangle
            rect = cv2.minAreaRect(largest_contour)
            angle = rect[2]
            
            # Adjust angle
            if angle < -45:
                angle = 90 + angle
            
            # Rotate image
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            corrected = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            
            return corrected
            
        except Exception as e:
            logger.warning(f"Rotation correction failed: {str(e)}")
            return image
    
    def _enhance_image_quality(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image quality for better OCR.
        
        Args:
            image: Input image
            
        Returns:
            Enhanced image
        """
        try:
            # Convert to PIL for enhancement
            pil_image = Image.fromarray(image)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(pil_image)
            pil_image = enhancer.enhance(1.5)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(pil_image)
            pil_image = enhancer.enhance(1.5)
            
            # Convert back to numpy
            enhanced = np.array(pil_image)
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Image enhancement failed: {str(e)}")
            return image
    
    def extract_text_from_image(self, image_path: Path) -> Dict[str, Any]:
        """
        Extract text from image using OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            logger.info(f"Processing image file: {image_path}")
            
            # Validate file
            self.validate_image_file(image_path)
            
            # Preprocess image
            processed_image = self.preprocess_image(image_path)
            
            # Configure OCR
            ocr_config_str = self._build_ocr_config()
            
            # Extract text
            text = pytesseract.image_to_string(processed_image, config=ocr_config_str)
            
            # Get confidence scores if available
            try:
                data = pytesseract.image_to_data(processed_image, config=ocr_config_str, output_type=pytesseract.Output.DICT)
                confidence = [conf for conf in data['conf'] if conf > 0]
                avg_confidence = sum(confidence) / len(confidence) if confidence else 0
            except:
                avg_confidence = 0
            
            # Get image metadata
            with Image.open(image_path) as img:
                metadata = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode
                }
            
            result = {
                'full_text': text.strip(),
                'avg_confidence': avg_confidence,
                'image_metadata': metadata,
                'file_path': str(image_path),
                'file_size': image_path.stat().st_size,
                'format': 'image',
                'text_length': len(text.strip())
            }
            
            logger.info(f"Successfully processed image file: {image_path}")
            return result
            
        except DocumentProcessingError:
            raise
        except Exception as e:
            logger.error(f"Failed to process image file {image_path}: {str(e)}")
            raise DocumentProcessingError(f"Image processing failed: {str(e)}")
    
    def _build_ocr_config(self) -> str:
        """
        Build OCR configuration string.
        
        Returns:
            OCR configuration string
        """
        config_parts = []
        
        # Page segmentation mode
        psm = self.ocr_config.get('psm', 6)
        config_parts.append(f"--psm {psm}")
        
        # OCR engine mode
        oem = self.ocr_config.get('oem', 3)
        config_parts.append(f"--oem {oem}")
        
        # Language
        lang = self.ocr_config.get('lang', 'eng')
        config_parts.append(f"-l {lang}")
        
        # Additional parameters
        if self.ocr_config.get('preserve_interword_spaces', True):
            config_parts.append("--preserve_interword_spaces 1")
        
        if self.ocr_config.get('dpi', 300):
            config_parts.append(f"-c tessedit_write_images=true")
        
        return ' '.join(config_parts)
    
    def get_image_metadata(self, image_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing image metadata
        """
        try:
            with Image.open(image_path) as img:
                metadata = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'info': dict(img.info) if img.info else {}
                }
                
                # Try to get EXIF data
                try:
                    exif = img._getexif()
                    if exif:
                        metadata['exif'] = exif
                except:
                    pass
                
                return metadata
                
        except Exception as e:
            logger.warning(f"Failed to extract image metadata: {str(e)}")
            return {}
    
    def batch_process_images(self, image_paths: List[Path]) -> List[Dict[str, Any]]:
        """
        Process multiple images in batch.
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            List of processed image results
        """
        results = []
        
        for image_path in image_paths:
            try:
                result = self.extract_text_from_image(image_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process image {image_path}: {str(e)}")
                results.append({
                    'error': str(e),
                    'file_path': str(image_path),
                    'success': False
                })
        
        return results