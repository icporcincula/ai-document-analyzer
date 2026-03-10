# Web UI User Guide

This guide provides comprehensive instructions for using the Document Analyzer Web UI.

## Overview

The Document Analyzer Web UI provides a user-friendly interface for:
- Uploading and analyzing documents
- Viewing analysis results with PII detection
- Managing document history
- Exporting results in multiple formats
- Monitoring system metrics

## Getting Started

### Accessing the Web UI

The Web UI is available at:
- **Development**: `http://localhost:3001`
- **Production**: `https://your-domain.com`

### Prerequisites

- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection to access the API backend
- Valid API key (if authentication is enabled)

## Features

### 1. Document Upload

#### Supported File Types
- PDF documents (.pdf)
- Word documents (.docx)
- PowerPoint presentations (.pptx)
- Images (.jpg, .jpeg, .png, .gif, .bmp)

#### File Size Limits
- Maximum file size: 10 MB
- Maximum page count: 50 pages (for PDFs)

#### Upload Methods
1. **Drag and Drop**: Drag files directly onto the upload area
2. **File Browser**: Click the upload area to open file browser
3. **Multiple Files**: Only one file can be uploaded at a time

#### Document Types
- **Auto**: Automatically detect document type
- **Contract**: Legal contracts and agreements
- **Invoice**: Financial invoices and bills
- **Resume**: CVs and resumes
- **Custom**: User-defined document types

### 2. Analysis Results

#### Results Page Layout
- **Document Information**: File details and processing metadata
- **PII Detection Summary**: Overview of detected PII entities
- **Extracted Fields**: Structured data extracted from the document
- **Confidence Scores**: AI confidence levels for each field

#### PII Entity Types
- **Personal Information**: Names, addresses, phone numbers
- **Financial Data**: Credit card numbers, bank account details
- **Identification**: Social security numbers, passport numbers
- **Health Information**: Medical records, health data

#### Confidence Indicators
- **Green (80-100%)**: High confidence
- **Yellow (50-79%)**: Medium confidence
- **Red (0-49%)**: Low confidence

### 3. Document History

#### Viewing History
- Navigate to "History" from the main menu
- View all processed documents in a paginated table
- Filter documents by search terms

#### History Columns
- **Task ID**: Unique identifier for the analysis
- **Filename**: Original document name
- **Document Type**: Detected or specified document type
- **Status**: Processing status (completed, processing, failed)
- **Created At**: Date and time of processing
- **Processing Time**: Duration of analysis
- **File Size**: Original document size
- **PII Count**: Number of PII entities detected

#### Actions
- **View Results**: Open detailed analysis results
- **Delete**: Remove document from history (soft delete)

### 4. Export Functionality

#### Export Formats
- **CSV**: Comma-separated values for spreadsheet applications
- **Excel**: Microsoft Excel format with formatting
- **JSON**: Structured data format for developers

#### Export Options
- **Single Document**: Export results for one document
- **Batch Export**: Export multiple documents (planned feature)
- **History Export**: Export entire history as CSV

#### Download Process
1. Navigate to results or history page
2. Click the appropriate export button
3. File downloads automatically to browser downloads folder

### 5. Metrics Dashboard

#### Available Metrics
- **Document Processing Rate**: Documents processed per minute
- **Processing Duration**: Average, P95, P99 processing times
- **PII Detection Rate**: PII entities detected per minute
- **Error Rate**: Failed processing attempts
- **Active Connections**: Current system connections

#### Dashboard Features
- Real-time metric updates
- Historical trend charts
- Performance threshold alerts
- Export capabilities for metric data

## Advanced Features

### 1. PII Anonymization

#### Anonymization Process
- PII entities are automatically detected and anonymized
- Original document content is preserved in analysis
- Anonymized text is used for AI processing
- PII detection results are still available in results

