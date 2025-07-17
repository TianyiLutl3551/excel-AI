import os

class FileTypeClassifierNode:
    """
    LangGraph node: Classifies the file type based on extension.
    Usage: state = FileTypeClassifierNode()(state)
    Expects state['file_path'], adds state['file_type'] ('excel', 'msg', or 'unknown')
    """
    def __call__(self, state: dict) -> dict:
        file_path = state["file_path"]
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".xlsx", ".xls"]:
            file_type = "excel"
        elif ext == ".msg":
            file_type = "msg"
        else:
            file_type = "unknown"
        state["file_type"] = file_type
        return state 