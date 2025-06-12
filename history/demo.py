import os
import pandas as pd

folder_path = "/Users/lutianyi/Desktop/excel AI/input"

for file in os.listdir(folder_path):
    if file.endswith(".xlsx"):
        full_path = os.path.join(folder_path, file)
        # Extract from each file
        df = pd.read_excel(full_path, sheet_name=None)  # Reads all sheets
        # Send to LLM or custom extraction logic
