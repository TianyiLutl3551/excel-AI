# 🚀 Setup Guide for AI Document Processing Workflow

## Quick Start for New Users

### 1. **Download and Setup**
```bash
git clone <your-repo-url>
cd excel-AI/redo
python setup.py  # This creates venv and installs dependencies
```

### 2. **Configure Your Environment**

#### **Essential Files to Edit:**

1. **`secrets.toml`** - Add your API keys:
```toml
[openai]
api_key = "your-openai-api-key-here"

[azure]
endpoint = "https://your-region.cognitiveservices.azure.com/"
key = "your-azure-document-intelligence-key-here"
```

2. **`config.json`** - Customize paths (optional):
```json
{
    "paths": {
        "input_dir": "../input",           # Where your files are
        "output_dir": "output",            # Where results go
        "tesseract_cmd": null              # Auto-detected, or set custom path
    }
}
```

### 3. **Platform-Specific Tesseract Setup**

The system auto-detects Tesseract, but you can override:

- **Windows**: `"tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"`
- **macOS**: `"tesseract_cmd": "/opt/homebrew/bin/tesseract"`
- **Linux**: `"tesseract_cmd": "/usr/bin/tesseract"`

### 4. **Directory Structure**
```
your-project/
├── redo/                    # Main workflow code
│   ├── config.json         # Your configuration
│   ├── secrets.toml        # Your API keys
│   └── venv/               # Virtual environment
├── input/                  # Put your .xlsx/.msg files here
└── output/                 # Results appear here
```

### 5. **Run the Workflow**
```bash
cd redo
source venv/bin/activate         # macOS/Linux
# or venv\Scripts\activate      # Windows
python main_workflow.py --mode range 20240501 20240501
```

## 🔒 Security Notes

- **Never commit `secrets.toml`** to version control
- **`config.json`** is safe to commit (no secrets)
- All paths are relative - works on any machine
- No hardcoded user-specific paths in code

## 🛠️ Customization Options

### Input/Output Directories
- Change `paths.input_dir` to point to your files
- Change `paths.output_dir` for custom results location
- All paths can be relative or absolute

### Tesseract Configuration
- Set `paths.tesseract_cmd` to null for auto-detection
- Or specify exact path for your installation

### Logging
- All log files go to output directory by default
- Customize in `logging` section of config.json

## ⚡ One-Command Setup
For the fastest setup:
```bash
git clone <repo> && cd excel-AI/redo && python setup.py
# Edit secrets.toml with your keys
# Run: python main_workflow.py --mode all
```

**You're ready to process documents!** 🎯 