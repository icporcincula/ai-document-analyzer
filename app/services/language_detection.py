"""
Language Detection Service for identifying document languages.

This service uses langdetect to identify the language of text content
and provides confidence scoring for language detection.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from langdetect import detect, detect_langs, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

from app.utils.config import get_config
from app.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)

# Set seed for consistent results
DetectorFactory.seed = 0

# Supported languages mapping
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'de': 'German', 
    'es': 'Spanish',
    'fr': 'French',
    'it': 'Italian',
    'pt': 'Portuguese',
    'nl': 'Dutch',
    'ru': 'Russian',
    'ja': 'Japanese',
    'zh': 'Chinese',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'ko': 'Korean',
    'tr': 'Turkish',
    'pl': 'Polish',
    'sv': 'Swedish',
    'da': 'Danish',
    'no': 'Norwegian',
    'fi': 'Finnish',
    'cs': 'Czech',
    'sk': 'Slovak',
    'hu': 'Hungarian',
    'ro': 'Romanian',
    'bg': 'Bulgarian',
    'hr': 'Croatian',
    'sr': 'Serbian',
    'el': 'Greek',
    'th': 'Thai',
    'vi': 'Vietnamese',
    'id': 'Indonesian',
    'ms': 'Malay',
    'tl': 'Tagalog',
    'sw': 'Swahili',
    'am': 'Amharic',
    'he': 'Hebrew',
    'fa': 'Persian',
    'ur': 'Urdu',
    'bn': 'Bengali',
    'ta': 'Tamil',
    'te': 'Telugu',
    'ml': 'Malayalam',
    'kn': 'Kannada',
    'gu': 'Gujarati',
    'pa': 'Punjabi',
    'or': 'Odia',
    'as': 'Assamese',
    'my': 'Myanmar',
    'km': 'Khmer',
    'lo': 'Lao',
    'ka': 'Georgian',
    'hy': 'Armenian',
    'eu': 'Basque',
    'ca': 'Catalan',
    'gl': 'Galician',
    'eu': 'Basque',
    'is': 'Icelandic',
    'mt': 'Maltese',
    'et': 'Estonian',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
    'sl': 'Slovenian',
    'mk': 'Macedonian',
    'cy': 'Welsh',
    'ga': 'Irish',
    'gd': 'Scottish Gaelic',
    'br': 'Breton',
    'fo': 'Faroese',
    'ht': 'Haitian Creole',
    'sq': 'Albanian',
    'la': 'Latin',
    'lv': 'Latvian'
}


class LanguageDetectionService:
    """Service for detecting languages in text content."""
    
    def __init__(self):
        """Initialize language detection service."""
        self.config = get_config()
        self.min_confidence = self.config.language.min_confidence
        self.max_text_length = self.config.language.max_text_length
        self.supported_languages = set(SUPPORTED_LANGUAGES.keys())
        
    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the primary language of text with confidence scoring.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with language detection results
        """
        try:
            # Preprocess text
            clean_text = self._preprocess_text(text)
            
            if not clean_text:
                return {
                    'detected_language': None,
                    'language_name': None,
                    'confidence': 0.0,
                    'all_languages': [],
                    'success': False,
                    'error': 'Empty text provided'
                }
            
            # Detect language
            detected_lang = detect(clean_text)
            confidence = self._get_confidence(clean_text, detected_lang)
            
            # Get all possible languages with probabilities
            all_languages = self._get_all_languages(clean_text)
            
            # Validate against supported languages
            if detected_lang not in self.supported_languages:
                detected_lang = 'unknown'
                confidence = 0.0
            
            result = {
                'detected_language': detected_lang,
                'language_name': SUPPORTED_LANGUAGES.get(detected_lang, 'Unknown'),
                'confidence': confidence,
                'all_languages': all_languages,
                'success': True,
                'error': None
            }
            
            # Check if confidence is above threshold
            if confidence < self.min_confidence:
                result['success'] = False
                result['error'] = f'Confidence too low: {confidence:.2f} < {self.min_confidence:.2f}'
            
            return result
            
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {str(e)}")
            return {
                'detected_language': None,
                'language_name': None,
                'confidence': 0.0,
                'all_languages': [],
                'success': False,
                'error': f'Language detection failed: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error in language detection: {str(e)}")
            return {
                'detected_language': None,
                'language_name': None,
                'confidence': 0.0,
                'all_languages': [],
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def detect_language_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Detect languages for multiple texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of language detection results
        """
        results = []
        
        for i, text in enumerate(texts):
            try:
                result = self.detect_language(text)
                result['text_index'] = i
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to detect language for text {i}: {str(e)}")
                results.append({
                    'detected_language': None,
                    'language_name': None,
                    'confidence': 0.0,
                    'all_languages': [],
                    'success': False,
                    'error': str(e),
                    'text_index': i
                })
        
        return results
    
    def detect_mixed_language(self, text: str) -> Dict[str, Any]:
        """
        Detect if text contains multiple languages.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with mixed language analysis
        """
        try:
            clean_text = self._preprocess_text(text)
            
            if not clean_text:
                return {
                    'is_mixed': False,
                    'primary_language': None,
                    'secondary_languages': [],
                    'language_distribution': {},
                    'confidence': 0.0
                }
            
            # Get all language probabilities
            all_languages = self._get_all_languages(clean_text)
            
            # Check for mixed languages
            primary_lang = all_languages[0] if all_languages else None
            secondary_langs = [lang for lang in all_languages[1:] if lang[1] > 0.05]
            
            # Calculate distribution
            distribution = {lang: prob for lang, prob in all_languages}
            
            return {
                'is_mixed': len(secondary_langs) > 0,
                'primary_language': primary_lang[0] if primary_lang else None,
                'secondary_languages': [lang[0] for lang in secondary_langs],
                'language_distribution': distribution,
                'confidence': primary_lang[1] if primary_lang else 0.0
            }
            
        except Exception as e:
            logger.error(f"Mixed language detection failed: {str(e)}")
            return {
                'is_mixed': False,
                'primary_language': None,
                'secondary_languages': [],
                'language_distribution': {},
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for language detection.
        
        Args:
            text: Raw text
            
        Returns:
            Preprocessed text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Limit text length
        if len(text) > self.max_text_length:
            text = text[:self.max_text_length]
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove special characters that might interfere
        text = ''.join(c for c in text if c.isalnum() or c.isspace() or c in '.,!?;:')
        
        return text.strip()
    
    def _get_confidence(self, text: str, language: str) -> float:
        """
        Get confidence score for a specific language.
        
        Args:
            text: Text to analyze
            language: Language code
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        try:
            all_languages = detect_langs(text)
            for lang in all_languages:
                if lang.lang == language:
                    return lang.prob
            return 0.0
        except:
            return 0.0
    
    def _get_all_languages(self, text: str) -> List[Tuple[str, float]]:
        """
        Get all possible languages with their probabilities.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of (language_code, probability) tuples
        """
        try:
            all_languages = detect_langs(text)
            return [(lang.lang, lang.prob) for lang in all_languages]
        except:
            return []
    
    def validate_language_support(self, language_code: str) -> bool:
        """
        Check if a language is supported by the system.
        
        Args:
            language_code: Language code to check
            
        Returns:
            True if supported, False otherwise
        """
        return language_code.lower() in self.supported_languages
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get all supported languages.
        
        Returns:
            Dictionary of language codes and names
        """
        return SUPPORTED_LANGUAGES.copy()
    
    def get_language_name(self, language_code: str) -> str:
        """
        Get the full name of a language.
        
        Args:
            language_code: Language code
            
        Returns:
            Language name or 'Unknown' if not found
        """
        return SUPPORTED_LANGUAGES.get(language_code.lower(), 'Unknown')
    
    def filter_supported_languages(self, languages: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """
        Filter list of languages to only include supported ones.
        
        Args:
            languages: List of (language_code, probability) tuples
            
        Returns:
            Filtered list with only supported languages
        """
        return [(lang, prob) for lang, prob in languages if self.validate_language_support(lang)]