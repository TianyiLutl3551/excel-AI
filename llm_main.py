from llm_data import LLMData
from llm_API import process_with_llm
import os
import pandas as pd

class LLMOrchestrator:
    def __init__(self, file_path, output_dir="output"):
        self.file_path = file_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.llm_data = LLMData(file_path)

    def process_sheets(self, sheet_names):
        all_llm_results = []
        for sheet in sheet_names:
            try:
                cleaned_df = self.llm_data.get_cleaned_sheet(sheet)
                if cleaned_df is not None:
                    llm_result = process_with_llm(cleaned_df)
                    if llm_result is not None:
                        all_llm_results.append(llm_result)
                        llm_result.to_csv(os.path.join(self.output_dir, f"{sheet}_llm_output.csv"), index=False)
            except Exception as e:
                print(f"Error processing sheet {sheet}: {e}")
        if all_llm_results:
            combined = pd.concat(all_llm_results, ignore_index=True)
            combined.to_csv(os.path.join(self.output_dir, "combined_llm_output_classed.csv"), index=False)
            print("Combined LLM output saved to output/combined_llm_output_classed.csv")
        else:
            print("No LLM results to save.")

if __name__ == "__main__":
    file_path = "/Users/lutianyi/Desktop/excel AI/input/AVsample.xlsx"
    sheet_names = ["WB", "DBIB"]
    orchestrator = LLMOrchestrator(file_path)
    orchestrator.process_sheets(sheet_names) 