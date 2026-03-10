"""
Webhook Service

This service handles sending webhook notifications for task completion,
including retry logic, signature validation, and error handling.
"""

import json
import logging
import hashlib
import hmac
import time
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.config.webhook_config import (
    validate_webhook_url, get_webhook_config, calculate_retry_delay,
    WEBHOOK_TIMEOUT, WEBHOOK_MAX_RETRIES, WEBHOOK_SECRET_KEY,
    WEBHOOK_SIGNATURE_HEADER, WEBHOOK_SIGNATURE_ALGORITHM
)
from app.services.task_result_service import TaskResultService
from app.services.task_progress_service import TaskProgressService

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for sending webhook notifications."""
    
    def __init__(self):
        self.config = get_webhook_config()
        self.task_result_service = TaskResultService()
        self.task_progress_service = TaskProgressService()
        self.retry_delays = []
        
    def send_completion_webhook(self, task_id: str, webhook_url: str, 
                               user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a completion webhook notification for a task.
        
        Args:
            task_id: The task ID that completed
            webhook_url: The webhook URL to send notification to
            user_id: Optional user identifier
            
        Returns:
            Dictionary with webhook result
        """
        try:
            # Validate webhook URL
            validation_result = validate_webhook_url(webhook_url)
            if not validation_result['valid']:
                return {
                    'status': 'failed',
                    'error': f'Invalid webhook URL: {", ".join(validation_result["errors"])}',
                    'task_id': task_id
                }
            
            # Get task result
            task_result = self.task_result_service.get_result(task_id)
            if not task_result:
                return {
                    'status': 'failed',
                    'error': 'Task result not found',
                    'task_id': task_id
                }
            
            # Prepare webhook payload
            payload = self._prepare_webhook_payload(task_id, task_result, user_id)
            
            # Send webhook with retry logic
            result = self._send_webhook_with_retry(webhook_url, payload)
            
            if result['status'] == 'success':
                logger.info(f"Webhook sent successfully for task {task_id}")
            else:
                logger.error(f"Webhook failed for task {task_id}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending webhook for task {task_id}: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'task_id': task_id
            }
    
    def send_batch_completion_webhook(self, batch_id: str, webhook_url: str,
                                     user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a completion webhook notification for a batch processing task.
        
        Args:
            batch_id: The batch task ID that completed
            webhook_url: The webhook URL to send notification to
            user_id: Optional user identifier
            
        Returns:
            Dictionary with webhook result
        """
        try:
            # Validate webhook URL
            validation_result = validate_webhook_url(webhook_url)
            if not validation_result['valid']:
                return {
                    'status': 'failed',
                    'error': f'Invalid webhook URL: {", ".join(validation_result["errors"])}',
                    'batch_id': batch_id
                }
            
            # Get batch result
            batch_result = self.task_result_service.get_batch_result(batch_id)
            if not batch_result:
                return {
                    'status': 'failed',
                    'error': 'Batch result not found',
                    'batch_id': batch_id
                }
            
            # Prepare webhook payload
            payload = self._prepare_batch_webhook_payload(batch_id, batch_result, user_id)
            
            # Send webhook with retry logic
            result = self._send_webhook_with_retry(webhook_url, payload)
            
            if result['status'] == 'success':
                logger.info(f"Batch webhook sent successfully for batch {batch_id}")
            else:
                logger.error(f"Batch webhook failed for batch {batch_id}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending batch webhook for batch {batch_id}: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'batch_id': batch_id
            }
    
    def _prepare_webhook_payload(self, task_id: str, task_result: Dict[str, Any], 
                                user_id: Optional[str]) -> Dict[str, Any]:
        """Prepare the webhook payload for a single task."""
        payload = {
            'event_type': 'task_completed',
            'timestamp': datetime.utcnow().isoformat(),
            'task_id': task_id,
            'user_id': user_id,
            'status': task_result.get('status', 'unknown'),
            'result': task_result
        }
        
        # Add processing statistics if available
        result_data = task_result.get('result_data', {})
        if result_data:
            payload['processing_time'] = result_data.get('processing_time')
            payload['entities_found'] = len(result_data.get('pii_entities', []))
            payload['file_type'] = task_result.get('file_type')
        
        return payload
    
    def _prepare_batch_webhook_payload(self, batch_id: str, batch_result: Dict[str, Any],
                                      user_id: Optional[str]) -> Dict[str, Any]:
        """Prepare the webhook payload for a batch task."""
        payload = {
            'event_type': 'batch_completed',
            'timestamp': datetime.utcnow().isoformat(),
            'batch_id': batch_id,
            'user_id': user_id,
            'status': 'completed',
            'summary': {
                'total_files': batch_result.get('total_files', 0),
                'successful': batch_result.get('successful', 0),
                'failed': batch_result.get('failed', 0),
                'extraction_errors': batch_result.get('extraction_errors', [])
            },
            'results': batch_result.get('results', [])
        }
        
        return payload
    
    def _send_webhook_with_retry(self, webhook_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send webhook with retry logic."""
        last_error = None
        
        for attempt in range(WEBHOOK_MAX_RETRIES + 1):
            try:
                result = self._send_single_webhook(webhook_url, payload)
                
                if result['status'] == 'success':
                    return result
                
                last_error = result.get('error', 'Unknown error')
                
                # If this is the last attempt, break
                if attempt == WEBHOOK_MAX_RETRIES:
                    break
                
                # Calculate delay and wait
                delay = calculate_retry_delay(attempt)
                logger.info(f"Webhook attempt {attempt + 1} failed, retrying in {delay} seconds...")
                time.sleep(delay)
                
            except Exception as e:
                last_error = str(e)
                if attempt == WEBHOOK_MAX_RETRIES:
                    break
                
                delay = calculate_retry_delay(attempt)
                logger.info(f"Webhook attempt {attempt + 1} exception, retrying in {delay} seconds...")
                time.sleep(delay)
        
        return {
            'status': 'failed',
            'error': f'Webhook failed after {WEBHOOK_MAX_RETRIES + 1} attempts: {last_error}'
        }
    
    def _send_single_webhook(self, webhook_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a single webhook request."""
        try:
            # Create signature if secret key is configured
            headers = {'Content-Type': 'application/json'}
            if WEBHOOK_SECRET_KEY:
                signature = self._create_signature(payload)
                headers[WEBHOOK_SIGNATURE_HEADER] = signature
            
            # Send request
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=WEBHOOK_TIMEOUT,
                verify=True  # Enable SSL verification
            )
            
            # Check response
            if response.status_code >= 400:
                return {
                    'status': 'failed',
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'response_code': response.status_code
                }
            
            return {
                'status': 'success',
                'response_code': response.status_code,
                'response_text': response.text
            }
            
        except requests.exceptions.Timeout:
            return {
                'status': 'failed',
                'error': f'Request timed out after {WEBHOOK_TIMEOUT} seconds'
            }
        except requests.exceptions.ConnectionError as e:
            return {
                'status': 'failed',
                'error': f'Connection error: {str(e)}'
            }
        except requests.exceptions.RequestException as e:
            return {
                'status': 'failed',
                'error': f'Request error: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': f'Unexpected error: {str(e)}'
            }
    
    def _create_signature(self, payload: Dict[str, Any]) -> str:
        """Create webhook signature for payload validation."""
        try:
            payload_str = json.dumps(payload, sort_keys=True)
            
            if WEBHOOK_SIGNATURE_ALGORITHM == 'sha256':
                signature = hmac.new(
                    WEBHOOK_SECRET_KEY.encode(),
                    payload_str.encode(),
                    hashlib.sha256
                ).hexdigest()
            else:
                # Default to sha256
                signature = hmac.new(
                    WEBHOOK_SECRET_KEY.encode(),
                    payload_str.encode(),
                    hashlib.sha256
                ).hexdigest()
            
            return signature
            
        except Exception as e:
            logger.error(f"Error creating webhook signature: {str(e)}")
            return ''
    
    def validate_webhook_signature(self, payload: Dict[str, Any], 
                                 signature: str, algorithm: str = 'sha256') -> bool:
        """
        Validate webhook signature for incoming requests.
        
        Args:
            payload: The webhook payload
            signature: The signature header value
            algorithm: The hashing algorithm used
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not WEBHOOK_SECRET_KEY:
            logger.warning("Webhook secret key not configured, skipping signature validation")
            return True
        
        try:
            expected_signature = self._create_signature(payload)
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error validating webhook signature: {str(e)}")
            return False
    
    def get_webhook_stats(self) -> Dict[str, Any]:
        """Get webhook service statistics."""
        return {
            'config': {
                'timeout': WEBHOOK_TIMEOUT,
                'max_retries': WEBHOOK_MAX_RETRIES,
                'retry_delay': self.config['retry_delay'],
                'retry_backoff': self.config['retry_backoff'],
                'signature_enabled': bool(WEBHOOK_SECRET_KEY)
            },
            'retry_delays': self.retry_delays,
            'average_retry_delay': sum(self.retry_delays) / len(self.retry_delays) if self.retry_delays else 0
        }
    
    def cleanup_old_webhooks(self, max_age_hours: int = 24) -> int:
        """
        Clean up old webhook retry data.
        
        Args:
            max_age_hours: Maximum age in hours for webhook data to keep
            
        Returns:
            Number of items cleaned up
        """
        try:
            # This is a placeholder for future implementation
            # Currently, we don't store webhook retry data persistently
            return 0
            
        except Exception as e:
            logger.error(f"Error cleaning up old webhooks: {str(e)}")
            return 0