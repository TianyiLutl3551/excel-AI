import pandas as pd
import hashlib
import time
import os
from datetime import datetime

class ValidationNode:
    def __init__(self, log_path="output/validation_log.txt"):
        self.log_path = log_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def hash_columns(self, df, columns):
        # Format numbers consistently with 6 decimal places
        def format_value(x):
            if isinstance(x, (int, float)):
                # Normalize all zero values to 0.0
                if x == 0 or x == 0.0 or x == -0.0:
                    x = 0.0
                return f"{x:.6f}"
            return str(x)
        
        concat_str = df[columns].apply(lambda row: ','.join(format_value(x) for x in row), axis=1).str.cat(sep='|')
        return hashlib.sha256(concat_str.encode('utf-8')).hexdigest(), concat_str

    def log_validation_result(self, file_name, match):
        """Log process date/time, file name, and whether correct or wrong"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "correct" if match else "wrong"
        with open(self.log_path, 'a') as f:
            f.write(f"[{timestamp}] {file_name} | {status}\n")

    def __call__(self, state: dict) -> dict:
        start_time = time.time()
        file_type = state.get("file_type", "unknown")
        file_name = os.path.basename(state.get("file_path", ""))
        print(f"[DEBUG] Validation node called for file type: {file_type}")
        match = None
        hash1 = hash2 = None
        concat1 = concat2 = None
        error = None
        
        try:
            if file_type in ["xlsx", "xls"]:
                print("[DEBUG] Processing Excel validation...")
                # Excel: compare original Excel and LLM output
                excel_path = state["file_path"]
                llm_output_path = state["excel_outputs"]["combined_output"]
                print(f"[DEBUG] Excel path: {excel_path}")
                print(f"[DEBUG] LLM output path: {llm_output_path}")
                
                # Read original Excel (WB+DBIB) and find the actual data columns
                df1_wb = pd.read_excel(excel_path, sheet_name="WB")
                df1_dbib = pd.read_excel(excel_path, sheet_name="DBIB")
                
                # Find the Liability and Asset columns (they should be in the header row)
                # Look for the row that contains "Liability" and "Asset"
                liability_col = None
                asset_col = None
                
                for idx, row in df1_wb.iterrows():
                    for col_idx, value in enumerate(row):
                        if pd.notna(value):
                            value_str = str(value).strip().lower()
                            # Look for exact matches for column headers, not partial matches
                            if liability_col is None and value_str == "liability":
                                liability_col = col_idx
                            elif asset_col is None and value_str == "asset":
                                asset_col = col_idx
                    if liability_col is not None and asset_col is not None:
                        break
                
                if liability_col is None or asset_col is None:
                    error = "Could not find Liability and Asset columns"
                    print(f"[DEBUG] {error}")
                    state["validation"] = {"error": error}
                    self.log_validation_result(file_name, False)
                    return state
                
                # Extract the data rows (skip header rows)
                data_start_row = None
                for idx, row in df1_wb.iterrows():
                    if pd.notna(row.iloc[liability_col]) and pd.notna(row.iloc[asset_col]):
                        # Check if these are numeric values
                        try:
                            float(row.iloc[liability_col])
                            float(row.iloc[asset_col])
                            data_start_row = idx
                            break
                        except (ValueError, TypeError):
                            continue
                
                if data_start_row is None:
                    error = "Could not find data rows"
                    print(f"[DEBUG] {error}")
                    state["validation"] = {"error": error}
                    self.log_validation_result(file_name, False)
                    return state
                
                # Extract data from both sheets
                excel_data = []
                for sheet_name, df in [("WB", df1_wb), ("DBIB", df1_dbib)]:
                    for idx in range(data_start_row, len(df)):
                        row = df.iloc[idx]
                        
                        # Skip rows that are empty or contain only NaN values
                        if pd.isna(row.iloc[liability_col]) and pd.isna(row.iloc[asset_col]):
                            continue
                        
                        # Get the row label (first non-empty column) to check for "Total" rows
                        row_label = ""
                        for col_idx in range(len(row)):
                            if pd.notna(row.iloc[col_idx]) and str(row.iloc[col_idx]).strip():
                                row_label = str(row.iloc[col_idx]).strip()
                                break
                        
                        # Skip rows containing "Total" (unless it's "HY Total")
                        if "Total" in row_label and "HY Total" not in row_label:
                            continue
                        
                        try:
                            liability_val = float(row.iloc[liability_col]) if pd.notna(row.iloc[liability_col]) else 0
                            asset_val = float(row.iloc[asset_col]) if pd.notna(row.iloc[asset_col]) else 0
                            
                            # Round to 6 decimal places for consistency
                            liability_val = round(liability_val, 6)
                            asset_val = round(asset_val, 6)
                            
                            # Skip rows where both values are zero (likely empty/invalid rows)
                            if liability_val == 0 and asset_val == 0 and not row_label:
                                continue
                                
                            excel_data.append([liability_val, asset_val])
                        except (ValueError, TypeError):
                            continue
                
                df1 = pd.DataFrame(excel_data, columns=["Liability", "Asset"])
                
                # Read LLM output
                df2 = pd.read_csv(llm_output_path)
                
                # Extract and hash
                hash1, concat1 = self.hash_columns(df1, ["Liability", "Asset"])
                hash2, concat2 = self.hash_columns(df2, ["RIDER_VALUE", "ASSET_VALUE"])
                match = (hash1 == hash2)
            elif file_type == "msg":
                # MSG: compare after Document Intelligence and LLM output table
                docint_df = state.get("msg_outputs", {}).get("docint_df")
                table_path = state.get("msg_outputs", {}).get("table_output")
                if docint_df is not None and table_path:
                    df1 = docint_df
                    df2 = pd.read_csv(table_path)
                    hash1, concat1 = self.hash_columns(df1, ["Liability", "Asset"])
                    hash2, concat2 = self.hash_columns(df2, ["RIDER_VALUE", "ASSET_VALUE"])
                    match = (hash1 == hash2)
                else:
                    error = "Missing Document Intelligence data or table output"
                    print(f"[DEBUG] {error}")
                    state["validation"] = {"error": error}
                    self.log_validation_result(file_name, False)
                    return state
        except Exception as e:
            error = str(e)
            print(f"[DEBUG] Validation error: {error}")
            state["validation"] = {"error": error}
            self.log_validation_result(file_name, False)
            return state
        process_time = time.time() - start_time
        state["validation"] = {
            "match": match,
            "hash1": hash1,
            "hash2": hash2,
            "concat1": concat1,
            "concat2": concat2,
            "process_time": process_time
        }
        # Log every result as correct or wrong
        self.log_validation_result(file_name, match)
        return state 