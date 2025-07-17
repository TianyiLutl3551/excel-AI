#!/usr/bin/env python3
"""
Direct test of validation logic with known data from the problematic file
"""

import pandas as pd
import hashlib

def hash_columns(df, columns):
    # Format numbers consistently with 6 decimal places
    def format_value(x):
        if isinstance(x, (int, float)):
            # Normalize negative zero to positive zero
            if x == 0:
                x = 0.0
            return f"{x:.6f}"
        return str(x)
    
    concat_str = df[columns].apply(lambda row: ','.join(format_value(x) for x in row), axis=1).str.cat(sep='|')
    return hashlib.sha256(concat_str.encode('utf-8')).hexdigest(), concat_str

def test_validation():
    """Test validation with the actual data from the problematic file"""
    
    print("🔍 TESTING VALIDATION WITH ACTUAL DATA")
    print("=" * 80)
    
    # Document Intelligence parsed data (from debug output)
    # This is what the Document Intelligence should have parsed with correct column indices
    docint_data = [
        {'Liability': -15.7, 'Asset': 16.1},  # Equity Delta
        {'Liability': -0.0, 'Asset': 0.0},    # Equity Gamma & Residual
        {'Liability': 31.2, 'Asset': -30.8},  # Interest Rate Rho
        {'Liability': -0.6, 'Asset': -0.1},   # Interest Rate Convexity & Residual
        {'Liability': 0.0, 'Asset': 1.1},     # Interest Rate Basis
        {'Liability': -0.2, 'Asset': 0.3},    # HY Total
        {'Liability': 0.0, 'Asset': 0.0},     # AGG Credit
        {'Liability': -0.1, 'Asset': 0.0},    # Agg Risk Free Growth
        {'Liability': 0.0, 'Asset': 0.0},     # ILP Update
        {'Liability': -4.0, 'Asset': 0.6},    # Fund Basis & Fund Mapping
        {'Liability': -0.1, 'Asset': 0.1},    # Passage of Time
        {'Liability': -0.6, 'Asset': 0.0},    # Other Inforce
        {'Liability': -0.0, 'Asset': 0.0},    # New Business
        {'Liability': 0.3, 'Asset': 0.0}      # Cross Impact, True-up
    ]
    
    # LLM output data (from debug output)
    llm_data = [
        {'RIDER_VALUE': -15.7, 'ASSET_VALUE': 16.1},  # Equity Delta
        {'RIDER_VALUE': 0.0, 'ASSET_VALUE': 0.0},     # Equity Gamma_Residual
        {'RIDER_VALUE': 31.2, 'ASSET_VALUE': -30.8},  # Interest_Rate Rho
        {'RIDER_VALUE': -0.6, 'ASSET_VALUE': -0.1},   # Interest_Rate Convexity_Residual
        {'RIDER_VALUE': 0.0, 'ASSET_VALUE': 1.1},     # Interest_Rate Basis
        {'RIDER_VALUE': -0.2, 'ASSET_VALUE': 0.3},    # Credit HY_Total
        {'RIDER_VALUE': 0.0, 'ASSET_VALUE': 0.0},     # Credit AGG_Credit
        {'RIDER_VALUE': -0.1, 'ASSET_VALUE': 0.0},    # Credit Agg_Risk_Free_Growth
        {'RIDER_VALUE': 0.0, 'ASSET_VALUE': 0.0},     # Credit ILP_Update
        {'RIDER_VALUE': -4.0, 'ASSET_VALUE': 0.6},    # Fund_Basis_Fund_Mapping
        {'RIDER_VALUE': -0.1, 'ASSET_VALUE': 0.1},    # Passage_Of_Time
        {'RIDER_VALUE': -0.6, 'ASSET_VALUE': 0.0},    # Other_Inforce
        {'RIDER_VALUE': -0.0, 'ASSET_VALUE': 0.0},    # New_Business
        {'RIDER_VALUE': 0.3, 'ASSET_VALUE': 0.0}      # Cross_Impact_True_up
    ]
    
    # Create DataFrames
    docint_df = pd.DataFrame(docint_data)
    llm_df = pd.DataFrame(llm_data)
    
    print("📋 Document Intelligence Data:")
    print(docint_df)
    print(f"Total rows: {len(docint_df)}")
    
    print("\n📋 LLM Output Data:")
    print(llm_df)
    print(f"Total rows: {len(llm_df)}")
    
    # Hash the data
    hash1, concat1 = hash_columns(docint_df, ["Liability", "Asset"])
    hash2, concat2 = hash_columns(llm_df, ["RIDER_VALUE", "ASSET_VALUE"])
    
    print("\n🔍 VALIDATION RESULTS:")
    print("=" * 80)
    print(f"Hash 1 (Document Intelligence): {hash1}")
    print(f"Hash 2 (LLM): {hash2}")
    print(f"Match: {hash1 == hash2}")
    
    print(f"\n📝 Document Intelligence concatenated string (first 200 chars):")
    print(f"'{concat1[:200]}...'")
    print(f"\n📝 LLM concatenated string (first 200 chars):")
    print(f"'{concat2[:200]}...'")
    
    # Show the actual values being compared
    print("\n📊 VALUE COMPARISON:")
    print("=" * 80)
    for i in range(min(len(docint_df), len(llm_df))):
        docint_row = docint_df.iloc[i]
        llm_row = llm_df.iloc[i]
        print(f"Row {i}: DI({docint_row['Liability']}, {docint_row['Asset']}) vs LLM({llm_row['RIDER_VALUE']}, {llm_row['ASSET_VALUE']})")

if __name__ == "__main__":
    test_validation() 