#!/usr/bin/env python3
"""
CSV Table Concatenation Script
Concatenates all table CSV files in the output directory, preserves row order within each table,
and sorts the final result by VALUATION_DATE.
"""

import os
import pandas as pd
import glob
from datetime import datetime

def main():
    """Main function to concatenate all table CSV files."""
    
    # Configuration
    output_dir = "output"
    output_file = "combined_all_tables.csv"
    
    print("🔄 Starting CSV concatenation process...")
    print("=" * 60)
    
    # Step 1: Discover CSV files (exclude highlights)
    csv_pattern = os.path.join(output_dir, "*.csv")
    all_csv_files = glob.glob(csv_pattern)
    
    # Filter out highlights files
    table_files = [f for f in all_csv_files if "highlights_" not in os.path.basename(f)]
    
    if not table_files:
        print("❌ No table CSV files found in output directory!")
        return
    
    print(f"📁 Found {len(table_files)} table CSV files:")
    for file in sorted(table_files):
        print(f"  - {os.path.basename(file)}")
    print()
    
    # Step 2: Read and concatenate CSV files
    dataframes = []
    file_stats = []
    
    for file_path in sorted(table_files):
        try:
            print(f"📖 Reading: {os.path.basename(file_path)}")
            df = pd.read_csv(file_path)
            
            # Validate expected columns
            expected_columns = ['VALUATION_DATE', 'PRODUCT_TYPE', 'RISK_TYPE', 'GREEK_TYPE', 'RIDER_VALUE', 'ASSET_VALUE']
            if not all(col in df.columns for col in expected_columns):
                print(f"⚠️  Warning: {os.path.basename(file_path)} has unexpected columns: {list(df.columns)}")
                print(f"   Expected: {expected_columns}")
            
            # Add source file information for tracking
            df['SOURCE_FILE'] = os.path.basename(file_path)
            
            dataframes.append(df)
            file_stats.append({
                'file': os.path.basename(file_path),
                'rows': len(df),
                'date_range': f"{df['VALUATION_DATE'].min()} - {df['VALUATION_DATE'].max()}" if 'VALUATION_DATE' in df.columns else "N/A"
            })
            
            print(f"   ✅ Loaded {len(df)} rows")
            
        except Exception as e:
            print(f"❌ Error reading {os.path.basename(file_path)}: {e}")
            continue
    
    if not dataframes:
        print("❌ No valid CSV files could be loaded!")
        return
    
    print()
    
    # Step 3: Concatenate all dataframes (preserving row order within each file)
    print("🔗 Concatenating all tables...")
    combined_df = pd.concat(dataframes, ignore_index=True)
    print(f"   ✅ Combined dataset has {len(combined_df)} total rows")
    
    # Step 4: Sort by VALUATION_DATE
    if 'VALUATION_DATE' in combined_df.columns:
        print("📅 Sorting by VALUATION_DATE...")
        # Convert to numeric for proper sorting (in case it's stored as string)
        combined_df['VALUATION_DATE'] = pd.to_numeric(combined_df['VALUATION_DATE'], errors='coerce')
        combined_df = combined_df.sort_values('VALUATION_DATE')
        combined_df = combined_df.reset_index(drop=True)
        print(f"   ✅ Sorted by date range: {combined_df['VALUATION_DATE'].min()} - {combined_df['VALUATION_DATE'].max()}")
    else:
        print("⚠️  VALUATION_DATE column not found - skipping date sorting")
    
    # Step 5: Save the combined file
    output_path = os.path.join(output_dir, output_file)
    print(f"💾 Saving combined file to: {output_path}")
    combined_df.to_csv(output_path, index=False)
    
    # Step 6: Display summary statistics
    print()
    print("📊 Summary Statistics:")
    print("=" * 60)
    print(f"Total files processed: {len(dataframes)}")
    print(f"Total rows: {len(combined_df)}")
    
    if 'VALUATION_DATE' in combined_df.columns:
        print(f"Date range: {combined_df['VALUATION_DATE'].min()} - {combined_df['VALUATION_DATE'].max()}")
        print(f"Unique dates: {combined_df['VALUATION_DATE'].nunique()}")
    
    if 'PRODUCT_TYPE' in combined_df.columns:
        print(f"Product types: {', '.join(combined_df['PRODUCT_TYPE'].unique())}")
    
    print()
    print("📋 File breakdown:")
    for stat in file_stats:
        print(f"  {stat['file']}: {stat['rows']} rows, dates {stat['date_range']}")
    
    print()
    print(f"✅ Successfully created: {output_path}")
    print("🎉 Concatenation completed!")

if __name__ == "__main__":
    main() 