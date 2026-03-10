"""
Async Processing Unit Tests

This module contains unit tests for asynchronous document processing functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from celery import Celery
from app.tasks.document_tasks import process_document, process_batch
from app.services.task_result_service import TaskResultService
from app.services.task_progress_service import TaskProgressService
from app.models.schemas import ProcessingResult, ProcessingError


class TestAsyncDocumentProcessing:
    """Test async document processing tasks."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_task_result_service = Mock(spec=TaskResultService)
        self.mock_task_progress_service = Mock(spec=TaskProgressService)
        
    @pytest.mark.asyncio
    async def test_process_document_success(self):
        """Test successful document processing."""
        # Mock dependencies
        with patch('app.tasks.document_tasks.pdf_service') as mock_pdf_service, \
             patch('app.tasks.document_tasks.extraction_service') as mock_extraction_service:
            
            # Setup mocks
            mock_pdf_service.extract_text.return_value = "Test document content"
            mock_extraction_service.extract_pii.return_value = ProcessingResult(
                id="test-result-id",
                text="Test document content",
                pii_entities=[],
                statistics={},
                processing_time=1.0,
                language="en"
            )
            
            # Call the task
            result = await process_document.apply_async(
                args=["test_file.pdf", "pdf", "test_user"]
            ).get()
            
            # Verify result
            assert result['status'] == 'success'
            assert result['task_id'] is not None
            assert result['result_id'] == "test-result-id"
    
    @pytest.mark.asyncio
    async def test_process_document_with_error(self):
        """Test document processing with error."""
        # Mock dependencies to raise an error
        with patch('app.tasks.document_tasks.pdf_service') as mock_pdf_service:
            mock_pdf_service.extract_text.side_effect = Exception("File not found")
            
            # Call the task
            result = await process_document.apply_async(
                args=["nonexistent.pdf", "pdf", "test_user"]
            ).get()
            
            # Verify error result
            assert result['status'] == 'failed'
            assert 'File not found' in result['error']
    
    @pytest.mark.asyncio
    async def test_process_document_timeout(self):
        """Test document processing timeout."""
        # Mock dependencies to simulate timeout
        with patch('app.tasks.document_tasks.pdf_service') as mock_pdf_service:
            mock_pdf_service.extract_text.side_effect = asyncio.TimeoutError()
            
            # Call the task with timeout
            with pytest.raises(asyncio.TimeoutError):
                await process_document.apply_async(
                    args=["test_file.pdf", "pdf", "test_user"]
                ).get(timeout=1)
    
    @pytest.mark.asyncio
    async def test_process_batch_success(self):
        """Test successful batch processing."""
        # Mock dependencies
        with patch('app.tasks.document_tasks.process_document.apply_async') as mock_process_doc:
            # Setup mock to return successful results
            mock_process_doc.return_value.get.return_value = {
                'status': 'success',
                'result_id': 'result-1',
                'task_id': 'task-1'
            }
            
            # Call the batch task
            result = await process_batch.apply_async(
                args=[["file1.pdf", "file2.pdf"], "test_user"]
            ).get()
            
            # Verify result
            assert result['status'] == 'success'
            assert result['batch_id'] is not None
            assert result['summary']['total_files'] == 2
            assert result['summary']['successful'] == 2
            assert result['summary']['failed'] == 0
    
    @pytest.mark.asyncio
    async def test_process_batch_partial_failure(self):
        """Test batch processing with partial failures."""
        # Mock dependencies with mixed results
        with patch('app.tasks.document_tasks.process_document.apply_async') as mock_process_doc:
            def mock_get_result():
                if mock_get_result.call_count == 1:
                    return Mock(get=lambda: {
                        'status': 'success',
                        'result_id': 'result-1',
                        'task_id': 'task-1'
                    })
                else:
                    return Mock(get=lambda: {
                        'status': 'failed',
                        'error': 'Processing failed',
                        'task_id': 'task-2'
                    })
            
            mock_process_doc.side_effect = mock_get_result
            
            # Call the batch task
            result = await process_batch.apply_async(
                args=[["file1.pdf", "file2.pdf"], "test_user"]
            ).get()
            
            # Verify result
            assert result['status'] == 'success'  # Batch itself succeeds
            assert result['summary']['total_files'] == 2
            assert result['summary']['successful'] == 1
            assert result['summary']['failed'] == 1


