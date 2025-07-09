import pandas as pd
import hashlib
import time
import os

class ValidationNode:
    def __init__(self, log_path="/Users/lutianyi/Desktop/excel AI/redo/output/validation_log.txt"):
        self.log_path = log_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def hash_columns(self, df, columns):
        # Preserve original data types - don't force float formatting
        concat_str = df[columns].apply(lambda row: ','.join(str(x) for x in row), axis=1).str.cat(sep='|')
        return hashlib.sha256(concat_str.encode('utf-8')).hexdigest(), concat_str

    def log_unmatch(self, file_name, process_time):
        with open(self.log_path, 'a') as f:
            f.write(f"{file_name}, {process_time:.2f} seconds\n")

    def __call__(self, state: dict) -> dict:
        start_time = time.time()
        file_type = state.get("file_type", "unknown")
        file_name = os.path.basename(state.get("file_path", ""))
        match = None
        hash1 = hash2 = None
        concat1 = concat2 = None
        try:
            if file_type in ["xlsx", "xls"]:
                # Excel: compare original Excel and LLM output
                excel_path = state["file_path"]
                llm_output_path = state["excel_outputs"]["combined_output"]
                # Read original Excel (WB+DBIB)
                df1 = pd.concat([
                    pd.read_excel(excel_path, sheet_name=sheet) for sheet in ["WB", "DBIB"]
                ], ignore_index=True)
                # Read LLM output
                df2 = pd.read_csv(llm_output_path)
                # Extract and hash
                hash1, concat1 = self.hash_columns(df1, ["Liability", "Asset"])
                hash2, concat2 = self.hash_columns(df2, ["RIDER_VALUE", "ASSET_VALUE"])
                print("\n[VALIDATION] Excel original data (Liability, Asset):\n", df1[["Liability", "Asset"]].head())
                print("[VALIDATION] LLM output data (RIDER_VALUE, ASSET_VALUE):\n", df2[["RIDER_VALUE", "ASSET_VALUE"]].head())
                print(f"[VALIDATION] Excel hash: {hash1}")
                print(f"[VALIDATION] LLM output hash: {hash2}")
                match = (hash1 == hash2)
            elif file_type == "msg":
                # MSG: compare after Document Intelligence and LLM output table
                docint_df = state.get("msg_outputs", {}).get("docint_df")
                table_path = state.get("msg_outputs", {}).get("table_output")
                if docint_df is not None and table_path:
                    df1 = docint_df
                    df2 = pd.read_excel(table_path)
                    # You may need to adjust column names here
                    hash1, concat1 = self.hash_columns(df1, ["Liability", "Asset"])
                    hash2, concat2 = self.hash_columns(df2, ["RIDER_VALUE", "ASSET_VALUE"])
                    print("\n[VALIDATION] Document Intelligence data:")
                    print(df1.values.tolist())
                    print("[VALIDATION] LLM output data:")
                    print(df2[["RIDER_VALUE", "ASSET_VALUE"]].values.tolist())
                    print(f"[VALIDATION] Document Intelligence hash: {hash1}")
                    print(f"[VALIDATION] LLM output hash: {hash2}")
                    match = (hash1 == hash2)
        except Exception as e:
            state["validation"] = {"error": str(e)}
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
        if match is False:
            self.log_unmatch(file_name, process_time)
        return state 