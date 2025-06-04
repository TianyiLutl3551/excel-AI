# Excel AI

A Python-based tool that uses OpenAI's GPT-4 to analyze and transform Excel data into structured formats.

## Features

- Reads Excel files using pandas
- Processes data using OpenAI's GPT-4
- Transforms and organizes data based on patterns and relationships
- Saves processed data back to Excel format

## Requirements

- Python 3.9+
- pandas
- openpyxl
- openai
- xlsxwriter

## Installation

1. Clone the repository:
```bash
git clone https://github.com/TianyiLutl3551/excel-AI.git
cd excel-AI
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your OpenAI API key:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

## Usage

1. Place your input Excel file in the `input` directory
2. Run the script:
```bash
python process_excel.py
```
3. Find the processed output in the `output` directory

## Project Structure

```
excel-AI/
├── input/              # Directory for input Excel files
├── output/             # Directory for processed output files
├── process_excel.py    # Main processing script
├── requirements.txt    # Python dependencies
└── README.md          # Project documentation
```

## Version History

### v1.0.0
- Initial release
- Basic Excel processing functionality
- GPT-4 integration for data transformation 