# AI Document Processing Workflow

An intelligent document processing system built with LangGraph that automatically processes Excel and MSG files, extracts financial data, and validates the results using AI-powered analysis.

## Features

- **Multi-format Support**: Processes Excel (.xlsx, .xls) and MSG files
- **AI-Powered Analysis**: Uses OpenAI GPT models for data extraction and validation
- **Azure Integration**: Leverages Azure Document Intelligence for OCR
- **Automated Validation**: Compares extracted data using SHA-256 hashing
- **Flexible Processing Modes**: All files, single file, or unprocessed files only

## Prerequisites

### Windows Requirements

1. **Python 3.9+**: Download from [python.org](https://www.python.org/downloads/)
2. **Tesseract OCR**: 
   - Download from [UB-Mannheim GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - Install to `C:\Program Files\Tesseract-OCR\`
   - Add to PATH: `C:\Program Files\Tesseract-OCR\`
3. **Git**: Download from [git-scm.com](https://git-scm.com/download/win)

### API Keys Required

1. **OpenAI API Key**: Get from [platform.openai.com](https://platform.openai.com/api-keys)
2. **Azure Document Intelligence**: 
   - Endpoint: `https://your-resource.cognitiveservices.azure.com/`
   - Key: Get from Azure Portal

## Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd excel-ai-workflow
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

   ```bash
   pip install -r requirements.txt
   ```

### 4. Configure Environment

Create `secrets.toml` file in the project root:

   ```toml
   [openai]
api_key = "your-openai-api-key"
   model = "gpt-4o"
vision_model = "gpt-4o"

[azure]
endpoint = "https://your-resource.cognitiveservices.azure.com/"
key = "your-azure-key"
model = "prebuilt-layout"
```

### 5. Update Configuration

Edit `config.json`:

```json
{
    "input_dir": "C:\\path\\to\\your\\input\\folder",
    "output_dir": "C:\\path\\to\\your\\output\\folder",
    "process_log_file": "C:\\path\\to\\your\\output\\process_log.txt"
}
```

### 6. Update Tesseract Path

In `msg_processor.py`, update the Tesseract path:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## Usage

### Processing Modes

1. **All Files**: Process all files in input directory
```bash
   python main_workflow.py --mode all
```

2. **Single File**: Process files by date code (YYYYMMDD)
```bash
   python main_workflow.py --mode single --date 20240501
```

3. **Unprocessed Files**: Process only files not previously processed
```bash
   python main_workflow.py --mode unprocessed
```

### Example Commands

```bash
# Process all files
python main_workflow.py --mode all

# Process specific date
python main_workflow.py --mode single --date 20240501

# Process unprocessed files
python main_workflow.py --mode unprocessed

# Custom input directory
python main_workflow.py --mode all --input_dir "C:\MyFiles\Input"
  ```

## Project Structure

```
excel-ai-workflow/
├── main_workflow.py          # Main workflow orchestrator
├── file_type_classifier.py   # File type detection
├── excel_workflow.py         # Excel processing logic
├── msg_workflow.py           # MSG processing logic
├── validation_node.py        # Data validation
├── msg_processor.py          # MSG file and image processing
├── excel_processor.py        # Excel data extraction
├── config.json              # Configuration file
├── secrets.toml             # API keys (create this)
├── requirements.txt         # Python dependencies
├── input/                   # Input files directory
└── output/                  # Output files directory
```

## Workflow Process

1. **File Classification**: Detects file type (Excel or MSG)
2. **Excel Processing**: 
   - Extracts data from WB and DBIB sheets
   - Uses LLM to transform data into structured format
3. **MSG Processing**:
   - Extracts images from MSG attachments
   - Uses vision model to classify table type (blue/red)
   - Uses Azure Document Intelligence for OCR
   - Uses LLM to extract structured data
4. **Validation**: Compares extracted data using SHA-256 hashing

## Output Files

- **Highlights**: Extracted highlights from MSG files
- **Tables**: Structured data in Excel format
- **Validation Log**: Processing results and validation status
- **Process Log**: Tracking of processed files

## Troubleshooting

### Common Issues

1. **Tesseract not found**:
   - Ensure Tesseract is installed and in PATH
   - Update path in `msg_processor.py`

2. **Azure connection errors**:
   - Verify endpoint and key in `secrets.toml`
   - Check Azure service status

3. **OpenAI API errors**:
   - Verify API key in `secrets.toml`
   - Check API quota and billing

4. **Permission errors**:
   - Run as administrator if needed
   - Check file/folder permissions

### Debug Mode

For detailed debugging, check the console output for `[DEBUG]` messages.

## Dependencies

Key dependencies include:
- **LangGraph**: Workflow orchestration
- **OpenAI**: AI model integration
- **Azure Document Intelligence**: OCR processing
- **Pandas**: Data manipulation
- **Pillow**: Image processing
- **Tesseract**: OCR engine
- **extract-msg**: MSG file processing

## License

[Your License Here] 

## Support

For issues and questions, please create an issue in the repository. 