# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import logging

from app.api.routes import router
from app.utils.config import get_settings
from app.middleware.rate_limit import create_limiter, rate_limit_exceeded_handler
from app.middleware.audit import AuditLoggingMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.exceptions.handlers import setup_exception_handlers
from app.utils.config_validator import validate_config_on_startup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="AI Document Analyzer with PII Anonymization",
    description="Extract structured data from PDFs with privacy-preserving PII anonymization",
    version="1.0.0"
)

# Create and configure rate limiter
limiter = create_limiter()

# Add CORS middleware with environment-based configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost", "*.docker.internal", "0.0.0.0"]
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add audit logging middleware
app.add_middleware(AuditLoggingMiddleware)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Validate configuration on startup
validate_config_on_startup()

# Setup custom exception handlers
setup_exception_handlers(app)

# Include router
app.include_router(router, prefix="/api/v1", tags=["analysis"])

@app.get("/")
async def root():
    return {
        "message": "AI Document Analyzer API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)