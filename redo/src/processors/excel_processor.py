import pandas as pd
import re
from datetime import datetime

class ExcelProcessor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None

    def load_sheet(self, sheet_name):
        """Load a specific sheet from the Excel file."""
        self.df = pd.read_excel(self.file_path, sheet_name=sheet_name)

    def wb_dbib_clean_df(self):
        """Clean DataFrame for WB and DBIB sheets."""
        df_clean = self.df.dropna(how="all")
        df_clean = df_clean.dropna(how="all", axis=1)
        # Skip rows where the first column starts with 'Total'
        first_col = df_clean.columns[0]
        mask = ~df_clean[first_col].str.match(r"^Total", na=False)
        df_clean = df_clean[mask].reset_index(drop=True)
        return df_clean
    
    def av_clean_df(self):
        """Clean DataFrame for AV sheets."""
        df_clean = self.df.dropna(how="all")
        df_clean = df_clean.dropna(how="all", axis=1)
        # Check if the first row's first column starts with "Account value allocations"
        first_col = df_clean.columns[0]
        if df_clean.iloc[0][first_col].strip().startswith("Account value allocations"):
            df_clean = df_clean.iloc[1:].reset_index(drop=True)
        return df_clean

    def wb_dbib_extract_product_and_date_from_anywhere(self, df_clean):
        """Extract product type and valuation date from anywhere in the DataFrame."""
        # Flatten the DataFrame to a list of strings
        for row in df_clean.itertuples(index=False):
            for cell in row:
                if isinstance(cell, str) and "Total Dynamic Hedge" in cell and "as of" in cell:
                    title_text = cell
                    # Extract valuation date
                    date_match = re.search(r"as of (\d{2}/\d{2}/\d{4})", title_text)
                    if date_match:
                        raw_date = date_match.group(1)
                        valuation_date = datetime.strptime(raw_date, "%m/%d/%Y").strftime("%Y%m%d")
                    else:
                        valuation_date = ""
                    # Extract product type (e.g., WB, DBIB, etc.)
                    product_match = re.search(r"([A-Z]+) Total Dynamic Hedge", title_text)
                    product_type = product_match.group(1) if product_match else ""
                    return product_type, valuation_date
        # If not found, return empty strings
        return "", ""

    def wb_dbib_structure_final_df(self, df_clean, valuation_date, product_type):
        """Structure the final DataFrame for WB and DBIB sheets."""
        # 1. Drop the first row (title row)
        df_struct = df_clean.iloc[1:].reset_index(drop=True)
        # 2. Add VALUATION_DATE and PRODUCT_TYPE columns
        df_struct.insert(0, "VALUATION_DATE", valuation_date)
        df_struct.insert(1, "PRODUCT_TYPE", product_type)
        # 3. Set the new header (the next row, which contains the actual column names)
        df_struct.columns = ["VALUATION_DATE", "PRODUCT_TYPE"] + list(df_struct.iloc[0, 2:])
        df_struct = df_struct.iloc[1:].reset_index(drop=True)
        # 4. Drop unwanted columns
        cols_to_drop = [col for col in df_struct.columns if col.strip() in ["Daily Net", "QTD Net", "YTD Net"]]
        df_struct = df_struct.drop(columns=cols_to_drop)
        # 5. Standardize the VA Rider column name
        for col in df_struct.columns:
            if col.startswith("VA Rider"):
                df_struct = df_struct.rename(columns={col: "Risk Type & Greeks"})
                break
        # 6. Keep only the columns you want
        keep_cols = ["VALUATION_DATE", "PRODUCT_TYPE", "Risk Type & Greeks", "Liability", "Asset"]
        df_struct = df_struct[keep_cols]
        return df_struct

    def get_cleaned_sheet(self, sheet_name):
        """Get cleaned and structured sheet data."""
        self.load_sheet(sheet_name)
        if sheet_name in ["WB", "DBIB"]:
            df_clean = self.wb_dbib_clean_df()
            product_type, valuation_date = self.wb_dbib_extract_product_and_date_from_anywhere(df_clean)
            df_struct = self.wb_dbib_structure_final_df(df_clean, valuation_date, product_type)
            return df_struct
        elif sheet_name == "AV":
            return self.av_clean_df()
        else:
            raise ValueError(f"Unknown sheet: {sheet_name}") 