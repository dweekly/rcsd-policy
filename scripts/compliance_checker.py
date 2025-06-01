#!/usr/bin/env python3
"""
RCSD Policy Compliance Checker
- Uses Anthropic Claude API to analyze policies for California legal compliance
- Implements caching to avoid redundant API calls
- Extracts and follows cross-references between policies
- Generates detailed compliance reports with material issues identified
- Supports parallel processing, batching, and resume capability
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


class ComplianceChecker:
    def __init__(
        self,
        cache_dir="data/cache",
        output_dir="data/analysis/compliance",
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

    def get_cache_key(self, policy_code, policy_xml, last_reviewed):
        """Generate cache key for API responses"""
        # Include version to invalidate cache when we fix parsing issues
        version = "v4"  # Increment this when fixing parsing bugs
        content = f"{version}:{policy_code}:{last_reviewed}:{policy_xml}"
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

    def find_related_policies(self, policy_code, cross_refs, base_dir="data/extracted"):
        """Find related policies based on cross-references and numbering patterns"""
        related = {}

        # Start with explicitly cross-referenced policies
        check_codes = set(cross_refs)

        # Add sequential policies (e.g., 5131.1, 5131.2 if checking 5131)
        base_code = policy_code.split(".")[0]
        for i in range(1, 6):
            check_codes.add(f"{base_code}.{i}")

        # Check parent policy if this is a sub-policy
        if "." in policy_code:
            check_codes.add(base_code)

        # Common related series patterns
        series = int(base_code[0]) * 1000 if base_code[0].isdigit() else 0
        if series == 5000:  # Student policies often relate
            check_codes.update(["0410", "1312.3", "5145.3", "5145.7"])
        elif series == 3000:  # Business policies
            if "35" in base_code:  # Food/nutrition
                check_codes.update(["5030", "3550", "3551", "3552", "3553"])
        elif series == 0:  # Philosophy/goals
            if base_code == "0450":  # Safety
                check_codes.update(["3515", "3516", "5131.4", "5141.4"])

        # Check for each potentially related policy
        for code in check_codes:
            if code == policy_code:  # Skip self
                continue

            for subdir in ["policies", "regulations"]:
                file_path = os.path.join(base_dir, subdir, f"{code}.txt")
                if os.path.exists(file_path):
                    try:
                        with open(file_path) as f:
                            header = f.read(500)

                        title_match = re.search(r"Title:\s*(.+?)(?:\n|$)", header)
                        title = title_match.group(1) if title_match else "Unknown"

                        related[code] = {
                            "title": title,
                            "type": subdir[:-1].capitalize(),
                            "file_path": file_path,
                        }
                    except Exception:
                        pass

        return related

    def parse_policy_to_xml(self, file_path):
        """Convert policy to XML and extract metadata"""
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
        xml = f"""<policy>
    <metadata>
        <code>{code}</code>
        <type>{doc_type}</type>
        <title>{title}</title>
        <adopted>{adopted or "Unknown"}</adopted>
        <last_reviewed>{reviewed or adopted or "Unknown"}</last_reviewed>
    </metadata>
    <content>{main_text}</content>
</policy>"""

        return xml, code, title, reviewed

    def check_compliance(
        self, policy_xml, code, title, last_reviewed, related_policies
    ):
        """Check compliance with caching"""
        cache_key = self.get_cache_key(code, policy_xml, last_reviewed)

        # Check cache first
        cached_response = self.get_cached_response(cache_key)
        if cached_response:
            print(f"  Using cached response for {code}")
            return cached_response

        # Build context about related policies
        related_context = "Related policies in the district:\n"
        for rel_code, rel_info in related_policies.items():
            related_context += f"- {rel_info['type']} {rel_code}: {rel_info['title']}\n"

        prompt = f"""You are reviewing a California school district policy for compliance.

IMPORTANT: School districts organize requirements across multiple related policies. Only flag issues as MATERIAL if the requirement MUST be in this specific policy by law.

Policy: {code} - {title}
Last Updated: {last_reviewed}

{related_context}

For each compliance issue:
1. Consider if this requirement belongs in THIS policy or a related one
2. Only flag as MATERIAL if legally required in this specific policy
3. Include confidence level and specific legal citations

<compliance_report>
    <compliance_issues>
        <issue priority="MATERIAL|MINOR" confidence="[0-100]">
            <title>[Issue Title]</title>
            <description>[Why this specific policy needs this]</description>
            <typical_location>[This Policy or Usually in Policy XXXX]</typical_location>

            <legal_basis>
                <california_code>
                    <citation>[Ed Code/Gov Code Section]</citation>
                    <text>[Relevant excerpt]</text>
                    <requires_in_specific_policy>[true/false]</requires_in_specific_policy>
                </california_code>
            </legal_basis>

            <required_language>
                <text>[Specific language that must be added]</text>
            </required_language>

            <recommended_action>
                <option type="ADD_LANGUAGE|CROSS_REFERENCE|VERIFY_EXISTS">[Action]</option>
            </recommended_action>
        </issue>
    </compliance_issues>
