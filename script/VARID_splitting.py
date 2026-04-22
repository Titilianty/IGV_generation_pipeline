# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 10:14:53 2025

@author: Tiimbang(應婷婷)
"""

import pandas as pd
import re
import os

path = "/content/public_vcfs"
os.chdir(path)

# Load the Excel file
input_file = "VARID_splitting.xlsx"
sheet_name = 0  # If multiple sheets, specify by name or index

# Output settings
output_prefix = "split_output_ids"

# Helper function to sort chromosomes naturally
def chr_sort_key(chr_name):
    match = re.match(r'chr(\d+|X|Y|M)', str(chr_name))
    if match:
        val = match.group(1)
        if val == 'X':
            return 23
        elif val == 'Y':
            return 24
        elif val == 'M':
            return 25
        else:
            return int(val)
    else:
        return 1000  # Unknown chromosomes at end

# Read the Excel sheet
df = pd.read_excel(input_file, sheet_name=sheet_name)

# Check and show columns
print("Columns in file:", df.columns.tolist())

# Sort by chromosome and position
df['chr_sort'] = df['chr'].apply(chr_sort_key)
df = df.sort_values(by=['chr_sort', 'chr', 'pos']).drop(columns=['chr_sort'])

# Splitting
chunk = []
chunk_num = 1
row_count = 0

# Create output directory
os.makedirs(output_prefix, exist_ok=True)

current_chr = None

for idx, row in df.iterrows():
    chr_now = row['chr']

    # Save chunk if changing chromosome and already collected >= 50 rows
    if chr_now != current_chr and row_count >= 100:
        # Save only the 'VCF_ID' column
        out_file = os.path.join(output_prefix, f"{output_prefix}_part{chunk_num}.txt")
        pd.DataFrame(chunk)['VCF_ID'].to_csv(out_file, index=False, header=False)
        print(f"Saved {out_file}")
        chunk = []
        chunk_num += 1
        row_count = 0

    chunk.append(row)
    current_chr = chr_now
    row_count += 1

# Save last chunk
if chunk:
    out_file = os.path.join(output_prefix, f"{output_prefix}_part{chunk_num}.txt")
    pd.DataFrame(chunk)['VCF_ID'].to_csv(out_file, index=False, header=False)
    print(f"Saved {out_file}")
