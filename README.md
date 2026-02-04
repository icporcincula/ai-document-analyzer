# Private AI Document Analyzer with PII Anonymization

**Extract structured data from PDF documents while preserving privacy through automatic PII detection and anonymization.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-required-2496ED.svg)](https://www.docker.com/)

---

## 🎯 **Overview**

This system analyzes PDF documents (contracts, invoices, resumes, etc.) and extracts structured data using AI, while automatically detecting and anonymizing personally identifiable information (PII) before sending data to language models.

**Key Features:**
- **PDF Text Extraction** - Direct text extraction with OCR fallback for scanned documents
- **Privacy-First Architecture** - PII detection using Microsoft Presidio and 100% local field extraction via Ollama (Gemma 3 / DeepSeek-R1). No sensitive data ever leaves your infrastructure.
- **No Third-Party Data Leakage** - By using local LLMs, you eliminate the risk of sensitive document contents being used for model training by third-party providers.
- **AI-Powered Extraction** - Structured field extraction using OpenAI GPT models
- **Containerized Microservices** - Docker-based deployment with zero dependency issues
- **Explainability** - Confidence scores and detailed extraction metadata
- **Production-Ready** - Clean architecture, logging, error handling

---

## 🏗️ **Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                         Client                              │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PDF Service  │  │  Presidio    │  │ Extraction   │      │
│  │ (OCR/Text)   │→ │   Client     │→ │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────┬──────────────────┬──────────────────┬──────────────┘
         │                  │                  │
         ↓                  ↓                  ↓
┌────────────────┐  ┌─────────────┐  ┌─────────────┐
│ Tesseract OCR  │  │  Presidio   │  │  Local LLM  │
│                │  │  Services   │  │  (Ollama)   │
└────────────────┘  └─────────────┘  └─────────────┘
```

**Service Components:**
1. **FastAPI Application** - Main API server and orchestration
2. **Presidio Analyzer** - PII detection service (Microsoft)
3. **Presidio Anonymizer** - PII anonymization service (Microsoft)
4. **Tesseract OCR** - Optical character recognition for scanned PDFs
5. **OpenAI API** - AI-powered field extraction

---

## **Quick Start**

### **Prerequisites**

- Docker & Docker Compose
- Ollama (running on host machine) & Local Models: ollama pull deepseek-r1:7b or gemma3:12b
- Cloud LLM API Key (if using cloud LLMs)

### **Installation**

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/ai-document-analyzer.git
cd ai-document-analyzer
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

3. **Start all services**
```bash
docker-compose up --build
```

4. **Access the API**
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/v1/health

---

## **Usage**

### **API Endpoints**

#### **1. Health Check**
```bash
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-05T10:30:00Z",
  "services": {
    "presidio_analyzer": true,
    "presidio_anonymizer": true
  }
}
```

---

#### **2. Analyze Document**
```bash
POST /api/v1/analyze
```

**Parameters:**
- `file` (required): PDF file to analyze
- `document_type` (optional): Type of document (`contract`, `invoice`, `resume`, `auto`)
- `enable_ocr` (optional): Enable OCR for scanned documents (default: `true`)
- `anonymize_pii` (optional): Anonymize PII before AI processing (default: `true`)

**Example using cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze?document_type=contract&anonymize_pii=true" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/contract.pdf"
```