</compliance_report>

<policy_document>
{policy_xml}
</policy_document>"""

        print(f"  Calling API for {code}...")
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
                    "typical_location": issue.find("typical_location").text
                    if issue.find("typical_location") is not None
                    else "",
                    "legal_citations": [],
                    "required_language": "",
                    "recommended_actions": [],
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

                # Recommended actions
                for action in issue.findall(".//recommended_action/option"):
                    issue_data["recommended_actions"].append(
                        {"type": action.get("type"), "description": action.text}
                    )

                issues.append(issue_data)

            return {"issues": issues}

        except Exception as e:
            return {"error": f"Parse error: {e!s}", "raw": xml_response}

    def save_results(self, policy_data, compliance_data):
        """Save comprehensive results in multiple formats"""
        code = policy_data["code"]

        # Save full JSON data
        json_file = self.output_dir / "json_data" / f"{code}.json"
        with open(json_file, "w") as f:
            json.dump(
                {
                    "policy": policy_data,
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
            if i.get("priority") == "MATERIAL"
        ]

        if material_issues:
            # Track for summary
            self.all_material_issues.append(
                {"policy": policy_data, "issues": material_issues}
            )

            # Save material issues report
            material_file = self.output_dir / "material_issues" / f"{code}_material.txt"
            with open(material_file, "w") as f:
                f.write("MATERIAL COMPLIANCE ISSUES\n")
                f.write(f"Policy {code}: {policy_data['title']}\n")
                f.write(
                    f"Last Reviewed: {policy_data.get('last_reviewed', 'Unknown')}\n"
                )
                f.write("=" * 80 + "\n\n")

                for issue in material_issues:
                    f.write(f"{issue['title']} (Confidence: {issue['confidence']}%)\n")
                    f.write(f"{issue['description']}\n\n")

                    if issue.get("legal_citations"):
                        f.write("Legal Basis:\n")
                        for cite in issue["legal_citations"]:
                            f.write(f"- {cite['citation']}: {cite['text']}\n")
                        f.write("\n")

                    if issue.get("required_language"):
                        f.write("Required Language:\n")
                        f.write(f"{issue['required_language']}\n\n")

                    f.write("-" * 40 + "\n\n")

    def process_policy(self, file_path):
        """Process a single policy with full context"""
        print(f"\nProcessing: {file_path}")

        # Parse policy
        policy_xml, code, title, last_reviewed = self.parse_policy_to_xml(file_path)

        # Extract cross-references
        cross_refs = self.extract_cross_references(file_path)
        print(
            f"  Found {len(cross_refs)} cross-references: {', '.join(sorted(cross_refs))}"
        )

        # Find related policies
        related = self.find_related_policies(code, cross_refs)
        print(f"  Found {len(related)} related policies")

        # Check compliance
        response = self.check_compliance(
            policy_xml, code, title, last_reviewed, related
        )

        # Parse response
        compliance_data = self.parse_compliance_xml(response)

        # Save results
        policy_data = {
            "code": code,
            "title": title,
            "type": "Policy" if "/policies/" in file_path else "Regulation",
            "last_reviewed": last_reviewed,
            "file_path": file_path,
            "cross_references": cross_refs,
            "related_policies": list(related.keys()),
        }

        self.save_results(policy_data, compliance_data)

        # Report material issues
        material_count = len(
            [
                i
                for i in compliance_data.get("issues", [])
                if i.get("priority") == "MATERIAL"
            ]
        )
        print(f"  Material issues found: {material_count}")

        return material_count

    def generate_summary(self):
        """Generate executive summary of all findings"""
        summary_file = self.output_dir / "EXECUTIVE_SUMMARY.md"

        with open(summary_file, "w") as f:
            f.write("# RCSD Policy Compliance Check - Executive Summary\n\n")
            f.write(
                f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}\n\n"
            )

            f.write("## Statistics\n\n")
            f.write(f"- Total API calls made: {self.api_calls_made}\n")
            f.write(f"- Cached responses used: {self.api_calls_cached}\n")
            f.write(
                f"- Policies with material issues: {len(self.all_material_issues)}\n"
            )

            total_issues = sum(len(p["issues"]) for p in self.all_material_issues)
            f.write(f"- Total material issues found: {total_issues}\n\n")

            if self.all_material_issues:
                f.write("## Policies Requiring Immediate Attention\n\n")

                # Sort by number of issues
                sorted_policies = sorted(
                    self.all_material_issues,
                    key=lambda x: len(x["issues"]),
                    reverse=True,
                )

                for policy_issues in sorted_policies[:20]:  # Top 20
                    policy = policy_issues["policy"]
                    issues = policy_issues["issues"]

                    f.write(f"### {policy['code']} - {policy['title']}\n")
                    f.write(
                        f"- Last reviewed: {policy.get('last_reviewed', 'Unknown')}\n"
                    )
                    f.write(f"- Material issues: {len(issues)}\n")
                    f.write("- Issues:\n")

                    for issue in issues:
                        f.write(
                            f"  - {issue['title']} ({issue['confidence']}% confidence)\n"
                        )

                    f.write("\n")

                # Group by issue type
                f.write("## Common Compliance Gaps\n\n")
                issue_types = {}
                for policy_issues in self.all_material_issues:
                    for issue in policy_issues["issues"]:
                        title = issue["title"]
                        if title not in issue_types:
                            issue_types[title] = []
                        issue_types[title].append(policy_issues["policy"]["code"])

                for issue_title, policies in sorted(
                    issue_types.items(), key=lambda x: len(x[1]), reverse=True
                )[:10]:
                    f.write(f"- **{issue_title}** ({len(policies)} policies)\n")
                    f.write(
                        f"  - Affected policies: {', '.join(sorted(policies)[:10])}"
                    )
                    if len(policies) > 10:
                        f.write(f" and {len(policies) - 10} more")
                    f.write("\n")

    def get_completed_documents(self) -> set[str]:
        """Get set of documents that have already been processed"""
        completed = set()
        json_dir = self.output_dir / "json_data"

        if json_dir.exists():
            for file in json_dir.glob("*.json"):
                # Extract document code from filename
                completed.add(file.stem)

        return completed

    def process_batch_parallel(self, files: list[Path]) -> int:
        """Process a batch of files in parallel"""
        processed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.process_policy, str(file_path)): file_path
                for file_path in files
            }

            # Process completed tasks
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    future.result()
                    processed += 1
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

        return processed

    def run_batch(self, resume=True, max_policies=None):
        """Run compliance check on all policies with batching and parallelization"""
        print("Starting comprehensive compliance check...")
        print(f"Batch size: {self.batch_size}, Workers: {self.max_workers}\n")

        # Get all policy files
        all_files = []
        for subdir in ["policies", "regulations"]:
            dir_path = Path("data/extracted") / subdir
            if dir_path.exists():
                all_files.extend(list(dir_path.glob("*.txt")))

        if max_policies:
            all_files = all_files[:max_policies]

        # Filter out completed documents if resuming
        if resume:
            completed = self.get_completed_documents()
            print(f"Already completed: {len(completed)} documents")

            remaining_files = []
            for file in all_files:
                if file.stem not in completed:
                    remaining_files.append(file)

            print(f"Remaining to check: {len(remaining_files)} documents")
            files_to_process = remaining_files
        else:
            files_to_process = all_files

        print(f"Total to process: {len(files_to_process)} documents\n")

        if not files_to_process:
            print("All documents have been checked!")
            self.generate_summary()
            return

        # Process in batches
        total_batches = (len(files_to_process) + self.batch_size - 1) // self.batch_size
        total_processed = 0

        for batch_num in range(total_batches):
            batch_start = batch_num * self.batch_size
            batch_end = min(batch_start + self.batch_size, len(files_to_process))
            batch_files = files_to_process[batch_start:batch_end]

            print(f"\n--- Batch {batch_num + 1}/{total_batches} ---")
            print(
                f"Processing documents {batch_start + 1} to {batch_end} of {len(files_to_process)}"
            )

            # Process batch in parallel
            batch_processed = self.process_batch_parallel(batch_files)
            total_processed += batch_processed

            print(
                f"\nBatch {batch_num + 1} complete. Processed: {batch_processed} documents"
            )

            # Small delay between batches to avoid rate limits
            if batch_num < total_batches - 1:
                print("Waiting 2 seconds before next batch...")
                time.sleep(2)

        # Generate summary
        print("\n\nGenerating executive summary...")
        self.generate_summary()

        print("\nCompliance check complete!")
        print(f"Total processed: {total_processed} documents")
        print(f"Results saved to: {self.output_dir}/")
        print(f"Executive summary: {self.output_dir}/EXECUTIVE_SUMMARY.md")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="RCSD Policy Compliance Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check all policies with resume capability (recommended)
  python compliance_checker.py

  # Check without resuming (start fresh)
  python compliance_checker.py --no-resume

  # Check a single policy
  python compliance_checker.py --policy data/extracted/policies/1234.txt

  # Limit number of policies to check
  python compliance_checker.py --max 100

  # Adjust batch size and parallelization
  python compliance_checker.py --batch-size 10 --workers 5
        """,
    )

    parser.add_argument("--policy", help="Check single policy file")
    parser.add_argument("--max", type=int, help="Maximum policies to check")
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start fresh instead of resuming from previous run",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Number of documents to process per batch (default: 20)",
    )
    parser.add_argument(
        "--workers", type=int, default=3, help="Number of parallel workers (default: 3)"
    )

    args = parser.parse_args()

    checker = ComplianceChecker(batch_size=args.batch_size, max_workers=args.workers)

    if args.policy:
        checker.process_policy(args.policy)
    else:
        checker.run_batch(resume=not args.no_resume, max_policies=args.max)


if __name__ == "__main__":
    main()
