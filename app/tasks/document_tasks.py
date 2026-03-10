"""
Document Processing Tasks

This module contains Celery tasks for asynchronous document processing
including PDF, DOCX, and image processing with error handling and progress tracking.
"""

import logging
import traceback
from typing import Dict, Any, Optional, List
from celery import current_task
from celery.exceptions import SoftTimeLimitExceeded
from app.tasks import celery_app
from app.services.pdf_service import PDFService
from app.services.docx_service import DOCXService
from app.services.image_service import ImageService
from app.services.extraction_service import ExtractionService
from app.services.task_result_service import TaskResultService
from app.services.task_progress_service import TaskProgressService
from app.models.schemas import ProcessingResult, ProcessingError
from app.utils.config import get_config

logger = logging.getLogger(__name__)

# Initialize services
pdf_service = PDFService()
docx_service = DOCXService()
image_service = ImageService()
extraction_service = ExtractionService()
task_result_service = TaskResultService()
task_progress_service = TaskProgressService()


@celery_app.task(bind=True, max_retries=3)
def process_document(self, file_path: str, file_type: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a single document asynchronously.
    
    Args:
        file_path: Path to the document file
        file_type: Type of document (pdf, docx, image)
        user_id: Optional user identifier for audit purposes
        
    Returns:
        Processing result or error information
    """
    try:
        # Update task progress
        task_progress_service.update_progress(
            task_id=self.request.id,
            stage='started',
            message=f'Starting processing for {file_type} document'
        )
        
        # Extract text based on file type
        if file_type.lower() == 'pdf':
            task_progress_service.update_progress(
                task_id=self.request.id,
                stage='extracting_text',
                message='Extracting text from PDF'
            )
            text_content = pdf_service.extract_text(file_path)
            
        elif file_type.lower() in ['docx', 'doc']:
            task_progress_service.update_progress(
                task_id=self.request.id,
                stage='extracting_text',
                message='Extracting text from DOCX'
            )
            text_content = docx_service.extract_text(file_path)
            
        elif file_type.lower() in ['jpg', 'jpeg', 'png', 'tiff', 'bmp']:
            task_progress_service.update_progress(
                task_id=self.request.id,
                stage='extracting_text',
                message='Extracting text from image using OCR'
            )
            text_content = image_service.extract_text(file_path)
            
        else:
            raise ValueError(f'Unsupported file type: {file_type}')
        
        # Update progress
        task_progress_service.update_progress(
            task_id=self.request.id,
            stage='text_extraction_complete',
            message=f'Extracted {len(text_content)} characters'
        )
        
        # Process the extracted text
        task_progress_service.update_progress(
            task_id=self.request.id,
            stage='processing_text',
            message='Processing extracted text with Presidio'
        )
        
        result = extraction_service.extract_pii(text_content, file_type)
        
        # Store result
        task_result_service.store_result(
            task_id=self.request.id,
            result=result,
            file_path=file_path,
            file_type=file_type,
            user_id=user_id
        )
        
        # Update final progress
        task_progress_service.update_progress(
            task_id=self.request.id,
            stage='completed',
            message='Document processing completed successfully',
            completed=True
        )
        
        logger.info(f"Document processing completed for task {self.request.id}")
        return {
            'status': 'success',
            'task_id': self.request.id,
            'result_id': result.id,
            'file_type': file_type,
            'file_path': file_path
        }
        
    except SoftTimeLimitExceeded:
        logger.warning(f"Task {self.request.id} exceeded time limit")
        task_progress_service.update_progress(
            task_id=self.request.id,
            stage='timeout',
            message='Task exceeded time limit',
            completed=True,
            error=True
        )
        raise
        
    except Exception as e:
        logger.error(f"Error processing document in task {self.request.id}: {str(e)}")
        error_details = ProcessingError(
            error_type=type(e).__name__,
            error_message=str(e),
            traceback=traceback.format_exc(),
            file_path=file_path,
            file_type=file_type
        )
        
        # Store error result
        task_result_service.store_error(
            task_id=self.request.id,
            error=error_details,
            file_path=file_path,
            file_type=file_type,
            user_id=user_id
        )
        
        # Update progress with error
        task_progress_service.update_progress(
            task_id=self.request.id,
            stage='error',
            message=f'Error: {str(e)}',
            completed=True,
            error=True
        )
        
        # Retry logic
        retry_count = self.request.retries
        if retry_count < self.max_retries:
            logger.info(f"Retrying task {self.request.id}, attempt {retry_count + 1}")
            raise self.retry(exc=e, countdown=60 * (retry_count + 1))  # Exponential backoff
        
        return {
            'status': 'failed',
            'task_id': self.request.id,
            'error': str(e),
            'retry_count': retry_count
        }


@celery_app.task(bind=True)
def process_batch(self, file_paths: List[str], user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a batch of documents asynchronously.
    
    Args:
        file_paths: List of document file paths
        user_id: Optional user identifier for audit purposes
        
    Returns:
        Batch processing summary
    """
    try:
        total_files = len(file_paths)
        successful = 0
        failed = 0
        results = []
        
        task_progress_service.update_progress(
            task_id=self.request.id,
            stage='started',
            message=f'Starting batch processing of {total_files} files'
        )
        
        for i, file_path in enumerate(file_paths):
            try:
                # Determine file type
                file_type = file_path.split('.')[-1].lower()
                
                # Process individual file
                file_result = process_document.apply_async(
                    args=[file_path, file_type, user_id],
                    queue='document_processing'
                )
                
                # Wait for individual task to complete
                result = file_result.get(timeout=600)  # 10 minute timeout per file
                
                if result['status'] == 'success':
                    successful += 1
                    results.append({
                        'file_path': file_path,
                        'status': 'success',
                        'result_id': result['result_id']
                    })
                else:
                    failed += 1
                    results.append({
                        'file_path': file_path,
                        'status': 'failed',
                        'error': result.get('error')
                    })
                    
            except Exception as e:
                failed += 1
                results.append({
                    'file_path': file_path,
                    'status': 'failed',
                    'error': str(e)
                })
            
            # Update batch progress
            progress_percent = ((i + 1) / total_files) * 100
            task_progress_service.update_progress(
                task_id=self.request.id,
                stage='processing_batch',
                message=f'Processed {i + 1}/{total_files} files',
                progress=progress_percent
            )
        
        # Store batch result
        batch_result = {
            'batch_id': self.request.id,
            'total_files': total_files,
            'successful': successful,
            'failed': failed,
            'results': results,
            'user_id': user_id
        }
        
        task_result_service.store_batch_result(
            task_id=self.request.id,
            batch_result=batch_result
        )
        
        # Update final progress
        task_progress_service.update_progress(
            task_id=self.request.id,
            stage='completed',
            message=f'Batch processing completed: {successful} successful, {failed} failed',
            completed=True
        )
        
        logger.info(f"Batch processing completed for task {self.request.id}")
        return batch_result
        
    except Exception as e:
        logger.error(f"Error in batch processing task {self.request.id}: {str(e)}")
        task_progress_service.update_progress(
            task_id=self.request.id,
            stage='error',
            message=f'Batch processing error: {str(e)}',
            completed=True,
            error=True
        )
        raise


@celery_app.task(bind=True)
def process_large_document(self, file_path: str, file_type: str, chunk_size: int = 5000, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process large documents by chunking them into smaller pieces.
    
    Args:
        file_path: Path to the document file
        file_type: Type of document
        chunk_size: Size of text chunks to process
        user_id: Optional user identifier
        
    Returns:
        Aggregated processing result
    """
    try:
        # Extract text
        if file_type.lower() == 'pdf':
            text_content = pdf_service.extract_text(file_path)
        elif file_type.lower() in ['docx', 'doc']:
            text_content = docx_service.extract_text(file_path)
        elif file_type.lower() in ['jpg', 'jpeg', 'png', 'tiff', 'bmp']:
            text_content = image_service.extract_text(file_path)
        else:
            raise ValueError(f'Unsupported file type: {file_type}')
        
        # Split into chunks
        chunks = [text_content[i:i+chunk_size] for i in range(0, len(text_content), chunk_size)]
        total_chunks = len(chunks)
        
        task_progress_service.update_progress(
            task_id=self.request.id,
            stage='chunking',
            message=f'Split document into {total_chunks} chunks'
        )
        
        # Process chunks in parallel
        chunk_tasks = []
        for i, chunk in enumerate(chunks):
            chunk_task = extraction_service.extract_pii.apply_async(
                args=[chunk, file_type],
                kwargs={'chunk_number': i, 'total_chunks': total_chunks},
                queue='document_processing'
            )
            chunk_tasks.append(chunk_task)
        
        # Collect results
        chunk_results = []
        for i, task in enumerate(chunk_tasks):
            try:
                result = task.get(timeout=300)  # 5 minute timeout per chunk
                chunk_results.append(result)
                
                task_progress_service.update_progress(
                    task_id=self.request.id,
                    stage='processing_chunks',
                    message=f'Processed chunk {i + 1}/{total_chunks}',
                    progress=((i + 1) / total_chunks) * 100
                )
            except Exception as e:
                logger.error(f"Error processing chunk {i}: {str(e)}")
                chunk_results.append(None)
        
        # Aggregate results
        aggregated_result = extraction_service.aggregate_chunk_results(chunk_results)
        
        # Store result
        task_result_service.store_result(
            task_id=self.request.id,
            result=aggregated_result,
            file_path=file_path,
            file_type=file_type,
            user_id=user_id
        )
        
        task_progress_service.update_progress(
            task_id=self.request.id,
            stage='completed',
            message='Large document processing completed',
            completed=True
        )
        
        return {
            'status': 'success',
            'task_id': self.request.id,
            'result_id': aggregated_result.id,
            'chunks_processed': len([r for r in chunk_results if r is not None]),
            'total_chunks': total_chunks
        }
        
    except Exception as e:
        logger.error(f"Error processing large document in task {self.request.id}: {str(e)}")
        task_progress_service.update_progress(
            task_id=self.request.id,
            stage='error',
            message=f'Large document processing error: {str(e)}',
            completed=True,
            error=True
        )
        raise