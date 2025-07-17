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
                
                if table_type == "red" or table_type == "blue":
                    # Unified header detection for both table types
                    parsed_data = []
                    header_line = None
                    rider_col_idx = None
                    asset_col_idx = None
                    header_pattern = re.compile(r"\b(rider|liability)\b", re.IGNORECASE)
                    asset_pattern = re.compile(r"\basset\b", re.IGNORECASE)
                    for i, line in enumerate(non_empty_lines):
                        parts = line.split()
                        # For blue table, skip 'Rider' between 'VA' and 'WB' or 'DBIB'
                        skip_rider = False
                        if table_type == "blue":
                            for j, part in enumerate(parts):
                                # Check for 'Rider' between 'VA' and 'WB' or 'DBIB'
                                if part.lower() in ["rider", "liability"]:
                                    if (
                                        j > 0 and parts[j-1].lower() == "va" and
                                        j+1 < len(parts) and parts[j+1].lower() in ["wb", "dbib"]
                                    ):
                                        # Skip this 'Rider'/'Liability'
                                        continue
                                    elif rider_col_idx is None:
                                        rider_col_idx = j
                                if asset_col_idx is None and part.lower() == "asset":
                                    asset_col_idx = j
                        else:
                            # Red table: use previous logic
                            for j, part in enumerate(parts):
                                if rider_col_idx is None and header_pattern.fullmatch(part):
                                    rider_col_idx = j
                                if asset_col_idx is None and asset_pattern.fullmatch(part):
                                    asset_col_idx = j
                        if rider_col_idx is not None and asset_col_idx is not None:
                            header_line = i
                            print(f"[DEBUG] Header line parts: {parts}")
                            print(f"[DEBUG] Found blue/red table header at line {header_line}")
                            print(f"[DEBUG] Rider/Liability column index: {rider_col_idx}, Asset column index: {asset_col_idx}")
                            break
                    # Fallback to known structure if not found
                    if rider_col_idx is None or asset_col_idx is None:
                        print("[DEBUG] Could not find column indices automatically, using known structure")
                        if table_type == "blue":
                            rider_col_idx = 3
                            asset_col_idx = 4
                        else:
                            rider_col_idx = 1
                            asset_col_idx = 2
                        print(f"[DEBUG] Using default indices: Rider/Liability={rider_col_idx}, Asset={asset_col_idx}")
                    if header_line is not None and rider_col_idx is not None and asset_col_idx is not None:
                        # Step 3: Extract data rows after header, skipping "Total" rows (except "HY Total")
                        data_rows = []
                        for line in non_empty_lines[header_line + 1:]:
                            if 'Total' in line and 'HY Total' not in line:
                                continue
                            data_rows.append(line)
                        print(f"[DEBUG] Document Intelligence parsing rows ({table_type.upper()} table):")
                        for i, line in enumerate(data_rows):
                            print(f"[DEBUG] Row {i}: {line}")
                            parts = line.split()
                            if len(parts) > max(rider_col_idx, asset_col_idx):
                                try:
                                    rider_val_str = parts[rider_col_idx]
                                    asset_val_str = parts[asset_col_idx]
                                    print(f"[DEBUG] Raw values: rider='{rider_val_str}', asset='{asset_val_str}'")
                                    # Parse Rider/Liability value
                                    if rider_val_str in ['None', 'nan', '', '-']:
                                        rider_val = 0.0
                                        print(f"[DEBUG] Rider parsed as 0.0 (None/nan/empty)")
                                    elif rider_val_str.startswith('(') and rider_val_str.endswith(')'):
                                        clean_part = rider_val_str[1:-1]
                                        if re.match(r'^\d+\.?\d*$', clean_part):
                                            rider_val = -float(clean_part)
                                            print(f"[DEBUG] Rider parsed as {rider_val} (parentheses)")
                                        else:
                                            print(f"[DEBUG] Rider skipped: invalid parentheses format '{clean_part}'")
                                            continue
                                    else:
                                        # Clean OCR artifacts and handle various formats
                                        clean_rider = re.sub(r'0\n:unselected:', '0', rider_val_str)
                                        print(f"[DEBUG] Cleaned rider: '{clean_rider}'")
                                        if re.match(r'^-?\d+\.?\d*$', clean_rider):
                                            rider_val = float(clean_rider)
                                            print(f"[DEBUG] Rider parsed as {rider_val} (numeric)")
                                        else:
                                            print(f"[DEBUG] Rider skipped: not numeric '{clean_rider}'")
                                            continue
                                    # Parse Asset value
                                    if asset_val_str in ['None', 'nan', '', '-']:
                                        asset_val = 0.0
                                        print(f"[DEBUG] Asset parsed as 0.0 (None/nan/empty)")
                                    elif asset_val_str.startswith('(') and asset_val_str.endswith(')'):
                                        clean_part = asset_val_str[1:-1]
                                        if re.match(r'^\d+\.?\d*$', clean_part):
                                            asset_val = -float(clean_part)
                                            print(f"[DEBUG] Asset parsed as {asset_val} (parentheses)")
                                        else:
                                            print(f"[DEBUG] Asset skipped: invalid parentheses format '{clean_part}'")
                                            continue
                                    else:
                                        # Clean OCR artifacts and handle various formats
                                        clean_asset = re.sub(r'0\n:unselected:', '0', asset_val_str)
                                        print(f"[DEBUG] Cleaned asset: '{clean_asset}'")
                                        if re.match(r'^-?\d+\.?\d*$', clean_asset):
                                            asset_val = float(clean_asset)
                                            print(f"[DEBUG] Asset parsed as {asset_val} (numeric)")
                                        else:
                                            print(f"[DEBUG] Asset skipped: not numeric '{clean_asset}'")
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
                        print(f"[DEBUG] No valid header found with 'Rider'/'Liability' and 'Asset' columns in Document Intelligence output ({table_type.upper()} table)")
                        print(f"[DEBUG] Header line found: {header_line}")
                        print(f"[DEBUG] Rider/Liability column index: {rider_col_idx}")
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