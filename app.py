from flask import Flask, request, render_template, redirect, session, url_for, flash, render_template, send_file, jsonify
from supabase_config import supabase, supabase_admin
from functools import wraps
import os
import secrets
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
from utils.excel_parser import read_student_data_from_excel
from utils.report_generator import ReportGenerationService, ReportGenerationError
from utils.storage import storage_service, StorageError
from utils.usage import usage_service, UsageTrackingError
import openpyxl.utils.exceptions
from asgiref.wsgi import WsgiToAsgi
import asyncio

#create uploads directory on boot
os.makedirs("uploads", exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Global progress tracking
progress_tracker = {}

def ensure_uploads_table():
    try:
        # Check if table exists
        result = supabase.table('uploads').select('*').limit(1).execute()
        logger.debug("Uploads table exists")
    except Exception as e:
        logger.error(f"Error checking uploads table: {str(e)}")
        # Create the table if it doesn't exist
        try:
            # Note: You'll need to create this table in Supabase manually
            # with the following structure:
            # - id (uuid, primary key)
            # - user_id (uuid, foreign key to auth.users)
            # - filename (text)
            # - file_path (text)
            # - created_at (timestamp with time zone)
            logger.error("Please create the uploads table in Supabase with the required structure")
        except Exception as create_error:
            logger.error(f"Error creating uploads table: {str(create_error)}")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a secure random key

# Ensure uploads table exists
ensure_uploads_table()

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
logger.debug(f"Upload folder path: {UPLOAD_FOLDER}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form['fullName']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirmPassword']
        school = request.form['school']
        how_did_you_hear = request.form['howDidYouHear']
        newsletter = request.form.get('newsletter') == 'yes'  # Checkbox returns 'yes' or None
        
        # Validate passwords match
        if password != confirm_password:
            return render_template('signup.html', error="Passwords do not match")
        
        try:
            # Sign up the user with Supabase
            result = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "school": school,
                        "how_did_you_hear": how_did_you_hear,
                        "newsletter_signup": newsletter
                    }
                }
            })
            
            # Redirect to a success page or login page
            return render_template('index.html', message="Please check your email to confirm your account")
        except Exception as e:
            return render_template('signup.html', error=str(e))
            
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            result = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            if result.user.email_confirmed_at:
                session['user'] = result.user.id
                return redirect(url_for('download_template'))
            else:
                return render_template('login.html', error="Please verify your email before continuing.")
        except Exception as e:
            return render_template('login.html', error=str(e))
    return render_template('login.html')

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return wrapper

@app.route('/download-template')
@login_required
def download_template():
    """Download template page"""
    return render_template('download.html')

