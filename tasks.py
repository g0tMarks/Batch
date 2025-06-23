import os
import logging
from utils.report_generator import ReportGenerationService
from utils.excel_parser import read_student_data_from_excel
from utils.storage import storage_service, StorageError
import asyncio

def generate_reports_task(user_id, temp_file_path, upload_id, progress_tracker):
    logger = logging.getLogger(__name__)
    output_file_path = None
    try:
        logger.info(f"[RQ] Starting report generation for user {user_id}")
        # Read student data
        student_data = read_student_data_from_excel(temp_file_path)
        if not student_data:
            logger.warning("No valid student data found in the file")
            return {'success': False, 'message': 'No valid student data found in the file.'}
        progress_tracker[user_id] = {
            'current': 0,
            'total': len(student_data),
            'status': 'Processing students...',
            'progress': 0
        }
        # Generate reports
        report_service = ReportGenerationService()
        reports = asyncio.run(report_service.generate_reports_with_progress(
            student_data,
            user_id,
            progress_tracker
        ))
        # Create Word document
        output_file_path = asyncio.run(report_service.create_word_doc(reports))
        output_filename = os.path.basename(output_file_path)
        output_storage_path = f"{user_id}/reports/{output_filename}"
        # Upload the generated report to Supabase Storage
        with open(output_file_path, 'rb') as f:
            storage_service.supabase.storage.from_('uploads').upload(
                path=output_storage_path,
                file=f,
                file_options={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
            )
        # Get the public URL for the output file
        output_url = storage_service.supabase.storage.from_('uploads').get_public_url(output_storage_path)
        # Set progress to 100% and status to 'Complete'
        progress_tracker[user_id] = {
            'current': len(student_data),
            'total': len(student_data),
            'status': 'Complete',
            'progress': 100
        }
        # Clean up temp files
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if output_file_path and os.path.exists(output_file_path):
            os.remove(output_file_path)
        return {
            'success': True,
            'filename': output_filename,
            'download_url': f"/download/reports/{output_filename}"
        }
    except Exception as e:
        logger.error(f"[RQ] Error in background job: {e}")
        return {'success': False, 'message': str(e)} 