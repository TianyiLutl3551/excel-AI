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

Please analyze this data and transform it into a structured format that:
1. Groups related data together
2. Identifies patterns and relationships
3. Organizes the information in a clear, logical way

Return ONLY the transformed data as a JSON array of objects, with each object representing a row. Do not include any explanation or markdown formatting."""

    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a data analysis expert that helps transform and organize Excel data."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the transformed data from the response
        transformed_data = response.choices[0].message.content.strip()
        
        # Parse the JSON response
        data = json.loads(transformed_data)
        return pd.DataFrame(data)
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