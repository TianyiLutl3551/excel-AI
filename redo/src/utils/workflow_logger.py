import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

"""
Centralized logging system for the AI Document Processing Workflow.
Handles process logs, validation logs, error logs, and summary reports.
"""

class WorkflowLogger:
    def __init__(self, log_dir: str = "log"):
        """
        Initialize workflow logger with automatic log directory and file creation.
        
        Args:
            log_dir: Directory to store log files (default: "log")
        """
        self.log_dir = log_dir
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Define log file paths
        self.process_log_file = os.path.join(log_dir, "process_log.txt")
        self.validation_log_file = os.path.join(log_dir, "validation_log.txt")
        self.error_log_file = os.path.join(log_dir, "error_log.txt")
        self.summary_log_file = os.path.join(log_dir, "summary_log.txt")
        
        # Create log files if they don't exist
        self._ensure_log_files_exist()
    
    def _ensure_log_files_exist(self):
        """Create log files if they don't exist."""
        log_files = [
            self.process_log_file,
            self.validation_log_file,
            self.error_log_file,
            self.summary_log_file
        ]
        
        for log_file in log_files:
            if not os.path.exists(log_file):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                filename = os.path.basename(log_file)
                with open(log_file, "w") as f:
                    f.write(f"# {filename} - Created {timestamp}\n")
    
    def log_process_start(self, file_path: str) -> None:
        """
        Log when file processing starts.
        
        Args:
            file_path: Path to the file being processed
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = os.path.basename(file_path)
        
        log_message = f"[{timestamp}] Processing started: {filename}\n"
        
        try:
            with open(self.process_log_file, "a", encoding="utf-8") as f:
                f.write(log_message)
        except Exception as e:
            print(f"Warning: Failed to write to process log: {e}")
    
    def log_validation_result(self, file_path: str, success: bool, error: Optional[str] = None) -> None:
        """
        Log validation results.
        
        Args:
            file_path: Path to the file that was validated
            success: Whether validation passed
            error: Error message if validation failed
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = os.path.basename(file_path)
        status = "PASSED" if success else "FAILED"
        
        log_message = f"[{timestamp}] {filename} | {status}"
        if error:
            log_message += f" | Error: {error}"
        log_message += "\n"
        
        try:
            with open(self.validation_log_file, "a", encoding="utf-8") as f:
                f.write(log_message)
        except Exception as e:
            print(f"Warning: Failed to write to validation log: {e}")
    
    def log_error(self, error_message: str, context: Optional[str] = None) -> None:
        """
        Log error messages.
        
        Args:
            error_message: The error message to log
            context: Additional context about where the error occurred
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_message = f"[{timestamp}] ERROR: {error_message}"
        if context:
            log_message += f" | Context: {context}"
        log_message += "\n"
        
        try:
            with open(self.error_log_file, "a", encoding="utf-8") as f:
                f.write(log_message)
        except Exception as e:
            print(f"Warning: Failed to write to error log: {e}")
    
    def log_summary(self, summary_data: Dict[str, Any]) -> None:
        """
        Log summary information about processing session.
        
        Args:
            summary_data: Dictionary containing summary information
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_message = f"\n[{timestamp}] PROCESSING SUMMARY\n"
        log_message += "=" * 50 + "\n"
        
        for key, value in summary_data.items():
            log_message += f"{key}: {value}\n"
        
        log_message += "=" * 50 + "\n\n"
        
        try:
            with open(self.summary_log_file, "a", encoding="utf-8") as f:
                f.write(log_message)
        except Exception as e:
            print(f"Warning: Failed to write to summary log: {e}")
    
    def clear_logs(self, log_type: Optional[str] = None) -> None:
        """
        Clear log files.
        
        Args:
            log_type: Specific log type to clear ("process", "validation", "error", "summary")
                     If None, clears all logs
        """
        log_files = {
            "process": self.process_log_file,
            "validation": self.validation_log_file,
            "error": self.error_log_file,
            "summary": self.summary_log_file
        }
        
        if log_type:
            if log_type in log_files:
                files_to_clear = [log_files[log_type]]
            else:
                print(f"Warning: Unknown log type '{log_type}'")
                return
        else:
            files_to_clear = list(log_files.values())
        
        for log_file in files_to_clear:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                filename = os.path.basename(log_file)
                with open(log_file, "w") as f:
                    f.write(f"# {filename} - Cleared {timestamp}\n")
            except Exception as e:
                print(f"Warning: Failed to clear log {log_file}: {e}")
    
    def get_log_summary(self) -> Dict[str, str]:
        """Get paths to all log files."""
        return {
            "process": self.process_log_file,
            "validation": self.validation_log_file,
            "error": self.error_log_file,
            "summary": self.summary_log_file
        }

# Global logger instance
_workflow_logger: Optional[WorkflowLogger] = None

def get_workflow_logger(log_dir: str = None) -> WorkflowLogger:
    """
    Get or create the global workflow logger instance.
    
    Args:
        log_dir: Directory for log files (only used on first call)
    
    Returns:
        WorkflowLogger instance
    """
    global _workflow_logger
    if _workflow_logger is None:
        _workflow_logger = WorkflowLogger(log_dir or "log")
    return _workflow_logger

# Backward compatibility function
def log_process(file_path: str) -> None:
    """Backward compatibility wrapper for log_process_start."""
    get_workflow_logger().log_process_start(file_path)
