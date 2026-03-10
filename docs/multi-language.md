# Multi-Language Support Documentation

This document describes the multi-language capabilities of the AI Document Analyzer, including language detection, PII processing, and document extraction in multiple languages.

## Supported Languages

The system supports PII detection and document processing in the following languages:

### Primary Languages (Full Support)
- **English** (`en`) - Default language
- **German** (`de`)
- **Spanish** (`es`)
- **French** (`fr`)
- **Italian** (`it`)
- **Portuguese** (`pt`)
- **Dutch** (`nl`)

### Extended Languages (PII Detection)
- **Russian** (`ru`)
- **Japanese** (`ja`)
- **Chinese** (`zh`)
- **Arabic** (`ar`)
- **Hindi** (`hi`)
- **Korean** (`ko`)
- **Turkish** (`tr`)
- **Polish** (`pl`)
- **Swedish** (`sv`)
- **Danish** (`da`)
- **Norwegian** (`no`)
- **Finnish** (`fi`)
- **Czech** (`cs`)
- **Slovak** (`sk`)
- **Hungarian** (`hu`)
- **Romanian** (`ro`)
- **Bulgarian** (`bg`)
- **Croatian** (`hr`)
- **Serbian** (`sr`)
- **Greek** (`el`)
- **Thai** (`th`)
- **Vietnamese** (`vi`)
- **Indonesian** (`id`)

## Language Detection

### Automatic Detection
The system automatically detects document language using:

1. **Text Analysis**: Analyzes character patterns and word structures
2. **Confidence Scoring**: Provides confidence level for language identification
3. **Mixed Language Detection**: Identifies documents with multiple languages

### Detection Accuracy
- **High Accuracy (90%+)**: English, German, Spanish, French, Italian, Portuguese
- **Medium Accuracy (80-90%)**: Dutch, Russian, Japanese, Chinese
- **Variable Accuracy (60-80%)**: Other supported languages depending on text quality

### Language Detection API

```http
POST /detect-language
Content-Type: multipart/form-data

file: document.pdf
```

**Response:**
```json
{
  "success": true,
  "detected_language": {
    "detected_language": "es",
    "language_name": "Spanish",
    "confidence": 0.95,
    "all_languages": [
      ["es", 0.95],
      ["pt", 0.03],
      ["it", 0.02]
    ],
    "success": true
  },
  "text_length": 1500,
  "format": "pdf"
}
```

## Multi-Language PII Detection

### Presidio Integration
The system uses Microsoft Presidio for PII detection with multi-language support:

- **Entity Types**: 30+ PII entity types with language-specific patterns
- **Language-Specific Rules**: Different detection rules for each language
- **Confidence Scoring**: Language-aware confidence levels

### Supported PII Entities by Language

| Entity Type | English | German | Spanish | French | Italian |
|-------------|---------|--------|---------|--------|---------|
| PERSON | ✅ | ✅ | ✅ | ✅ | ✅ |
| EMAIL_ADDRESS | ✅ | ✅ | ✅ | ✅ | ✅ |
| PHONE_NUMBER | ✅ | ✅ | ✅ | ✅ | ✅ |
| LOCATION | ✅ | ✅ | ✅ | ✅ | ✅ |
| DATE_TIME | ✅ | ✅ | ✅ | ✅ | ✅ |
| CREDIT_CARD | ✅ | ✅ | ✅ | ✅ | ✅ |
| US_SSN | ✅ | ❌ | ❌ | ❌ | ❌ |
| DE_IDNR | ❌ | ✅ | ❌ | ❌ | ❌ |
| ES_NIF | ❌ | ❌ | ✅ | ❌ | ❌ |
| FR_SIRET | ❌ | ❌ | ❌ | ✅ | ❌ |
| IT_FISCAL_CODE | ❌ | ❌ | ❌ | ❌ | ✅ |

### Custom Entity Support
Custom PII patterns can be defined per language:

```yaml
entities:
  - name: "GERMAN_TAX_ID"
    pattern: r'\b[0-9]{3}[.][0-9]{3}[.][0-9]{3}[0-9]\b'
    description: "German Tax Identification Number"
    context: ["steuer", "tax", "identification"]
    enabled: true
```

## Multi-Language Document Processing

### Document Type Detection
The system can automatically detect document types in multiple languages:

- **Contract** - Vertrag, Contrato, Contrat, Contratto
- **Invoice** - Rechnung, Factura, Facture, Fattura
- **Resume** - Lebenslauf, Curriculum, CV, Curriculum Vitae
- **Legal Brief** - Gutachten, Escrito, Mémoire, Parere

### Field Extraction
AI-powered field extraction works across languages:

```http
POST /analyze-multi-format
Content-Type: multipart/form-data

file: contrato_espanol.pdf
document_type: contract
language: es
anonymize_pii: true
```

