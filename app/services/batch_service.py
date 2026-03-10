"""
Batch Processing Service

This service handles batch document processing including ZIP file extraction,
parallel processing, and result aggregation with error handling.
"""

import logging
import tempfile
import zipfile
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from celery import chain, group
from app.tasks.document_tasks import process_document
from app.services.task_result_service import TaskResultService
from app.services.task_progress_service import TaskProgressService
from app.utils.config import get_config

logger = logging.getLogger(__name__)


class BatchProcessingService:
    """Service for handling batch document processing."""
    
    def __init__(self):
        self.task_result_service = TaskResultService()
        self.task_progress_service = TaskProgressService()
        self.max_batch_size = 1000  # Maximum files per batch
        self.max_file_size = 50 * 1024 * 1024  # 50MB max file size
        
    def validate_batch_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate a batch file (ZIP archive).
        
        Args:
            file_path: Path to the ZIP file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return False, f"File size {file_size} exceeds maximum {self.max_file_size}"
            
            if not zipfile.is_zipfile(file_path):
                return False, "File is not a valid ZIP archive"
            
            # Check ZIP contents
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                
                if not file_list:
                    return False, "ZIP file is empty"
                
                if len(file_list) > self.max_batch_size:
                    return False, f"Too many files ({len(file_list)}) exceeds maximum {self.max_batch_size}"
                
                # Validate individual files
                for file_name in file_list:
                    if file_name.endswith('/'):
                        continue  # Skip directories
                    
                    file_info = zip_file.getinfo(file_name)
                    if file_info.file_size > self.max_file_size:
                        return False, f"File {file_name} exceeds maximum size"
                    
                    # Check file extension
                    ext = Path(file_name).suffix.lower().lstrip('.')
                    if ext not in ['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'tiff', 'bmp']:
                        return False, f"Unsupported file type: {ext}"
            
            return True, "Valid batch file"
            
        except Exception as e:
            logger.error(f"Error validating batch file {file_path}: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def extract_batch_files(self, zip_path: str, extract_to: str) -> Tuple[List[str], List[Dict[str, str]]]:
        """
        Extract files from a ZIP archive.
        
        Args:
            zip_path: Path to the ZIP file
            extract_to: Directory to extract files to
            
        Returns:
            Tuple of (extracted_file_paths, extraction_errors)
        """
        extracted_files = []
        errors = []
        
        try:
            os.makedirs(extract_to, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                for file_info in zip_file.infolist():
                    if file_info.filename.endswith('/'):
                        continue  # Skip directories
                    
                    try:
                        # Extract file
                        zip_file.extract(file_info, extract_to)
                        extracted_path = os.path.join(extract_to, file_info.filename)
                        extracted_files.append(extracted_path)
                        
                    except Exception as e:
                        errors.append({
                            'file': file_info.filename,
                            'error': f"Extraction failed: {str(e)}"
                        })
                        logger.error(f"Failed to extract {file_info.filename}: {str(e)}")
            
            return extracted_files, errors
            
        except Exception as e:
            logger.error(f"Error extracting batch files from {zip_path}: {str(e)}")
            errors.append({
                'file': zip_path,
                'error': f"Extraction failed: {str(e)}"
            })
            return [], errors
    
    def process_batch(self, zip_file_path: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a batch of documents from a ZIP file.
        
        Args:
            zip_file_path: Path to the ZIP file containing documents
            user_id: Optional user identifier
            
        Returns:
            Batch processing result summary
        """
        batch_id = None
        temp_dir = None
        
        try:
            # Validate batch file
            is_valid, validation_message = self.validate_batch_file(zip_file_path)
            if not is_valid:
                return {
                    'status': 'failed',
                    'error': validation_message,
                    'batch_id': None
                }
            
            # Create temporary directory for extraction
            temp_dir = tempfile.mkdtemp(prefix='batch_processing_')
            
            # Extract files
            extracted_files, extraction_errors = self.extract_batch_files(
                zip_file_path, temp_dir
            )
            
            if not extracted_files:
                return {
                    'status': 'failed',
                    'error': 'No files could be extracted from batch',
                    'extraction_errors': extraction_errors,
                    'batch_id': None
                }
            
            # Determine file types and create processing tasks
            processing_tasks = []
            file_mappings = {}
            
            for file_path in extracted_files:
                file_name = os.path.basename(file_path)
                file_type = Path(file_name).suffix.lower().lstrip('.')
                
                # Map file path to original name for result tracking
                file_mappings[file_path] = file_name
                
                # Create processing task
                task = process_document.apply_async(
                    args=[file_path, file_type, user_id],
                    queue='batch_processing'
                )
                processing_tasks.append(task)
            
            # Wait for all tasks to complete with timeout
            batch_results = []
            successful = 0
            failed = 0
            
            for i, task in enumerate(processing_tasks):
                try:
                    result = task.get(timeout=600)  # 10 minute timeout per file
                    
                    if result['status'] == 'success':
                        successful += 1
                        batch_results.append({
                            'original_file': file_mappings[task.args[0]],
                            'status': 'success',
                            'result_id': result['result_id'],
                            'task_id': result['task_id']
                        })
                    else:
                        failed += 1
                        batch_results.append({
                            'original_file': file_mappings[task.args[0]],
                            'status': 'failed',
                            'error': result.get('error'),
                            'task_id': task.id
                        })
                        
                except Exception as e:
                    failed += 1
                    batch_results.append({
                        'original_file': file_mappings.get(task.args[0], 'unknown'),
                        'status': 'failed',
                        'error': str(e),
                        'task_id': task.id
                    })
                
                # Update progress
                progress_percent = ((i + 1) / len(processing_tasks)) * 100
                if batch_id:
                    self.task_progress_service.update_progress(
                        task_id=batch_id,
                        stage='processing_batch',
                        message=f'Processed {i + 1}/{len(processing_tasks)} files',
                        progress=progress_percent
                    )
            
            # Create batch result summary
            batch_summary = {
                'batch_id': batch_id,
                'total_files': len(processing_tasks),
                'successful': successful,
                'failed': failed,
                'extraction_errors': extraction_errors,
                'results': batch_results,
                'user_id': user_id,
                'timestamp': None  # Will be set by task result service
            }
            
            # Store batch result
            batch_task = process_document.si(None, None, user_id)  # Create a dummy task for batch ID
            batch_id = batch_task.freeze().id
            
            self.task_result_service.store_batch_result(
                task_id=batch_id,
                batch_result=batch_summary
            )
            
            # Update final progress
            self.task_progress_service.update_progress(
                task_id=batch_id,
                stage='completed',
                message=f'Batch processing completed: {successful} successful, {failed} failed',
                completed=True
            )
            
            return {
                'status': 'success',
                'batch_id': batch_id,
                'summary': batch_summary
            }
            
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'batch_id': batch_id
            }
        
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory {temp_dir}: {str(e)}")
    
    def process_large_batch(self, zip_file_path: str, user_id: Optional[str] = None, 
                           chunk_size: int = 100) -> Dict[str, Any]:
        """
        Process large batches by chunking them into smaller groups.
        
        Args:
            zip_file_path: Path to the ZIP file
            user_id: Optional user identifier
            chunk_size: Number of files to process in each chunk
            
        Returns:
            Batch processing result summary
        """
        try:
            # Validate batch file
            is_valid, validation_message = self.validate_batch_file(zip_file_path)
            if not is_valid:
                return {
                    'status': 'failed',
                    'error': validation_message
                }
            
            # Extract files
            temp_dir = tempfile.mkdtemp(prefix='large_batch_processing_')
            extracted_files, extraction_errors = self.extract_batch_files(
                zip_file_path, temp_dir
            )
            
            if not extracted_files:
                return {
                    'status': 'failed',
                    'error': 'No files could be extracted from batch',
                    'extraction_errors': extraction_errors
                }
            
            # Process files in chunks
            all_results = []
            total_successful = 0
            total_failed = 0
            
            for i in range(0, len(extracted_files), chunk_size):
                chunk_files = extracted_files[i:i + chunk_size]
                chunk_results = self._process_chunk(chunk_files, user_id)
                
                all_results.extend(chunk_results['results'])
                total_successful += chunk_results['successful']
                total_failed += chunk_results['failed']
                
                logger.info(f"Completed chunk {i//chunk_size + 1}: {chunk_results['successful']} successful, {chunk_results['failed']} failed")
            
            # Clean up
            import shutil
            shutil.rmtree(temp_dir)
            
            # Create final summary
            batch_summary = {
                'total_files': len(extracted_files),
                'successful': total_successful,
                'failed': total_failed,
                'extraction_errors': extraction_errors,
                'results': all_results,
                'user_id': user_id
            }
            
            return {
                'status': 'success',
                'summary': batch_summary
            }
            
        except Exception as e:
            logger.error(f"Error in large batch processing: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _process_chunk(self, file_paths: List[str], user_id: Optional[str]) -> Dict[str, Any]:
        """Process a chunk of files."""
        results = []
        successful = 0
        failed = 0
        
        for file_path in file_paths:
            try:
                file_name = os.path.basename(file_path)
                file_type = Path(file_name).suffix.lower().lstrip('.')
                
                # Process individual file
                task = process_document.apply_async(
                    args=[file_path, file_type, user_id],
                    queue='batch_processing'
                )
                
                result = task.get(timeout=600)  # 10 minute timeout
                
                if result['status'] == 'success':
                    successful += 1
                    results.append({
                        'original_file': file_name,
                        'status': 'success',
                        'result_id': result['result_id'],
                        'task_id': result['task_id']
                    })
                else:
                    failed += 1
                    results.append({
                        'original_file': file_name,
                        'status': 'failed',
                        'error': result.get('error'),
                        'task_id': task.id
                    })
                    
            except Exception as e:
                failed += 1
                results.append({
                    'original_file': os.path.basename(file_path),
                    'status': 'failed',
                    'error': str(e),
                    'task_id': None
                })
        
        return {
            'results': results,
            'successful': successful,
            'failed': failed
        }
    
    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Get status of a batch processing job.
        
        Args:
            batch_id: Batch processing task ID
            
        Returns:
            Batch status information
        """
        try:
            batch_result = self.task_result_service.get_batch_result(batch_id)
            if not batch_result:
                return {
                    'batch_id': batch_id,
                    'status': 'not_found',
                    'message': 'Batch result not found'
                }
            
            # Get progress information
            progress = self.task_progress_service.get_progress(batch_id)
            
            status = {
                'batch_id': batch_id,
                'status': 'completed' if batch_result.get('successful') is not None else 'processing',
                'total_files': batch_result.get('total_files', 0),
                'successful': batch_result.get('successful', 0),
                'failed': batch_result.get('failed', 0),
                'extraction_errors': batch_result.get('extraction_errors', []),
                'progress': progress.get('progress') if progress else None,
                'message': progress.get('message') if progress else 'Batch processing in progress'
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting batch status for {batch_id}: {str(e)}")
            return {
                'batch_id': batch_id,
                'status': 'error',
                'message': f'Error retrieving status: {str(e)}'
            }