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
        highlight_path = os.path.join(self.output_dir, f"highlights_{date_str}.csv")
        highlights_df.to_csv(highlight_path, index=False)
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

    def _parse_numeric_value(self, value_str):
        """Parse a numeric value from string, handling parentheses, OCR artifacts, etc."""
        if value_str in ['None', 'nan', '', '-', 'None']:
            return 0.0
        
        # Clean OCR artifacts
        clean_value = re.sub(r'0\n:unselected:', '0', str(value_str))
        clean_value = clean_value.strip()
        
        # Handle parentheses (negative values)
        if clean_value.startswith('(') and clean_value.endswith(')'):
            inner_value = clean_value[1:-1]
            if re.match(r'^\d+\.?\d*$', inner_value):
                return -float(inner_value)
            else:
                return None
        
        # Handle regular numeric values
        if re.match(r'^-?\d+\.?\d*$', clean_value):
            return float(clean_value)
        
        return None

    def _find_numeric_columns_in_row(self, row_parts, min_cols=2):
        """Find numeric columns in a row, returning their indices and values."""
        numeric_data = []
        for i, part in enumerate(row_parts):
            parsed_val = self._parse_numeric_value(part)
            if parsed_val is not None:
                numeric_data.append((i, parsed_val))
        return numeric_data

    def _parse_table_text_robust(self, table_text, table_type):
        """
        Robust parsing of Document Intelligence table text for both RED and BLUE tables.
        Uses position-based analysis rather than word-based splitting.
        """
        print(f"[DEBUG] Starting robust parsing for {table_type.upper()} table")
        
        lines = table_text.strip().split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Step 1: Find header line
        header_line_idx = None
        for i, line in enumerate(non_empty_lines):
            line_lower = line.lower()
            if ('liability' in line_lower and 'asset' in line_lower) or \
               ('rider' in line_lower and 'asset' in line_lower):
                header_line_idx = i
                print(f"[DEBUG] Found header line at index {i}: {line}")
                break
        
        if header_line_idx is None:
            print("[DEBUG] No header line found, using fallback method")
            return self._parse_table_text_fallback(non_empty_lines, table_type)
        
        # Step 2: Analyze header structure to determine column positions
        header_line = non_empty_lines[header_line_idx]
        header_parts = header_line.split()
        print(f"[DEBUG] Header parts: {header_parts}")
        
        # Find Liability/Rider and Asset column indices in header
        liability_col_idx = None
        asset_col_idx = None
        
        for i, part in enumerate(header_parts):
            part_lower = part.lower()
            if part_lower in ['liability', 'rider'] and liability_col_idx is None:
                # For BLUE tables, skip "Rider" if it's between "VA" and product name
                if table_type == "blue" and part_lower == "rider":
                    if (i > 0 and header_parts[i-1].lower() == "va" and
                        i+1 < len(header_parts) and header_parts[i+1].lower() in ["wb", "dbib"]):
                        continue  # Skip this rider
                liability_col_idx = i
            elif part_lower == 'asset' and asset_col_idx is None:
                asset_col_idx = i
        
        print(f"[DEBUG] Header analysis: Liability/Rider col={liability_col_idx}, Asset col={asset_col_idx}")
        
        # Step 3: Process data rows using robust numeric detection
        data_rows = []
        for line in non_empty_lines[header_line_idx + 1:]:
            # Skip total rows (except HY Total)
            if 'Total' in line and 'HY Total' not in line:
                continue
            # Skip empty rows and section headers
            if not line.strip() or ('BOP' in line or 'EoP' in line):
                continue
            # Skip rows that contain only None values
            if line.strip() and all(part.lower() in ['none', 'nan', '', '-'] for part in line.split() if part.strip()):
                continue
            data_rows.append(line)
        
        parsed_data = []
        print(f"[DEBUG] Processing {len(data_rows)} data rows:")
        
        for i, line in enumerate(data_rows):
            print(f"[DEBUG] Row {i}: {line}")
            
            # Skip rows with only None values
            if 'None' in line and line.count('None') >= 2:
                print(f"[DEBUG] Skipped row {i}: contains only None values")
                continue
            
            # Use smarter column detection that aligns with LLM logic
            liability_val, asset_val = self._extract_liability_asset_smart(line, table_type)
            
            if liability_val is not None and asset_val is not None:
                parsed_data.append({
                    'Liability': liability_val,
                    'Asset': asset_val
                })
                print(f"[DEBUG] Parsed: Liability={liability_val}, Asset={asset_val}")
            else:
                print(f"[DEBUG] Skipped row {i}: could not extract valid liability/asset values")
        
        if parsed_data:
            docint_df = pd.DataFrame(parsed_data)
            print(f"[DEBUG] Successfully parsed Document Intelligence DataFrame: {docint_df.shape}")
            print(f"[DEBUG] Document Intelligence columns: {list(docint_df.columns)}")
            print(f"[DEBUG] First few rows of Document Intelligence data:")
            print(docint_df.head())
            return docint_df
        else:
            print("[DEBUG] No valid data parsed from Document Intelligence table_text")
            return None
    
    def _extract_liability_asset_smart(self, line, table_type):
        """
        Smart extraction that tries to match LLM logic for liability/asset detection.
        """
        # Clean the line and split
        row_parts = line.split()
        
        # Find all numeric values in the row
        numeric_data = self._find_numeric_columns_in_row(row_parts)
        
        if len(numeric_data) < 2:
            return None, None
        
        if table_type == "red":
            # RED tables: Use pattern matching similar to LLM
            # Look for the pattern: Label... Liability Asset Net MTD QTD
            # The LLM correctly identifies liability and asset columns
            
            # Handle special OCR cases
            if '0\\n:unselected:' in line:
                # Find liability (first numeric), treat OCR artifact as 0 for asset
                liability_val = numeric_data[0][1]
                # Look for the next valid numeric after the OCR artifact
                clean_line = line.replace('0\\n:unselected:', '0')
                clean_parts = clean_line.split()
                clean_numeric = self._find_numeric_columns_in_row(clean_parts)
                
                # The pattern is usually: liability, ocr_artifact(=0), next_value, next_value...
                # The LLM treats ocr_artifact as asset=0
                asset_val = 0.0
                return liability_val, asset_val
            else:
                # Normal case: first two numeric values
                return numeric_data[0][1], numeric_data[1][1]
                
        elif table_type == "blue":
            # BLUE tables: More complex, need to find the right liability/asset columns
            # Based on debug output, the pattern is different
            
            # For BLUE tables, we need to be smarter about column selection
            # The structure is typically: Label Liability Asset Daily MTD QTD
            # But labels can be multi-word
            
            # Use position-based detection similar to what worked in debug
            if len(numeric_data) >= 2:
                # Take first two significant numeric values
                return numeric_data[0][1], numeric_data[1][1]
        
        return None, None



    def _parse_table_text_fallback(self, non_empty_lines, table_type):
        """Fallback parsing method when header detection fails."""
        print(f"[DEBUG] Using fallback parsing for {table_type.upper()} table")
        
        parsed_data = []
        for i, line in enumerate(non_empty_lines):
            # Skip obvious header and section lines
            if any(keyword in line.lower() for keyword in ['liability', 'asset', 'bop', 'eop', 'total dynamic']):
                continue
            
            # Skip total rows (except HY Total)
            if 'Total' in line and 'HY Total' not in line:
                continue
            
            row_parts = line.split()
            numeric_data = self._find_numeric_columns_in_row(row_parts)
            
            if len(numeric_data) >= 2:
                liability_val = numeric_data[0][1]
                asset_val = numeric_data[1][1]
                
                parsed_data.append({
                    'Liability': liability_val,
                    'Asset': asset_val
                })
                print(f"[DEBUG] Fallback - Row {i}: Liability={liability_val}, Asset={asset_val}")
        
        if parsed_data:
            return pd.DataFrame(parsed_data)
        else:
            return None

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
        # Extract date from filename for context
        filename = os.path.basename(file_path)
        date_match = re.search(r'(\d{4})[_-](\d{1,2})[_-](\d{1,2})', filename)
        extracted_date = None
        if date_match:
            year, month, day = date_match.groups()
            extracted_date = f"{year}{month.zfill(2)}{day.zfill(2)}"
        
        # Use the correct prompt logic
        if table_type == "blue":
            prompt = get_blue_llm_prompt(table_text, extracted_date)
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
        table_path = os.path.join(self.output_dir, f"table_{base_name}.csv")
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
            df.to_csv(table_path, index=False)
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
                docint_df = self._parse_table_text_robust(table_text, table_type)
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