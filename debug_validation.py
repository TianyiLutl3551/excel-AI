#!/usr/bin/env python3
"""
Debug script to run validation on a specific file and show detailed output
"""

import os
import sys
import pandas as pd
import hashlib
from datetime import datetime

# Add the redo directory to the path so we can import the modules
sys.path.append('/Users/lutianyi/Desktop/excel AI/redo')

from main_workflow import DocumentProcessingWorkflow, log_process

def debug_validation(file_path: str):
    """Run the workflow on a specific file and show detailed validation output"""
    
    print(f"🔍 DEBUG: Processing file: {file_path}")
    print("=" * 80)
    
    # Run the workflow
    workflow = DocumentProcessingWorkflow()
    initial_state = {"file_path": file_path}
    
    try:
        result = workflow.workflow.invoke(initial_state)
        
        print("\n📋 PROCESSING RESULTS:")
        print("=" * 80)
        
        file_type = result.get("file_type", "unknown")
        print(f"📄 File type: {file_type}")
        
        if file_type == "msg":
            msg_outputs = result.get("msg_outputs", {})
            if msg_outputs.get("success", False):
                print("✅ MSG processing successful!")
                print(f"📁 Highlights: {msg_outputs['highlight_output']}")
                print(f"📁 Table: {msg_outputs['table_output']}")
                print(f"📊 Table type: {msg_outputs['table_type']}")
                
                # Show validation details
                validation = result.get("validation", {})
                if validation:
                    print("\n🔍 VALIDATION DETAILS:")
                    print("=" * 80)
                    print(f"Match: {validation.get('match', 'N/A')}")
                    print(f"Hash 1 (Original): {validation.get('hash1', 'N/A')}")
                    print(f"Hash 2 (LLM): {validation.get('hash2', 'N/A')}")
                    print(f"Process time: {validation.get('process_time', 'N/A')} seconds")
                    
                    # Show the concatenated strings (first 200 chars each)
                    concat1 = validation.get('concat1', '')
                    concat2 = validation.get('concat2', '')
                    
                    print(f"\n📝 Original concatenated string (first 200 chars):")
                    print(f"'{concat1[:200]}...'")
                    print(f"\n📝 LLM concatenated string (first 200 chars):")
                    print(f"'{concat2[:200]}...'")
                    
                    # Show the actual data being compared
                    print("\n📊 DATA COMPARISON:")
                    print("=" * 80)
                    
                    # Get Document Intelligence data
                    docint_df = msg_outputs.get("docint_df")
                    if docint_df is not None:
                        print("📋 Document Intelligence Data (first 10 rows):")
                        print(docint_df.head(10))
                        print(f"Total rows: {len(docint_df)}")
                        
                        # Show the columns being hashed
                        if "Liability" in docint_df.columns and "Asset" in docint_df.columns:
                            print(f"\n🔢 Liability column sample: {docint_df['Liability'].head(5).tolist()}")
                            print(f"🔢 Asset column sample: {docint_df['Asset'].head(5).tolist()}")
                    
                    # Get LLM output data
                    table_path = msg_outputs.get("table_output")
                    if table_path and os.path.exists(table_path):
                        llm_df = pd.read_excel(table_path)
                        print(f"\n📋 LLM Output Data (first 10 rows):")
                        print(llm_df.head(10))
                        print(f"Total rows: {len(llm_df)}")
                        
                        # Show the columns being hashed
                        if "RIDER_VALUE" in llm_df.columns and "ASSET_VALUE" in llm_df.columns:
                            print(f"\n🔢 RIDER_VALUE column sample: {llm_df['RIDER_VALUE'].head(5).tolist()}")
                            print(f"🔢 ASSET_VALUE column sample: {llm_df['ASSET_VALUE'].head(5).tolist()}")
                    
                else:
                    print("❌ No validation data found")
                    
            else:
                print("❌ MSG processing failed")
                print(f"Error: {msg_outputs.get('error', 'Unknown error')}")
        else:
            print(f"❌ Unexpected file type: {file_type}")
            
    except Exception as e:
        print(f"❌ Workflow error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # The specific file to debug
    file_path = "/Users/lutianyi/Desktop/excel AI/input/FW_ Daily Hedging P&L Summary for DBIB 2025_06_13.msg"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    debug_validation(file_path) 