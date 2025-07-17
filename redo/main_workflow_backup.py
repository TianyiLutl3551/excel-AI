#!/usr/bin/env python3
"""
Main LangGraph workflow for document processing
Handles file type classification and routes to appropriate processing nodes
"""

import os
import json
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from file_type_classifier import FileTypeClassifierNode
from excel_workflow import ExcelWorkflowNode
from msg_workflow import MsgWorkflowNode
import toml
from openai import OpenAI
import base64
from PIL import Image
import io
from validation_node import ValidationNode
from datetime import datetime
import argparse
import re

# Load configuration
def load_config():
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

config = load_config()

# Real LLM function (same as in test_msg_node.py)
def real_llm_func(prompt):
    secrets = toml.load("secrets.toml")
    api_key = secrets["openai"]["api_key"]
    model = secrets["openai"]["model"]
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a data analysis expert that helps transform and organize Excel data. Always return valid JSON arrays."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content.strip()
        print(f"[DEBUG] Raw LLM response:\n{content}")
        
        # Use the robust JSON extraction method from reference code
        import re, json
        json_match = re.search(r'(\[.*?\])', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            try:
                data = json.loads(json_str)
                if not isinstance(data, list):
                    print("LLM response is not a JSON array")
                    return {"table": ""}
                
                # Convert JSON array to CSV format for compatibility
                import pandas as pd
                df = pd.DataFrame(data)
                from io import StringIO
                csv_str = df.to_csv(index=False)
                return {"table": csv_str}
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                return {"table": ""}
        else:
            print("No JSON array found in LLM response.")
            return {"table": ""}
    except Exception as e:
        print(f"Error calling OpenAI LLM: {e}")
        return {"table": ""}

def real_llm_vision_func(image_path):
    # Load OpenAI API key and model from secrets.toml
    secrets = toml.load("secrets.toml")
    api_key = secrets["openai"]["api_key"]
    model = secrets["openai"].get("vision_model", "gpt-4o")
    client = OpenAI(api_key=api_key)
    prompt = "Classify this picture: is it a blue table or a red table. Return blue or red. Don't return anything else."
    # Read image and encode as base64
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]}
            ]
        )
        content = response.choices[0].message.content.strip().lower()
        if "blue" in content:
            return "blue"
        elif "red" in content:
            return "red"
        else:
            print(f"Vision model returned unexpected content: {content}")
            return "unknown"
    except Exception as e:
        print(f"Error calling OpenAI vision model: {e}")
        return "unknown"

class DocumentProcessingWorkflow:
    def __init__(self):
        """Initialize the workflow with all nodes."""
        self.graph = StateGraph(dict)
        
        # Add nodes
        self.graph.add_node("classify", FileTypeClassifierNode())
        self.graph.add_node("excel_process", ExcelWorkflowNode())
        self.graph.add_node("msg_process", MsgWorkflowNode(
            llm_vision_func=real_llm_vision_func,
            llm_func=real_llm_func,
            output_dir="/Users/lutianyi/Desktop/excel AI/redo/output"
        ))
        self.graph.add_node("validate", ValidationNode())
        
        # Set entry point
        self.graph.set_entry_point("classify")
        
        # Add conditional edges for routing
        self.graph.add_conditional_edges(
            "classify",
            self.route_by_file_type,
            {
                "excel_process": "excel_process",
                "msg_process": "msg_process",
                END: END
            }
        )
        
        # Add validation after both excel and msg processing
        self.graph.add_edge("excel_process", "validate")
        self.graph.add_edge("msg_process", "validate")
        self.graph.add_edge("validate", END)
        
        # Compile the graph
        self.workflow = self.graph.compile()
    
    def route_by_file_type(self, state: Dict[str, Any]) -> str:
        file_type = state.get("file_type", "unknown")
        if file_type in ["xlsx", "xls"]:
            return "excel_process"
        elif file_type == "msg":
            return "msg_process"
        else:
            print(f"❌ Unsupported file type: {file_type}")
            return END

