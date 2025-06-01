#!/usr/bin/env python3
"""
RCSD Policy Compliance Analyzer - Main Entry Point
Processes PDF files to extract policies and analyze compliance
"""

import argparse
import os
import sys

from pdf_parser import PDFPolicyParser


def main():
    parser = argparse.ArgumentParser(
        description="RCSD Policy Compliance Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all policies from PDFs
  python main.py --extract
  
  # Extract from specific PDF
  python main.py --extract --pdf "policies/RCSD Policies 1000.pdf"
  
  # Analyze extracted policies (future feature)
  python main.py --analyze
        """,
    )

    parser.add_argument(
        "--extract", action="store_true", help="Extract policies from PDF files"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        help="Specific PDF file to process (default: all PDFs in policies/)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/extracted",
        help="Output directory for extracted policies",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze extracted policies for compliance (not yet implemented)",
    )

    args = parser.parse_args()

    if not any([args.extract, args.analyze]):
        parser.print_help()
        return 1

    if args.extract:
        pdf_parser = PDFPolicyParser()

        if args.pdf:
            # Process single PDF
            if not os.path.exists(args.pdf):
                print(f"Error: PDF file not found: {args.pdf}")
                return 1
            print(f"Extracting policies from: {args.pdf}")
            pdf_parser.parse_pdf(args.pdf, args.output_dir)
        else:
            # Process all PDFs in policies directory
            pdf_dir = "policies"
            if not os.path.exists(pdf_dir):
                print(f"Error: Policies directory not found: {pdf_dir}")
                return 1

            pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
            if not pdf_files:
                print(f"No PDF files found in {pdf_dir}")
                return 1

            print(f"Found {len(pdf_files)} PDF files to process")
            for pdf_file in sorted(pdf_files):
                pdf_path = os.path.join(pdf_dir, pdf_file)
                print(f"\nProcessing: {pdf_file}")
                pdf_parser.parse_pdf(pdf_path, args.output_dir)

    if args.analyze:
        print("Policy analysis feature not yet implemented")
        print("This will analyze extracted policies for:")
        print("  - Compliance with CA Ed Code requirements")
        print("  - Cross-reference validation")
        print("  - Policy gaps and recommendations")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
