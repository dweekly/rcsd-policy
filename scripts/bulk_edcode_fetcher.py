#!/usr/bin/env python3
"""
Bulk Ed Code fetcher using requests and ThreadPoolExecutor
Fetches multiple sections in parallel
"""

import json
import requests
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys
import re
from html.parser import HTMLParser


class EdCodeParser(HTMLParser):
    """Simple HTML parser to extract Ed Code content"""
    
    def __init__(self):
        super().__init__()
        self.in_content = False
        self.content_lines = []
        self.current_text = []
        
    def handle_starttag(self, tag, attrs):
        # Look for content divs
        for attr, value in attrs:
            if attr == 'class' and 'content' in value.lower():
                self.in_content = True
    
    def handle_endtag(self, tag):
        if self.in_content and tag in ['div', 'article', 'main']:
            self.in_content = False
    
    def handle_data(self, data):
        if self.in_content:
            cleaned = data.strip()
            if cleaned:
                self.current_text.append(cleaned)
        elif self.current_text:
            # Save accumulated text
            self.content_lines.append(' '.join(self.current_text))
            self.current_text = []
    
    def get_content(self):
        if self.current_text:
            self.content_lines.append(' '.join(self.current_text))
        return '\n'.join(self.content_lines)


def fetch_section(section_info):
    """Fetch a single Ed Code section"""
    section = section_info["section"]
    law_code = section_info["law_code"]
    url = section_info["url"]
    
    # Check if already cached
    safe_section = section.replace(".", "_")
    cache_file = Path(f"data/cache/edcode/{law_code.lower()}_{safe_section}_full.json")
    
    if cache_file.exists():
        return {
            "status": "cached",
            "section": section,
            "law_code": law_code
        }
    
    try:
        # Make request with timeout
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return {
                "status": "error",
                "section": section,
                "law_code": law_code,
                "error": f"HTTP {response.status_code}"
            }
        
        # Extract content
        html = response.text
        content = extract_content_simple(html, section, law_code)
        
        if content:
            # Save to file
            save_section(section, law_code, content["text"], content["title"], url)
            
            return {
                "status": "success",
                "section": section,
                "law_code": law_code,
                "title": content["title"]
            }
        else:
            return {
                "status": "parse_error",
                "section": section,
                "law_code": law_code,
                "error": "Could not extract content"
            }
            
    except requests.Timeout:
        return {
            "status": "timeout",
            "section": section,
            "law_code": law_code,
            "error": "Request timed out"
        }
    except Exception as e:
        return {
            "status": "error",
            "section": section,
            "law_code": law_code,
            "error": str(e)
        }


def extract_content_simple(html, section, law_code):
    """Extract section content using simple regex patterns"""
    
    # Remove script and style tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Look for section patterns
    patterns = [
        # Pattern 1: Section number with brackets
        rf'{section}\.\s*\[([^\]]+)\](.*?)(?=\n{section}\.|$)',
        # Pattern 2: Section number with title
        rf'Section\s+{section}[^\n]*\n(.*?)(?=Section\s+\d+|$)',
        # Pattern 3: Just section number
        rf'{section}\.\s*(.*?)(?=\d+\.\s*|$)',
    ]
    
    content = None
    title = f"{law_code} Section {section}"
    
    for pattern in patterns:
        match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        if match:
            if len(match.groups()) > 1:
                title = match.group(1).strip()
                content = match.group(2).strip()
            else:
                content = match.group(1).strip()
            break
    
    if not content:
        # Try to find any text containing the section number
        # Extract a window of text around it
        section_pattern = rf'\b{section}\b'
        match = re.search(section_pattern, html)
        if match:
            start = max(0, match.start() - 1000)
            end = min(len(html), match.end() + 5000)
            content = html[start:end]
    
    if content:
        # Clean up HTML tags
        content = re.sub(r'<[^>]+>', ' ', content)
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        # Extract title if found in content
        title_match = re.search(rf'{section}\.\s*\[([^\]]+)\]', content)
        if title_match:
            title = title_match.group(1).strip()
        
        return {
            "title": title,
            "text": content
        }
    
    return None


