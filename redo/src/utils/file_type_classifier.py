import os
from src.utils.config_manager import ConfigManager

class FileTypeClassifierNode:
    def __init__(self, config_path="config/config.json"):
        # Use ConfigManager for consistent configuration handling
        self.config_manager = ConfigManager()
        # Get supported extensions from the new config structure
        self.allowed_types = [ext.lower().strip() for ext in self.config_manager.get_supported_extensions()]

    def __call__(self, state: dict) -> dict:
        file_path = state["file_path"]
        ext = os.path.splitext(file_path)[1].lower()
        if ext in self.allowed_types:
            file_type = ext.lstrip(".")
        else:
            file_type = "unknown"
        state["file_type"] = file_type
        return state
