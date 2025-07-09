def get_llm_prompt2(data_str):
    return f'''Given the following table image data:
{data_str}

TASK: Extract and transform the WB Total Dynamic Hedge P&L table into a structured JSON array.

OUTPUT FORMAT:
Return a JSON array of objects with these columns:
- VALUATION_DATE (YYYYMMDD format, from the date in the table title)
- PRODUCT_TYPE (e.g., "WB", from the first word in the title)
- RISK_TYPE (e.g., "Equity", "Rates", "Credit", "Underlying_Fund", "Theta_Carry", "Other_Unhedged", "Fees", "ILP", "New_Business", "Claims", "Model_Change")
- GREEK_TYPE (e.g., "Delta", "Gamma", "Volatility", "Dynamic_Rho", "Credit", "ILP"; blank if not applicable)
- RIDER_VALUE (value from the Liability column)
- ASSET_VALUE (value from the Asset column)

DATA EXTRACTION RULES:

1. Title Row Processing:
   - Extract PRODUCT_TYPE from the first word in the title (e.g., "WB").
   - Extract VALUATION_DATE from the date in the title (e.g., "as of 05/01/2024" → "20240501").

2. Row Processing:
   - For each row with a label (not a section header or total row), extract the label, Liability, and Asset values.
   - RISK_TYPE is the main category (e.g., "Equity", "Rates", "Credit", "Underlying_Fund", "Theta_Carry", "Other_Unhedged", "Fees", "ILP", "New_Business", "Claims", "Model_Change").
   - GREEK_TYPE is the specific risk measure (e.g., "Delta", "Gamma", "Volatility", "Dynamic_Rho", "Credit", "ILP"). If not applicable, leave blank.
   - For rows like "Equity: Delta P&L", RISK_TYPE = "Equity", GREEK_TYPE = "Delta".
   - For rows like "Rate: Dynamic Rho P&L", RISK_TYPE = "Rates", GREEK_TYPE = "Dynamic_Rho".
   - For rows like "Credit: Credit P&L", RISK_TYPE = "Credit", GREEK_TYPE = "Credit".
   - For rows like "Underlying Fund P&L", RISK_TYPE = "Underlying_Fund", GREEK_TYPE = "".
   - For rows like "Theta / Carry P&L", RISK_TYPE = "Theta_Carry", GREEK_TYPE = "".
   - For rows like "Other Unhedged P&L", RISK_TYPE = "Other_Unhedged", GREEK_TYPE = "".
   - For rows like "Fees", "Claims", "ILP", "New Business", "Model Change", use the row label as RISK_TYPE and leave GREEK_TYPE blank.

3. Text Normalization:
   - Replace spaces and slashes with underscores in RISK_TYPE and GREEK_TYPE.
   - Remove special characters (except underscores).
   - Maintain capitalization as in the table.
   - Example: "Theta / Carry P&L" → RISK_TYPE: "Theta_Carry"
   - Example: "Dynamic Rho" → GREEK_TYPE: "Dynamic_Rho"

4. Value Extraction:
   - RIDER_VALUE = value from the Liability column (column 0).
   - ASSET_VALUE = value from the Asset column (column 1).
   - If a cell is '-', 'None', or blank, output 0. Otherwise, use the exact number shown.
   - Only extract rows with a label (skip section headers like "BOP Market Value", "EoP Market Value", and total rows like "Sub Total P&L (IFRS)", "Total P&L").

IMPORTANT:
- Do not guess or infer values. Only output the exact numbers shown in the table.
- Do not shift values between columns or rows.
- Return ONLY the JSON array, no explanations or additional text.
- Do not merge RISK_TYPE and GREEK_TYPE into a single field.
- Output all rows with a label, even if the values are zero or missing.
- Handle negative values correctly.
- Extract the actual date from the table title, not use a hardcoded date.

EXAMPLE OUTPUT FORMAT:
[
    {{
        "VALUATION_DATE": "20240501",
        "PRODUCT_TYPE": "WB",
        "RISK_TYPE": "Equity",
        "GREEK_TYPE": "Delta",
        "RIDER_VALUE": -14,
        "ASSET_VALUE": 14
    }},
    {{
        "VALUATION_DATE": "20240501",
        "PRODUCT_TYPE": "WB",
        "RISK_TYPE": "Equity",
        "GREEK_TYPE": "Gamma",
        "RIDER_VALUE": 0,
        "ASSET_VALUE": 0
    }}
]

Return ONLY the JSON array, no other text or explanations.
''' 