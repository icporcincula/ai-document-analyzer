# Phase 4: Format & Language Expansion

**Target:** Broader document coverage
**Priority:** MEDIUM - Expands usability and market reach
**Estimated Time:** 4-5 days

## Overview

This phase expands document format support beyond PDFs and adds multi-language capabilities to serve a global user base and handle diverse document types.

## Prerequisites

- [x] Core MVP functionality working
- [x] Phase 2 Security & Authentication completed
- [x] Phase 3 Quality & Testing completed
- [x] Test infrastructure in place

## Tasks

### 4.1 DOCX Support

#### 4.1.1 Install DOCX Dependencies
- **File:** `requirements.txt`
- **Task:** Add `python-docx` dependency
- **Task:** Add `python-pptx` for PowerPoint support (future)
- **Test:** Verify DOCX dependencies install correctly

#### 4.1.2 DOCX Service Implementation
- **File:** `app/services/docx_service.py`
- **Task:** Create DOCX text extraction service
- **Task:** Extract text from paragraphs
- **Task:** Extract text from tables
- **Task:** Extract text from headers/footers
- **Task:** Handle DOCX formatting preservation
- **Test:** Test with simple DOCX files
- **Test:** Test with complex DOCX (tables, images)
- **Test:** Test with password-protected DOCX

#### 4.1.3 DOCX Validation
- **File:** `app/services/docx_service.py`
- **Task:** Add DOCX file validation
- **Task:** Check file size limits
- **Task:** Validate DOCX structure
- **Task:** Handle corrupted DOCX files
- **Test:** Test validation with invalid DOCX files
- **Test:** Test with empty DOCX files

#### 4.1.4 Integration with Main Service
- **File:** `app/services/pdf_service.py`
- **Task:** Extend PDFService to handle DOCX
- **Task:** Add format detection logic
- **Task:** Route DOCX files to DOCX service
- **Task:** Maintain consistent API interface
- **Test:** Test format detection accuracy
- **Test:** Test seamless integration

### 4.2 Image Input Support

#### 4.2.1 Image Processing Dependencies
- **File:** `requirements.txt`
- **Task:** Add `Pillow` (PIL) for image processing
- **Task:** Add `opencv-python` for advanced image processing
- **Test:** Verify image processing dependencies work

#### 4.2.2 Image Service Implementation
- **File:** `app/services/image_service.py`
- **Task:** Create image text extraction service
- **Task:** Support PNG, JPEG, BMP, TIFF formats
- **Task:** Preprocess images for better OCR
- **Task:** Handle image rotation and skew correction
- **Task:** Optimize image quality for OCR
- **Test:** Test with various image formats
- **Test:** Test with low-quality images
- **Test:** Test with rotated images

#### 4.2.3 Image Validation
- **File:** `app/services/image_service.py`
- **Task:** Add image file validation
- **Task:** Check image dimensions
- **Task:** Validate image format
- **Task:** Handle corrupted image files
- **Test:** Test validation with invalid images
- **Test:** Test with very large images

#### 4.2.4 Direct OCR Routing
- **File:** `app/services/pdf_service.py`
- **Task:** Route images directly to OCR
- **Task:** Skip PDF parsing for images
- **Task:** Optimize OCR parameters for images
- **Test:** Test direct OCR performance
- **Test:** Compare quality with PDF OCR

### 4.3 Multi-Language Support

#### 4.3.1 Language Detection
- **File:** `app/services/language_detection.py`
- **Task:** Implement language detection service
- **Task:** Use `langdetect` or similar library
- **Task:** Support 50+ languages
- **Task:** Add confidence scoring for language detection
- **Test:** Test language detection accuracy
- **Test:** Test with mixed-language documents

#### 4.3.2 Presidio Multi-Language
- **File:** `app/services/presidio_client.py`
- **Task:** Configure Presidio for multiple languages
- **Task:** Support: English, German, Spanish, French, Italian, Portuguese, Dutch
- **Task:** Add language-specific PII patterns
- **Task:** Test PII detection in different languages
- **Test:** Verify language-specific entity recognition

#### 4.3.3 LLM Multi-Language
- **File:** `app/services/extraction_service.py`
- **Task:** Configure LLM for multi-language processing
- **Task:** Add language parameter to extraction
- **Task:** Use language-specific prompts
- **Task:** Handle language-specific field names
- **Test:** Test extraction in different languages
- **Test:** Verify prompt effectiveness per language

#### 4.3.4 Language Configuration
- **File:** `app/utils/config.py`
- **Task:** Add supported languages configuration
- **Task:** Add default language setting
- **Task:** Add language detection enable/disable
- **Test:** Test configuration loading
- **Test:** Test language switching

### 4.4 Additional Document Types

#### 4.4.1 Legal Brief Support
- **File:** `app/services/extraction_service.py`
- **Task:** Add legal brief field extraction
- **Task:** Extract case names, citations, judges
- **Task:** Extract legal arguments and conclusions
- **Task:** Handle legal document structure
- **Test:** Test with sample legal briefs
- **Test:** Verify legal field accuracy

#### 4.4.2 Medical Record Support
- **File:** `app/services/extraction_service.py`
- **Task:** Add medical record field extraction
- **Task:** Extract patient information (anonymized)
- **Task:** Extract diagnoses, medications, procedures
- **Task:** Handle medical terminology
- **Task:** Add HIPAA compliance considerations
- **Test:** Test with sample medical records
- **Test:** Verify medical field accuracy

#### 4.4.3 Bank Statement Support
- **File:** `app/services/extraction_service.py`
- **Task:** Add bank statement field extraction
- **Task:** Extract account numbers, transactions
- **Task:** Extract balances, dates
- **Task:** Handle financial formatting
- **Test:** Test with sample bank statements
- **Test:** Verify financial field accuracy

