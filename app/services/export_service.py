"""
Export service for different formats (CSV, Excel, JSON).
"""

import csv
import json
import io
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.services.task_result_service import TaskResultService

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting analysis results to different formats."""
    
    def __init__(self):
        self.task_result_service = TaskResultService()
    
    async def export_to_csv(self, task_id: str) -> Optional[str]:
        """Export analysis results to CSV format."""
        try:
            result = await self.task_result_service.get_task_result(task_id)
            if not result:
                return None
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow([
                'Task ID',
                'Document Type',
                'Status',
                'Processing Time (s)',
                'PII Count',
                'Confidence',
                'Field Name',
                'Field Value'
            ])
            
            # Write data
            pii_count = len(result.get('pii_entities_found', []))
            extracted_fields = result.get('extracted_fields', {})
            
            for field_name, field_value in extracted_fields.items():
                writer.writerow([
                    result.get('document_id', ''),
                    result.get('document_type', ''),
                    'completed',  # Assuming completed status
                    result.get('processing_time_seconds', 0),
                    pii_count,
                    result.get('confidence', 0),
                    field_name,
                    str(field_value)
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting CSV for task {task_id}: {str(e)}")
            return None
    
    async def export_to_excel(self, task_id: str) -> Optional[bytes]:
        """Export analysis results to Excel format."""
        try:
            result = await self.task_result_service.get_task_result(task_id)
            if not result:
                return None
            
            # For now, return a simple CSV-like format as Excel
            # In a full implementation, you would use openpyxl or xlsxwriter
            csv_content = await self.export_to_csv(task_id)
            if not csv_content:
                return None
            
            # Convert CSV to bytes (simplified Excel export)
            return csv_content.encode('utf-8')
            
        except Exception as e:
            logger.error(f"Error exporting Excel for task {task_id}: {str(e)}")
            return None
    
    async def export_to_json(self, task_id: str) -> Optional[str]:
        """Export analysis results to JSON format."""
        try:
            result = await self.task_result_service.get_task_result(task_id)
            if not result:
                return None
            
            # Return the result as JSON
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error exporting JSON for task {task_id}: {str(e)}")
            return None
    
    async def export_history_to_csv(self, search: str = "") -> str:
        """Export document history to CSV format."""
        try:
            # Get all history (simplified - would need pagination in real implementation)
            history = await self.task_result_service.get_task_history(
                page=1, 
                page_size=1000,  # Large page size for export
                search=search
            )
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow([
                'Task ID',
                'Filename',
                'Document Type',
                'Status',
                'Created At',
                'Processing Time (s)',
                'File Size (KB)',
                'PII Count'
            ])
            
            # Write data
            for item in history.get('items', []):
                writer.writerow([
                    item.get('task_id', ''),
                    item.get('filename', ''),
                    item.get('document_type', ''),
                    item.get('status', ''),
                    item.get('created_at', ''),
                    item.get('processing_time', 0),
                    item.get('file_size', 0),
                    item.get('pii_count', 0)
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting history CSV: {str(e)}")
            return ""
    
    def format_field_value(self, value: Any) -> str:
        """Format field value for export."""
        if value is None:
            return ""
        elif isinstance(value, (list, dict)):
            return json.dumps(value, default=str)
        else:
            return str(value)
    
    async def export_batch_to_csv(self, task_ids: List[str]) -> Optional[str]:
        """Export multiple tasks to a single CSV file."""
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow([
                'Task ID',
                'Document Type',
                'Status',
                'Processing Time (s)',
                'PII Count',
                'Confidence',
                'Field Name',
                'Field Value'
            ])
            
            # Write data for each task
            for task_id in task_ids:
                result = await self.task_result_service.get_task_result(task_id)
                if result:
                    pii_count = len(result.get('pii_entities_found', []))
                    extracted_fields = result.get('extracted_fields', {})
                    
                    for field_name, field_value in extracted_fields.items():
                        writer.writerow([
                            result.get('document_id', ''),
                            result.get('document_type', ''),
                            'completed',
                            result.get('processing_time_seconds', 0),
                            pii_count,
                            result.get('confidence', 0),
                            field_name,
                            self.format_field_value(field_value)
                        ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting batch CSV: {str(e)}")
            return None
    
    async def export_to_pdf_report(self, task_id: str) -> Optional[bytes]:
        """Export analysis results to PDF report format."""
        try:
            result = await self.task_result_service.get_task_result(task_id)
            if not result:
                return None
            
            # Create a simple text-based PDF report
            # In a full implementation, you would use reportlab or weasyprint
            report_content = f"""
Document Analysis Report
========================

Task ID: {result.get('document_id', '')}
Document Type: {result.get('document_type', '')}
Processing Time: {result.get('processing_time_seconds', 0)} seconds
Confidence: {result.get('confidence', 0)}
PII Entities Found: {len(result.get('pii_entities_found', []))}

Extracted Fields:
-----------------
"""
            
            for field_name, field_value in result.get('extracted_fields', {}).items():
                report_content += f"{field_name}: {self.format_field_value(field_value)}\n"
            
            report_content += f"\nGenerated on: {datetime.utcnow().isoformat()}"
            
            return report_content.encode('utf-8')
            
        except Exception as e:
            logger.error(f"Error exporting PDF report for task {task_id}: {str(e)}")
            return None