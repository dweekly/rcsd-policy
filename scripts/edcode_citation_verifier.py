#!/usr/bin/env python3
"""
Ed Code Citation Verifier
Extracts Ed Code citations from compliance findings and fetches actual statute text
from the authoritative CA Legislative Information website.
"""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed


class EdCodeFetcher:
    """Fetches and caches California Education Code sections"""
    
    def __init__(self, cache_dir="data/cache/edcode"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def fetch_section(self, section_num: str) -> Dict[str, str]:
        """Fetch a specific Education Code section"""
        # Check cache first
        cache_file = self.cache_dir / f"edc_{section_num.replace('.', '_')}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
                # Cache for 180 days
                if (datetime.now(timezone.utc) - datetime.fromisoformat(data["fetched"])).days < 180:
                    print(f"  Using cached version of Ed Code {section_num}")
                    return data
        
        # Fetch from website
        print(f"  Fetching Ed Code {section_num} from leginfo.legislature.ca.gov...")
        
        params = {
            "sectionNum": section_num,
            "lawCode": "EDC"
        }
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract the section content
            section_data = self._extract_section_content(soup, section_num)
            
            if section_data["content"]:
                # Cache the result
                section_data["fetched"] = datetime.now(timezone.utc).isoformat()
                with open(cache_file, 'w') as f:
                    json.dump(section_data, f, indent=2)
                
                print(f"  ✓ Successfully fetched Ed Code {section_num}")
            else:
                print(f"  ✗ Could not find content for Ed Code {section_num}")
            
            return section_data
            
        except Exception as e:
            print(f"  ✗ Error fetching Ed Code {section_num}: {e}")
            return {
                "section": section_num,
                "content": None,
                "error": str(e),
                "fetched": datetime.now(timezone.utc).isoformat()
            }
    
    def _extract_section_content(self, soup: BeautifulSoup, section_num: str) -> Dict[str, str]:
        """Extract section content from the HTML page"""
        result = {
            "section": section_num,
            "content": None,
            "title": None,
            "url": f"{self.base_url}?sectionNum={section_num}&lawCode=EDC"
        }
        
        # Method 1: Look for the section content in a specific pattern
        # The CA leg site typically shows the section in a content area
        content_area = soup.find('div', {'id': 'contentlist'})
        if not content_area:
            # Try alternative selectors
            content_area = soup.find('div', class_='content')
            if not content_area:
                content_area = soup.find('div', {'id': 'content'})
        
        if content_area:
            # Look for the section number in the content
            text = content_area.get_text(separator='\n', strip=True)
            
            # Try to find the section number and extract content after it
            patterns = [
                rf"{section_num}\.",  # "15282."
                rf"Section {section_num}",  # "Section 15282"
                rf"\b{section_num}\b"  # Just the number
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Extract content starting from the section number
                    start_idx = match.start()
                    # Extract up to next section or end
                    next_section = re.search(r'\n\d{4,5}\.', text[start_idx + 10:])
                    if next_section:
                        end_idx = start_idx + 10 + next_section.start()
                        result["content"] = text[start_idx:end_idx].strip()
                    else:
                        result["content"] = text[start_idx:].strip()
                    break
        
        # Method 2: If method 1 failed, try extracting all text and searching
        if not result["content"]:
            all_text = soup.get_text(separator='\n', strip=True)
            
            # Look for patterns that indicate the start of our section
            section_pattern = rf"(?:^|\n)({section_num}\..*?)(?=\n\d{{4,5}}\.|$)"
            match = re.search(section_pattern, all_text, re.DOTALL | re.MULTILINE)
            
            if match:
                result["content"] = match.group(1).strip()
        
        return result


class ComplianceCitationExtractor:
    """Extracts Ed Code citations from compliance findings"""
    
    def __init__(self, analysis_dir="data/analysis"):
        self.analysis_dir = Path(analysis_dir)
        self.citation_pattern = re.compile(
            r'(?:Education Code|Ed\.?\s*Code|Section|§)\s*(\d{4,5}(?:\.\d+)?)',
            re.IGNORECASE
        )
    
    def extract_citations_from_file(self, json_file: Path) -> Dict[str, List[str]]:
        """Extract Ed Code citations from a compliance JSON file"""
        with open(json_file) as f:
            data = json.load(f)
        
        citations = {
            "code": data.get("code", "unknown"),
            "citations": set()
        }
        
        # Look through compliance issues
        compliance = data.get("compliance", {})
        for issue in compliance.get("issues", []):
            # Only process material issues
            if issue.get("priority") != "MATERIAL":
                continue
            
            # Check description
            if desc := issue.get("description"):
                citations["citations"].update(self.citation_pattern.findall(desc))
            
            # Check legal citations
            for legal_cite in issue.get("legal_citations", []):
                if cite_num := legal_cite.get("citation"):
                    # Extract just the number
                    if match := re.search(r'(\d{4,5}(?:\.\d+)?)', cite_num):
                        citations["citations"].add(match.group(1))
                
                if cite_text := legal_cite.get("text"):
                    citations["citations"].update(self.citation_pattern.findall(cite_text))
        
        citations["citations"] = sorted(list(citations["citations"]))
        return citations
    
    def extract_all_citations(self, compliance_version="compliance") -> Dict[str, Set[str]]:
        """Extract all Ed Code citations from all compliance findings"""
        all_citations = {}
        unique_citations = set()
        
        json_dir = self.analysis_dir / compliance_version / "json_data"
        if not json_dir.exists():
            print(f"Directory {json_dir} not found")
            return all_citations, unique_citations
        
        for json_file in json_dir.glob("*.json"):
            file_citations = self.extract_citations_from_file(json_file)
            if file_citations["citations"]:
                all_citations[file_citations["code"]] = file_citations["citations"]
                unique_citations.update(file_citations["citations"])
        
        return all_citations, sorted(list(unique_citations))


class CitationVerificationReport:
    """Generates verification reports for Ed Code citations"""
    
    def __init__(self, output_dir="data/analysis/citation_verification"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, citations_by_policy: Dict, fetched_codes: Dict, compliance_version: str):
        """Generate a comprehensive verification report"""
        report_file = self.output_dir / f"verification_report_{compliance_version}.md"
        
        with open(report_file, 'w') as f:
            f.write(f"# Ed Code Citation Verification Report\n\n")
            f.write(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")
            f.write(f"Compliance Version: {compliance_version}\n\n")
            
            # Summary statistics
            total_policies = len(citations_by_policy)
            total_citations = sum(len(cites) for cites in citations_by_policy.values())
            unique_citations = len(fetched_codes)
            verified_citations = sum(1 for data in fetched_codes.values() if data.get("content"))
            
            f.write("## Summary\n\n")
            f.write(f"- Policies with Ed Code citations: {total_policies}\n")
            f.write(f"- Total citation instances: {total_citations}\n")
            f.write(f"- Unique Ed Code sections cited: {unique_citations}\n")
            f.write(f"- Successfully verified: {verified_citations}\n")
            f.write(f"- Could not verify: {unique_citations - verified_citations}\n\n")
            
            # Verification failures
            if failed := [s for s, d in fetched_codes.items() if not d.get("content")]:
                f.write("## ⚠️ Unverified Citations\n\n")
                f.write("These Ed Code sections could not be verified:\n\n")
                for section in sorted(failed):
                    f.write(f"- Section {section}")
                    if error := fetched_codes[section].get("error"):
                        f.write(f" (Error: {error})")
                    f.write("\n")
                f.write("\n")
            
            # Verified citations with content
            f.write("## ✓ Verified Citations\n\n")
            for section in sorted(fetched_codes.keys()):
                if content := fetched_codes[section].get("content"):
                    f.write(f"### Education Code Section {section}\n\n")
                    f.write(f"URL: {fetched_codes[section].get('url', 'N/A')}\n\n")
                    
                    # Show first 500 chars of content
                    if len(content) > 500:
                        f.write(f"{content[:500]}...\n\n")
                        f.write(f"*[Content truncated - full text available in cache]*\n\n")
                    else:
                        f.write(f"{content}\n\n")
                    
                    # Show which policies cite this
                    citing_policies = [
                        code for code, cites in citations_by_policy.items() 
                        if section in cites
                    ]
                    if citing_policies:
                        f.write(f"**Cited by:** {', '.join(sorted(citing_policies))}\n\n")
                    
                    f.write("---\n\n")
            
            # Policy-by-policy breakdown
            f.write("## Citations by Policy\n\n")
            for policy_code in sorted(citations_by_policy.keys()):
                citations = citations_by_policy[policy_code]
                f.write(f"### {policy_code}\n")
                f.write("Ed Code sections cited:\n")
                for cite in citations:
                    status = "✓" if fetched_codes.get(cite, {}).get("content") else "✗"
                    f.write(f"- {status} Section {cite}\n")
                f.write("\n")
        
        print(f"\nVerification report saved to: {report_file}")
        
        # Also save JSON data for programmatic use
        json_file = self.output_dir / f"verification_data_{compliance_version}.json"
        with open(json_file, 'w') as f:
            json.dump({
                "generated": datetime.now(timezone.utc).isoformat(),
                "compliance_version": compliance_version,
                "citations_by_policy": citations_by_policy,
                "fetched_codes": fetched_codes,
                "summary": {
                    "total_policies": total_policies,
                    "total_citations": total_citations,
                    "unique_citations": unique_citations,
                    "verified_citations": verified_citations
                }
            }, f, indent=2)
        
        print(f"Verification data saved to: {json_file}")


def main():
    """Main function to extract and verify Ed Code citations"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract and verify Ed Code citations from compliance findings"
    )
    parser.add_argument(
        "--version",
        default="compliance",
        help="Compliance version directory to analyze (default: compliance)"
    )
    parser.add_argument(
        "--max-citations",
        type=int,
        help="Maximum number of citations to fetch (for testing)"
    )
    parser.add_argument(
        "--policy",
        help="Analyze only a specific policy code"
    )
    
    args = parser.parse_args()
    
    # Initialize components
    extractor = ComplianceCitationExtractor()
    fetcher = EdCodeFetcher()
    reporter = CitationVerificationReport()
    
    print(f"Extracting Ed Code citations from {args.version} findings...\n")
    
    # Extract citations
    if args.policy:
        # Single policy mode
        json_file = Path(f"data/analysis/{args.version}/json_data/{args.policy}.json")
        if not json_file.exists():
            print(f"File not found: {json_file}")
            return
        
        file_citations = extractor.extract_citations_from_file(json_file)
        citations_by_policy = {file_citations["code"]: file_citations["citations"]}
        unique_citations = file_citations["citations"]
    else:
        # All policies mode
        citations_by_policy, unique_citations = extractor.extract_all_citations(args.version)
    
    print(f"Found {len(unique_citations)} unique Ed Code sections cited")
    print(f"Cited by {len(citations_by_policy)} policies\n")
    
    if not unique_citations:
        print("No Ed Code citations found.")
        return
    
    # Limit citations if requested
    if args.max_citations:
        unique_citations = unique_citations[:args.max_citations]
        print(f"Limiting to first {args.max_citations} citations for testing\n")
    
    # Fetch Ed Code sections
    print("Fetching Ed Code sections from leginfo.legislature.ca.gov...\n")
    
    fetched_codes = {}
    for i, section in enumerate(unique_citations, 1):
        print(f"[{i}/{len(unique_citations)}] Processing Ed Code {section}")
        
        # Add small delay to be respectful to the server
        if i > 1:
            time.sleep(1)
        
        result = fetcher.fetch_section(section)
        fetched_codes[section] = result
    
    # Generate report
    print("\nGenerating verification report...")
    reporter.generate_report(citations_by_policy, fetched_codes, args.version)
    
    # Summary
    verified = sum(1 for d in fetched_codes.values() if d.get("content"))
    print(f"\n✓ Successfully verified {verified}/{len(unique_citations)} Ed Code sections")
    
    if verified < len(unique_citations):
        print(f"✗ Could not verify {len(unique_citations) - verified} sections")


if __name__ == "__main__":
    main()