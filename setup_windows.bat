@echo off
echo ========================================
echo AI Document Processing Workflow Setup
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python found. Checking version...
python --version

echo.
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Checking Tesseract installation...
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Tesseract not found in PATH
    echo Please install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
    echo Install to: C:\Program Files\Tesseract-OCR\
    echo Add to PATH: C:\Program Files\Tesseract-OCR\
    echo.
    echo After installing Tesseract, update the path in msg_processor.py:
    echo pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
) else (
    echo Tesseract found.
)

echo.
echo Creating configuration files...
if not exist "secrets.toml" (
    echo Creating secrets.toml template...
    echo [openai] > secrets.toml
    echo api_key = "your-openai-api-key" >> secrets.toml
    echo model = "gpt-4o" >> secrets.toml
    echo vision_model = "gpt-4o" >> secrets.toml
    echo. >> secrets.toml
    echo [azure] >> secrets.toml
    echo endpoint = "https://your-resource.cognitiveservices.azure.com/" >> secrets.toml
    echo key = "your-azure-key" >> secrets.toml
    echo model = "prebuilt-layout" >> secrets.toml
    echo.
    echo Please edit secrets.toml with your actual API keys
)

if not exist "input" mkdir input
if not exist "output" mkdir output

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit secrets.toml with your API keys
echo 2. Update config.json with your paths
echo 3. Place your files in the input/ directory
echo 4. Run: python main_workflow.py --mode all
echo.
pause 