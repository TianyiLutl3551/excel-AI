import pandas as pd
from openai import OpenAI
import os
from pathlib import Path
import json
import re

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def read_excel_file(input_path):
    """Read the Excel file and return a pandas DataFrame."""
    try:
        df = pd.read_excel(input_path)
        return df
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

def read_excel_sheets(input_path, sheet_names):
    """Read specified sheets from the Excel file and return a dict of DataFrames."""
    try:
        dfs = pd.read_excel(input_path, sheet_name=sheet_names)
        return dfs
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

def process_data_with_llm(df):
    """Process the data using OpenAI's API to transform it into the desired format."""
    # Convert DataFrame to string representation
    data_str = df.to_string()
    
    # Create a prompt for the LLM
    prompt = f"""Given the following Excel data:
{data_str}

TASK: Transform this DBIB Total Dynamic Hedge P&L Excel data into a structured format.

OUTPUT FORMAT:
Return a JSON array of objects with these columns:
- VALUATION_DATE (YYYYMMDD format)
- PRODUCT_TYPE (e.g., \"DBIB\")
- RISK_TYPE (categorized risk)
- GREEK_TYPE (specific risk measure)
- RIDER_VALUE (from Liability column)
- ASSET_VALUE (from Asset column)

DATA EXTRACTION RULES:

1. Title Row Processing:
   - Extract PRODUCT_TYPE from first word (e.g., \"DBIB\")
   - Extract VALUATION_DATE from \"as of MM/DD/YYYY\" and convert to YYYYMMDD

2. Section Processing:
   Main sections to identify:
   - Total Equity
   - Total Interest Rate
   - Total Credit
   - Standalone sections (e.g., Fund Basis & Fund Mapping, Passage of Time)

3. Risk Type Classification:
   For rows under sections:
   - RISK_TYPE = section name (e.g., \"Equity\", \"Interest_Rate\", \"Credit\")
   - GREEK_TYPE = specific measure (e.g., \"Delta\", \"Rho\", \"Gamma_Residual\")
   
   For standalone rows:
   - RISK_TYPE = full row name (e.g., \"FundBasis_Mapping\", \"Passage_Of_Time\")
   - GREEK_TYPE = null or empty

4. Text Normalization Rules:
   - Replace spaces with underscores
   - Replace & with underscore
   - Remove duplicate underscores
   - Maintain proper capitalization
   - Example: \"Interest Rate & Basis\" → \"Interest_Rate_Basis\"

5. Value Extraction:
   - RIDER_VALUE = value from Liability column
   - ASSET_VALUE = value from Asset column
   - Skip Daily Net, QTD Net, YTD Net columns
   - Skip summary/total rows
   - Include all rows with a label, even if the values are zero or missing, except for rows labeled \"Total\" or section headers.

MANDATORY OUTPUT CHECKLIST:
For each of the following RISK_TYPE and GREEK_TYPE pairs, you MUST output a row, even if the value is missing or zero. If a row is not present in the data, output it with RIDER_VALUE and ASSET_VALUE as 0.

- (\"Interest_Rate\", \"Basis\")
- (\"Interest_Rate\", \"Rho\")
- (\"Interest_Rate\", \"Convexity_Residual\")
- (\"Equity\", \"Delta\")
- (\"Equity\", \"Gamma_Residual\")
- (\"Credit\", \"HY_Total\")
- (\"Credit\", \"AGG_Credit\")
- (\"Credit\", \"Agg_Risk_Free_Growth\")
- (\"Credit\", \"ILP_Update\")
- (\"Fund_Basis_Fund_Mapping\", \"\")
- (\"Passage_Of_Time\", \"\")
- (\"Other_Inforce\", \"\")
- (\"New_Business\", \"\")
- (\"Cross_Impact_True_up\", \"\")

FLEXIBLE OUTPUT:
If the data contains additional RISK_TYPE and GREEK_TYPE pairs not listed above, you MUST also include them in the output, using the same format.

DO NOT merge RISK_TYPE and GREEK_TYPE into a single field.
If a pair above is not found, output it with zeros.
If a new pair is found in the data, include it as-is.

IMPORTANT:
- Always output all pairs in the checklist above, even if the values are zero or missing.
- Also output any additional RISK_TYPE/GREEK_TYPE pairs found in the data.
- Do not merge RISK_TYPE and GREEK_TYPE into a single field.
- Return ONLY the JSON array, no explanations or additional text.

EXAMPLE OUTPUT FORMAT:
[
    {{
        \"VALUATION_DATE\": \"20240801\",
        \"PRODUCT_TYPE\": \"DBIB\",
        \"RISK_TYPE\": \"Equity\",
        \"GREEK_TYPE\": \"Delta\",
        \"RIDER_VALUE\": 123.45,
        \"ASSET_VALUE\": 67.89
    }},
    {{
        \"VALUATION_DATE\": \"20240801\",
        \"PRODUCT_TYPE\": \"DBIB\",
        \"RISK_TYPE\": \"Interest_Rate\",
        \"GREEK_TYPE\": \"Rho\",
        \"RIDER_VALUE\": 234.56,
        \"ASSET_VALUE\": 78.90
    }}
]
"""

    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a data analysis expert that helps transform and organize Excel data. Always return valid JSON arrays."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the transformed data from the response
        transformed_data = response.choices[0].message.content.strip()
        print("\nLLM Response:")
        print(transformed_data)
        
        # Robust JSON extraction: extract only the JSON array
        json_match = re.search(r'(\[.*?\])', transformed_data, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            print("No JSON array found in LLM response.")
            return None
        # Parse the JSON response
        try:
            data = json.loads(json_str)
            if not isinstance(data, list):
                raise ValueError("LLM response is not a JSON array")
            return pd.DataFrame(data)
        except json.JSONDecodeError as e:
            print(f"\nError parsing JSON response: {e}")
            print("Raw response:", json_str)
            return None
    except Exception as e:
        print(f"Error processing data with LLM: {e}")
        return None

def save_to_excel(df, output_path):
    """Save the processed DataFrame to an Excel file."""
    try:
        df.to_excel(output_path, index=False)
        print(f"Successfully saved processed data to {output_path}")
    except Exception as e:
        print(f"Error saving Excel file: {e}")

def main():
    input_dir = os.path.join(os.getcwd(), "input")
    output_dir = os.path.join(os.getcwd(), "output")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    sheet_names = ["WB", "DBIB"]
    for filename in os.listdir(input_dir):
        if filename.endswith(".xlsx") and not filename.startswith(".~"):  # skip temp files
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            print(f"Processing file: {filename}")
            dfs = read_excel_sheets(input_path, sheet_names)
            if dfs is None:
                print(f"Could not read sheets from {filename}")
                continue
            processed_dfs = []
            for sheet, df in dfs.items():
                if df is None or df.empty:
                    print(f"Sheet {sheet} in {filename} is empty or could not be read.")
                    continue
                print(f"  Processing sheet: {sheet}")
                processed_df = process_data_with_llm(df)
                if processed_df is not None:
                    processed_dfs.append(processed_df)
            if not processed_dfs:
                print(f"No data processed from any sheet in {filename}.")
                continue
            combined_df = pd.concat(processed_dfs, ignore_index=True)
            save_to_excel(combined_df, output_path)
            print(f"Saved combined output to {output_path}\n")

if __name__ == "__main__":
    main() 