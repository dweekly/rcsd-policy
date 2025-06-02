#!/usr/bin/env python3
"""
RCSD Policy Compliance Checker v3
- Verifies Ed Code citations before making compliance recommendations
- Uses two-step analysis: identify issues, then verify citations
- Reduces hallucination by checking actual statute text
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
import requests
from bs4 import BeautifulSoup

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class EdCodeVerifier:
    """Fetches and verifies California Education Code sections"""
    
    def __init__(self, cache_dir="data/cache/edcode"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml"
    
    def get_ed_code_section(self, section_num):
        """Fetch a specific Education Code section from CA Legislative website"""
        # Check cache first
        cache_file = self.cache_dir / f"edc_{section_num}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
                # Cache for 90 days
                if (datetime.now(timezone.utc) - datetime.fromisoformat(data["fetched"])).days < 90:
                    return data["content"]
        
        # Fetch from website
        try:
            params = {
                "sectionNum": f"{section_num}.",
                "lawCode": "EDC"
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse HTML to extract statute text
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the content div that contains the statute text
            content_div = soup.find('div', {'id': 'manylawsection'})
            if not content_div:
                return None
            
            # Extract and clean the text
            statute_text = content_div.get_text(separator='\n', strip=True)
            
            # Cache the result
            with open(cache_file, 'w') as f:
                json.dump({
                    "section": section_num,
                    "content": statute_text,
                    "fetched": datetime.now(timezone.utc).isoformat()
                }, f)
            
            return statute_text
            
        except Exception as e:
            print(f"Error fetching Ed Code {section_num}: {e}")
            return None
    
    def extract_citations_from_text(self, text):
        """Extract Ed Code citations from compliance analysis text"""
        # Pattern to match Ed Code citations
        patterns = [
            r"Education Code Section (\d+(?:\.\d+)?)",
            r"Ed(?:ucation)? Code (\d+(?:\.\d+)?)",
            r"Section (\d+(?:\.\d+)?)",
            r"§\s*(\d+(?:\.\d+)?)"
        ]
        
        citations = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            citations.update(matches)
        
        return list(citations)


class ComplianceCheckerV3:
    def __init__(
        self,
        cache_dir="data/cache",
        output_dir="data/analysis/compliance_v3",
        batch_size=10,  # Smaller batches due to verification overhead
        max_workers=2,  # Fewer workers to avoid rate limits
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
        (self.output_dir / "verification_logs").mkdir(exist_ok=True)

        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-4-sonnet-20250514")

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = Anthropic(api_key=self.api_key)
        self.verifier = EdCodeVerifier()

        # Track all issues for final summary
        self.all_material_issues = []
        self.api_calls_made = 0
        self.api_calls_cached = 0
        self.verifications_performed = 0

    def get_cache_key(self, code, policy_xml, regulation_xml, last_reviewed):
        """Generate cache key for API responses"""
        version = "v3.0"  # New version for verified compliance
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
        main_text = re.sub(r"\n\d+\n", "\n", main_text)  # Remove standalone page numbers

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

    def identify_potential_issues(self, code, policy_xml, regulation_xml, title, last_reviewed):
        """Step 1: Identify potential compliance issues"""
        
        prompt = f"""You are reviewing a California school district's policy and regulation set for potential compliance issues.

IMPORTANT: 
- When citing Education Code sections, be VERY SPECIFIC about the section number
- If you're unsure about an exact citation, indicate this with phrases like "approximately Section X" or "likely in Section X"
- Focus on identifying potential issues that need verification

Policy/Regulation: {code} - {title}
Last Updated: {last_reviewed}

Identify potential compliance issues. For each issue:
1. Describe what might be missing
2. Provide your best guess at the relevant Ed Code section
3. Indicate your confidence in the citation (high/medium/low)
4. Note whether issue would be material only if missing from BOTH documents

<potential_issues>
    <issue>
        <title>[Brief issue title]</title>
        <description>[What might be missing]</description>
        <ed_code_guess>[Your best guess at Ed Code section, e.g., "15282" or "approximately 15278-15282"]</ed_code_guess>
        <citation_confidence>high|medium|low</citation_confidence>
        <missing_from>BP|AR|BOTH</missing_from>
    </issue>
</potential_issues>

<board_policy>
{policy_xml if policy_xml else "<not_found/>"}
</board_policy>

