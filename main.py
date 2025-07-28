#!/usr/bin/env python3
"""
Main script for Task 1A - PDF Structure Extraction
Processes all PDFs from /app/input and generates JSON outputs in /app/output
"""

import os
import sys
import json
from pathlib import Path

# Import your PDF extractor class
from pdf_extractor import extract_pdf_structure

def main():
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if input directory exists
    if not input_dir.exists():
        print(f"Input directory {input_dir} does not exist")
        sys.exit(1)
    
    # Find all PDF files in input directory
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in input directory")
        sys.exit(1)
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF file
    for pdf_file in pdf_files:
        try:
            print(f"Processing: {pdf_file.name}")
            
            # Extract structure using your function
            result = extract_pdf_structure(str(pdf_file))
            
            # Create output filename (replace .pdf with .json)
            output_filename = pdf_file.stem + ".json"
            output_path = output_dir / output_filename
            
            # Write result to JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"Generated: {output_filename}")
            
        except Exception as e:
            print(f"Error processing {pdf_file.name}: {str(e)}")
            # Create error output
            error_result = {
                "title": "Error extracting title",
                "outline": []
            }
            output_filename = pdf_file.stem + ".json"
            output_path = output_dir / output_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(error_result, f, indent=2)
    
    print("Processing complete!")

if __name__ == "__main__":
    main()