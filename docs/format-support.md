# Format Support Documentation

This document describes the supported document formats and their capabilities in the AI Document Analyzer.

## Supported Formats

The system supports the following document formats:

### PDF (Portable Document Format)
- **File Extensions**: `.pdf`
- **Max File Size**: 10 MB
- **Features**:
  - Text extraction (direct)
  - OCR processing for scanned documents
  - Multi-language support
  - PII anonymization
  - Field extraction
- **Limitations**:
  - Encrypted PDFs are not supported
  - Maximum 100 pages per document
  - OCR quality depends on scan quality

### DOCX (Microsoft Word)
- **File Extensions**: `.docx`, `.doc`
- **Max File Size**: 5 MB
- **Features**:
  - Text extraction from paragraphs
  - Table content extraction
  - Header/footer extraction
  - Metadata extraction
  - Multi-language support
  - PII anonymization
  - Field extraction
- **Limitations**:
  - Password-protected documents not supported
  - Complex formatting may affect extraction quality

### Image Formats
- **Supported Extensions**: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, `.tif`
- **Max File Size**: 10 MB
- **Features**:
  - OCR text extraction
  - Image preprocessing (enhancement, denoising, rotation correction)
  - Multi-language OCR support
  - PII anonymization
  - Field extraction
- **Limitations**:
  - OCR quality depends on image resolution and clarity
  - Handwritten text may not be recognized accurately
  - Very large images may be processed slower

### Text Formats
- **Supported Extensions**: `.txt`, `.md`, `.rtf`
- **Max File Size**: 1 MB
- **Features**:
  - Direct text processing
  - Multi-language support
  - PII anonymization
  - Field extraction
- **Limitations**:
  - No formatting preservation
  - Limited to plain text content

## Format Detection

The system automatically detects document formats using multiple methods:

1. **File Extension**: Basic format identification
2. **MIME Type**: Content-type detection
3. **Magic Numbers**: File signature analysis
4. **Content Analysis**: Text vs. binary content analysis

### Detection Confidence

Format detection includes confidence scoring:
- **High Confidence (0.8-1.0)**: All detection methods agree
- **Medium Confidence (0.5-0.8)**: Most methods agree
- **Low Confidence (0.0-0.5)**: Methods disagree or inconclusive

## Processing Capabilities by Format

| Format | Text Extraction | OCR | PII Anonymization | Field Extraction | Language Detection |
|--------|----------------|-----|-------------------|------------------|-------------------|
| PDF    | ✅ Direct      | ✅  | ✅                | ✅               | ✅                |
| DOCX   | ✅             | ❌  | ✅                | ✅               | ✅                |
| Image  | ❌             | ✅  | ✅                | ✅               | ✅                |
| Text   | ✅             | ❌  | ✅                | ✅               | ✅                |

## API Endpoints

### Single Format Processing
```http
POST /analyze
Content-Type: multipart/form-data

# For PDF files only
file: document.pdf
document_type: contract
enable_ocr: true
anonymize_pii: true
```

### Multi-Format Processing
```http
POST /analyze-multi-format
Content-Type: multipart/form-data

# For any supported format
file: document.docx
document_type: resume
enable_ocr: true
detect_language: true
anonymize_pii: true
```

### Format Detection
```http
GET /format-detection
Content-Type: multipart/form-data

file: document.unknown
```

### Language Detection
```http
POST /detect-language
Content-Type: multipart/form-data

file: document.pdf
```

## Best Practices

### PDF Files
- Use high-quality scans (300 DPI minimum)
- Avoid encrypted or password-protected files
- Prefer text-based PDFs over image-only scans when possible

### DOCX Files
- Save in modern DOCX format when possible
- Avoid complex nested tables
- Use standard fonts for better text extraction

### Image Files
- Use high resolution (300 DPI minimum)
- Ensure good lighting and contrast
- Avoid skewed or rotated images
- Use lossless formats (PNG, TIFF) for best OCR results

### Text Files
- Use UTF-8 encoding
- Avoid special characters that may cause issues
- Keep files under 1MB for optimal performance

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "File too large" | File exceeds size limit | Compress or split large files |
| "Unsupported format" | File extension not supported | Convert to supported format |
| "Invalid file" | Corrupted or malformed file | Re-upload or recreate the file |
| "OCR failed" | Poor image quality | Improve scan quality or resolution |
| "Language detection failed" | Insufficient text content | Provide documents with more text |

### Troubleshooting

1. **Check File Size**: Ensure files are within size limits
2. **Verify Format**: Confirm file extension matches actual format
3. **Test with Sample**: Try processing a known good file
4. **Check Logs**: Review system logs for detailed error information
5. **Contact Support**: For persistent issues, contact technical support

## Performance Considerations

### Processing Times
- **PDF (text-based)**: 1-5 seconds per page
- **PDF (OCR)**: 5-15 seconds per page
- **DOCX**: 1-3 seconds per document
- **Image**: 3-10 seconds per image
- **Text**: < 1 second per document

### Resource Usage
- **Memory**: 100-500 MB per concurrent processing
- **CPU**: High usage during OCR processing
- **Storage**: Temporary files created during processing

### Scaling Recommendations
- Use load balancing for high-volume processing
- Implement queueing for batch processing
- Monitor resource usage during peak times
- Consider distributed processing for large files

## Future Format Support

Planned formats for future releases:
- **PowerPoint**: `.ppt`, `.pptx` (presentation slides)
- **Excel**: `.xls`, `.xlsx` (spreadsheet data)
- **Email**: `.eml`, `.msg` (email messages)
- **Archive**: `.zip`, `.rar` (compressed documents)

## Support and Feedback

For issues with format support or suggestions for new formats:
- Submit bug reports via GitHub Issues
- Request new format support through feature requests
- Contact support for enterprise format requirements