from flask import Flask, request, render_template, redirect, session, url_for, flash, render_template, send_file, jsonify
from supabase_config import supabase
from functools import wraps
import os
import secrets
from werkzeug.utils import secure_filename
import logging
from utils.excel_parser import read_student_data_from_excel
import openpyxl.utils.exceptions
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
        try:
            logger.debug("POST request received")
            logger.debug(f"Files in request: {request.files}")
            
            # Check if the post request has the file part
            if 'files' not in request.files:
                logger.error("No file part in request")
                flash('No file part')
                return redirect(request.url)
            
            file = request.files['files']
            logger.debug(f"File received: {file.filename}")
            
            # If user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                logger.error("No selected file")
                flash('No selected file')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                logger.debug(f"Secured filename: {filename}")
                
                # Save the file
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                logger.debug(f"Attempting to save file to: {file_path}")
                
                try:
                    file.save(file_path)
                    logger.debug("File saved successfully")
                except Exception as save_error:
                    logger.error(f"Error saving file: {str(save_error)}")
                    flash(f'Error saving file: {str(save_error)}')
                    return redirect(request.url)
                
                # Store file information in Supabase
                try:
                    logger.debug("Attempting to store file info in Supabase")
                    result = supabase.table('uploads').insert({
                        'user_id': session['user'],
                        'filename': filename,
                        'file_path': file_path
                    }).execute()
                    logger.debug(f"Supabase insert result: {result}")
                except Exception as e:
                    logger.error(f"Error storing file info in Supabase: {str(e)}")
                    flash('File uploaded but failed to save to database')
                
                flash('File uploaded successfully')
                return redirect(url_for('upload_page'))
            else:
                logger.error(f"Invalid file type: {file.filename}")
                flash('Invalid file type. Please upload an .xlsx file')
                return redirect(request.url)
        except Exception as e:
            logger.error(f"Unexpected error during upload: {str(e)}")
            flash(f'Error uploading file: {str(e)}')
            return redirect(request.url)
            
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
            
            # TODO: Add your report generation logic here
            # For now, we'll just return the number of students parsed
            return jsonify({
                'success': True,
                'message': f'Successfully parsed {len(student_list)} students',
                'student_count': len(student_list)
            })
            
        except openpyxl.utils.exceptions.InvalidFileException:
            logger.error("Invalid Excel file format")
            return jsonify({
                'success': False,
                'message': 'Invalid Excel file format. Please ensure the file is a valid .xlsx file.'
            }), 400
            
        except openpyxl.utils.exceptions.EmptyFileException:
            logger.error("Empty Excel file")
            return jsonify({
                'success': False,
                'message': 'The Excel file is empty. Please upload a file with data.'
            }), 400
            
        except Exception as e:
            logger.error(f"Error parsing Excel file: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Failed to parse Excel file: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in generate_report: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred. Please try again.'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