**Example using Python:**
```python
import requests

url = "http://localhost:8000/api/v1/analyze"
files = {"file": open("contract.pdf", "rb")}
params = {
    "document_type": "contract",
    "anonymize_pii": True,
    "enable_ocr": True
}

response = requests.post(url, files=files, params=params)
result = response.json()

print(f"Extracted {len(result['extracted_fields'])} fields")
print(f"Found {len(result['pii_entities_found'])} PII entities")
print(f"Confidence: {result['confidence']}")
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_type": "contract",
  "extracted_fields": {
    "contract_type": {
      "field_name": "contract_type",
      "value": "Employment Agreement",
      "confidence": 0.9,
      "source": "ai_extraction"
    },
    "parties": {
      "field_name": "parties",
      "value": "Employer: <PERSON>, Employee: <PERSON>",
      "confidence": 0.9,
      "source": "ai_extraction"
    },
    "effective_date": {
      "field_name": "effective_date",
      "value": "<DATE>",
      "confidence": 0.9,
      "source": "ai_extraction"
    },
    "contract_value": {
      "field_name": "contract_value",
      "value": "$85,000 annual salary",
      "confidence": 0.9,
      "source": "ai_extraction"
    }
  },
  "anonymization_performed": true,
  "pii_entities_found": [
    {
      "entity_type": "PERSON",
      "text": "John Smith",
      "start": 45,
      "end": 55,
      "score": 0.95
    },
    {
      "entity_type": "EMAIL_ADDRESS",
      "text": "john.smith@example.com",
      "start": 120,
      "end": 142,
      "score": 0.98
    },
    {
      "entity_type": "DATE_TIME",
      "text": "January 15, 2024",
      "start": 200,
      "end": 216,
      "score": 0.92
    }
  ],
  "confidence": 0.87,
  "processing_time_seconds": 3.45,
  "processed_at": "2026-02-05T10:30:00Z"
}
```

---

## 🔧 **Configuration**

### **Environment Variables**

Create a `.env` file in the project root:
```env
# Required
OPENAI_URL=http://host.docker.internal:11434/v1 (or your cloud LLM url)
OPENAI_API_KEY=ollama (or your cloud api key)
OPENAI_MODEL=deepseek-r1:7b (or your preferred model)
# Optional (defaults shown)
PRESIDIO_ANALYZER_URL=http://presidio-analyzer:3000
PRESIDIO_ANONYMIZER_URL=http://presidio-anonymizer:3000
ENVIRONMENT=development
```

### **Supported Document Types**

The system can automatically detect or you can specify:

- **`contract`** - Employment agreements, service contracts, NDAs
- **`invoice`** - Bills, receipts, purchase orders
- **`resume`** - CVs, job applications
- **`auto`** - Automatic detection (default)

### **PII Entity Types Detected**

- Person names (PERSON)
- Email addresses (EMAIL_ADDRESS)
- Phone numbers (PHONE_NUMBER)
- Credit card numbers (CREDIT_CARD)
- Social Security Numbers (US_SSN)
- IP addresses (IP_ADDRESS)
- Locations (LOCATION)
- Dates and times (DATE_TIME)
- URLs (URL)
- Bank account numbers (US_BANK_NUMBER)
- Driver's license numbers (US_DRIVER_LICENSE)
- Passport numbers (US_PASSPORT)

---

## **Development**

### **Local Development Setup**

If you want to develop without Docker:

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Start Presidio services**
```bash
docker-compose up presidio-analyzer presidio-anonymizer
```

4. **Run the FastAPI app locally**
```bash
# Update .env with localhost URLs
PRESIDIO_ANALYZER_URL=http://localhost:5002
PRESIDIO_ANONYMIZER_URL=http://localhost:5001

# Run
python main.py
```

### **Project Structure**
```
ai-document-analyzer/
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # FastAPI app container
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
├── .dockerignore              # Docker build exclusions
├── main.py                     # FastAPI application entry point
├── README.md                   # This file
│
├── app/
│   ├── __init__.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoints
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_service.py      # PDF extraction & OCR
│   │   ├── presidio_client.py  # Presidio API client
│   │   └── extraction_service.py # AI field extraction
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic data models
│   │
│   └── utils/
│       ├── __init__.py
│       └── config.py           # Configuration management
```

### **Running Tests**
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v
```

---

## **Docker Commands**
```bash
# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# Rebuild containers
docker-compose up --build

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f api

# Check service status
docker-compose ps

