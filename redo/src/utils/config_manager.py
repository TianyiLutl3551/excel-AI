import os
import json
import toml
import platform
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file="config/config.json", secrets_file="config/secrets.toml"):
        # Use current working directory as project root (should be redo/)
        self.project_root = Path.cwd()
        self.config_path = self.project_root / config_file
        self.secrets_path = self.project_root / secrets_file
        self.config = self._load_config()
        self.secrets = self._load_secrets()
    
    def _load_config(self):
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file not found: {self.config_path}")
            return {}
    
    def _load_secrets(self):
        try:
            with open(self.secrets_path, "r") as f:
                return toml.load(f)
        except FileNotFoundError:
            print(f"Secrets file not found: {self.secrets_path}")
            return {}
    
    def get_input_dir(self):
        return self.config.get("paths", {}).get("input_dir", "input")
    
    def get_output_dir(self):
        return self.config.get("paths", {}).get("output_dir", "data/output")
    
    def get_azure_config(self):
        return self.secrets.get("azure", {})
    
    def get_openai_config(self):
        return self.secrets.get("openai", {})
    
    def get_supported_extensions(self):
        """Get supported file extensions from config."""
        return self.config.get("processing", {}).get("supported_extensions", [".xlsx", ".xls", ".msg"])
    
    def get_tesseract_path(self):
        """Get tesseract path from config."""
        return self.config.get("paths", {}).get("tesseract_cmd")
    
    def get_tesseract_cmd(self):
        """Get tesseract command path from config."""
        tesseract_path = self.config.get("paths", {}).get("tesseract_cmd")
        if tesseract_path:
            return tesseract_path
        
        # Auto-detect based on platform if not configured
        if self.config.get("system", {}).get("auto_detect_tesseract", True):
            platform_paths = self.config.get("system", {}).get("platform_specific_paths", {})
            system = platform.system().lower()
            if system == "darwin":
                return platform_paths.get("darwin_tesseract", "/opt/homebrew/bin/tesseract")
            elif system == "windows":
                return platform_paths.get("windows_tesseract", "C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
            elif system == "linux":
                return platform_paths.get("linux_tesseract", "/usr/bin/tesseract")
        
        return "tesseract"  # Default fallback
    
    def get_log_files(self):
        """Get log file paths from config."""
        logging_config = self.config.get("logging", {})
        return {
            "process_log": logging_config.get("process_log_file", "logs/process_log.txt"),
            "validation_log": logging_config.get("validation_log_file", "logs/validation_log.txt"),
            "error_log": logging_config.get("error_log_file", "logs/error_log.txt"),
            "summary_log": logging_config.get("summary_log_file", "logs/summary_log.txt")
        }

# Create global instance
config_manager = ConfigManager()