**Response includes language-specific field names:**
```json
{
  "extracted_fields": {
    "partes_contratantes": {
      "value": "Empresa XYZ y Cliente ABC",
      "confidence": 0.92,
      "language": "es"
    },
    "fecha_efectiva": {
      "value": "01/01/2024",
      "confidence": 0.95,
      "language": "es"
    }
  }
}
```

## Language-Specific Processing

### Text Preprocessing
Each language has specific preprocessing rules:

- **Character Encoding**: UTF-8 with language-specific normalization
- **Text Cleaning**: Language-appropriate punctuation and whitespace handling
- **Tokenization**: Language-specific word boundary detection

### OCR Language Support
Image processing supports multiple OCR languages:

```python
# Configure OCR for specific language
ocr_config = {
    "psm": 6,
    "oem": 3,
    "lang": "deu+eng",  # German + English
    "enhance_contrast": True
}
```

### LLM Prompt Adaptation
AI extraction prompts are adapted per language:

- **System Prompts**: Language-specific instructions
- **Field Names**: Localized field extraction
- **Validation Rules**: Language-appropriate validation

## API Usage Examples

### Multi-Language Processing
```python
import requests

# Process German document
response = requests.post(
    "http://localhost:8000/analyze-multi-format",
    files={"file": open("vertrag.pdf", "rb")},
    data={
        "document_type": "contract",
        "language": "de",
        "anonymize_pii": "true"
    }
)

result = response.json()
print(f"Language: {result['metadata']['language_detected']}")
print(f"Confidence: {result['confidence']}")
```

### Language Detection Only
```python
# Detect language without full processing
response = requests.post(
    "http://localhost:8000/detect-language",
    files={"file": open("document.pdf", "rb")}
)

language_info = response.json()
if language_info["success"]:
    detected_lang = language_info["detected_language"]["detected_language"]
    confidence = language_info["detected_language"]["confidence"]
    print(f"Detected: {detected_lang} (confidence: {confidence})")
```

### Supported Languages List
```python
# Get list of supported languages
response = requests.get("http://localhost:8000/supported-languages")
languages = response.json()

print(f"Total supported languages: {languages['total']}")
for lang_code in languages["languages"][:10]:  # Show first 10
    print(f"- {lang_code}")
```

## Configuration

### Language Settings
Language detection and processing can be configured:

```python
# Configuration example
LANGUAGE_CONFIG = {
    "min_confidence": 0.8,           # Minimum confidence for language detection
    "max_text_length": 10000,        # Maximum text length for processing
    "default_language": "en",        # Fallback language
    "supported_languages": ["en", "de", "es", "fr", "it", "pt", "nl"]
}
```

### Custom Entity Configuration
Custom PII patterns can be configured per language:

```yaml
# config/custom_entities.yaml
entities:
  - name: "MULTI_LANGUAGE_ENTITY"
    pattern: r'\b[A-Z]{2}[0-9]{8}\b'
    description: "International identifier pattern"
    context: 
      - en: ["identifier", "code", "number"]
      - de: ["identifikator", "code", "nummer"]
      - es: ["identificador", "código", "número"]
    enabled: true
```

## Performance Considerations

### Processing Speed
- **English**: Fastest processing (optimized models)
- **Major Languages**: 10-20% slower than English
- **Extended Languages**: 20-50% slower depending on model availability

### Memory Usage
- **Base Models**: 500MB-1GB per language model
- **Shared Models**: Reduced memory with multi-language models
- **On-Demand Loading**: Load language models only when needed

### Accuracy Trade-offs
- **High Resource**: Best accuracy, highest resource usage
- **Balanced**: Good accuracy, moderate resource usage
- **Lightweight**: Acceptable accuracy, minimal resource usage

## Troubleshooting

### Common Issues

1. **Low Confidence Detection**
   - **Cause**: Insufficient text or mixed languages
   - **Solution**: Provide documents with more text in target language

2. **Incorrect Language Detection**
   - **Cause**: Similar languages or poor text quality
   - **Solution**: Manually specify language parameter

3. **Poor PII Detection**
   - **Cause**: Language not fully supported or custom patterns needed
   - **Solution**: Use custom entity patterns or fallback to English

4. **Slow Processing**
   - **Cause**: Large documents or resource constraints
   - **Solution**: Process smaller documents or increase resources

### Debug Information
Enable debug logging for language processing:

```python
import logging
logging.getLogger('app.services.language_detection').setLevel(logging.DEBUG)
```

## Future Language Support

Planned language additions:
- **Additional European**: Polish, Czech, Hungarian, Romanian
- **Asian Languages**: Korean, Vietnamese, Thai, Indonesian
- **Middle Eastern**: Hebrew, Farsi, Turkish
- **African Languages**: Swahili, Amharic

## Support and Feedback

For language-specific issues or requests:
- Report language detection accuracy issues
- Request support for additional languages
- Submit custom entity patterns for review
- Provide feedback on multi-language processing quality