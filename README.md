# IGV_generation_pipeline
This project uses IGV to inspect variant calls in order to determine whether a variant represents a true biological mutation or a technical sequencing artifact

# Steps to run the pipeline
1. Prepare the variant ID list
Check the number of variant IDs in the VCF file.
If the VCF contains more than 50 variants, it is recommended to split them using VARID_splitting.py.
Before running the script, modify the working directory inside the Python script.
Also update the Excel file containing the variant IDs.
The script will generate a .txt output file.

2. Modify the JSON file
This file specifies the BAM files you want to visualize in IGV.

3. Modify the .sh file
Update the following fields:
The VCF filename
The output directory paths you want to use
