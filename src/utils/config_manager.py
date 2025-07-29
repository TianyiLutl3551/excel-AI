import os
import json
import toml
import platform
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file="config/config.json", secrets_file="config/secrets.toml"):
        # Get the project root (redo folder)
        self.current_dir = Path(__file__).parent.parent.parent  # Go up from src/utils/ to redo/
        self.config_path = self.current_dir / config_file
        self.secrets_path = self.current_dir / secrets_file
        self.project_root = self.current_dir
        self.config = self._load_config()
        self.secrets = self._load_secrets() 