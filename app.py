from flask import Flask, request, render_template, redirect, session, url_for, flash, render_template, send_file, jsonify
from supabase_config import supabase
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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

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
                        "full_name": full_name
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
        print("Upload endpoint hit")
        if 'files' not in request.files:
            print("No file part in request")
            return jsonify({'error': 'No file part'}), 400

        file = request.files['files']
        print(f"Received file: {file.filename}")
        if file.filename == '':
            print("No selected file")
            return jsonify({'error': 'No selected file'}), 400

        try:
            # Save the file to disk
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                print(f"Saved file to {file_path}")
                
                # Store file info in database
                user_id = session['user']
                result = supabase.table('uploads').insert({
                    'user_id': user_id,
                    'filename': filename,
                    'file_path': file_path,
                    'created_at': datetime.utcnow().isoformat()
                }).execute()
                print(f"Stored file info in database: {result.data}")
                
                # Count students
                import pandas as pd
                df = pd.read_excel(file_path)
                student_count = len(df)
                print(f"Student count: {student_count}")
                
                return jsonify({
                    'student_count': student_count,
                    'upload_id': result.data[0]['id'] if result.data else None
                }), 200
            else:
                return jsonify({'error': 'Invalid file type. Only .xlsx files are allowed.'}), 400

        except Exception as e:
            print("Exception occurred:", e)
            return jsonify({'error': str(e)}), 500
            
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
        try:
            user_id = session.get('user')
            
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
                logger.warning("No files found for user")
                return jsonify({
                    'success': False,
                    'message': 'No files found. Please upload an Excel file first.'
                }), 400
            
            latest_upload = result.data[0]
            excel_path = latest_upload['file_path']
            upload_id = latest_upload['id']
            
            logger.debug(f"Found latest upload: {excel_path} (ID: {upload_id})")
            
            # Verify file exists
            if not os.path.exists(excel_path):
                logger.error(f"File not found at path: {excel_path}")
                return jsonify({
                    'success': False,
                    'message': 'Uploaded file not found. Please try uploading again.'
                }), 404
            
            # Parse the Excel file
            try:
                logger.debug(f"Parsing Excel file: {excel_path}")
                student_list = read_student_data_from_excel(excel_path)
                logger.debug(f"Successfully parsed {len(student_list)} students from {excel_path}")
                
                # Update progress with total count
                progress_tracker[user_id] = {
                    'current': 0,
                    'total': len(student_list),
                    'status': 'Generating reports...',
                    'progress': 0
                }
                
                # Initialize services
                logger.debug("Initializing ReportGenerationService")
                report_service = ReportGenerationService()
                
                # Generate reports with progress tracking
                logger.debug(f"Generating reports for {len(student_list)} students")
                reports = await report_service.generate_reports_with_progress(student_list, user_id, progress_tracker)
                logger.debug(f"Successfully generated {len(reports)} reports")
                
                # Update progress for document creation
                progress_tracker[user_id]['status'] = 'Creating document...'
                
                # Create Word document
                logger.debug("Creating Word document")
                output_path = await report_service.create_word_doc(reports)
                logger.debug(f"Word document created at: {output_path}")
                
                # Update progress for upload
                progress_tracker[user_id]['status'] = 'Uploading...'
                
                # Upload to storage
                logger.debug(f"Uploading document to storage")
                output_url = await storage_service.upload_file(output_path, user_id=user_id)
                logger.debug(f"Document uploaded, URL: {output_url}")
                
                # Update usage tracking
                logger.debug(f"Updating usage records")
                await usage_service.update_upload_record(upload_id, len(student_list), output_url)
                await usage_service.increment_usage(user_id)
                logger.debug(f"Usage records updated")
                
                # Clean up temporary file
                try:
                    os.remove(output_path)
                    logger.debug(f"Temporary file removed: {output_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to remove temporary file: {str(cleanup_error)}")
                
                filename = output_url.split('/')[-1].split('?')[0]
                logger.debug(f"Report generation complete. Filename: {filename}")
                
                # Mark as complete
                progress_tracker[user_id] = {
                    'current': len(student_list),
                    'total': len(student_list),
                    'status': 'Complete',
                    'progress': 100
                }
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully generated reports for {len(student_list)} students',
                    'download_url': output_url,
                    'filename': filename
                })
                
            except openpyxl.utils.exceptions.InvalidFileException as e:
                logger.error(f"Invalid Excel file: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'Invalid Excel file format. Please ensure you are uploading a valid .xlsx file.'
                }), 400
                
            except ReportGenerationError as e:
                logger.error(f"Report generation error: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'Error generating reports: {str(e)}'
                }), 500
                
            except StorageError as e:
                logger.error(f"Storage error: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'Error uploading generated report: {str(e)}'
                }), 500
                
            except UsageTrackingError as e:
                logger.error(f"Usage tracking error: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'Error updating usage records: {str(e)}'
                }), 500
                
            except Exception as e:
                logger.error(f"Unexpected error in report generation: {str(e)}", exc_info=True)
                return jsonify({
                    'success': False,
                    'message': 'An unexpected error occurred during report generation. Please try again.'
                }), 500
                
        except Exception as e:
            logger.error(f"Unexpected error in generate_report: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'message': 'An unexpected error occurred. Please try again.'
            }), 500

    try:
        return asyncio.run(_generate())
    except Exception as e:
        logger.error(f"Error running async function: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Server error occurred. Please try again later.'
        }), 500

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
