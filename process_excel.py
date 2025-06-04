import pandas as pd
from openai import OpenAI
import os
from pathlib import Path
import json
import re

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_title_info(df):
    """Extract PRODUCT_TYPE and VALUATION_DATE from the title row."""
    # Assume the title is in the first cell of the first row
    title_row = str(df.iloc[0, 0])
    product_type = re.match(r"^(\w+)", title_row).group(1)
    date_match = re.search(r"as of (\d{2}/\d{2}/\d{4})", title_row)
    if date_match:
        date_str = date_match.group(1)
        valuation_date = pd.to_datetime(date_str, format="%m/%d/%Y").strftime("%Y%m%d")
    else:
        valuation_date = ""
    return product_type, valuation_date

def read_excel_file(input_path):
    """Read the Excel file and return a pandas DataFrame."""
    try:
        df = pd.read_excel(input_path, header=None)
        return df
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

def process_data_with_llm(df, product_type, valuation_date):
    """Process the data using OpenAI's API to transform it into the desired format."""
    # Convert DataFrame to string representation (skip the title row)
    data_str = df.iloc[1:].to_string(index=False, header=False)
    
    # Create a prompt for the LLM
    prompt = f"""
Given the following Excel data:
{data_str}

PRODUCT_TYPE for this data is: {product_type}
VALUATION_DATE for this data is: {valuation_date}

TASK: Extract a table with these columns:
- VALUATION_DATE (use the provided value above)
- PRODUCT_TYPE (use the provided value above)
- RISK_TYPE (the section name, e.g., 'Credit', 'Equity', etc.)
- GREEK_TYPE (the row label under the section, e.g., 'ILP_Update')
- RIDER_VALUE (the value from the 'Liability' column for that row)
- ASSET_VALUE (the value from the 'Asset' column for that row)

RULES:
- For rows under a section (e.g., under 'Total Credit'), RISK_TYPE is the section name, GREEK_TYPE is the row label (e.g., 'ILP_Update').
- Only use a row label as RISK_TYPE if it is a standalone bolded row not under any section.
- Extract RIDER_VALUE and ASSET_VALUE directly from the data. Do not make up values.
- Output a JSON array of objects, one per row, with the above columns.

EXAMPLE OUTPUT:
[
  {{
    "VALUATION_DATE": "20240801",
    "PRODUCT_TYPE": "DBIB",
    "RISK_TYPE": "Credit",
    "GREEK_TYPE": "ILP_Update",
    "RIDER_VALUE": 123.45,
    "ASSET_VALUE": 67.89
  }}
]

IMPORTANT: Return ONLY the JSON array, no explanations or additional text.
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
    
    # Extract PRODUCT_TYPE and VALUATION_DATE
    product_type, valuation_date = extract_title_info(df)
    print(f"Extracted PRODUCT_TYPE: {product_type}, VALUATION_DATE: {valuation_date}")
    
    # Process the data using LLM
    processed_df = process_data_with_llm(df, product_type, valuation_date)
    if processed_df is None:
        return
    
    # Save the processed data to Excel
    save_to_excel(processed_df, output_path)

if __name__ == "__main__":
    main() 