# Restart a specific service
docker-compose restart api
```

---

## 📊 **Performance**

**Typical Processing Times:**
- Small PDF (1-5 pages, text-based): 2-4 seconds
- Medium PDF (5-20 pages, text-based): 4-8 seconds
- Scanned PDF with OCR (1-5 pages): 10-20 seconds
- Large scanned PDF (20+ pages): 30-60 seconds

**Optimization Tips:**
- Disable OCR for text-based PDFs (`enable_ocr=false`)
- Use faster OpenAI models (e.g., `gpt-4o-mini` instead of `gpt-4`)
- Scale Presidio services horizontally for high throughput

---

## **Security & Privacy**

### **Privacy-First Design**

1. **PII Detection** - All sensitive information is detected before AI processing
2. **Anonymization** - PII is replaced with placeholders (e.g., `<EMAIL>`, `<PERSON>`)
3. **Reversible** - Original values can be restored for authorized users
4. **No Storage** - Documents are processed in-memory and not persisted

### **Best Practices**

- ✅ Always enable `anonymize_pii=true` for sensitive documents
- ✅ Use environment variables for API keys (never commit them)
- ✅ Run Presidio services in private networks
- ✅ Implement rate limiting in production
- ✅ Add authentication/authorization for production deployments

### **GDPR Compliance**

This system helps with GDPR compliance by:
- Detecting and anonymizing personal data before external processing
- Providing explainability (what PII was found and where)
- Minimizing data exposure to third-party services (OpenAI)

---

## **Deployment**

### **Production Deployment**

For production, consider:

1. **Add Authentication**
```python
# Example: API key authentication
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    # Verify API key logic
    ...
```

2. **Use HTTPS**
```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
```

3. **Add Rate Limiting**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/analyze")
@limiter.limit("10/minute")
async def analyze_document(...):
    ...
```

4. **Deploy to Cloud**

**AWS ECS:**
```bash
# Build and push to ECR
docker build -t ai-document-analyzer .
docker tag ai-document-analyzer:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-document-analyzer:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-document-analyzer:latest
```

**Google Cloud Run:**
```bash
gcloud run deploy ai-document-analyzer \
  --image gcr.io/<project-id>/ai-document-analyzer \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Railway:**
```bash
# Connect GitHub repo to Railway
# Deploy automatically on push
```

---

## **Troubleshooting**

### **Common Issues**

#### **1. Presidio services not starting**
```bash
# Check if services are running
docker-compose ps

# Check logs
docker-compose logs presidio-analyzer
docker-compose logs presidio-anonymizer

# Restart services
docker-compose restart presidio-analyzer presidio-anonymizer
```

#### **2. OCR not working**
```bash
# Verify Tesseract is installed in container
docker-compose exec api tesseract --version

# If missing, rebuild
docker-compose up --build
```

#### **3. OpenAI API errors**
```bash
# Verify API key is set
docker-compose exec api printenv OPENAI_API_KEY

# Check OpenAI status
curl https://status.openai.com/
```

#### **4. Out of memory errors**
```bash
# Increase Docker memory limit
# Docker Desktop > Settings > Resources > Memory
# Increase to at least 4GB
```

---

## **Roadmap**

- [ ] Support for more document formats (DOCX, images, etc.)
- [ ] Batch processing API endpoint
- [ ] Database integration for storing results
- [ ] User authentication and multi-tenancy
- [ ] Custom entity recognizers (industry-specific PII)
- [ ] Support for multiple languages
- [ ] Web UI for document upload and results viewing
- [ ] Webhook notifications for async processing
- [ ] Export to multiple formats (CSV, Excel, JSON)
- [ ] Performance metrics and monitoring dashboard

---

## **Contributing**

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- [Microsoft Presidio](https://microsoft.github.io/presidio/) - PII detection and anonymization
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [OpenAI](https://openai.com/) - Language model API
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Optical character recognition

---

## **Contact**

**Bart Porcincula**
- Portfolio: [https://bart-porcincula.lovable.app/](https://bart-porcincula.lovable.app/)
- LinkedIn: [https://www.linkedin.com/in/porcinculabart/](https://www.linkedin.com/in/porcinculabart/)
- Email: porcincula.bart@gmail.com
- Upwork: [https://www.upwork.com/freelancers/~01830e4a35fdb4a629](https://www.upwork.com/freelancers/~01830e4a35fdb4a629)

---

## **Hire Me**

I specialize in building backend systems, AI integrations, and automation tools. Available for:
- Custom document processing systems
- Privacy-focused AI applications
- API development and microservices
- Cloud architecture and deployment

**Rate:** $25-30/hr | **Availability:** 20-30 hrs/week

[Contact me](mailto:porcincula.developer@gmail.com) for a quote.

---

**⭐ If you find this project useful, please consider giving it a star!**
```

---

## **Additional Files to Create**

### **LICENSE**
```
MIT License

Copyright (c) 2026 Bart P.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.