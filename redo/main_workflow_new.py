#!/usr/bin/env python3
"""
Simplified Main LangGraph workflow for document processing
Clean, modular design with separated concerns
"""

import os
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from file_type_classifier import FileTypeClassifierNode
from excel_workflow import ExcelWorkflowNode
from msg_workflow import MsgWorkflowNode
from validation_node import ValidationNode
from config_manager import ConfigManager
from logging_node import ProcessLoggingNode

class DocumentProcessingWorkflow:
    def __init__(self):
        """Initialize the workflow with clean, focused nodes."""
        self.config = ConfigManager()
        self.build_graph()
        
    def build_graph(self):
        """Build the workflow graph with clear separation of concerns."""
        self.graph = StateGraph(dict)
        
        # Add nodes
        self.graph.add_node("log_process", ProcessLoggingNode())
        self.graph.add_node("classify", FileTypeClassifierNode())
        self.graph.add_node("excel_process", ExcelWorkflowNode())
        self.graph.add_node("msg_process", MsgWorkflowNode(
            llm_vision_func=self.config.get_llm_vision_func(),
            llm_func=self.config.get_llm_func(),
            output_dir=self.config.get_output_dir()
        ))
        self.graph.add_node("validate", ValidationNode())
        
        # Set entry point
        self.graph.set_entry_point("log_process")
        
        # Add edges
        self.graph.add_edge("log_process", "classify")
        self.graph.add_conditional_edges(
            "classify",
            self.route_by_file_type,
            {
                "excel_process": "excel_process",
                "msg_process": "msg_process",
                END: END
            }
        )
        self.graph.add_edge("excel_process", "validate")
        self.graph.add_edge("msg_process", "validate")
        self.graph.add_edge("validate", END)
        
        self.workflow = self.graph.compile()
    
    def route_by_file_type(self, state: Dict[str, Any]) -> str:
        """Route files based on their type."""
        file_type = state.get("file_type", "unknown")
        if file_type in ["xlsx", "xls"]:
            return "excel_process"
        elif file_type == "msg":
            return "msg_process"
        else:
            print(f"❌ Unsupported file type: {file_type}")
            return END

def process_single_file(file_path: str) -> Dict[str, Any]:
    """Process a single file through the workflow."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    workflow = DocumentProcessingWorkflow()
    initial_state = {"file_path": file_path}
    
    print(f"🔄 Processing file: {file_path}")
    print("=" * 60)
    
    try:
        result = workflow.workflow.invoke(initial_state)
        print("\n📋 Processing Results:")
        print("=" * 60)
        
        file_type = result.get("file_type", "unknown")
        print(f"📄 File type: {file_type}")
        
        if file_type in ["xlsx", "xls"]:
            excel_outputs = result.get("excel_outputs", {})
            if excel_outputs.get("success", False):
                print("✅ Excel processing successful!")
                print(f"📁 Output: {excel_outputs['combined_output']}")
                print(f"📊 Sheets processed: {excel_outputs['processed_sheets']}")
            else:
                print("❌ Excel processing failed")
        elif file_type == "msg":
            msg_outputs = result.get("msg_outputs", {})
            if msg_outputs.get("success", False):
                print("✅ MSG processing successful!")
                print(f"📁 Highlights: {msg_outputs['highlight_output']}")
                print(f"📁 Table: {msg_outputs['table_output']}")
                print(f"📊 Table type: {msg_outputs['table_type']}")
            else:
                print("❌ MSG processing failed")
        else:
            print(f"❌ Unsupported file type: {file_type}")
            
        return result
    except Exception as e:
        print(f"❌ Workflow error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    from cli import WorkflowCLI
    cli = WorkflowCLI()
    cli.run()