<administrative_regulation>
{regulation_xml if regulation_xml else "<not_found/>"}
</administrative_regulation>"""

        print(f"  Step 1: Identifying potential issues for {code}...")
        self.api_calls_made += 1

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def verify_and_finalize_issues(self, code, potential_issues_xml, verified_citations):
        """Step 2: Verify citations and finalize compliance findings"""
        
        prompt = f"""You are finalizing compliance findings for Policy/Regulation {code}.

Based on the potential issues identified and the ACTUAL Education Code text provided below, 
create final compliance findings. Only include issues where the legal requirement is VERIFIED
in the actual statute text.

<verified_ed_code_sections>
{json.dumps(verified_citations, indent=2)}
</verified_ed_code_sections>

<potential_issues>
{potential_issues_xml}
</potential_issues>

For each VERIFIED issue, provide:
1. Exact quote from the Ed Code supporting the requirement
2. Specific language that must be added to comply
3. Whether this is truly a MATERIAL issue

<compliance_report>
    <compliance_issues>
        <issue priority="MATERIAL|MINOR" confidence="[0-100]">
            <title>[Issue Title]</title>
            <description>[Why this is required based on verified statute]</description>
            <missing_from>BP|AR|BOTH</missing_from>
            
            <legal_basis>
                <california_code>
                    <citation>[Exact Ed Code Section]</citation>
                    <text>[EXACT QUOTE from verified statute]</text>
                    <verified>true</verified>
                </california_code>
            </legal_basis>
            
            <required_language>
                <text>[Specific language based on verified requirement]</text>
            </required_language>
            
            <recommended_placement>BP|AR</recommended_placement>
        </issue>
    </compliance_issues>
