import os
import glob
import datetime
import pytz
import re
from typing import List, Optional, Set

class FileProcessor:
    """
    Class to handle different ways of processing Excel input files:
    1. Process all files in the input directory
    2. Process a specific file by date code (e.g., 20240802)
    3. Process only unprocessed files based on a tracking file
    """
    
    def __init__(self, input_dir="input", output_dir="output", 
                 processed_file="/Users/lutianyi/Desktop/excel AI/process_record.txt", file_prefix="SampleInput"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processed_file = processed_file
        self.file_prefix = file_prefix
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
    def _get_all_input_files(self) -> List[str]:
        """Get all Excel files in the input directory with the specified prefix."""
        pattern = os.path.join(self.input_dir, f"{self.file_prefix}*.xlsx")
        files = glob.glob(pattern)
        # Filter out temporary Excel files (those starting with ~)
        return [f for f in files if not os.path.basename(f).startswith('.~')]
    
    def _extract_date_code(self, filename: str) -> Optional[str]:
        """Extract the date code from a filename (e.g., SampleInput20240802.xlsx -> 20240802)."""
        match = re.search(rf"{self.file_prefix}(\d+)\.xlsx", os.path.basename(filename))
        if match:
            return match.group(1)
        return None
    
    def _get_processed_files(self) -> Set[str]:
        """Read the processed files tracking file and return a set of processed date codes."""
        if not os.path.exists(self.processed_file):
            return set()
            
        processed = set()
        with open(self.processed_file, 'r') as f:
            for line in f:
                # Skip timestamp lines and empty lines
                if line.strip() and not line.startswith('['):
                    processed.add(line.strip())
        return processed
    
    def _mark_as_processed(self, date_codes: List[str]):
        """Mark files as processed by adding them to the tracking file with timestamp."""
        # Get current timestamp with timezone
        now = datetime.datetime.now(pytz.timezone('UTC'))
        timestamp = now.strftime('[%Y-%m-%d %H:%M:%S %Z]')
        
        # Append to the tracking file
        with open(self.processed_file, 'a') as f:
            f.write(f"\n{timestamp}\n")
            for code in date_codes:
                f.write(f"{code}\n")
    
    def get_file_by_date(self, date_code: str) -> Optional[str]:
        """Get the file path for a specific date code."""
        filename = f"{self.file_prefix}{date_code}.xlsx"
        filepath = os.path.join(self.input_dir, filename)
        
        if os.path.exists(filepath):
            return filepath
        return None
    
    def process_all_files(self) -> List[str]:
        """Process all files in the input directory."""
        return self._get_all_input_files()
    
    def process_specific_date(self, date_code: str) -> List[str]:
        """Process a specific file by date code."""
        filepath = self.get_file_by_date(date_code)
        if filepath:
            return [filepath]
        return []
    
    def process_unprocessed_files(self) -> List[str]:
        """Process only files that haven't been processed yet."""
        all_files = self._get_all_input_files()
        processed_codes = self._get_processed_files()
        
        unprocessed_files = []
        unprocessed_codes = []
        
        for file in all_files:
            date_code = self._extract_date_code(file)
            if date_code and date_code not in processed_codes:
                unprocessed_files.append(file)
                unprocessed_codes.append(date_code)
        
        # Mark these files as processed if there are any
        if unprocessed_codes:
            self._mark_as_processed(unprocessed_codes)
            
        return unprocessed_files 