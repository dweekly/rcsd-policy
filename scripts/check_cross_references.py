#!/usr/bin/env python3
"""
Check for missing cross-referenced policies with improved filtering
to avoid false positives from legal citations
"""

import os
import re
from collections import defaultdict


def find_policy_references(text):
    """Find references to other policies in text"""
    references = set()

    # First, remove common legal citation contexts to avoid false positives
    # Remove U.S.C. citations like "20 U.S.C. § 6318"
    text_cleaned = re.sub(
        r"\d+\s+U\.S\.C\.?\s*(?:§|Section)?\s*\d+", "", text, flags=re.IGNORECASE
    )
    # Remove CFR citations like "34 CFR 104.33"
    text_cleaned = re.sub(
        r"\d+\s+C\.F\.R\.?\s*(?:§|Section)?\s*\d+(?:\.\d+)*",
        "",
        text_cleaned,
        flags=re.IGNORECASE,
    )
    # Remove Ed. Code citations
    text_cleaned = re.sub(
        r"(?:Ed\.?\s*Code|Education\s+Code)\s*(?:§|Section)?\s*\d+",
        "",
        text_cleaned,
        flags=re.IGNORECASE,
    )
    # Remove state code citations like "5 CCR 3051"
    text_cleaned = re.sub(r"\d+\s+CCR\s+\d+", "", text_cleaned, flags=re.IGNORECASE)

    # Pattern 1: Explicit policy/regulation references
    # Must have "Policy", "Regulation", "AR", "BP", etc. before the number
    pattern1 = re.findall(
        r"\b(?:Policy|Regulation|Administrative\s+Regulation|Board\s+Policy|Bylaw|BP|AR|BB)\s+(\d{4}(?:\.\d+)?)\b",
        text_cleaned,
        re.IGNORECASE,
    )
    references.update(pattern1)

    # Pattern 2: References in specific contexts like "(see Policy 1234.5)"
    pattern2 = re.findall(
        r"\((?:see|refer to|pursuant to)\s+(?:Policy|Regulation|AR|BP)?\s*(\d{4}(?:\.\d+)?)\)",
        text_cleaned,
        re.IGNORECASE,
    )
    references.update(pattern2)

    # Pattern 3: Cross-reference sections often use format "1234 - Title"
    # Look for this pattern specifically in cross-reference contexts
    if "cross reference" in text.lower():
        pattern3 = re.findall(
            r"\b(\d{4}(?:\.\d+)?)\s*[-–—]\s*[A-Z]",  # noqa: RUF001
            text_cleaned,
        )
        references.update(pattern3)

    # Filter out any remaining false positives
    # Remove any 4-digit numbers that are likely years (1900-2099)
    references = {
        ref for ref in references if not (ref.isdigit() and 1900 <= int(ref) <= 2099)
    }

    # Remove any that are likely page numbers or other non-policy numbers
    references = {ref for ref in references if not (ref.isdigit() and int(ref) > 7000)}

    return references


def get_all_extracted_codes(base_dir="data/extracted"):
    """Get all policy codes that were successfully extracted"""
    extracted_codes = set()

    # Check all subdirectories
    for subdir in ["policies", "regulations", "exhibits"]:
        dir_path = os.path.join(base_dir, subdir)
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                if filename.endswith(".txt"):
                    # Extract code from filename
                    code = filename.replace(".txt", "")
                    # Handle special cases like "3320-E PDF(2)"
                    code = re.sub(r"\s+PDF\(\d+\)", "", code)
                    code = re.sub(r"-E$", "", code)
                    extracted_codes.add(code)

    return extracted_codes


