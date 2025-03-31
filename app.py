import os
import time
import threading
import traceback
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO
import pandas as pd
from dotenv import load_dotenv
import uuid
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-for-facebook-automation')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active tasks
active_tasks = {}

# Import automation module
from automation import FacebookSignupAutomation

def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Return success response with file path
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'filepath': filepath,
            'filename': filename
        })
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/start-process', methods=['POST'])
def start_process():
    """Start the automation process"""
    data = request.json
    filepath = data.get('filepath')
    
    if not filepath or not os.path.exists(filepath):
        return jsonify({'error': 'Invalid file path'}), 400
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Initialize task info before starting thread
    active_tasks[task_id] = {
        'status': 'PENDING',
        'filepath': filepath
    }
    
    # Start processing thread
    thread = threading.Thread(target=process_excel, args=(task_id, filepath))
    thread.daemon = True
    thread.start()
    
    # Store thread reference
    active_tasks[task_id]['thread'] = thread
    
    logger.info(f"Started task {task_id} for file {filepath}")
    
    return jsonify({
        'success': True,
        'message': 'Process started',
        'task_id': task_id
    })

@app.route('/task-status/<task_id>')
def task_status(task_id):
    """Get the status of a task"""
    if task_id not in active_tasks:
        return jsonify({
            'state': 'NOT_FOUND',
            'status': 'Task not found'
        })
    
    task = active_tasks[task_id]
    
    if task['status'] == 'PENDING':
        response = {
            'state': 'PENDING',
            'status': 'Pending...'
        }
    elif task['status'] == 'PROGRESS':
        response = {
            'state': 'PROGRESS',
            'status': task.get('progress', {})
        }
    elif task['status'] == 'SUCCESS':
        response = {
            'state': 'SUCCESS',
            'result': task.get('result', {})
        }
    else:
        # task failed
        response = {
            'state': task['status'],
            'status': task.get('error', 'Unknown error')
        }
    
    return jsonify(response)

@app.route('/download/<filename>')
def download_file(filename):
    """Download the processed Excel file"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(filepath, as_attachment=True)

def process_excel(task_id, filepath):
    """Process the Excel file with phone numbers"""
    logger.info(f"Starting process_excel for task {task_id}")
    try:
        # Update task status
        active_tasks[task_id]['status'] = 'PROGRESS'
        
        # Load Excel file
        df = pd.read_excel(filepath)
        
        # Check if the file has the required column
        if df.empty or len(df.columns) < 1:
            logger.error(f"Invalid Excel format for task {task_id}")
            active_tasks[task_id]['status'] = 'FAILED'
            active_tasks[task_id]['error'] = 'Invalid Excel format. File must have at least one column with phone numbers.'
            return
        
        # Get total number of rows
        total_rows = len(df)
        logger.info(f"Processing {total_rows} phone numbers for task {task_id}")
        
        # Initialize automation
        automation = FacebookSignupAutomation()
        
        # Process each phone number
        for index, row in df.iterrows():
            # Update task progress
            progress_info = {
                'current': index + 1,
                'total': total_rows,
                'status': f'Processing phone number {index + 1} of {total_rows}'
            }
            active_tasks[task_id]['progress'] = progress_info
            
            # Get phone number from first column
            phone_number = str(row[0])
            logger.info(f"Processing phone number {phone_number} ({index + 1}/{total_rows})")
            
            # Emit progress via SocketIO
            socketio.emit('progress_update', {
                'current': index + 1,
                'total': total_rows,
                'phone': phone_number,
                'status': 'Processing'
            })
            
            # Process the phone number
            result = automation.process_phone_number(phone_number)
            
            # Log the result for debugging
            logger.info(f"Result for phone {phone_number}: {result}")
            
            # Update Excel file with result
            if 'Status' not in df.columns:
                df['Status'] = ''
            if 'Error' not in df.columns and 'error' in result:
                df['Error'] = ''
                
            df.at[index, 'Status'] = result.get('status', 'Unknown')
            if 'error' in result:
                df.at[index, 'Error'] = result.get('error', '')
            
            # Save updated Excel file
            df.to_excel(filepath, index=False)
            
            # Emit result via SocketIO with more detailed information
            status_message = result.get('status', 'Unknown')
            error_message = result.get('error', '')
            message = result.get('message', '')
            
            # Create a more descriptive status message for the UI
            ui_status = status_message
            if status_message == 'OTP Sent':
                ui_status = 'OTP Sent '
            elif status_message == 'Failed':
                ui_status = f'Failed ({error_message})'
            elif status_message == 'Success':
                ui_status = 'Success '
            
            socketio.emit('phone_processed', {
                'phone': phone_number,
                'status': ui_status,
                'raw_status': status_message,
                'error': error_message,
                'message': message,
                'url': result.get('url', '')
            })
            
            # Also update the progress info with the latest status
            progress_info = {
                'current': index + 1,
                'total': total_rows,
                'status': f'Phone {phone_number}: {ui_status}',
                'last_processed': {
                    'phone': phone_number,
                    'status': ui_status
                }
            }
            active_tasks[task_id]['progress'] = progress_info
            
            # Add a small delay to avoid rate limiting
            time.sleep(1)
        
        # Close automation
        automation.close()
        
        # Update task status
        active_tasks[task_id]['status'] = 'SUCCESS'
        active_tasks[task_id]['result'] = {
            'status': 'success',
            'message': f'Processed {total_rows} phone numbers',
            'filepath': filepath,
            'filename': os.path.basename(filepath)
        }
        logger.info(f"Successfully completed task {task_id}")
    
    except Exception as e:
        # Log the full exception with traceback
        logger.error(f"Error in process_excel for task {task_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Update task status
        active_tasks[task_id]['status'] = 'FAILED'
        active_tasks[task_id]['error'] = str(e)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
