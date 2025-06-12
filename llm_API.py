import toml
import re
import json
import pandas as pd
from openai import OpenAI
from prompt import get_llm_prompt

# Load secrets from secrets.toml
config = toml.load("secrets.toml")
api_key = config["openai"]["api_key"]
model = config["openai"]["model"]

client = OpenAI(api_key=api_key)

def process_with_llm(df):
    data_str = df.to_string()
    prompt = get_llm_prompt(data_str)
    try:
        response = client.chat.completions.create(
            model=model,
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
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error processing data with LLM: {e}")
        return None 