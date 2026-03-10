"""
Webhook Configuration Module

This module contains configuration settings for webhook callbacks
including URL validation, retry logic, and timeout handling.
"""

import os
from typing import Dict, Any
from urllib.parse import urlparse
import re

# Webhook Configuration
WEBHOOK_TIMEOUT = int(os.getenv('WEBHOOK_TIMEOUT', '30'))  # 30 seconds default
WEBHOOK_MAX_RETRIES = int(os.getenv('WEBHOOK_MAX_RETRIES', '3'))
WEBHOOK_RETRY_DELAY = int(os.getenv('WEBHOOK_RETRY_DELAY', '5'))  # 5 seconds
WEBHOOK_RETRY_BACKOFF = float(os.getenv('WEBHOOK_RETRY_BACKOFF', '2.0'))  # Exponential backoff

# Security Configuration
WEBHOOK_SECRET_KEY = os.getenv('WEBHOOK_SECRET_KEY', '')
WEBHOOK_SIGNATURE_HEADER = os.getenv('WEBHOOK_SIGNATURE_HEADER', 'X-Webhook-Signature')
WEBHOOK_SIGNATURE_ALGORITHM = os.getenv('WEBHOOK_SIGNATURE_ALGORITHM', 'sha256')

# URL Validation
ALLOWED_WEBHOOK_SCHEMES = ['http', 'https']
ALLOWED_WEBHOOK_DOMAINS = os.getenv('ALLOWED_WEBHOOK_DOMAINS', '').split(',')
BLOCKED_WEBHOOK_IPS = os.getenv('BLOCKED_WEBHOOK_IPS', '').split(',')

# Rate Limiting
WEBHOOK_RATE_LIMIT = int(os.getenv('WEBHOOK_RATE_LIMIT', '100'))  # requests per minute
WEBHOOK_BURST_LIMIT = int(os.getenv('WEBHOOK_BURST_LIMIT', '10'))  # burst requests


def validate_webhook_url(url: str) -> Dict[str, Any]:
    """
    Validate a webhook URL.
    
    Args:
        url: The webhook URL to validate
        
    Returns:
        Dictionary with validation result
    """
    result = {
        'valid': False,
        'errors': [],
        'warnings': []
    }
    
    if not url:
        result['errors'].append('Webhook URL cannot be empty')
        return result
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        result['errors'].append(f'Invalid URL format: {str(e)}')
        return result
    
    # Check scheme
    if parsed.scheme not in ALLOWED_WEBHOOK_SCHEMES:
        result['errors'].append(f'Unsupported scheme: {parsed.scheme}. Only http and https are allowed')
        return result
    
    # Check hostname
    if not parsed.hostname:
        result['errors'].append('URL must include a hostname')
        return result
    
    # Check for localhost in production
    if parsed.hostname in ['localhost', '127.0.0.1', '::1']:
        if os.getenv('ENVIRONMENT', 'development') == 'production':
            result['warnings'].append('Using localhost URL in production environment')
    
    # Check for IP addresses
    ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    if ip_pattern.match(parsed.hostname):
        if parsed.hostname in BLOCKED_WEBHOOK_IPS:
            result['errors'].append(f'IP address {parsed.hostname} is blocked')
            return result
        result['warnings'].append('Using IP address as hostname is not recommended')
    
    # Check port
    if parsed.port:
        if parsed.port < 1 or parsed.port > 65535:
            result['errors'].append(f'Invalid port: {parsed.port}')
            return result
    
    # Check path
    if parsed.path and not parsed.path.startswith('/'):
        result['errors'].append('Path must start with /')
        return result
    
    result['valid'] = True
    return result


def get_webhook_config() -> Dict[str, Any]:
    """Get complete webhook configuration."""
    return {
        'timeout': WEBHOOK_TIMEOUT,
        'max_retries': WEBHOOK_MAX_RETRIES,
        'retry_delay': WEBHOOK_RETRY_DELAY,
        'retry_backoff': WEBHOOK_RETRY_BACKOFF,
        'secret_key': WEBHOOK_SECRET_KEY,
        'signature_header': WEBHOOK_SIGNATURE_HEADER,
        'signature_algorithm': WEBHOOK_SIGNATURE_ALGORITHM,
        'allowed_schemes': ALLOWED_WEBHOOK_SCHEMES,
        'allowed_domains': ALLOWED_WEBHOOK_DOMAINS,
        'blocked_ips': BLOCKED_WEBHOOK_IPS,
        'rate_limit': WEBHOOK_RATE_LIMIT,
        'burst_limit': WEBHOOK_BURST_LIMIT
    }


def is_webhook_configured() -> bool:
    """Check if webhook functionality is properly configured."""
    return bool(WEBHOOK_SECRET_KEY and WEBHOOK_SIGNATURE_HEADER)


def calculate_retry_delay(attempt: int) -> int:
    """
    Calculate retry delay using exponential backoff.
    
    Args:
        attempt: Current retry attempt number (0-based)
        
    Returns:
        Delay in seconds
    """
    delay = WEBHOOK_RETRY_DELAY * (WEBHOOK_RETRY_BACKOFF ** attempt)
    return min(int(delay), 300)  # Cap at 5 minutes