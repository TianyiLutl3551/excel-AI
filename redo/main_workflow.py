#!/usr/bin/env python3
"""
Refactored Main LangGraph Workflow for Document Processing
Clean, modular design with separated concerns
"""

import os
import argparse
from typing import Dict, Any

from langgraph.graph import StateGraph, END

# Import modular components
from file_type_classifier import FileTypeClassifierNode
from excel_workflow import ExcelWorkflowNode  
from msg_workflow import MsgWorkflowNode
from validation_node import ValidationNode
from config_manager import config_manager
from llm_client import real_llm_func, real_llm_vision_func
from file_manager import get_file_manager
from workflow_logger import get_workflow_logger


class DocumentProcessingWorkflow:
    """
    Main workflow orchestrator using LangGraph.
    Handles routing between Excel and MSG processing nodes.
    """
    
    def __init__(self):
        """Initialize the workflow with all nodes."""
        self.graph = StateGraph(dict)
        self.logger = get_workflow_logger()
        
        # Initialize workflow nodes
        self._setup_nodes()
        self._setup_routing()
        
        # Compile the graph
        self.workflow = self.graph.compile()
    
    def _setup_nodes(self):
        """Setup all processing nodes."""
        # Add processing nodes
        self.graph.add_node("classify", FileTypeClassifierNode())
        self.graph.add_node("excel_process", ExcelWorkflowNode())
        self.graph.add_node("msg_process", MsgWorkflowNode(
            llm_vision_func=real_llm_vision_func,
            llm_func=real_llm_func,
            output_dir=config_manager.get_output_dir()
        ))
        self.graph.add_node("validate", ValidationNode())
    
    def _setup_routing(self):
        """Setup workflow routing logic."""
        # Set entry point
        self.graph.set_entry_point("classify")
        
        # Add conditional routing based on file type
        self.graph.add_conditional_edges(
            "classify",
            self._route_by_file_type,
            {
                "excel_process": "excel_process",
                "msg_process": "msg_process",
                END: END
            }
        )
        
        # Add validation after processing
        self.graph.add_edge("excel_process", "validate")
        self.graph.add_edge("msg_process", "validate")
        self.graph.add_edge("validate", END)
    
    def _route_by_file_type(self, state: Dict[str, Any]) -> str:
        """
        Route processing based on detected file type.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name to execute
        """
        file_type = state.get("file_type", "unknown")
        
        if file_type in ["xlsx", "xls"]:
            return "excel_process"
        elif file_type == "msg":
            return "msg_process"
        else:
            print(f"❌ Unsupported file type: {file_type}")
            return END
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single file through the workflow.
        
        Args:
            file_path: Path to file to process
            
        Returns:
            Processing results
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Log processing start
        self.logger.log_process_start(file_path)
        
        # Initialize workflow state
        initial_state = {"file_path": file_path}
        
        print(f"🔄 Processing file: {file_path}")
        print("=" * 60)
        
        try:
            # Execute workflow
            result = self.workflow.invoke(initial_state)
            
            # Display results
            self._display_results(result)
            
            return result
            
        except Exception as e:
            print(f"❌ Workflow error: {e}")
            self.logger.log_error(file_path, str(e), "workflow")
            raise
    
    def _display_results(self, result: Dict[str, Any]):
        """
        Display processing results in a formatted way.
        
        Args:
            result: Workflow execution results
        """
        print("\n📋 Processing Results:")
        print("=" * 60)
        
        file_type = result.get("file_type", "unknown")
        print(f"📄 File type: {file_type}")
        
        if file_type in ["xlsx", "xls"]:
            self._display_excel_results(result)
        elif file_type == "msg":
            self._display_msg_results(result)
        else:
            print(f"❌ Unsupported file type: {file_type}")
    
    def _display_excel_results(self, result: Dict[str, Any]):
        """Display Excel processing results."""
        excel_outputs = result.get("excel_outputs", {})
        
        if excel_outputs.get("success", False):
            print("✅ Excel processing successful!")
            print(f"📁 Output: {excel_outputs['combined_output']}")
            print(f"📊 Sheets processed: {excel_outputs['processed_sheets']}")
        else:
            print("❌ Excel processing failed")
    
    def _display_msg_results(self, result: Dict[str, Any]):
        """Display MSG processing results."""
        msg_outputs = result.get("msg_outputs", {})
        
        if msg_outputs.get("success", False):
            print("✅ MSG processing successful!")
            print(f"📁 Highlights: {msg_outputs['highlight_output']}")
            print(f"📁 Table: {msg_outputs['table_output']}")
            print(f"📊 Table type: {msg_outputs['table_type']}")
        else:
            print("❌ MSG processing failed")