def log_process(file_path):
    log_path = config.get('process_log_file', '/Users/lutianyi/Desktop/excel AI/redo/output/process_log.txt')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_name = os.path.basename(file_path)
    with open(log_path, 'a') as f:
        f.write(f"[{timestamp}] {file_name}\n")

def process_single_file(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    # Log the process at the start
    log_process(file_path)
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

def extract_date_code(filename):
    """Extract date code in the form YYYYMMDD from a filename."""
    # Match 20240801 or 2024_08_01 or 2024-08-01
    match = re.search(r'(20\d{2})[\-_]?([01]\d)[\-_]?([0-3]\d)', filename)
    if match:
        return f"{match.group(1)}{match.group(2)}{match.group(3)}"
    return None

def get_all_files(input_dir):
    files = []
    for fname in os.listdir(input_dir):
        if fname.startswith('.'):
            continue
        if fname.lower().endswith(('.xlsx', '.xls', '.msg')):
            files.append(os.path.join(input_dir, fname))
    return files

def get_files_by_date(input_dir, date_code):
    files = get_all_files(input_dir)
    matched = []
    for f in files:
        code = extract_date_code(os.path.basename(f))
        if code == date_code:
            matched.append(f)
    return matched

def get_unprocessed_files(input_dir, processed_file):
    files = get_all_files(input_dir)
    processed = set()
    if os.path.exists(processed_file):
        with open(processed_file, 'r') as f:
            for line in f:
                if line.strip() and line.startswith('['):
                    # Extract filename from timestamp line: [timestamp] filename
                    parts = line.strip().split('] ', 1)
                    if len(parts) == 2:
                        processed.add(parts[1])
                        print(f"[DEBUG] Found processed file: {parts[1]}")
    print(f"[DEBUG] All processed files: {processed}")
    unprocessed = []
    for f in files:
        filename = os.path.basename(f)
        print(f"[DEBUG] Checking file: {filename}")
        if filename not in processed:
            unprocessed.append(f)
            print(f"[DEBUG] Adding to unprocessed: {filename}")
        else:
            print(f"[DEBUG] Skipping (already processed): {filename}")
    return unprocessed

def mark_as_processed(processed_file, date_codes):
    from datetime import datetime
    now = datetime.now()
    timestamp = now.strftime('[%Y-%m-%d %H:%M:%S]')
    with open(processed_file, 'a') as f:
        f.write(f"\n{timestamp}\n")
        for code in date_codes:
            f.write(f"{code}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Excel/MSG files with LangGraph workflow.")
    parser.add_argument('--mode', choices=['all', 'single', 'unprocessed'], default='single', help='Processing mode')
    parser.add_argument('--date', type=str, help='Date code (YYYYMMDD) for single mode')
    parser.add_argument('--input_dir', type=str, default=config.get('input_dir', '/Users/lutianyi/Desktop/excel AI/input'), help='Input directory')
    parser.add_argument('--processed_file', type=str, default=config.get('process_log_file', '/Users/lutianyi/Desktop/excel AI/process_record.txt'), help='Tracking file for processed date codes')
    args = parser.parse_args()

    if args.mode == 'all':
        files = get_all_files(args.input_dir)
        print(f"Processing ALL files: {files}")
        for f in files:
            process_single_file(f)
    elif args.mode == 'single':
        if not args.date:
            print("--date argument required for single mode")
        else:
            files = get_files_by_date(args.input_dir, args.date)
            if not files:
                print(f"No files found for date code {args.date}")
            else:
                print(f"Processing files for date {args.date}: {files}")
                for f in files:
                    process_single_file(f)
    elif args.mode == 'unprocessed':
        files = get_unprocessed_files(args.input_dir, args.processed_file)
        print(f"Processing UNPROCESSED files: {files}")
        for f in files:
            process_single_file(f) 