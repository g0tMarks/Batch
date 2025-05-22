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
                return redirect(url_for('upload_page'))
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
            # Get the latest uploaded file for the current user
            result = supabase.table('uploads').select('*').eq('user_id', session['user']).order('created_at', desc=True).limit(1).execute()
            
            if not result.data:
                return jsonify({
                    'success': False,
                    'message': 'No files found. Please upload an Excel file first.'
                }), 400
            
            latest_upload = result.data[0]
            excel_path = latest_upload['file_path']
            upload_id = latest_upload['id']
            
            # Verify file exists
            if not os.path.exists(excel_path):
                return jsonify({
                    'success': False,
                    'message': 'Uploaded file not found. Please try uploading again.'
                }), 404
            
            # Parse the Excel file
            try:
                student_list = read_student_data_from_excel(excel_path)
                logger.debug(f"Successfully parsed {len(student_list)} students from {excel_path}")
                
                # Initialize services
                report_service = ReportGenerationService()
                
                # Generate reports
                reports = await report_service.generate_reports(student_list)
                
                # Create Word document
                output_path = await report_service.create_word_doc(reports)
                
                # Upload to storage
                output_url = await storage_service.upload_file(output_path, user_id=session['user'])
                
                # Update usage tracking
                await usage_service.update_upload_record(upload_id, len(student_list), output_url)
                await usage_service.increment_usage(session['user'])
                
                # Clean up temporary file
                os.remove(output_path)
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully generated reports for {len(student_list)} students',
                    'download_url': output_url
                })
                
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
                logger.error(f"Unexpected error in generate_report: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'An unexpected error occurred. Please try again.'
                }), 500
                
        except Exception as e:
            logger.error(f"Unexpected error in generate_report: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'An unexpected error occurred. Please try again.'
            }), 500

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
                mimetype=mime_type,
                etag=False,
                cache_timeout=0,
                conditional=True
            )

        except StorageError as e:
            logger.error(f"Storage error during download: {str(e)}")
            return jsonify({"error": str(e)}), 500
        except Exception as e:
            logger.error(f"Error during file download: {str(e)}")
            return jsonify({"error": "Failed to download file"}), 500

    return asyncio.run(_download())

@app.route('/static/download_handler.js')
def serve_download_handler():
    """Serve the download handler JavaScript file"""
    return send_file('templates/download_handler.js', mimetype='application/javascript')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