#### 4.4.4 Dynamic Document Type Detection
- **File:** `app/services/document_classifier.py`
- **Task:** Implement ML-based document classification
- **Task:** Use text features for classification
- **Task:** Support confidence scoring
- **Task:** Add fallback to manual selection
- **Test:** Test classification accuracy
- **Test:** Test with ambiguous documents

### 4.5 Custom Entity Recognition

#### 4.5.1 Custom Entity Configuration
- **File:** `app/config/entities.yaml`
- **Task:** Create custom entity configuration
- **Task:** Define domain-specific PII patterns
- **Task:** Support regex patterns
- **Task:** Add entity scoring
- **Test:** Test custom entity detection
- **Test:** Test configuration loading

#### 4.5.2 Custom Entity Service
- **File:** `app/services/custom_entity_service.py`
- **Task:** Implement custom entity recognition
- **Task:** Load custom entity patterns
- **Task:** Integrate with Presidio
- **Task:** Add entity validation
- **Test:** Test custom entity detection
- **Test:** Test integration with anonymization

#### 4.5.3 Client Configuration API
- **File:** `app/api/routes.py`
- **Task:** Add custom entity configuration endpoint
- **Task:** Allow clients to define custom entities
- **Task:** Validate custom entity patterns
- **Task:** Store configuration per client
- **Test:** Test custom entity API
- **Test:** Test pattern validation

### 4.6 Format Conversion and Enhancement

#### 4.6.1 Document Preprocessing
- **File:** `app/services/preprocessing_service.py`
- **Task:** Implement document preprocessing
- **Task:** Image enhancement for OCR
- **Task:** Text normalization
- **Task:** Format standardization
- **Test:** Test preprocessing effectiveness
- **Test:** Measure OCR improvement

#### 4.6.2 Format Detection Enhancement
- **File:** `app/services/format_detection.py`
- **Task:** Improve format detection accuracy
- **Task:** Use file signatures (magic numbers)
- **Task:** Add MIME type detection
- **Task:** Handle ambiguous file extensions
- **Test:** Test format detection accuracy
- **Test:** Test with mislabeled files

### 4.7 Testing for New Formats

#### 4.7.1 Format-Specific Test Fixtures
- **File:** `tests/fixtures/`
- **Task:** Create test files for each format
- **Task:** Add DOCX test files
- **Task:** Add image test files (PNG, JPEG)
- **Task:** Add multi-language test files
- **Task:** Add new document type test files
- **Test:** Verify all test fixtures work

#### 4.7.2 Format Integration Tests
- **File:** `tests/integration/test_formats.py`
- **Task:** Test DOCX processing end-to-end
- **Task:** Test image processing end-to-end
- **Task:** Test multi-language processing
- **Task:** Test new document types
- **Test:** Verify consistent API responses
- **Test:** Test error handling per format

#### 4.7.3 Performance Testing
- **File:** `tests/performance/test_formats.py`
- **Task:** Benchmark different format processing
- **Task:** Compare OCR performance across formats
- **Task:** Test memory usage per format
- **Test:** Identify format-specific bottlenecks
- **Test:** Optimize slow formats

### 4.8 Documentation and Examples

#### 4.8.1 Format Support Documentation
- **File:** `docs/format-support.md`
- **Task:** Document supported formats
- **Task:** Document format-specific limitations
- **Task:** Provide format conversion recommendations
- **Test:** Verify documentation accuracy

#### 4.8.2 Multi-Language Documentation
- **File:** `docs/multi-language.md`
- **Task:** Document language support
- **Task:** Provide language-specific examples
- **Task:** Document language detection behavior
- **Test:** Verify documentation completeness

## Testing Strategy

### Format Testing
- **Unit Tests**: Individual format service testing
- **Integration Tests**: End-to-end format processing
- **Performance Tests**: Format-specific benchmarks
- **Compatibility Tests**: Cross-format consistency

### Language Testing
- **Unit Tests**: Language detection accuracy
- **Integration Tests**: Multi-language processing
- **Localization Tests**: Language-specific behavior
- **Performance Tests**: Language processing speed

### Custom Entity Testing
- **Unit Tests**: Custom entity pattern matching
- **Integration Tests**: Custom entity integration
- **Configuration Tests**: Entity configuration validation

## Quality Metrics

### Format Support
- [ ] 95%+ format detection accuracy
- [ ] DOCX processing within 2x PDF performance
- [ ] Image OCR quality comparable to PDF OCR
- [ ] Support for 10+ document types

### Language Support
- [ ] 90%+ language detection accuracy
- [ ] PII detection in 8+ languages
- [ ] LLM extraction in 5+ languages
- [ ] Consistent quality across languages

### Custom Entities
- [ ] Custom pattern validation
- [ ] Integration with existing PII detection
- [ ] Performance impact < 10%

## Deployment Checklist

- [ ] All new format services tested
- [ ] Multi-language support validated
- [ ] Custom entity configuration working
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Error handling comprehensive

## Success Criteria

- [ ] Support for DOCX, images, and 3+ new document types
- [ ] Multi-language support for 8+ languages
- [ ] Custom entity recognition working
- [ ] Consistent API across all formats
- [ ] Performance within acceptable limits
- [ ] Comprehensive test coverage for new features
- [ ] Clear documentation for all new capabilities

## Rollback Plan

- [ ] Feature flags for format support
- [ ] Language support can be disabled
- [ ] Custom entities can be disabled
- [ ] Performance monitoring for format impact