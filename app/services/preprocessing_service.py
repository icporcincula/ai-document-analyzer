"""
Document Preprocessing Service for format enhancement and detection.

This service handles document preprocessing including image enhancement,
text normalization, format standardization, and format detection.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import mimetypes
import hashlib

# Try to import magic for better file detection, fall back to mimetypes if it fails
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logging.warning("python-magic not available, falling back to mimetypes for file detection")

from app.utils.config import get_config
from app.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)


class FormatDetectionService:
    """Service for detecting document formats using multiple methods."""
    
    def __init__(self):
        """Initialize format detection service."""
        self.config = get_config()
        self.supported_formats = {
            'pdf': ['.pdf'],
            'docx': ['.docx', '.doc'],
            'image': ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'],
            'text': ['.txt', '.md', '.rtf']
        }
        
        # MIME type mappings
        self.mime_type_mappings = {
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'image/png': 'image',
            'image/jpeg': 'image',
            'image/bmp': 'image',
            'image/tiff': 'image',
            'text/plain': 'text',
            'text/markdown': 'text'
        }
        
        # Magic number signatures for file format detection
        self.magic_signatures = {
            'pdf': b'%PDF-',
            'docx': b'PK\x03\x04',  # ZIP file signature (DOCX is ZIP-based)
            'png': b'\x89PNG\r\n\x1a\n',
            'jpg': b'\xff\xd8\xff',
            'bmp': b'BM',
            'tiff': [b'II*\x00', b'MM\x00*'],  # Little-endian and big-endian
            'txt': None,  # Text files don't have specific signatures
            'md': None
        }
    
    def detect_format(self, file_path: Path) -> Dict[str, Any]:
        """
        Detect document format using multiple methods.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with format detection results
        """
        try:
            # Get file extension
            file_extension = file_path.suffix.lower()
            
            # Get MIME type
            mime_type = self._get_mime_type(file_path)
            
            # Get magic number signature
            magic_format = self._detect_by_magic_numbers(file_path)
            
            # Determine most likely format
            detected_format = self._determine_format(
                file_extension, mime_type, magic_format
            )
            
            # Get confidence score
            confidence = self._calculate_confidence(
                file_extension, mime_type, magic_format, detected_format
            )
            
            result = {
                'detected_format': detected_format,
                'file_extension': file_extension,
                'mime_type': mime_type,
                'magic_format': magic_format,
                'confidence': confidence,
                'is_supported': detected_format in self.supported_formats,
                'methods': {
                    'extension': file_extension,
                    'mime_type': mime_type,
                    'magic_numbers': magic_format
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Format detection failed for {file_path}: {str(e)}")
            return {
                'detected_format': None,
                'file_extension': file_extension,
                'mime_type': None,
                'magic_format': None,
                'confidence': 0.0,
                'is_supported': False,
                'error': str(e)
            }
    
    def _get_mime_type(self, file_path: Path) -> Optional[str]:
        """
        Get MIME type of file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type string or None
        """
        try:
            # Try using python-magic first for more accurate detection
            with open(file_path, 'rb') as f:
                file_content = f.read(1024)  # Read first 1KB for detection
            
            mime_type = magic.from_buffer(file_content, mime=True)
            return mime_type
            
        except Exception:
            # Fallback to mimetypes
            mime_type, _ = mimetypes.guess_type(str(file_path))
            return mime_type
    
    def _detect_by_magic_numbers(self, file_path: Path) -> Optional[str]:
        """
        Detect format using magic numbers (file signatures).
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected format or None
        """
        try:
            with open(file_path, 'rb') as f:
                file_header = f.read(16)  # Read first 16 bytes
            
            for format_name, signatures in self.magic_signatures.items():
                if signatures is None:
                    continue
                
                if isinstance(signatures, list):
                    # Multiple possible signatures
                    for signature in signatures:
                        if file_header.startswith(signature):
                            return format_name
                else:
                    # Single signature
                    if file_header.startswith(signatures):
                        return format_name
            
            return None
            
        except Exception as e:
            logger.warning(f"Magic number detection failed: {str(e)}")
            return None
    
    def _determine_format(self, extension: str, mime_type: Optional[str], magic_format: Optional[str]) -> Optional[str]:
        """
        Determine the most likely format based on multiple detection methods.
        
        Args:
            extension: File extension
            mime_type: MIME type
            magic_format: Magic number detected format
            
        Returns:
            Most likely format
        """
        # Priority: Magic numbers > MIME type > Extension
        if magic_format and magic_format in self.supported_formats:
            return magic_format
        
        if mime_type and mime_type in self.mime_type_mappings:
            return self.mime_type_mappings[mime_type]
        
        # Check extension
        for format_name, extensions in self.supported_formats.items():
            if extension in extensions:
                return format_name
        
        return None
    
    def _calculate_confidence(self, extension: str, mime_type: Optional[str], 
                            magic_format: Optional[str], detected_format: Optional[str]) -> float:
        """
        Calculate confidence score for format detection.
        
        Args:
            extension: File extension
            mime_type: MIME type
            magic_format: Magic number detected format
            detected_format: Final detected format
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not detected_format:
            return 0.0
        
        confidence = 0.0
        methods_agreeing = 0
        
        # Check magic number confidence
        if magic_format == detected_format:
            confidence += 0.4
            methods_agreeing += 1
        
        # Check MIME type confidence
        expected_mime_types = [k for k, v in self.mime_type_mappings.items() if v == detected_format]
        if mime_type in expected_mime_types:
            confidence += 0.3
            methods_agreeing += 1
        
        # Check extension confidence
        if extension in self.supported_formats.get(detected_format, []):
            confidence += 0.3
            methods_agreeing += 1
        
        # Bonus for all methods agreeing
        if methods_agreeing == 3:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def validate_format_consistency(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate that file format is consistent across detection methods.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Validation results
        """
        detection_result = self.detect_format(file_path)
        
        # Check for inconsistencies
        inconsistencies = []
        
        if detection_result['mime_type'] and detection_result['magic_format']:
            expected_mime = self.mime_type_mappings.get(detection_result['magic_format'])
            if expected_mime and expected_mime != detection_result['mime_type']:
                inconsistencies.append(f"MIME type mismatch: {detection_result['mime_type']} vs {expected_mime}")
        
        if detection_result['file_extension'] and detection_result['detected_format']:
            if detection_result['file_extension'] not in self.supported_formats.get(detection_result['detected_format'], []):
                inconsistencies.append(f"Extension mismatch: {detection_result['file_extension']} not supported for {detection_result['detected_format']}")
        
        return {
            'is_consistent': len(inconsistencies) == 0,
            'inconsistencies': inconsistencies,
            'detection_result': detection_result
        }


class DocumentPreprocessingService:
    """Service for preprocessing documents to improve quality."""
    
    def __init__(self):
        """Initialize preprocessing service."""
        self.config = get_config()
        self.format_detector = FormatDetectionService()
    
    def preprocess_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Preprocess document for optimal processing.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Preprocessing results
        """
        try:
            # Detect format
            format_result = self.format_detector.detect_format(file_path)
            
            if not format_result['is_supported']:
                raise DocumentProcessingError(f"Unsupported document format: {file_path.suffix}")
            
            # Get file hash for integrity
            file_hash = self._calculate_file_hash(file_path)
            
            # Get file size
            file_size = file_path.stat().st_size
            
            # Check file size limits
            max_size = self._get_max_size_for_format(format_result['detected_format'])
            if file_size > max_size:
                raise DocumentProcessingError(f"File too large: {file_size} bytes (max: {max_size})")
            
            result = {
                'original_path': str(file_path),
                'detected_format': format_result['detected_format'],
                'file_size': file_size,
                'file_hash': file_hash,
                'format_confidence': format_result['confidence'],
                'is_format_consistent': self._check_format_consistency(format_result),
                'preprocessing_needed': self._needs_preprocessing(format_result['detected_format'], file_size),
                'suggested_service': self._get_suggested_service(format_result['detected_format'])
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Document preprocessing failed: {str(e)}")
            raise DocumentProcessingError(f"Document preprocessing failed: {str(e)}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of file for integrity checking.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash string
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to calculate file hash: {str(e)}")
            return ""
    
    def _get_max_size_for_format(self, format_type: str) -> int:
        """
        Get maximum allowed file size for a format.
        
        Args:
            format_type: Document format type
            
        Returns:
            Maximum file size in bytes
        """
        size_limits = {
            'pdf': self.config.pdf_max_file_size,
            'docx': self.config.docx_max_file_size,
            'image': self.config.image_max_file_size,
            'text': self.config.text_max_file_size
        }
        
        return size_limits.get(format_type, 10 * 1024 * 1024)  # Default 10MB
    
    def _check_format_consistency(self, format_result: Dict[str, Any]) -> bool:
        """
        Check if format detection methods are consistent.
        
        Args:
            format_result: Format detection result
            
        Returns:
            True if consistent, False otherwise
        """
        return format_result['confidence'] >= 0.8
    
    def _needs_preprocessing(self, format_type: str, file_size: int) -> bool:
        """
        Determine if document needs preprocessing.
        
        Args:
            format_type: Document format
            file_size: File size in bytes
            
        Returns:
            True if preprocessing is needed
        """
        # Large files or low-confidence detections may need preprocessing
        if file_size > 5 * 1024 * 1024:  # 5MB
            return True
        
        return False
    
    def _get_suggested_service(self, format_type: str) -> str:
        """
        Get suggested service for processing the format.
        
        Args:
            format_type: Document format
            
        Returns:
            Suggested service name
        """
        service_mapping = {
            'pdf': 'pdf_service',
            'docx': 'docx_service', 
            'image': 'image_service',
            'text': 'text_service'
        }
        
        return service_mapping.get(format_type, 'generic_service')
    
    def batch_preprocess_documents(self, file_paths: List[Path]) -> List[Dict[str, Any]]:
        """
        Preprocess multiple documents in batch.
        
        Args:
            file_paths: List of document paths
            
        Returns:
            List of preprocessing results
        """
        results = []
        
        for file_path in file_paths:
            try:
                result = self.preprocess_document(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to preprocess document {file_path}: {str(e)}")
                results.append({
                    'error': str(e),
                    'file_path': str(file_path),
                    'success': False
                })
        
        return results