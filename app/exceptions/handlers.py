# app/exceptions/handlers.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback

logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler that prevents sensitive information leakage"""
    
    # Log the full error for debugging
    logger.error(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "request_path": str(request.url.path),
            "request_method": request.method,
            "client_ip": request.client.host if request.client else "Unknown"
        }
    )
    
    # Return sanitized error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "An error occurred while processing your request",
            "status_code": exc.status_code,
            "timestamp": None  # Will be set by FastAPI
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom validation exception handler"""
    
    # Log the validation error
    logger.error(
        f"Validation Error: {exc.errors()}",
        extra={
            "request_path": str(request.url.path),
            "request_method": request.method,
            "client_ip": request.client.host if request.client else "Unknown"
        }
    )
    
    # Return sanitized validation error response
    return JSONResponse(
        status_code=422,
        content={
            "error": "Invalid request data",
            "status_code": 422,
            "message": "Please check your request parameters and try again"
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unhandled exceptions"""
    
    # Log the full traceback
    logger.error(
        f"Unhandled Exception: {str(exc)}",
        exc_info=True,
        extra={
            "request_path": str(request.url.path),
            "request_method": request.method,
            "client_ip": request.client.host if request.client else "Unknown"
        }
    )
    
    # Return generic error response
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "message": "An unexpected error occurred. Please try again later."
        }
    )

def setup_exception_handlers(app):
    """Setup custom exception handlers for the FastAPI app"""
    
    # Override default HTTP exception handler
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Override validation exception handler
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Add general exception handler
    app.add_exception_handler(Exception, general_exception_handler)