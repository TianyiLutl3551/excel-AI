# AI Document Processing Workflow Setup Script for Windows
# Run this script in PowerShell as Administrator if needed

Write-Host "========================================" -ForegroundColor Green
Write-Host "AI Document Processing Workflow Setup" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Python found: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
try {
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create virtual environment"
    }
    Write-Host "Virtual environment created successfully" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
try {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install dependencies"
    }
    Write-Host "Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Write-Host "Try running: python -m pip install --upgrade pip" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Tesseract installation
Write-Host ""
Write-Host "Checking Tesseract installation..." -ForegroundColor Yellow
try {
    $tesseractVersion = tesseract --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Tesseract found: $($tesseractVersion[0])" -ForegroundColor Green
    } else {
        throw "Tesseract not found"
    }
} catch {
    Write-Host "WARNING: Tesseract not found in PATH" -ForegroundColor Yellow
    Write-Host "Please install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Yellow
    Write-Host "Install to: C:\Program Files\Tesseract-OCR\" -ForegroundColor Yellow
    Write-Host "Add to PATH: C:\Program Files\Tesseract-OCR\" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After installing Tesseract, update the path in msg_processor.py:" -ForegroundColor Yellow
    Write-Host "pytesseract.pytesseract.tesseract_cmd = r`"C:\Program Files\Tesseract-OCR\tesseract.exe`"" -ForegroundColor Yellow
}

# Create configuration files
Write-Host ""
Write-Host "Creating configuration files..." -ForegroundColor Yellow

# Create secrets.toml if it doesn't exist
if (-not (Test-Path "secrets.toml")) {
    Write-Host "Creating secrets.toml template..." -ForegroundColor Yellow
    @"
[openai]
api_key = "your-openai-api-key"
model = "gpt-4o"
vision_model = "gpt-4o"

[azure]
endpoint = "https://your-resource.cognitiveservices.azure.com/"
key = "your-azure-key"
model = "prebuilt-layout"
"@ | Out-File -FilePath "secrets.toml" -Encoding UTF8
    Write-Host "Created secrets.toml template" -ForegroundColor Green
    Write-Host "Please edit secrets.toml with your actual API keys" -ForegroundColor Yellow
} else {
    Write-Host "secrets.toml already exists" -ForegroundColor Green
}

# Create directories
if (-not (Test-Path "input")) {
    New-Item -ItemType Directory -Path "input" | Out-Null
    Write-Host "Created input directory" -ForegroundColor Green
}

if (-not (Test-Path "output")) {
    New-Item -ItemType Directory -Path "output" | Out-Null
    Write-Host "Created output directory" -ForegroundColor Green
}

# Update Tesseract path in msg_processor.py if needed
if (Test-Path "msg_processor.py") {
    Write-Host ""
    Write-Host "Checking Tesseract path in msg_processor.py..." -ForegroundColor Yellow
    $content = Get-Content "msg_processor.py" -Raw
    if ($content -match "pytesseract\.pytesseract\.tesseract_cmd = `/opt/homebrew/bin/tesseract`") {
        Write-Host "Updating Tesseract path for Windows..." -ForegroundColor Yellow
        $content = $content -replace "pytesseract\.pytesseract\.tesseract_cmd = `/opt/homebrew/bin/tesseract`", "pytesseract.pytesseract.tesseract_cmd = r`"C:\Program Files\Tesseract-OCR\tesseract.exe`""
        $content | Out-File -FilePath "msg_processor.py" -Encoding UTF8
        Write-Host "Updated Tesseract path" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit secrets.toml with your API keys" -ForegroundColor White
Write-Host "2. Update config.json with your paths" -ForegroundColor White
Write-Host "3. Place your files in the input/ directory" -ForegroundColor White
Write-Host "4. Run: python main_workflow.py --mode all" -ForegroundColor White
Write-Host ""
Write-Host "To activate the virtual environment in the future:" -ForegroundColor Yellow
Write-Host ".\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit" 