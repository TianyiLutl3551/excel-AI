"""
File Manager Module
Handles file operations, date extraction, and file filtering logic
"""

import os
import re
from typing import List, Optional


class FileManager:
    def __init__(self, input_dir: str, supported_extensions: List[str] = None):
        """
        Initialize file manager.
        
        Args:
            input_dir: Directory containing input files
            supported_extensions: List of supported file extensions
        """
        self.input_dir = input_dir
        self.supported_extensions = supported_extensions or ['.xlsx', '.xls', '.msg']
    
    def extract_date_code(self, filename: str) -> Optional[str]:
        """
        Extract date code in the form YYYYMMDD from a filename.
        
        Args:
            filename: Filename to extract date from
            
        Returns:
            Date code as string (YYYYMMDD) or None if not found
        """
        # Match patterns like: 20240801, 2024_08_01, 2024-08-01
        match = re.search(r'(20\d{2})[\-_]?([01]\d)[\-_]?([0-3]\d)', filename)
        if match:
            return f"{match.group(1)}{match.group(2)}{match.group(3)}"
        return None
    
    def get_all_files(self) -> List[str]:
        """
        Get all supported files from input directory.
        
        Returns:
            List of full file paths
        """
        files = []
        
        if not os.path.exists(self.input_dir):
            print(f"Warning: Input directory does not exist: {self.input_dir}")
            return files
        
        for fname in os.listdir(self.input_dir):
            # Skip hidden files
            if fname.startswith('.'):
                continue
            
            # Check file extension
            if any(fname.lower().endswith(ext) for ext in self.supported_extensions):
                files.append(os.path.join(self.input_dir, fname))
        
        return sorted(files)  # Sort for consistent ordering
    
    def get_files_by_date(self, date_code: str) -> List[str]:
        """
        Get files matching a specific date code.
        
        Args:
            date_code: Date code in YYYYMMDD format
            
        Returns:
            List of full file paths matching the date
        """
        all_files = self.get_all_files()
        matched_files = []
        
        for file_path in all_files:
            filename = os.path.basename(file_path)
            file_date = self.extract_date_code(filename)
            
            if file_date == date_code:
                matched_files.append(file_path)
        
        return matched_files
    
    def get_files_by_date_range(self, start_date: str, end_date: str) -> List[str]:
        """
        Get files within a date range (inclusive).
        
        Args:
            start_date: Start date in YYYYMMDD format
            end_date: End date in YYYYMMDD format (inclusive)
            
        Returns:
            List of full file paths within the date range
        """
        all_files = self.get_all_files()
        matched_files = []
        
        # Validate date format
        try:
            start_int = int(start_date)
            end_int = int(end_date)
        except ValueError:
            print(f"Error: Invalid date format. Use YYYYMMDD (e.g., 20240716)")
            return []
        
        # Ensure start_date <= end_date
        if start_int > end_int:
            start_date, end_date = end_date, start_date
            start_int, end_int = end_int, start_int
            print(f"Note: Swapped dates to {start_date} - {end_date}")
        
        for file_path in all_files:
            filename = os.path.basename(file_path)
            file_date = self.extract_date_code(filename)
            
            if file_date:
                try:
                    file_date_int = int(file_date)
                    if start_int <= file_date_int <= end_int:
                        matched_files.append(file_path)
                except ValueError:
                    # Skip files with invalid date codes
                    continue
        
        return sorted(matched_files)  # Sort for consistent ordering
    
    def get_unprocessed_files(self, processed_log_file: str) -> List[str]:
        """
        Get files that haven't been processed yet.
        
        Args:
            processed_log_file: Path to file containing processed file log
            
        Returns:
            List of unprocessed file paths
        """
        all_files = self.get_all_files()
        processed_filenames = self._load_processed_files(processed_log_file)
        
        unprocessed_files = []
        
        for file_path in all_files:
            filename = os.path.basename(file_path)
            
            if filename not in processed_filenames:
                unprocessed_files.append(file_path)
                print(f"[DEBUG] Adding to unprocessed: {filename}")
            else:
                print(f"[DEBUG] Skipping (already processed): {filename}")
        
        return unprocessed_files
    
    def _load_processed_files(self, processed_log_file: str) -> set:
        """
        Load set of processed filenames from log file.
        
        Args:
            processed_log_file: Path to processed files log
            
        Returns:
            Set of processed filenames
        """
        processed = set()
        
        if not os.path.exists(processed_log_file):
            print(f"[DEBUG] Processed log file does not exist: {processed_log_file}")
            return processed
        
        try:
            with open(processed_log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and line.startswith('['):
                        # Extract filename from timestamp line: [timestamp] filename
                        parts = line.split('] ', 1)
                        if len(parts) == 2:
                            processed.add(parts[1])
                            print(f"[DEBUG] Found processed file: {parts[1]}")
        except Exception as e:
            print(f"Warning: Error reading processed log file: {e}")
        
        print(f"[DEBUG] Total processed files: {len(processed)}")
        return processed
    
    def validate_file_path(self, file_path: str) -> bool:
        """
        Validate that a file path exists and has supported extension.
        
        Args:
            file_path: Path to validate
            
        Returns:
            True if file is valid, False otherwise
        """
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            return False
        
        filename = os.path.basename(file_path)
        if not any(filename.lower().endswith(ext) for ext in self.supported_extensions):
            print(f"Error: Unsupported file type: {filename}")
            return False
        
        return True
    
    def get_file_stats(self) -> dict:
        """
        Get statistics about files in input directory.
        
        Returns:
            Dictionary with file statistics
        """
        all_files = self.get_all_files()
        stats = {
            'total_files': len(all_files),
            'by_extension': {},
            'date_codes': set()
        }
        
        for file_path in all_files:
            filename = os.path.basename(file_path)
            
            # Count by extension
            for ext in self.supported_extensions:
                if filename.lower().endswith(ext):
                    stats['by_extension'][ext] = stats['by_extension'].get(ext, 0) + 1
                    break
            
            # Extract date codes
            date_code = self.extract_date_code(filename)
            if date_code:
                stats['date_codes'].add(date_code)
        
        stats['date_codes'] = sorted(list(stats['date_codes']))
        return stats


# Global instance for easy access
_file_manager = None

def get_file_manager(input_dir: str = None) -> FileManager:
    """Get global file manager instance."""
    global _file_manager
    if _file_manager is None or (input_dir and _file_manager.input_dir != input_dir):
        # Import here to avoid circular imports
        try:
            from config_manager import config_manager
            default_input_dir = config_manager.get_input_dir()
        except ImportError:
            default_input_dir = "../input"
        
        _file_manager = FileManager(input_dir or default_input_dir)
    
    return _file_manager 