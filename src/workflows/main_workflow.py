import os
import sys
import argparse
from typing import Dict, Any
from langgraph.graph import StateGraph, END

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.file_type_classifier import FileTypeClassifierNode
from src.workflows.excel_workflow import ExcelWorkflowNode
from src.workflows.msg_workflow import MsgWorkflowNode
from src.nodes.validation_node import ValidationNode
from src.utils.config_manager import config_manager
from src.utils.llm_client import real_llm_func, real_llm_vision_func
from src.utils.file_manager import get_file_manager
from src.utils.workflow_logger import WorkflowLogger 