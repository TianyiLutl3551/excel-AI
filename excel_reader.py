import pandas as pd
import re

class ExcelReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.expected_headers = ["Liability", "Asset", "Daily Net", "QTD Net", "YTD Net"]

    def extract_table(self):
        # Read the whole sheet as raw data (no header)
        df_raw = pd.read_excel(self.file_path, header=None, dtype=str)
        df_raw = df_raw.fillna("")

        # 1. Find header row
        header_row_idx = None
        for i, row in df_raw.iterrows():
            row_values = [str(cell).strip() for cell in row]
            if all(h in row_values for h in self.expected_headers):
                header_row_idx = i
                break
        if header_row_idx is None:
            raise ValueError("Could not find header row with expected headers.")

        # 2. Extract table data below header
        df_table = pd.read_excel(self.file_path, header=header_row_idx, dtype=str)
        df_table = df_table.fillna("")

        # 3. Remove rows that are completely empty or have no useful data in the "Label" column
        first_col = df_table.columns[0]
        df_table = df_table.rename(columns={first_col: "Label"})
        df_table = df_table[df_table["Label"].str.strip() != ""]
        df_table = df_table.dropna(how="all")  # Drop rows where all columns are empty

        # 4. Infer PRODUCT_TYPE and VALUATION_DATE from top 10 rows
        df_raw_top = df_raw.head(10)
        top_text = " ".join(" ".join(map(str, df_raw_top.iloc[i].values)) for i in range(len(df_raw_top)))
        m = re.search(r"VA Rider (\w+)", top_text)
        product_type = m.group(1) if m else ""
        m = re.search(r"as of (\d{2}/\d{2}/\d{4})", top_text)
        if m:
            date_str = m.group(1)
            valuation_date = pd.to_datetime(date_str, format="%m/%d/%Y").strftime("%Y%m%d")
        else:
            valuation_date = ""

        df_table["PRODUCT_TYPE"] = product_type
        df_table["VALUATION_DATE"] = valuation_date

        # 5. Clean up whitespace
        df_table = df_table.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        # 6. Drop the "Label" column if you don't want it
        df_table = df_table.drop(columns=["Label"])

        return df_table

if __name__ == "__main__":
    file_path = "input/SampleInput20240801.xlsx"
    output_path = "output/cleaned_table.csv"
    reader = ExcelReader(file_path)
    df = reader.extract_table()
    print(df)
    df.to_csv(output_path, index=False)
    print(f"Saved cleaned table to {output_path}")
