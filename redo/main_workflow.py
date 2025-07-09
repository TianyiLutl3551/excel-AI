#!/usr/bin/env python3
"""
Main LangGraph workflow for document processing
Handles file type classification and routes to appropriate processing nodes
"""

import os
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

def process_single_file(file_path: str) -> Dict[str, Any]:
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

def main():
    test_file = "/Users/lutianyi/Desktop/excel AI/input/SampleInput20240802.xlsx"
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        print("Please update the test_file path in main() function")
        return
    try:
        result = process_single_file(test_file)
        print("\n🎉 Workflow completed successfully!")
    except Exception as e:
        print(f"❌ Workflow failed: {e}")

if __name__ == "__main__":
    main() 