#### Anonymization Settings
- **Enabled by Default**: PII anonymization is active
- **Disable Option**: Can be disabled in advanced settings
- **Custom Entities**: Support for custom PII patterns

### 2. Multi-Language Support

#### Supported Languages
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- And more (depending on Presidio configuration)

#### Language Detection
- Automatic language detection for uploaded documents
- Manual language override available
- Language-specific PII patterns

### 3. Custom Entity Detection

#### Adding Custom Entities
1. Navigate to Settings (planned feature)
2. Define custom regex patterns
3. Assign entity names and categories
4. Enable/disable specific entities

#### Use Cases
- Company-specific identifiers
- Industry-specific data patterns
- Custom PII definitions

## Troubleshooting

### Common Issues

#### Upload Failures
- **File Too Large**: Reduce file size or split large documents
- **Unsupported Format**: Convert to supported format
- **Corrupted File**: Verify file integrity
- **Network Issues**: Check internet connection

#### Processing Errors
- **Timeout**: Large documents may timeout (increase timeout in settings)
- **Memory Issues**: System may run out of memory with large files
- **API Errors**: Check backend service status

#### Display Issues
- **Browser Cache**: Clear browser cache and reload
- **JavaScript Disabled**: Enable JavaScript in browser
- **CSS Issues**: Check browser developer tools for errors

### Error Messages

#### "File too large"
- Maximum file size is 10 MB
- Compress images or split large documents
- Use PDF optimization tools

#### "Unsupported file format"
- Ensure file extension matches actual format
- Convert documents to supported formats
- Check file integrity

#### "Processing failed"
- Check backend service logs
- Verify API connectivity
- Contact system administrator

#### "No text extracted"
- Document may be scanned image (enable OCR)
- Document may be corrupted
- Try alternative document format

### Performance Optimization

#### Large Document Processing
- Split large documents into smaller sections
- Use document compression tools
- Process during off-peak hours

#### Browser Performance
- Close other browser tabs
- Clear browser cache regularly
- Use latest browser version

#### Network Optimization
- Use wired connection when possible
- Minimize network congestion
- Check firewall settings

## Security Considerations

### Data Privacy
- Documents are processed securely
- PII anonymization protects sensitive data
- Temporary storage with automatic cleanup
- No permanent document storage

### Access Control
- API key authentication required
- Role-based access control (planned)
- Audit logging for all operations
- Secure transmission (HTTPS)

### Best Practices
- Use strong, unique API keys
- Regularly rotate API keys
- Monitor access logs
- Implement proper error handling

## API Integration

### REST API Endpoints
- `/api/v1/analyze` - Analyze document
- `/api/v1/results/{task_id}` - Get analysis results
- `/api/v1/history` - Get processing history
- `/api/v1/export/{task_id}/{format}` - Export results

### API Authentication
- API key in Authorization header
- Rate limiting applied
- CORS restrictions enforced
- HTTPS required in production

### Example API Usage
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Authorization: Bearer your-api-key" \
  -F "file=@document.pdf" \
  -F "document_type=auto" \
  -F "anonymize_pii=true"
```

## Support and Feedback

### Getting Help
- Check this documentation first
- Review system logs for technical issues
- Contact system administrator
- Submit bug reports via GitHub Issues

### Providing Feedback
- Feature requests welcome
- Bug reports should include:
  - Browser and version
  - Steps to reproduce
  - Expected vs actual behavior
  - Screenshots if applicable

### System Requirements
- **Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **JavaScript**: Required
- **Cookies**: Required for session management
- **Network**: Stable internet connection

## Version Information

### Current Version
- Web UI: 1.0.0
- API: 1.0.0
- Backend: 1.0.0

### Changelog
- **v1.0.0**: Initial release with core functionality
- **v1.1.0**: Added multi-language support
- **v1.2.0**: Added custom entity detection
- **v1.3.0**: Added metrics dashboard

For the latest updates and changes, see the [CHANGELOG](../CHANGELOG.md).