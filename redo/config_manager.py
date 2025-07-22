"""
Cross-platform configuration manager for the AI Document Processing Workflow.
Handles paths, secrets, and platform-specific configurations automatically.
Maintains backwards compatibility with existing hardcoded values.
"""
import os
import json
import toml
import platform
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file="config.json", secrets_file="secrets.toml"):
        """Initialize configuration manager with automatic path resolution."""
        self.project_root = self._get_project_root()
        self.config_file = self._resolve_path(config_file)
        self.secrets_file = self._resolve_path(secrets_file)
        
        # Load configurations with fallbacks
        self.config = self._load_config()
        self.secrets = self._load_secrets()
        
    def _get_project_root(self):
        """Find project root directory by looking for key files."""
        current = Path(__file__).parent
        
        # Look for project indicators
        indicators = ["main_workflow.py", "requirements.txt", ".git"]
        
        while current != current.parent:
            if any((current / indicator).exists() for indicator in indicators):
                return current
            current = current.parent
        
        # Fallback to current file's directory
        return Path(__file__).parent
    
    def _resolve_path(self, filename):
        """Resolve file path relative to project root."""
        return self.project_root / filename
    
    def _load_config(self):
        """Load configuration with fallbacks."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {self.config_file}: {e}")
        
        # Default configuration
        return {
            "file_processing": {
                "supported_extensions": [".xlsx", ".xls", ".msg"],
                "default_sheets": ["WB", "DBIB"],
                "decimal_precision": 6
            },
            "paths": {
                "input_dir": "../input",
                "output_dir": "output",
                "process_log_file": "output/process_log.txt",
                "validation_log_file": "output/validation_log.txt"
            },
            "output_patterns": {
                "combined_excel": "combined_llm_output_{basename}.csv",
                "highlights": "highlights_{date}.csv",
                "table": "table_{basename}.csv"
            },
            "platform": {
                "tesseract_cmd": ""  # Auto-detect
            }
        }
    
    def _load_secrets(self):
        """Load secrets with fallbacks."""
        try:
            if self.secrets_file.exists():
                with open(self.secrets_file, 'r') as f:
                    return toml.load(f)
        except Exception as e:
            print(f"Warning: Could not load {self.secrets_file}: {e}")
        
        # Default/fallback secrets (should be overridden in production)
        return {
            "openai": {
                "api_key": "your-openai-api-key",
                "model": "gpt-4o",
                "vision_model": "gpt-4o"
            },
            "azure": {
                "endpoint": "https://your-resource.cognitiveservices.azure.com/",
                "key": "your-azure-key",
                "model": "prebuilt-layout"
            }
        }
    
    def get_azure_config(self):
        """Get Azure Document Intelligence configuration."""
        return self.secrets.get("azure", {})
    
    def get_openai_config(self):
        """Get OpenAI configuration."""
        return self.secrets.get("openai", {})
    
    def get_tesseract_cmd(self):
        """Get platform-appropriate Tesseract command."""
        # Check if explicitly configured
        cmd = self.config.get("platform", {}).get("tesseract_cmd", "")
        if cmd:
            return cmd
        
        # Auto-detect based on platform
        system = platform.system().lower()
        if system == "windows":
            return r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        elif system == "darwin":  # macOS
            return "/opt/homebrew/bin/tesseract"
        else:  # Linux
            return "/usr/bin/tesseract"
    
    def get_input_dir(self):
        """Get input directory path."""
        input_dir = self.config.get("paths", {}).get("input_dir", "../input")
        return str(self.project_root / input_dir)
    
    def get_output_dir(self):
        """Get output directory path."""
        output_dir = self.config.get("paths", {}).get("output_dir", "output")
        return str(self.project_root / output_dir)
    
    def get_supported_extensions(self):
        """Get supported file extensions."""
        return self.config["file_processing"]["supported_extensions"]

# Global configuration instance
config_manager = ConfigManager()

if __name__ == "__main__":
    # Test the configuration
    print("🔧 Configuration Manager Test:")
    print(f"Project root: {config_manager.project_root}")
    print(f"Input dir: {config_manager.get_input_dir()}")
    print(f"Output dir: {config_manager.get_output_dir()}")
    print(f"Tesseract cmd: {config_manager.get_tesseract_cmd()}")
    print(f"Azure endpoint: {config_manager.get_azure_config().get('endpoint', 'Not configured')}")
    print("✅ Configuration system working!") 