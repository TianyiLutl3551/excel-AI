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
   - If a value is "-", treat it as 0.
   - Do NOT use values from the "Daily Net" or "QTD Net" columns for "RIDER_VALUE" or "ASSET_VALUE".
   - Only use the value under the "Asset" column for "ASSET_VALUE".

MANDATORY OUTPUT CHECKLIST:
For each of the following RISK_TYPE and GREEK_TYPE pairs, you MUST output a row, even if the value is missing or zero. If a row is not present in the data, output it with RIDER_VALUE and ASSET_VALUE as 0.

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
- Always output all pairs in the checklist above, even if the values are zero or missing.
- Also output any additional RISK_TYPE/GREEK_TYPE pairs found in the data.
- Do not merge RISK_TYPE and GREEK_TYPE into a single field.
- Return ONLY the JSON array, no explanations or additional text.

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