class TestTaskResultService:
    """Test task result service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TaskResultService()
        
    @patch('redis.Redis.setex')
    def test_store_result_success(self, mock_setex):
        """Test successful result storage."""
        mock_setex.return_value = True
        
        result = ProcessingResult(
            id="test-result",
            text="Test content",
            pii_entities=[],
            statistics={},
            processing_time=1.0,
            language="en"
        )
        
        success = self.service.store_result(
            task_id="test-task",
            result=result,
            file_path="test.pdf",
            file_type="pdf",
            user_id="test_user"
        )
        
        assert success is True
        mock_setex.assert_called_once()
    
    @patch('redis.Redis.get')
    def test_get_result_success(self, mock_get):
        """Test successful result retrieval."""
        mock_get.return_value = '{"task_id": "test-task", "status": "completed"}'
        
        result = self.service.get_result("test-task")
        
        assert result is not None
        assert result['task_id'] == "test-task"
        assert result['status'] == "completed"
    
    @patch('redis.Redis.get')
    def test_get_result_not_found(self, mock_get):
        """Test result retrieval when not found."""
        mock_get.return_value = None
        
        result = self.service.get_result("nonexistent-task")
        
        assert result is None


class TestTaskProgressService:
    """Test task progress service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TaskProgressService()
        
    @patch('redis.Redis.setex')
    def test_update_progress_success(self, mock_setex):
        """Test successful progress update."""
        mock_setex.return_value = True
        
        success = self.service.update_progress(
            task_id="test-task",
            stage="processing",
            message="Processing document",
            progress=50.0
        )
        
        assert success is True
        mock_setex.assert_called_once()
    
    @patch('redis.Redis.get')
    def test_get_progress_success(self, mock_get):
        """Test successful progress retrieval."""
        mock_get.return_value = '{"task_id": "test-task", "stage": "processing", "progress": 50.0}'
        
        progress = self.service.get_progress("test-task")
        
        assert progress is not None
        assert progress['task_id'] == "test-task"
        assert progress['stage'] == "processing"
        assert progress['progress'] == 50.0
    
    @patch('redis.Redis.zrevrange')
    @patch('redis.Redis.get')
    def test_get_active_tasks(self, mock_get, mock_zrevrange):
        """Test retrieval of active tasks."""
        mock_zrevrange.return_value = [b"task-1", b"task-2"]
        mock_get.side_effect = [
            '{"task_id": "task-1", "stage": "processing"}',
            '{"task_id": "task-2", "stage": "completed"}'
        ]
        
        active_tasks = self.service.get_active_tasks()
        
        # Only task-1 should be active (task-2 is completed)
        assert len(active_tasks) == 1
        assert active_tasks[0]['task_id'] == "task-1"


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker initial state."""
        from app.middleware.circuit_breaker import CircuitBreaker
        
        circuit = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60,
            name="TestCircuit"
        )
        
        assert circuit.state.name == "CLOSED"
        assert circuit.failure_count == 0
        assert circuit.total_requests == 0
    
    def test_circuit_breaker_failure_counting(self):
        """Test circuit breaker failure counting."""
        from app.middleware.circuit_breaker import CircuitBreaker
        
        circuit = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=60,
            name="TestCircuit"
        )
        
        # Simulate failures
        def failing_function():
            raise Exception("Service unavailable")
        
        # First failure
        try:
            circuit.call(failing_function)
        except Exception:
            pass
        
        assert circuit.failure_count == 1
        assert circuit.state.name == "CLOSED"
        
        # Second failure (should open circuit)
        try:
            circuit.call(failing_function)
        except Exception:
            pass
        
        assert circuit.failure_count == 2
        assert circuit.state.name == "OPEN"
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery."""
        from app.middleware.circuit_breaker import CircuitBreaker
        import time
        
        circuit = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=1,  # Short timeout for testing
            name="TestCircuit"
        )
        
        # Open the circuit
        def failing_function():
            raise Exception("Service unavailable")
        
        try:
            circuit.call(failing_function)
        except Exception:
            pass
        
        assert circuit.state.name == "OPEN"
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Circuit should attempt reset (half-open)
        def successful_function():
            return "Success"
        
        result = circuit.call(successful_function)
        assert result == "Success"
        assert circuit.state.name == "CLOSED"


class TestWebhookService:
    """Test webhook service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = Mock()
        
    @patch('requests.post')
    def test_send_webhook_success(self, mock_post):
        """Test successful webhook sending."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "OK"
        
        # This would need actual implementation in the service
        # For now, just verify the structure
        assert True  # Placeholder for actual webhook test
    
    def test_validate_webhook_url_valid(self):
        """Test webhook URL validation with valid URL."""
        from app.config.webhook_config import validate_webhook_url
        
        result = validate_webhook_url("https://example.com/webhook")
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_validate_webhook_url_invalid(self):
        """Test webhook URL validation with invalid URL."""
        from app.config.webhook_config import validate_webhook_url
        
        result = validate_webhook_url("invalid-url")
        
        assert result['valid'] is False
        assert len(result['errors']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])