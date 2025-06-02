#!/usr/bin/env python3
"""
RCSD Policy Compliance Checker v2
- Analyzes policies and regulations together as a unit
- Clearly identifies whether findings are for BP or AR
- Considers both documents when determining material compliance issues
"""

import hashlib
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class ComplianceCheckerV2:
    def __init__(
        self,
        cache_dir="data/cache",
        output_dir="data/analysis/compliance_v2",
        batch_size=20,
        max_workers=3,
    ):
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.batch_size = batch_size
        self.max_workers = max_workers

        self.cache_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

        # Create subdirectories for organization
        (self.output_dir / "material_issues").mkdir(exist_ok=True)
        (self.output_dir / "full_reports").mkdir(exist_ok=True)
        (self.output_dir / "json_data").mkdir(exist_ok=True)

        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-4-sonnet-20250514")

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = Anthropic(api_key=self.api_key)

        # Track all issues for final summary
        self.all_material_issues = []
        self.api_calls_made = 0
        self.api_calls_cached = 0

    def get_cache_key(self, code, policy_xml, regulation_xml, last_reviewed):
        """Generate cache key for API responses"""
        # Include version to invalidate cache when we fix parsing issues
        version = "v2.0"  # New version for policy+regulation analysis
        content = f"{version}:{code}:{last_reviewed}:{policy_xml}:{regulation_xml}"
        return hashlib.md5(content.encode()).hexdigest()

    def get_cached_response(self, cache_key):
        """Check if we have a cached API response"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
                # Check if cache is still valid (30 days)
                cached_date = datetime.fromisoformat(data["cached_date"])
                if (datetime.now(timezone.utc) - cached_date).days < 30:
                    self.api_calls_cached += 1
                    return data["response"]
        return None

    def save_cache(self, cache_key, response):
        """Save API response to cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        with open(cache_file, "w") as f:
            json.dump(
                {
                    "cached_date": datetime.now(timezone.utc).isoformat(),
                    "response": response,
                },
                f,
            )

    def extract_cross_references(self, file_path):
        """Extract actual cross-references from policy text"""
        cross_refs = set()

        try:
            with open(file_path) as f:
                content = f.read()

            # Extract the policy code from the filename to avoid self-references
            own_code = Path(file_path).stem

            # First, look for the structured Cross References section at the end
            cross_refs_match = re.search(
                r"Cross References\s*:?\s*\n(?:Description\s*\n)?(.*?)(?:Board Policy Manual|$)",
                content,
                re.DOTALL | re.IGNORECASE,
            )

            if cross_refs_match:
                refs_text = cross_refs_match.group(1)
                # Extract policy numbers from the Cross References section
                # Pattern matches lines that start with a dash and policy number
                policy_pattern = r"^\s*-?\s*(\d{4}(?:\.\d+)?)\s+"
                matches = re.findall(policy_pattern, refs_text, re.MULTILINE)
                cross_refs.update(matches)

            # Also check for inline references in the main text
            # Get main text (before REFERENCES section)
            main_text_match = re.search(
                r"^(.*?)(?:\n={50,}\nREFERENCES|$)", content, re.DOTALL
            )
            main_text = main_text_match.group(1) if main_text_match else content

            # More flexible patterns that catch various reference styles
            inline_patterns = [
                # Board Policy references
                r"(?:Board )?(?:Policy|BP)\s+(\d{4}(?:\.\d+)?)",
                # Administrative Regulation references
                r"(?:Administrative )?(?:Regulation|AR)\s+(\d{4}(?:\.\d+)?(?:/\d{4}(?:\.\d+)?)*)",
                # Bylaw references
                r"(?:Bylaw)\s+(\d{4}(?:\.\d+)?)",
            ]

            for pattern in inline_patterns:
                matches = re.findall(pattern, main_text, re.IGNORECASE)
                # Handle multiple references separated by slashes
                for match in matches:
                    if "/" in match:
                        # Split multiple references like "4119.12/4219.12/4319.12"
                        for ref in match.split("/"):
                            cross_refs.add(ref.strip())
                    else:
                        cross_refs.add(match)

            # Remove self-reference
            cross_refs.discard(own_code)

        except Exception as e:
            print(f"Error extracting cross-references: {e}")

        return sorted(cross_refs)

    def find_companion_document(self, code, doc_type, base_dir="data/extracted"):
        """Find the companion policy or regulation for a given code"""
        # If this is a policy, look for the regulation; if regulation, look for policy
        if doc_type == "Policy":
            companion_path = Path(base_dir) / "regulations" / f"{code}.txt"
            companion_type = "Regulation"
        else:
            companion_path = Path(base_dir) / "policies" / f"{code}.txt"
            companion_type = "Policy"

        if companion_path.exists():
            return str(companion_path), companion_type
        return None, None

    def parse_document_to_xml(self, file_path):
        """Convert policy/regulation to XML and extract metadata"""
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Extract metadata
        code_match = re.search(
            r"RCSD (?:Policy|Regulation|Bylaw)\s+(\d+(?:\.\d+)?)", content
        )
        code = code_match.group(1) if code_match else "Unknown"

        # Document type
        if "RCSD Policy" in content[:100]:
            doc_type = "Policy"
        elif "RCSD Regulation" in content[:100]:
            doc_type = "Regulation"
        elif "RCSD Bylaw" in content[:100]:
            doc_type = "Bylaw"
        else:
            doc_type = "Unknown"

        # Title
        title_match = re.search(r"Title:\s*(.+?)(?:\n|$)", content)
        title = title_match.group(1).strip() if title_match else "Unknown Title"

        # Dates
        adopted_match = re.search(
            r"Original Adopted Date:\s*(\d{1,2}/\d{1,2}/\d{2,4})", content
        )
        adopted = adopted_match.group(1) if adopted_match else None

        reviewed_match = re.search(
            r"Last Reviewed Date:\s*(\d{1,2}/\d{1,2}/\d{2,4})", content
        )
        reviewed = reviewed_match.group(1) if reviewed_match else adopted

        # Main content
        main_text_match = re.search(
            r"={50,}\n\n(.+?)(?=\n={50,}\nREFERENCES)", content, re.DOTALL
        )
        if not main_text_match:
            main_text_match = re.search(r"={50,}\n\n(.+?)$", content, re.DOTALL)
        main_text = main_text_match.group(1).strip() if main_text_match else content

        # Clean up page break artifacts and formatting issues
        main_text = re.sub(r"\nBoard Policy Manual\n.*?\n", "\n", main_text)
        main_text = re.sub(r"\nRedwood City School District\n.*?\n", "\n", main_text)
        main_text = re.sub(r"\nPolicy Reference Disclaimer:?\n", "\n", main_text)
        main_text = re.sub(
            r"\n\d+\n", "\n", main_text
        )  # Remove standalone page numbers

        # Ensure we keep the full text, not truncated
        # Only truncate for extremely long policies (>20k chars)
        if len(main_text) > 20000:
            main_text = (
                main_text[:20000] + "\n[TRUNCATED - POLICY EXCEEDS 20000 CHARACTERS]"
            )

        # Build XML
        xml = f"""<{doc_type.lower()}>
    <metadata>
        <code>{code}</code>
        <type>{doc_type}</type>
        <title>{title}</title>
        <adopted>{adopted or "Unknown"}</adopted>
        <last_reviewed>{reviewed or adopted or "Unknown"}</last_reviewed>
    </metadata>
    <content>{main_text}</content>
</{doc_type.lower()}>"""

        return xml, code, title, reviewed, doc_type

    def check_compliance_unified(
        self, code, policy_xml, regulation_xml, title, last_reviewed
    ):
        """Check compliance considering both policy and regulation together"""

        # Create combined key for caching
        cache_key = self.get_cache_key(code, policy_xml, regulation_xml, last_reviewed)

        # Check cache first
        cached_response = self.get_cached_response(cache_key)
        if cached_response:
            print(f"  Using cached response for {code}")
            return cached_response

        prompt = f"""You are reviewing a California school district's policy and regulation set for compliance.

IMPORTANT: School districts organize requirements across both Board Policy (BP) and Administrative Regulation (AR).
- Policies typically contain the "what" and "why" (board direction, rights, notifications)
- Regulations typically contain the "how" (implementation procedures)
- Consider BOTH documents together when evaluating compliance

Policy/Regulation: {code} - {title}
Last Updated: {last_reviewed}

For each compliance issue:
1. Check if the requirement is met in EITHER the policy OR regulation
2. Only flag as MATERIAL if missing from BOTH documents
3. Clearly indicate which document (BP or AR) is missing each element
4. Include confidence level and specific legal citations

<compliance_report>
    <compliance_issues>
        <issue priority="MATERIAL|MINOR" confidence="[0-100]">
            <title>[Issue Title]</title>
            <description>[Why this is required and what's missing]</description>
            <missing_from>BP|AR|BOTH</missing_from>

            <legal_basis>
                <california_code>
                    <citation>[Ed Code/Gov Code Section]</citation>
                    <text>[Relevant excerpt]</text>
                </california_code>
            </legal_basis>

            <required_language>
                <text>[Specific language that must be added]</text>
            </required_language>

            <recommended_placement>BP|AR</recommended_placement>
        </issue>
    </compliance_issues>
</compliance_report>

<board_policy>
{policy_xml if policy_xml else "<not_found/>"}
</board_policy>

<administrative_regulation>
{regulation_xml if regulation_xml else "<not_found/>"}
</administrative_regulation>"""

        print(f"  Calling API for {code} (BP+AR analysis)...")
        self.api_calls_made += 1

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )

        result = response.content[0].text

        # Cache the response
        self.save_cache(cache_key, result)

        return result

    def parse_compliance_xml(self, xml_response):
        """Parse XML response into structured data"""
        try:
            # Extract XML
            xml_match = re.search(
                r"<compliance_report>.*</compliance_report>", xml_response, re.DOTALL
            )
            if not xml_match:
                return {"error": "No XML found", "raw": xml_response}

            root = ET.fromstring(xml_match.group(0))

            issues = []
            for issue in root.findall(".//issue"):
                issue_data = {
                    "priority": issue.get("priority"),
                    "confidence": int(issue.get("confidence", 0)),
                    "title": issue.find("title").text
                    if issue.find("title") is not None
                    else "",
                    "description": issue.find("description").text
                    if issue.find("description") is not None
                    else "",
                    "missing_from": issue.find("missing_from").text
                    if issue.find("missing_from") is not None
                    else "UNKNOWN",
                    "legal_citations": [],
                    "required_language": "",
                    "recommended_placement": issue.find("recommended_placement").text
                    if issue.find("recommended_placement") is not None
                    else "",
                }

                # Legal citations
                for ca_code in issue.findall(".//california_code"):
                    citation = ca_code.find("citation")
                    text = ca_code.find("text")
                    if citation is not None:
                        issue_data["legal_citations"].append(
                            {
                                "citation": citation.text,
                                "text": text.text if text is not None else "",
                            }
                        )

                # Required language
                req_lang = issue.find(".//required_language/text")
                if req_lang is not None:
                    issue_data["required_language"] = req_lang.text

                issues.append(issue_data)

            return {"issues": issues}

        except Exception as e:
            return {"error": f"Parse error: {e!s}", "raw": xml_response}

    def save_results(self, code, policy_data, regulation_data, compliance_data):
        """Save comprehensive results in multiple formats"""

        # Determine primary document type for display
        primary_type = "BP" if policy_data else "AR"

        # Save full JSON data
        json_file = self.output_dir / "json_data" / f"{code}.json"
        with open(json_file, "w") as f:
            json.dump(
                {
                    "code": code,
                    "has_policy": policy_data is not None,
                    "has_regulation": regulation_data is not None,
                    "policy": policy_data,
                    "regulation": regulation_data,
                    "compliance": compliance_data,
                    "check_date": datetime.now(timezone.utc).isoformat(),
                },
                f,
                indent=2,
            )

        # Extract material issues
        material_issues = [
            i
            for i in compliance_data.get("issues", [])
            if i.get("priority") == "MATERIAL" and i.get("missing_from") == "BOTH"
        ]

        if material_issues:
            # Track for summary
            display_title = (policy_data or regulation_data)["title"]
            last_reviewed = (policy_data or regulation_data).get(
                "last_reviewed", "Unknown"
            )

            self.all_material_issues.append(
                {
                    "code": code,
                    "title": display_title,
                    "primary_type": primary_type,
                    "last_reviewed": last_reviewed,
                    "issues": material_issues,
                }
            )

            # Save material issues report
            material_file = self.output_dir / "material_issues" / f"{code}_material.txt"
            with open(material_file, "w") as f:
                f.write("MATERIAL COMPLIANCE ISSUES\n")
                f.write(f"{primary_type} {code}: {display_title}\n")
                f.write(f"Last Reviewed: {last_reviewed}\n")
                f.write("=" * 80 + "\n\n")

                for issue in material_issues:
                    f.write(f"{issue['title']} (Confidence: {issue['confidence']}%)\n")
                    f.write(f"Missing from: {issue['missing_from']}\n")
                    f.write(f"{issue['description']}\n\n")

                    if issue.get("legal_citations"):
                        f.write("Legal Basis:\n")
                        for cite in issue["legal_citations"]:
                            f.write(f"- {cite['citation']}: {cite['text']}\n")
                        f.write("\n")

                    if issue.get("required_language"):
                        f.write("Required Language:\n")
                        f.write(f"{issue['required_language']}\n\n")

                    if issue.get("recommended_placement"):
                        f.write(
                            f"Recommended Placement: {issue['recommended_placement']}\n\n"
                        )

                    f.write("-" * 40 + "\n\n")

    def process_policy_group(self, code):
        """Process a policy number group (both BP and AR if they exist)"""
        print(f"\nProcessing: {code}")

        # Check for both policy and regulation
        policy_path = Path("data/extracted/policies") / f"{code}.txt"
        regulation_path = Path("data/extracted/regulations") / f"{code}.txt"

        policy_xml = None
        policy_data = None
        regulation_xml = None
        regulation_data = None

        # Parse policy if exists
        if policy_path.exists():
            policy_xml, _, title, last_reviewed, _ = self.parse_document_to_xml(
                str(policy_path)
            )
            policy_data = {
                "code": code,
                "title": title,
                "type": "Policy",
                "last_reviewed": last_reviewed,
                "file_path": str(policy_path),
            }
            print(f"  Found BP {code}")

        # Parse regulation if exists
        if regulation_path.exists():
            regulation_xml, _, title, last_reviewed, _ = self.parse_document_to_xml(
                str(regulation_path)
            )
            regulation_data = {
                "code": code,
                "title": title,
                "type": "Regulation",
                "last_reviewed": last_reviewed,
                "file_path": str(regulation_path),
            }
            print(f"  Found AR {code}")

        # We need at least one document to proceed
        if not policy_xml and not regulation_xml:
            print(f"  No documents found for {code}")
            return 0

        # Use title and date from whichever document exists (prefer policy)
        title = (policy_data or regulation_data)["title"]
        last_reviewed = (policy_data or regulation_data)["last_reviewed"]

        # Check compliance considering both documents
        response = self.check_compliance_unified(
            code, policy_xml, regulation_xml, title, last_reviewed
        )

        # Parse response
        compliance_data = self.parse_compliance_xml(response)

        # Save results
        self.save_results(code, policy_data, regulation_data, compliance_data)

        # Report material issues
        material_count = len(
            [
                i
                for i in compliance_data.get("issues", [])
                if i.get("priority") == "MATERIAL" and i.get("missing_from") == "BOTH"
            ]
        )
        print(f"  Material issues found: {material_count}")

        return material_count

    def get_all_policy_codes(self):
        """Get all unique policy codes from both policies and regulations"""
        codes = set()

        # Get codes from policies
        policy_dir = Path("data/extracted/policies")
        if policy_dir.exists():
            for file in policy_dir.glob("*.txt"):
                codes.add(file.stem)

        # Get codes from regulations
        regulation_dir = Path("data/extracted/regulations")
        if regulation_dir.exists():
            for file in regulation_dir.glob("*.txt"):
                codes.add(file.stem)

        return sorted(codes)

    def get_completed_codes(self):
        """Get set of policy codes that have already been processed"""
        completed = set()
        json_dir = self.output_dir / "json_data"

        if json_dir.exists():
            for file in json_dir.glob("*.json"):
                completed.add(file.stem)

        return completed

    def generate_summary(self):
        """Generate executive summary of all findings"""
        summary_file = self.output_dir / "EXECUTIVE_SUMMARY.md"

        with open(summary_file, "w") as f:
            f.write("# RCSD Policy Compliance Check - Executive Summary (v2)\n\n")
            f.write(
                f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}\n\n"
            )
            f.write(
                "**Note**: This analysis considers Board Policies (BP) and Administrative Regulations (AR) together.\n"
            )
            f.write(
                "Only issues missing from BOTH documents are flagged as material.\n\n"
            )

            f.write("## Statistics\n\n")
            f.write(f"- Total API calls made: {self.api_calls_made}\n")
            f.write(f"- Cached responses used: {self.api_calls_cached}\n")
            f.write(
                f"- Policy groups with material issues: {len(self.all_material_issues)}\n"
            )

            total_issues = sum(len(p["issues"]) for p in self.all_material_issues)
            f.write(f"- Total material issues found: {total_issues}\n\n")

            if self.all_material_issues:
                f.write("## Policy Groups Requiring Immediate Attention\n\n")

                # Sort by number of issues
                sorted_policies = sorted(
                    self.all_material_issues,
                    key=lambda x: len(x["issues"]),
                    reverse=True,
                )

                for policy_group in sorted_policies[:20]:  # Top 20
                    code = policy_group["code"]
                    title = policy_group["title"]
                    primary_type = policy_group["primary_type"]
                    issues = policy_group["issues"]

                    f.write(f"### {primary_type} {code} - {title}\n")
                    f.write(f"- Last reviewed: {policy_group['last_reviewed']}\n")
                    f.write(
                        f"- Material issues (missing from both BP and AR): {len(issues)}\n"
                    )
                    f.write("- Issues:\n")

                    for issue in issues:
                        f.write(
                            f"  - {issue['title']} ({issue['confidence']}% confidence)\n"
                        )

                    f.write("\n")

                # Group by issue type
                f.write("## Common Compliance Gaps\n\n")
                issue_types = {}
                for policy_group in self.all_material_issues:
                    for issue in policy_group["issues"]:
                        title = issue["title"]
                        if title not in issue_types:
                            issue_types[title] = []
                        issue_types[title].append(
                            f"{policy_group['primary_type']} {policy_group['code']}"
                        )

                for issue_title, policies in sorted(
                    issue_types.items(), key=lambda x: len(x[1]), reverse=True
                )[:10]:
                    f.write(f"- **{issue_title}** ({len(policies)} policy groups)\n")
                    f.write(f"  - Affected: {', '.join(sorted(policies)[:10])}")
                    if len(policies) > 10:
                        f.write(f" and {len(policies) - 10} more")
                    f.write("\n")

    def process_batch_parallel(self, codes: list[str]) -> int:
        """Process a batch of policy codes in parallel"""
        processed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_code = {
                executor.submit(self.process_policy_group, code): code for code in codes
            }

            # Process completed tasks
            for future in as_completed(future_to_code):
                code = future_to_code[future]
                try:
                    future.result()
                    processed += 1
                except Exception as e:
                    print(f"Error processing {code}: {e}")

        return processed

    def run_batch(self, resume=True, max_codes=None):
        """Run compliance check on all policy groups with batching and parallelization"""
        print("Starting comprehensive compliance check (v2)...")
        print(f"Batch size: {self.batch_size}, Workers: {self.max_workers}\n")

        # Get all unique policy codes
        all_codes = self.get_all_policy_codes()

        if max_codes:
            all_codes = all_codes[:max_codes]

        # Filter out completed codes if resuming
        if resume:
            completed = self.get_completed_codes()
            print(f"Already completed: {len(completed)} policy groups")

            remaining_codes = [code for code in all_codes if code not in completed]

            print(f"Remaining to check: {len(remaining_codes)} policy groups")
            codes_to_process = remaining_codes
        else:
            codes_to_process = all_codes

        print(f"Total to process: {len(codes_to_process)} policy groups\n")

        if not codes_to_process:
            print("All policy groups have been checked!")
            self.generate_summary()
            return

        # Process in batches
        total_batches = (len(codes_to_process) + self.batch_size - 1) // self.batch_size
        total_processed = 0

        for batch_num in range(total_batches):
            batch_start = batch_num * self.batch_size
            batch_end = min(batch_start + self.batch_size, len(codes_to_process))
            batch_codes = codes_to_process[batch_start:batch_end]

            print(f"\n--- Batch {batch_num + 1}/{total_batches} ---")
            print(
                f"Processing policy groups {batch_start + 1} to {batch_end} of {len(codes_to_process)}"
            )

            # Process batch in parallel
            batch_processed = self.process_batch_parallel(batch_codes)
            total_processed += batch_processed

            print(
                f"\nBatch {batch_num + 1} complete. Processed: {batch_processed} policy groups"
            )

            # Small delay between batches to avoid rate limits
            if batch_num < total_batches - 1:
                print("Waiting 2 seconds before next batch...")
                time.sleep(2)

        # Generate summary
        print("\n\nGenerating executive summary...")
        self.generate_summary()

        print("\nCompliance check complete!")
        print(f"Total processed: {total_processed} policy groups")
        print(f"Results saved to: {self.output_dir}/")
        print(f"Executive summary: {self.output_dir}/EXECUTIVE_SUMMARY.md")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="RCSD Policy Compliance Checker v2 - Analyzes BP and AR together",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check all policy groups with resume capability (recommended)
  python compliance_checker_v2.py

  # Check without resuming (start fresh)
  python compliance_checker_v2.py --no-resume

  # Check a single policy group (BP and AR together)
  python compliance_checker_v2.py --code 6142.1

  # Limit number of policy groups to check
  python compliance_checker_v2.py --max 100

  # Adjust batch size and parallelization
  python compliance_checker_v2.py --batch-size 10 --workers 5
        """,
    )

    parser.add_argument("--code", help="Check single policy code (BP and AR together)")
    parser.add_argument("--max", type=int, help="Maximum policy groups to check")
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start fresh instead of resuming from previous run",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Number of policy groups to process per batch (default: 20)",
    )
    parser.add_argument(
        "--workers", type=int, default=3, help="Number of parallel workers (default: 3)"
    )

    args = parser.parse_args()

    checker = ComplianceCheckerV2(batch_size=args.batch_size, max_workers=args.workers)

    if args.code:
        checker.process_policy_group(args.code)
    else:
        checker.run_batch(resume=not args.no_resume, max_codes=args.max)


if __name__ == "__main__":
    main()
