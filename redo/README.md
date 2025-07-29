# AI Document Processing Workflow

Automated processing of Excel and MSG files using OpenAI GPT-4 and Azure Document Intelligence.

## 🚀 Quick Start (Company Laptop)

### One-Command Setup:
```bash
python setup.py
```

That's it! The setup script will automatically:
- ✅ Create all necessary directories
- ✅ Set up Python virtual environment  
- ✅ Install all dependencies
- ✅ Create configuration files
- ✅ Check Tesseract installation

### After Setup:
1. **Add API keys** to `config/secrets.toml`
2. **Add input files** to `data/input/`
3. **Run workflow**: `python main.py --mode all`

## 🔑 Required API Keys

Edit `config/secrets.toml` with:

```toml
[openai]
api_key = "your-openai-api-key-here"

[azure]
endpoint = "https://your-resource.cognitiveservices.azure.com/"
key = "your-azure-key-here"
```

**Where to get API keys:**
- **OpenAI**: https://platform.openai.com/api-keys
- **Azure**: Azure Portal → Document Intelligence resource

## 💻 Usage Commands

```bash
# Process all files in data/input/
python main.py --mode all

# Process files from specific date
python main.py --mode range 20240501 20240501

# Process date range
python main.py --mode range 20240501 20240510

# Process unprocessed files only
python main.py --mode unprocessed

# Combine results
python concat_tables.py      # Combine all table data
python concat_highlights.py  # Combine all highlights
```

## 📁 Directory Structure

```
redo/
├── main.py                 # Main entry point
├── setup.py               # One-click setup script
├── requirements.txt       # Python dependencies
├── config/
│   ├── config.json        # Main configuration
│   └── secrets.toml       # API keys (you edit this)
├── data/
│   ├── input/            # Put your .msg/.xlsx files here
│   └── output/           # Processed .csv files appear here
├── log/                  # Processing logs
└── src/                  # Source code
```

## 📊 Supported File Types

- **MSG files**: Outlook email files with embedded tables
- **Excel files**: .xlsx and .xls spreadsheets
- **Images**: .png files (OCR processing)

## 🔧 Dependencies

The setup script automatically installs:
- OpenAI API client
- Azure Document Intelligence
- Pandas for data processing
- Tesseract OCR
- BeautifulSoup for HTML parsing
- And more...

## 🛠️ Manual Setup (if needed)

If the automatic setup doesn't work:

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data/input data/output log

# Copy config templates
cp config/config.json.template config/config.json
cp config/secrets.toml.template config/secrets.toml
```

## 📋 Processing Workflow

1. **File Detection**: Automatically detects file types
2. **OCR Processing**: Extracts text from images using Tesseract + Azure
3. **Table Extraction**: Identifies and extracts P&L tables
4. **LLM Processing**: Structures data using GPT-4
5. **Validation**: Cryptographic validation of results
6. **Output**: Saves structured CSV files and highlights

## 🎯 Output Files

- **Table files**: `table_[filename].csv` - Structured P&L data
- **Highlights**: `highlights_[date]_[product].csv` - Key insights
- **Combined files**: `combined_all_tables.csv`, `combined_all_highlights.csv`
- **Logs**: Processing, validation, error, and summary logs

## 🔍 Troubleshooting

**Virtual environment issues:**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Tesseract not found:**
- Windows: Download from GitHub Tesseract releases
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`

**API errors:**
- Check your API keys in `config/secrets.toml`
- Verify Azure endpoint URL format
- Ensure sufficient API credits

## 📞 Support

If you encounter issues:
1. Check the logs in the `log/` directory
2. Verify API keys are correctly configured
3. Ensure all dependencies are installed
4. Check Tesseract installation

---

**Ready to process your documents! 🚀** 