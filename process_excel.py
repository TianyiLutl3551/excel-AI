import pandas as pd
from openai import OpenAI
import os
from pathlib import Path
import json

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
- PRODUCT_TYPE (e.g., "DBIB")
- RISK_TYPE (categorized risk)
- GREEK_TYPE (specific risk measure)
- RIDER_VALUE (from Liability column)
- ASSET_VALUE (from Asset column)

DATA EXTRACTION RULES:

1. Title Row Processing:
   - Extract PRODUCT_TYPE from first word (e.g., "DBIB")
   - Extract VALUATION_DATE from "as of MM/DD/YYYY" and convert to YYYYMMDD

2. Section Processing:
   Main sections to identify:
   - Total Equity
   - Total Interest Rate
   - Total Credit
   - Standalone sections (e.g., Fund Basis & Fund Mapping, Passage of Time)

3. Risk Type Classification:
   For rows under sections:
   - RISK_TYPE = section name (e.g., "Equity", "Interest_Rate", "Credit")
   - GREEK_TYPE = specific measure (e.g., "Delta", "Rho", "Gamma_Residual")
   
   For standalone rows:
   - RISK_TYPE = full row name (e.g., "FundBasis_Mapping", "Passage_Of_Time")
   - GREEK_TYPE = null or empty

4. Text Normalization Rules:
   - Replace spaces with underscores
   - Replace & with underscore
   - Remove duplicate underscores
   - Maintain proper capitalization
   - Example: "Interest Rate & Basis" → "Interest_Rate_Basis"

5. Value Extraction:
   - RIDER_VALUE = value from Liability column
   - ASSET_VALUE = value from Asset column
   - Skip Daily Net, QTD Net, YTD Net columns
   - Skip summary/total rows

EXAMPLE OUTPUT FORMAT:
[
    {{
        "VALUATION_DATE": "20240801",
        "PRODUCT_TYPE": "DBIB",
        "RISK_TYPE": "Equity",
        "GREEK_TYPE": "Delta",
        "RIDER_VALUE": 123.45,
        "ASSET_VALUE": 67.89
    }},
    {{
        "VALUATION_DATE": "20240801",
        "PRODUCT_TYPE": "DBIB",
        "RISK_TYPE": "Interest_Rate",
        "GREEK_TYPE": "Rho",
        "RIDER_VALUE": 234.56,
        "ASSET_VALUE": 78.90
    }}
]

IMPORTANT: Return ONLY the JSON array, no explanations or additional text."""

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
        
        # Parse the JSON response
        try:
            data = json.loads(transformed_data)
            if not isinstance(data, list):
                raise ValueError("LLM response is not a JSON array")
            return pd.DataFrame(data)
        except json.JSONDecodeError as e:
            print(f"\nError parsing JSON response: {e}")
            print("Raw response:", transformed_data)
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
    # Define input and output paths
    input_path = "/Users/lutianyi/Desktop/excel AI/input/SampleInput20240801.xlsx"
    output_path = "/Users/lutianyi/Desktop/excel AI/output/sampleoutput20240801.xlsx"
    
    # Create output directory if it doesn't exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Read the input Excel file
    df = read_excel_file(input_path)
    if df is None:
        return
    
    # Process the data using LLM
    processed_df = process_data_with_llm(df)
    if processed_df is None:
        return
    
    # Save the processed data to Excel
    save_to_excel(processed_df, output_path)

if __name__ == "__main__":
    main() 