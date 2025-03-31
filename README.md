# Facebook Signup Automation

A robust application for automating Facebook account creation using phone numbers from an Excel file.

## Project Overview

This application automates the Facebook signup process by processing phone numbers from an Excel file. It handles OTP detection, error messages, and provides real-time status updates through a web interface.

## Architecture

```
┌─────────────────┐     ┌───────────────────┐     ┌─────────────────┐
│                 │     │                   │     │                 │
│  Web Interface  │◄────┤  Flask Backend    │◄────┤  Automation     │
│  (HTML/JS/CSS)  │     │  (Python/Flask)   │     │  Engine         │
│                 │     │                   │     │  (Selenium)     │
└────────┬────────┘     └─────────┬─────────┘     └────────┬────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐     ┌───────────────────┐     ┌─────────────────┐
│                 │     │                   │     │                 │
│  Real-time      │     │  Data Processing  │     │  Screenshot     │
│  Updates        │     │  (Excel/Pandas)   │     │  Capture        │
│  (Socket.IO)    │     │                   │     │                 │
└─────────────────┘     └───────────────────┘     └─────────────────┘
```

### Key Components

1. **Web Interface (Frontend)**
   - User-friendly interface for file upload and process monitoring
   - Real-time status updates using Socket.IO
   - Progress tracking and error reporting

2. **Flask Backend (Server)**
   - RESTful API endpoints for file handling and process control
   - Task management and status tracking
   - Socket.IO integration for real-time updates

3. **Automation Engine (Core)**
   - Selenium-based browser automation
   - Intelligent OTP detection and error handling
   - Random data generation for signup fields
   - Captcha solving integration

4. **Data Processing**
   - Excel file parsing using Pandas
   - Status logging and result tracking
   - Output generation with detailed results

## Features

- **Intelligent OTP Detection**: Automatically detects when Facebook sends an OTP code
- **Error Handling**: Comprehensive error detection and reporting
- **Real-time Updates**: Live status updates during processing
- **Random Data Generation**: Creates unique profiles for each signup attempt
- **Screenshot Capture**: Saves screenshots at critical points for debugging
- **Detailed Logging**: Comprehensive logging for troubleshooting

## Technical Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, JavaScript, Bootstrap
- **Browser Automation**: Selenium WebDriver
- **Data Processing**: Pandas
- **Real-time Communication**: Socket.IO
- **Logging**: Python's logging module

## Setup and Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd facebook-auto-flow
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Create a `.env` file in the project root
   - Add the following variables:
     ```
     SECRET_KEY=your_secret_key
     CAPTCHA_API_KEY=your_captcha_api_key
     CAPTCHA_SERVICE_URL=https://2captcha.com/in.php
     ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the web interface**
   - Open a browser and navigate to `http://localhost:5000`

## Usage

1. **Prepare your data**
   - Create an Excel file with phone numbers in the first column
   - Ensure numbers are in international format (e.g., 67073408555)

2. **Upload the file**
   - Click "Choose File" on the web interface
   - Select your Excel file and click "Upload"

3. **Start the process**
   - Click "Start Process" to begin automation
   - Monitor the progress in real-time

4. **View results**
   - Check the "Phone Numbers Status" table for results
   - Each number will be marked as "OTP Sent", "Failed", or "Success"
   - Error details will be provided for failed attempts

## Troubleshooting

- **Check the logs**: Review `app.log` and `automation.log` for detailed information
- **Examine screenshots**: Look in the `screenshots` folder for visual debugging
- **Verify Excel format**: Ensure your input file follows the required format
- **Browser issues**: Try updating the WebDriver or browser version

## License

[Include license information here]

## Contributors

[List contributors here]
