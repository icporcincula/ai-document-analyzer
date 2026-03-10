"""
Tests for Language Detection Service
"""
import pytest
from unittest.mock import Mock, patch

from app.services.language_detection import LanguageDetectionService
from app.exceptions import DocumentProcessingError


class TestLanguageDetectionService:
    """Test cases for Language Detection service functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = LanguageDetectionService()
        
    def test_detect_language_english(self):
        """Test language detection for English text"""
        text = "This is a sample English text for testing language detection."
        
        result = self.service.detect_language(text)
        
        assert result['success'] is True
        assert result['detected_language'] == 'en'
        assert result['language_name'] == 'English'
        assert result['confidence'] > 0.8
        assert 'all_languages' in result
    
    def test_detect_language_spanish(self):
        """Test language detection for Spanish text"""
        text = "Este es un texto en español para probar la detección de idioma."
        
        result = self.service.detect_language(text)
        
        assert result['success'] is True
        assert result['detected_language'] == 'es'
        assert result['language_name'] == 'Spanish'
        assert result['confidence'] > 0.8
    
    def test_detect_language_german(self):
        """Test language detection for German text"""
        text = "Dies ist ein deutscher Text zur Überprüfung der Spracherkennung."
        
        result = self.service.detect_language(text)
        
        assert result['success'] is True
        assert result['detected_language'] == 'de'
        assert result['language_name'] == 'German'
        assert result['confidence'] > 0.8
    
    def test_detect_language_empty_text(self):
        """Test language detection with empty text"""
        result = self.service.detect_language("")
        
        assert result['success'] is False
        assert result['error'] == 'Empty text provided'
        assert result['detected_language'] is None
        assert result['confidence'] == 0.0
    
    def test_detect_language_short_text(self):
        """Test language detection with very short text"""
        result = self.service.detect_language("Hi")
        
        assert result['success'] is False
        assert 'confidence too low' in result['error']
    
    def test_detect_language_invalid_text(self):
        """Test language detection with invalid text"""
        result = self.service.detect_language(None)
        
        assert result['success'] is False
        assert result['error'] is not None
    
    def test_detect_language_batch(self):
        """Test batch language detection"""
        texts = [
            "This is English text",
            "Este es texto en español",
            "Dies ist deutscher Text"
        ]
        
        results = self.service.detect_language_batch(texts)
        
        assert len(results) == 3
        assert results[0]['detected_language'] == 'en'
        assert results[1]['detected_language'] == 'es'
        assert results[2]['detected_language'] == 'de'
    
    def test_detect_mixed_language(self):
        """Test detection of mixed language content"""
        text = "This is English with some español words mixed in."
        
        result = self.service.detect_mixed_language(text)
        
        assert 'is_mixed' in result
        assert 'primary_language' in result
        assert 'secondary_languages' in result
        assert 'language_distribution' in result
    
    def test_validate_language_support(self):
        """Test language support validation"""
        assert self.service.validate_language_support('en') is True
        assert self.service.validate_language_support('es') is True
        assert self.service.validate_language_support('fr') is True
        assert self.service.validate_language_support('xx') is False
    
    def test_get_supported_languages(self):
        """Test getting list of supported languages"""
        languages = self.service.get_supported_languages()
        
        assert isinstance(languages, dict)
        assert 'en' in languages
        assert 'es' in languages
        assert 'de' in languages
        assert languages['en'] == 'English'
        assert languages['es'] == 'Spanish'
    
    def test_get_language_name(self):
        """Test getting language name from code"""
        assert self.service.get_language_name('en') == 'English'
        assert self.service.get_language_name('es') == 'Spanish'
        assert self.service.get_language_name('xx') == 'Unknown'
    
    def test_filter_supported_languages(self):
        """Test filtering languages to only supported ones"""
        languages = [('en', 0.9), ('xx', 0.8), ('es', 0.7)]
        
        filtered = self.service.filter_supported_languages(languages)
        
        assert len(filtered) == 2
        assert ('en', 0.9) in filtered
        assert ('es', 0.7) in filtered
        assert ('xx', 0.8) not in filtered
    
    def test_preprocess_text(self):
        """Test text preprocessing"""
        text = "  This is a test text with   extra spaces.  "
        
        processed = self.service._preprocess_text(text)
        
        assert processed == "This is a test text with extra spaces."
        assert not processed.startswith(' ')
        assert not processed.endswith(' ')
    
    def test_preprocess_text_long(self):
        """Test text preprocessing with long text"""
        long_text = "A" * 20000  # Longer than max_text_length
        
        processed = self.service._preprocess_text(long_text)
        
        assert len(processed) <= self.service.max_text_length
    
    def test_preprocess_text_special_chars(self):
        """Test text preprocessing with special characters"""
        text = "Test text with @#$% special chars!"
        
        processed = self.service._preprocess_text(text)
        
        # Should preserve alphanumeric, spaces, and basic punctuation
        assert 'Test' in processed
        assert 'text' in processed
        assert 'special' in processed
        assert 'chars' in processed
    
    def test_get_statistics(self):
        """Test getting service statistics"""
        stats = self.service.get_statistics()
        
        assert 'total_entities' in stats
        assert 'enabled_entities' in stats
        assert 'disabled_entities' in stats
        assert 'entity_names' in stats
        assert isinstance(stats['total_entities'], int)
        assert isinstance(stats['entity_names'], list)