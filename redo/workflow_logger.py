"""
Workflow Logger Module
Handles logging for processing and validation events
"""

import os
from datetime import datetime
from typing import Optional


class WorkflowLogger:
    def __init__(self, log_dir: str = "output"):
        """
        Initialize workflow logger.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = log_dir
        self.process_log_file = os.path.join(log_dir, "process_log.txt")
        self.validation_log_file = os.path.join(log_dir, "validation_log.txt")
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
    
    def log_process_start(self, file_path: str) -> None:
        """
        Log when file processing starts.
        
        Args:
            file_path: Path of file being processed
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_name = os.path.basename(file_path)
        
        try:
            with open(self.process_log_file, 'a') as f:
                f.write(f"[{timestamp}] {file_name}\n")
        except Exception as e:
            print(f"Warning: Failed to write to process log: {e}")
    
    def log_validation_result(self, file_path: str, success: bool, error: Optional[str] = None) -> None:
        """
        Log validation result.
        
        Args:
            file_path: Path of validated file
            success: Whether validation passed
            error: Error message if validation failed
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_name = os.path.basename(file_path)
        result = "correct" if success else "wrong"
        
        log_entry = f"[{timestamp}] {file_name} | {result}"
        if error:
            log_entry += f" | {error}"
        
        try:
            with open(self.validation_log_file, 'a') as f:
                f.write(f"{log_entry}\n")
        except Exception as e:
            print(f"Warning: Failed to write to validation log: {e}")
    
    def log_error(self, file_path: str, error_message: str, stage: str = "processing") -> None:
        """
        Log error during processing.
        
        Args:
            file_path: Path of file that caused error
            error_message: Error description
            stage: Processing stage where error occurred
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_name = os.path.basename(file_path)
        
        error_log_file = os.path.join(self.log_dir, "error_log.txt")
        
        try:
            with open(error_log_file, 'a') as f:
                f.write(f"[{timestamp}] {file_name} | {stage} | {error_message}\n")
        except Exception as e:
            print(f"Warning: Failed to write to error log: {e}")
    
    def log_summary(self, total_files: int, successful: int, failed: int) -> None:
        """
        Log processing summary.
        
        Args:
            total_files: Total number of files processed
            successful: Number of successful files
            failed: Number of failed files
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        summary_log_file = os.path.join(self.log_dir, "summary_log.txt")
        
        try:
            with open(summary_log_file, 'a') as f:
                f.write(f"[{timestamp}] Summary: {total_files} total, {successful} successful, {failed} failed\n")
        except Exception as e:
            print(f"Warning: Failed to write to summary log: {e}")
    
    def get_recent_logs(self, log_type: str = "process", lines: int = 10) -> list:
        """
        Get recent log entries.
        
        Args:
            log_type: Type of log ('process', 'validation', 'error', 'summary')
            lines: Number of recent lines to return
            
        Returns:
            List of recent log entries
        """
        log_files = {
            "process": self.process_log_file,
            "validation": self.validation_log_file,
            "error": os.path.join(self.log_dir, "error_log.txt"),
            "summary": os.path.join(self.log_dir, "summary_log.txt")
        }
        
        log_file = log_files.get(log_type)
        if not log_file or not os.path.exists(log_file):
            return []
        
        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                return [line.strip() for line in all_lines[-lines:]]
        except Exception as e:
            print(f"Warning: Failed to read {log_type} log: {e}")
            return []
    
    def clear_logs(self, log_type: Optional[str] = None) -> None:
        """
        Clear log files.
        
        Args:
            log_type: Specific log type to clear, or None to clear all logs
        """
        if log_type is None:
            # Clear all logs
            log_files = [
                self.process_log_file,
                self.validation_log_file,
                os.path.join(self.log_dir, "error_log.txt"),
                os.path.join(self.log_dir, "summary_log.txt")
            ]
        else:
            log_files = {
                "process": [self.process_log_file],
                "validation": [self.validation_log_file],
                "error": [os.path.join(self.log_dir, "error_log.txt")],
                "summary": [os.path.join(self.log_dir, "summary_log.txt")]
            }
            log_files = log_files.get(log_type, [])
        
        for log_file in log_files:
            try:
                if os.path.exists(log_file):
                    open(log_file, 'w').close()  # Clear file
                    print(f"Cleared log: {log_file}")
            except Exception as e:
                print(f"Warning: Failed to clear log {log_file}: {e}")


# Global instance for easy access
_workflow_logger = None

def get_workflow_logger(log_dir: str = None) -> WorkflowLogger:
    """Get global workflow logger instance."""
    global _workflow_logger
    if _workflow_logger is None or (log_dir and _workflow_logger.log_dir != log_dir):
        # Import here to avoid circular imports
        try:
            from config_manager import config_manager
            default_log_dir = config_manager.get_output_dir()
        except ImportError:
            default_log_dir = "output"
        
        _workflow_logger = WorkflowLogger(log_dir or default_log_dir)
    
    return _workflow_logger

# Backward compatibility functions
def log_process(file_path: str) -> None:
    """Backward compatibility function for process logging."""
    get_workflow_logger().log_process_start(file_path) 