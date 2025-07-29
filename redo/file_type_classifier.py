import os
import json

class FileTypeClassifierNode:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r") as f:
            config = json.load(f)
        # 统一小写，去空格
        self.allowed_types = [ext.lower().strip() for ext in config.get("file_types", [])]

    def __call__(self, state: dict) -> dict:
        file_path = state["file_path"]
        ext = os.path.splitext(file_path)[1].lower()
        if ext in self.allowed_types:
            file_type = ext.lstrip(".")
        else:
            file_type = "unknown"
        state["file_type"] = file_type
        return state 