</compliance_report>"""

        print(f"  Step 2: Verifying and finalizing issues for {code}...")
        self.api_calls_made += 1

        response = self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def check_compliance_with_verification(self, code, policy_xml, regulation_xml, title, last_reviewed):
        """Check compliance with Ed Code verification"""
        
        # Check cache first
        cache_key = self.get_cache_key(code, policy_xml, regulation_xml, last_reviewed)
        cached_response = self.get_cached_response(cache_key)
        if cached_response:
            print(f"  Using cached response for {code}")
            return cached_response

        # Step 1: Identify potential issues
        potential_issues = self.identify_potential_issues(
            code, policy_xml, regulation_xml, title, last_reviewed
        )
        
        # Extract Ed Code citations to verify
        citations_to_verify = self.extract_citations_from_potential_issues(potential_issues)
        
        # Step 2: Verify Ed Code citations
        verified_citations = {}
        for citation in citations_to_verify:
            print(f"  Verifying Ed Code {citation}...")
            self.verifications_performed += 1
            statute_text = self.verifier.get_ed_code_section(citation)
            if statute_text:
                verified_citations[citation] = statute_text
            else:
                verified_citations[citation] = "COULD NOT VERIFY - Section not found"
        
        # Save verification log
        verification_log = self.output_dir / "verification_logs" / f"{code}_verification.json"
        with open(verification_log, 'w') as f:
            json.dump({
                "code": code,
                "potential_issues": potential_issues,
                "citations_checked": citations_to_verify,
                "verified_citations": verified_citations,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, f, indent=2)
        
        # Step 3: Finalize issues based on verified citations
        final_response = self.verify_and_finalize_issues(
            code, potential_issues, verified_citations
        )
        
        # Cache the response
        self.save_cache(cache_key, final_response)
        
        return final_response

    def extract_citations_from_potential_issues(self, xml_text):
        """Extract Ed Code citations from potential issues XML"""
        citations = set()
        
        # Look for ed_code_guess tags
        guess_matches = re.findall(r"<ed_code_guess>([^<]+)</ed_code_guess>", xml_text)
        for guess in guess_matches:
            # Extract numbers from guesses like "15282" or "approximately 15278-15282"
            numbers = re.findall(r"\d+(?:\.\d+)?", guess)
            citations.update(numbers)
        
        # Also check for any Ed Code mentions in the text
        text_citations = self.verifier.extract_citations_from_text(xml_text)
        citations.update(text_citations)
        
        return sorted(list(citations))

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
                    "verified": False
                }

                # Legal citations
                for ca_code in issue.findall(".//california_code"):
                    citation = ca_code.find("citation")
                    text = ca_code.find("text")
                    verified = ca_code.find("verified")
                    if citation is not None:
                        issue_data["legal_citations"].append(
                            {
                                "citation": citation.text,
                                "text": text.text if text is not None else "",
                                "verified": verified.text == "true" if verified is not None else False
                            }
                        )
                    if verified is not None and verified.text == "true":
                        issue_data["verified"] = True

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

        # Extract material issues (only verified ones)
        material_issues = [
            i
            for i in compliance_data.get("issues", [])
            if i.get("priority") == "MATERIAL" 
            and i.get("missing_from") == "BOTH"
            and i.get("verified", False)
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
                f.write("MATERIAL COMPLIANCE ISSUES (VERIFIED)\n")
                f.write(f"{primary_type} {code}: {display_title}\n")
                f.write(f"Last Reviewed: {last_reviewed}\n")
                f.write("=" * 80 + "\n\n")

                for issue in material_issues:
                    f.write(f"{issue['title']} (Confidence: {issue['confidence']}%)\n")
                    f.write(f"Missing from: {issue['missing_from']}\n")
                    f.write(f"VERIFIED: Yes - Citation confirmed against actual statute\n")
                    f.write(f"{issue['description']}\n\n")

                    if issue.get("legal_citations"):
                        f.write("Legal Basis (VERIFIED):\n")
                        for cite in issue["legal_citations"]:
                            f.write(f"- {cite['citation']}: {cite['text']}\n")
                            if cite.get('verified'):
                                f.write("  ✓ VERIFIED against actual statute text\n")
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

        # Check compliance with verification
        response = self.check_compliance_with_verification(
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
                if i.get("priority") == "MATERIAL" 
                and i.get("missing_from") == "BOTH"
                and i.get("verified", False)
            ]
        )
        print(f"  Verified material issues found: {material_count}")

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
            f.write("# RCSD Policy Compliance Check - Executive Summary (v3)\n\n")
            f.write(
                f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}\n\n"
            )
            f.write("## Important Notice\n\n")
            f.write("**This analysis uses VERIFIED Education Code citations.**\n")
            f.write("All material findings have been checked against actual California statutes.\n")
            f.write("Verification logs are available in `data/analysis/compliance_v3/verification_logs/`\n\n")

            f.write("## Statistics\n\n")
            f.write(f"- Total API calls made: {self.api_calls_made}\n")
            f.write(f"- Cached responses used: {self.api_calls_cached}\n")
            f.write(f"- Ed Code verifications performed: {self.verifications_performed}\n")
            f.write(
                f"- Policy groups with verified material issues: {len(self.all_material_issues)}\n"
            )

            total_issues = sum(len(p["issues"]) for p in self.all_material_issues)
            f.write(f"- Total verified material issues found: {total_issues}\n\n")

            if self.all_material_issues:
                f.write("## Policy Groups Requiring Immediate Attention (Verified)\n\n")

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
                        f"- Verified material issues (missing from both BP and AR): {len(issues)}\n"
                    )
                    f.write("- Issues:\n")

                    for issue in issues:
                        f.write(
                            f"  - {issue['title']} ({issue['confidence']}% confidence) ✓ VERIFIED\n"
                        )

                    f.write("\n")

                # Group by issue type
                f.write("## Common Compliance Gaps (All Verified)\n\n")
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
        print("Starting comprehensive compliance check (v3 - with verification)...")
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
        print(f"Ed Code verifications performed: {self.verifications_performed}")
        print(f"Results saved to: {self.output_dir}/")
        print(f"Executive summary: {self.output_dir}/EXECUTIVE_SUMMARY.md")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="RCSD Policy Compliance Checker v3 - With Ed Code Verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check all policy groups with verification (recommended)
  python compliance_checker_v3.py

  # Check without resuming (start fresh)
  python compliance_checker_v3.py --no-resume

  # Check a single policy group with verification
  python compliance_checker_v3.py --code 1221.4

  # Limit number of policy groups to check
  python compliance_checker_v3.py --max 10

  # Adjust batch size and parallelization
  python compliance_checker_v3.py --batch-size 5 --workers 1
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
        default=10,
        help="Number of policy groups to process per batch (default: 10)",
    )
    parser.add_argument(
        "--workers", type=int, default=2, help="Number of parallel workers (default: 2)"
    )

    args = parser.parse_args()

    checker = ComplianceCheckerV3(batch_size=args.batch_size, max_workers=args.workers)

    if args.code:
        checker.process_policy_group(args.code)
    else:
        checker.run_batch(resume=not args.no_resume, max_codes=args.max)


if __name__ == "__main__":
    main()