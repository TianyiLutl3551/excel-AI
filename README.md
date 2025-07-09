# Excel AI Processor

A robust tool for processing Excel financial reports using LLM technology, with support for batch, date-range, and incremental processing. Tracks processed files and outputs only the final combined result for each file.

## Features
- **Process all, date range, or only unprocessed files**
- **Date range support:** Process files from a start date to an end date (inclusive)
- **Single combined output:** Only the final combined CSV is saved per file
- **Processed file tracking:** All processed files are recorded in `process_record.txt` in the project root
- **Prompt caching ready:** Easily add caching to avoid repeated LLM calls for the same data
- **Parallel processing ready:** Easily extend to process multiple files in parallel (see below)

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `secrets.toml` file in the root directory with your OpenAI API key:
   ```toml
   [openai]
   api_key = "your-api-key-here"
   model = "gpt-4o"
   ```

## File Structure
- `input/`: Place your Excel files here, named like `SampleInputYYYYMMDD.xlsx`
- `output/`: Processed combined CSVs are saved here
- `process_record.txt`: Tracks all processed files and timestamps (in the project root)

## Usage

### 1. Process All Files
```bash
python llm_main.py --all
```

### 2. Process Files by Date Range
Process all files from `STARTDATE` to `ENDDATE` (inclusive):
```bash
python llm_main.py --date 20240801 20240802
```
To process a single date:
```bash
python llm_main.py --date 20240802 20240802
```

### 3. Process Only Unprocessed Files
```bash
python llm_main.py --unprocessed
```

### Additional Options
- Specify which Excel sheets to process:
  ```bash
  python llm_main.py --all --sheets "WB,DBIB,Sheet3"
  ```

## Output
- For each processed file, only a single combined CSV is saved in `output/`
- All processed files are tracked in `process_record.txt` with timestamps

## Prompt Caching (Recommended)
To save on API costs and speed up repeated runs, implement prompt caching in `llm_api.py`:
- Cache the LLM response using a hash of the actual data string (`data_str`) as the key
- See the assistant's suggestions above for code examples

## Parallel Processing (Optional)
To process multiple files at once, use Python's `concurrent.futures.ThreadPoolExecutor` in `llm_main.py`:
- This can greatly speed up processing, but be mindful of API rate limits
- See the assistant's suggestions above for code examples

## License
[Your License Here] 