@app.route('/download-template-file')
@login_required
def download_template_file():
    """Download the Excel template from local static directory"""
    return send_file(
        'static/files/template_student_data.xlsx',
        as_attachment=True,
        download_name='template_student_data.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_page():
    if request.method == 'POST':
        logger.info("Upload endpoint hit")
        if 'files' not in request.files:
            logger.warning("No file part in request")
            return jsonify({'error': 'No file part'}), 400

        file = request.files['files']
        logger.info(f"Received file: {file.filename}")
        if file.filename == '':
            logger.warning("No selected file")
            return jsonify({'error': 'No selected file'}), 400

        # Server-side file type validation
        if file and allowed_file(file.filename):
            # Check MIME type for .xlsx
            if file.mimetype != 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                logger.warning(f"Invalid file type: {file.mimetype}")
                return jsonify({'error': 'Invalid file type. Only .xlsx files are allowed.'}), 400

            try:
                # Generate unique filename with timestamp
                original_filename = secure_filename(file.filename)
                filename_without_ext, file_ext = os.path.splitext(original_filename)
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{filename_without_ext}_{timestamp}{file_ext}"
                
                # Save the file to disk temporarily
                temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(temp_file_path)
                logger.info(f"Saved file temporarily to {temp_file_path}")
                
                # Get user ID from session
                user_id = session['user']
                
                # Upload to Supabase Storage
                try:
                    # Create a unique path for the file in storage
                    storage_path = f"{user_id}/{unique_filename}"
                    logger.info(f"Uploading to Supabase Storage: {storage_path}")
                    
                    # Upload the file to Supabase Storage
                    with open(temp_file_path, 'rb') as f:
                        supabase.storage.from_('uploads').upload(
                            path=storage_path,
                            file=f,
                            file_options={"content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
                        )
                    
                    # Get the public URL
                    public_url = supabase.storage.from_('uploads').get_public_url(storage_path)
                    logger.info(f"File uploaded successfully to {public_url}")
                    
                    # Store file info in database
                    result = supabase_admin.table('uploads').insert({
                        'user_id': user_id,
                        'filename': unique_filename,
                        'file_path': storage_path,
                        'created_at': datetime.utcnow().isoformat()
                    }).execute()
                    logger.info(f"Stored file info in database: {result.data}")
                    
                    # Count students
                    import pandas as pd
                    df = pd.read_excel(temp_file_path)
                    student_count = len(df)
                    logger.info(f"Student count: {student_count}")
                    
                    # Clean up temporary file
                    os.remove(temp_file_path)
                    logger.info(f"Cleaned up temporary file: {temp_file_path}")
                    
                    return jsonify({
                        'student_count': student_count,
                        'upload_id': result.data[0]['id'] if result.data else None
                    }), 200
                    
                except Exception as storage_error:
                    logger.error(f"Error uploading to Supabase Storage: {str(storage_error)}")
                    # Clean up temporary file
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    return jsonify({'error': f'Failed to upload file to storage: {str(storage_error)}'}), 500
                    
            except Exception as e:
                logger.error(f"Error processing upload: {str(e)}")
                return jsonify({'error': str(e)}), 500
        else:
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Invalid file type. Only .xlsx files are allowed.'}), 400
            
    return render_template('upload.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/progress')
@login_required
def get_progress():
    """Get the current progress of report generation for the user"""
    user_id = session.get('user')
    if user_id in progress_tracker:
        return jsonify(progress_tracker[user_id])
    else:
        return jsonify({
            'current': 0,
            'total': 0,
            'status': 'No active generation',
            'progress': 0
        })

class ExcelParsingError(Exception):
    """Custom exception for Excel parsing errors"""
    pass

class FileNotFoundError(Exception):
    """Custom exception for file not found errors"""
    pass

@app.route("/generate", methods=["POST"])
@login_required
def generate_report():
    async def _generate():
        temp_file_path = None
        output_file_path = None
        try:
            user_id = session.get('user')
            logger.info(f"Starting report generation process for user {user_id}")
            
            # Initialize progress tracking
            progress_tracker[user_id] = {
                'current': 0,
                'total': 0,
                'status': 'Starting...',
                'progress': 0
            }
            
            # Get the latest uploaded file for the current user
            logger.debug(f"Getting latest upload for user: {user_id}")
            result = supabase.table('uploads').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(1).execute()
            
            if not result.data:
                logger.warning(f"No files found for user {user_id}")
                return jsonify({
                    'success': False,
                    'message': 'No files found. Please upload an Excel file first.'
                }), 400
            
            latest_upload = result.data[0]
            storage_path = latest_upload['file_path']
            upload_id = latest_upload['id']
            
            logger.info(f"Processing file {storage_path} (ID: {upload_id}) for user {user_id}")
            
            # Download file from Supabase Storage
            try:
                logger.info(f"Downloading file from storage: {storage_path}")
                temp_file_path = await download_from_storage(storage_path, user_id)
                logger.info(f"Successfully downloaded file to: {temp_file_path}")
                
                # Process the file
                try:
                    # Read student data
                    logger.info("Starting to read student data from Excel file")
                    student_data = read_student_data_from_excel(temp_file_path)
                    if not student_data:
                        logger.warning("No valid student data found in the file")
                        # Update upload record with error
                        supabase_admin.table('uploads').update({
                            'status': 'error',
                            'error_message': 'No valid student data found in the file'
                        }).eq('id', upload_id).execute()
                        return jsonify({
                            'success': False,
                            'message': 'No valid student data found in the file.'
                        }), 400
                    
                    logger.info(f"Successfully read data for {len(student_data)} students")
                    
                    # Update progress tracking
                    progress_tracker[user_id]['total'] = len(student_data)
                    progress_tracker[user_id]['status'] = 'Processing students...'
                    
                    # Generate reports
                    logger.info("Starting report generation process")
                    report_service = ReportGenerationService()
                    reports = await report_service.generate_reports_with_progress(
                        student_data,
                        user_id,
                        progress_tracker
                    )
                    logger.info(f"Successfully generated {len(reports)} reports")
                    
                    # Create Word document
                    logger.info("Creating Word document with generated reports")
                    output_file_path = await report_service.create_word_doc(reports)
                    logger.info(f"Successfully created Word document at: {output_file_path}")
                    
                    # Upload the generated report to Supabase Storage
                    output_filename = os.path.basename(output_file_path)
                    output_storage_path = f"{user_id}/reports/{output_filename}"
                    logger.info(f"Uploading generated report to storage: {output_storage_path}")
                    
                    with open(output_file_path, 'rb') as f:
                        supabase.storage.from_('uploads').upload(
                            path=output_storage_path,
                            file=f,
                            file_options={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
                        )
                    
                    # Get the public URL for the output file
                    output_url = supabase.storage.from_('uploads').get_public_url(output_storage_path)
                    logger.info(f"Generated report available at: {output_url}")
                    
                    # Update the upload record with the output file URL and success status
                    logger.info(f"Updating upload record {upload_id} with output URL")
                    supabase_admin.table('uploads').update({
                        'output_file_url': output_url,
                        'status': 'completed',
                        'error_message': None
                    }).eq('id', upload_id).execute()
                    
                    # Delete the original Excel file from storage
                    try:
                        logger.info(f"Starting deletion of original Excel file from storage: {storage_path}")
                        await storage_service.delete_file(os.path.basename(storage_path), user_id=user_id)
                        logger.info(f"Successfully deleted original Excel file from storage: {storage_path}")
                    except Exception as delete_error:
                        logger.warning(f"Failed to delete original Excel file {storage_path}: {str(delete_error)}", exc_info=True)
                        # Continue with cleanup even if deletion fails
                    
                    # Clean up temporary files
                    logger.info("Starting cleanup of temporary files")
                    try:
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                            logger.info(f"Successfully deleted temporary file: {temp_file_path}")
                        if os.path.exists(output_file_path):
                            os.remove(output_file_path)
                            logger.info(f"Successfully deleted output file: {output_file_path}")
                        logger.info("Successfully completed cleanup of all temporary files")
                    except Exception as cleanup_error:
                        logger.error(f"Error during temporary file cleanup: {str(cleanup_error)}", exc_info=True)
                        # Continue with response even if cleanup fails
                    
                    logger.info(f"Report generation completed successfully for user {user_id}")
                    return jsonify({
                        'success': True,
                        'message': 'Reports generated successfully!',
                        'output_url': output_url
                    })
                    
                except Exception as process_error:
                    logger.error(f"Error processing file: {str(process_error)}", exc_info=True)
                    # Update upload record with error information
                    supabase_admin.table('uploads').update({
                        'status': 'error',
                        'error_message': str(process_error)
                    }).eq('id', upload_id).execute()
                    return jsonify({
                        'success': False,
                        'message': f'Error processing file: {str(process_error)}'
                    }), 500
                    
            except Exception as download_error:
                logger.error(f"Error downloading file: {str(download_error)}", exc_info=True)
                # Update upload record with error information
                supabase_admin.table('uploads').update({
                    'status': 'error',
                    'error_message': f'Error downloading file: {str(download_error)}'
                }).eq('id', upload_id).execute()
                return jsonify({
                    'success': False,
                    'message': f'Error downloading file: {str(download_error)}'
                }), 500
                
        except Exception as e:
            logger.error(f"Unexpected error in report generation: {str(e)}", exc_info=True)
            # Update upload record with error information if we have an upload_id
            if 'upload_id' in locals():
                supabase_admin.table('uploads').update({
                    'status': 'error',
                    'error_message': f'Unexpected error: {str(e)}'
                }).eq('id', upload_id).execute()
            return jsonify({
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            }), 500
            
        finally:
            # Ensure temporary files are cleaned up even if an error occurs
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.info(f"Cleaned up temporary file in finally block: {temp_file_path}")
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up temporary file in finally block: {str(cleanup_error)}", exc_info=True)
            
            if output_file_path and os.path.exists(output_file_path):
                try:
                    os.remove(output_file_path)
                    logger.info(f"Cleaned up output file in finally block: {output_file_path}")
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up output file in finally block: {str(cleanup_error)}", exc_info=True)

    return asyncio.run(_generate())

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    """Download a report file from storage"""
    async def _download():
        try:
            # Get the user ID from the session
            user_id = session.get('user')
            if not user_id:
                return jsonify({"error": "User not authenticated"}), 401

            # Get custom download path from query parameter if provided
            custom_path = request.args.get('path')
            if custom_path:
                # Validate the custom path is within allowed directories
                allowed_dirs = ['/tmp/reports', os.path.expanduser('~/Downloads')]
                custom_path = os.path.abspath(custom_path)
                if not any(custom_path.startswith(allowed_dir) for allowed_dir in allowed_dirs):
                    return jsonify({"error": "Invalid download path"}), 400

            # Download the file
            try:
                download_path = await storage_service.download_file(
                    filename=filename,
                    user_id=user_id,
                    download_path=custom_path
                )
            except StorageError as e:
                if "not found" in str(e):
                    return jsonify({"error": "File not found"}), 404
                elif "Invalid file type" in str(e):
                    return jsonify({"error": str(e)}), 400
                else:
                    raise

            # Get the correct MIME type based on file extension
            mime_types = {
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.pdf': 'application/pdf',
                '.txt': 'text/plain'
            }
            file_ext = os.path.splitext(filename)[1].lower()
            mime_type = mime_types.get(file_ext, 'application/octet-stream')

            # Send the file to the user with proper headers
            return send_file(
                download_path,
                as_attachment=True,
                download_name=filename,
                mimetype=mime_type
            )

        except StorageError as e:
            logger.error(f"Storage error during download: {str(e)}")
            return jsonify({"error": str(e)}), 500
        except Exception as e:
            logger.error(f"Error during file download: {str(e)}")
            return jsonify({"error": "Failed to download file"}), 500

    return asyncio.run(_download())

@app.route('/reports')
@login_required
def list_reports():
    """List all reports generated by the current user"""
    try:
        # Get the user ID from the session
        user_id = session.get('user')
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        # Query the uploads table for this user's uploads that have reports
        logger.debug(f"Querying uploads table for user_id: {user_id}")
        result = supabase.table('uploads').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        
        logger.debug(f"Found {len(result.data)} uploads for user")
        
        reports = []
        for upload in result.data:
            logger.debug(f"Upload record: {upload}")
            # Only check for output_file_url which exists in the table
            output_url = upload.get('output_file_url')
            logger.debug(f"Output URL for upload {upload['id']}: {output_url}")
            
            # If we have a completed report with an output URL
            if output_url:
                filename = output_url.split('/')[-1]
                logger.debug(f"Adding report with filename: {filename}")
                reports.append({
                    'id': upload['id'],
                    'filename': filename,
                    'created_at': upload['created_at'],
                    'download_url': f"/download/{filename}"
                })
            else:
                logger.debug(f"Skipping upload {upload['id']} - no output URL found")
        
        logger.debug(f"Returning {len(reports)} reports")
        return jsonify(reports)
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/reports/view')
@login_required
def view_reports():
    """View page for listing and downloading reports"""
    return render_template('reports.html')

@app.route('/reports/<report_id>', methods=['DELETE'])
@login_required
def delete_report(report_id):
    """Delete a specific report"""
    async def _delete():
        try:
            # Get the user ID from the session
            user_id = session.get('user')
            if not user_id:
                return jsonify({"error": "User not authenticated"}), 401

            # First, get the report details to verify ownership and get the file URL
            logger.debug(f"Attempting to delete report {report_id} for user {user_id}")
            result = supabase.table('uploads').select('*').eq('id', report_id).eq('user_id', user_id).execute()
            
            if not result.data:
                logger.warning(f"Report {report_id} not found for user {user_id}")
                return jsonify({"error": "Report not found"}), 404
            
            report = result.data[0]
            output_url = report.get('output_file_url')
            
            # Delete the file from storage if it exists
            if output_url:
                try:
                    filename = output_url.split('/')[-1]
                    logger.debug(f"Attempting to delete file from storage: {filename}")
                    # Use the storage service to delete the file
                    await storage_service.delete_file(filename, user_id=user_id)
                    logger.debug(f"Successfully deleted file from storage: {filename}")
                except Exception as storage_error:
                    logger.warning(f"Failed to delete file from storage: {str(storage_error)}")
                    # Continue with database deletion even if storage deletion fails
            
            # Delete the record from the database
            logger.debug(f"Deleting report record from database: {report_id}")
            delete_result = supabase.table('uploads').delete().eq('id', report_id).eq('user_id', user_id).execute()
            
            # Supabase delete operations return empty data array on success
            # Check if there was no error rather than checking for data
            logger.debug(f"Delete result: {delete_result}")
            logger.debug(f"Successfully deleted report {report_id}")
            return jsonify({"message": "Report deleted successfully"}), 200
                
        except Exception as e:
            logger.error(f"Error deleting report {report_id}: {str(e)}", exc_info=True)
            return jsonify({"error": "Internal server error"}), 500

    return asyncio.run(_delete())

@app.route('/static/download_handler.js')
def serve_download_handler():
    """Serve the download handler JavaScript file"""
    return send_file('templates/download_handler.js', mimetype='application/javascript')

async def download_from_storage(storage_path: str, user_id: str = None) -> str:
    """
    Download a file from Supabase Storage to a temporary location
    
    Args:
        storage_path: The path of the file in Supabase Storage
        user_id: Optional user ID for logging purposes
        
    Returns:
        str: Path to the downloaded temporary file
        
    Raises:
        Exception: If download fails or file is not found
    """
    try:
        # Create a temporary directory for downloads if it doesn't exist
        temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Download the file
        logger.debug(f"Downloading file from storage: {storage_path}")
        response = supabase.storage.from_('uploads').download(storage_path)
        if not response:
            raise Exception("Failed to download file from storage")
        
        # Save to temporary file
        temp_file_path = os.path.join(temp_dir, os.path.basename(storage_path))
        with open(temp_file_path, 'wb') as f:
            f.write(response)
        
        logger.debug(f"Downloaded file to: {temp_file_path}")
        
        # Verify file exists
        if not os.path.exists(temp_file_path):
            raise Exception(f"File not found at path: {temp_file_path}")
            
        return temp_file_path
        
    except Exception as e:
        logger.error(f"Error downloading file from storage: {str(e)}")
        raise

if __name__ == '__main__':
    app.run(debug=True, port=5000)
