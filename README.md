# Automated Facebook Signup Flow

This project automates the Facebook account creation process using an Excel file as input.

## Features

- Random data generation for signup fields (names, DOB, password)
- Excel integration for phone number processing
- Browser automation using Selenium
- Captcha bypass using third-party services
- Web UI for file upload and process control
- Background task processing with Celery

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Install Redis (required for Celery):
   - Windows: Download and install from https://github.com/microsoftarchive/redis/releases
   - Linux: `sudo apt-get install redis-server`
   - macOS: `brew install redis`

3. Configure environment variables:
   - Create a `.env` file based on `.env.example`
   - Add your captcha service API key

4. Run the application:
   ```
   # Start Redis server (if not running as a service)
   redis-server

   # Start Celery worker
   celery -A app.celery worker --pool=solo --loglevel=info

   # Start Flask application
   python app.py
   ```

5. Access the web interface at http://localhost:5000

## Usage

1. Prepare an Excel file with phone numbers in the first column
2. Upload the file through the web interface
3. Click "Start Process" to begin the automation
4. Monitor progress in real-time
5. Download the updated Excel file with results when complete
