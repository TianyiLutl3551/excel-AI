#!/usr/bin/env python3
"""
Concatenation utility for highlights data.
Concatenates all highlights CSV files in the output directory and sorts by date.
"""

import os
import pandas as pd
import glob
from config_manager import ConfigManager

def concatenate_highlights():
    """
    Concatenate all highlights CSV files into a single file, sorted by date.
    """
    # Load configuration
    config_manager = ConfigManager()
    output_dir = config_manager.get_output_dir()
    output_file = "combined_all_highlights.csv"
    
    print("🔄 Starting highlights CSV concatenation process...")
    print("=" * 60)
    
    # Step 1: Discover highlights CSV files
    csv_pattern = os.path.join(output_dir, "highlights_*.csv")
    highlights_files = glob.glob(csv_pattern)
    
    if not highlights_files:
        print("❌ No highlights CSV files found in output directory!")
        return
    
    print(f"📁 Found {len(highlights_files)} highlights CSV files:")
    for file in sorted(highlights_files):
        print(f"  - {os.path.basename(file)}")
    print()
    
    # Step 2: Read and concatenate highlights CSV files
    dataframes = []
    file_stats = []
    
    for file_path in sorted(highlights_files):
        try:
            print(f"📖 Reading: {os.path.basename(file_path)}")
            df = pd.read_csv(file_path)
            
            # Show the columns for the first file to understand structure
            if not dataframes:
                print(f"   📋 Columns found: {list(df.columns)}")
            
            # Validate expected columns (flexible structure)
            if 'Date' not in df.columns:
                print(f"⚠️  Warning: {os.path.basename(file_path)} missing 'Date' column: {list(df.columns)}")
            
            # Add source file information for tracking
            df['SOURCE_FILE'] = os.path.basename(file_path)
            
            dataframes.append(df)
            
            # Get date range info
            if 'Date' in df.columns:
                date_range = f"{df['Date'].min()} - {df['Date'].max()}"
            else:
                date_range = "No Date column"
            
            file_stats.append({
                'file': os.path.basename(file_path),
                'rows': len(df),
                'date_range': date_range
            })
            
            print(f"   ✅ Loaded {len(df)} rows")
            
        except Exception as e:
            print(f"❌ Error reading {os.path.basename(file_path)}: {e}")
            continue
    
    if not dataframes:
        print("❌ No valid highlights CSV files could be loaded!")
        return
    
    print()
    
    # Step 3: Concatenate all dataframes (preserving row order within each file)
    print("🔗 Concatenating all highlights...")
    combined_df = pd.concat(dataframes, ignore_index=True)
    print(f"   ✅ Combined dataset has {len(combined_df)} total rows")
    
    # Step 4: Sort by Date
    if 'Date' in combined_df.columns:
        print("📅 Sorting by Date...")
        # Convert to numeric for proper sorting (in case it's stored as string)
        combined_df['Date'] = pd.to_numeric(combined_df['Date'], errors='coerce')
        combined_df = combined_df.sort_values('Date')
        combined_df = combined_df.reset_index(drop=True)
        print(f"   ✅ Sorted by date range: {combined_df['Date'].min()} - {combined_df['Date'].max()}")
    else:
        print("⚠️  Date column not found - skipping date sorting")
    
    # Step 5: Save the combined file
    output_path = os.path.join(output_dir, output_file)
    print(f"💾 Saving combined highlights to: {output_path}")
    combined_df.to_csv(output_path, index=False)
    
    # Step 6: Display summary statistics
    print()
    print("📊 Highlights Summary Statistics:")
    print("=" * 60)
    print(f"Total files processed: {len(dataframes)}")
    print(f"Total rows: {len(combined_df)}")
    
    if 'Date' in combined_df.columns:
        print(f"Date range: {combined_df['Date'].min()} - {combined_df['Date'].max()}")
        print(f"Unique dates: {combined_df['Date'].nunique()}")
    
    # Show column structure
    print(f"Columns: {list(combined_df.columns)}")
    
    # Show highlights content summary
    if 'Daily Highlights' in combined_df.columns:
        non_empty_daily = combined_df[combined_df['Daily Highlights'].notna() & 
                                     (combined_df['Daily Highlights'].str.strip() != '')].shape[0]
        print(f"Non-empty Daily Highlights: {non_empty_daily}")
    
    if 'QTD Highlights' in combined_df.columns:
        non_empty_qtd = combined_df[combined_df['QTD Highlights'].notna() & 
                                   (combined_df['QTD Highlights'].str.strip() != '')].shape[0]
        print(f"Non-empty QTD Highlights: {non_empty_qtd}")
    
    print()
    print("📋 File breakdown:")
    for stat in file_stats:
        print(f"  {stat['file']}: {stat['rows']} rows, dates {stat['date_range']}")
    
    print()
    print(f"✅ Successfully created: {output_path}")
    print("🎉 Highlights concatenation completed!")

if __name__ == "__main__":
    concatenate_highlights() 