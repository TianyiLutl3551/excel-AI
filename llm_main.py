from llm_data import LLMData
from llm_api import process_with_llm
from file_processor import FileProcessor
import os
import pandas as pd
import argparse
import sys

class LLMOrchestrator:
    def __init__(self, file_path, output_dir="output"):
        self.file_path = file_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.llm_data = LLMData(file_path)

    def process_sheets(self, sheet_names):
        all_llm_results = []
        for sheet in sheet_names:
            try:
                cleaned_df = self.llm_data.get_cleaned_sheet(sheet)
                if cleaned_df is not None:
                    llm_result = process_with_llm(cleaned_df)
                    if llm_result is not None:
                        all_llm_results.append(llm_result)
                        llm_result.to_csv(os.path.join(self.output_dir, f"{sheet}_llm_output.csv"), index=False)
            except Exception as e:
                print(f"Error processing sheet {sheet}: {e}")
        if all_llm_results:
            combined = pd.concat(all_llm_results, ignore_index=True)
            output_filename = f"combined_llm_output_{os.path.basename(self.file_path).replace('.xlsx', '')}.csv"
            combined.to_csv(os.path.join(self.output_dir, output_filename), index=False)
            print(f"Combined LLM output saved to {os.path.join(self.output_dir, output_filename)}")
        else:
            print("No LLM results to save.")
        return len(all_llm_results) > 0

def process_file(file_path, sheet_names=["WB", "DBIB"]):
    """Process a single file and return True if successful, False otherwise."""
    try:
        print(f"Processing file: {file_path}")
        orchestrator = LLMOrchestrator(file_path)
        success = orchestrator.process_sheets(sheet_names)
        if success:
            print(f"Successfully processed {file_path}")
        else:
            print(f"No results generated for {file_path}")
        return success
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Process Excel files with LLM")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Process all files in the input directory")
    group.add_argument("--date", type=str, help="Process a specific file by date code (e.g., 20240802)")
    group.add_argument("--unprocessed", action="store_true", help="Process only unprocessed files")
    parser.add_argument("--sheets", type=str, default="WB,DBIB", help="Comma-separated list of sheet names to process")
    
    args = parser.parse_args()
    sheet_names = args.sheets.split(",")
    
    file_processor = FileProcessor()
    files_to_process = []
    
    if args.all:
        files_to_process = file_processor.process_all_files()
        print(f"Found {len(files_to_process)} files to process")
    elif args.date:
        files_to_process = file_processor.process_specific_date(args.date)
        if not files_to_process:
            print(f"No file found for date code {args.date}")
            return
    elif args.unprocessed:
        files_to_process = file_processor.process_unprocessed_files()
        print(f"Found {len(files_to_process)} unprocessed files")
    
    if not files_to_process:
        print("No files to process.")
        return
    
    success_count = 0
    for file_path in files_to_process:
        if process_file(file_path, sheet_names):
            success_count += 1
    
    print(f"Processed {success_count} out of {len(files_to_process)} files successfully.")

if __name__ == "__main__":
    main() 