class WorkflowManager:
    """
    High-level manager for different processing modes.
    Handles file discovery and batch processing.
    """
    
    def __init__(self, input_dir: str = None):
        """
        Initialize workflow manager.
        
        Args:
            input_dir: Input directory override
        """
        self.file_manager = get_file_manager(input_dir)
        self.workflow = DocumentProcessingWorkflow()
        self.logger = get_workflow_logger()
    
    def process_all(self):
        """Process all files in input directory."""
        files = self.file_manager.get_all_files()
        
        if not files:
            print("No files found to process")
            return
        
        print(f"Processing ALL files: {[os.path.basename(f) for f in files]}")
        
        successful = 0
        failed = 0
        
        for file_path in files:
            try:
                self.workflow.process_file(file_path)
                successful += 1
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")
                failed += 1
        
        # Log summary
        self.logger.log_summary(len(files), successful, failed)
        print(f"\n📊 Summary: {len(files)} total, {successful} successful, {failed} failed")
    
    def process_by_date(self, date_code: str):
        """
        Process files matching a specific date.
        
        Args:
            date_code: Date in YYYYMMDD format
        """
        files = self.file_manager.get_files_by_date(date_code)
        
        if not files:
            print(f"No files found for date code {date_code}")
            return
        
        print(f"Processing files for date {date_code}: {[os.path.basename(f) for f in files]}")
        
        for file_path in files:
            try:
                self.workflow.process_file(file_path)
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")
    
    def process_unprocessed(self, processed_log_file: str = None):
        """
        Process files that haven't been processed yet.
        
        Args:
            processed_log_file: Path to processing log file
        """
        if processed_log_file is None:
            processed_log_file = self.logger.process_log_file
        
        files = self.file_manager.get_unprocessed_files(processed_log_file)
        
        if not files:
            print("No unprocessed files found")
            return
        
        print(f"Processing UNPROCESSED files: {[os.path.basename(f) for f in files]}")
        
        for file_path in files:
            try:
                self.workflow.process_file(file_path)
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")
    
    def get_stats(self):
        """Display file statistics."""
        stats = self.file_manager.get_file_stats()
        
        print("📊 File Statistics:")
        print(f"   Total files: {stats['total_files']}")
        print(f"   By extension: {stats['by_extension']}")
        print(f"   Date codes: {stats['date_codes']}")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Process Excel/MSG files with modular LangGraph workflow.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main_workflow_refactored.py --mode all
  python main_workflow_refactored.py --mode single --date 20240501
  python main_workflow_refactored.py --mode unprocessed
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['all', 'single', 'unprocessed', 'stats'], 
        default='single',
        help='Processing mode'
    )
    parser.add_argument(
        '--date', 
        type=str, 
        help='Date code (YYYYMMDD) for single mode'
    )
    parser.add_argument(
        '--input_dir', 
        type=str, 
        help='Input directory override'
    )
    parser.add_argument(
        '--processed_file', 
        type=str, 
        help='Tracking file for processed files'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize workflow manager
        manager = WorkflowManager(args.input_dir)
        
        # Execute based on mode
        if args.mode == 'all':
            manager.process_all()
            
        elif args.mode == 'single':
            if not args.date:
                print("Error: --date argument required for single mode")
                return 1
            manager.process_by_date(args.date)
            
        elif args.mode == 'unprocessed':
            manager.process_unprocessed(args.processed_file)
            
        elif args.mode == 'stats':
            manager.get_stats()
        
        return 0
        
    except Exception as e:
        print(f"❌ Application error: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 