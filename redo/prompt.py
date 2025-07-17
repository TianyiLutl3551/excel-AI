import re
import json
import pandas as pd
from openai import OpenAI
import os

def get_llm_prompt(data_str):
    """Return the LLM prompt for transforming Excel data into a structured format."""
    return f'''Given the following Excel data:
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
   - Include all rows with a label, even if the values are zero or missing, except for rows labeled "Total" or section headers.

IMPORTANT EXTRACTION INSTRUCTIONS:
- Do not guess or infer values. Only output the exact numbers shown in the table.
- If a cell is '-', output 0. If a cell is blank, output 0. Otherwise, use the exact number shown.
- Do not shift values between columns or rows!!!!!
- Rider value is always the value in the Liability column, and Asset value is always the value in the Asset column.

- DO NOT include any rows where the label is a section header or a total/subtotal row (e.g., "Total", "Total Equity", "Total Interest Rate", "Total Credit", "Sub Total", "Total P&L", etc.), or where RISK_TYPE is just the section name with no GREEK_TYPE.
  Only include rows with a specific risk/greek type (e.g., "Delta", "Gamma", "Rho", etc.), or standalone rows that are not totals.

OUTPUT CHECKLIST:
For each of the following RISK_TYPE and GREEK_TYPE pairs, you SHOULD output a row, even if RIDER_VALUE and ASSET_VALUE is 0.

- ("Interest_Rate", "Basis")
- ("Interest_Rate", "Rho")
- ("Interest_Rate", "Convexity_Residual")
- ("Equity", "Delta")
- ("Equity", "Gamma_Residual")
- ("Credit", "HY_Total")
- ("Credit", "AGG_Credit")
- ("Credit", "Agg_Risk_Free_Growth")
- ("Credit", "ILP_Update")
- ("Fund_Basis_Fund_Mapping", "")
- ("Passage_Of_Time", "")
- ("Other_Inforce", "")
- ("New_Business", "")
- ("Cross_Impact_True_up", "")

FLEXIBLE OUTPUT:
If the data contains additional RISK_TYPE and GREEK_TYPE pairs not listed above, you MUST also include them in the output, using the same format.

DO NOT merge RISK_TYPE and GREEK_TYPE into a single field.
If a pair above is not found, output it with zeros.
If a new pair is found in the data, include it as-is.

IMPORTANT:
- Always output the pairs if they are shown up in the table which may be covered in the checklist above, even if the values are zero or missing.
- Also output any additional RISK_TYPE/GREEK_TYPE pairs found in the data.
- Do not merge RISK_TYPE and GREEK_TYPE into a single field.
- Return ONLY the JSON array, no explanations or additional text.
- Do not output any pairs that are not shown up in the table.
- Do not round up the values, use the exact values shown up in the table.

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
''' 