def save_section(section, law_code, content, title, url):
    """Save section to JSON file"""
    safe_section = section.replace(".", "_")
    output_file = Path(f"data/cache/edcode/{law_code.lower()}_{safe_section}_full.json")
    
    data = {
        "section": section,
        "content": content,
        "title": title,
        "law_code": law_code,
        "url": url,
        "fetched": datetime.now(timezone.utc).isoformat(),
        "verified_by": "Bulk fetcher"
    }
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_sections_to_fetch():
    """Load sections from manifests"""
    
    # First check for remaining sections file
    remaining_file = Path("scripts/remaining_sections.json")
    if remaining_file.exists():
        with open(remaining_file) as f:
            return json.load(f)
    
    manifest_dir = Path("data/cache/edcode_manifests")
    all_sections = []
    
    if not manifest_dir.exists():
        # Try loading from the summary file
        summary_file = Path("data/cache/edcode_fetch_summary.json")
        if summary_file.exists():
            with open(summary_file) as f:
                data = json.load(f)
                return data.get("top_sections", [])
        return []
    
    # Load all manifests
    for manifest_file in sorted(manifest_dir.glob("batch_*.json")):
        with open(manifest_file) as f:
            manifest = json.load(f)
            
        for cmd in manifest["commands"]:
            all_sections.append({
                "section": cmd["section"],
                "law_code": cmd["law_code"],
                "url": cmd["url"],
                "count": cmd.get("count", 1),
                "description": cmd.get("description", "")
            })
    
    return all_sections


def process_batch_parallel(sections, max_workers=10):
    """Process a batch of sections in parallel"""
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_section = {
            executor.submit(fetch_section, section): section 
            for section in sections
        }
        
        # Process completed tasks
        completed = 0
        for future in as_completed(future_to_section):
            section = future_to_section[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "status": "error",
                    "section": section["section"],
                    "law_code": section["law_code"],
                    "error": str(e)
                })
            
            completed += 1
            if completed % 10 == 0:
                print(f"Progress: {completed}/{len(sections)} sections...")
    
    return results


def main():
    """Main function"""
    
    print("=" * 80)
    print("BULK ED CODE FETCHER")
    print("=" * 80)
    
    # Load sections
    sections = load_sections_to_fetch()
    
    # Filter out already cached
    to_fetch = []
    for s in sections:
        safe_section = s["section"].replace(".", "_")
        cache_file = Path(f"data/cache/edcode/{s['law_code'].lower()}_{safe_section}_full.json")
        if not cache_file.exists():
            to_fetch.append(s)
    
    if not to_fetch:
        print("All sections are already cached!")
        return
    
    print(f"\nTotal sections in manifests: {len(sections)}")
    print(f"Already cached: {len(sections) - len(to_fetch)}")
    print(f"To fetch: {len(to_fetch)}")
    
    # Sort by priority
    to_fetch.sort(key=lambda x: x.get("count", 1), reverse=True)
    
    # Determine batch size
    batch_size = 50
    if len(sys.argv) > 1:
        batch_size = int(sys.argv[1])
    
    batch_size = min(batch_size, len(to_fetch))
    
    print(f"\nFetching top {batch_size} sections by citation count...")
    print("\nTop 10:")
    for s in to_fetch[:10]:
        print(f"  {s['law_code']} {s['section']}: {s['count']} citations")
    
    # Process batch
    batch = to_fetch[:batch_size]
    
    print(f"\nProcessing {len(batch)} sections with 10 parallel workers...")
    start_time = time.time()
    
    results = process_batch_parallel(batch, max_workers=10)
    
    # Summarize results
    elapsed = time.time() - start_time
    
    status_counts = {}
    for r in results:
        status = r["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"\n\nCompleted in {elapsed:.1f} seconds")
    print(f"Average: {elapsed/len(batch):.2f} seconds per section")
    
    print("\nResults:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    # Show successful fetches
    successes = [r for r in results if r["status"] == "success"]
    if successes:
        print(f"\nSuccessfully fetched {len(successes)} sections")
        for s in successes[:5]:
            print(f"  {s['law_code']} {s['section']}: {s.get('title', 'No title')}")
    
    # Show errors
    errors = [r for r in results if r["status"] in ["error", "parse_error", "timeout"]]
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors[:5]:
            print(f"  {e['law_code']} {e['section']}: {e.get('error', 'Unknown')}")
    
    # Calculate remaining
    remaining = len(to_fetch) - batch_size
    if remaining > 0:
        print(f"\n{remaining} sections remaining")
        print(f"To fetch next batch: python scripts/bulk_edcode_fetcher.py {min(100, remaining)}")


if __name__ == "__main__":
    main()