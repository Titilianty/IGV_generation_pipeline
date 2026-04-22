#!/bin/bash
set -euo pipefail

# Base folder in Colab
BASE_DIR="/content/public_vcfs"

# Input VCF
input_vcf="${BASE_DIR}/demo_called_from_bam.withID.vcf"

# Folder where ID lists are stored
id_list_folder="${BASE_DIR}/split_output_ids"

# Output folders
vcf_output_folder="${BASE_DIR}/filtered_vcfs"
report_output_folder="${BASE_DIR}/reports"

# Fasta reference
reference_fasta="${BASE_DIR}/GRCh38_chr17.fa"

# Track config for IGV-style report
track_config="${BASE_DIR}/track_AG.json"

# Python script for modifying report
check_column_script="${BASE_DIR}/add_check_column_tool_3.py"

# Create output directories if not exist
mkdir -p "$vcf_output_folder" "$report_output_folder"

# Check required tools
for cmd in bcftools bgzip tabix create_report python3; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: $cmd not found in PATH"
        exit 1
    fi
done

# Check required files
for f in "$input_vcf" "$reference_fasta" "$track_config" "$check_column_script"; do
    if [ ! -f "$f" ]; then
        echo "ERROR: Required file not found: $f"
        exit 1
    fi
done

# Check input VCF index only if compressed/indexed format is used
if [[ "$input_vcf" == *.vcf.gz || "$input_vcf" == *.bcf ]]; then
    if [ ! -f "${input_vcf}.tbi" ] && [ ! -f "${input_vcf}.csi" ]; then
        echo "ERROR: Input VCF index not found for $input_vcf"
        exit 1
    fi
fi

echo "Starting filtering and reporting for each ID list..."

shopt -s nullglob
id_files=("${id_list_folder}"/*.txt)

if [ ${#id_files[@]} -eq 0 ]; then
    echo "ERROR: No .txt files found in ${id_list_folder}"
    exit 1
fi

for id_file in "${id_files[@]}"; do
    base_name=$(basename "$id_file" .txt)
    echo "Processing ${base_name}..."

    # Step 1: Filter VCF by ID
    filtered_vcf_gz="${vcf_output_folder}/${base_name}.vcf.gz"
    bcftools view \
        -i "ID=@${id_file}" \
        -Oz \
        -o "$filtered_vcf_gz" \
        "$input_vcf"
    tabix -f -p vcf "$filtered_vcf_gz"
    echo "  Filtered VCF: $filtered_vcf_gz"

    # Step 2: Remove duplicate entries based on VCF ID field
    deduped_vcf="${vcf_output_folder}/${base_name}.dedup.vcf"
    (
        bcftools view -h "$filtered_vcf_gz"
        bcftools view -H "$filtered_vcf_gz" | awk '
            BEGIN { OFS="\t" }
            {
                key = $1 FS $2 FS $4 FS $5
            if (!seen[key]++) print
            }
        '
    ) > "$deduped_vcf"
    echo "  Deduplicated VCF: $deduped_vcf"

    # Step 3: Compress and index deduplicated VCF
    deduped_vcf_gz="${deduped_vcf}.gz"
    bgzip -f -c "$deduped_vcf" > "$deduped_vcf_gz"
    tabix -f -p vcf "$deduped_vcf_gz"
    echo "  Compressed and indexed: $deduped_vcf_gz"

    # Step 4: Generate IGV-style report
    report_html="${report_output_folder}/${base_name}.html"
    create_report \
      "$deduped_vcf_gz" \
      --flanking 1000 \
      --track-config "$track_config" \
      --fasta "$reference_fasta" \
      --sort STRAND \
      --window 300 \
      --info-columns TVAF TDP NVAF NDP \
      --output "$report_html"
    echo "  Generated report: $report_html"

    # Step 5: Determine chromosome range
    chr_range=$(bcftools query -f '%CHROM\n' "$deduped_vcf_gz" | sort -V | uniq)

    if [ -z "$chr_range" ]; then
        echo "  Warning: no variants found in $deduped_vcf_gz"
        final_report_html="${report_output_folder}/${base_name}_empty.html"
    else
        chr_start=$(echo "$chr_range" | head -n1)
        chr_end=$(echo "$chr_range" | tail -n1)

        chr_start_clean=${chr_start#chr}
        chr_end_clean=${chr_end#chr}

        final_report_html="${report_output_folder}/${base_name}_chr${chr_start_clean}_${chr_end_clean}.html"
    fi

    # Step 6: Add interactive Check column
    python3 "$check_column_script" -i "$report_html" -o "$final_report_html"
    echo "  Final report: $final_report_html"

    echo "Done with ${base_name}"
done

echo "All ID lists processed!"