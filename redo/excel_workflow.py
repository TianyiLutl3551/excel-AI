import os
import json
import toml
import re
import pandas as pd
from openai import OpenAI
from excel_processor import ExcelProcessor
from excel_prompts import get_llm_prompt

class ExcelWorkflowNode:
    def __init__(self, config_path="/Users/lutianyi/Desktop/excel AI/redo/config.json", secrets_path="/Users/lutianyi/Desktop/excel AI/redo/secrets.toml"):
        # Load configuration
        with open(config_path, "r") as f:
            self.config = json.load(f)
        
        # Load secrets
        self.secrets = toml.load(secrets_path)
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.secrets["openai"]["api_key"])
        self.model = self.secrets["openai"]["model"]
        
        # Get settings from config
        self.default_sheets = self.config.get("default_sheets", ["WB", "DBIB"])
        self.output_dir = self.config.get("output_dir", "redo/output")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

    def process_with_llm(self, df):
        """Process DataFrame with LLM using the same logic as llm_api.py."""
        data_str = df.to_string()
        prompt = get_llm_prompt(data_str)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data analysis expert that helps transform and organize Excel data. Always return valid JSON arrays."},
                    {"role": "user", "content": prompt}
                ]
            )
            transformed_data = response.choices[0].message.content.strip()
            json_match = re.search(r'(\[.*?\])', transformed_data, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                print("No JSON array found in LLM response.")
                return None
            data = json.loads(json_str)
            if not isinstance(data, list):
                raise ValueError("LLM response is not a JSON array")
            df_llm = pd.DataFrame(data)
            # --- POST-PROCESSING FILTER ---
            # Remove rows where RISK_TYPE or label contains 'Total' (except 'HY_Total')
            def is_valid_row(row):
                for col in row.index:
                    val = str(row[col]).lower()
                    if 'total' in val and 'hy_total' not in val:
                        return False
                return True
            if 'RISK_TYPE' in df_llm.columns:
                mask = df_llm['RISK_TYPE'].apply(lambda x: ('total' not in str(x).lower()) or ('hy_total' in str(x).lower()))
                df_llm = df_llm[mask]
            else:
                df_llm = df_llm[df_llm.apply(is_valid_row, axis=1)]
            return df_llm.reset_index(drop=True)
        except Exception as e:
            print(f"Error processing data with LLM: {e}")
            return None

    def __call__(self, state: dict) -> dict:
        """Main node function that processes Excel files with LLM."""
        file_path = state["file_path"]
        
        # Initialize processor for this file
        processor = ExcelProcessor(file_path)
        
        all_llm_results = []
        processed_sheets = []
        
        # Process each sheet
        for sheet in self.default_sheets:
            try:
                print(f"Processing sheet: {sheet}")
                
                # Get cleaned and structured data
                cleaned_df = processor.get_cleaned_sheet(sheet)
                if cleaned_df is not None and not cleaned_df.empty:
                    # Process with LLM
                    llm_result = self.process_with_llm(cleaned_df)
                    if llm_result is not None:
                        all_llm_results.append(llm_result)
                        processed_sheets.append(sheet)
                        print(f"Successfully processed {sheet}")
                    else:
                        print(f"No LLM result for sheet {sheet}")
                else:
                    print(f"No cleaned data for sheet {sheet}")
                    
            except Exception as e:
                print(f"Error processing sheet {sheet}: {e}")
        
        # Create combined output if we have results
        if all_llm_results:
            combined = pd.concat(all_llm_results, ignore_index=True)
            base_filename = os.path.basename(file_path).replace('.xlsx', '').replace('.xls', '')
            combined_filename = f"combined_llm_output_{base_filename}.csv"
            combined_path = os.path.join(self.output_dir, combined_filename)
            combined.to_csv(combined_path, index=False)
            print(f"Combined LLM output saved to {combined_path}")
            
            # Update state with results
            state["excel_outputs"] = {
                "combined_output": combined_path,
                "success": True,
                "processed_sheets": processed_sheets
            }
        else:
            print("No LLM results to save.")
            state["excel_outputs"] = {
                "combined_output": None,
                "success": False,
                "processed_sheets": []
            }
        
        return state 