def check_missing_references(base_dir="data/extracted"):
    """Check for cross-referenced policies that weren't extracted"""

    # Get all extracted codes
    extracted_codes = get_all_extracted_codes(base_dir)
    print(f"Total extracted documents: {len(extracted_codes)}")

    # Track all cross-referenced codes and where they're referenced from
    all_referenced_codes = defaultdict(list)

    # Analyze each file for cross-references
    total_files = 0
    files_with_refs = 0

    for doc_type in ["policies", "regulations", "exhibits"]:
        doc_dir = os.path.join(base_dir, doc_type)
        if not os.path.exists(doc_dir):
            continue

        for filename in os.listdir(doc_dir):
            if filename.endswith(".txt"):
                total_files += 1
                file_path = os.path.join(doc_dir, filename)
                code = filename.replace(".txt", "")
                code = re.sub(r"\s+PDF\(\d+\)", "", code)

                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Find references in the content
                refs = find_policy_references(content)

                # Remove self-references
                refs = {ref for ref in refs if ref != code and not code.startswith(ref)}

                if refs:
                    files_with_refs += 1
                    doc_type_name = doc_type[:-1]  # Remove 's'
                    for ref in refs:
                        all_referenced_codes[ref].append(f"{doc_type_name} {code}")

    print(f"\nFiles analyzed: {total_files}")
    print(f"Files with cross-references: {files_with_refs}")
    print(f"Total unique cross-referenced codes: {len(all_referenced_codes)}")

    # Find missing codes
    missing_codes = set(all_referenced_codes.keys()) - extracted_codes

    print(f"Missing cross-referenced codes: {len(missing_codes)}")

    if missing_codes:
        print("\nMissing policies/regulations:")
        print("=" * 60)

        # Group by series
        missing_by_series = defaultdict(list)
        for code in sorted(missing_codes):
            if code[0].isdigit():
                series = code[0] + "000"
                missing_by_series[series].append(code)
            else:
                missing_by_series["Other"].append(code)

        for series in sorted(missing_by_series.keys()):
            print(f"\n{series} Series:")
            for code in sorted(missing_by_series[series]):
                referrers = sorted(all_referenced_codes[code])[:3]
                more = (
                    f" and {len(all_referenced_codes[code]) - 3} others"
                    if len(all_referenced_codes[code]) > 3
                    else ""
                )
                print(f"  - {code} (referenced by: {', '.join(referrers)}{more})")

    # Show some examples to verify we're not catching legal citations
    print("\n\nSample of detected cross-references (for verification):")
    print("=" * 60)
    count = 0
    for ref, referrers in sorted(all_referenced_codes.items())[:10]:
        if ref in extracted_codes:
            status = "EXISTS"
        else:
            status = "MISSING"
        print(f"{ref} [{status}] <- referenced by {', '.join(sorted(referrers)[:2])}")
        count += 1
        if count >= 10:
            break

    # Also check for codes referenced in specific ranges that might be missing
    print("\n\nChecking for potentially missing series...")
    series_coverage = defaultdict(set)

    for code in extracted_codes:
        if re.match(r"^\d{4}", code):
            series = code[0]
            series_coverage[series].add(code)

    for series in sorted(series_coverage.keys()):
        codes = sorted(series_coverage[series])
        print(f"\n{series}000 series: {len(codes)} documents extracted")

        # Check for gaps in numbering
        numeric_codes = []
        for code in codes:
            match = re.match(r"^(\d{4})", code)
            if match:
                numeric_codes.append(int(match.group(1)))

        if numeric_codes:
            numeric_codes.sort()
            gaps = []
            for i in range(len(numeric_codes) - 1):
                if numeric_codes[i + 1] - numeric_codes[i] > 1:
                    gap_start = numeric_codes[i] + 1
                    gap_end = numeric_codes[i + 1] - 1
                    if gap_start == gap_end:
                        gaps.append(str(gap_start))
                    else:
                        gaps.append(f"{gap_start}-{gap_end}")

            if gaps and len(gaps) < 20:  # Only show if reasonable number of gaps
                print(f"  Gaps in numbering: {', '.join(gaps[:10])}")
                if len(gaps) > 10:
                    print(f"  ... and {len(gaps) - 10} more gaps")


if __name__ == "__main__":
    check_missing_references()
