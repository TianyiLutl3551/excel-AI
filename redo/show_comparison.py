#!/usr/bin/env python3
"""
Show exact comparison between LLM output and Document Intelligence DataFrame
"""
import pandas as pd
import hashlib

def hash_columns(df, columns):
    """Same hash function as in validation node"""
    concat_str = df[columns].apply(lambda row: ','.join(f"{x:.6f}" for x in row), axis=1).str.cat(sep='|')
    return hashlib.sha256(concat_str.encode('utf-8')).hexdigest(), concat_str

# LLM Output values (from the debug output)
llm_data = [
    (-15.7, 16.1),
    (0.0, 0.0),
    (31.2, -30.8),
    (-0.6, -0.1),
    (0.0, 1.1),
    (-0.2, 0.3),
    (0.0, 0.0),
    (-0.1, 0.0),
    (0.0, 0.0),
    (-4.0, 0.6),
    (-0.1, 0.1),
    (-0.6, 0.0),
    (0.0, 0.0),
    (0.3, 0.0)
]

# Document Intelligence values (from the debug output)
docint_data = [
    (16.1, 0.4),
    (31.2, -30.8),
    (0.0, 1.1),
    (0.3, 0.1),
    (0.0, -0.1),
    (-0.1, 0.1),
    (0.0, -0.6),
    (0.3, 0.0)
]

print("🔍 Exact Comparison")
print("=" * 60)

# Create DataFrames
llm_df = pd.DataFrame(llm_data, columns=['RIDER_VALUE', 'ASSET_VALUE'])
docint_df = pd.DataFrame(docint_data, columns=['Liability', 'Asset'])

print("📊 LLM Output DataFrame:")
print(llm_df)
print(f"Shape: {llm_df.shape}")

print("\n📊 Document Intelligence DataFrame:")
print(docint_df)
print(f"Shape: {docint_df.shape}")

# Calculate hashes
llm_hash, llm_concat = hash_columns(llm_df, ['RIDER_VALUE', 'ASSET_VALUE'])
docint_hash, docint_concat = hash_columns(docint_df, ['Liability', 'Asset'])

print(f"\n🔍 LLM hash: {llm_hash}")
print(f"🔍 Document Intelligence hash: {docint_hash}")
print(f"Match: {llm_hash == docint_hash}")

print(f"\n🔍 LLM concatenated values:")
print(llm_concat)

print(f"\n🔍 Document Intelligence concatenated values:")
print(docint_concat)

# Show the differences
print(f"\n🔍 Differences:")
print(f"LLM rows: {len(llm_df)}")
print(f"Document Intelligence rows: {len(docint_df)}")

if len(llm_df) != len(docint_df):
    print(f"❌ Row count mismatch: LLM has {len(llm_df)} rows, Document Intelligence has {len(docint_df)} rows")

# Compare first few rows
min_rows = min(len(llm_df), len(docint_df))
print(f"\n🔍 Comparing first {min_rows} rows:")
for i in range(min_rows):
    llm_row = llm_df.iloc[i]
    docint_row = docint_df.iloc[i]
    print(f"Row {i}: LLM({llm_row['RIDER_VALUE']}, {llm_row['ASSET_VALUE']}) vs DocInt({docint_row['Liability']}, {docint_row['Asset']})") 