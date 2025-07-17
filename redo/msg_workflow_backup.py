import os
import pandas as pd
from msg_processor import MsgProcessor
import extract_msg
from bs4 import BeautifulSoup
import re
from datetime import datetime
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../reference code')))
from prompt import get_llm_prompt as get_blue_llm_prompt
from prompt2 import get_llm_prompt2 as get_red_llm_prompt

class MsgWorkflowNode:
    def __init__(self, llm_vision_func, llm_func, output_dir=None):
        import json
        config_path = "/Users/lutianyi/Desktop/excel AI/redo/config.json"
        if output_dir is None:
            with open(config_path, "r") as f:
                config = json.load(f)
            output_dir = config.get("output_dir", "redo/output")
        self.processor = MsgProcessor(llm_vision_func)
        self.llm_func = llm_func  # Function to call LLM for table extraction
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_highlights(self, msg_path):
        msg = extract_msg.Message(msg_path)
        subject = msg.subject or ""
        match = re.search(r'(\d{4})[/-](\d{2})[/-](\d{2})', subject)
        if match:
            date_str = ''.join(match.groups())
        else:
            date_str = datetime.now().strftime('%Y%m%d')
        html = getattr(msg, 'htmlBody', None) or msg.body or getattr(msg, 'rtfBody', None) or ""
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator='\n')
        lines = text.splitlines()
        daily, qtd, generic = [], [], []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Robust Dynamic P&L Highlights extraction
            if re.search(r'Dynamic.*P.*L.*Highlights|Dynamic.*P&amp;L.*Highlights', line, re.IGNORECASE):
                section = [line]
                i += 1
                # Skip blank lines after header
                while i < len(lines) and lines[i].strip() == '':
                    i += 1
                # Collect all indented/bullet/monetary lines
                while i < len(lines):
                    next_line = lines[i]
                    next_line_stripped = next_line.strip()
                    # Stop if new section header (all caps, not a highlight)
                    if (re.match(r'^[A-Z][A-Za-z0-9 &/:-]{2,}$', next_line_stripped) and not re.search(r'highlights', next_line_stripped, re.IGNORECASE)):
                        break
                    # Collect if indented, bullet, or contains $/m, or is not empty
                    if (next_line.startswith(' ') or next_line.startswith('\xa0') or
                        re.search(r'[•▪o\-]', next_line_stripped) or
                        re.search(r'\$[0-9]+m', next_line_stripped, re.IGNORECASE) or
                        next_line_stripped):
                        section.append(next_line_stripped)
                    i += 1
                # Clean up the section text - remove excessive whitespace
                cleaned_section = self._clean_highlights_text('\n'.join(section))
                daily.append(cleaned_section)
            elif re.search(r'daily highlights', line, re.IGNORECASE):
                section = [line]
                i += 1
                while i < len(lines):
                    if (re.match(r'^[A-Z][A-Za-z0-9 &/:-]{2,}$', lines[i].strip()) and not re.search(r'highlights', lines[i], re.IGNORECASE)) or lines[i].strip() == '':
                        break
                    section.append(lines[i].strip())
                    i += 1
                cleaned_section = self._clean_highlights_text('\n'.join(section))
                daily.append(cleaned_section)
            elif re.search(r'qtd highlights', line, re.IGNORECASE):
                section = [line]
                i += 1
                while i < len(lines):
                    if (re.match(r'^[A-Z][A-Za-z0-9 &/:-]{2,}$', lines[i].strip()) and not re.search(r'highlights', lines[i], re.IGNORECASE)) or lines[i].strip() == '':
                        break
                    section.append(lines[i].strip())
                    i += 1
                cleaned_section = self._clean_highlights_text('\n'.join(section))
                qtd.append(cleaned_section)
            elif re.search(r'highlights', line, re.IGNORECASE):
                section = [line]
                i += 1
                while i < len(lines):
                    if (re.match(r'^[A-Z][A-Za-z0-9 &/:-]{2,}$', lines[i].strip()) and not re.search(r'highlights', lines[i], re.IGNORECASE)) or lines[i].strip() == '':
                        break
                    section.append(lines[i].strip())
                    i += 1
                cleaned_section = self._clean_highlights_text('\n'.join(section))
                generic.append(cleaned_section)
            else:
                i += 1
        if not daily and not qtd and generic:
            daily = generic
        highlights_df = pd.DataFrame({
            'Daily Highlights': daily if daily else [''],
            'QTD Highlights': qtd if qtd else ['']
        })
        highlight_path = os.path.join(self.output_dir, f"highlights_{date_str}.xlsx")
        highlights_df.to_excel(highlight_path, index=False)
        return highlight_path

    def _clean_highlights_text(self, text):
        """Clean up highlights text by removing excessive whitespace and empty lines."""
        # Replace multiple newlines with single newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text

    def __call__(self, state: dict) -> dict:
        file_path = state["file_path"]
        highlight_path = self.extract_highlights(file_path)
        result = self.processor.process_msg(file_path)
        if not result:
            state["msg_outputs"] = {"success": False, "reason": "No target image found"}
            return state
        table_type = result["table_type"]
        table_text = result["table_text"]
        image_path = result["image_path"]
        print(f"[DEBUG] Table type classified by vision model: {table_type}")
        print("[DEBUG] Azure OCR table_text sent to LLM:\n", table_text)
        # Use the correct prompt logic
        if table_type == "blue":
            prompt = get_blue_llm_prompt(table_text)
        else:
            prompt = get_red_llm_prompt(table_text)
        print("[DEBUG] LLM Prompt:\n", prompt)
        # Patch: capture full LLM response
        llm_output = self.llm_func(prompt, return_full_response=True) if 'return_full_response' in self.llm_func.__code__.co_varnames else self.llm_func(prompt)
        if isinstance(llm_output, dict) and 'full_response' in llm_output:
            print("[DEBUG] Full LLM response content:\n", llm_output['full_response'])
        table_csv = llm_output.get("table", "")
        print("[DEBUG] Raw LLM table CSV output:\n", table_csv)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        table_path = os.path.join(self.output_dir, f"table_{base_name}.xlsx")
        if not table_csv.strip():
            print("[ERROR] LLM did not return a valid table CSV. Skipping table save.")
            state["msg_outputs"] = {
                "success": False,
                "table_type": table_type,
                "highlight_output": highlight_path,
                "table_output": None,
                "error": "LLM did not return a valid table CSV."
            }
            return state
        try:
            import pandas as pd
            from io import StringIO
            df = pd.read_csv(StringIO(table_csv))
            # --- POST-PROCESSING FILTER ---
            # Remove rows where RISK_TYPE or label contains 'Total' (except 'HY_Total')
            def is_valid_row(row):
                for col in row.index:
                    val = str(row[col]).lower()
                    if 'total' in val and 'hy_total' not in val:
                        return False
                return True
            if 'RISK_TYPE' in df.columns:
                mask = df['RISK_TYPE'].apply(lambda x: ('total' not in str(x).lower()) or ('hy_total' in str(x).lower()))
                df = df[mask]
            else:
                df = df[df.apply(is_valid_row, axis=1)]
            df.to_excel(table_path, index=False)
        except Exception as e:
            print(f"[ERROR] Failed to parse LLM table CSV: {e}")
            state["msg_outputs"] = {
                "success": False,
                "table_type": table_type,
                "highlight_output": highlight_path,
                "table_output": None,
                "error": f"Failed to parse LLM table CSV: {e}"
            }
            return state

        # --- Only for validation: robustly parse table_text to DataFrame ---
        docint_df = None
        if table_text.strip():
            try:
                # Parse the Document Intelligence table_text using correct logic
                lines = table_text.strip().split('\n')
                
                # Step 1: Delete empty rows
                non_empty_lines = [line for line in lines if line.strip()]
                
                if table_type == "red":
                    # Red table parsing logic (existing logic)
                    # Step 2: Find the header row with "Liability" and "Asset" (robust)
                    parsed_data = []
                    header_line = None
                    for i, line in enumerate(non_empty_lines):
                        norm_line = ' '.join(line.strip().lower().split())
                        if 'liability' in norm_line and 'asset' in norm_line:
                            header_line = i
                            break
                    
                    if header_line is not None:
                        # Step 3: Extract data rows after header, skipping "Total" rows (except "HY Total")
                        data_rows = []
                        for line in non_empty_lines[header_line + 1:]:
                            # Skip rows containing "Total" (unless it's "HY Total")
                            if 'Total' in line and 'HY Total' not in line:
                                continue
                            data_rows.append(line)
                        
                        # Step 4: Parse each data row to extract Liability and Asset values
                        print("[DEBUG] Document Intelligence parsing rows (RED table):")
                        for i, line in enumerate(data_rows):
                            print(f"[DEBUG] Row {i}: {line}")
                            parts = line.split()
                            numeric_values = []
                            for part in parts:
                                try:
                                    if part in ['None', 'nan', '', '-']:
                                        numeric_values.append(0)
                                    else:
                                        # If it's an integer, keep as int; if decimal, keep as float
                                        if re.match(r'^-?\d+$', part):
                                            numeric_values.append(int(part))
                                        elif re.match(r'^-?\d+\.\d+$', part):
                                            numeric_values.append(float(part))
                                        else:
                                            continue
                                except ValueError:
                                    continue
                            # Skip rows that only contain zeros (from None/nan values)
                            if len(numeric_values) >= 2 and not all(x == 0 for x in numeric_values):
                                parsed_data.append({
                                    'Liability': numeric_values[0],
                                    'Asset': numeric_values[1]
                                })
                                print(f"[DEBUG] Parsed: Liability={numeric_values[0]}, Asset={numeric_values[1]}")
                            else:
                                print(f"[DEBUG] Skipped: insufficient numeric values or all zeros")
                    else:
                        print("[DEBUG] No header found with both 'Liability' and 'Asset' in Document Intelligence output (RED table)")
                
                elif table_type == "blue":
                    # Blue table parsing logic - different column structure
                    parsed_data = []
                    
                    # For blue tables, we need to find the header row and identify columns
                    # Blue table structure: VA Rider DBIB | Rider | Asset | Daily Net | QTD Net
                    # Where "Rider" is the Liability column and "Asset" is the Asset column
                    
                    header_line = None
                    rider_col_idx = None
                    asset_col_idx = None
                    
                    for i, line in enumerate(non_empty_lines):
                        norm_line = ' '.join(line.strip().lower().split())
                        # Look for "rider" and "asset" in the header
                        if 'rider' in norm_line and 'asset' in norm_line:
                            header_line = i
                            # Find the column indices
                            parts = line.split()
                            print(f"[DEBUG] Header line parts: {parts}")
                            for j, part in enumerate(parts):
                                if 'rider' in part.lower() and 'asset' not in part.lower():
                                    rider_col_idx = j
                                elif 'asset' in part.lower():
                                    asset_col_idx = j
                            break
                    
                    # If we didn't find the header, try a different approach
                    if header_line is None:
                        # Look for the line that contains column numbers and headers
                        for i, line in enumerate(non_empty_lines):
                            if re.search(r'\d+\s+\d+\s+\d+', line) and 'rider' in line.lower() and 'asset' in line.lower():
                                header_line = i
                                # Parse the header line to find column indices
                                parts = line.split()
                                print(f"[DEBUG] Found header line: {line}")
                                print(f"[DEBUG] Header parts: {parts}")
                                
                                # For blue tables, the structure is typically:
                                # VA Rider DBIB | Rider | Asset | Daily Net | QTD Net
                                # We need to find the "Rider" and "Asset" columns
                                for j, part in enumerate(parts):
                                    if 'rider' in part.lower() and 'asset' not in part.lower() and 'va' not in part.lower():
                                        rider_col_idx = j
                                        print(f"[DEBUG] Found Rider column at index {j}: {part}")
                                    elif 'asset' in part.lower():
                                        asset_col_idx = j
                                        print(f"[DEBUG] Found Asset column at index {j}: {part}")
                                break
                    
                    # If we still don't have the correct indices, use the known structure
                    if rider_col_idx is None or asset_col_idx is None:
                        print("[DEBUG] Could not find column indices automatically, using known structure")
                        # Based on the debug output, the correct indices are:
                        # Column 1 (index 1): Rider (Liability)
                        # Column 2 (index 2): Asset
                        rider_col_idx = 1
                        asset_col_idx = 2
                        print(f"[DEBUG] Using default indices: Rider={rider_col_idx}, Asset={asset_col_idx}")
                 
                 if header_line is not None and rider_col_idx is not None and asset_col_idx is not None:
                     print(f"[DEBUG] Found blue table header at line {header_line}")
                     print(f"[DEBUG] Rider column index: {rider_col_idx}, Asset column index: {asset_col_idx}")
                     
                     # Step 3: Extract data rows after header, skipping "Total" rows (except "HY Total")
                     data_rows = []
                     for line in non_empty_lines[header_line + 1:]:
                         # Skip rows containing "Total" (unless it's "HY Total")
                         if 'Total' in line and 'HY Total' not in line:
                             continue
                         data_rows.append(line)
                     
                     # Step 4: Parse each data row to extract Rider (Liability) and Asset values
                     print("[DEBUG] Document Intelligence parsing rows (BLUE table):")
                     for i, line in enumerate(data_rows):
                         print(f"[DEBUG] Row {i}: {line}")
                         parts = line.split()
                         
                         # Check if we have enough columns
                         if len(parts) > max(rider_col_idx, asset_col_idx):
                             try:
                                 # Extract Rider value (Liability)
                                 rider_val_str = parts[rider_col_idx]
                                 asset_val_str = parts[asset_col_idx]
                                 
                                 # Parse Rider value
                                 if rider_val_str in ['None', 'nan', '', '-']:
                                     rider_val = 0
                                 elif rider_val_str.startswith('(') and rider_val_str.endswith(')'):
                                     # Convert (14.8) to -14.8
                                     clean_part = rider_val_str[1:-1]
                                     if re.match(r'^\d+\.?\d*$', clean_part):
                                         rider_val = -float(clean_part)
                                     else:
                                         continue
                                 else:
                                     if re.match(r'^-?\d+$', rider_val_str):
                                         rider_val = int(rider_val_str)
                                     elif re.match(r'^-?\d+\.\d+$', rider_val_str):
                                         rider_val = float(rider_val_str)
                                     else:
                                         continue
                                 
                                 # Parse Asset value
                                 if asset_val_str in ['None', 'nan', '', '-']:
                                     asset_val = 0
                                 elif asset_val_str.startswith('(') and asset_val_str.endswith(')'):
                                     # Convert (14.8) to -14.8
                                     clean_part = asset_val_str[1:-1]
                                     if re.match(r'^\d+\.?\d*$', clean_part):
                                         asset_val = -float(clean_part)
                                     else:
                                         continue
                                 else:
                                     if re.match(r'^-?\d+$', asset_val_str):
                                         asset_val = int(asset_val_str)
                                     elif re.match(r'^-?\d+\.\d+$', asset_val_str):
                                         asset_val = float(asset_val_str)
                                     else:
                                         continue
                                 
                                 # Skip rows where both values are zero (likely empty/invalid rows)
                                 if rider_val == 0 and asset_val == 0:
                                     print(f"[DEBUG] Skipped: both values are zero")
                                     continue
                                 
                                 parsed_data.append({
                                     'Liability': rider_val,
                                     'Asset': asset_val
                                 })
                                 print(f"[DEBUG] Parsed: Liability={rider_val}, Asset={asset_val}")
                                 
                             except (ValueError, IndexError) as e:
                                 print(f"[DEBUG] Error parsing row {i}: {e}")
                                 continue
                         else:
                             print(f"[DEBUG] Skipped: insufficient columns (need {max(rider_col_idx, asset_col_idx) + 1}, got {len(parts)})")
                 else:
                     print("[DEBUG] No valid header found with 'Rider' and 'Asset' columns in Document Intelligence output (BLUE table)")
                     print(f"[DEBUG] Header line found: {header_line}")
                     print(f"[DEBUG] Rider column index: {rider_col_idx}")
                     print(f"[DEBUG] Asset column index: {asset_col_idx}")
                 
                 if parsed_data:
                     docint_df = pd.DataFrame(parsed_data)
                     print(f"[DEBUG] Successfully parsed Document Intelligence DataFrame: {docint_df.shape}")
                     print(f"[DEBUG] Document Intelligence columns: {list(docint_df.columns)}")
                     print(f"[DEBUG] First few rows of Document Intelligence data:")
                     print(docint_df.head())
                 else:
                     print("[DEBUG] No valid data parsed from Document Intelligence table_text")
                 
             except Exception as e:
                 print(f"[ERROR] Could not parse Document Intelligence table_text as DataFrame: {e}")
                 print(f"[DEBUG] Table text format: {table_text[:200]}...")

        state["msg_outputs"] = {
            "success": True,
            "table_type": table_type,
            "highlight_output": highlight_path,
            "table_output": table_path,
            "docint_df": docint_df
        }
        return state 